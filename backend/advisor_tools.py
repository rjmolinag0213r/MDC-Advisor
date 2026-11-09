"""Plan preview, transfer-school lookup by URL, and "what if I switch?" analysis.

All numbers that can be computed are computed (planner + catalog); AI only writes the advice
and fills gaps (careers outside the catalog, facts read from a school's web page). Every AI-
derived field is labeled so the UI can say "AI estimate".
"""
from __future__ import annotations

import ipaddress
import json
import re
import socket
from urllib.parse import urljoin, urlparse

import requests

import llm
import planner
import roadmap
import safety

# MDC's published Florida-resident rates per credit (nwsa.mdc.edu tuition page, 2025-26): lower 118.22, upper 186.08.
# Plans mix both; a 120-credit B.S. is about half and half, so whole-plan estimates use the blend.
MDC_RATE = round((planner.mdc_rates().get("lowerDivision", 118.22) + planner.mdc_rates().get("upperDivision", 186.08)) / 2)
PROGRAM_CAREER = {"AI": "ai-engineer", "DATA": "data-analyst", "CYBER": "cybersecurity-specialist",
                  "SWE": "software-developer", "NET": "network-engineer", "ECE": "electrical-engineer",
                  "AIBS": "ai-engineer", "AIAS": "ai-engineer"}


def _ai_json(system: str, user: str, max_tokens: int = 700) -> tuple[dict | None, str | None, dict]:
    if not llm.available_providers():
        return None, None, {}
    meta: dict = {}
    msgs = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    try:
        content, used = llm.complete(msgs, temperature=0.3, max_tokens=max_tokens, meta_out=meta)
        # Prune's template/semantic caches treat prompts that differ only in numbers as the same request, so they
        # can hand back another student's (or another school's) answer. These answers are personal: ask again uncached.
        if (meta.get("prune") or {}).get("cacheHit"):
            try:
                meta = {}
                content, used = llm.complete(msgs, temperature=0.3, max_tokens=max_tokens, meta_out=meta, skip=("prune",))
            except llm.LLMUnavailable:
                return None, None, {}
    except llm.LLMUnavailable:
        return None, None, {}
    s = re.sub(r"^```(?:json)?|```$", "", content.strip()).strip()
    try:
        return json.loads(s), used, meta
    except ValueError:
        m = re.search(r"\{.*\}", s, re.S)
        try:
            return (json.loads(m.group(0)) if m else None), used, meta
        except ValueError:
            return None, used, meta


def _engine(used: str | None, meta: dict) -> dict:
    if not used:
        return {"name": "catalog", "detail": "Computed from the catalog (no AI)"}
    return {"name": "llm", "detail": used, **({"prune": meta["prune"]} if meta.get("prune") else {})}


# ---------------------------------------------------------------- plan preview

def plan_preview(program: str, completed=None, strengths: dict | None = None, memory: dict | None = None,
                 start_term: str = "Fall 2026", load: int = 15) -> dict:
    p = planner.get_program(program)
    full = planner.plan(p["app_program_code"], completed or [], start_term, load, 6, True)
    first = full["terms"][:2]
    career = roadmap.CAREERS.get(PROGRAM_CAREER.get(p["app_program_code"], ""), {})
    credits_left = full["creditsPlanned"]
    facts = {"program": p["name"], "graduationTerm": full["graduationTerm"], "termCount": full["termCount"],
             "creditsLeft": credits_left, "strongSubjects": (strengths or {}).get("strong", []),
             "interests": (memory or {}).get("interests", []), "goals": (memory or {}).get("goals", []),
             "career": career.get("title"), "medianSalary": (career.get("salary") or {}).get("median")}
    data, used, meta = _ai_json(
        "You are an MDC academic advisor writing a short plan preview for a student. Return ONLY JSON: "
        '{"why": "2 sentences: why this program fits THEM, citing their strong subjects/interests", '
        '"skills": ["3 skills they already have that transfer to this career"], '
        '"firstSteps": ["3 short concrete actions for the first semester"]}. Plain language, encouraging, honest.',
        json.dumps(facts))
    why = (data or {}).get("why") or (
        f"{p['name']} builds on your strengths in {', '.join(facts['strongSubjects'][:2]).lower()}." if facts["strongSubjects"]
        else f"{p['name']} is a 120-credit path that starts at MDC.")
    return {
        "program": {"code": p["app_program_code"], "name": p["name"], "totalCredits": p["total_credits"]},
        "career": {"id": career.get("id"), "title": career.get("title"), "salary": career.get("salary")},
        "why": safety.scrub_output(str(why), [])[:500],
        "skills": [str(x)[:120] for x in (data or {}).get("skills", [])][:3],
        "firstSteps": [str(x)[:140] for x in (data or {}).get("firstSteps", [])][:3],
        "firstTerms": first, "graduationTerm": full["graduationTerm"], "termCount": full["termCount"],
        "creditsLeft": credits_left, "estimatedCost": credits_left * MDC_RATE, "ratePerCredit": MDC_RATE,
        "warnings": full["warnings"], "engine": _engine(used, meta), "synthetic": True,
    }


# ---------------------------------------------------------------- school lookup by URL

class FetchError(ValueError):
    pass


def _public_host(host: str) -> None:
    """SSRF guard: the URL must resolve only to public internet addresses."""
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror:
        raise FetchError("That website address doesn't resolve.")
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast or ip.is_unspecified:
            raise FetchError("That address isn't a public website.")


def _fetch_public(url: str, max_bytes: int = 1_500_000) -> tuple[str, str]:
    for _ in range(4):  # follow up to 3 redirects, re-checking each hop
        u = urlparse(url)
        if u.scheme not in ("http", "https") or not u.hostname or (u.port and u.port not in (80, 443)):
            raise FetchError("Use a normal http(s) website address, e.g. https://www.fiu.edu")
        _public_host(u.hostname)
        r = requests.get(url, timeout=10, allow_redirects=False, stream=True,
                         headers={"User-Agent": "NextStop-MDC-Advisor/1.0 (+student transfer research)"})
        if r.status_code in (301, 302, 303, 307, 308) and r.headers.get("Location"):
            url = urljoin(url, r.headers["Location"])
            continue
        if r.status_code >= 400:
            raise FetchError(f"The site answered with an error ({r.status_code}).")
        ctype = r.headers.get("Content-Type", "")
        if "html" not in ctype and "text" not in ctype:
            raise FetchError("That link isn't a web page (try the school's tuition or transfer page).")
        body = b""
        for chunk in r.iter_content(65536):
            body += chunk
            if len(body) > max_bytes:
                break
        return body.decode(r.encoding or "utf-8", errors="replace"), url
    raise FetchError("Too many redirects.")


def _visible_text(html: str) -> tuple[str, str]:
    title = re.search(r"<title[^>]*>(.*?)</title>", html, re.S | re.I)
    html = re.sub(r"(?is)<(script|style|noscript|svg|nav|footer)[^>]*>.*?</\1>", " ", html)
    text = re.sub(r"(?s)<[^>]+>", " ", html)
    text = re.sub(r"&nbsp;|&#160;", " ", text)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text, re.sub(r"\s+", " ", title.group(1)).strip() if title else ""


TYPE_INDEX = {"florida_public": 0, "private": 1, "out_of_state_public": 2}


def school_info(url: str, program: str | None = None) -> dict:
    url = (url or "").strip()
    if not re.match(r"^https?://", url, re.I):
        url = "https://" + url
    html, final_url = _fetch_public(url)
    text, title = _visible_text(html)
    if len(text) < 200:
        raise FetchError("Couldn't read much from that page. Try the school's tuition or transfer admissions page.")
    data, used, meta = _ai_json(
        "You read a university web page for a transfer student. Extract ONLY what the page states. Return ONLY JSON: "
        '{"schoolName": str, "type": "florida_public"|"private"|"out_of_state_public"|"unknown", '
        '"costPerCreditInState": number|null, "costPerCreditOutOfState": number|null, "tuitionNote": str|null, '
        '"programs": [up to 6 program/major names relevant to the student, from the page], '
        '"transferNotes": [up to 4 short facts about transfer admission/credit transfer from the page], '
        '"deadline": str|null}. Use null when the page doesn\'t say. Never invent numbers.',
        f"Student's program: {program or 'unknown'}\nPage title: {title}\nURL: {final_url}\nPage text:\n{text[:12000]}",
        max_tokens=600)
    data = data or {}
    # fallback for cost when no AI or the model missed it: "$123.45 per credit (hour)"
    if not data.get("costPerCreditInState"):
        m = re.search(r"\$\s?(\d{2,4}(?:\.\d{2})?)\s*(?:per|/|a)\s*(?:credit|semester hour|credit hour)", text, re.I)
        if m:
            data["costPerCreditInState"] = float(m.group(1))
            data.setdefault("tuitionNote", "Found on the page as a per-credit price.")
    host = urlparse(final_url).hostname or ""
    stype = data.get("type") if data.get("type") in TYPE_INDEX else (
        "florida_public" if re.search(r"\b(fiu|ucf|usf|ufl|fsu|fau|unf|famu|fgcu|uwf|ncf|fpu)\.edu$", host) else "unknown")
    name = str(data.get("schoolName") or title.split("|")[0].split(" - ")[0] or host)[:80]
    rate = data.get("costPerCreditInState") or data.get("costPerCreditOutOfState")
    try:
        rate = float(rate) if rate else None
    except (TypeError, ValueError):
        rate = None
    return {
        "name": name, "type": stype, "typeIndex": TYPE_INDEX.get(stype, 1 if stype == "unknown" else 0),
        "rate": round(rate) if rate else None, "rateOutOfState": data.get("costPerCreditOutOfState"),
        "tuitionNote": data.get("tuitionNote"), "programs": [str(x)[:80] for x in (data.get("programs") or [])][:6],
        "transferNotes": [str(x)[:200] for x in (data.get("transferNotes") or [])][:4], "deadline": data.get("deadline"),
        "sourceUrl": final_url, "engine": _engine(used, meta), "aiExtracted": bool(used),
    }


# ---------------------------------------------------------------- what if I switch?

def _program_from_text(target: str) -> str | None:
    t = target.strip().upper()
    if t in planner.catalog()["programs"]:
        return planner.get_program(t)["app_program_code"]
    low = target.lower()
    if re.search(r"\b(a\.?s\.?|associate)\b", low) and re.search(r"\bai\b|artificial", low):
        return "AIAS"
    for code, name in (("AI", "artificial intelligence|machine learning"), ("DATA", "data analytics|data science|analytics"),
                       ("CYBER", "cyber|security"), ("SWE", "software|programming|developer"),
                       ("NET", "network|cloud"), ("ECE", "electrical|electronics|computer engineering|hardware")):
        if re.search(name, low):
            return code
    return None


def _gen_ed_credits(done: list[str]) -> int:
    cs = planner.catalog()["courses"]
    return sum(cs[c]["credits"] for c in done if c in cs and cs[c]["category"] in ("gen_ed",))


def whatif(current: str, completed, target: str, load: int = 15, in_progress=None, current_term: str = "Fall 2026") -> dict:
    """Stay vs switch, planned exactly like the Student Hub: completed + in-progress classes, from the term after now."""
    cur = planner.get_program(current)
    done, _ = planner._completed_set(completed)
    now, _ = planner._completed_set(in_progress)
    done = {c for c in done if planner.same_catalog(cur, c)}
    now = {c for c in now - done if planner.same_catalog(cur, c)}
    taken = sorted(done | now)   # in-progress classes count once they finish, as on the Progress tab
    start = planner.next_term(current_term)
    cur_plan = planner.plan(cur["app_program_code"], taken, start, load, 0, False)
    earned = planner._credits(done)
    pct = round(100 * earned / cur["total_credits"])
    cur_career = roadmap.CAREERS.get(PROGRAM_CAREER.get(cur["app_program_code"], ""), {})
    current_side = {"program": cur["name"], "code": cur["app_program_code"], "percent": pct, "creditsEarned": earned,
                    "creditsInProgress": planner._credits(now), "startTerm": start,
                    "termsLeft": cur_plan["termCount"], "creditsLeft": cur_plan["creditsPlanned"],
                    "costLeft": cur_plan["creditsPlanned"] * MDC_RATE, "graduationTerm": cur_plan["graduationTerm"],
                    "career": cur_career.get("title"), "medianSalary": (cur_career.get("salary") or {}).get("median")}

    code = _program_from_text(target)
    if code and code != cur["app_program_code"]:
        tgt = planner.get_program(code)
        audit = planner.audit(code, sorted(done))
        tplan = planner.plan(code, taken, start, load, 0, False)
        car = roadmap.CAREERS.get(PROGRAM_CAREER.get(code, ""), {})
        target_side = {"kind": "catalog", "title": tgt["name"], "code": code, "creditsCarryOver": audit["creditsEarned"],
                       "creditsLost": max(0, earned - audit["creditsEarned"]), "termsLeft": tplan["termCount"],
                       "creditsLeft": tplan["creditsPlanned"], "costLeft": tplan["creditsPlanned"] * MDC_RATE,
                       "yearsToCareer": round(tplan["termCount"] / 3, 1), "graduationTerm": tplan["graduationTerm"],
                       "career": car.get("title"), "medianSalary": (car.get("salary") or {}).get("median"),
                       "outlook": None, "estimate": False}
    else:
        # career outside the catalog (e.g. doctor): gen-ed carries over, AI estimates the rest
        gen = _gen_ed_credits(sorted(done))
        est, used0, _ = _ai_json(
            "You estimate the path to a career for a US student. Return ONLY JSON: "
            '{"title": str, "steps": [short list of required degrees/training in order], "yearsFromStart": number '
            '(total years from starting college to working in the career, incl. graduate school/residency), '
            '"typicalTotalCostUSD": number (tuition for all required schooling, US public-school typical), '
            '"medianSalaryUSD": number|null (BLS-style median), "jobOutlook": "short phrase, e.g. Faster than average (+X% 2023-33)", '
            '"prereqNotes": "one sentence on prerequisites a student switching in would still need"}. '
            "Be realistic; if unsure give conservative typical values.",
            f"Career: {target[:80]}", max_tokens=500)
        est = est or {}
        years = float(est.get("yearsFromStart") or 8)
        credit_years = gen / 30.0   # ~30 credits a year
        target_side = {"kind": "career", "title": str(est.get("title") or target.title())[:80], "code": None,
                       "creditsCarryOver": gen, "creditsLost": max(0, earned - gen),
                       "steps": [str(s)[:120] for s in (est.get("steps") or [])][:6],
                       "yearsToCareer": round(max(years - credit_years, 1), 1),
                       "costLeft": int(est.get("typicalTotalCostUSD") or 0) or None,
                       "medianSalary": est.get("medianSalaryUSD"), "outlook": est.get("jobOutlook"),
                       "prereqNotes": est.get("prereqNotes"), "estimate": True}
    current_side["yearsToCareer"] = round(current_side["termsLeft"] / 3, 1)

    delta_years = round((target_side.get("yearsToCareer") or 0) - current_side["yearsToCareer"], 1)
    lost = target_side["creditsLost"]
    # rule-of-thumb verdict, then AI writes the advice around these numbers
    if pct < 25:
        verdict, timing = "switch_ok", "early"
    elif pct < 60:
        verdict, timing = ("consider" if lost < 30 else "think_hard"), "middle"
    else:
        verdict, timing = "finish_first", "late"
    facts = {"current": current_side, "target": target_side, "extraYears": delta_years, "creditsLost": lost,
             "ruleOfThumb": verdict, "timing": timing}
    adv, used, meta = _ai_json(
        "You are a caring, honest MDC academic advisor. A student asks if they should switch from their current path to a new one. "
        "Using ONLY the numbers given, return ONLY JSON: "
        '{"verdict": "stay"|"switch"|"finish_then_pivot"|"explore_first", "headline": "max 12 words", '
        '"advice": "3-4 sentences: is it early or late to switch, what they lose/gain in time, money and job market, '
        'and a smart middle path (e.g. finish the degree then a post-bacc, or take one intro course first)", '
        '"nextSteps": ["3 concrete actions"]}. Plain language for a teenager or young adult. '
        "Write money like $12,345 and use the student's real numbers from the facts.",
        json.dumps(facts, default=str))
    if not adv:
        adv = {"verdict": {"switch_ok": "switch", "consider": "explore_first", "think_hard": "explore_first",
                           "finish_first": "finish_then_pivot"}[verdict],
               "headline": {"early": "It's early. Switching now costs little.",
                            "middle": "Halfway there: test the new path before you switch.",
                            "late": "You're close. Finish first, then pivot."}[timing],
               "advice": f"You're {pct}% through {cur['name']}. Switching means about {abs(delta_years)} more years and "
                         f"{lost} credits that won't count. Talk to an MDC advisor before you decide.",
               "nextSteps": ["Talk to an MDC advisor", "Take one intro course in the new field", "Compare costs with your family"]}
    return {"current": current_side, "target": target_side, "extraYears": delta_years, "timing": timing,
            "verdict": adv.get("verdict"), "headline": safety.scrub_output(str(adv.get("headline") or ""), [])[:120],
            "advice": safety.scrub_output(str(adv.get("advice") or ""), [])[:900],
            "nextSteps": [str(x)[:140] for x in (adv.get("nextSteps") or [])][:3],
            "engine": _engine(used, meta), "ratePerCredit": MDC_RATE, "synthetic": True}


# ---------------------------------------------------------------- other possible paths (approved plan stays locked)

def paths(current: str, completed, load: int = 15, limit: int = 3) -> dict:
    """Programs closest to the approved one, ranked by how many of the student's credits would carry over.
    Read-only: nothing here changes the approved plan."""
    cur = planner.get_program(current)
    done, _ = planner._completed_set(completed)
    mine = planner.audit(cur["app_program_code"], sorted(done))["creditsEarned"]
    out = []
    for p in planner.catalog()["program_list"]:
        code = p["app_program_code"]
        if code == cur["app_program_code"]:
            continue
        # a sample-catalog twin of the approved program (same name) is the same path, not an alternative
        if p["name"] == cur["name"] and p.get("synthetic", True) != cur.get("synthetic", True):
            continue
        same = planner.map_to_catalog(p, sorted(done))
        estimated = p.get("synthetic", True) != cur.get("synthetic", True)   # matched across catalogs by title
        a = planner.audit(code, same)
        req = {planner.canon(c) for g in p["requirement_groups"] for c in g["courses"]}
        cur_req = set(planner.map_to_catalog(p, [planner.canon(c) for g in cur["requirement_groups"] for c in g["courses"]]))
        shared = len(req & cur_req) / max(len(req | cur_req), 1)     # how alike the two programs are
        if a["creditsEarned"] == 0 and shared == 0:
            continue
        pl = planner.plan(code, same, "Fall 2026", load, 6, True)
        car = roadmap.CAREERS.get(PROGRAM_CAREER.get(code, ""), {})
        label = planner.program_label(p) + (" (sample catalog)" if p.get("synthetic", True) and not cur.get("synthetic", True) else "")
        out.append({"code": code, "name": label, "official": not p.get("synthetic", True), "estimate": estimated,
                    "creditsCarryOver": a["creditsEarned"], "creditsEarnedNow": mine,
                    "percentDone": a["percentComplete"], "termsLeft": pl["termCount"], "graduationTerm": pl["graduationTerm"],
                    "sharedCourses": round(100 * shared), "career": car.get("title"),
                    "medianSalary": (car.get("salary") or {}).get("median")})
    out.sort(key=lambda x: (-x["creditsCarryOver"], -x["sharedCourses"], x["termsLeft"]))
    return {"approved": {"code": cur["app_program_code"], "name": planner.program_label(cur), "creditsEarned": mine},
            "paths": out[:limit], "note": "Possible paths are for comparing only. Your approved plan stays locked."}
