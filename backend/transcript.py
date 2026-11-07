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
CODE_RE = re.compile(r"\b([A-Z]{3})\s?-?(\d{4}L?)\b")

PROMPT = """You are reading a student's academic transcript or unofficial course history.
Extract EVERY course row. Return ONLY JSON:
{"courses": [{"code": "ABC 1234", "title": "...", "grade": "A|B|C|D|F|W|IP|P|null", "credits": number|null, "term": "Fall 2026"|null}]}
Rules: codes are 3 letters + 4 digits (optional L). Use null when a field is not visible. Do not include the student's name, ID or any personal data."""


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


def _gemini_rows(data: bytes, mime: str) -> tuple[list[dict], str]:
    text, used = llm.gemini_vision(PROMPT, data, mime)
    s = re.sub(r"^```(?:json)?|```$", "", text.strip()).strip()
    try:
        obj = json.loads(s)
    except ValueError:
        m = re.search(r"\{.*\}", s, re.S)
        obj = json.loads(m.group(0)) if m else {}
    rows = obj.get("courses") if isinstance(obj, dict) else obj
    return [r for r in (rows or []) if isinstance(r, dict) and r.get("code")], used


def read(*, data: bytes | None = None, mime: str | None = None, text: str | None = None) -> dict:
    engine = {"name": "parser", "detail": "local text parser"}
    if text is not None:
        rows = _parse_text(text[:50000])
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
            rows = _parse_text(_pdf_text(data))
            engine = {"name": "parser", "detail": "PDF text layer"}
        if not rows:  # images, or scanned PDFs with no text layer
            try:
                rows, used = _gemini_rows(data, mime)
                engine = {"name": "gemini", "detail": used}
            except llm.LLMUnavailable as e:
                raise TranscriptError(503, "vision_unavailable",
                                      f"Reading images needs Gemini ({str(e)[:80]}). Paste the course list as text instead.")

    matched, not_in_catalog, not_counted = [], [], []
    cat = planner.catalog()["courses"]
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
    return {"engine": engine, "courses": matched, "completed": completed, "notCounted": not_counted,
            "notInCatalog": not_in_catalog, "synthetic": True}
