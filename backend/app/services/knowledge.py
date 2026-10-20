from __future__ import annotations

import json
from pathlib import Path


class KnowledgeBase:
    def __init__(self, path: Path):
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        self.intents: dict[str, dict] = data["intents"]
        self.notice: str = data.get("_notice", "")
        self.fallback_oos: str = data["fallback_out_of_scope"]
        self.fallback_repeated: str = data["fallback_repeated"]
        self.repair_prompt: str = data["repair_prompt"]
        self.clarify_prompt: str = data["clarify_prompt"]

    def answer(self, intent: str) -> str:
        return self.intents[intent]["answer"]

    def label(self, intent: str) -> str:
        return self.intents.get(intent, {}).get("label", intent.replace("_", " "))

    def has(self, intent: str) -> bool:
        return intent in self.intents
