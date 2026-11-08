"""Real MDC program sheets (S9520 B.S., 25080 A.S.) and the transfer universities (FIU, UM, UCF, USF)."""
import planner
import transcript

REAL_TRANSCRIPT = "ENC 1101 A\nMAC 1105 B+\nCAI 1001C A\nCGS 1060C A-\nCOP 1047C A\nSTA 2023 B\nMAC 1114 D\nCAI 2100C IP"


def test_real_programs_match_the_official_sheets():
    bs, as_ = planner.get_program("AIBS"), planner.get_program("AIAS")
    assert bs["total_credits"] == 120 and bs["sheet_code"] == "S9520" and bs["synthetic"] is False
    assert as_["total_credits"] == 60 and as_["sheet_code"] == "25080"
    assert sum(g["credits"] for g in bs["requirement_groups"]) == 120
    core = next(g for g in bs["requirement_groups"] if g["group"] == "Upper Division Core")
    assert "CAI 4950C" in core["courses"] and core["credits"] == 31
    assert planner.course_info("CAI 4505C")["prerequisites"] == [["CAI 3822C"], ["COP 3530"]]


def test_plan_respects_real_prerequisites():
    p = planner.plan("AIBS", ["ENC 1101", "MAC 1105", "COP 1047C", "CAI 1001C", "STA 2023"], "Spring 2027", 15, 6, True)
    seen = set()
    for term in p["terms"]:
        codes = [c["code"] for c in term["courses"]]
        if "CAI 4505C" in codes:
            assert {"CAI 3822C", "COP 3530"} <= seen
        seen |= set(codes)
    assert p["creditsPlanned"] > 0 and p["graduationTerm"]


def test_transcript_with_real_mdc_codes():
    t = transcript.read(text=REAL_TRANSCRIPT)
    assert t["level"] == "college" and "CAI 1001C" in t["completed"] and t["realCourses"] >= 6
    assert [c["code"] for c in t["notCounted"]] == ["MAC 1114"]       # D doesn't count
    top = t["strengths"]["suggestedPrograms"][0]
    assert top["code"] in ("AIBS", "AIAS") and top["official"] is True


def test_hub_shows_real_universities_course_by_course():
    h = planner.hub("AIBS", ["ENC 1101", "CAI 1001C", "MAC 1105", "COP 3530"], [], {}, {}, "Sam", "Fall 2026", 15)
    names = [d["name"] for d in h["dests"]]
    assert {"Florida International University", "University of Miami", "University of Central Florida",
            "University of South Florida"} <= set(names)
    fiu = names.index("Florida International University")
    um = names.index("University of Miami")
    by = {c["code"]: c for c in h["courses"]}
    assert by["MAC 1105"]["t"][fiu] == "full" and "program sheet" in by["MAC 1105"]["whyAt"][fiu - 3]
    assert by["CAI 1001C"]["t"][um] == "full" and "CSC 145" in by["CAI 1001C"]["whyAt"][um - 3]
    assert by["COP 3530"]["t"][fiu] == "elective"
    assert h["official"] is True and h["student"]["credential"] == "B.S."
    assert h["dests"][fiu]["rate"] == 206    # FIU's published $205.57 a credit


def test_tuition_rates_come_from_official_pages():
    unis = {u["id"]: u for u in planner.universities()}
    assert unis["fiu"]["rate"] == 205.57 and unis["ucf"]["rate"] == 212.28
    assert all(u["tuitionSource"].startswith("https://") for u in unis.values())
    assert planner.mdc_rates()["lowerDivision"] == 118.22
