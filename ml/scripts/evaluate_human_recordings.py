"""Score REAL human recordings (optional): WER/CER, language detection, and end-to-end behaviour per language.

Setup: record the sentences in ml/data/recording_script.md, save as <lang>_<nn>.<ext> (wav/m4a/mp3/webm/ogg/flac) in ml/human_audio/.
Run:   python ml/scripts/evaluate_human_recordings.py [--audio ml/human_audio] [--script ml/data/recording_script.md] [--model small]
Out:   ml/reports/human_speech_eval.json (picked up by export_evaluation.py and build_report.py)

Honest limits baked into the output: n is small, usually ONE speaker, and the reference sentences were written by the project author.
"""
from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / "backend"))

EXTS = (".wav", ".m4a", ".mp3", ".webm", ".ogg", ".flac", ".mp4")
LINE = re.compile(r"^\s*\d+\.\s+`([a-z]{2}_\d{2})`\s+(.+?)\s*$")


def norm(t: str) -> str:
    t = t.lower().replace("।", " ").replace("॥", " ")
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s']", " ", t, flags=re.UNICODE)).strip()


def parse_script(path: Path) -> dict[str, str]:
    refs = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        m = LINE.match(line)
        if m:
            refs[m.group(1)] = m.group(2)
    return refs


def find_audio(folder: Path, clip_id: str) -> Path | None:
    for ext in EXTS:
        p = folder / f"{clip_id}{ext}"
        if p.exists():
            return p
    return None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--audio", default=str(ROOT / "human_audio"))
    ap.add_argument("--script", default=str(ROOT / "data" / "recording_script.md"))
    ap.add_argument("--model", default="small")
    ap.add_argument("--out", default=str(ROOT / "reports" / "human_speech_eval.json"))
    args = ap.parse_args()

    audio_dir, refs = Path(args.audio), parse_script(Path(args.script))
    clips = {cid: find_audio(audio_dir, cid) for cid in refs} if audio_dir.exists() else {}
    found = {cid: p for cid, p in clips.items() if p}
    if not found:
        print(f"No recordings found in {audio_dir}.\nRecord the sentences in {args.script} and save them as hi_01.wav, pa_01.wav, de_01.wav ...")
        return

    import jiwer
    from faster_whisper import WhisperModel
    from app.core.languages import display_name
    from app.core.policy import PolicyParams, decide
    from app.services.intent import IntentClassifier
    from app.services.translate import Translator

    gold_by_text = {}
    for l in (ROOT / "data" / "multilingual_test.jsonl").read_text(encoding="utf-8").splitlines():
        r = json.loads(l)
        gold_by_text[r["text"]] = r["intent"]
    clf = IntentClassifier(ROOT / "artifacts" / "intent_model")
    policy = PolicyParams.load(ROOT / "artifacts" / "policy.json")
    tr = Translator(ROOT / "artifacts" / "nllb-ct2") if (ROOT / "artifacts" / "nllb-ct2" / "model.bin").exists() else None
    asr = WhisperModel(args.model, device="cpu", compute_type="int8")

    per: dict[str, dict] = {}
    for cid, path in sorted(found.items()):
        lang = cid.split("_")[0]
        ref = refs[cid]
        rec = per.setdefault(lang, {"refs": [], "hyp_forced": [], "hyp_auto": [], "detected": [], "lat": [], "intent_ok": [], "wrong": [], "answered": [], "examples": []})
        t0 = time.perf_counter()
        segs, info = asr.transcribe(str(path), beam_size=1, language=lang, vad_filter=True, condition_on_previous_text=False)
        hyp_forced = " ".join(s.text.strip() for s in segs).strip()
        rec["lat"].append(time.perf_counter() - t0)
        segs2, info2 = asr.transcribe(str(path), beam_size=1, language=None, vad_filter=True, condition_on_previous_text=False)
        hyp_auto = " ".join(s.text.strip() for s in segs2).strip()
        rec["refs"].append(norm(ref)); rec["hyp_forced"].append(norm(hyp_forced) or "<empty>"); rec["hyp_auto"].append(norm(hyp_auto) or "<empty>")
        rec["detected"].append(info2.language)
        # end-to-end from the language-forced transcript
        text_en = hyp_forced if (lang == "en" or tr is None) else tr.translate(hyp_forced, lang, "en")
        probs = clf.predict(text_en or "...")
        d = decide(probs, policy)
        gold = gold_by_text.get(ref)
        if gold:
            if d.action == "answer":
                rec["answered"].append(1); rec["intent_ok"].append(int(d.intent == gold)); rec["wrong"].append(int(d.intent != gold))
            else:
                rec["answered"].append(0); rec["intent_ok"].append(0); rec["wrong"].append(0)
        rec["examples"].append({"id": cid, "reference": ref, "heard": hyp_forced, "heard_auto": hyp_auto, "detected": info2.language})
        print(f"{cid}: ref='{ref[:40]}' heard='{hyp_forced[:40]}' detected={info2.language}", flush=True)

    out = {"asr_model": args.model, "audio": "human recordings (see notes)", "languages": {},
           "missing_clips": sorted(c for c, p in clips.items() if not p),
           "notes": ["Small sample, typically a single speaker; reference sentences were written by the project author (not native-verified).",
                     "WER on Hindi/Punjabi is sensitive to spelling variants (e.g. English loanwords in Latin vs native script); CER is reported alongside.",
                     "Forced-language decoding uses the language chosen in the app's picker; auto-detect is what the app does by default."]}
    for lang, r in per.items():
        n = len(r["refs"])
        out["languages"][lang] = {
            "name": display_name(lang), "n": n,
            "wer_forced_language": float(jiwer.wer(r["refs"], r["hyp_forced"])), "cer_forced_language": float(jiwer.cer(r["refs"], r["hyp_forced"])),
            "wer_auto_detect": float(jiwer.wer(r["refs"], r["hyp_auto"])),
            "language_detect_accuracy": float(np.mean([d == lang for d in r["detected"]])),
            "latency_s_median": statistics.median(r["lat"]),
            "end_to_end": {"n_scored": len(r["intent_ok"]), "answered_rate": float(np.mean(r["answered"])) if r["answered"] else None,
                           "answered_correctly": float(np.mean(r["intent_ok"])) if r["intent_ok"] else None,
                           "wrong_answer_rate": float(np.mean(r["wrong"])) if r["wrong"] else None},
            "examples": r["examples"][:5]}
        print(f"{lang}: n={n} WER={out['languages'][lang]['wer_forced_language']:.3f} CER={out['languages'][lang]['cer_forced_language']:.3f} "
              f"auto-WER={out['languages'][lang]['wer_auto_detect']:.3f} detect={out['languages'][lang]['language_detect_accuracy']:.2f}")
    Path(args.out).write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print("wrote", args.out)


if __name__ == "__main__":
    main()
