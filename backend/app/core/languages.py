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


def detect_text_language(text: str) -> str:
    """Script-based detection first (reliable for Indic scripts), langid for Latin/Cyrillic/Arabic."""
    for pat, code in _SCRIPT_RULES:
        if pat.search(text):
            return code
    try:
        import langid
        langid.set_languages([c for c in LANGS if c not in ("pa", "ta", "te", "bn", "gu", "kn", "ml", "th", "ko", "ja", "zh")])
        code, _ = langid.classify(text)
        return code if code in LANGS else "en"
    except Exception:
        return "en"


def nllb_code(iso: str) -> str | None:
    return LANGS[iso][0] if iso in LANGS else None


def display_name(iso: str) -> str:
    return LANGS[iso][1] if iso in LANGS else iso
