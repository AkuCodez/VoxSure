# VoxSure: an error-aware voice assistant for student support

**Live application:** _not deployed yet: add URL after deployment (see `docs/DEPLOYMENT.md`)_
**Source code:** _add repository link_
**Colab training notebook:** `ml/notebooks/VoxSure_Train_Colab.ipynb`

All numbers below come from reproducible runs in this repository (`ml/reports/*.json`, seed 42). Nothing is estimated by hand.

## 1. Abstract

VoxSure is a browser voice assistant for a bounded Student Support & Campus Information domain. Speech is transcribed
with Whisper (`faster-whisper`, `base.en`), the transcript is shown and can be edited, and a fine-tuned DistilBERT
classifier predicts one of 15 intents plus an explicit out-of-scope class. A recovery policy then decides to **answer**
from a reviewed knowledge base, **ask a targeted clarification**, or **fall back transparently**, instead of always
guessing. On a held-out test set the policy reduced the rate of confidently wrong answers from 20.9% (argmax pipeline) to 2.5%,
at the cost of asking for clarification on 34.2% of turns. The dataset is small and author-written, so absolute numbers
are optimistic relative to real users; see Limitations.

## 2. Problem and related work

Misrecognised words and ambiguous requests cause voice assistants to give confident but irrelevant answers. Relevant
prior work: Whisper for robust ASR (Radford et al., 2022); DistilBERT, a compact distilled transformer (Sanh et al.,
2019); out-of-scope intent detection datasets such as CLINC150 (Larson et al., 2019); and the observation that modern
neural networks are often over-confident, with temperature scaling as a simple calibration method (Guo et al., 2017).
Uncertainty-aware intent clarification already exists in the literature, so the contribution claimed here is narrower: a
**reproducible, measured evaluation of a recovery workflow** (transcript editing, uncertainty/ambiguity handling, targeted
clarification, optional consent-based correction memory) in one defined domain, compared against a no-clarification baseline.

## 3. Dataset

* **Source:** all 288 seed utterances were written by the author for this project (11 campus intents × 16 = 176;
  greeting 18; thanks/goodbye 24; about-the-assistant 14; what-can-you-do 16; out-of-scope 40). No scraped or third-party data; no licence constraints.
  Seeds were expanded programmatically with conversational fillers, lower-casing/punctuation removal (ASR style) and
  plausible ASR substitutions (e.g. "hostel"→"hostile", "wifi"→"why fi"). Script: `ml/scripts/build_dataset.py`.
* **Classes (16):** library_hours, library_borrow, academic_calendar, exam_info, fee_payment, hostel_info, it_helpdesk,
  placement_process, scholarship_aid, certificates, campus_services, greeting, thanks_bye, about_bot, help_capabilities, out_of_scope.
* **Splits (by seed group, so variants of one seed never straddle splits):** train 1386, validation 253, test 253.
  Exact-text overlap between splits: 0. Fixed seed 42.
* **Ambiguous set (evaluation only, never trained on):** 50 hand-written under-specified requests ("When does it open?")
  with the set of plausible intents; 25 for policy tuning (validation), 25 held out for test.
* **Dataset history (disclosed):** the first version had 13 classes. The conversational classes `about_bot` and
  `help_capabilities` were added after manual testing showed "What's your name?" fell into the out-of-scope fallback. A subsequent
  run showed `thanks_bye` with F1 = 0.00 on test (only 12 seeds, 2 held out), so more small-talk seeds were added and the splits
  regenerated. Test metrics from earlier versions are therefore superseded and not reported.
* **Knowledge base:** answers use illustrative values for a fictional campus (not real institutional data).

## 4. Models and method

| Component | Choice |
|---|---|
| ASR | `faster-whisper` `base.en`, int8, CPU, beam 1, VAD filter, domain `initial_prompt` |
| Classifier | `distilbert-base-uncased` fine-tuned, 16 classes, max length 48, AdamW lr 5e-5, batch 16, 6 epochs, linear warm-up/decay, seed 42, best epoch by validation accuracy |
| Confidence | Softmax with temperature scaling, T = 1.40 fitted on validation data only |
| Baseline | TF-IDF (1-2 grams) + Logistic Regression (experimental baseline only) |
| Policy | Thresholds (t_high 0.90, margin 0.50, t_low 0.15, t_oos 0.40) grid-searched on **validation + ambiguous_val only**, then frozen before test evaluation |

Policy objective on validation: reward correct answers/fallbacks and appropriate clarifications (0.6), penalise a wrong
answer 3× and an unnecessary clarification 0.6×. A "wrong answer" is (a) answering with the wrong intent, (b) answering an
out-of-scope request, or (c) answering an ambiguous request at all (it should have been clarified).

## 5. Results

### 5.1 Experiment A: text-only intent classification (test, n = 253)

| Model | Accuracy | Macro-F1 |
|---|---|---|
| TF-IDF + LogReg baseline | 0.577 | 0.550 |
| Fine-tuned DistilBERT | 0.830 | **0.805** |

DistilBERT per-class test F1: about_bot 1.00, academic_calendar 1.00, greeting 1.00, library_borrow 1.00, placement_process 1.00,
thanks_bye 1.00, certificates 0.97, help_capabilities 0.97, out_of_scope 0.87, library_hours 0.78, exam_info 0.72, fee_payment 0.68,
it_helpdesk 0.67, scholarship_aid 0.67, hostel_info 0.55, **campus_services 0.00**. Confusion matrix: `ml/reports/confusion_matrix.png`.

The `campus_services` result reflects a small test set rather than a bug: each class has only 2 held-out seed phrasings, and
for this class they were "Where can I park my bicycle or bike?" (predicted out-of-scope) and "Does the campus have a counselling service?"
(predicted hostel_info), topics unseen in training. Per-class scores on 14-18 examples from 2 distinct seeds are high-variance.
Earlier dataset versions of the same pipeline scored macro-F1 0.83 and 0.75 on differently-split test sets, so **differences of several
points should be treated as noise**. Validation accuracy of the selected epoch was 0.806.

**Calibration.** ECE on test: 0.108 uncalibrated vs 0.061 after temperature scaling (validation: 0.146 vs 0.124). Mean test
confidence 0.851 vs accuracy 0.830. Confidence drives decisions, so thresholds are tuned empirically rather than trusting raw probabilities.

### 5.2 Experiments B vs C: no recovery vs error-aware recovery (test n = 278 = 253 clear + 25 ambiguous)

| Metric | B: argmax, no clarification | C: error-aware |
|---|---|---|
| Wrong-answer rate (all turns) | 20.9% | **2.5%** |
| Clarification rate | 0% | 34.2% |
| Wrong-answer rate, clear requests only | 14.2% | 2.4% |
| Task completion, one turn (clear requests) | 83.0% | 65.6% |
| Task completion if user taps a clarification option | 83.0% | 76.7% |
| Ambiguous requests answered (wrongly) | 22/25 | 1/25 (21 clarified) |

Trade-off: the policy asks an unnecessary clarification on 69 of 253 clear requests (27%), and even counting a tap on an offered
option it completes fewer tasks than the baseline (76.7% vs 83.0%). The benefit is safety: wrong answers fall about eight-fold. Whether
this trade is right depends on the cost of a wrong answer versus an extra question; thresholds should be re-tuned with real users.

### 5.3 Experiment E: noise stress (test text with heavier synthetic corruption: dropped words, character swaps, substitutions)

Text-only accuracy falls from 0.830 to 0.719. Wrong-answer rate: B 28.4% vs C 2.5%; clarification rate C 52.9%;
one-turn completion B 71.9% vs C 44.3% (56.9% with option click). Under heavy corruption the policy is very conservative.

### 5.4 Speech pipeline (Whisper base.en on 64 synthetic test utterances, 2 Windows TTS voices)

| Condition (white-noise SNR) | WER (with domain prompt) | WER (no prompt) | Latency median / p95 (s) |
|---|---|---|---|
| Clean | 1.1% | 1.1% | 0.81 / 0.91 |
| 20 dB | 1.3% | 1.1% | 0.80 / 0.84 |
| 10 dB | 2.4% | 2.4% | 0.46 / 0.86 |
| 5 dB | 5.1% | 3.7% | 0.79 / 0.87 |

On clean audio the full audio-to-answer pipeline gives wrong-answer rate B 42.2% vs C 3.1% (64 items, 39% ambiguous), with
clarification rate 48.4% and one-turn completion on clear requests 84.6% vs 69.2%. The domain prompt gave **no measurable WER
benefit** (slightly worse at 5 dB) on this synthetic set. Latency was measured on the author's laptop CPU (int8).

**Important caveat:** the audio is clean synthetic TTS speech; it says nothing about accents, spontaneous speech or
real microphones, so WER here is a lower bound. Human recordings were not collected.

### 5.5 Experiment D: correction memory (simulation)

Stressed utterances (n = 253); 164 were not answered correctly on first pass and the corrected text was "remembered".
When the same utterances recurred, the correct-answer rate was 35.2% with memory off vs 55.3% with memory on. This is an
**upper bound for exact repeats**: memory matches only the identical normalised utterance and does not generalise. No
real-user study was done.

## 6. System and deployment

React + TypeScript + Tailwind frontend with a live microphone waveform and a "Pipeline insights" panel (ASR confidence, intent
probabilities, policy decision and reason, timings); FastAPI backend; SQLite (default) or PostgreSQL for opt-in correction memory and
metrics-only events; one Docker image serving both on a single HTTPS origin (see `docs/ARCHITECTURE.md`, `docs/DEPLOYMENT.md`).
Audio is never persisted; logged events contain no transcript text. Automated tests: 34 backend (policy, every endpoint, failure
paths, SQL-injection inertness, privacy) and 7 frontend.

## 7. Limitations and future work

* Author-written, templated dataset; test sentences come from the same author and distribution, so real-user accuracy is expected to be lower.
* Small test set (253 clear + 25 ambiguous; 2 distinct seeds per class); no confidence intervals; results varied noticeably across dataset versions.
* `campus_services` generalised poorly to unseen sub-topics (parking, counselling); more diverse real utterances are needed.
* 27% unnecessary clarifications on clear requests and lower one-turn completion than the baseline are a real usability cost.
* ASR evaluated on synthetic speech only. Needs human recordings across accents and noise.
* Knowledge-base content is illustrative; browser speech synthesis availability varies; correction memory is exact-match only.
* The dataset was revised twice after observing test failures (disclosed in §3), a mild form of test-set feedback.
* Free-tier hosting may have cold starts.

## References

* Radford, A. et al. (2022). Robust Speech Recognition via Large-Scale Weak Supervision (Whisper).
* Sanh, V. et al. (2019). DistilBERT, a distilled version of BERT.
* Guo, C. et al. (2017). On Calibration of Modern Neural Networks. ICML.
* Larson, S. et al. (2019). An Evaluation Dataset for Intent Classification and Out-of-Scope Prediction (CLINC150). EMNLP.
* SYSTRAN. faster-whisper (CTranslate2 implementation of Whisper).
