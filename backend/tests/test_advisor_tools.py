"""High-school transcripts, plan preview, school lookup (with SSRF guard), what-if analysis."""
import json

import pytest

HS = """Algebra II A
AP Calculus AB A-
AP Computer Science A A
English 3 B
US History B+
Physics Honors A
Spanish 2 C
Art 1 B"""


def test_high_school_transcript_strengths(client):
    t = client.post("/api/transcript", json={"text": HS}).get_json()
    assert t["level"] == "high_school" and t["completed"] == []
    s = t["strengths"]
    assert s["strong"][:3] and "Math" in s["strong"] and "Computer science" in s["strong"]
    codes = [p["code"] for p in s["suggestedPrograms"]]
    assert codes and codes[0] in ("AI", "SWE", "ECE") and "why" in s["suggestedPrograms"][0]
    assert 3.0 <= s["gpa"] <= 4.0


def test_college_transcript_also_has_strengths(client):
    t = client.post("/api/transcript", json={"text": "ZEN 1101 English Composition I A\nZMA 1105 College Algebra B"}).get_json()
    assert t["level"] == "college" and t["completed"] == ["ZEN 1101", "ZMA 1105"] and "strengths" in t


def test_plan_preview_offline(client):
    p = client.post("/api/plan/preview", json={"program": "AI", "strengths": {"strong": ["Math", "Computer science"]}}).get_json()
    assert p["program"]["code"] == "AI" and len(p["firstTerms"]) == 2 and p["graduationTerm"]
    assert p["creditsLeft"] == 120 and p["estimatedCost"] == 120 * p["ratePerCredit"]
    assert "math" in p["why"].lower()
    assert client.post("/api/plan/preview", json={"program": "NOPE"}).status_code == 400


def test_plan_preview_with_ai(client, monkeypatch):
    import llm
    monkeypatch.setattr(llm, "available_providers", lambda: ["prune"])
    monkeypatch.setattr(llm, "complete", lambda *a, **k: (json.dumps({"why": "Your A in AP CS fits AI.", "skills": ["logic"],
                                                                     "firstSteps": ["Join the AI club"]}), "prune/test"))
    p = client.post("/api/plan/preview", json={"program": "AI"}).get_json()
    assert p["why"] == "Your A in AP CS fits AI." and p["skills"] == ["logic"] and p["engine"]["name"] == "llm"


def test_whatif_between_programs(client):
    w = client.post("/api/whatif", json={"program": "AI", "completed": ["ZEN 1101", "ZMA 1105", "ZCP 1000", "ZAI 1010"],
                                         "target": "Cybersecurity"}).get_json()
    assert w["target"]["kind"] == "catalog" and w["target"]["title"] == "Cybersecurity"
    assert w["target"]["creditsCarryOver"] >= 9 and w["target"]["creditsLost"] >= 3      # ZAI 1010 doesn't count for CYBER
    assert w["timing"] == "early" and w["verdict"] and w["headline"] and w["advice"]
    assert w["current"]["percent"] < 25


def test_whatif_to_outside_career(client, monkeypatch):
    import llm
    monkeypatch.setattr(llm, "available_providers", lambda: ["prune"])
    calls = []

    def fake(messages, **k):
        calls.append(messages[0]["content"][:30])
        if len(calls) == 1:
            return json.dumps({"title": "Physician", "steps": ["Bachelor's (pre-med)", "MD (4 years)", "Residency (3-7 years)"],
                               "yearsFromStart": 12, "typicalTotalCostUSD": 250000, "medianSalaryUSD": 239200,
                               "jobOutlook": "As fast as average", "prereqNotes": "Biology and chemistry with labs."}), "prune/t"
        return json.dumps({"verdict": "finish_then_pivot", "headline": "You're close: finish, then pre-med.",
                           "advice": "Finish your B.S., then a post-bacc pre-med.", "nextSteps": ["Shadow a doctor"]}), "prune/t"

    monkeypatch.setattr(llm, "complete", fake)
    done = ["ZEN 1101", "ZEN 1102", "ZMA 1105", "ZST 2023", "ZAH 2020", "ZHU 1020", "ZSC 1005", "ZSP 2600", "ZPS 2012"]
    w = client.post("/api/whatif", json={"program": "AI", "completed": done, "target": "doctor"}).get_json()
    t = w["target"]
    assert t["kind"] == "career" and t["title"] == "Physician" and t["estimate"] is True
    assert t["creditsCarryOver"] == 27 and t["yearsToCareer"] < 12      # gen-ed carries over
    assert w["verdict"] == "finish_then_pivot" and w["nextSteps"] == ["Shadow a doctor"]


def test_whatif_validation(client):
    assert client.post("/api/whatif", json={"program": "AI", "target": ""}).status_code == 400
    assert client.post("/api/whatif", json={"program": "NOPE", "target": "Data"}).status_code == 400


@pytest.mark.parametrize("url", ["http://127.0.0.1:5000", "http://localhost/", "http://10.1.2.3/", "http://192.168.0.1/",
                                 "ftp://example.com", "http://example.com:8080/x"])
def test_school_lookup_blocks_private_and_odd_urls(client, url):
    r = client.post("/api/schools/lookup", json={"url": url})
    assert r.status_code == 422 and r.get_json()["error"] == "school_unreadable"


def test_school_lookup_parses_a_page(client, monkeypatch):
    import advisor_tools
    html = ("<html><head><title>Transfer Admissions | Florida International University</title></head><body>"
            "<nav>menu</nav><h1>Transfer to FIU</h1><p>Tuition is $205.57 per credit hour for Florida residents.</p>"
            + "<p>Transfer students with an AA from a Florida college are guaranteed admission.</p>" * 5 + "</body></html>")
    monkeypatch.setattr(advisor_tools, "_fetch_public", lambda url, max_bytes=0: (html, "https://admissions.fiu.edu/transfer"))
    s = client.post("/api/schools/lookup", json={"url": "admissions.fiu.edu/transfer"}).get_json()
    assert s["name"].startswith("Transfer Admissions") and s["rate"] == 206
    assert s["type"] == "florida_public" and s["typeIndex"] == 0 and s["sourceUrl"].startswith("https://")


def test_chat_accepts_transcript_context(client, monkeypatch):
    import llm
    seen = {}
    monkeypatch.setattr(llm, "available_providers", lambda: ["prune"])
    monkeypatch.setattr(llm, "complete", lambda messages, **k: (seen.setdefault("s", messages[0]["content"]) and
                                                                '{"chatResponse": "What do you enjoy about math?"}', "prune/t"))
    client.post("/api/chat", json={"chatHistory": [{"sender": "user", "text": "hi"}],
                                   "context": {"strengths": {"strong": ["Math", "Physics"], "gpa": 3.7,
                                                             "suggestedPrograms": [{"name": "Electrical & Computer Engineering"}]},
                                               "level": "high_school"}})
    assert "Strongest subjects from their transcript: Math, Physics" in seen["s"] and "Electrical & Computer Engineering" in seen["s"]


def test_template_cache_hit_is_asked_again_without_prune(monkeypatch):
    """Prune's template cache can return another student's numbers: personal answers are re-asked uncached."""
    import advisor_tools
    import llm
    calls = []

    def fake(msgs, **k):
        calls.append(k.get("skip", ()))
        if not k.get("skip"):
            k["meta_out"]["prune"] = {"cacheHit": True, "cacheType": "template_semantic"}
            return json.dumps({"advice": "stale"}), "prune/x"
        return json.dumps({"advice": "fresh"}), "gemini/x"
    monkeypatch.setattr(llm, "available_providers", lambda: ["prune", "gemini"])
    monkeypatch.setattr(llm, "complete", fake)
    data, used, _ = advisor_tools._ai_json("sys", "user")
    assert data == {"advice": "fresh"} and used == "gemini/x" and calls == [(), ("prune",)]


def test_dollar_amounts_are_not_redacted_as_ids():
    import safety
    out = safety.scrub_output("Median pay is $108020, about 108020 dollars. Student ID 12345678.", [])
    assert "$108020" in out and "108020 dollars" in out and "12345678" not in out
