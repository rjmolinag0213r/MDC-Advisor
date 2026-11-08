"""Advisor memory: conversations and remembered facts per signed-in student."""
import json

A = {"X-Demo-User": "mem_alice"}
B = {"X-Demo-User": "mem_bob"}


def say(client, text, headers=None, history=None):
    hist = (history or []) + [{"sender": "user", "text": text}]
    return client.post("/api/chat", json={"chatHistory": hist}, headers=headers or {}).get_json()


def test_anonymous_chat_has_no_memory(client):
    r = say(client, "I love fixing wifi and routers")
    assert "memory" not in r and "_memoryUpdate" not in r


def test_signed_in_chat_is_saved_and_remembered(client):
    client.delete("/api/me/chat", headers=A)
    r = say(client, "I build Arduino projects and want to design circuit boards", A)
    assert r["recommendedProgram"] == "ECE"
    assert r["memory"]["programLeaning"] == "ECE" and r["memory"]["careerLeaning"] == "electrical-engineer"
    m = client.get("/api/me/chat", headers=A).get_json()
    assert [x["sender"] for x in m["messages"]] == ["user", "bot"]
    assert "Arduino" in m["messages"][0]["text"]
    assert m["memory"]["programLeaning"] == "ECE"


def test_memory_is_injected_into_the_next_conversation(client, monkeypatch):
    import llm
    client.delete("/api/me/chat", headers=A)
    seen = {}

    def fake(messages, meta_out=None, **kw):
        seen["system"] = messages[0]["content"]
        return json.dumps({"chatResponse": "Great, cybersecurity it is.", "recommendedProgram": "CYBER",
                           "memoryUpdate": {"interests": ["CTF challenges", "Mr. Robot"], "grade": "11"}}), "prune/test"

    monkeypatch.setattr(llm, "available_providers", lambda: ["prune"])
    monkeypatch.setattr(llm, "complete", fake)
    first = say(client, "I do CTF challenges and loved Mr. Robot", A)
    assert set(first["memory"]["interests"]) == {"CTF challenges", "Mr. Robot"} and first["memory"]["grade"] == "11"
    # brand-new conversation (empty history on the client): the advisor still knows
    say(client, "hi again", A)
    assert "CTF challenges" in seen["system"] and "CYBER" in seen["system"] and "Grade: 11" in seen["system"]


def test_memory_never_stores_personal_details(client, monkeypatch):
    import llm
    client.delete("/api/me/chat", headers=A)
    monkeypatch.setattr(llm, "available_providers", lambda: ["prune"])
    monkeypatch.setattr(llm, "complete", lambda *a, **k: (json.dumps({
        "chatResponse": "Noted!", "recommendedProgram": None,
        "memoryUpdate": {"interests": ["robots", "call me at 305-555-0147"], "goals": ["email me at a@example.com"]}}), "prune/test"))
    r = say(client, "text me at 305-555-0147, I like robots", A)
    dumped = json.dumps(client.get("/api/me/chat", headers=A).get_json())
    assert "305-555-0147" not in dumped and "a@example.com" not in dumped
    assert r["memory"]["interests"] == ["robots"]


def test_memory_is_per_student_and_can_be_forgotten(client):
    client.delete("/api/me/chat", headers=A)
    client.delete("/api/me/chat", headers=B)
    say(client, "I want to be an ethical hacker", A)
    assert client.get("/api/me/chat", headers=B).get_json() == {"messages": [], "memory": {}}
    assert client.delete("/api/me/chat", headers=A).status_code == 200
    assert client.get("/api/me/chat", headers=A).get_json() == {"messages": [], "memory": {}}


def test_saved_record_reaches_the_advisor(client, monkeypatch):
    import llm
    client.put("/api/me/plans/AI", json={"plan": {"program": "AI", "completed": ["ZEN 1101", "ZMA 1105"]}}, headers=A)
    seen = {}
    monkeypatch.setattr(llm, "available_providers", lambda: ["prune"])
    monkeypatch.setattr(llm, "complete", lambda messages, **k: (seen.setdefault("s", messages[0]["content"]) and
                                                                '{"chatResponse": "ok", "recommendedProgram": null}', "prune/test"))
    say(client, "what should I take next?", A)
    assert "AI program; 2 courses completed (ZEN 1101, ZMA 1105)" in seen["s"]


def test_merge_memory_dedupes_and_caps():
    import store
    m = store.merge_memory({"interests": ["robots"]}, {"interests": ["Robots", "games"], "programLeaning": "null"})
    assert m == {"interests": ["robots", "games"]}
    big = store.merge_memory({}, {"interests": [f"i{n}" for n in range(20)]})
    assert len(big["interests"]) == 8


def test_chat_history_requires_identity(client):
    assert client.get("/api/me/chat").status_code == 401
    assert client.get("/api/me/chat?limit=x", headers=A).status_code == 400


def test_heuristic_memory_when_model_skips_it():
    import app
    m = app._heuristic_memory("I really love statistics and making charts about basketball, I'm in 11th grade. I'm worried about math")
    assert m["grade"] == "11" and m["interests"] == ["statistics and making charts about basketball"] and m["concerns"] == ["math"]
    assert app._heuristic_memory("I'm a junior")["grade"] == "11"
    assert app._heuristic_memory("can you tell me about networking") == {}


def test_offline_chat_still_remembers(client):
    client.delete("/api/me/chat", headers=A)
    r = say(client, "I like fixing wifi and routers, I'm a senior", A)   # offline engine: no memoryUpdate from a model
    assert r["memory"]["grade"] == "12" and "fixing wifi and routers" in r["memory"]["interests"]
    assert r["memory"]["programLeaning"] == "NET"
