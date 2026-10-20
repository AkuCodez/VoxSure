"""Fine-tune DistilBERT for VoxSure intent classification.

Usage: python ml/scripts/train_intent.py [--epochs 6] [--seed 42]
Saves model, tokenizer, label_map.json and train_config.json (incl. fitted
temperature) to ml/artifacts/intent_model/. Temperature scaling is fitted on the
VALIDATION split only; the test split is never touched here.
"""
from __future__ import annotations

import argparse
import json
import random
import time
from pathlib import Path

import numpy as np
import torch
from torch import nn
from transformers import AutoModelForSequenceClassification, AutoTokenizer

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "artifacts" / "intent_model"
BASE = "distilbert-base-uncased"
MAX_LEN = 48


def read(name: str) -> list[dict]:
    return [json.loads(l) for l in (DATA / f"{name}.jsonl").read_text(encoding="utf-8").splitlines()]


def encode(tok, texts):
    return tok(texts, padding=True, truncation=True, max_length=MAX_LEN, return_tensors="pt")


@torch.no_grad()
def logits_for(model, tok, texts, bs=64):
    model.eval()
    out = []
    for i in range(0, len(texts), bs):
        out.append(model(**encode(tok, texts[i:i + bs])).logits)
    return torch.cat(out)


def fit_temperature(logits: torch.Tensor, labels: torch.Tensor) -> float:
    log_t = torch.zeros(1, requires_grad=True)
    opt = torch.optim.LBFGS([log_t], lr=0.1, max_iter=100)
    ce = nn.CrossEntropyLoss()

    def closure():
        opt.zero_grad()
        loss = ce(logits / log_t.exp(), labels)
        loss.backward()
        return loss

    opt.step(closure)
    return float(log_t.exp().item())


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=6)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--lr", type=float, default=5e-5)
    ap.add_argument("--bs", type=int, default=16)
    args = ap.parse_args()

    random.seed(args.seed); np.random.seed(args.seed); torch.manual_seed(args.seed)
    train, val = read("train"), read("val")
    labels = sorted({r["intent"] for r in train})
    l2i = {l: i for i, l in enumerate(labels)}

    tok = AutoTokenizer.from_pretrained(BASE)
    model = AutoModelForSequenceClassification.from_pretrained(
        BASE, num_labels=len(labels),
        id2label={i: l for l, i in l2i.items()}, label2id=l2i)
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=0.01)
    steps = args.epochs * ((len(train) + args.bs - 1) // args.bs)
    sched = torch.optim.lr_scheduler.LambdaLR(
        opt, lambda s: min((s + 1) / (0.1 * steps), max(0.0, (steps - s) / (0.9 * steps))))

    vt = [r["text"] for r in val]
    vy = torch.tensor([l2i[r["intent"]] for r in val])
    history, best_acc, best_state = [], -1.0, None
    t0 = time.time()
    for ep in range(args.epochs):
        model.train()
        random.shuffle(train)
        total = 0.0
        for i in range(0, len(train), args.bs):
            b = train[i:i + args.bs]
            enc = encode(tok, [r["text"] for r in b])
            y = torch.tensor([l2i[r["intent"]] for r in b])
            loss = model(**enc, labels=y).loss
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step(); sched.step(); opt.zero_grad()
            total += loss.item() * len(b)
        acc = float((logits_for(model, tok, vt).argmax(1) == vy).float().mean())
        history.append({"epoch": ep + 1, "train_loss": total / len(train), "val_acc": acc})
        print(history[-1], f"{time.time() - t0:.0f}s", flush=True)
        if acc >= best_acc:
            best_acc = acc
            best_state = {k: v.clone() for k, v in model.state_dict().items()}
    model.load_state_dict(best_state)

    temperature = fit_temperature(logits_for(model, tok, vt), vy)
    OUT.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(OUT, safe_serialization=True)
    tok.save_pretrained(OUT)
    (OUT / "label_map.json").write_text(json.dumps(labels, indent=2), encoding="utf-8")
    (OUT / "train_config.json").write_text(json.dumps({
        "base_model": BASE, "seed": args.seed, "epochs": args.epochs, "lr": args.lr,
        "batch_size": args.bs, "max_len": MAX_LEN, "temperature": temperature,
        "n_train": len(train), "n_val": len(val), "best_val_acc": best_acc,
        "history": history, "model_version": "distilbert-intent-v1",
    }, indent=2), encoding="utf-8")
    print(f"saved to {OUT}; temperature={temperature:.3f}; best val acc={best_acc:.3f}")


if __name__ == "__main__":
    main()
