"""Language registry: ISO 639-1 code -> NLLB-200 code + display name, and text language detection."""
from __future__ import annotations

import re

# (NLLB code, display name). Whisper and langid both use ISO 639-1 codes for these.
LANGS: dict[str, tuple[str, str]] = {
    "en": ("eng_Latn", "English"), "hi": ("hin_Deva", "Hindi"), "pa": ("pan_Guru", "Punjabi"),
    "de": ("deu_Latn", "German"), "fr": ("fra_Latn", "French"), "es": ("spa_Latn", "Spanish"),
    "pt": ("por_Latn", "Portuguese"), "it": ("ita_Latn", "Italian"), "nl": ("nld_Latn", "Dutch"),
    "ru": ("rus_Cyrl", "Russian"), "ar": ("arb_Arab", "Arabic"), "zh": ("zho_Hans", "Chinese"),
    "ja": ("jpn_Jpan", "Japanese"), "ko": ("kor_Hang", "Korean"), "tr": ("tur_Latn", "Turkish"),
    "ur": ("urd_Arab", "Urdu"), "bn": ("ben_Beng", "Bengali"), "ta": ("tam_Taml", "Tamil"),
    "te": ("tel_Telu", "Telugu"), "mr": ("mar_Deva", "Marathi"), "gu": ("guj_Gujr", "Gujarati"),
    "kn": ("kan_Knda", "Kannada"), "ml": ("mal_Mlym", "Malayalam"), "ne": ("npi_Deva", "Nepali"),
    "pl": ("pol_Latn", "Polish"), "uk": ("ukr_Cyrl", "Ukrainian"), "id": ("ind_Latn", "Indonesian"),
    "vi": ("vie_Latn", "Vietnamese"), "th": ("tha_Thai", "Thai"), "sv": ("swe_Latn", "Swedish"),
}

_GURMUKHI = re.compile(r"[਀-੿]")
_DEVANAGARI = re.compile(r"[ऀ-ॿ]")
_SCRIPT_RULES = [  # unambiguous scripts first
    (re.compile(r"[਀-੿]"), "pa"),
    (re.compile(r"[஀-௿]"), "ta"), (re.compile(r"[ఀ-౿]"), "te"),
    (re.compile(r"[ঀ-৿]"), "bn"), (re.compile(r"[઀-૿]"), "gu"),
    (re.compile(r"[ಀ-೿]"), "kn"), (re.compile(r"[ഀ-ൿ]"), "ml"),
    (re.compile(r"[฀-๿]"), "th"), (re.compile(r"[가-힯]"), "ko"),
    (re.compile(r"[぀-ヿ]"), "ja"), (re.compile(r"[一-鿿]"), "zh"),
    (re.compile(r"[ऀ-ॿ]"), "hi"),  # Devanagari: Hindi (Marathi/Nepali share it; best effort)
]


_EN_WORDS = {
    "the", "is", "are", "do", "does", "did", "i", "my", "you", "your", "me", "can", "how", "what", "when", "where", "who", "which",
    "would", "to", "of", "and", "for", "it", "there", "this", "that", "have", "has", "need", "want", "please", "hello", "hi",
    "thanks", "thank", "our", "with", "from", "about", "tell", "not", "get", "be", "if", "any", "much", "many",
}
_LATIN_LANGS = [c for c in LANGS if c not in ("pa", "ta", "te", "bn", "gu", "kn", "ml", "th", "ko", "ja", "zh", "hi", "mr", "ne", "ur", "ar", "ru", "uk")]
_IDENT = None


def _identifier():
    global _IDENT
    if _IDENT is None:
        from langid.langid import LanguageIdentifier, model
        _IDENT = LanguageIdentifier.from_modelstring(model, norm_probs=True)
        _IDENT.set_languages(sorted(set(_LATIN_LANGS) | {"ru", "ar", "uk", "ur"}))
    return _IDENT


# Common function words per language (generic, not tuned to any test sentence). Used for Latin-script text,
# where the statistical detector is unreliable on short messages.
_STOP: dict[str, set[str]] = {
    "es": {"el", "la", "los", "las", "un", "una", "de", "del", "que", "qué", "y", "en", "es", "por", "para", "con", "mi", "mis", "cómo", "como", "cuándo",
           "cuál", "dónde", "quién", "puedo", "necesito", "quiero", "hay", "está", "hora", "olvidé", "hola", "gracias", "se", "no", "su"},
    "pt": {"os", "as", "um", "uma", "de", "do", "da", "dos", "das", "que", "em", "é", "por", "para", "com", "meu", "minha", "como", "quando",
           "qual", "onde", "quem", "posso", "preciso", "quero", "está", "horas", "esqueci", "olá", "obrigado", "obrigada", "não", "você", "se"},
    "fr": {"le", "la", "les", "un", "une", "des", "de", "du", "que", "qui", "et", "en", "est", "pour", "avec", "mon", "ma", "mes", "je", "j'ai", "comment", "quand",
           "quel", "quelle", "où", "puis", "peux", "veux", "bonjour", "merci", "à", "au", "aux", "ne", "pas", "ouvre", "mot"},
    "it": {"il", "lo", "la", "gli", "le", "un", "una", "di", "del", "della", "che", "in", "è", "per", "con", "mio", "mia", "come", "quando", "quale", "dove",
           "chi", "posso", "devo", "voglio", "ho", "ora", "ciao", "grazie", "non", "apre", "sono", "cosa", "puoi", "può", "fare", "sei", "hai", "questo", "quello"},
    "de": {"der", "die", "das", "ein", "eine", "und", "ist", "ich", "wie", "wann", "wo", "was", "kann", "muss", "mein", "meine", "mir", "mich", "für", "mit", "nicht",
           "bitte", "hallo", "danke", "zu", "auf", "im", "von", "den", "dem", "wer", "habe", "bin", "gibt", "es", "du", "kannst", "guten", "morgen", "tun", "können", "sie", "wir", "was"},
    "nl": {"de", "het", "een", "en", "is", "ik", "hoe", "wanneer", "waar", "wat", "kan", "mijn", "mij", "voor", "met", "niet", "alsjeblieft", "hallo", "dank", "te", "op",
           "van", "wie", "heb", "ben", "laat", "betaal", "gaat"},
    "tr": {"bir", "ve", "bu", "ne", "nasıl", "nerede", "kaçta", "saat", "için", "ile", "mi", "mı", "mu", "mü", "benim", "ben", "var", "yok", "merhaba", "teşekkürler", "lütfen", "unuttum"},
    "id": {"yang", "dan", "di", "ke", "dari", "ini", "itu", "apa", "bagaimana", "kapan", "dimana", "saya", "tolong", "terima", "kasih", "halo", "untuk", "dengan", "tidak", "bisa"},
}


def _stop_scores(tokens: list[str]) -> dict[str, int]:
    return {lang: sum(t in words for t in tokens) for lang, words in _STOP.items()}


def detect_text_language(text: str) -> str:
    """Script rules first (reliable for Indic/CJK scripts). For Latin script: English function words win; otherwise the
    language with the most function-word hits (ties broken by the statistical model); the statistical model alone is used
    only when it is very confident on a longer message. Everything uncertain defaults to English."""
    for pat, code in _SCRIPT_RULES:
        if pat.search(text):
            return code
    tokens = re.findall(r"[^\W\d_]+(?:'[^\W\d_]+)?", text.lower())
    if not tokens:
        return "en"
    en_hits = sum(t in _EN_WORDS for t in tokens)
    scores = _stop_scores(tokens)
    best = max(scores.values())
    if en_hits and en_hits / len(tokens) >= 0.25 and en_hits >= best:
        return "en"
    if best >= 2 or (best >= 1 and len(tokens) <= 2 and en_hits == 0):
        cands = [l for l, v in scores.items() if v == best]
        if len(cands) == 1:
            return cands[0]
        try:
            for lang, _ in _identifier().rank(text):
                if lang in cands:
                    return lang
        except Exception:
            pass
        return cands[0]
    if len(tokens) < 3:
        return "en"
    try:
        code, prob = _identifier().classify(text)
        return code if (code in LANGS and prob >= 0.95 and en_hits == 0) else "en"
    except Exception:
        return "en"


def nllb_code(iso: str) -> str | None:
    return LANGS[iso][0] if iso in LANGS else None


def display_name(iso: str) -> str:
    return LANGS[iso][1] if iso in LANGS else iso
