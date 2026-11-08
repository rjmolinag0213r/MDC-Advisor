"""Persistence: saved progress, saved plans, and a time-series event log for trends.

- DATABASE_URL set (TigerData / Timescale Postgres) -> psycopg; `events` becomes a hypertable
  and trends use time_bucket().
- DATABASE_URL unset -> local SQLite file (backend/data/nextstop.db), same API, so the app and
  tests work with zero setup.

Event logging runs on a background thread and never fails or slows a request.
"""
from __future__ import annotations

import json
import os
import queue
import sqlite3
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
SQLITE_PATH = Path(os.getenv("SQLITE_PATH", str(Path(__file__).parent / "data" / "nextstop.db")))
IS_PG = DATABASE_URL.startswith(("postgres://", "postgresql://"))

_init_lock = threading.Lock()
_ready = False
_timescale = False


def _connect():
    if IS_PG:
        import psycopg
        return psycopg.connect(DATABASE_URL, autocommit=True, connect_timeout=8)
    SQLITE_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(SQLITE_PATH, timeout=10, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def _q(sql: str) -> str:
    """Write SQL with %s placeholders; convert for SQLite."""
    return sql if IS_PG else sql.replace("%s", "?")


def init() -> None:
    global _ready, _timescale
    with _init_lock:
        if _ready:
            return
        conn = _connect()
        try:
            cur = conn.cursor()
            ts = "TIMESTAMPTZ" if IS_PG else "TEXT"
            js = "JSONB" if IS_PG else "TEXT"
            cur.execute(f"""CREATE TABLE IF NOT EXISTS progress (
                user_id TEXT NOT NULL, career_id TEXT NOT NULL, statuses {js} NOT NULL,
                updated_at {ts} NOT NULL, PRIMARY KEY (user_id, career_id))""")
            cur.execute(f"""CREATE TABLE IF NOT EXISTS saved_plans (
                user_id TEXT NOT NULL, program TEXT NOT NULL, plan {js} NOT NULL,
                updated_at {ts} NOT NULL, PRIMARY KEY (user_id, program))""")
            serial = "BIGSERIAL" if IS_PG else "INTEGER"
            pk = "PRIMARY KEY" + ("" if IS_PG else " AUTOINCREMENT")
            cur.execute(f"""CREATE TABLE IF NOT EXISTS chat_messages (
                id {serial} {pk}, user_id TEXT NOT NULL, sender TEXT NOT NULL,
                text TEXT NOT NULL, created_at {ts} NOT NULL)""")
            cur.execute("CREATE INDEX IF NOT EXISTS chat_messages_user ON chat_messages (user_id, id)")
            cur.execute(f"""CREATE TABLE IF NOT EXISTS chat_memory (
                user_id TEXT PRIMARY KEY, facts {js} NOT NULL, updated_at {ts} NOT NULL)""")
            cur.execute(f"""CREATE TABLE IF NOT EXISTS events (
                time {ts} NOT NULL, kind TEXT NOT NULL, career_id TEXT, program TEXT,
                engine TEXT, latency_ms INTEGER, language TEXT)""")
            if IS_PG:
                try:
                    cur.execute("CREATE EXTENSION IF NOT EXISTS timescaledb")
                    cur.execute("SELECT create_hypertable('events', 'time', if_not_exists => TRUE, migrate_data => TRUE)")
                    _timescale = True
                except Exception as e:  # plain Postgres still works, just without time_bucket
                    print(f"[store] timescaledb not available ({type(e).__name__}); using plain table")
                    conn.rollback() if not conn.autocommit else None
            cur.execute("CREATE INDEX IF NOT EXISTS events_kind_time ON events (kind, time)")
            if not IS_PG:
                conn.commit()
            _ready = True
            print(f"[store] {'TigerData/Postgres' if IS_PG else 'SQLite ' + str(SQLITE_PATH)} ready"
                  f"{' (timescaledb hypertable)' if _timescale else ''}")
        finally:
            conn.close()


def backend_info() -> dict:
    return {"kind": "postgres" if IS_PG else "sqlite", "timescale": _timescale, "ready": _ready}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _run(sql: str, params=(), fetch: bool = False):
    init()
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute(_q(sql), params)
        rows = cur.fetchall() if fetch else None
        if not IS_PG:
            conn.commit()
        return rows
    finally:
        conn.close()


def _dump(v) -> str:
    return json.dumps(v, ensure_ascii=False)


def _load(v):
    return v if isinstance(v, (dict, list)) else json.loads(v)


def _ts(dt: datetime):
    return dt if IS_PG else dt.isoformat()


# ---------- progress & plans ----------

def get_progress(user_id: str) -> dict:
    rows = _run("SELECT career_id, statuses, updated_at FROM progress WHERE user_id = %s", (user_id,), fetch=True)
    return {r[0]: {"statuses": _load(r[1]), "updatedAt": str(r[2])} for r in rows}


def put_progress(user_id: str, career_id: str, statuses: dict) -> None:
    _run("""INSERT INTO progress (user_id, career_id, statuses, updated_at) VALUES (%s, %s, %s, %s)
            ON CONFLICT (user_id, career_id) DO UPDATE SET statuses = excluded.statuses, updated_at = excluded.updated_at""",
         (user_id, career_id, _dump(statuses), _ts(_now())))


def delete_progress(user_id: str, career_id: str) -> None:
    _run("DELETE FROM progress WHERE user_id = %s AND career_id = %s", (user_id, career_id))


def get_plans(user_id: str) -> dict:
    rows = _run("SELECT program, plan, updated_at FROM saved_plans WHERE user_id = %s", (user_id,), fetch=True)
    return {r[0]: {"plan": _load(r[1]), "updatedAt": str(r[2])} for r in rows}


def save_plan(user_id: str, program: str, plan: dict) -> None:
    _run("""INSERT INTO saved_plans (user_id, program, plan, updated_at) VALUES (%s, %s, %s, %s)
            ON CONFLICT (user_id, program) DO UPDATE SET plan = excluded.plan, updated_at = excluded.updated_at""",
         (user_id, program, _dump(plan), _ts(_now())))


# ---------- advisor memory: conversation + remembered facts ----------

MEMORY_KEYS = ("interests", "goals", "subjects", "concerns", "programLeaning", "careerLeaning", "language", "grade")
LIST_KEYS = ("interests", "goals", "subjects", "concerns")


def append_chat(user_id: str, messages: list[dict]) -> None:
    init()
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.executemany(_q("INSERT INTO chat_messages (user_id, sender, text, created_at) VALUES (%s, %s, %s, %s)"),
                        [(user_id, m["sender"], str(m["text"])[:4000], _ts(_now())) for m in messages])
        # keep the last 200 messages per student
        cur.execute(_q("""DELETE FROM chat_messages WHERE user_id = %s AND id NOT IN
                          (SELECT id FROM chat_messages WHERE user_id = %s ORDER BY id DESC LIMIT 200)"""), (user_id, user_id))
        if not IS_PG:
            conn.commit()
    finally:
        conn.close()


def get_chat(user_id: str, limit: int = 50) -> list[dict]:
    rows = _run("SELECT sender, text, created_at FROM chat_messages WHERE user_id = %s ORDER BY id DESC LIMIT %s",
                (user_id, int(limit)), fetch=True)
    return [{"sender": r[0], "text": r[1], "at": str(r[2])} for r in reversed(rows)]


def get_memory(user_id: str) -> dict:
    rows = _run("SELECT facts FROM chat_memory WHERE user_id = %s", (user_id,), fetch=True)
    return _load(rows[0][0]) if rows else {}


def merge_memory(old: dict, update: dict | None) -> dict:
    """Merge facts the model learned into what we already remember (dedupe, cap, drop junk)."""
    out = {k: (list(old.get(k) or []) if k in LIST_KEYS else old.get(k)) for k in MEMORY_KEYS}
    if not isinstance(update, dict):
        return {k: v for k, v in out.items() if v}
    for k in LIST_KEYS:
        vals = update.get(k)
        if isinstance(vals, str):
            vals = [vals]
        for v in vals or []:
            v = str(v).strip()[:60]
            if v and v.lower() not in {x.lower() for x in out[k]}:
                out[k].append(v)
        out[k] = out[k][-8:]
    for k in ("programLeaning", "careerLeaning", "language", "grade"):
        v = update.get(k)
        if isinstance(v, (str, int)) and str(v).strip() and str(v).lower() not in ("null", "none", "unknown"):
            out[k] = str(v).strip()[:60]
    return {k: v for k, v in out.items() if v}


def put_memory(user_id: str, facts: dict) -> None:
    _run("""INSERT INTO chat_memory (user_id, facts, updated_at) VALUES (%s, %s, %s)
            ON CONFLICT (user_id) DO UPDATE SET facts = excluded.facts, updated_at = excluded.updated_at""",
         (user_id, _dump(facts), _ts(_now())))


def forget_chat(user_id: str) -> None:
    _run("DELETE FROM chat_messages WHERE user_id = %s", (user_id,))
    _run("DELETE FROM chat_memory WHERE user_id = %s", (user_id,))


# ---------- events (time series) ----------

_events: queue.Queue = queue.Queue(maxsize=5000)


def log_event(kind: str, **fields) -> None:
    """Fire-and-forget. Never raises, never blocks the request."""
    if os.getenv("EVENTS_DISABLED") == "1":
        return
    try:
        _events.put_nowait((_now(), kind, fields))
    except queue.Full:
        pass


def _writer():
    while True:
        batch = [_events.get()]
        time.sleep(0.2)
        while not _events.empty() and len(batch) < 200:
            batch.append(_events.get_nowait())
        try:
            init()
            conn = _connect()
            try:
                cur = conn.cursor()
                sql = _q("INSERT INTO events (time, kind, career_id, program, engine, latency_ms, language) VALUES (%s, %s, %s, %s, %s, %s, %s)")
                cur.executemany(sql, [(_ts(t), k, f.get("career_id"), f.get("program"), f.get("engine"),
                                       f.get("latency_ms"), f.get("language")) for t, k, f in batch])
                if not IS_PG:
                    conn.commit()
            finally:
                conn.close()
        except Exception as e:
            print(f"[store] dropped {len(batch)} events: {type(e).__name__}: {str(e)[:120]}")


threading.Thread(target=_writer, daemon=True, name="event-writer").start()


def flush(timeout: float = 3.0) -> None:
    """Wait for queued events to be written (tests / shutdown)."""
    end = time.monotonic() + timeout
    while not _events.empty() and time.monotonic() < end:
        time.sleep(0.05)
    time.sleep(0.4)


def trends(days: int = 7, bucket: str = "day") -> dict:
    init()
    since = _now() - timedelta(days=days)
    if IS_PG and _timescale:
        interval = {"hour": "1 hour", "day": "1 day"}[bucket]
        series_sql = (f"SELECT time_bucket('{interval}', time) AS b, kind, count(*) FROM events "
                      f"WHERE time >= %s GROUP BY b, kind ORDER BY b")
    elif IS_PG:
        series_sql = f"SELECT date_trunc('{bucket}', time) AS b, kind, count(*) FROM events WHERE time >= %s GROUP BY b, kind ORDER BY b"
    else:
        width = 13 if bucket == "hour" else 10
        series_sql = f"SELECT substr(time, 1, {width}) AS b, kind, count(*) FROM events WHERE time >= %s GROUP BY b, kind ORDER BY b"
    series = _run(series_sql, (_ts(since),), fetch=True)
    top = _run("""SELECT career_id, count(*) AS n FROM events WHERE time >= %s AND career_id IS NOT NULL
                  GROUP BY career_id ORDER BY n DESC LIMIT 10""", (_ts(since),), fetch=True)
    programs = _run("""SELECT program, count(*) AS n FROM events WHERE time >= %s AND kind = 'chat' AND program IS NOT NULL
                       GROUP BY program ORDER BY n DESC""", (_ts(since),), fetch=True)
    engines = _run("""SELECT engine, count(*), avg(latency_ms) FROM events WHERE time >= %s AND engine IS NOT NULL
                      GROUP BY engine ORDER BY count(*) DESC""", (_ts(since),), fetch=True)
    langs = _run("""SELECT language, count(*) FROM events WHERE time >= %s AND language IS NOT NULL
                    GROUP BY language""", (_ts(since),), fetch=True)
    out_series: dict = {}
    for b, kind, n in series:
        key = b.isoformat() if hasattr(b, "isoformat") else str(b)
        out_series.setdefault(key, {})[kind] = int(n)
    return {
        "days": days, "bucket": bucket, "storage": backend_info(),
        "series": [{"bucket": k, **v} for k, v in out_series.items()],
        "topCareers": [{"careerId": c, "count": int(n)} for c, n in top],
        "recommendedPrograms": [{"program": p, "count": int(n)} for p, n in programs],
        "engines": [{"engine": e, "count": int(n), "avgLatencyMs": round(float(a), 1) if a is not None else None} for e, n, a in engines],
        "languages": {l: int(n) for l, n in langs},
    }
