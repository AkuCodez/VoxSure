# VoxSure: Product Requirements (as built)

Source of truth: `VoxSure_Project_Specification.docx`. This file records what was built, what changed from the spec, and what is not done.
Status labels: **Tested** (automated test or recorded measurement) · **Manual** (checked by hand only) · **Planned** (not built).

## 1. Problem and goal
Voice assistants answer confidently when speech recognition mishears or a request is ambiguous. VoxSure inserts a
confidence-aware recovery layer: it highlights doubtful words, lets the user edit the transcript, asks a targeted
clarification, or declines honestly, instead of guessing. Domain: student support and campus information.

## 2. Users and journeys
Students speak or type a question, check the transcript, and receive a source-labelled answer, a clarification, or a fallback,
optionally spoken aloud, in the language they used.

## 3. Functional requirements and status
| ID | Requirement | Status |
|---|---|---|
| FR-01 Voice capture with clear denial guidance | Tested (recorder logic via injected stream; real mics: Manual) |
| FR-02 Visible transcript | Tested |
| FR-03 Edit and resubmit transcript; doubtful words highlighted | Tested (UI) |
| FR-04 DL intent + confidence | Tested |
| FR-05 Uncertainty recovery (answer / clarify / fallback) | Tested |
| FR-06 Grounded answers with source and last-updated label | Tested (links: **Planned**, none invented) |
| FR-07 Speech output | Manual (browser voices vary; non-English voices depend on the device) |
| FR-08 Opt-in correction memory | Tested |
| FR-09 Conversation UI, reset | Manual |
| FR-10 Minimal metrics, no raw audio | Tested |
| FR-11 Public HTTPS deployment | **Planned** (needs the owner's hosting account) |
| FR-12 Failure handling | Tested |
| NEW Multilingual (Hindi, Punjabi, German + best-effort others) | Tested for typed text; speech WER **not measured** |
| NEW In-app evaluation dashboard | Tested (API) / Manual (UI) |

## 4. Changes from the specification (all deliberate)
* Hosting: single Docker image on Hugging Face Spaces instead of Vercel + separate backend (Whisper + DistilBERT need more RAM than typical free tiers).
* ASR model `small` (multilingual) instead of an English-only model; English-only `base.en` remains selectable.
* Added two conversational intents (`about_bot`, `help_capabilities`) after testing showed ordinary questions hit the out-of-scope fallback.
* Added multilingual support via NLLB-200 translation (licence CC-BY-NC; fine for academic use).
* **Open-domain answers added at the owner's request** (the spec listed this as a non-goal): non-campus questions can be answered by an external general AI model, labelled AI-generated, opt-out per user, daily-capped, off unless a key is configured. Campus answers remain grounded in the reviewed knowledge base.

## 5. Non-goals
Training ASR from scratch, ASR ensembles, biometrics, raw-audio retention by default.
