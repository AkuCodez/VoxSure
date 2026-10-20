"""Evaluate the multilingual text pipeline: language ID -> NLLB translation to English -> DistilBERT -> policy.

Per language (typed input) it reports language-ID accuracy, intent accuracy / macro-F1 after translation,
wrong-answer rate with and without the recovery policy, clarification rate, and translation latency.
English is the control. Also writes backend/app/data/language_status.json (which languages the UI
may label "verified").

PRE-REGISTERED criterion (fixed before running; not tuned on these results):
    verified  <=>  intent accuracy >= 0.80  AND  wrong_answer_rate_C <= 0.10  AND  language-ID accuracy >= 0.95
Speech accuracy (WER) for these languages is NOT measured here: it needs human recordings.

Usage: python ml/scripts/evaluate_multilingual.py     (needs ml/artifacts/nllb-ct2, see prepare_nllb.py)
"""
from __future__ import annotations

import json
import statistics
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / "backend"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.core.languages import detect_text_language, display_name  # noqa: E402
from app.core.policy import OOS, PolicyParams, decide  # noqa: E402
from app.services.intent import IntentClassifier  # noqa: E402
from app.services.knowledge import KnowledgeBase, numbers_preserved  # noqa: E402
from app.services.translate import Translator  # noqa: E402
from evaluate_intent import baseline_decision, score  # noqa: E402
from sklearn.metrics import f1_score  # noqa: E402

THRESH = {"accuracy": 0.80, "wrong_answer_rate_C": 0.10, "lang_id_accuracy": 0.95}


def main() -> None:
    rows = [json.loads(l) for l in (ROOT / "data" / "multilingual_test.jsonl").read_text(encoding="utf-8").splitlines()]
    clf = IntentClassifier(ROOT / "artifacts" / "intent_model")
    tr = Translator(ROOT / "artifacts" / "nllb-ct2")
    policy = PolicyParams.load(ROOT / "artifacts" / "policy.json")
    labels = clf.labels
    out: dict = {"languages": {}, "criterion": THRESH, "n_per_language": 47,
                 "notes": ["Test sentences were written by the author and are not verified by native speakers.",
                           "Typed text only: speech recognition accuracy for these languages was not measured (no human recordings).",
                           "Verified = intent accuracy >= 80%, wrong-answer rate with recovery <= 10%, language-ID accuracy >= 95% (fixed in advance)."],
                 "translation_model": "NLLB-200 distilled 600M (int8, CTranslate2)"}
    verified = []
    for lang in ("en", "hi", "pa", "de"):
        lr = [r for r in rows if r["lang"] == lang]
        detected = [detect_text_language(r["text"]) for r in lr]
        lid = float(np.mean([d == lang for d in detected]))
        lat, en_texts = [], []
        for r in lr:
            t0 = time.perf_counter()
            en_texts.append(tr.translate(r["text"], lang, "en"))
            lat.append(time.perf_counter() - t0)
        probs = clf.predict_batch(en_texts)
        gold = [r["intent"] for r in lr]
        pred = [max(p, key=p.get) for p in probs]
        acc = float(np.mean([a == b for a, b in zip(pred, gold)]))
        f1 = float(f1_score(gold, pred, average="macro", labels=labels, zero_division=0))
        srows = [{"kind": "clear", "gold": g, "text": t} for g, t in zip(gold, en_texts)]
        sb = score(srows, [baseline_decision(p) for p in probs])
        sc = score(srows, [decide(p, policy) for p in probs])
        ok = acc >= THRESH["accuracy"] and sc["wrong_answer_rate"] <= THRESH["wrong_answer_rate_C"] and lid >= THRESH["lang_id_accuracy"]
        if ok and lang != "en":
            verified.append(lang)
        mistakes = [{"text": r["text"], "english": e, "gold": g, "pred": p} for r, e, g, p in zip(lr, en_texts, gold, pred) if g != p][:8]
        out["languages"][lang] = {
            "name": display_name(lang), "n": len(lr), "accuracy": acc, "macro_f1": f1, "lang_id_accuracy": lid,
            "wrong_answer_rate_B": sb["wrong_answer_rate"], "wrong_answer_rate_C": sc["wrong_answer_rate"],
            "clarification_rate_C": sc["clarification_rate"], "task_completion_one_turn_C": sc["task_completion_one_turn"],
            "translate_latency_s_median": statistics.median(lat), "translate_latency_s_p95": float(np.percentile(lat, 95)),
            "verified": bool(ok or lang == "en"), "sample_errors": mistakes,
            "sample_translations": [{"text": r["text"], "english": e} for r, e in list(zip(lr, en_texts))[:4]],
        }
        print(f"{lang}: acc={acc:.3f} f1={f1:.3f} langID={lid:.3f} wrongB={sb['wrong_answer_rate']:.3f} "
              f"wrongC={sc['wrong_answer_rate']:.3f} clarifyC={sc['clarification_rate']:.3f} "
              f"translate p50={statistics.median(lat):.2f}s verified={ok}", flush=True)

    # ---- reply side: does machine translation preserve the numbers/times in the fixed answers? ----
    kb = KnowledgeBase(ROOT.parent / "backend" / "app" / "data" / "knowledge_base.json")
    numeric = [k for k, v in kb.intents.items() if any(ch.isdigit() for ch in v["answer"])]
    mt_check = {}
    for lang in ("hi", "pa", "de", "fr", "es"):
        flagged = [k for k in numeric if not numbers_preserved(kb.answer(k), tr.translate(kb.answer(k), "en", lang))]
        mt_check[lang] = {"answers_with_numbers": len(numeric), "numbers_changed_by_machine_translation": len(flagged), "which": flagged}
        print(f"MT number check {lang}: {len(flagged)}/{len(numeric)} answers changed numbers {flagged}", flush=True)
    out["machine_translation_number_check"] = mt_check
    out["reply_policy"] = ("hi, pa and de replies use hand-written text (not machine translated). Other languages use NLLB; "
                           "replies whose numbers changed are flagged to the user.")

    (ROOT / "reports" / "multilingual_eval.json").write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    status = {"verified": verified, "criterion": THRESH,
              "measured_on": "ml/data/multilingual_test.jsonl (typed text; author-written, not native-verified)",
              "note": "Languages not listed are best effort: translation is attempted but accuracy has not been measured."}
    (ROOT.parent / "backend" / "app" / "data" / "language_status.json").write_text(json.dumps(status, indent=2), encoding="utf-8")
    print("verified languages:", verified)


if __name__ == "__main__":
    main()
