"""Degree planner on top of the synthetic course catalog (data/synthetic).

SYNTHETIC DATA: course codes start with Z and nothing here is MDC's real catalog.
Every response is flagged with "synthetic": true so the UI can label it.

- audit(program, completed)                -> per-requirement progress and what's left
- plan(program, completed, start_term ...) -> semester-by-semester plan that respects
                                              prerequisites, corequisite labs, terms offered,
                                              credit minimums and permission flags
- schedule(courses, term, preferences)     -> conflict-free sections (pairs linked labs,
                                              skips cancelled, reports full/waitlist/conflicts)
"""
from __future__ import annotations

import json
import os
import re
from functools import lru_cache
from itertools import product
from pathlib import Path

DATA_DIR = Path(os.getenv("CATALOG_DIR", str(Path(__file__).parent / "data" / "synthetic")))
SEASONS = ("Fall", "Spring", "Summer")


class PlannerError(ValueError):
    def __init__(self, message: str, field: str | None = None, **extra):
        super().__init__(message)
        self.field, self.extra = field, extra


@lru_cache(maxsize=1)
def catalog() -> dict:
    load = lambda name: json.loads((DATA_DIR / name).read_text(encoding="utf-8"))
    programs, courses, sections = load("programs.json"), load("courses.json"), load("sections.json")
    by_code = {c["code"]: c for c in courses["courses"]}
    alias = {}
    for c in courses["courses"]:
        for other in c.get("cross_listed_as") or []:
            alias[other] = c["code"]
    progs = {p["app_program_code"]: p for p in programs["programs"]}
    progs.update({p["id"]: p for p in programs["programs"]})
    secs: dict[tuple[str, str], list] = {}
    by_crn = {}
    for s in sections["sections"]:
        secs.setdefault((s["course_code"], s["term"]), []).append(s)
        by_crn[s["crn"]] = s
    return {"programs": progs, "program_list": programs["programs"], "courses": by_code, "alias": alias,
            "sections": secs, "by_crn": by_crn, "terms": sections["terms"], "edge_cases": courses.get("edge_cases", {})}


def available() -> bool:
    try:
        catalog()
        return True
    except (OSError, ValueError, KeyError):
        return False


def canon(code: str) -> str:
    code = re.sub(r"\s+", " ", str(code).strip().upper())
    m = re.fullmatch(r"([A-Z]{3})\s?(\d{4}L?)", code)
    if m:
        code = f"{m.group(1)} {m.group(2)}"
    return catalog()["alias"].get(code, code)


def get_program(code: str) -> dict:
    p = catalog()["programs"].get(str(code).strip().upper()) or catalog()["programs"].get(str(code).strip())
    if not p:
        raise PlannerError(f"Unknown program '{str(code)[:20]}'.", "program",
                           validPrograms=[x["app_program_code"] for x in catalog()["program_list"]])
    return p


def course_info(code: str) -> dict | None:
    c = catalog()["courses"].get(canon(code))
    if not c:
        return None
    return {k: c[k] for k in ("code", "title", "credits", "level", "category", "prerequisites", "corequisites",
                              "terms_offered", "min_credits_completed", "instructor_permission", "cross_listed_as", "status")}


def _completed_set(completed) -> tuple[set[str], list[str]]:
    if completed is None:
        completed = []
    if not isinstance(completed, list):
        raise PlannerError("completed must be an array of course codes.", "completed")
    done, unknown = set(), []
    for x in completed[:200]:
        code = canon(x)
        (done.add(code) if code in catalog()["courses"] else unknown.append(str(x)[:20]))
    return done, unknown


def _credits(codes) -> int:
    cs = catalog()["courses"]
    return sum(cs[c]["credits"] for c in codes if c in cs)


def _prereqs_met(code: str, done: set[str]) -> bool:
    c = catalog()["courses"][code]
    return all(any(canon(opt) in done for opt in group) for group in c.get("prerequisites") or [])


def _missing_prereqs(code: str, done: set[str]) -> list[list[str]]:
    c = catalog()["courses"][code]
    return [g for g in c.get("prerequisites") or [] if not any(canon(o) in done for o in g)]


# ---------------- audit ----------------

def _choose_electives(group: dict, done: set[str], required: set[str]) -> list[str]:
    """Pick electives: already-completed first, then ones whose prerequisites the program covers."""
    outside = group.get("electives_with_outside_prerequisites") or {}
    cs = catalog()["courses"]
    pool = [canon(c) for c in group["courses"] if canon(c) in cs and cs[canon(c)]["status"] == "active"]
    picked, total = [], 0
    for c in sorted(pool, key=lambda c: (c not in done, c in outside, c)):
        if total >= group["credits"]:
            break
        picked.append(c)
        total += cs[c]["credits"]
    return picked


def required_courses(program: dict, done: set[str] = frozenset()) -> list[str]:
    req: list[str] = []
    for g in program["requirement_groups"]:
        if g["rule"] == "all":
            req += [canon(c) for c in g["courses"]]
    for g in program["requirement_groups"]:
        if g["rule"] == "choose_credits":
            req += [c for c in _choose_electives(g, set(done), set(req)) if c not in req]
    # pull in corequisite labs
    cs = catalog()["courses"]
    for c in list(req):
        for co in cs[c].get("corequisites") or []:
            if canon(co) not in req:
                req.append(canon(co))
    return list(dict.fromkeys(req))


def audit(program_code: str, completed=None) -> dict:
    p = get_program(program_code)
    done, unknown = _completed_set(completed)
    cs = catalog()["courses"]
    groups, earned_total = [], 0
    for g in p["requirement_groups"]:
        codes = [canon(c) for c in g["courses"]]
        if g["rule"] == "all":
            have = [c for c in codes if c in done]
            earned = _credits(have)
            remaining = [c for c in codes if c not in done]
            need = g["credits"]
        else:
            have = [c for c in codes if c in done]
            earned = min(_credits(have), g["credits"])
            remaining = [c for c in codes if c not in done] if earned < g["credits"] else []
            need = g["credits"]
        earned_total += min(earned, need)
        groups.append({
            "group": g["group"], "rule": g["rule"], "creditsRequired": need, "creditsEarned": min(earned, need),
            "complete": earned >= need, "completed": have,
            "remaining": [{"code": c, "title": cs[c]["title"], "credits": cs[c]["credits"],
                           "prerequisitesMet": _prereqs_met(c, done)} for c in remaining],
            **({"chooseCredits": g["credits"], "electivesWithOutsidePrerequisites": g.get("electives_with_outside_prerequisites", {})}
               if g["rule"] == "choose_credits" else {}),
        })
    total = p["total_credits"]
    return {
        "program": {"code": p["app_program_code"], "id": p["id"], "name": p["name"], "degree": p["degree"], "totalCredits": total},
        "creditsEarned": earned_total, "creditsRemaining": max(0, total - earned_total),
        "percentComplete": round(100 * earned_total / total) if total else 0,
        "groups": groups, "unknownCourses": unknown, "synthetic": True,
    }


# ---------------- plan ----------------

def _term_name(season: str, year: int) -> str:
    return f"{season} {year}"


def _term_seq(start: str, n: int, include_summer: bool):
    m = re.fullmatch(r"(Fall|Spring|Summer)\s+(\d{4})", (start or "").strip(), re.I)
    if not m:
        raise PlannerError("startTerm must look like 'Fall 2026', 'Spring 2027' or 'Summer 2027'.", "startTerm")
    season, year = m.group(1).title(), int(m.group(2))
    out = []
    while len(out) < n:
        if season != "Summer" or include_summer:
            out.append((season, year))
        season = SEASONS[(SEASONS.index(season) + 1) % 3]
        if season == "Spring":
            year += 1
    return out


def _depth(code: str, dependents: dict, memo: dict) -> int:
    if code in memo:
        return memo[code]
    memo[code] = 0
    memo[code] = 1 + max((_depth(d, dependents, memo) for d in dependents.get(code, ())), default=0)
    return memo[code]


def plan(program_code: str, completed=None, start_term: str = "Fall 2026", max_credits: int = 15,
         summer_credits: int = 6, include_summer: bool = True) -> dict:
    p = get_program(program_code)
    done, unknown = _completed_set(completed)
    if not isinstance(max_credits, int) or not 3 <= max_credits <= 21:
        raise PlannerError("maxCredits must be an integer between 3 and 21.", "maxCredits")
    if not isinstance(summer_credits, int) or not 0 <= summer_credits <= 15:
        raise PlannerError("summerCredits must be an integer between 0 and 15.", "summerCredits")
    cs = catalog()["courses"]
    need = [c for c in required_courses(p, done) if c not in done]
    need_set = set(need)

    dependents: dict[str, set] = {}
    for c in need:
        for g in cs[c].get("prerequisites") or []:
            for o in g:
                dependents.setdefault(canon(o), set()).add(c)
    memo: dict = {}
    priority = {c: _depth(c, dependents, memo) for c in need}

    # electives with prerequisites outside the program: add the missing prerequisite to the plan
    warnings = []
    for c in list(need):
        for g in _missing_prereqs(c, done | need_set):
            extra = canon(g[0])
            if extra in cs and extra not in need_set:
                need.append(extra)
                need_set.add(extra)
                priority[extra] = priority.get(c, 1) + 1
                warnings.append({"type": "outside_prerequisite", "course": c, "addedPrerequisite": extra,
                                 "message": f"{c} needs {extra}, which the program doesn't require. Added it to the plan."})

    have = set(done)
    terms_out, stalled = [], 0
    for season, year in _term_seq(start_term, 24, include_summer):
        if not need_set:
            break
        cap = summer_credits if season == "Summer" else max_credits
        if cap <= 0:
            continue
        credits_before = _credits(have)
        eligible = []
        for c in need_set:
            info = cs[c]
            if info["status"] != "active" or season not in info["terms_offered"]:
                continue
            if info.get("category") == "lab" and any(canon(co) in need_set for co in info.get("corequisites") or []):
                continue  # labs ride along with their lecture
            if not _prereqs_met(c, have):
                continue
            if info.get("min_credits_completed") and credits_before < info["min_credits_completed"]:
                continue
            eligible.append(c)
        eligible.sort(key=lambda c: (-priority.get(c, 0), cs[c].get("level") != "lower", c))
        chosen, load = [], 0
        for c in eligible:
            bundle = [c] + [canon(co) for co in cs[c].get("corequisites") or [] if canon(co) in need_set]
            cr = _credits(bundle)
            if load + cr <= cap:
                chosen += bundle
                load += cr
        if not chosen:
            stalled += 1
            if stalled >= 3:
                break
            continue
        stalled = 0
        term = _term_name(season, year)
        rows = []
        for c in chosen:
            info = cs[c]
            row = {"code": c, "title": info["title"], "credits": info["credits"]}
            notes = []
            if info.get("instructor_permission"):
                notes.append("instructor permission required")
            if info.get("min_credits_completed"):
                notes.append(f"needs {info['min_credits_completed']} credits completed")
            if len(info["terms_offered"]) == 1:
                notes.append(f"only offered in {info['terms_offered'][0]}")
            if info.get("cross_listed_as"):
                notes.append("cross-listed as " + ", ".join(info["cross_listed_as"]))
            if notes:
                row["notes"] = notes
            rows.append(row)
        terms_out.append({"term": term, "credits": load, "courses": rows})
        have |= set(chosen)
        need_set -= set(chosen)

    blocked = []
    for c in sorted(need_set):
        info = cs[c]
        reason = ("inactive course" if info["status"] != "active" else
                  "prerequisites not reachable: " + json.dumps(_missing_prereqs(c, have)) if not _prereqs_met(c, have) else
                  f"needs {info['min_credits_completed']} credits" if info.get("min_credits_completed") and _credits(have) < info["min_credits_completed"] else
                  "not offered in the planned terms")
        blocked.append({"code": c, "title": info["title"], "reason": reason})

    total_after = _credits(have)
    return {
        "program": {"code": p["app_program_code"], "name": p["name"], "totalCredits": p["total_credits"]},
        "startTerm": start_term, "maxCredits": max_credits, "includeSummer": include_summer,
        "creditsCompleted": _credits(done), "creditsPlanned": total_after - _credits(done),
        "creditsAtGraduation": total_after, "meetsTotalCredits": total_after >= p["total_credits"],
        "terms": terms_out, "termCount": len(terms_out),
        "graduationTerm": terms_out[-1]["term"] if terms_out and not blocked else None,
        "blocked": blocked, "warnings": warnings, "unknownCourses": unknown, "synthetic": True,
    }


# ---------------- schedule ----------------

def _minutes(hhmm: str) -> int:
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


def _overlap(a: dict, b: dict) -> bool:
    if a["term"] != b["term"] or not (a["start_date"] <= b["end_date"] and b["start_date"] <= a["end_date"]):
        return False
    for ma in a["meetings"]:
        for mb in b["meetings"]:
            if not ma.get("start") or not mb.get("start"):
                continue
            if set(ma["days"]) & set(mb["days"]) and _minutes(ma["start"]) < _minutes(mb["end"]) and _minutes(mb["start"]) < _minutes(ma["end"]):
                return True
    return False


def _section_view(s: dict) -> dict:
    keys = ("crn", "course_code", "title", "credits", "term", "session", "section_number", "campus", "modality",
            "meetings", "instructor", "capacity", "enrolled", "waitlist", "status", "linked_crn", "test_tags")
    v = {k: s.get(k) for k in keys}
    v["seatsOpen"] = max(0, (s.get("capacity") or 0) - (s.get("enrolled") or 0))
    return v


def _pref_ok(s: dict, prefs: dict) -> bool:
    if prefs.get("modality") and s["modality"] not in prefs["modality"]:
        return False
    for m in s["meetings"]:
        if not m.get("start"):
            continue
        if prefs.get("noEvening") and _minutes(m["start"]) >= 17 * 60:
            return False
        if prefs.get("noWeekend") and "S" in m["days"]:
            return False
        if set(prefs.get("avoidDays") or "") & set(m["days"]):
            return False
        if prefs.get("earliestStart") and _minutes(m["start"]) < _minutes(prefs["earliestStart"]):
            return False
    if prefs.get("campus") and s["modality"] != "online" and s["campus"] not in prefs["campus"]:
        return False
    return True


def sections_for(course: str, term: str | None = None) -> list[dict]:
    code = canon(course)
    out = []
    for (c, t), secs in catalog()["sections"].items():
        if c == code and (term is None or t == term):
            out += [_section_view(s) for s in secs]
    return sorted(out, key=lambda s: (s["term"], s["section_number"]))


def _validate_prefs(prefs) -> dict:
    if prefs is None:
        return {}
    if not isinstance(prefs, dict):
        raise PlannerError("preferences must be an object.", "preferences")
    out = {}
    if prefs.get("modality"):
        mods = prefs["modality"] if isinstance(prefs["modality"], list) else [prefs["modality"]]
        bad = [m for m in mods if m not in ("in_person", "online", "hybrid")]
        if bad:
            raise PlannerError("preferences.modality values: in_person, online, hybrid.", "preferences.modality")
        out["modality"] = mods
    for k in ("noEvening", "noWeekend", "allowWaitlist"):
        if k in prefs:
            if not isinstance(prefs[k], bool):
                raise PlannerError(f"preferences.{k} must be true or false.", f"preferences.{k}")
            out[k] = prefs[k]
    if prefs.get("avoidDays"):
        days = str(prefs["avoidDays"]).upper()
        if not re.fullmatch(r"[MTWRFS]+", days):
            raise PlannerError("preferences.avoidDays uses letters M T W R F S, e.g. 'F' or 'MW'.", "preferences.avoidDays")
        out["avoidDays"] = days
    if prefs.get("earliestStart"):
        if not re.fullmatch(r"\d{2}:\d{2}", str(prefs["earliestStart"])):
            raise PlannerError("preferences.earliestStart must be HH:MM, e.g. '09:00'.", "preferences.earliestStart")
        out["earliestStart"] = prefs["earliestStart"]
    if prefs.get("campus"):
        out["campus"] = prefs["campus"] if isinstance(prefs["campus"], list) else [prefs["campus"]]
    return out


def schedule(courses, term: str, preferences=None) -> dict:
    if not isinstance(courses, list) or not courses:
        raise PlannerError("courses must be a non-empty array of course codes.", "courses")
    if len(courses) > 8:
        raise PlannerError("Schedule at most 8 courses at once.", "courses")
    terms = [t["term"] for t in catalog()["terms"]]
    if term not in terms:
        raise PlannerError(f"term must be one of {terms}.", "term", validTerms=terms)
    prefs = _validate_prefs(preferences)
    allow_wait = prefs.get("allowWaitlist", True)
    cs, by_crn = catalog()["courses"], catalog()["by_crn"]

    codes = list(dict.fromkeys(canon(c) for c in courses))
    unknown = [c for c in codes if c not in cs]
    codes = [c for c in codes if c in cs]
    # labs linked to a lecture in the request are scheduled with that lecture
    lectures = {c for c in codes if any(canon(co) in codes for co in cs[c].get("corequisites") or []) and cs[c].get("category") != "lab"}
    labs_with_lecture = {canon(co) for c in lectures for co in cs[c].get("corequisites") or []}

    options, unscheduled = {}, []
    for c in codes:
        if c in labs_with_lecture:
            continue
        secs = catalog()["sections"].get((c, term), [])
        if not secs:
            unscheduled.append({"code": c, "reason": "not_offered", "message": f"{c} has no sections in {term}."})
            continue
        live = [s for s in secs if s["status"] != "cancelled"]
        if not live:
            unscheduled.append({"code": c, "reason": "cancelled", "message": f"Every {c} section in {term} is cancelled."})
            continue
        fit = [s for s in live if _pref_ok(s, prefs)]
        if not fit:
            unscheduled.append({"code": c, "reason": "preferences", "message": f"No {c} section matches your preferences in {term}.",
                                "alternatives": [_section_view(s) for s in live][:4]})
            continue
        open_ = [s for s in fit if s["status"] == "open"]
        pool = open_ or (fit if allow_wait else [])
        if not pool:
            unscheduled.append({"code": c, "reason": "full", "message": f"Every matching {c} section is full."})
            continue
        # open seats first, then shortest waitlist
        options[c] = sorted(pool, key=lambda s: (s["status"] != "open", s.get("waitlist") or 0, s["section_number"]))[:6]

    def bundle(s):
        out = [s]
        if s.get("linked_crn") and s["linked_crn"] in by_crn:
            out.append(by_crn[s["linked_crn"]])
        return out

    best, best_score = None, None
    keys = list(options)
    for combo in product(*(options[k] for k in keys)) if keys else [()]:
        flat = [x for s in combo for x in bundle(s)]
        clashes = sum(_overlap(a, b) for i, a in enumerate(flat) for b in flat[i + 1:])
        waits = sum(s["status"] != "open" for s in flat)
        score = (clashes, waits)
        if best_score is None or score < best_score:
            best, best_score = combo, score
            if score == (0, 0):
                break

    chosen, conflicts = [], []
    if best:
        flat = [x for s in best for x in bundle(s)]
        for i, a in enumerate(flat):
            for b in flat[i + 1:]:
                if _overlap(a, b):
                    conflicts.append({"crns": [a["crn"], b["crn"]], "courses": [a["course_code"], b["course_code"]],
                                      "message": f"{a['course_code']} and {b['course_code']} overlap in {term}. Take one in another term."})
        chosen = [_section_view(s) for s in flat]
    waitlisted = [s for s in chosen if s["status"] != "open"]
    return {
        "term": term, "preferences": prefs, "sections": chosen,
        "credits": sum(s["credits"] for s in chosen),
        "conflicts": conflicts, "waitlisted": [{"crn": s["crn"], "course": s["course_code"], "waitlist": s["waitlist"]} for s in waitlisted],
        "unscheduled": unscheduled, "unknownCourses": unknown,
        "ok": not conflicts and not unscheduled and not unknown, "synthetic": True,
    }


def program_summary() -> list[dict]:
    return [{"code": p["app_program_code"], "id": p["id"], "name": p["name"], "degree": p["degree"],
             "totalCredits": p["total_credits"], "groups": [{"group": g["group"], "rule": g["rule"], "credits": g["credits"],
                                                              "courses": len(g["courses"])} for g in p["requirement_groups"]]}
            for p in catalog()["program_list"]]


def program_detail(code: str) -> dict:
    p = get_program(code)
    cs = catalog()["courses"]
    return {
        "code": p["app_program_code"], "id": p["id"], "name": p["name"], "degree": p["degree"],
        "totalCredits": p["total_credits"], "minGpa": p.get("min_gpa"), "minGradeInMajor": p.get("min_grade_in_major"),
        "requirementGroups": [{**{k: v for k, v in g.items() if k != "courses"},
                               "courses": [course_info(c) or {"code": c, "missing": True} for c in g["courses"]]}
                              for g in p["requirement_groups"]],
        "synthetic": True,
    }


# ---------------- Student Hub dataset (feeds mdc-pathways/student-hub.html) ----------------

# Transfer destinations shown on the hub's Transfer tab. Rates are rough per-credit tuition figures.
DESTS = [
    {"id": 0, "name": "Florida public university", "rate": 210,
     "note": "<b>Why most credits move:</b> Florida public colleges and universities share one course numbering "
             "system, so a course with the same prefix and number usually transfers as the same course. Specialized "
             "program courses can arrive as electives when the new major has no matching course."},
    {"id": 1, "name": "Private university", "rate": 1900,
     "note": "<b>Why more is lost:</b> each private school decides course by course, and many don't accept "
             "internships, labs or advanced technical courses. Ask for an unofficial credit evaluation before you "
             "apply, and get it in writing."},
    {"id": 2, "name": "Out-of-state public university", "rate": 1100,
     "note": "<b>Why it varies:</b> there's no Florida articulation agreement across state lines. Most schools "
             "publish a transfer equivalency database; look up each course code there. Out-of-state tuition also "
             "makes every lost credit cost more to repeat."},
]

REASONS = {
    "gen_ed": "General education transfers almost everywhere",
    "common_core": "Standard intro technology course",
    "lower": "Lower-level major course; outside Florida it often lands as an elective",
    "upper": "Upper-level major course; schools outside Florida rarely match it",
    "permission": "Internships and permission-only courses usually don't transfer",
    "lab": "Labs follow their lecture course",
}


def transfer_rule(course: dict) -> tuple[list[str], str]:
    """Rules-based estimate of how a course transfers to [FL public, private, out-of-state public]."""
    cat, level = course.get("category"), course.get("level")
    if course.get("instructor_permission") or (course.get("min_credits_completed") or 0) >= 60:
        return ["elective", "none", "none"], REASONS["permission"]
    if cat == "gen_ed":
        return ["full", "full", "full"], REASONS["gen_ed"]
    if cat == "common_core":
        return ["full", "elective", "full"], REASONS["common_core"]
    if cat == "lab":
        return ["full", "none", "elective"], REASONS["lab"]
    if level == "upper":
        return ["full", "elective", "none"], REASONS["upper"]
    return ["full", "elective", "elective"], REASONS["lower"]


GROUP_IDS = {"General Education": "gen", "Common Technology Core": "common", "Program Foundations": "found",
             "Program Core": "core", "Capstone and Internship": "cap", "Electives": "elect"}


def hub(program_code: str, completed=None, in_progress=None, grades=None, terms=None, name: str | None = None,
        current_term: str = "Fall 2026", load: int = 15) -> dict:
    """Everything the Student Hub page renders, computed from the synthetic catalog."""
    p = get_program(program_code)
    done_set, unknown = _completed_set(completed)
    now_set, unknown2 = _completed_set(in_progress)
    now_set -= done_set
    if grades is not None and not isinstance(grades, dict):
        raise PlannerError("grades must be an object {courseCode: grade}.", "grades")
    if terms is not None and not isinstance(terms, dict):
        raise PlannerError("terms must be an object {courseCode: term}.", "terms")
    grades = {canon(k): str(v).upper()[:3] for k, v in (grades or {}).items()}
    terms = {canon(k): str(v)[:20] for k, v in (terms or {}).items()}
    cs = catalog()["courses"]

    # which requirement group each course counts toward
    group_of: dict[str, str] = {}
    groups = []
    for g in p["requirement_groups"]:
        gid = GROUP_IDS.get(g["group"], re.sub(r"[^a-z]", "", g["group"].lower())[:8])
        groups.append({"id": gid, "label": g["group"], "need": g["credits"]})
        for c in g["courses"]:
            group_of.setdefault(canon(c), gid)
    for c in list(group_of):
        for co in cs.get(c, {}).get("corequisites") or []:
            group_of.setdefault(canon(co), group_of[c])

    # planned remaining courses, term by term, starting after the current term
    m = re.fullmatch(r"(Fall|Spring|Summer)\s+(\d{4})", current_term)
    nxt_season, nxt_year = (m.group(1), int(m.group(2))) if m else ("Fall", 2026)
    nxt_season = SEASONS[(SEASONS.index(nxt_season) + 1) % 3]
    if nxt_season == "Spring":
        nxt_year += 1
    if nxt_season == "Summer":
        nxt_season, nxt_year = "Fall", nxt_year
    the_plan = plan(p["app_program_code"], sorted(done_set | now_set), f"{nxt_season} {nxt_year}", load, 0, False)

    courses = []

    def add(code, st, term):
        info = cs[code]
        t, why = transfer_rule(info)
        courses.append({"code": code, "title": info["title"], "cr": info["credits"], "g": group_of.get(code, "elect"),
                        "st": st, "term": term, "grade": grades.get(code) if st == "done" else None, "t": t, "why": why})

    for code in sorted(done_set, key=lambda c: (terms.get(c, "zz"), c)):
        add(code, "done", terms.get(code, "Completed"))
    for code in sorted(now_set):
        add(code, "now", current_term)
    for term in the_plan["terms"]:
        for c in term["courses"]:
            add(c["code"], "next", term["term"])

    return {
        "student": {"name": (name or "You")[:60], "program": p["name"], "credential": "B.S.",
                    "programCode": p["app_program_code"], "required": p["total_credits"],
                    "currentTerm": current_term, "startTerm": None},
        "groups": groups,
        "courses": courses,
        "dests": [{**d, "degree": f"B.S. {p['name']}", "total": p["total_credits"]} for d in DESTS],
        "reasons": {"full": "Matches a required course", "elective": "Accepted, but no matching course in the major",
                    "none": "No equivalent course; not accepted"},
        "graduationTerm": the_plan["graduationTerm"],
        "unknownCourses": unknown + unknown2,
        "synthetic": True,
    }
