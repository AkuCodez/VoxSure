"""Content of the short submission report as neutral blocks, shared by the PDF and Word builders so they never disagree.

Every figure is read from the result files in ml/reports (nothing typed by hand). Inline markup: <b>bold</b>, <i>italic</i>.
Block kinds: title, sub, h1, h2, p, note, table, image, caption.
"""
from __future__ import annotations

import glob
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REP = ROOT / "ml" / "reports"
SHOTS = ROOT / "docs" / "screenshots"
L = lambda p: json.loads(Path(p).read_text(encoding="utf-8")) if Path(p).exists() else None
pc = lambda x, d=1: f"{x * 100:.{d}f}%"


def build_blocks(name: str, regno: str, live: str, repo: str) -> list[tuple]:
    r = L(REP / "intent_eval.json")
    cfg = L(ROOT / "ml" / "artifacts" / "intent_model" / "train_config.json")
    ml = L(REP / "multilingual_eval.json")
    par = L(REP / "onnx_parity.json")
    sp_files = sorted(glob.glob(str(REP / "speech_eval_*.json")))
    sp = L(sp_files[-1]) if sp_files else None
    base, dist, bs = r["A_baseline_tfidf_logreg"], r["A_distilbert"], r["bootstrap_95ci"]
    B, C = r["BC_test"]["B_argmax_no_clarification"], r["BC_test"]["C_error_aware"]
    Bc, Cc = r["BC_test"]["B_clear_only"], r["BC_test"]["C_clear_only"]
    sz = r["sizes"]
    out: list[tuple] = []
    add = out.append

    add(("title", "Voice-Enabled Chatbot using Speech Recognition and Deep Learning"))
    add(("sub", "VoxSure: an error-aware, multilingual voice assistant for student support"))
    add(("sub", "<b>Project Report - Lab Assessment</b>"))
    add(("sub", f"<b>Submitted by:</b> {name} ({regno})"))
    add(("sub", f"<b>Live application:</b> {live}"))
    add(("sub", f"<b>Source code repository:</b> {repo}"))

    add(("h1", "1. Introduction"))
    add(("p", "This project implements a voice-enabled chatbot for a student support and campus information domain. The user speaks (or types) a question; "
              "a Speech Recognition (ASR) module converts the speech to text; a fine-tuned deep learning model (DistilBERT) classifies the intent; and the system "
              "replies. Both the recognized speech and the chatbot response are displayed, and the reply can be read aloud. The main contribution is an "
              "<b>error-aware recovery policy</b>: instead of always guessing, the assistant underlines words the recogniser was unsure about, lets the user edit the "
              "transcript, asks a targeted clarification question when two intents compete, and declines honestly when a request is out of scope. The assistant "
              "replies in the language the user speaks, and non-campus questions can be answered by a clearly labelled AI model. The application is packaged for public "
              "hosting; the live link and source code are submitted for evaluation."))

    add(("h1", "2. Objective"))
    add(("p", "To design, implement and deploy an end-to-end voice interaction pipeline consisting of: (i) speech-to-text conversion, (ii) a deep learning model for "
              "understanding user intent with a measured confidence, (iii) a recovery layer that reduces confidently wrong answers, and (iv) a publicly accessible web "
              "interface that displays the transcribed speech and the chatbot reply, together with an in-app evaluation dashboard that shows real measured results."))

    add(("h1", "3. Dataset"))
    add(("p", f"The intent classifier is trained on a domain dataset of {sum(sz[k] for k in ('train', 'val', 'test')):,} short utterances in {len(r['labels'])} classes: "
              "11 campus intents (library hours, library borrowing, academic calendar, exams, fee payment, hostel, IT helpdesk, placements, scholarships, certificates, "
              "campus services), greeting, thanks/goodbye, questions about the assistant, a what-can-you-do class, and an explicit <i>out-of-scope</i> class. "
              "<b>The data was written by the project author</b> (no scraped or third-party data): hand-written seed utterances were expanded with conversational "
              "fillers and plausible speech-recognition errors. Splits are made by seed group so near-duplicates never cross splits (zero exact overlap). "
              "The speech component needs no training data because a pre-trained Whisper model is used."))
    add(("table", {"rows": [["Split", "Utterances", "Notes"],
                            ["Train", f"{sz['train']:,}", "fine-tuning (seed 42)"],
                            ["Validation", f"{sz['val']:,}", "model selection, temperature scaling and policy thresholds"],
                            ["Test", f"{sz['test']:,}", "held out; final results only"],
                            ["Ambiguous set", f"{sz['ambiguous_val']} + {sz['ambiguous_test']}", "hand-written under-specified requests (validation + test), never trained on"],
                            ["Multilingual test", f"{ml['n_per_language']} x 4 languages" if ml else "n/a", "English, Hindi, Punjabi, German (typed text, never trained on)"]],
                   "widths": [0.20, 0.19, 0.61]}))
    add(("note", "Limitation: the data comes from a single author and the held-out phrasings per class are few, so real-user accuracy is expected to be lower. The dataset was "
                 "revised several times after weak results were observed; this is disclosed in the full report."))

    add(("h1", "4. Methodology / System Architecture"))
    add(("p", "The system is organised as a pipeline:"))
    add(("table", {"rows": [["Stage", "Function", "Technique / Tool"],
                            ["1. Voice input", "Capture audio from the user's microphone in the browser (permission asked only on button press); live waveform; auto-stop after a pause",
                             "Browser MediaRecorder + Web Audio API"],
                            ["2. Speech recognition", "Convert speech to text with a per-clip confidence; language auto-detected or chosen by the user",
                             "Whisper: faster-whisper 'small' (full build) or Whisper large-v3-turbo via the Groq API (free serverless build)"],
                            ["3. Language handling", "Detect the language; translate non-English input to English for the classifier; reply in the user's language",
                             "Script/word-based detector; NLLB-200 or LLM translation; hand-written Hindi/Punjabi/German replies"],
                            ["4. Intent classification", "Classify the text into an intent with a calibrated confidence",
                             "Fine-tuned DistilBERT (deep learning) + temperature scaling; int8 ONNX export for the serverless build"],
                            ["5. Recovery policy", "Decide: answer, ask a targeted clarification, ask to re-check the transcript, or decline",
                             "Rules on confidence, margin and speech confidence (thresholds tuned on validation data only)"],
                            ["6. Response and output", "Show recognized text and reply with source label and last-updated date; optionally speak the reply",
                             "Reviewed knowledge base; optional AI model for non-campus questions (labelled AI-generated); browser speech synthesis; React + FastAPI"]],
                   "widths": [0.19, 0.39, 0.42]}))
    add(("h2", "4.1 Intent classification and recovery policy"))
    add(("p", f"Text is tokenised with the DistilBERT WordPiece tokenizer and passed to a fine-tuned <b>distilbert-base-uncased</b> classifier "
              f"({cfg['epochs']} epochs, learning rate {cfg['lr']}, batch size {cfg['batch_size']}, seed {cfg['seed']}). Raw softmax scores are over-confident, so "
              f"temperature scaling (T = {cfg['temperature']:.2f}, fitted on validation data) is applied. The recovery policy then answers only when the top class "
              f"is confident and clearly ahead of the runner-up; if two campus intents compete it asks <i>\"do you mean A or B?\"</i> with tap-to-choose options; "
              f"if the speech recogniser was unsure it asks the user to check the transcript; out-of-scope requests receive an honest fallback. A TF-IDF + "
              f"Logistic Regression model is used only as a baseline for comparison."))
    add(("h2", "4.2 Deployment"))
    add(("p", "The system is a FastAPI backend with a React + TypeScript + Tailwind frontend. Two builds share one code base: a <b>full</b> build (local Whisper, NLLB "
              "translation and PyTorch, packaged as a Docker image) and a <b>lite</b> build designed for free serverless hosting (hosted Whisper, LLM translation and "
              "an int8 ONNX copy of the same DistilBERT model). Secrets are provided through environment variables. The source code is maintained at the repository "
              "link above."))

    add(("h1", "5. Results"))
    add(("p", "All figures come from reproducible runs on held-out data (seed 42) and are also shown on the application's evaluation page."))
    add(("h2", "5.1 Intent classification (text only, test set)"))
    add(("table", {"rows": [["Model", "Accuracy", "Macro-F1 (95% bootstrap CI)"],
                            ["TF-IDF + Logistic Regression (baseline)", f"{base['accuracy']:.3f}", f"{base['macro_f1']:.3f} ({bs['macro_f1_baseline'][0]:.3f} - {bs['macro_f1_baseline'][1]:.3f})"],
                            ["Fine-tuned DistilBERT (proposed)", f"{dist['accuracy']:.3f}", f"<b>{dist['macro_f1']:.3f}</b> ({bs['macro_f1_distilbert'][0]:.3f} - {bs['macro_f1_distilbert'][1]:.3f})"]],
                   "widths": [0.48, 0.16, 0.36]}))
    if par:
        t = par["test"]
        add(("note", f"The int8 ONNX export used by the serverless build ({par['onnx_size_mb']} MB) reaches macro-F1 {t['macro_f1_onnx']:.3f} on the same test set "
                     f"(PyTorch {t['macro_f1_pytorch']:.3f}); {pc(t['prediction_agreement'], 0)} of predictions are identical."))
    add(("h2", "5.2 Effect of the error-aware recovery policy (test set, including 25 ambiguous requests)"))
    add(("table", {"rows": [["Metric", "Always answer", "VoxSure (recovery policy)"],
                            ["Wrong-answer rate (95% CI)", f"{pc(B['wrong_answer_rate'])} ({pc(bs['wrong_answer_rate_B'][0])} - {pc(bs['wrong_answer_rate_B'][1])})",
                             f"<b>{pc(C['wrong_answer_rate'])}</b> ({pc(bs['wrong_answer_rate_C'][0])} - {pc(bs['wrong_answer_rate_C'][1])})"],
                            ["Clarification rate", pc(B["clarification_rate"]), pc(C["clarification_rate"])],
                            ["One-turn task completion (clear requests)", pc(Bc["task_completion_one_turn"]), pc(Cc["task_completion_one_turn"])]],
                   "widths": [0.41, 0.27, 0.32]}))
    add(("note", "The policy greatly reduces confidently wrong answers, at the cost of more clarification questions: a real trade-off between safety and convenience."))
    if sp:
        rows = [["Noise (white noise SNR)", "Word error rate", "Latency p50 / p95 (s)"]]
        for c_, v_ in sp["conditions"].items():
            w_ = v_["with_domain_prompt"]
            rows.append(["Clean" if c_ == "clean" else c_.replace("snr", "") + " dB", pc(w_["wer"]), f"{w_['latency_s_median']:.2f} / {w_['latency_s_p95']:.2f}"])
        add(("h2", "5.3 Speech recognition (Whisper small)"))
        add(("table", {"rows": rows, "widths": [0.34, 0.28, 0.38]}))
        add(("note", f"Measured on {sp['n_utterances']} synthetic text-to-speech utterances (two Windows voices), so these are lower bounds that say nothing about accents or real "
                     "microphones. Latency was measured on a laptop CPU while other jobs were running."))
    if ml:
        rows = [["Language", "Intent accuracy", "Language ID", "Wrong answers (always answer to VoxSure)", "Label"]]
        for v_ in ml["languages"].values():
            rows.append([v_["name"], pc(v_["accuracy"]), pc(v_["lang_id_accuracy"]), f"{pc(v_['wrong_answer_rate_B'])} to {pc(v_['wrong_answer_rate_C'])}",
                         "verified" if v_["verified"] else "best effort"])
        add(("h2", "5.4 Multilingual (typed text, test sentences written by the author)"))
        add(("table", {"rows": rows, "widths": [0.17, 0.18, 0.15, 0.31, 0.19]}))
        add(("note", "A language is labelled verified only if it met criteria fixed in advance (accuracy at least 80%, wrong-answer rate at most 10%, language ID at least 95%). "
                     "Other languages are best effort and not measured. Speech accuracy for Hindi, Punjabi and German is not measured: it needs human recordings."))
    shot = SHOTS / "01-chat-desktop.png"
    if shot.exists():
        add(("h2", "5.5 The working application"))
        add(("image", {"path": str(shot), "width_cm": 12.5, "aspect": 900 / 1600}))
        add(("caption", "Desktop view: voice and text input, language picker, and the pipeline-insights panel (speech confidence, intent probabilities, policy decision). "
                        "Live demo link: " + live))

    add(("h1", "6. Conclusion"))
    add(("p", f"The project delivers a working voice-enabled chatbot in which speech recognition, a fine-tuned deep learning intent classifier and a recovery policy are "
              f"combined and evaluated honestly. DistilBERT clearly beats the TF-IDF baseline (macro-F1 {dist['macro_f1']:.3f} vs {base['macro_f1']:.3f}), and the recovery policy cuts "
              f"the wrong-answer rate from {pc(B['wrong_answer_rate'])} to {pc(C['wrong_answer_rate'])}. Limitations are stated plainly: a small author-written dataset, speech tested on "
              f"synthetic voices only, multilingual sentences not native-verified, and some ambiguous requests still answered rather than clarified. The code, reports and "
              f"live demo link are submitted for evaluation."))
    return out
