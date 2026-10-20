import io

from app.core.languages import detect_text_language

CID = "client-12345678"


def turn(client, text, **kw):
    return client.post("/api/v1/chat/turn", json={"text": text, **kw}).json()


def test_script_detection():
    assert detect_text_language("पुस्तकालय कब खुलता है") == "hi"
    assert detect_text_language("ਲਾਇਬ੍ਰੇਰੀ ਕਦੋਂ ਖੁੱਲ੍ਹਦੀ ਹੈ") == "pa"
    assert detect_text_language("When does the library open?") == "en"
    assert detect_text_language("Wann öffnet die Bibliothek und wie lange ist sie geöffnet?") == "de"


def test_hindi_text_is_translated_classified_and_answered_in_hindi(client):
    r = turn(client, "पुस्तकालय कब खुलता है")
    assert r["lang"] == "hi" and r["lang_name"] == "Hindi"
    assert r["translated_input"] == "when does the library open"
    assert r["action"] == "answer" and r["intent"] == "library_hours"
    assert r["response"].startswith("[hi] ")
    assert r["transcript"] == "पुस्तकालय कब खुलता है"  # original text preserved


def test_punjabi_and_explicit_german(client):
    assert turn(client, "ਲਾਇਬ੍ਰੇਰੀ ਕਦੋਂ ਖੁੱਲ੍ਹਦੀ ਹੈ")["lang"] == "pa"
    r = turn(client, "wann öffnet die bibliothek", lang="de")
    assert r["lang"] == "de" and r["intent"] == "library_hours" and r["response"].startswith("[de] ")


def test_clarification_options_are_translated(client):
    r = turn(client, "when does it open", lang="hi")
    assert r["action"] == "clarify" and r["response"].startswith("[hi] ")
    assert all(o["label"].startswith("[hi] ") for o in r["options"])


def test_english_is_untouched(client):
    r = turn(client, "When does the library open?")
    assert r["lang"] == "en" and r["translated_input"] is None and not r["response"].startswith("[")


def test_unknown_lang_hint_falls_back_to_detection(client):
    assert turn(client, "पुस्तकालय कब खुलता है", lang="zz")["lang"] == "hi"


def test_language_verified_flag(client, vox):
    vox.language_status = {"verified": ["hi"]}
    assert turn(client, "पुस्तकालय कब खुलता है")["lang_verified"] is True
    assert turn(client, "wann öffnet die bibliothek", lang="de")["lang_verified"] is False


def test_graceful_without_translation_model(vox):
    from fastapi.testclient import TestClient
    from app.main import create_app
    vox.translator = None
    r = turn(TestClient(create_app(vox)), "पुस्तकालय कब खुलता है")
    assert r["translation_available"] is False and r["translated_input"] is None
    assert not r["response"].startswith("[")  # English reply rather than a crash


def test_transcribe_language_hint(client, vox):
    def post(lang):
        return client.post("/api/v1/transcribe", data={"language": lang} if lang else None,
                           files={"audio": ("r.webm", io.BytesIO(b"x" * 100), "audio/webm")})
    r = post("hi")
    assert r.status_code == 200 and vox.transcriber.last_language == "hi"
    assert post("auto").status_code == 200 and vox.transcriber.last_language is None
    assert post("xx").status_code == 422
    body = post(None).json()
    assert body["language"] == "en" and body["words"] == []
