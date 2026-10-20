"""Assemble every measured result into backend/app/data/evaluation.json for the in-app dashboard.

Nothing is typed in by hand: all values are read from the report files produced by
evaluate_intent.py / evaluate_speech.py / evaluate_multilingual.py and from the dataset stats.
Re-run after any evaluation:  python ml/scripts/export_evaluation.py
"""
from __future__ import annotations

import datetime as dt
import glob
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT.parent / "backend" / "app" / "data" / "evaluation.json"


def load(p: Path):
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def main() -> None:
    intent = load(ROOT / "reports" / "intent_eval.json")
    if intent is None:
        raise SystemExit("run ml/scripts/evaluate_intent.py first")
    stats = load(ROOT / "data" / "stats.json") or {}
    cfg = load(ROOT / "artifacts" / "intent_model" / "train_config.json") or {}
    speech_files = sorted(glob.glob(str(ROOT / "reports" / "speech_eval_*.json")))
    speech = load(Path(speech_files[-1])) if speech_files else None
    multi = load(ROOT / "reports" / "multilingual_eval.json")
    human = load(ROOT / "reports" / "human_speech_eval.json")

    doc = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "dataset": {"seed_utterances": stats.get("n_seed_utterances"), "sizes": intent["sizes"],
                    "classes": intent["labels"], "provenance": "Author-written seeds expanded programmatically; no real users."},
        "model": {"name": cfg.get("model_version"), "base": cfg.get("base_model"), "epochs": cfg.get("epochs"),
                  "best_val_acc": cfg.get("best_val_acc"), "temperature": cfg.get("temperature"), "seed": cfg.get("seed")},
        "intent": {
            "baseline": {k: intent["A_baseline_tfidf_logreg"][k] for k in ("accuracy", "macro_f1")},
            "distilbert": {k: intent["A_distilbert"][k] for k in ("accuracy", "macro_f1")},
            "per_class": {l: {"distilbert_f1": intent["A_distilbert"]["per_class"][l]["f1"],
                              "baseline_f1": intent["A_baseline_tfidf_logreg"]["per_class"][l]["f1"],
                              "support": intent["A_distilbert"]["per_class"][l]["support"]} for l in intent["labels"]},
            "confusion_matrix": intent["A_distilbert"]["confusion_matrix"],
            "calibration": intent["calibration"],
            "bootstrap_95ci": intent.get("bootstrap_95ci"),
        },
        "policy": {"params": intent["policy"]["params"], "tuned_on": intent["policy"]["tuned_on"]},
        "recovery": {
            "B_no_clarification": intent["BC_test"]["B_argmax_no_clarification"],
            "C_error_aware": intent["BC_test"]["C_error_aware"],
            "stress_B": intent["E_stress"]["B_argmax_no_clarification"],
            "stress_C": intent["E_stress"]["C_error_aware"],
            "stress_text_accuracy": intent["E_stress"]["text_only_accuracy_on_stressed_clear"],
        },
        "memory_ablation": intent["D_memory_ablation"],
        "speech": None if speech is None else {
            "asr_model": speech["asr_model"], "n_utterances": speech["n_utterances"], "voices": speech["voices"],
            "audio_kind": "synthetic text-to-speech (2 Windows voices); not human speech",
            "conditions": {c: {"wer": v["with_domain_prompt"]["wer"], "wer_no_prompt": (v.get("no_prompt") or {}).get("wer"),
                               "auto_detect": v.get("auto_detect"),
                               "latency_median_s": v["with_domain_prompt"]["latency_s_median"],
                               "latency_p95_s": v["with_domain_prompt"]["latency_s_p95"],
                               "pipeline_B": {k: v["with_domain_prompt"]["pipeline_B_argmax"][k] for k in ("wrong_answer_rate", "clarification_rate", "task_completion_one_turn")},
                               "pipeline_C": {k: v["with_domain_prompt"]["pipeline_C_error_aware"][k] for k in ("wrong_answer_rate", "clarification_rate", "task_completion_one_turn")}}
                           for c, v in speech["conditions"].items()}},
        "multilingual": multi,
        "human_speech": human,
        "limitations": [
            "Dataset is author-written and small (2 distinct held-out phrasings per class); real-user accuracy will be lower.",
            "Speech results use synthetic text-to-speech audio only; no human recordings, accents or real microphones.",
            "The recovery policy trades usability for safety: it asks for clarification on roughly a third of turns.",
            "Hindi, Punjabi and German were tested on sentences written by the author, not verified by native speakers.",
        ],
    }
    OUT.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    print("wrote", OUT, f"({OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
