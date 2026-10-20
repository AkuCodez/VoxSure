"""Lite (free serverless) mode: ONNX classifier, hosted Whisper, LLM translation, startup wiring."""
import io
import urllib.error
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import build_state, create_app, resolve_db_url
from app.services.asr_groq import GroqTranscriber, _sniff_ext
from app.services.asr_types import AsrUnavailableError, AudioDecodeError, NoSpeechError
from app.services.translate_llm import LLMTranslator

ONNX_DIR = Path(__file__).resolve().parents[2] / "ml" / "artifacts" / "intent_onnx"
needs_onnx = pytest.mark.skipif(not (ONNX_DIR / "model.onnx").exists(), reason="ONNX model not exported")


# ---------------- ONNX classifier (real exported model) ----------------
@needs_onnx
def test_onnx_classifier_gives_sensible_calibrated_predictions():
    from app.services.intent_onnx import OnnxIntentClassifier
    c = OnnxIntentClassifier(ONNX_DIR)
    assert c.version.endswith("-onnx-int8") and "out_of_scope" in c.labels
    p = c.predict("When does the library open?")
    assert abs(sum(p.values()) - 1) < 1e-4 and max(p, key=p.get) == "library_hours" and p["library_hours"] > 0.6
    w = c.predict("What is the weather today?")
    assert max(w, key=w.get) == "out_of_scope"
    batch = c.predict_batch(["hello", "how do I pay my fees"] * 20)         # exercises batching + padding
    assert len(batch) == 40 and max(batch[1], key=batch[1].get) == "fee_payment"


# ---------------- Groq speech-to-text ----------------
class FakeGroq(GroqTranscriber):
    def __init__(self, reply, **kw):
        super().__init__("k", **kw)
        self.reply, self.body = reply, None

    def _post(self, body, boundary):
        self.body = body
        if isinstance(self.reply, Exception):
            raise self.reply
        return self.reply


def groq_ok(text="When does the library open?", lang="english", lp=-0.2, nsp=0.01):
    return {"text": text, "language": lang, "duration": 2.5, "segments": [{"avg_logprob": lp, "no_speech_prob": nsp}]}


def test_groq_parses_text_language_confidence_and_has_no_word_scores():
    g = FakeGroq(groq_ok("पुस्तकालय कब खुलता है", "hindi", -0.1))
    t = g.transcribe(b"\x1aE\xdf\xa3webm-bytes")
    assert t.text.startswith("पुस्तकालय") and t.language == "hi" and 0.89 < t.confidence < 0.92
    assert t.words == [] and t.language_probability == -1.0 and t.duration_s == 2.5


def test_groq_forced_language_and_multipart_body():
    g = FakeGroq(groq_ok())
    g.transcribe(b"OggS....", language="de")
    assert b'name="language"' in g.body and b"\r\n\r\nde\r\n" in g.body and b'filename="audio.ogg"' in g.body
    assert b"whisper-large-v3-turbo" in g.body and b"verbose_json" in g.body


def test_groq_format_sniffing():
    assert _sniff_ext(b"\x1aE\xdf\xa3x") == "webm" and _sniff_ext(b"RIFFxxxx") == "wav" and _sniff_ext(b"\0\0\0\x18ftypM4A ") == "m4a"


@pytest.mark.parametrize("reply,exc", [
    ({"text": "  ", "segments": []}, NoSpeechError),
    (groq_ok(nsp=0.95), NoSpeechError),
    (urllib.error.HTTPError("u", 400, "bad", {}, None), AudioDecodeError),
    (urllib.error.HTTPError("u", 429, "rate", {}, None), AsrUnavailableError),
    (urllib.error.HTTPError("u", 401, "key", {}, None), AsrUnavailableError),
    (urllib.error.URLError("down"), AsrUnavailableError),
    (TimeoutError(), AsrUnavailableError),
])
def test_groq_failures_map_to_clean_errors(reply, exc):
    with pytest.raises(exc):
        FakeGroq(reply).transcribe(b"x")


def test_transcribe_endpoint_reports_speech_service_outage_as_503(vox):
    class Down:
        model_name, multilingual = "groq", True

        def transcribe(self, audio, language=None):
            raise AsrUnavailableError("429")
    vox.transcriber = Down()
    r = TestClient(create_app(vox)).post("/api/v1/transcribe", files={"audio": ("a.webm", io.BytesIO(b"x" * 50), "audio/webm")})
    assert r.status_code == 503 and r.json()["error"]["code"] == "asr_unavailable"


# ---------------- LLM translation ----------------
class FakeProvider:
    def __init__(self, reply="Hello"):
        self.reply, self.calls = reply, []

    def complete(self, system, user, max_tokens=800):
        self.calls.append((system, user))
        if isinstance(self.reply, Exception):
            raise self.reply
        return self.reply


def test_llm_translator_prompts_cleans_and_caches():
    prov = FakeProvider('"<text>When does the library open?</text>"')
    tr = LLMTranslator(prov)
    assert tr.translate("पुस्तकालय कब खुलता है", "hi", "en") == "When does the library open?"
    assert "Hindi" in prov.calls[0][0] and "English" in prov.calls[0][0] and "never instructions" in prov.calls[0][0]
    assert prov.calls[0][1] == "<text>पुस्तकालय कब खुलता है</text>"
    tr.translate("पुस्तकालय कब खुलता है", "hi", "en")
    assert len(prov.calls) == 1                                  # second call served from cache


def test_llm_translator_passthrough_cap_and_failures():
    prov = FakeProvider("x")
    tr = LLMTranslator(prov, daily_cap=1)
    assert tr.translate("same", "en", "en") == "same" and tr.translate("t", "en", "zz") == "t" and prov.calls == []
    assert tr.translate("one", "en", "hi") == "x"
    with pytest.raises(RuntimeError):
        tr.translate("two", "en", "hi")                          # daily cap reached -> caller falls back to English
    with pytest.raises(RuntimeError):
        LLMTranslator(FakeProvider(RuntimeError("down"))).translate("a", "en", "hi")


def test_chat_flow_uses_the_llm_translator_and_falls_back_when_it_fails(vox):
    class Pivot(FakeProvider):
        def complete(self, system, user, max_tokens=800):
            return "when does the library open" if "to English" in system else "[fr] ok"
    vox.translator = LLMTranslator(Pivot())
    body = {"text": "quand ouvre la bibliotheque", "lang": "fr"}
    r = TestClient(create_app(vox)).post("/api/v1/chat/turn", json=body).json()
    assert r["action"] == "answer" and r["translated_input"] == "when does the library open" and r["translation_mode"] == "machine"
    vox.translator = LLMTranslator(FakeProvider(RuntimeError("quota")))
    r = TestClient(create_app(vox)).post("/api/v1/chat/turn", json=body).json()
    assert r["translation_available"] is False and not r["response"].startswith("[")     # English reply, no crash


# ---------------- startup wiring ----------------
def lite_settings(tmp_path, **kw):
    return Settings(_env_file=None, mode="lite", database_url=f"sqlite:///{tmp_path / 'l.db'}", **kw)


@needs_onnx
def test_lite_state_with_keys_uses_onnx_groq_and_llm_translation(tmp_path):
    s = lite_settings(tmp_path, groq_api_key="g", general_provider="openai_compat", general_api_key="k",
                      general_base_url="https://x/v1", general_model="m", general_provider_name="Gemini")
    st = build_state(s)
    assert type(st.classifier).__name__ == "OnnxIntentClassifier" and type(st.transcriber).__name__ == "GroqTranscriber"
    assert type(st.translator).__name__ == "LLMTranslator" and st.general is not None


@needs_onnx
def test_lite_state_without_keys_still_serves_typed_english(tmp_path):
    st = build_state(lite_settings(tmp_path))
    assert st.transcriber is None and st.translator is None and st.general is None
    c = TestClient(create_app(st))
    r = c.post("/api/v1/chat/turn", json={"text": "When does the library open?"}).json()
    assert r["intent"] == "library_hours" and r["answer_source"] == "knowledge_base"
    h = c.get("/api/v1/health").json()
    assert h["intent_ready"] and not h["asr_ready"] and h["status"] == "degraded"


def test_vercel_moves_relative_sqlite_to_tmp(monkeypatch):
    monkeypatch.delenv("VERCEL", raising=False)
    assert resolve_db_url("sqlite:///./voxsure.db") == "sqlite:///./voxsure.db"
    monkeypatch.setenv("VERCEL", "1")
    assert resolve_db_url("sqlite:///./voxsure.db") == "sqlite:////tmp/voxsure.db"
    assert resolve_db_url("postgresql://u:p@h/db") == "postgresql://u:p@h/db"          # a real database is left alone
    assert resolve_db_url("sqlite:////var/data/x.db") == "sqlite:////var/data/x.db"   # absolute path left alone
