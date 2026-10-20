"""Evaluate VoxSure end-to-end at the text level and tune/freeze the recovery policy.

Stages (all numbers written to ml/reports/intent_eval.json, nothing hand-typed):
  1. Experiment A: text-only intent classification on the held-out TEST split
     (TF-IDF+LogReg baseline vs fine-tuned DistilBERT): accuracy, macro-F1, per-class
     P/R/F1, confusion matrix, calibration (ECE) before/after temperature scaling.
  2. Policy tuning on VALIDATION data only (val utterances + ambiguous_val) -> policy.json
  3. Experiments B/C/E on TEST (+ ambiguous_test + a noise stress set):
       B = argmax pipeline with no clarification;  C = full error-aware policy
  4. Experiment D: correction-memory ablation (simulated repeat scenarios).

Usage:  python ml/scripts/evaluate_intent.py
"""
from __future__ import annotations

import itertools
import json
import random
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / "backend"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.core.policy import OOS, SMALLTALK, PolicyParams, decide  # noqa: E402
from app.services.intent import IntentClassifier  # noqa: E402
from build_dataset import ASR_SUBS, normalise_asr  # noqa: E402
from sklearn.feature_extraction.text import TfidfVectorizer  # noqa: E402
from sklearn.linear_model import LogisticRegression  # noqa: E402
from sklearn.metrics import accuracy_score, confusion_matrix, precision_recall_fscore_support  # noqa: E402

DATA = ROOT / "data"
MODEL_DIR = ROOT / "artifacts" / "intent_model"
REPORT = ROOT / "reports"
SEED = 42


def read(name):
    return [json.loads(l) for l in (DATA / f"{name}.jsonl").read_text(encoding="utf-8").splitlines()]


def ece(probs: np.ndarray, y: np.ndarray, bins: int = 10) -> float:
    conf, pred = probs.max(1), probs.argmax(1)
    edges, total = np.linspace(0, 1, bins + 1), 0.0
    for lo, hi in zip(edges[:-1], edges[1:]):
        m = (conf > lo) & (conf <= hi)
        if m.any():
            total += m.mean() * abs((pred[m] == y[m]).mean() - conf[m].mean())
    return float(total)


def clf_metrics(y, pred, labels):
    p, r, f, s = precision_recall_fscore_support(y, pred, labels=range(len(labels)), zero_division=0)
    return {
        "accuracy": float(accuracy_score(y, pred)),
        "macro_f1": float(f.mean()),
        "per_class": {l: {"precision": float(p[i]), "recall": float(r[i]), "f1": float(f[i]), "support": int(s[i])}
                      for i, l in enumerate(labels)},
        "confusion_matrix": confusion_matrix(y, pred, labels=range(len(labels))).tolist(),
    }


# ---------- outcome scoring ----------
def score(rows, decisions):
    """rows: dict(kind, gold|plausible). Returns counts incl. wrong-answer rate."""
    c = dict(n=len(rows), correct_answer=0, wrong_answer=0, clarify=0, fallback=0,
             appropriate_clarify=0, unnecessary_clarify=0, correct_fallback=0, missed_fallback=0,
             recoverable_by_option=0)
    for r, d in zip(rows, decisions):
        a = d.action
        if r["kind"] == "ambiguous":
            if a == "answer":
                c["wrong_answer"] += 1  # confident answer to an under-specified request
            elif a == "clarify":
                c["clarify"] += 1; c["appropriate_clarify"] += 1
                if d.clarify_kind == "disambiguate" and set(d.options) & set(r["plausible"]):
                    c["recoverable_by_option"] += 1
            else:
                c["fallback"] += 1
        elif r["gold"] == OOS:
            if a == "answer":
                c["wrong_answer"] += 1
            elif a == "fallback":
                c["fallback"] += 1; c["correct_fallback"] += 1
            else:
                c["clarify"] += 1
        else:  # clear in-scope (incl. small talk)
            if a == "answer":
                if d.intent == r["gold"]:
                    c["correct_answer"] += 1
                else:
                    c["wrong_answer"] += 1
            elif a == "clarify":
                c["clarify"] += 1; c["unnecessary_clarify"] += 1
                if d.clarify_kind == "disambiguate" and r["gold"] in d.options:
                    c["recoverable_by_option"] += 1
            else:
                c["fallback"] += 1; c["missed_fallback"] += 1
    n = c["n"]
    c["wrong_answer_rate"] = c["wrong_answer"] / n
    c["clarification_rate"] = c["clarify"] / n
    n_clear = sum(r["kind"] == "clear" for r in rows)
    c["n_clear"] = n_clear
    c["task_completion_one_turn"] = (c["correct_answer"] + c["correct_fallback"]) / max(1, sum(
        1 for r in rows if r["kind"] == "clear"))
    c["task_completion_with_option_click"] = (c["correct_answer"] + c["correct_fallback"] + sum(
        1 for r, d in zip(rows, decisions) if r["kind"] == "clear" and d.action == "clarify"
        and d.clarify_kind == "disambiguate" and r["gold"] in d.options)) / max(1, n_clear)
    return c


def baseline_decision(probs):
    """Experiment B: argmax, no clarification. Out-of-scope prediction -> fallback."""
    from app.core.policy import Decision
    top = max(probs, key=probs.get)
    return Decision("fallback", reason="oos") if top == OOS else Decision("answer", intent=top, reason="argmax")


def utility(c):
    return (c["correct_answer"] + c["correct_fallback"] + 0.6 * c["appropriate_clarify"]
            - 3.0 * c["wrong_answer"] - 0.6 * c["unnecessary_clarify"] - 0.5 * c["missed_fallback"])


def stress(text, rng):
    """Heavier ASR-like corruption for experiment E (independent of training noise)."""
    words = normalise_asr(text).split()
    out = []
    for w in words:
        r = rng.random()
        if r < 0.15 and len(words) > 3:
            continue                                  # dropped word
        if r < 0.30 and len(w) > 4:
            i = rng.randrange(1, len(w) - 1)          # character swap / deletion
            w = w[:i] + w[i + 1:] if rng.random() < 0.5 else w[:i - 1] + w[i] + w[i - 1] + w[i + 1:]
        elif w in ASR_SUBS and rng.random() < 0.7:
            w = ASR_SUBS[w]
        out.append(w)
    return " ".join(out) or text


def main() -> None:
    random.seed(SEED); np.random.seed(SEED)
    REPORT.mkdir(parents=True, exist_ok=True)
    train, val, test = read("train"), read("val"), read("test")
    amb_val, amb_test = read("ambiguous_val"), read("ambiguous_test")
    labels = json.loads((MODEL_DIR / "label_map.json").read_text())
    l2i = {l: i for i, l in enumerate(labels)}
    ytest = np.array([l2i[r["intent"]] for r in test])
    yval = np.array([l2i[r["intent"]] for r in val])
    report: dict = {"seed": SEED, "labels": labels,
                    "sizes": {"train": len(train), "val": len(val), "test": len(test),
                              "ambiguous_val": len(amb_val), "ambiguous_test": len(amb_test)}}

    # ---- Experiment A ----
    vec = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True)
    Xtr = vec.fit_transform([r["text"] for r in train])
    lr = LogisticRegression(max_iter=2000, C=10, random_state=SEED).fit(Xtr, [l2i[r["intent"]] for r in train])
    base_pred = lr.predict(vec.transform([r["text"] for r in test]))
    report["A_baseline_tfidf_logreg"] = clf_metrics(ytest, base_pred, labels)

    clf = IntentClassifier(MODEL_DIR)
    T = clf.temperature
    def probs_matrix(rows, temp):
        return np.array([[p[l] for l in labels] for p in clf.predict_batch([r["text"] for r in rows], temp)])
    p_test_T, p_test_1 = probs_matrix(test, T), probs_matrix(test, 1.0)
    p_val_T, p_val_1 = probs_matrix(val, T), probs_matrix(val, 1.0)
    report["A_distilbert"] = clf_metrics(ytest, p_test_T.argmax(1), labels)
    report["calibration"] = {"temperature": T,
                             "ece_test_uncalibrated": ece(p_test_1, ytest), "ece_test_calibrated": ece(p_test_T, ytest),
                             "ece_val_uncalibrated": ece(p_val_1, yval), "ece_val_calibrated": ece(p_val_T, yval),
                             "mean_conf_test_calibrated": float(p_test_T.max(1).mean()),
                             "acc_test": float((p_test_T.argmax(1) == ytest).mean())}

    # ---- policy tuning: VALIDATION ONLY ----
    def build_rows(clear, amb):
        return ([{"kind": "clear", "gold": r["intent"], "text": r["text"]} for r in clear] +
                [{"kind": "ambiguous", "plausible": r["plausible"], "text": r["text"]} for r in amb])
    val_rows = build_rows(val, amb_val)
    val_probs = clf.predict_batch([r["text"] for r in val_rows])
    best, best_u, grid_log = None, -1e9, []
    for t_high, margin, t_low, t_oos in itertools.product(
            [0.5, 0.6, 0.7, 0.8, 0.9, 0.95], [0.0, 0.1, 0.2, 0.3, 0.4, 0.5], [0.15, 0.25, 0.35], [0.4, 0.5, 0.6]):
        P = PolicyParams(t_high=t_high, margin=margin, t_low=t_low, t_oos=t_oos)
        c = score(val_rows, [decide(p, P) for p in val_probs])
        u = utility(c) / c["n"]
        grid_log.append((u, t_high, margin, t_low, t_oos))
        if u > best_u + 1e-9:
            best, best_u = P, u
    # tie-break toward safer (stricter) settings among near-equal utilities
    near = [g for g in grid_log if g[0] >= best_u - 0.005]
    near.sort(key=lambda g: (-g[1], -g[2]))
    _, th, mg, tl, to = near[0]
    best = PolicyParams(t_high=th, margin=mg, t_low=tl, t_oos=to)
    val_score = score(val_rows, [decide(p, best) for p in val_probs])
    policy_doc = {"params": best.__dict__, "tuned_on": "val + ambiguous_val only", "seed": SEED,
                  "objective": "mean(correct + 0.6*appropriate_clarify - 3*wrong - 0.3*unnecessary_clarify - 0.5*missed_fallback)",
                  "val_score": val_score, "val_utility": utility(val_score) / val_score["n"]}
    (ROOT / "artifacts" / "policy.json").write_text(json.dumps(policy_doc, indent=2), encoding="utf-8")
    report["policy"] = policy_doc

    # ---- Experiments B / C on TEST (policy frozen) ----
    test_rows = build_rows(test, amb_test)
    tp = clf.predict_batch([r["text"] for r in test_rows])
    report["BC_test"] = {
        "B_argmax_no_clarification": score(test_rows, [baseline_decision(p) for p in tp]),
        "C_error_aware": score(test_rows, [decide(p, best) for p in tp]),
    }
    # clear-only and ambiguous-only breakdown
    for name, sel in (("clear_only", lambda r: r["kind"] == "clear"), ("ambiguous_only", lambda r: r["kind"] == "ambiguous")):
        idx = [i for i, r in enumerate(test_rows) if sel(r)]
        rr, pp = [test_rows[i] for i in idx], [tp[i] for i in idx]
        report["BC_test"][f"B_{name}"] = score(rr, [baseline_decision(p) for p in pp])
        report["BC_test"][f"C_{name}"] = score(rr, [decide(p, best) for p in pp])

    # ---- Experiment E: noise stress ----
    rng = random.Random(SEED)
    stress_clear = [{"text": stress(r["text"], rng), "intent": r["intent"]} for r in test]
    stress_amb = [{"text": stress(r["text"], rng), "plausible": r["plausible"]} for r in amb_test]
    s_rows = build_rows(stress_clear, stress_amb)
    sp = clf.predict_batch([r["text"] for r in s_rows])
    report["E_stress"] = {
        "examples": [r["text"] for r in s_rows[:8]],
        "text_only_accuracy_on_stressed_clear": float(np.mean([
            max(p, key=p.get) == r["gold"] for p, r in zip(sp, s_rows) if r["kind"] == "clear"])),
        "B_argmax_no_clarification": score(s_rows, [baseline_decision(p) for p in sp]),
        "C_error_aware": score(s_rows, [decide(p, best) for p in sp]),
    }

    # ---- Experiment D: correction-memory ablation (simulated) ----
    # Scenario: user speaks stressed (mis-heard) utterance; if the system does not answer
    # correctly, the user edits to the clean text (and, in the 'memory' arm, opts in to remember).
    # Later the SAME mis-heard utterance recurs. Measures pass-2 correct-answer rate.
    clean_by_stress = {s["text"]: r["intent"] for s, r in zip(stress_clear, test)}
    memory: dict[str, str] = {}
    pass1_fail = 0
    for s, r in zip(stress_clear, test):
        p = clf.predict(s["text"]); d = decide(p, best)
        if not (d.action == "answer" and d.intent == r["intent"]):
            pass1_fail += 1
            memory[normalise_asr(s["text"])] = r["text"]
    def pass2(use_memory: bool):
        ok = 0
        for s, r in zip(stress_clear, test):
            text = memory.get(normalise_asr(s["text"]), s["text"]) if use_memory else s["text"]
            d = decide(clf.predict(text), best)
            ok += d.action == "answer" and d.intent == r["intent"]
        return ok / len(test)
    report["D_memory_ablation"] = {
        "n_stressed_utterances": len(test), "pass1_not_answered_correctly": pass1_fail,
        "pass2_correct_answer_rate_memory_off": pass2(False), "pass2_correct_answer_rate_memory_on": pass2(True),
        "caveat": "Simulated upper bound: memory only helps EXACT repeats of an already-corrected utterance; it does not generalise.",
    }

    (REPORT / "intent_eval.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    _plot_confusion(report["A_distilbert"]["confusion_matrix"], labels)
    a, b = report["A_baseline_tfidf_logreg"], report["A_distilbert"]
    print(f"A  baseline macro-F1={a['macro_f1']:.3f} acc={a['accuracy']:.3f} | DistilBERT macro-F1={b['macro_f1']:.3f} acc={b['accuracy']:.3f}")
    print("ECE test: %.3f -> %.3f (T=%.2f)" % (report["calibration"]["ece_test_uncalibrated"], report["calibration"]["ece_test_calibrated"], T))
    print("policy:", best)
    for k in ("B_argmax_no_clarification", "C_error_aware"):
        c = report["BC_test"][k]
        print(f"{k:28s} wrong={c['wrong_answer_rate']:.3f} clarify={c['clarification_rate']:.3f} completion={c['task_completion_one_turn']:.3f}")
    for k in ("B_argmax_no_clarification", "C_error_aware"):
        c = report["E_stress"][k]
        print(f"stress {k:22s} wrong={c['wrong_answer_rate']:.3f} clarify={c['clarification_rate']:.3f}")
    print("D:", {k: v for k, v in report["D_memory_ablation"].items() if k != "caveat"})


def _plot_confusion(cm, labels):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    cm = np.array(cm)
    fig, ax = plt.subplots(figsize=(8, 7))
    ax.imshow(cm, cmap="Blues")
    ax.set_xticks(range(len(labels))); ax.set_yticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=60, ha="right", fontsize=8); ax.set_yticklabels(labels, fontsize=8)
    for i, j in itertools.product(range(len(labels)), repeat=2):
        if cm[i, j]:
            ax.text(j, i, cm[i, j], ha="center", va="center", fontsize=7, color="white" if cm[i, j] > cm.max() / 2 else "black")
    ax.set_xlabel("Predicted"); ax.set_ylabel("True"); ax.set_title("DistilBERT confusion matrix (test)")
    fig.tight_layout(); fig.savefig(REPORT / "confusion_matrix.png", dpi=140)


if __name__ == "__main__":
    main()
