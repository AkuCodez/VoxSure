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
    "thanks", "thank", "our", "with", "from", "about", "tell", "not", "get", "a", "be", "if", "or", "any", "much", "many",
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


def detect_text_language(text: str) -> str:
    """Script rules first (reliable for Indic scripts); for Latin script be English-biased:
    common English words win, and another language needs >= 80% model confidence on 2+ words."""
    for pat, code in _SCRIPT_RULES:
        if pat.search(text):
            return code
    tokens = re.findall(r"[^\W\d_]+", text.lower())
    if not tokens:
        return "en"
    hits = sum(t in _EN_WORDS for t in tokens)
    if hits and hits / len(tokens) >= 0.25:
        return "en"
    if len(tokens) < 2:
        return "en"
    try:
        code, prob = _identifier().classify(text)
        return code if (code in LANGS and prob >= 0.80) else "en"
    except Exception:
        return "en"


def nllb_code(iso: str) -> str | None:
    return LANGS[iso][0] if iso in LANGS else None


def display_name(iso: str) -> str:
    return LANGS[iso][1] if iso in LANGS else iso
