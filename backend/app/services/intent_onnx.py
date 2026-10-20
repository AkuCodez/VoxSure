from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import onnxruntime as ort
from tokenizers import Tokenizer


class OnnxIntentClassifier:
    """DistilBERT intent classifier exported to ONNX (int8). Same interface as IntentClassifier, but needs only
    onnxruntime + tokenizers (no PyTorch / transformers), so it fits on small serverless hosts."""

    def __init__(self, model_dir: Path, max_len: int | None = None):
        self.dir = Path(model_dir)
        cfg = json.loads((self.dir / "train_config.json").read_text(encoding="utf-8"))
        self.labels: list[str] = json.loads((self.dir / "label_map.json").read_text(encoding="utf-8"))
        self.temperature: float = float(cfg.get("temperature", 1.0))
        self.version: str = cfg.get("model_version", "unknown") + "-onnx-int8"
        self.max_len = max_len or int(cfg.get("max_len", 48))
        self.tok = Tokenizer.from_file(str(self.dir / "tokenizer.json"))
        self.tok.enable_truncation(max_length=self.max_len)
        self.tok.enable_padding(pad_id=self.tok.token_to_id("[PAD]") or 0, pad_token="[PAD]")
        so = ort.SessionOptions()
        so.intra_op_num_threads = 1
        self.sess = ort.InferenceSession(str(self.dir / "model.onnx"), so, providers=["CPUExecutionProvider"])
        self._inputs = {i.name for i in self.sess.get_inputs()}

    def predict_batch(self, texts: list[str], temperature: float | None = None) -> list[dict[str, float]]:
        t = self.temperature if temperature is None else temperature
        out: list[dict[str, float]] = []
        for i in range(0, len(texts), 32):
            enc = self.tok.encode_batch(texts[i:i + 32])
            feed = {"input_ids": np.array([e.ids for e in enc], dtype=np.int64),
                    "attention_mask": np.array([e.attention_mask for e in enc], dtype=np.int64)}
            logits = self.sess.run(None, {k: v for k, v in feed.items() if k in self._inputs})[0] / t
            logits = logits - logits.max(axis=1, keepdims=True)
            p = np.exp(logits)
            p /= p.sum(axis=1, keepdims=True)
            out += [dict(zip(self.labels, row.tolist())) for row in p]
        return out

    def predict(self, text: str) -> dict[str, float]:
        return self.predict_batch([text])[0]
