from __future__ import annotations

import json
from pathlib import Path

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer


class IntentClassifier:
    """Fine-tuned DistilBERT with temperature-scaled softmax (temperature fitted on val)."""

    def __init__(self, model_dir: Path, max_len: int | None = None):
        self.dir = Path(model_dir)
        cfg = json.loads((self.dir / "train_config.json").read_text(encoding="utf-8"))
        self.labels: list[str] = json.loads((self.dir / "label_map.json").read_text(encoding="utf-8"))
        self.temperature: float = float(cfg.get("temperature", 1.0))
        self.version: str = cfg.get("model_version", "unknown")
        self.max_len = max_len or int(cfg.get("max_len", 48))
        self.tok = AutoTokenizer.from_pretrained(self.dir)
        self.model = AutoModelForSequenceClassification.from_pretrained(self.dir).eval()
        torch.set_num_threads(max(1, min(4, torch.get_num_threads())))

    @torch.no_grad()
    def predict_batch(self, texts: list[str], temperature: float | None = None) -> list[dict[str, float]]:
        t = self.temperature if temperature is None else temperature
        out: list[dict[str, float]] = []
        for i in range(0, len(texts), 64):
            enc = self.tok(texts[i:i + 64], padding=True, truncation=True,
                           max_length=self.max_len, return_tensors="pt")
            probs = torch.softmax(self.model(**enc).logits / t, dim=-1)
            out += [dict(zip(self.labels, row.tolist())) for row in probs]
        return out

    def predict(self, text: str) -> dict[str, float]:
        return self.predict_batch([text])[0]
