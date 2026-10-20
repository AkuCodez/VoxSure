# VoxSure architecture

## Data flow

```
Browser mic ──MediaRecorder──► POST /api/v1/transcribe ──► faster-whisper (base.en, int8, CPU)
                                        │                       │  transcript + ASR confidence
                                        ▼                       ▼
                           editable transcript bubble ◄──────────┘
                                        │ (auto-submitted; user can Edit + Resend)
                                        ▼
                              POST /api/v1/chat/turn
              ┌─────────────────────────┴─────────────────────────┐
              │ correction memory lookup (opt-in, per anonymous id) │
              │ DistilBERT intent classifier + temperature scaling  │
              │ recovery policy  ──►  answer | clarify | fallback   │
              │ reviewed knowledge base (JSON)                      │
              └─────────────────────────┬─────────────────────────┘
                                        ▼
              chat UI (answer / option buttons / edit prompt)  ──► optional browser speechSynthesis
                                        │
                                        ▼
                  metrics-only event row (no text, no audio)  ──► SQLite / PostgreSQL
```

## Components

| Layer | Implementation | Notes |
|---|---|---|
| Frontend | React 18 + TypeScript + Vite + Tailwind 4 (`frontend/`) | Status machine: Ready, Listening, Uploading, Transcribing, Understanding, Needs clarification, Answered, Error. |
| ASR | `faster-whisper`, `base.en`, int8 CPU (`backend/app/services/asr.py`) | One engine. Domain `initial_prompt` biases vocabulary. Confidence = exp(mean segment avg_logprob). |
| Intent model | Fine-tuned `distilbert-base-uncased`, 14 classes incl. `out_of_scope` (`ml/scripts/train_intent.py`) | Temperature scaling fitted on validation data only. |
| Recovery policy | `backend/app/core/policy.py` | Pure function; thresholds in `ml/artifacts/policy.json`, tuned on validation then frozen. |
| Knowledge base | `backend/app/data/knowledge_base.json` | Reviewed, auditable answers. **Sample data for a fictional campus.** |
| API | FastAPI + Pydantic (`backend/app/api/routes.py`) | Uniform error envelope `{"error": {"code", "message"}}`. |
| Persistence | SQLAlchemy 2: SQLite default, PostgreSQL via `DATABASE_URL` | Tables: `correction_memory` (opt-in), `eval_events` (metrics only). |

## Recovery policy

Inputs: calibrated class probabilities `p`, optional ASR confidence, number of failed attempts.

1. Top class is `out_of_scope` with `p ≥ t_oos` → **fallback** (explain supported topics).
2. `p_top < t_low` → **clarify/repair** (show transcript; ask the user to edit or repeat).
3. ASR confidence below `asr_low` and `p_top < asr_override` → **clarify/repair**.
4. `p_top ≥ t_high` and margin over the runner-up `≥ margin` (small talk exempt from the margin) → **answer**.
5. Otherwise, if ≥ 2 plausible in-scope candidates → **clarify/disambiguate** with up to 3 selectable options; else **repair**.
6. After `max_attempts` failed clarifications → **fallback** with "type or reset" guidance (no endless loops).

Selecting an option sends `chosen_intent`, which answers directly (`reason = user_confirmed`).

## Correction memory (FR-08)

Off by default. When enabled in Settings, editing a transcript shows a "Remember this correction" checkbox.
Only if ticked is `{normalised original → corrected text}` stored under an anonymous random client id.
The user can list and delete entries (`GET/DELETE /api/v1/memory/{client_id}`). It only matches exact repeats of the
normalised original, by design: no fuzzy generalisation, so it cannot silently rewrite unrelated requests.

## Privacy

* Microphone is requested only after the user presses the button.
* Audio is processed in memory and never written to disk or to the database.
* `eval_events` holds action, intent, confidence, latency: no transcript text.
* No third-party analytics or fonts.

## Deployment

One Docker image (`Dockerfile`) = built React app + FastAPI + models, served on one HTTPS origin (no CORS).
See `docs/DEPLOYMENT.md`.
