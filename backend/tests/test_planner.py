"""Planner endpoints against the synthetic catalog's documented edge cases."""
import pytest

PROGRAMS = ["AI", "DATA", "CYBER", "SWE", "NET", "ECE"]


def test_programs_and_terms(client):
    progs = client.get("/api/programs").get_json()
    assert [p["code"] for p in progs["programs"]] == PROGRAMS and progs["synthetic"] is True
    terms = [t["term"] for t in client.get("/api/terms").get_json()["terms"]]
    assert terms == ["Fall 2026", "Spring 2027", "Summer 2027"]
    assert client.get("/api/health").get_json()["catalog"] is True


def test_program_detail(client):
    d = client.get("/api/programs/AI").get_json()
    assert d["totalCredits"] == 120 and d["requirementGroups"][0]["group"] == "General Education"
    assert client.get("/api/programs/SYN-AI").status_code == 200  # id alias
    r = client.get("/api/programs/NURSING")
    assert r.status_code == 404 and "AI" in r.get_json()["validPrograms"]


def test_course_detail_aliases_and_sections(client):
    for code in ("ZAI 3200", "zai3200", "ZDA 3200"):  # spacing, case, cross-listing
        d = client.get(f"/api/courses/{code}").get_json()
        assert d["code"] == "ZAI 3200" and d["cross_listed_as"] == ["ZDA 3200"]
    d = client.get("/api/courses/ZEE 2100?term=Fall 2026").get_json()
    assert d["sections"] and all(s["term"] == "Fall 2026" for s in d["sections"])
    assert client.get("/api/courses/ZZZ 9999").status_code == 404


@pytest.mark.parametrize("program", PROGRAMS)
def test_full_plan_reaches_120_credits(client, program):
    p = client.post("/api/plan", json={"program": program}).get_json()
    assert p["meetsTotalCredits"] and not p["blocked"] and p["graduationTerm"]
    for t in p["terms"]:
        cap = 6 if t["term"].startswith("Summer") else 15
        assert t["credits"] <= cap


@pytest.mark.parametrize("program", PROGRAMS)
def test_plan_respects_prerequisites_and_terms(client, program):
    import planner
    p = client.post("/api/plan", json={"program": program}).get_json()
    cs = planner.catalog()["courses"]
    taken, credits = set(), 0
    for t in p["terms"]:
        season = t["term"].split()[0]
        codes = [c["code"] for c in t["courses"]]
        for code in codes:
            info = cs[code]
            assert season in info["terms_offered"], f"{code} not offered in {season}"
            for group in info["prerequisites"]:
                assert any(planner.canon(o) in taken for o in group), f"{code} before its prerequisites {group}"
            if info.get("min_credits_completed"):
                assert credits >= info["min_credits_completed"], f"{code} before {info['min_credits_completed']} credits"
            for co in info.get("corequisites") or []:
                assert planner.canon(co) in codes or planner.canon(co) in taken, f"{code} without corequisite {co}"
        taken |= set(codes)
        credits += t["credits"]


def test_plan_skips_completed_and_shortens(client):
    full = client.post("/api/plan", json={"program": "DATA"}).get_json()
    first_two = [c["code"] for t in full["terms"][:2] for c in t["courses"]]
    later = client.post("/api/plan", json={"program": "DATA", "completed": first_two}).get_json()
    assert later["termCount"] < full["termCount"]
    assert not {c["code"] for t in later["terms"] for c in t["courses"]} & set(first_two)


def test_plan_no_summer_takes_longer(client):
    a = client.post("/api/plan", json={"program": "CYBER"}).get_json()
    b = client.post("/api/plan", json={"program": "CYBER", "includeSummer": False}).get_json()
    assert not any(t["term"].startswith("Summer") for t in b["terms"]) and b["termCount"] <= a["termCount"] + 3


def test_plan_flags_permission_and_single_term(client):
    p = client.post("/api/plan", json={"program": "AI"}).get_json()
    notes = [n for t in p["terms"] for c in t["courses"] for n in c.get("notes", [])]
    assert any("permission" in n for n in notes) and any("only offered" in n for n in notes)


@pytest.mark.parametrize("payload,field", [
    ({"program": "AI", "maxCredits": 40}, "maxCredits"),
    ({"program": "AI", "startTerm": "next year"}, "startTerm"),
    ({"program": "AI", "completed": "ZEN 1101"}, "completed"),
    ({"program": "AI", "includeSummer": "no"}, "includeSummer"),
    ({"program": "XYZ"}, "program"),
])
def test_plan_validation(client, payload, field):
    r = client.post("/api/plan", json=payload)
    assert r.status_code == 400 and r.get_json()["field"] == field


def test_audit(client):
    a = client.post("/api/audit", json={"program": "AI", "completed": ["ZEN 1101", "zen1102", "ZDA 3200", "FAKE 0000"]}).get_json()
    assert a["creditsEarned"] == 9 and a["unknownCourses"] == ["FAKE 0000"]
    gen = a["groups"][0]
    assert gen["group"] == "General Education" and gen["creditsEarned"] == 6
    assert all("prerequisitesMet" in c for c in gen["remaining"])
    assert any(g["rule"] == "choose_credits" and g["electivesWithOutsidePrerequisites"] for g in a["groups"])


# ---------- schedule edge cases ----------

def sched(client, courses, term, prefs=None):
    return client.post("/api/schedule", json={"courses": courses, "term": term, "preferences": prefs}).get_json()


def test_schedule_reports_time_conflict_pair(client):
    s = sched(client, ["ZAI 3300", "ZAI 4200"], "Spring 2027")
    assert not s["ok"] and s["conflicts"] and set(s["conflicts"][0]["courses"]) == {"ZAI 3300", "ZAI 4200"}


def test_schedule_all_sections_full(client):
    s = sched(client, ["ZSE 2400"], "Fall 2026")
    assert s["waitlisted"] and s["waitlisted"][0]["course"] == "ZSE 2400"
    s = sched(client, ["ZSE 2400"], "Fall 2026", {"allowWaitlist": False})
    assert s["unscheduled"][0]["reason"] == "full"


def test_schedule_pairs_lab_with_lecture(client):
    s = sched(client, ["ZEE 2100", "ZEE 2100L"], "Fall 2026")
    lec = next(x for x in s["sections"] if x["course_code"] == "ZEE 2100")
    lab = next(x for x in s["sections"] if x["course_code"] == "ZEE 2100L")
    assert lec["linked_crn"] == lab["crn"] and lab["linked_crn"] == lec["crn"]
    # lecture alone still brings its linked lab
    s = sched(client, ["ZEE 2100"], "Fall 2026")
    assert {x["course_code"] for x in s["sections"]} == {"ZEE 2100", "ZEE 2100L"}


def test_schedule_never_picks_cancelled(client):
    s = sched(client, ["ZHU 1020"], "Spring 2027")
    assert s["sections"] and all(x["status"] != "cancelled" for x in s["sections"])


def test_schedule_preferences(client):
    s = sched(client, ["ZEN 1101", "ZCP 1000"], "Fall 2026", {"modality": ["online"], "noEvening": True})
    assert s["ok"] and all(x["modality"] == "online" for x in s["sections"])
    s = sched(client, ["ZAH 2020"], "Fall 2026", {"noWeekend": True, "avoidDays": "F"})
    assert all("S" not in m["days"] and "F" not in m["days"] for x in s["sections"] for m in x["meetings"])


def test_schedule_not_offered_and_unknown(client):
    s = sched(client, ["ZEE 4570", "NOPE 1234"], "Fall 2026")
    assert s["unscheduled"][0]["code"] == "ZEE 4570" and s["unknownCourses"] == ["NOPE 1234"] and not s["ok"]


def test_schedule_clean_first_semester(client):
    s = sched(client, ["ZEN 1101", "ZMA 1105", "ZCP 1000", "ZCS 1100", "ZSC 1005"], "Fall 2026")
    assert s["ok"] and s["credits"] >= 15 and not s["conflicts"]


@pytest.mark.parametrize("payload,field", [
    ({"courses": [], "term": "Fall 2026"}, "courses"),
    ({"courses": ["ZEN 1101"] * 9, "term": "Fall 2026"}, "courses"),
    ({"courses": ["ZEN 1101"], "term": "Winter 2026"}, "term"),
    ({"courses": ["ZEN 1101"], "term": "Fall 2026", "preferences": {"modality": "zoom"}}, "preferences.modality"),
    ({"courses": ["ZEN 1101"], "term": "Fall 2026", "preferences": {"earliestStart": "9am"}}, "preferences.earliestStart"),
])
def test_schedule_validation(client, payload, field):
    r = client.post("/api/schedule", json=payload)
    assert r.status_code == 400 and r.get_json()["field"] == field
