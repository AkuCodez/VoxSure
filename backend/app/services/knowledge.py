from __future__ import annotations

import json
import re
from pathlib import Path

_DIGITS = str.maketrans("०१२३४५६७८९੦੧੨੩੪੫੬੭੮੯٠١٢٣٤٥٦٧٨٩", "0123456789" * 3)


def numbers_in(text: str) -> set[str]:
    """Digit sequences in any common script, normalised to ASCII (for the translation numeric guard)."""
    return {str(int(n)) for n in re.findall(r"\d+", text.translate(_DIGITS))}   # "08" and "8" are the same number


def numbers_preserved(source: str, translated: str) -> bool:
    """True if every number in the English source also appears in the translation."""
    return numbers_in(source) <= numbers_in(translated)


class KnowledgeBase:
    """Reviewed English answers plus optional curated translations (hi, pa, de)."""

    def __init__(self, path: Path, translations_path: Path | None = None):
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        self.intents: dict[str, dict] = data["intents"]
        self.notice: str = data.get("_notice", "")
        self.fallback_oos: str = data["fallback_out_of_scope"]
        self.fallback_repeated: str = data["fallback_repeated"]
        self.repair_prompt: str = data["repair_prompt"]
        self.repair_typed: str = data.get("repair_prompt_typed", data["repair_prompt"])
        self.clarify_prompt: str = data["clarify_prompt"]
        self.clarify_template: str = data.get("clarify_prompt_template", "Just to be sure, do you mean {options}?")
        self.clarify_or: str = data.get("clarify_or", "or")
        self.last_updated: str = data.get("last_updated", "")
        self.curated: dict[str, dict] = {}
        tp = Path(translations_path) if translations_path else Path(path).with_name("translations.json")
        if tp.exists():
            raw = json.loads(tp.read_text(encoding="utf-8"))
            self.curated = {k: v for k, v in raw.items() if not k.startswith("_")}

    # ---- language-aware accessors (lang "en" or a curated language) ----
    def has_curated(self, lang: str) -> bool:
        return lang in self.curated

    def _pick(self, lang: str, intent: str, field: str) -> str:
        if lang != "en" and lang in self.curated:
            v = self.curated[lang]["intents"].get(intent, {}).get(field)
            if v:
                return v
        return self.intents.get(intent, {}).get(field) or ""

    def answer(self, intent: str, lang: str = "en") -> str:
        return self._pick(lang, intent, "answer")

    def label(self, intent: str, lang: str = "en") -> str:
        return self._pick(lang, intent, "label") or intent.replace("_", " ")

    def short(self, intent: str, lang: str = "en") -> str:
        return self._pick(lang, intent, "short") or self.label(intent, lang)

    def _text(self, lang: str, key: str, default: str) -> str:
        if lang != "en" and lang in self.curated:
            return self.curated[lang].get(key, default)
        return default

    def fallback(self, reason: str, lang: str = "en") -> str:
        if reason == "repeated_failure":
            return self._text(lang, "fallback_repeated", self.fallback_repeated)
        return self._text(lang, "fallback_out_of_scope", self.fallback_oos)

    def repair(self, lang: str = "en", typed: bool = False) -> str:
        if typed and lang == "en":
            return self.repair_typed
        return self._text(lang, "repair_prompt", self.repair_prompt)

    def has(self, intent: str) -> bool:
        return intent in self.intents

    def sources(self, intent: str | None) -> list[dict]:
        return list(self.intents.get(intent or "", {}).get("sources", []))

    def clarification_question(self, intents: list[str], lang: str = "en") -> str:
        """Targeted question naming the competing intents, e.g. 'do you mean A, B, or C?'."""
        names = [self.short(i, lang) for i in intents]
        word = self._text(lang, "clarify_or", self.clarify_or)
        template = self._text(lang, "clarify_prompt_template", self.clarify_template)
        joined = names[0] if len(names) == 1 else (f"{names[0]} {word} {names[1]}" if len(names) == 2
                                                    else f"{', '.join(names[:-1])}, {word} {names[-1]}")
        return template.format(options=joined)
