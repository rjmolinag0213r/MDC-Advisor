"""Input and output guards: PII redaction, prompt-injection detection, output scrubbing."""
from __future__ import annotations

import re

_PHONE = re.compile(r"(?<!\d)(?:\+?1[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}(?!\d)")
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
_STUDENT_ID = re.compile(r"(?i)(?:student\s*(?:id|number|#)\s*(?:is|:)?\s*)?(?<!\d)\d{6,10}(?!\d)")
_ADDRESS = re.compile(
    r"(?i)\b\d{1,6}\s+(?:[A-Z][\w.]*\s){0,4}?(?:way|st|street|ave|avenue|rd|road|blvd|boulevard|dr|drive|"
    r"ln|lane|ct|court|ter|terrace|pl|place|hwy|highway|cir|circle)\b\.?(?:,?\s*(?:apt|apartment|unit|suite|#)\s*[\w-]+)?"
)
_SCHOOL = re.compile(r"\b(?:[A-Z][a-z]+\s){1,3}(?:High|Senior High|Middle|Academy)(?:\s+School)?\b")
_INTRO_NAME = re.compile(r"(?i)\b(?:i'?m|i am|my name is|me llamo|soy)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})(?=\s+(?:from|de|and|y)\b|[,.])")

_INJECTION = [
    r"ignore (?:all |any |the )?(?:previous|prior|above|earlier) (?:instructions|prompts|rules)",
    r"disregard (?:all |your )?(?:previous |prior )?(?:instructions|rules)",
    r"(?:print|show|reveal|repeat|output|tell me) (?:me )?(?:your |the )?(?:full |entire |whole )?(?:system|hidden|initial) (?:prompt|instructions|message)",
    r"system prompt",
    r"(?:set|change|make) (?:my )?(?:progress|programname|program name|careerplan)",
    r"mark (?:every|all) (?:class|classes|course|courses) (?:as )?completed",
    r"reply only with",
    r"you are now (?:dan|in developer mode)",
    r"ignora (?:todas )?las instrucciones",
]
_INJECTION_RE = re.compile("|".join(_INJECTION), re.I)


def redact_pii(text: str) -> tuple[str, list[str]]:
    """Replace personal details with placeholders. Returns (clean_text, kinds_found)."""
    found: list[str] = []

    def sub(pattern: re.Pattern, label: str, s: str) -> str:
        def repl(m):
            found.append(label)
            return f"[{label}]"
        return pattern.sub(repl, s)

    out = sub(_EMAIL, "email", text)
    out = sub(_PHONE, "phone", out)
    out = sub(_ADDRESS, "address", out)
    out = sub(_STUDENT_ID, "id number", out)
    out = sub(_SCHOOL, "school", out)

    def name_repl(m):
        found.append("name")
        return m.group(0).replace(m.group(1), "[name]")
    out = _INTRO_NAME.sub(name_repl, out)
    return out, sorted(set(found))


def is_injection(text: str) -> bool:
    return bool(_INJECTION_RE.search(text or ""))


PUBLIC_NUMBERS = re.compile(r"\(?305\)?[\s.-]?237[\s.-]?8888")  # MDC advisement line, safe to show
_MDC_TOKEN = "\u0000MDCPHONE\u0000"


def scrub_output(text: str, forbidden: list[str]) -> str:
    """Remove PII and any forbidden fragments (system-prompt lines, canaries) from model output."""
    out = PUBLIC_NUMBERS.sub(_MDC_TOKEN, text)
    out, _ = redact_pii(out)
    out = out.replace(_MDC_TOKEN, "(305) 237-8888")
    for frag in forbidden:
        if frag and len(frag) >= 12 and frag.lower() in out.lower():
            out = re.sub(re.escape(frag), "", out, flags=re.I)
    # drop emoji / pictographs but keep accented letters and Spanish punctuation
    out = re.sub(r"[\U0001F000-\U0001FAFF\u2600-\u27BF\uFE0F]", "", out)
    return out.strip()
