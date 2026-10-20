import io
import json
from pathlib import Path

from app.core.languages import detect_text_language
from app.services.knowledge import numbers_in, numbers_preserved

CID = "client-12345678"
CURATED = json.loads((Path(__file__).resolve().parents[1] / "app" / "data" / "translations.json").read_text(encoding="utf-8"))


def turn(client, text, **kw):
    return client.post("/api/v1/chat/turn", json={"text": text, **kw}).json()


def test_script_detection():
    assert detect_text_language("पुस्तकालय कब खुलता है") == "hi"
    assert detect_text_language("ਲਾਇਬ੍ਰੇਰੀ ਕਦੋਂ ਖੁੱਲ੍ਹਦੀ ਹੈ") == "pa"
    assert detect_text_language("When does the library open?") == "en"
    assert detect_text_language("Wann öffnet die Bibliothek und wie lange ist sie geöffnet?") == "de"


def test_latin_script_languages_are_detected_and_english_is_not_misrouted():
    cases = {"es": ["¿A qué hora abre la biblioteca?", "¿Cómo puedo pagar mis tasas de matrícula?", "Necesito un certificado de estudios", "Olvidé la contraseña del portal"],
             "pt": ["A que horas abre a biblioteca?", "Como posso pagar as propinas?", "Esqueci a senha do portal"],
             "fr": ["À quelle heure ouvre la bibliothèque ?", "Comment payer mes frais de scolarité ?"],
             "it": ["A che ora apre la biblioteca?", "Come posso pagare le tasse universitarie?"], "nl": ["Hoe laat gaat de bibliotheek open?"], "tr": ["Kütüphane saat kaçta açılıyor?"]}
    for lang, xs in cases.items():
        for x in xs:
            assert detect_text_language(x) == lang, x
    assert detect_text_language("Wo ist das Gesundheitszentrum?") == "de"


def test_english_text_is_never_misrouted_to_another_language():
    for t in ["I forgot my portal password", "Who do I contact for IT support?", "Are you a robot?", "Order me a pizza", "Hello", "What is the capital of France?", "Tell me a joke", "Can I get a receipt?"]:
        assert detect_text_language(t) == "en", t


def test_hindi_is_understood_and_answered_with_the_curated_hindi_reply(client):
    r = turn(client, "पुस्तकालय कब खुलता है")
    assert r["lang"] == "hi" and r["lang_name"] == "Hindi"
    assert r["translated_input"] == "when does the library open"
    assert r["action"] == "answer" and r["intent"] == "library_hours"
    assert r["response"] == CURATED["hi"]["intents"]["library_hours"]["answer"]   # hand-written, not machine translated
    assert r["translation_mode"] == "curated" and r["translation_warning"] is False
    assert r["response_en"].startswith("The Central Library")                      # English original always provided
    assert r["transcript"] == "पुस्तकालय कब खुलता है"                               # original text preserved


def test_punjabi_and_explicit_german(client):
    assert turn(client, "ਲਾਇਬ੍ਰੇਰੀ ਕਦੋਂ ਖੁੱਲ੍ਹਦੀ ਹੈ")["lang"] == "pa"
    r = turn(client, "wann öffnet die bibliothek", lang="de")
    assert r["lang"] == "de" and r["intent"] == "library_hours"
    assert r["response"] == CURATED["de"]["intents"]["library_hours"]["answer"]


def test_curated_times_are_consistent_with_english(client):
    en = turn(client, "When does the library open?")["response"]
    for lang in ("hi", "pa", "de"):
        assert numbers_preserved(en, CURATED[lang]["intents"]["library_hours"]["answer"]), lang


def test_clarification_is_targeted_and_localized(client):
    r = turn(client, "when does it open", lang="hi")
    assert r["action"] == "clarify" and r["translation_mode"] == "curated"
    assert CURATED["hi"]["intents"]["library_hours"]["short"] in r["response"]
    assert {o["label"] for o in r["options"]} <= {v["label"] for v in CURATED["hi"]["intents"].values() if "label" in v}


def test_out_of_scope_fallback_is_localized(client):
    assert turn(client, "what is the weather", lang="de")["response"] == CURATED["de"]["fallback_out_of_scope"]


def test_non_curated_language_uses_machine_translation_with_numeric_guard(client, vox):
    r = turn(client, "when does the library open", lang="fr")
    assert r["translation_mode"] == "machine" and r["response"].startswith("[fr] ") and r["translation_warning"] is False
    assert r["response_en"].startswith("The Central Library")

    class DropsNumbers:
        def translate(self, text, src, tgt):
            return text if tgt == "en" else "réponse sans chiffres"
    vox.translator = DropsNumbers()
    from fastapi.testclient import TestClient
    from app.main import create_app
    r2 = turn(TestClient(create_app(vox)), "when does the library open", lang="fr")
    assert r2["translation_warning"] is True   # 08:00 / 22:00 vanished: the UI will tell the user to verify


def test_numbers_guard_handles_indic_digits():
    assert numbers_in("सुबह ०८:०० से २२:००") == {"8", "0", "22"}   # leading zeros ignored: "08" == "8"
    assert numbers_preserved("Open 08:00 to 22:00", "ਖੁੱਲ੍ਹੀ ੦੮:੦੦ ਤੋਂ ੨੨:੦੦")
    assert not numbers_preserved("Open 08:00 to 22:00", "open at night")


def test_english_is_untouched(client):
    r = turn(client, "When does the library open?")
    assert r["lang"] == "en" and r["translated_input"] is None and r["response_en"] is None and r["translation_mode"] is None


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
    c = TestClient(create_app(vox))
    r = turn(c, "when does the library open", lang="fr")          # no curated text, no MT: English reply, flagged
    assert r["translation_available"] is False and r["translation_mode"] is None and not r["response"].startswith("[")
    r = turn(c, "पुस्तकालय कब खुलता है")                              # curated reply still works for output
    assert r["translation_mode"] == "curated" and r["translated_input"] is None


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
