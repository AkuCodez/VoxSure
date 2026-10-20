"""Export the trained DistilBERT intent model to a small int8 ONNX file for the lite (serverless) deployment,
then measure how closely it matches the PyTorch model on the validation and test splits.

Run:  python ml/scripts/export_onnx.py
Out:  ml/artifacts/intent_onnx/{model.onnx, tokenizer.json, label_map.json, train_config.json}
      ml/reports/onnx_parity.json
Parity is reported, not assumed: prediction agreement, probability differences, macro-F1 on test for both models,
and how often the recovery policy makes the same decision with either model.
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import numpy as np
import torch
from onnxruntime.quantization import QuantType, quantize_dynamic
from sklearn.metrics import f1_score
from transformers import AutoModelForSequenceClassification, AutoTokenizer

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / "backend"))
from app.core.policy import PolicyParams, decide  # noqa: E402
from app.services.intent import IntentClassifier  # noqa: E402
from app.services.intent_onnx import OnnxIntentClassifier  # noqa: E402

SRC = ROOT / "artifacts" / "intent_model"
OUT = ROOT / "artifacts" / "intent_onnx"
MAX_LEN = 48


def export() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    tok = AutoTokenizer.from_pretrained(SRC)
    model = AutoModelForSequenceClassification.from_pretrained(SRC).eval()
    dummy = tok(["when does the library open", "hi"], padding=True, truncation=True, max_length=MAX_LEN, return_tensors="pt")
    fp32 = OUT / "model_fp32.onnx"
    with torch.no_grad():
        torch.onnx.export(model, (dummy["input_ids"], dummy["attention_mask"]), str(fp32),
                          input_names=["input_ids", "attention_mask"], output_names=["logits"],
                          dynamic_axes={"input_ids": {0: "batch", 1: "seq"}, "attention_mask": {0: "batch", 1: "seq"}, "logits": {0: "batch"}},
                          opset_version=17, do_constant_folding=True)
    quantize_dynamic(str(fp32), str(OUT / "model.onnx"), weight_type=QuantType.QInt8, per_channel=True)
    fp32.unlink()
    for f in ("tokenizer.json", "label_map.json", "train_config.json"):
        shutil.copy(SRC / f, OUT / f)
    print(f"exported int8 ONNX: {(OUT / 'model.onnx').stat().st_size / 1e6:.1f} MB")


def read(name: str) -> list[dict]:
    return [json.loads(l) for l in (ROOT / "data" / f"{name}.jsonl").read_text(encoding="utf-8").splitlines()]


def parity() -> dict:
    pt, ox = IntentClassifier(SRC), OnnxIntentClassifier(OUT)
    policy = PolicyParams.load(ROOT / "artifacts" / "policy.json")
    labels = pt.labels
    res: dict = {"onnx_size_mb": round((OUT / "model.onnx").stat().st_size / 1e6, 1), "quantization": "dynamic int8, per-channel weights"}
    for split in ("val", "test"):
        rows = read(split)
        texts = [r["text"] for r in rows]
        gold = [r["intent"] for r in rows]
        p_pt, p_ox = pt.predict_batch(texts), ox.predict_batch(texts)
        a_pt = [max(p, key=p.get) for p in p_pt]
        a_ox = [max(p, key=p.get) for p in p_ox]
        diffs = [abs(p_pt[i][l] - p_ox[i][l]) for i in range(len(texts)) for l in labels]
        same_decision = np.mean([decide(a, policy).action == decide(b, policy).action and decide(a, policy).intent == decide(b, policy).intent
                                 for a, b in zip(p_pt, p_ox)])
        res[split] = {
            "n": len(rows),
            "prediction_agreement": float(np.mean([x == y for x, y in zip(a_pt, a_ox)])),
            "accuracy_pytorch": float(np.mean([x == g for x, g in zip(a_pt, gold)])),
            "accuracy_onnx": float(np.mean([x == g for x, g in zip(a_ox, gold)])),
            "macro_f1_pytorch": float(f1_score(gold, a_pt, average="macro", labels=labels, zero_division=0)),
            "macro_f1_onnx": float(f1_score(gold, a_ox, average="macro", labels=labels, zero_division=0)),
            "mean_abs_probability_difference": float(np.mean(diffs)),
            "max_abs_probability_difference": float(np.max(diffs)),
            "policy_decision_agreement": float(same_decision),
        }
        r = res[split]
        print(f"{split}: agree={r['prediction_agreement']:.3f} acc pt={r['accuracy_pytorch']:.3f} onnx={r['accuracy_onnx']:.3f} "
              f"F1 pt={r['macro_f1_pytorch']:.3f} onnx={r['macro_f1_onnx']:.3f} meanΔp={r['mean_abs_probability_difference']:.4f} "
              f"policy-same={r['policy_decision_agreement']:.3f}")
    (ROOT / "reports" / "onnx_parity.json").write_text(json.dumps(res, indent=2), encoding="utf-8")
    return res


if __name__ == "__main__":
    export()
    parity()
