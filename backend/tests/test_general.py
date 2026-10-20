import anthropic
import httpx2
import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.services.general import GeneralAnswerer


# ---------- fakes ----------
class FakeGeneral:
    def __init__(self, reply="Paris is the capital of France.", available=True):
        self.reply, self._avail, self.calls = reply, available, []

    def available(self):
        return self._avail

    def answer(self, text, history=None):
        self.calls.append((text, history))
        return self.reply


class Block:
    def __init__(self, type_, text=""):
        self.type, self.text = type_, text


class Resp:
    def __init__(self, blocks, stop="end_turn"):
        self.content, self.stop_reason = blocks, stop


class FakeClient:
    """Records calls; `script` is a list of responses or exceptions consumed in order."""
    def __init__(self, script):
        self.script, self.calls = list(script), []
        self.messages = self

    def create(self, **kw):
        self.calls.append(kw)
        item = self.script.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def req():
    return httpx2.Request("POST", "https://api.anthropic.com/v1/messages")


def bad_request():
    return anthropic.BadRequestError("bad", response=httpx2.Response(400, request=req()), body=None)


def conn_error():
    return anthropic.APIConnectionError(request=req())


def turn(client, text, **kw):
    return client.post("/api/v1/chat/turn", json={"text": text, **kw}).json()


# ---------- routing ----------
def test_out_of_scope_questions_are_answered_by_the_general_model(vox):
    vox.general = FakeGeneral()
    r = turn(TestClient(create_app(vox)), "what is the weather")   # classifier: out_of_scope
    assert r["action"] == "answer" and r["intent"] == "general_knowledge" and r["reason"] == "general_ai"
    assert r["response"] == "Paris is the capital of France." and r["answer_source"] == "general_ai"
    assert "AI model" in r["sources"][0]["title"] and r["sources"][0]["url"] is None


def test_campus_questions_still_use_the_reviewed_knowledge_base(vox):
    vox.general = FakeGeneral()
    r = turn(TestClient(create_app(vox)), "When does the library open?")
    assert r["answer_source"] == "knowledge_base" and r["intent"] == "library_hours" and vox.general.calls == []


def test_ambiguous_campus_questions_still_clarify_instead_of_guessing(vox):
    vox.general = FakeGeneral()
    r = turn(TestClient(create_app(vox)), "when does it open")
    assert r["action"] == "clarify" and vox.general.calls == []


def test_user_can_opt_out_of_general_answers(vox):
    vox.general = FakeGeneral()
    r = turn(TestClient(create_app(vox)), "what is the weather", allow_general=False)
    assert r["action"] == "fallback" and vox.general.calls == []


def test_general_failure_falls_back_to_the_standard_reply(vox):
    vox.general = FakeGeneral(reply=None)
    r = turn(TestClient(create_app(vox)), "what is the weather")
    assert r["action"] == "fallback" and r["answer_source"] == "none" and "outside" in r["response"].lower() + "outside"


def test_cap_reached_means_no_call_and_standard_fallback(vox):
    vox.general = FakeGeneral(available=False)
    assert turn(TestClient(create_app(vox)), "what is the weather")["action"] == "fallback"
    assert vox.general.calls == []


def test_no_key_configured_means_standard_fallback(client):
    assert turn(client, "what is the weather")["action"] == "fallback"


def test_recent_history_is_forwarded_and_trimmed(vox):
    vox.general = FakeGeneral()
    hist = [{"role": "user" if i % 2 == 0 else "assistant", "text": f"m{i}"} for i in range(8)]
    turn(TestClient(create_app(vox)), "what is the weather", history=hist)
    sent = vox.general.calls[0][1]
    assert len(sent) == 6 and sent[-1]["content"] == "m7"


def test_history_is_validated(vox):
    vox.general = FakeGeneral()
    c = TestClient(create_app(vox))
    assert c.post("/api/v1/chat/turn", json={"text": "x", "history": [{"role": "system", "text": "hi"}]}).status_code == 422
    assert c.post("/api/v1/chat/turn", json={"text": "x", "history": [{"role": "user", "text": "a" * 601}]}).status_code == 422
    assert c.post("/api/v1/chat/turn", json={"text": "x", "history": [{"role": "user", "text": "a"}] * 9}).status_code == 422


def test_general_reply_in_another_language_is_not_machine_translated(vox):
    vox.general = FakeGeneral(reply="पेरिस फ्रांस की राजधानी है।")
    r = turn(TestClient(create_app(vox)), "what is the weather", lang="hi")
    assert r["response"] == "पेरिस फ्रांस की राजधानी है।" and r["response_en"] is None and r["translation_mode"] is None


def test_health_reports_general_readiness(vox):
    c = TestClient(create_app(vox))
    assert c.get("/api/v1/health").json()["general_ready"] is False
    vox.general = FakeGeneral()
    assert c.get("/api/v1/health").json()["general_ready"] is True


# ---------- the service itself ----------
def test_service_extracts_text_and_ignores_thinking_blocks():
    fc = FakeClient([Resp([Block("thinking"), Block("text", "Paris."), Block("text", "It is in France.")])])
    assert GeneralAnswerer(client=fc).answer("capital of France?") == "Paris. It is in France."
    kw = fc.calls[0]
    assert kw["model"] == "claude-opus-5-5" and kw["messages"][-1] == {"role": "user", "content": "capital of France?"}
    assert "same language" in kw["system"] and kw["extra_body"]["output_config"]["effort"] == "low"


def test_service_sends_only_the_message_and_history_never_identifiers():
    fc = FakeClient([Resp([Block("text", "ok")])])
    GeneralAnswerer(client=fc).answer("hello", [{"role": "assistant", "content": "earlier"}, {"role": "user", "content": "q"}])
    msgs = fc.calls[0]["messages"]
    assert msgs[0]["role"] == "user"                      # leading assistant turn dropped (API requires user first)
    assert [m["content"] for m in msgs] == ["q", "hello"]
    assert set(fc.calls[0]) <= {"model", "max_tokens", "system", "messages", "extra_headers", "extra_body"}


def test_service_retries_without_extras_when_the_api_rejects_them():
    fc = FakeClient([bad_request(), Resp([Block("text", "fine")])])
    assert GeneralAnswerer(client=fc).answer("hi") == "fine"
    assert "extra_body" in fc.calls[0] and "extra_body" not in fc.calls[1]


@pytest.mark.parametrize("script", [[conn_error(), ], [Resp([Block("text", "x")], stop="refusal")], [Resp([Block("thinking")])]])
def test_service_returns_none_instead_of_raising(script):
    assert GeneralAnswerer(client=FakeClient(script)).answer("hi") is None


def test_service_enforces_the_daily_cap():
    g = GeneralAnswerer(client=FakeClient([Resp([Block("text", "a")]), Resp([Block("text", "b")])]), daily_cap=1)
    assert g.available() and g.answer("one") == "a"
    assert not g.available() and g.answer("two") is None


# ---------- OpenAI-compatible providers (Groq, Gemini compat endpoint, OpenRouter, ...) ----------
from app.core.config import Settings
from app.main import build_general
from app.services.general import OpenAICompatAnswerer


class CompatFake(OpenAICompatAnswerer):
    def __init__(self, reply, **kw):
        super().__init__("https://example.invalid/v1/", "k", "some-model", **kw)
        self.reply, self.payloads = reply, []

    def _post(self, payload):
        self.payloads.append(payload)
        if isinstance(self.reply, Exception):
            raise self.reply
        return self.reply


def ok(text):
    return {"choices": [{"message": {"content": text}}]}


def test_compat_answerer_builds_the_request_and_parses_the_reply():
    g = CompatFake(ok("  Paris.  "), provider_name="Groq")
    assert g.url == "https://example.invalid/v1/chat/completions"
    assert g.answer("capital of France?", [{"role": "assistant", "content": "x"}, {"role": "user", "content": "q"}]) == "Paris."
    p = g.payloads[0]
    assert p["model"] == "some-model" and p["messages"][0]["role"] == "system" and "same language" in p["messages"][0]["content"]
    assert [m["content"] for m in p["messages"][1:]] == ["q", "capital of France?"]   # leading assistant turn dropped


@pytest.mark.parametrize("reply", [OSError("boom"), TimeoutError(), {"choices": []}, {"oops": 1}, ok("   "), ValueError("bad json")])
def test_compat_answerer_returns_none_on_any_failure(reply):
    assert CompatFake(reply).answer("hi") is None


def test_compat_answerer_enforces_the_daily_cap():
    g = CompatFake(ok("a"), daily_cap=1)
    assert g.answer("one") == "a" and not g.available() and g.answer("two") is None


def test_provider_name_is_shown_to_the_user(vox):
    vox.general = CompatFake(ok("Berlin."), provider_name="Groq")
    r = turn(TestClient(create_app(vox)), "what is the weather")
    assert "Groq" in r["sources"][0]["title"] and r["answer_source"] == "general_ai"


def test_provider_selection_from_environment(monkeypatch):
    for k in ("ANTHROPIC_API_KEY", "GENERAL_API_KEY"):
        monkeypatch.delenv(k, raising=False)
    cfg = dict(general_base_url="https://api.groq.com/openai/v1", general_model="m", general_provider_name="Groq")
    assert build_general(Settings(**cfg)) is None                     # no keys -> feature off
    monkeypatch.setenv("GENERAL_API_KEY", "x")
    g = build_general(Settings(**cfg))                                 # settings are read at construction
    assert isinstance(g, OpenAICompatAnswerer) and g.provider_name == "Groq"
    monkeypatch.setenv("ANTHROPIC_API_KEY", "y")
    assert type(build_general(Settings(**cfg))).__name__ == "GeneralAnswerer"   # 'auto' prefers Claude when its key exists
    assert isinstance(build_general(Settings(general_provider="openai_compat", general_base_url="https://x/v1", general_model="m")), OpenAICompatAnswerer)
    assert build_general(Settings(general_answers_enabled=False)) is None
    assert build_general(Settings(general_provider="openai_compat")) is None   # missing url/model -> off, not a crash


def test_keys_in_a_dotenv_file_are_honoured(tmp_path, monkeypatch):
    for k in ("ANTHROPIC_API_KEY", "GENERAL_API_KEY"):
        monkeypatch.delenv(k, raising=False)
    env = tmp_path / ".env"
    env.write_text("GENERAL_API_KEY=from-dotenv\nGENERAL_BASE_URL=https://x/v1\nGENERAL_MODEL=m\n", encoding="utf-8")
    s = Settings(_env_file=str(env))
    assert s.general_api_key == "from-dotenv"
    assert isinstance(build_general(s), OpenAICompatAnswerer)
