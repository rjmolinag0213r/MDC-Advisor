"""The MDC Pathways website wiring: /api/hub, /api/config, static pages and sample files."""
import pytest

SAMPLE = ["ZEN 1101", "ZMA 1105", "ZCP 1000", "ZCS 1100", "ZSC 1005", "ZEN 1102", "ZCP 2006", "ZNT 1110"]


def test_hub_dataset_shape(client):
    r = client.post("/api/hub", json={"program": "AI", "completed": SAMPLE, "inProgress": ["ZAI 1010"],
                                      "grades": {"ZEN 1101": "A"}, "terms": {"ZEN 1101": "Fall 2026"}, "name": "Alex Rivera"})
    assert r.status_code == 200
    d = r.get_json()
    assert d["student"]["required"] == 120 and d["student"]["programCode"] == "AI" and d["student"]["name"] == "Alex Rivera"
    assert [g["need"] for g in d["groups"]] and sum(g["need"] for g in d["groups"]) == 120
    st = {c["st"] for c in d["courses"]}
    assert st == {"done", "now", "next"}
    done = [c for c in d["courses"] if c["st"] == "done"]
    assert {c["code"] for c in done} == set(SAMPLE)
    assert next(c for c in done if c["code"] == "ZEN 1101")["grade"] == "A"
    for c in d["courses"]:
        assert len(c["t"]) == 3 and set(c["t"]) <= {"full", "elective", "none"} and c["why"]
    assert len(d["dests"]) == 3 and all(x["rate"] > 0 for x in d["dests"])
    assert d["graduationTerm"] and d["synthetic"] is True


def test_hub_gen_ed_transfers_everywhere(client):
    d = client.post("/api/hub", json={"program": "DATA", "completed": ["ZEN 1101"]}).get_json()
    eng = next(c for c in d["courses"] if c["code"] == "ZEN 1101")
    assert eng["t"] == ["full", "full", "full"]


def test_hub_strips_pii_from_name(client):
    d = client.post("/api/hub", json={"program": "AI", "completed": [], "name": "call 305-555-0147"}).get_json()
    assert "305-555-0147" not in d["student"]["name"]


@pytest.mark.parametrize("payload,field", [
    ({"program": "NOPE"}, "program"),
    ({"program": "AI", "grades": "A"}, "grades"),
    ({"program": "AI", "load": 40}, "load"),
])
def test_hub_validation(client, payload, field):
    r = client.post("/api/hub", json=payload)
    assert r.status_code == 400 and r.get_json()["field"] == field


def test_config(client):
    c = client.get("/api/config").get_json()
    assert c["auth0"] is None and c["demoAuth"] is True      # tests run with Auth0 off
    assert [p["code"] for p in c["programs"]] == ["AI", "DATA", "CYBER", "SWE", "NET", "ECE"]


def test_site_pages_served(client):
    for path in ("/", "/index.html", "/explore.html", "/student-hub.html", "/login.html", "/account.html",
                 "/js/nextstop.js", "/js/explore.js", "/images/mdc-hero.png"):
        assert client.get(path).status_code == 200, path
    assert b"MDC Pathways" in client.get("/").data
    assert client.get("/some/deep/link").status_code == 200       # falls back to index.html


def test_samples_route(client):
    r = client.get("/samples/sample_transcript.png")
    assert r.status_code == 200 and r.data[:4] == b"\x89PNG"
    assert client.get("/samples/make_sample_transcript.py").status_code == 404
    assert client.get("/samples/../app.py").status_code == 404


def test_careers_include_fields_for_cards(client):
    c = client.get("/api/careers").get_json()["careers"][0]
    assert {"credential", "careers", "keywords"} <= set(c)
