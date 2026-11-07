"""Transcript reading, saved progress (Auth0 / demo), stats, Prune metadata, Swarms agent steps."""
import io
import json
import time

import pytest

TEXT_TRANSCRIPT = """Unofficial Transcript - Student: Jane Doe  ID 6602817
Fall 2026
ZEN 1101  English Composition I        A   3
ZMA 1105  College Algebra              B+  3
ZCP 1000  Intro to Programming         D   3
Spring 2027
ZEN 1102  English Composition II       W   3
ZCS 1100  Computer Concepts            C   3
ABC 9999  Transfer elective            A   3
ZST 2023  Statistics                   IP  3
"""


# ---------- transcript ----------

def test_transcript_text(client):
    r = client.post("/api/transcript", json={"text": TEXT_TRANSCRIPT, "program": "AI"})
    assert r.status_code == 200
    d = r.get_json()
    assert d["completed"] == ["ZEN 1101", "ZMA 1105", "ZCS 1100"]  # IP is listed but not completed
    assert {c["code"] for c in d["notCounted"]} == {"ZCP 1000", "ZEN 1102"}  # D and W
    assert [c["code"] for c in d["notInCatalog"]] == ["ABC 9999"]
    assert d["audit"]["creditsEarned"] == 9 and d["plan"]["terms"]
    dumped = json.dumps(d)
    assert "Jane Doe" not in dumped and "6602817" not in dumped


def test_transcript_image_uses_gemini(client, monkeypatch):
    import llm
    seen = {}

    def fake_vision(prompt, data, mime, **kw):
        seen["mime"] = mime
        return json.dumps({"courses": [{"code": "zen1101", "grade": "A"}, {"code": "ZDA 3200", "grade": "B"}]}), "gemini/test"

    monkeypatch.setattr(llm, "gemini_vision", fake_vision)
    png = b"\x89PNG\r\n\x1a\n" + b"0" * 100
    r = client.post("/api/transcript", data={"file": (io.BytesIO(png), "t.png"), "program": "DATA"},
                    content_type="multipart/form-data")
    d = r.get_json()
    assert r.status_code == 200 and seen["mime"] == "image/png" and d["engine"]["name"] == "gemini"
    assert d["completed"] == ["ZEN 1101", "ZAI 3200"]  # cross-listed alias resolved
    assert "audit" in d


def test_transcript_image_without_gemini_is_503(client):
    png = b"\x89PNG\r\n\x1a\n" + b"0" * 100
    r = client.post("/api/transcript", data={"file": (io.BytesIO(png), "t.png")}, content_type="multipart/form-data")
    assert r.status_code == 503 and r.get_json()["error"] == "vision_unavailable"


def test_transcript_rejects_bad_files(client):
    r = client.post("/api/transcript", data={"file": (io.BytesIO(b"MZ\x90 not an image"), "x.exe")}, content_type="multipart/form-data")
    assert r.status_code == 415
    big = b"%PDF" + b"0" * (5 * 1024 * 1024 + 10)
    r = client.post("/api/transcript", data={"file": (io.BytesIO(big), "big.pdf")}, content_type="multipart/form-data")
    assert r.status_code == 413
    r = client.post("/api/transcript", data={"other": "x"}, content_type="multipart/form-data")
    assert r.status_code == 400
    assert client.post("/api/transcript", json={"text": ""}).status_code == 400


# ---------- saved progress ----------

def test_me_requires_identity(client):
    r = client.get("/api/me")
    assert r.status_code == 401 and r.get_json()["auth"] == "demo" and r.headers["WWW-Authenticate"] == "Bearer"
    assert client.get("/api/me", headers={"X-Demo-User": "x"}).status_code == 401  # too short


def test_progress_roundtrip_and_isolation(client):
    a, b = {"X-Demo-User": "alice_1"}, {"X-Demo-User": "bob_2"}
    r = client.put("/api/me/progress/chef", json={"statuses": {"Food safety and sanitation": "completed"}}, headers=a)
    assert r.status_code == 200
    me = client.get("/api/me", headers=a).get_json()
    assert me["user"]["id"] == "demo|alice_1"
    assert me["progress"]["chef"]["statuses"] == {"Food safety and sanitation": "completed"}
    assert client.get("/api/me", headers=b).get_json()["progress"] == {}
    client.put("/api/me/progress/chef", json={"statuses": {"Food safety and sanitation": "planned"}}, headers=a)  # upsert
    assert client.get("/api/me", headers=a).get_json()["progress"]["chef"]["statuses"]["Food safety and sanitation"] == "planned"
    assert client.delete("/api/me/progress/chef", headers=a).status_code == 200
    assert client.get("/api/me", headers=a).get_json()["progress"] == {}


@pytest.mark.parametrize("path,body,code", [
    ("/api/me/progress/astronaut", {"statuses": {}}, 404),
    ("/api/me/progress/chef", {"statuses": {"x": "done"}}, 400),
    ("/api/me/progress/chef", {"statuses": "all"}, 400),
    ("/api/me/plans/AI", {"plan": "x"}, 400),
    ("/api/me/plans/NOPE", {"plan": {}}, 400),
])
def test_progress_validation(client, path, body, code):
    assert client.put(path, json=body, headers={"X-Demo-User": "carol_3"}).status_code == code


def test_save_plan(client):
    h = {"X-Demo-User": "dave_4"}
    plan = client.post("/api/plan", json={"program": "NET"}).get_json()
    assert client.put("/api/me/plans/net", json={"plan": plan}, headers=h).status_code == 200
    saved = client.get("/api/me", headers=h).get_json()["plans"]["NET"]["plan"]
    assert saved["termCount"] == plan["termCount"]


def test_auth0_tokens(client, monkeypatch):
    """Real RS256 verification path with a locally generated key standing in for Auth0's JWKS."""
    import jwt
    from cryptography.hazmat.primitives.asymmetric import rsa
    import auth

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    monkeypatch.setattr(auth, "AUTH0_DOMAIN", "nextstop-test.us.auth0.com")
    monkeypatch.setattr(auth, "AUTH0_AUDIENCE", "https://api.nextstop.test")

    class FakeJWKS:
        def get_signing_key_from_jwt(self, token):
            return type("K", (), {"key": key.public_key()})()

    monkeypatch.setattr(auth, "_jwks", lambda: FakeJWKS())

    def token(**over):
        claims = {"sub": "google-oauth2|123", "aud": "https://api.nextstop.test",
                  "iss": "https://nextstop-test.us.auth0.com/", "exp": int(time.time()) + 600, **over}
        return jwt.encode(claims, key, algorithm="RS256")

    ok = client.get("/api/me", headers={"Authorization": "Bearer " + token()})
    assert ok.status_code == 200 and ok.get_json()["user"] == {"id": "auth0|google-oauth2|123", "provider": "auth0"}
    assert client.get("/api/me", headers={"X-Demo-User": "alice_1"}).status_code == 401  # demo header ignored once Auth0 is on
    assert client.get("/api/me", headers={"Authorization": "Bearer " + token(aud="other")}).get_json()["error"] == "invalid_token"
    assert client.get("/api/me", headers={"Authorization": "Bearer " + token(exp=1)}).get_json()["error"] == "token_expired"
    other_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    forged = jwt.encode({"sub": "x", "aud": "https://api.nextstop.test", "iss": "https://nextstop-test.us.auth0.com/",
                         "exp": int(time.time()) + 600}, other_key, algorithm="RS256")
    assert client.get("/api/me", headers={"Authorization": "Bearer " + forged}).status_code == 401


# ---------- stats ----------

def test_stats_records_events(client):
    import store
    client.post("/api/chat", json={"chatHistory": [{"sender": "user", "text": "I love fixing wifi and routers"}]})
    client.post("/api/roadmap", json={"careerId": "chef", "personalize": False})
    client.post("/api/plan", json={"program": "AI"})
    store.flush()
    d = client.get("/api/stats?days=1&bucket=hour").get_json()
    kinds = {k for row in d["trends"]["series"] for k in row if k != "bucket"}
    assert {"chat", "roadmap", "plan"} <= kinds
    assert any(c["careerId"] == "chef" for c in d["trends"]["topCareers"])
    assert d["prune"]["pruneCalls"] >= 0 and d["trends"]["storage"]["kind"] == "sqlite"
    assert client.get("/api/stats?days=abc").status_code == 400
    assert client.get("/api/stats?bucket=week").status_code == 400


# ---------- sponsor metadata ----------

def test_prune_metadata_surfaces_in_chat(client, monkeypatch):
    import llm

    def fake_complete(messages, meta_out=None, **kw):
        if meta_out is not None:
            meta_out["prune"] = llm.prune_summary({"cache_hit": True, "cache_type": "template_semantic", "tokens_saved": 42,
                                                   "cost_saved_usd": 0.0012, "cost_without_prune_usd": 0.002,
                                                   "cost_with_prune_usd": 0.0008, "optimizations_applied": ["template_cache", "route_skipped:x"]})
        return '{"chatResponse": "Data Analytics (S9510) fits you.", "recommendedProgram": "DATA"}', "prune/gemini"

    monkeypatch.setattr(llm, "available_providers", lambda: ["prune"])
    monkeypatch.setattr(llm, "complete", fake_complete)
    e = client.post("/api/chat", json={"chatHistory": [{"sender": "user", "text": "I like spreadsheets"}]}).get_json()["engine"]
    assert e["prune"]["cacheHit"] is True and e["prune"]["tokensSaved"] == 42 and e["prune"]["optimizations"] == ["template_cache"]


def test_swarms_agent_steps(client, monkeypatch):
    import roadmap, os
    monkeypatch.setenv("SWARMS_API_KEY", "test")

    class R:
        status_code = 200
        def raise_for_status(self): pass
        def json(self):
            final = json.dumps({"tips": ["Join ProStart"], "firstSemester": ["Food safety and sanitation"], "summary": "Great fit."})
            return {"job_id": "swarm-1", "execution_time": 6.1, "usage": {"total_tokens": 900, "total_cost": 0.02},
                    "output": [{"role": "User", "content": "task..."},
                               {"role": "Career Researcher", "content": "Chefs work long hours. Call 305-555-0147"},
                               {"role": "MDC Pathway Planner", "content": "Start with food safety."},
                               {"role": "Transfer and Outcomes Advisor", "content": final}]}

    monkeypatch.setattr(roadmap.requests, "post", lambda *a, **k: R())
    rm = client.post("/api/roadmap", json={"careerId": "chef", "profile": {"interests": ["swarm-test"]}}).get_json()
    assert rm["engine"]["name"] == "swarms" and rm["engine"]["usage"]["costUsd"] == 0.02
    assert [s["agent"] for s in rm["agentSteps"]] == ["Career Researcher", "MDC Pathway Planner", "Transfer and Outcomes Advisor"]
    assert "305-555-0147" not in json.dumps(rm["agentSteps"])
    assert rm["personalTips"] == ["Join ProStart"]
