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


def test_real_courses_never_count_toward_a_sample_program():
    """A real-MDC transcript planned against a Z program must not show credits it can't use (the 96% / 0-of-36 bug)."""
    real = ["ENC 1101", "MAC 1105", "CAI 1001C", "COP 1047C", "CGS 1060C", "STA 2023"]
    h = planner.hub("AI", real, [], {}, {}, "x", "Fall 2026", 15)
    assert not [c for c in h["courses"] if c["st"] == "done"]
    assert set(real) <= set(h["otherCatalogCourses"])


def test_possible_paths_rank_by_credits_that_carry_over(client):
    done = ["ENC 1101", "MAC 1105", "CAI 1001C", "COP 1047C", "CGS 1060C", "STA 2023", "PSY 2012", "CAI 2100C"]
    r = client.post("/api/paths", json={"program": "AIBS", "completed": done}).get_json()
    assert r["approved"]["code"] == "AIBS" and r["paths"]
    codes = [p["code"] for p in r["paths"]]
    assert "AIBS" not in codes and codes[0] == "AIAS"           # the A.S. stacks into the B.S.
    carry = [p["creditsCarryOver"] for p in r["paths"]]
    assert carry == sorted(carry, reverse=True)
    assert all(p["estimate"] for p in r["paths"] if not p["official"])   # sample programs matched by title: estimates


def test_advisor_name_is_not_redacted_from_replies():
    import safety
    assert safety.scrub_output("I'm Finn Shark, your advisor. Call (305) 237-8888.", []).startswith("I'm Finn Shark")
    # student input still loses self-introduced names
    assert "[name]" in safety.redact_pii("Hi, I'm Maria Lopez, from Hialeah")[0]


def test_chat_retries_without_cache_when_it_knows_the_student(monkeypatch):
    import app as appmod
    import llm
    calls = []

    def fake(msgs, **k):
        calls.append(k.get("skip", ()))
        if not k.get("skip"):
            k["meta_out"]["prune"] = {"cacheHit": True}
            return '{"chatResponse": "I am NextStop, what subjects do you like?"}', "prune/x"
        return '{"chatResponse": "Doing great! Ready for MAC 1105 next term?"}', "gemini/x"
    monkeypatch.setattr(llm, "available_providers", lambda: ["prune", "gemini"])
    monkeypatch.setattr(llm, "complete", fake)
    out = appmod._llm_chat([{"role": "user", "content": "how are you"}], "\n\nWhat you remember: likes math")
    assert calls == [(), ("prune",)] and "MAC 1105" in out["chatResponse"]
    calls.clear()
    appmod._llm_chat([{"role": "user", "content": "how are you"}], "")     # nothing personal: cache is fine
    assert calls == [()]
