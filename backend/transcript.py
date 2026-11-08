"""Read a transcript (photo, screenshot, PDF or pasted text) into completed course codes.

Gemini reads images and scanned PDFs natively (multimodal). Text PDFs and pasted text are
parsed locally first, so the feature still works with no key. The file is never stored and
only course rows are returned; names and student IDs are discarded.
"""
from __future__ import annotations

import io
import json
import re

import llm
import planner

ALLOWED = {"application/pdf": "pdf", "image/png": "image", "image/jpeg": "image", "image/webp": "image"}
MAX_BYTES = 5 * 1024 * 1024
PASSING = {"A+", "A", "A-", "B+", "B", "B-", "C+", "C", "P", "S", "T", "TR", "IP"}  # IP = in progress
CODE_RE = re.compile(r"\b([A-Z]{3})\s?-?(\d{4}[CL]?)\b")   # C = combined lecture/lab at MDC (e.g. CAI 1001C)

PROMPT = """You are reading a student's academic transcript: a HIGH SCHOOL transcript or a COLLEGE course history.
Extract EVERY course row. Return ONLY JSON:
{"level": "high_school"|"college",
 "courses": [{"code": "ABC 1234"|null, "title": "...", "grade": "A|B|C|D|F|W|IP|P|null", "credits": number|null, "term": "Fall 2026"|null,
              "subject": "math"|"cs"|"science"|"english"|"social"|"language"|"art"|"business"|"health"|"tech"|"other",
              "honors": true|false}]}
Rules: college codes are 3 letters + 4 digits with an optional C or L suffix (e.g. CAI 1001C, PHY 2048L); keep the suffix.
High-school courses usually have no code (use null).
Set honors true for AP, IB, Honors or Dual Enrollment courses. Use null when a field is not visible.
Do not include the student's name, ID, school name or any personal data."""

# ---- high-school strengths -> MDC programs ----
SUBJECT_RE = [
    ("cs", r"computer|programming|coding|\bcs\b|robotics|python|java|web design|information tech|\bit\b|artificial intelligence|"
           r"machine learning|natural language|database|cloud|cyber|data analytics|data structures"),
    ("math", r"algebra|geometry|calculus|statistic|trig|pre-?calc|math"),
    ("science", r"physics|chemistry|biology|anatomy|science|environmental|engineering"),
    ("english", r"english|literature|writing|composition|language arts|journalism"),
    ("social", r"history|government|civics|economics|psychology|sociology|geography"),
    ("language", r"spanish|french|portuguese|creole|chinese|latin|italian|german"),
    ("art", r"\bart\b|drawing|design|music|theater|theatre|photography|ceramics|band|chorus"),
    ("business", r"business|accounting|marketing|finance|entrepreneur"),
    ("health", r"health|nursing|medical|culinary|nutrition|sports med"),
]
GRADE_PTS = {"A+": 4.0, "A": 4.0, "A-": 3.7, "B+": 3.3, "B": 3.0, "B-": 2.7, "C+": 2.3, "C": 2.0, "C-": 1.7,
             "D+": 1.3, "D": 1.0, "D-": 0.7, "F": 0.0}
SUBJECT_LABEL = {"math": "Math", "cs": "Computer science", "science": "Science", "english": "English and writing",
                 "social": "Social studies", "language": "World languages", "art": "Arts and design",
                 "business": "Business", "health": "Health sciences", "tech": "Technology", "other": "Other"}
# how much each subject points toward each MDC tech program (and a few non-tech careers)
PROGRAM_WEIGHTS = {
    "AI": {"math": 1.0, "cs": 1.0, "science": .4},
    "DATA": {"math": 1.0, "cs": .5, "business": .8, "social": .3},
    "CYBER": {"cs": 1.0, "tech": .8, "math": .4, "social": .2},
    "SWE": {"cs": 1.2, "math": .5, "art": .3},
    "NET": {"tech": 1.0, "cs": .7, "science": .4},
    "ECE": {"science": 1.0, "math": 1.0, "cs": .3},
}
CAREER_WEIGHTS = {"registered-nurse": {"health": 1.0, "science": .8}, "architect": {"art": .9, "math": .6},
                  "chef": {"health": .5, "art": .5, "business": .4}}
PROGRAM_NAME = {"AI": "Applied Artificial Intelligence", "DATA": "Data Analytics", "CYBER": "Cybersecurity",
                "SWE": "Software Engineering", "NET": "Networking", "ECE": "Electrical & Computer Engineering"}


def _subject_of(row: dict) -> str:
    s = str(row.get("subject") or "").lower()
    if s in SUBJECT_LABEL and s != "other":
        return s
    title = str(row.get("title") or "").lower()
    for subj, pat in SUBJECT_RE:
        if re.search(pat, title):
            return subj
    return "other"


def strengths(rows: list[dict]) -> dict:
    """Average grade per subject (honors/AP count a bit more) -> strengths and best-fit programs."""
    agg: dict[str, list[float]] = {}
    for r in rows:
        g = str(r.get("grade") or "").upper().strip()
        if g not in GRADE_PTS:
            continue
        pts = GRADE_PTS[g] + (0.5 if r.get("honors") or re.search(r"\b(ap|ib|honors|dual)\b", str(r.get("title") or ""), re.I) else 0)
        agg.setdefault(_subject_of(r), []).append(min(pts, 4.5))
    subjects = sorted(({"subject": k, "label": SUBJECT_LABEL[k], "avg": round(sum(v) / len(v), 2), "courses": len(v)}
                       for k, v in agg.items() if k != "other"), key=lambda x: (-x["avg"], -x["courses"]))
    strong = [s for s in subjects if s["avg"] >= 3.0]
    score = lambda w: sum(w.get(s["subject"], 0) * (s["avg"] - 2.0) * min(s["courses"], 4) ** .5 for s in subjects)
    progs = sorted(({"code": k, "name": PROGRAM_NAME[k], "score": round(score(w), 2)} for k, w in PROGRAM_WEIGHTS.items()),
                   key=lambda x: -x["score"])
    careers = sorted(({"careerId": k, "score": round(score(w), 2)} for k, w in CAREER_WEIGHTS.items()), key=lambda x: -x["score"])
    for p in progs:
        top = [s["label"].lower() for s in strong if PROGRAM_WEIGHTS[p["code"]].get(s["subject"], 0) >= .5][:2]
        p["why"] = f"Your strongest grades are in {' and '.join(top)}." if top else "A good fit to explore."
    all_pts = [x for v in agg.values() for x in v]
    return {"subjects": subjects, "strong": [s["label"] for s in strong[:4]],
            "gpa": round(sum(min(x, 4.0) for x in all_pts) / len(all_pts), 2) if all_pts else None,
            "suggestedPrograms": [p for p in progs if p["score"] > 0][:3] or progs[:2],
            "otherCareers": [c for c in careers if c["score"] > 1.5][:2]}


HS_LINE = re.compile(r"^\s*(?P<title>[A-Za-z][A-Za-z0-9 &/().,'-]{2,60}?)\s+(?P<grade>A\+|A-|A|B\+|B-|B|C\+|C-|C|D\+|D-|D|F)\s*(?:\d+(?:\.\d+)?)?\s*$")


def _parse_hs_text(text: str) -> list[dict]:
    rows = []
    for line in text.splitlines():
        m = HS_LINE.match(line)
        if m and not CODE_RE.search(line.upper()):
            rows.append({"code": None, "title": m.group("title").strip(), "grade": m.group("grade"), "credits": None,
                         "term": None, "subject": None, "honors": bool(re.search(r"\b(ap|ib|honors|dual)\b", line, re.I))})
    return rows


class TranscriptError(ValueError):
    def __init__(self, status: int, error: str, message: str):
        super().__init__(message)
        self.status, self.error, self.message = status, error, message


def _sniff(data: bytes, declared: str | None) -> str:
    if data[:4] == b"%PDF":
        return "application/pdf"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if data[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return declared or "application/octet-stream"


def _parse_text(text: str) -> list[dict]:
    rows, seen = [], set()
    for line in text.splitlines():
        m = CODE_RE.search(line.upper())
        if not m:
            continue
        code = f"{m.group(1)} {m.group(2)}"
        if code in seen:
            continue
        seen.add(code)
        grade = None
        g = re.search(r"\s(A\+|A-|A|B\+|B-|B|C\+|C-|C|D\+|D-|D|F|WF|W|IP|P|S|TR|T)\s*(?:\d+(?:\.\d+)?)?\s*$", line.strip().upper())
        if g:
            grade = g.group(1)
        rows.append({"code": code, "title": None, "grade": grade, "credits": None, "term": None})
    return rows


def _pdf_text(data: bytes) -> str:
    try:
        from pypdf import PdfReader
        return "\n".join((p.extract_text() or "") for p in PdfReader(io.BytesIO(data)).pages[:10])
    except Exception:
        return ""


_last_level = {"level": None}


def _gemini_rows(data: bytes, mime: str) -> tuple[list[dict], str]:
    text, used = llm.gemini_vision(PROMPT, data, mime)
    s = re.sub(r"^```(?:json)?|```$", "", text.strip()).strip()
    try:
        obj = json.loads(s)
    except ValueError:
        m = re.search(r"\{.*\}", s, re.S)
        obj = json.loads(m.group(0)) if m else {}
    rows = obj.get("courses") if isinstance(obj, dict) else obj
    _last_level["level"] = obj.get("level") if isinstance(obj, dict) else None
    return [r for r in (rows or []) if isinstance(r, dict) and (r.get("code") or r.get("title"))], used


def read(*, data: bytes | None = None, mime: str | None = None, text: str | None = None) -> dict:
    engine = {"name": "parser", "detail": "local text parser"}
    _last_level["level"] = None
    if text is not None:
        rows = _parse_text(text[:50000]) or _parse_hs_text(text[:50000])
    else:
        if not data:
            raise TranscriptError(400, "invalid_request", "Upload a file (field 'file') or send JSON {\"text\": ...}.")
        if len(data) > MAX_BYTES:
            raise TranscriptError(413, "payload_too_large", "Transcript files must be 5 MB or smaller.")
        mime = _sniff(data, mime)
        if mime not in ALLOWED:
            raise TranscriptError(415, "unsupported_media_type", "Upload a PDF, PNG, JPEG or WebP file.")
        rows = []
        if mime == "application/pdf":
            pdf_text = _pdf_text(data)
            rows = _parse_text(pdf_text) or _parse_hs_text(pdf_text)
            engine = {"name": "parser", "detail": "PDF text layer"}
        if not rows:  # images, or scanned PDFs with no text layer
            try:
                rows, used = _gemini_rows(data, mime)
                engine = {"name": "gemini", "detail": used}
            except llm.LLMUnavailable as e:
                raise TranscriptError(503, "vision_unavailable",
                                      f"Reading images needs Gemini ({str(e)[:80]}). Paste the course list as text instead.")

    cat = planner.catalog()["courses"]
    coded = [r for r in rows if r.get("code") and planner.canon(str(r["code"])) in cat]
    level = _last_level["level"] or ("college" if coded else "high_school" if rows else None)
    if level == "high_school" or (rows and not coded and not any(r.get("code") for r in rows)):
        hs = [{"title": str(r.get("title") or r.get("code") or "")[:80], "grade": (str(r.get("grade")).upper() if r.get("grade") not in (None, "", "null") else None),
               "subject": _subject_of(r), "honors": bool(r.get("honors")), "term": r.get("term")} for r in rows]
        return {"engine": engine, "level": "high_school", "courses": hs, "completed": [], "notCounted": [], "notInCatalog": [],
                "strengths": strengths(hs), "synthetic": True}

    matched, not_in_catalog, not_counted = [], [], []
    for r in rows:
        code = planner.canon(str(r.get("code", "")))
        grade = (str(r.get("grade")).upper().strip() if r.get("grade") not in (None, "", "null") else None)
        item = {"code": code, "title": r.get("title") or (cat.get(code) or {}).get("title"),
                "grade": grade, "credits": r.get("credits") or (cat.get(code) or {}).get("credits"), "term": r.get("term")}
        if code not in cat:
            not_in_catalog.append(item)
        elif grade and grade not in PASSING:
            item["reason"] = "grade below C (programs require C or higher)" if grade[0] in "DF" else f"grade {grade} does not earn credit"
            not_counted.append(item)
        else:
            matched.append(item)
    completed = list(dict.fromkeys(m["code"] for m in matched if m["grade"] != "IP"))
    # college transcripts get strengths too, using the catalog's course prefixes as subjects
    for m in matched + not_counted:
        m.setdefault("subject", _subject_of({"title": m.get("title")}))
    st = strengths(matched + not_counted)
    # real MDC course numbers (not the Z sample catalog): match them against MDC's official program sheets first
    real = [m for m in matched if not cat[m["code"]].get("synthetic", True)]
    if real:
        fits = []
        for code in ("AIBS", "AIAS"):
            p = planner.get_program(code)
            req = {c for g in p["requirement_groups"] for c in g["courses"]}
            hit = [m["code"] for m in real if m["code"] in req]
            if hit:
                fits.append({"code": code, "name": planner.program_label(p), "score": round(len(hit) * 2.0, 2), "official": True,
                             "why": f"{len(hit)} of your MDC courses count toward MDC's official {p.get('credential')} sheet ({p.get('sheet_code')})."})
        st["suggestedPrograms"] = fits + [s for s in st["suggestedPrograms"] if s["code"] not in ("AI",)][: max(0, 3 - len(fits))]
    return {"engine": engine, "level": "college", "courses": matched, "completed": completed, "notCounted": not_counted,
            "notInCatalog": not_in_catalog, "strengths": st, "realCourses": len(real), "synthetic": not real}
