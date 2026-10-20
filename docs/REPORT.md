# VoxSure: an error-aware voice assistant for student support

**Live application:** _not deployed yet: add URL after deployment (see `docs/DEPLOYMENT.md`)_
**Source code:** _add repository link_
**Colab training notebook:** `ml/notebooks/VoxSure_Train_Colab.ipynb`

All numbers below come from reproducible runs in this repository (`ml/reports/*.json`, seed 42). Nothing is estimated by hand.

## 1. Abstract

VoxSure is a browser voice assistant for a bounded Student Support & Campus Information domain. Speech is transcribed
with Whisper (`faster-whisper`, `base.en`), the transcript is shown and can be edited, and a fine-tuned DistilBERT
classifier predicts one of 13 intents plus an explicit out-of-scope class. A recovery policy then decides to **answer**
from a reviewed knowledge base, **ask a targeted clarification**, or **fall back transparently**, instead of always
guessing. On a held-out test set, the policy reduced the rate of confidently wrong answers from 26.8% (argmax pipeline) to 6.4%,
at the cost of asking for clarification on 30.2% of turns. The dataset is small and author-written, so absolute numbers
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

* **Source:** all 240 seed utterances (11 domain intents × 16 = 176, greeting/thanks 2 × 12 = 24, out-of-scope 40) were written by the author for
  this project. No scraped or third-party data; no licence constraints. Seeds were expanded programmatically with
  conversational fillers, lower-casing/punctuation removal (ASR style) and plausible ASR substitutions
  (e.g. "hostel"→"hostile", "wifi"→"why fi"). Script: `ml/scripts/build_dataset.py`.
* **Classes (14):** library_hours, library_borrow, academic_calendar, exam_info, fee_payment, hostel_info, it_helpdesk,
  placement_process, scholarship_aid, certificates, campus_services, greeting, thanks_bye, out_of_scope.
* **Splits (by seed group, so variants of one seed never straddle splits):** train 1172, validation 210, test 210.
  Exact-text overlap between splits: 0. Fixed seed 42.
* **Ambiguous set (evaluation only, never trained on):** 50 hand-written under-specified requests ("When does it open?")
  with the set of plausible intents; 25 used for policy tuning (validation), 25 held out for test.
* **Knowledge base:** sample answers for a fictional campus. Not real institutional data.

## 4. Models and method

| Component | Choice |
|---|---|
| ASR | `faster-whisper` `base.en`, int8, CPU, beam 1, VAD filter, domain `initial_prompt` |
| Classifier | `distilbert-base-uncased` fine-tuned, 14 classes, max length 48, AdamW lr 5e-5, batch 16, 6 epochs, linear warm-up/decay, seed 42, best epoch by validation accuracy |
| Confidence | Softmax with temperature scaling, T = 1.214 fitted on validation data only |
| Baseline | TF-IDF (1-2 grams) + Logistic Regression (experimental baseline only) |
| Policy | Thresholds (t_high 0.80, margin 0.50, t_low 0.15, t_oos 0.40) grid-searched on **validation + ambiguous_val only**, then frozen before test evaluation |

Policy objective on validation: reward correct answers/fallbacks and appropriate clarifications, penalise a wrong
answer 3× and an unnecessary clarification 0.3×. A "wrong answer" is (a) answering with the wrong intent, (b) answering an
out-of-scope request, or (c) answering an ambiguous request at all (it should have been clarified).

## 5. Results

### 5.1 Experiment A: text-only intent classification (test, n = 210)

| Model | Accuracy | Macro-F1 |
|---|---|---|
| TF-IDF + LogReg baseline | 0.610 | 0.583 |
| Fine-tuned DistilBERT | 0.819 | **0.832** |

DistilBERT per-class F1: hostel_info 1.00, library_borrow 1.00, library_hours 1.00, placement_process 0.97,
greeting 0.95, thanks_bye 0.95, certificates 0.88, exam_info 0.82, out_of_scope 0.78, academic_calendar 0.73,
it_helpdesk 0.70, campus_services 0.67, fee_payment 0.62, scholarship_aid 0.60. Confusion matrix:
`ml/reports/confusion_matrix.png`. Weakest classes (fee_payment, scholarship_aid, campus_services) overlap in vocabulary
(deadlines, forms, payments).
Validation accuracy of the selected epoch was 0.890 versus 0.819 on test: the group-wise split makes test
phrasings genuinely unseen, so the gap is expected.

**Calibration.** ECE on test: 0.076 uncalibrated vs 0.078 after temperature scaling (validation: 0.080 vs 0.080). Temperature scaling
**did not measurably improve** calibration here; mean test confidence 0.839 vs accuracy 0.819 shows mild over-confidence only.
Confidence still drives decisions, so the policy thresholds are tuned empirically rather than trusting raw probabilities.

### 5.2 Experiments B vs C: speech-to-intent without vs with recovery (text transcripts, test n = 235 = 210 clear + 25 ambiguous)

| Metric | B: argmax, no clarification | C: error-aware |
|---|---|---|
| Wrong-answer rate (all turns) | 26.8% | **6.4%** |
| Clarification rate | 0% | 30.2% |
| Wrong-answer rate, clear requests only | 18.1% | 1.9% |
| Task completion, one turn (clear requests) | 81.9% | 71.0% |
| Task completion if user taps a clarification option | 81.9% | 87.1% |
| Ambiguous requests answered (wrongly) | 25/25 | 11/25 (14 clarified) |

Trade-off: the policy asks an unnecessary clarification on 47 of 210 clear requests (22%). When the user then
chooses an offered option, completion exceeds the baseline (87.1% vs 81.9%). **Limitation:** 44% of ambiguous prompts are still
answered; the classifier is sometimes confidently wrong on under-specified input.

### 5.3 Experiment E: noise stress (test text with heavier synthetic corruption: dropped words, character swaps, substitutions)

Text-only accuracy falls from 0.819 to 0.714. Wrong-answer rate: B 34.0% vs C 10.2%; clarification rate C 34.9%;
one-turn completion B 71.4% vs C 59.0% (73.3% with option click).

### 5.4 Speech pipeline (Whisper base.en on 57 synthetic test utterances, 2 Windows TTS voices)

| Condition (white-noise SNR) | WER (with domain prompt) | WER (no prompt) | Latency median / p95 (s) |
|---|---|---|---|
| Clean | 0.0% | 0.0% | 0.93 / 1.00 |
| 20 dB | 0.6% | 0.0% | 0.92 / 0.97 |
| 10 dB | 0.6% | 0.6% | 0.80 / 1.01 |
| 5 dB | 2.5% | 2.1% | 0.84 / 0.95 |

On clean audio the full audio-to-answer pipeline gives wrong-answer rate B 54.4% vs C 24.6% (57 items, 44% ambiguous),
clarification rate 33.3%. The domain prompt gave **no measurable WER benefit** on this synthetic set.
Latency measured on the author's laptop CPU (Intel, int8); API-level transcription of a 2.7 s clip took ≈1.3 s including decoding.

**Important caveat:** the audio is clean synthetic TTS speech; it says nothing about accents, spontaneous speech or
real microphones, so WER here is a lower bound. Human recordings were not collected.

### 5.5 Experiment D: correction memory (simulation)

Stressed utterances (n = 210); 106 were not answered correctly on first pass and the corrected text was "remembered".
When the same utterances recurred, the correct-answer rate was 49.5% with memory off vs 64.8% with memory on. This is an
**upper bound for exact repeats**: memory matches only the identical normalised utterance and does not generalise. No
real-user study was done.

## 6. System and deployment

React + TypeScript + Tailwind frontend; FastAPI backend; SQLite (default) or PostgreSQL for opt-in correction memory and
metrics-only events; one Docker image serving both on a single HTTPS origin (see `docs/ARCHITECTURE.md`,
`docs/DEPLOYMENT.md`). Audio is never persisted; logged events contain no transcript text.
Automated tests: 33 backend (policy, every endpoint, failure paths, SQL-injection inertness, privacy) and 7 frontend.

## 7. Limitations and future work

* Author-written, templated dataset; test sentences come from the same author and distribution, so real-user accuracy is expected to be lower.
* Test set is small (210 clear + 25 ambiguous); differences of a few points are within noise; no confidence intervals were computed.
* Ambiguous handling is incomplete (11/25 still answered); temperature scaling did not help calibration. Candidates: ensemble/MC-dropout uncertainty, training an explicit "ambiguous" class from real data.
* 22% unnecessary clarifications on clear requests is a usability cost; thresholds should be re-tuned with real users.
* ASR evaluated on synthetic speech only. Needs human recordings across accents and noise.
* Knowledge-base content is sample data; browser speech synthesis availability varies; correction memory is exact-match only.
* Free-tier hosting may have cold starts.

## References

* Radford, A. et al. (2022). Robust Speech Recognition via Large-Scale Weak Supervision (Whisper).
* Sanh, V. et al. (2019). DistilBERT, a distilled version of BERT.
* Guo, C. et al. (2017). On Calibration of Modern Neural Networks. ICML.
* Larson, S. et al. (2019). An Evaluation Dataset for Intent Classification and Out-of-Scope Prediction (CLINC150). EMNLP.
* SYSTRAN. faster-whisper (CTranslate2 implementation of Whisper).
