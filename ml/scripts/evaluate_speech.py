"""Speech-pipeline evaluation on synthetic test audio (see synthesize_speech.ps1).

Measures, per noise condition (clean / SNR 20 dB / SNR 10 dB / SNR 5 dB white noise):
  * Word Error Rate against the known reference sentence (Whisper with/without domain prompt)
  * ASR latency (median, p95) on THIS machine's CPU
  * End-to-end behaviour: audio -> Whisper -> DistilBERT -> policy, Experiment B (argmax,
    no clarification) vs C (error-aware), using the policy frozen in artifacts/policy.json.

Caveat (also in the report): audio is synthetic TTS speech from two voices, with synthetic
noise. It says nothing about accents or real microphones.
"""
from __future__ import annotations

import json
import re
import statistics
import sys
import time
from pathlib import Path

import numpy as np
from scipy.io import wavfile
from scipy.signal import resample_poly

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / "backend"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import jiwer  # noqa: E402
from app.core.policy import PolicyParams  # noqa: E402
from app.services.asr import DOMAIN_PROMPT  # noqa: E402
from app.services.intent import IntentClassifier  # noqa: E402
from evaluate_intent import baseline_decision, score  # noqa: E402
from app.core.policy import decide  # noqa: E402
from faster_whisper import WhisperModel  # noqa: E402

AUDIO = ROOT / "eval_audio"
MODEL = sys.argv[1] if len(sys.argv) > 1 else "base.en"
SEED = 42


def load(path: Path) -> np.ndarray:
    sr, x = wavfile.read(path)
    x = x.astype(np.float32) / 32768.0
    if x.ndim > 1:
        x = x.mean(1)
    if sr != 16000:
        x = resample_poly(x, 16000, sr)
    return x.astype(np.float32)


def add_noise(x: np.ndarray, snr_db: float, rng: np.random.Generator) -> np.ndarray:
    p = np.mean(x ** 2) + 1e-12
    n = rng.normal(0, np.sqrt(p / (10 ** (snr_db / 10))), x.shape).astype(np.float32)
    return np.clip(x + n, -1, 1)


def norm(t: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9' ]", " ", t.lower())).strip()


def pad(x):  # a little leading/trailing silence, like a real push-to-talk recording
    z = np.zeros(8000, np.float32)
    return np.concatenate([z, x, z])


def main() -> None:
    manifest = json.loads((AUDIO / "manifest.json").read_text(encoding="utf-8-sig"))
    if isinstance(manifest, dict):
        manifest = [manifest]
    clf = IntentClassifier(ROOT / "artifacts" / "intent_model")
    policy = PolicyParams.load(ROOT / "artifacts" / "policy.json")
    asr = WhisperModel(MODEL, device="cpu", compute_type="int8")
    clean = {m["file"]: load(AUDIO / m["file"]) for m in manifest}
    rng = np.random.default_rng(SEED)

    detected = []

    def transcribe(x, prompt, language="en"):
        t0 = time.perf_counter()
        segs, info = asr.transcribe(pad(x), beam_size=1, language=language, vad_filter=True,
                                    initial_prompt=prompt, condition_on_previous_text=False)
        detected.append(info.language)
        segs = list(segs)
        dt = time.perf_counter() - t0
        text = " ".join(s.text.strip() for s in segs).strip()
        if segs:
            tot = sum(max(s.end - s.start, 1e-3) for s in segs)
            conf = float(np.exp(sum(s.avg_logprob * max(s.end - s.start, 1e-3) for s in segs) / tot))
        else:
            conf = 0.0
        return text, conf, dt

    report = {"asr_model": MODEL, "n_utterances": len(manifest),
              "voices": sorted({m["voice"] for m in manifest}), "conditions": {}}
    for cond, snr in (("clean", None), ("snr20", 20), ("snr10", 10), ("snr5", 5)):
        noisy = {m["file"]: (clean[m["file"]] if snr is None else add_noise(clean[m["file"]], snr, rng)) for m in manifest}
        res = {}
        arms = (("with_domain_prompt", DOMAIN_PROMPT), ("no_prompt", None)) if cond == "clean" else (("with_domain_prompt", DOMAIN_PROMPT),)
        for pname, prompt in arms:
            hyps, confs, lats = [], [], []
            for m in manifest:
                h, c, dt = transcribe(noisy[m["file"]], prompt)
                hyps.append(h); confs.append(c); lats.append(dt)
            refs = [norm(m["text"]) for m in manifest]
            wer = jiwer.wer(refs, [norm(h) or "<empty>" for h in hyps])
            res[pname] = {"wer": float(wer), "latency_s_median": statistics.median(lats),
                          "latency_s_p95": float(np.percentile(lats, 95)),
                          "exact_match_rate": float(np.mean([norm(h) == r for h, r in zip(hyps, refs)]))}
            if pname == "with_domain_prompt":
                rows, probs_b, probs_c = [], [], []
                for m, h, c in zip(manifest, hyps, confs):
                    p = clf.predict(norm(h) or "...")
                    row = {"kind": m["kind"], "text": h}
                    row.update({"gold": m["gold"]} if m["kind"] == "clear" else {"plausible": m["plausible"]})
                    rows.append(row)
                    probs_b.append(baseline_decision(p))
                    probs_c.append(decide(p, policy, asr_conf=c))
                res[pname]["pipeline_B_argmax"] = score(rows, probs_b)
                res[pname]["pipeline_C_error_aware"] = score(rows, probs_c)
                res[pname]["examples"] = [{"ref": m["text"], "hyp": h, "asr_conf": round(c, 3)}
                                          for m, h, c in list(zip(manifest, hyps, confs))[:6]]
        if cond == "clean":  # what the app does by default: auto-detect the language, no English prompt
            detected.clear()
            hyps_auto = [transcribe(noisy[m["file"]], None, None)[0] for m in manifest]
            refs = [norm(m["text"]) for m in manifest]
            res["auto_detect"] = {"wer": float(jiwer.wer(refs, [norm(h) or "<empty>" for h in hyps_auto])),
                                  "detected_english_rate": float(np.mean([d == "en" for d in detected])),
                                  "note": "language=None (auto-detect), as used by the app; audio is English"}
        report["conditions"][cond] = res
        w = res["with_domain_prompt"]
        if "auto_detect" in res:
            print(f"auto-detect: WER={res['auto_detect']['wer']:.3f} detected_en={res['auto_detect']['detected_english_rate']:.3f}", flush=True)
        print(f"{cond:6s} WER prompt={w['wer']:.3f} noprompt={res.get('no_prompt', {}).get('wer', float('nan')):.3f} "
              f"lat med={w['latency_s_median']:.2f}s p95={w['latency_s_p95']:.2f}s | "
              f"B wrong={w['pipeline_B_argmax']['wrong_answer_rate']:.3f} "
              f"C wrong={w['pipeline_C_error_aware']['wrong_answer_rate']:.3f} C clarify={w['pipeline_C_error_aware']['clarification_rate']:.3f}")
    (ROOT / "reports" / f"speech_eval_{MODEL}.json").write_text(json.dumps(report, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
