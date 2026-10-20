import io

CID = "client-12345678"


def turn(client, text, **kw):
    return client.post("/api/v1/chat/turn", json={"text": text, **kw})


def audio(client, data=b"x" * 100, ctype="audio/webm"):
    return client.post("/api/v1/transcribe", files={"audio": ("r.webm", io.BytesIO(data), ctype)})


# ---- health ----
def test_health_ok(client):
    r = client.get("/api/v1/health").json()
    assert r["status"] == "ok" and r["asr_ready"] and r["intent_ready"] and r["db_ready"]


def test_health_degraded_without_models(vox):
    from fastapi.testclient import TestClient
    from app.main import create_app
    vox.classifier = None
    assert TestClient(create_app(vox)).get("/api/v1/health").json()["status"] == "degraded"


# ---- /intent ----
def test_intent_ok(client):
    r = client.post("/api/v1/intent", json={"text": "When does the library open?"}).json()
    assert r["intent"] == "library_hours" and r["in_scope"] and r["model_version"] == "fake-v0"
    assert len(r["top"]) == 3


def test_intent_oos_flag(client):
    assert client.post("/api/v1/intent", json={"text": "what is the weather"}).json()["in_scope"] is False


def test_intent_validation(client):
    assert client.post("/api/v1/intent", json={"text": ""}).status_code == 422
    assert client.post("/api/v1/intent", json={"text": "a" * 301}).status_code == 422
    assert client.post("/api/v1/intent", json={}).status_code == 422


def test_intent_model_unavailable(vox):
    from fastapi.testclient import TestClient
    from app.main import create_app
    vox.classifier = None
    r = TestClient(create_app(vox)).post("/api/v1/intent", json={"text": "hi"})
    assert r.status_code == 503 and r.json()["error"]["code"] == "model_unavailable"


# ---- /chat/turn ----
def test_turn_answer(client):
    r = turn(client, "When does the library open?").json()
    assert r["action"] == "answer" and r["intent"] == "library_hours" and "Library" in r["response"]


def test_turn_clarify_options_then_choose(client):
    r = turn(client, "when does it open").json()
    assert r["action"] == "clarify" and r["clarify_kind"] == "disambiguate" and len(r["options"]) >= 2
    r2 = turn(client, r["options"][0]["label"], chosen_intent=r["options"][0]["intent"]).json()
    assert r2["action"] == "answer" and r2["reason"] == "user_confirmed"


def test_turn_repair_and_repeated_failure(client):
    r = turn(client, "gibberish words").json()
    assert r["clarify_kind"] == "repair"
    assert turn(client, "gibberish words", attempts=2).json()["action"] == "fallback"


def test_turn_out_of_scope(client):
    r = turn(client, "what is the weather").json()
    assert r["action"] == "fallback" and "outside" in r["response"]


def test_turn_validation(client):
    assert turn(client, "").status_code == 422
    assert turn(client, "   ").status_code == 422
    assert turn(client, "hi", attempts=-1).status_code == 422
    assert turn(client, "hi", input_mode="video").status_code == 422
    assert turn(client, "hi", chosen_intent="nope").status_code == 422
    assert turn(client, "hi", client_id="bad id!!").status_code == 422


def test_turn_logs_metrics_without_text(client, vox):
    turn(client, "When does the library open?")
    s = client.get("/api/v1/metrics/summary").json()
    assert s["turns"] == 1 and s["answer"] == 1
    from app.db.database import EvalEvent
    assert not any(c.name in ("text", "transcript") for c in EvalEvent.__table__.columns)


# ---- /transcribe ----
def test_transcribe_ok(client):
    r = audio(client).json()
    assert r["transcript"] == "when does the library open" and 0 < r["asr_confidence"] <= 1


def test_transcribe_empty(client):
    r = audio(client, b"")
    assert r.status_code == 400 and r.json()["error"]["code"] == "empty_audio"


def test_transcribe_too_large(client):
    r = audio(client, b"x" * 1500)
    assert r.status_code == 413 and r.json()["error"]["code"] == "audio_too_large"


def test_transcribe_bad_type(client):
    r = audio(client, ctype="text/plain")
    assert r.status_code == 415


def test_transcribe_no_speech_and_decode(client, vox):
    vox.transcriber.mode = "nospeech"
    assert audio(client).json()["error"]["code"] == "no_speech"
    vox.transcriber.mode = "decode"
    assert audio(client).json()["error"]["code"] == "decode_failed"


def test_transcribe_timeout(client, vox):
    vox.transcriber.mode = "slow"
    r = audio(client)
    assert r.status_code == 504 and r.json()["error"]["code"] == "asr_timeout"


def test_transcribe_unavailable(vox):
    from fastapi.testclient import TestClient
    from app.main import create_app
    vox.transcriber = None
    r = audio(TestClient(create_app(vox)))
    assert r.status_code == 503 and r.json()["error"]["code"] == "asr_unavailable"


# ---- feedback / correction memory ----
def fb(client, remember, orig="when does the libary open", corr="when does the library open"):
    return client.post("/api/v1/feedback", json={"client_id": CID, "original_text": orig,
                                                 "corrected_text": corr, "remember": remember})


def test_feedback_requires_opt_in(client):
    assert fb(client, False).json() == {"stored": False, "item": None}
    assert client.get(f"/api/v1/memory/{CID}").json() == []


def test_memory_roundtrip_and_apply(client):
    assert fb(client, True).json()["stored"] is True
    items = client.get(f"/api/v1/memory/{CID}").json()
    assert len(items) == 1
    # before memory the mis-heard text is not understood; with use_memory it is corrected
    assert turn(client, "when does the libary open").json()["action"] != "answer"
    r = turn(client, "When does the libary open?", client_id=CID, use_memory=True).json()
    assert r["memory_applied"] and r["action"] == "answer"
    # other clients are unaffected
    assert not turn(client, "when does the libary open", client_id="other-client-99", use_memory=True).json()["memory_applied"]


def test_memory_delete(client):
    fb(client, True); fb(client, True, orig="hello there x", corr="hello")
    items = client.get(f"/api/v1/memory/{CID}").json()
    assert client.delete(f"/api/v1/memory/{CID}/{items[0]['id']}").json()["deleted"] == 1
    assert client.delete(f"/api/v1/memory/{CID}/99999").status_code == 404
    assert client.delete(f"/api/v1/memory/{CID}").json()["deleted"] == 1
    assert client.get(f"/api/v1/memory/{CID}").json() == []


def test_feedback_validation(client):
    assert client.post("/api/v1/feedback", json={"client_id": "x", "original_text": "a",
                                                 "corrected_text": "b", "remember": True}).status_code == 422
    assert client.get("/api/v1/memory/bad!").status_code in (404, 422)


def test_sql_injection_is_inert(client):
    evil = "x'; DROP TABLE correction_memory; --"
    assert fb(client, True, orig=evil, corr="safe").status_code == 200
    assert len(client.get(f"/api/v1/memory/{CID}").json()) == 1
