# Requirements traceability and audit

**Status key.** **Tested** = automated test or recorded measurement in this repo. **Manual** = checked by hand only (how is stated).
**Pending** = not done; needs something outside the repo. Nothing is marked done without one of these.

## A. Functional requirements (specification §3.2)
| ID | Requirement | Where | Evidence | Status |
|---|---|---|---|---|
| FR-01 | Voice capture; denial/unsupported guidance | `hooks/useRecorder.ts`, `Composer.tsx` | Recorder start/stop/cancel/timeout/auto-stop exercised in a browser with an injected audio stream; Vitest | Tested (real microphone: **Manual**, owner-confirmed working earlier) |
| FR-02 | Visible transcript | `MessageBubble.tsx` | Vitest | Tested |
| FR-03 | Edit and resubmit transcript | `MessageBubble.tsx`, `useChat.editAndResend` | Vitest, browser run | Tested |
| FR-04 | DL intent + confidence | `services/intent.py`, `/intent` | `test_api.py`; macro-F1 with 95% CI in `ml/reports/intent_eval.json` | Tested |
| FR-05 | Uncertainty recovery | `core/policy.py` | `test_policy.py`, experiments B/C/E | Tested |
| FR-06 | Grounded answers | `knowledge_base.json`, `chat_turn` | `test_api.py` | Tested (illustrative content; **no source links** until a real institution is named) |
| FR-07 | Speech output play/mute/stop | `lib/speech.ts` | Browser TTS; voices vary, non-English voices depend on the device | Manual |
| FR-08 | Opt-in correction memory, listable and deletable | `db/database.py`, `SettingsPanel.tsx` | `test_api.py::test_memory_*` | Tested |
| FR-09 | Conversation UI, reset | `ChatPage.tsx` | Browser | Manual |
| FR-10 | Minimal metrics, no raw audio | `EvalEvent` | `test_turn_logs_metrics_without_text` | Tested |
| FR-11 | Public HTTPS deployment | `Dockerfile`, `docs/DEPLOYMENT.md` | none yet | **Pending** (owner's hosting account; Docker build untested: Docker not installed here) |
| FR-12 | Failure handling | error envelope, UI alert | `test_transcribe_*`, recorder timeout run | Tested |

## B. Final acceptance checklist (specification §14)
| Item | Status |
|---|---|
| Public HTTPS URL works in a fresh browser | **Pending** |
| Microphone permission appropriate; typed fallback | Tested (typed) / Manual (mic) |
| Transcript visible and editable | Tested |
| DL classifier integrated and documented | Tested (`ml/artifacts/README.md`) |
| Assistant answers, clarifies or falls back by policy | Tested |
| Spoken output works or limitations documented | Manual; limitation documented |
| Baseline and error-aware workflow compared on the same held-out set | Tested (`evaluate_intent.py`) |
| Metrics real, reproducible, with limitations | Tested (`docs/REPORT.md`, dashboard) |
| Tests cover API, classification/recovery, failure paths | Tested (backend + frontend suites) |
| README covers setup, env vars, training/evaluation, deployment, limitations | Done |
| No secrets or unapproved recordings committed | Checked (`git ls-files`: no `.env`, `.wav`, `.db`) |
| Final report, live link, source, model/data docs, demo | Report, docs and demo script done; **live link and hosted source repo pending** |

## C. Enhancement brief (Hinglish-free multilingual + production polish)
| Requirement | Status | Note |
|---|---|---|
| Whisper (faster-whisper) STT | Tested | model `small`, multilingual, word confidences |
| Fine-tuned DistilBERT intent model | Tested | macro-F1 and CI in report |
| FastAPI + React/TS/Tailwind | Tested | |
| Confidence-aware error recovery | Tested | |
| Highlight the doubtful part of the transcript | Tested (Vitest) | uses Whisper per-word probabilities; real-microphone behaviour **Manual** |
| Edit transcript and ask a specific clarification | Tested | question names the competing intents |
| Source-backed answers with last-updated | Tested for source label and date; **links Pending** | no link invented; a real institution is needed |
| Graceful unsupported-question handling | Tested | |
| Typed fallback; spoken responses | Tested / Manual | |
| Answer questions outside campus topics (open domain) | Tested with stand-in clients and a mock server for both providers; **live provider call not yet exercised (needs the owner's key)** | answers labelled AI-generated, opt-out in Settings, daily cap |
| Reply in the user's language (hi, pa, de verified; others best effort) | Tested for typed text (47 sentences per language) | speech WER for non-English **not measured** (no recordings) |
| Evaluation dashboard with real results | Tested (API + Vitest + axe) | `#/evaluation` |
| Comparison with TF-IDF + LogReg on the same test data | Tested | with bootstrap CIs |
| Optional consent-based correction memory, no raw audio retained | Tested | |
| Accessible controls, loading and error states | Tested with axe (jsdom); colour contrast and screen-reader use **not** audited | |
| Secure API configuration; rate limits; headers | Tested | |
| Reliable public HTTPS deployment | **Pending** | |

## D. Owner's other instructions
| Instruction | Status |
|---|---|
| Frontend looks polished, full screen | Done (owner confirmed "pretty and good") |
| Remove the demo banner | Done |
| Logical answers to ordinary questions | Done (`about_bot`, `help_capabilities`, friendlier fallback) |
| Recording must be stoppable and typing must work | Fixed and tested |
| Answer in whatever language the user speaks | Done for hi/pa/de (measured), best effort for others |
| Do not fabricate datasets, results, citations, completed features | Followed; see report limitations and the dataset-revision disclosure |
| Get human approval before deploying | Followed: nothing deployed |
