# VoxSure: Technical Requirements (as built)

## Stack
| Layer | Technology |
|---|---|
| Frontend | React 18, TypeScript, Vite 6, Tailwind 4 (no external fonts or analytics) |
| ASR | faster-whisper, model `small` (multilingual, int8, CPU), word timestamps and probabilities |
| Translation | NLLB-200 distilled 600M, int8, CTranslate2 (any language to and from English) |
| Intent model | Fine-tuned `distilbert-base-uncased`, 16 classes incl. `out_of_scope`, temperature scaling |
| Recovery | `backend/app/core/policy.py` (pure function) + targeted clarification text |
| Backend | FastAPI + Pydantic v2, SQLAlchemy 2 (SQLite default, PostgreSQL via `DATABASE_URL`) |
| Tests | pytest (backend), Vitest + Testing Library (frontend) |

## Request flow
voice: mic → `POST /transcribe` (Whisper auto-detects or uses the chosen language; returns text, confidence, per-word scores) →
`POST /chat/turn` (detect language → translate to English → DistilBERT → policy → English answer → translate reply back) → UI + optional speech.
typed input skips ASR. English requests skip translation.

## API (all under `/api/v1`)
`GET /health` · `POST /transcribe` (multipart `audio`, optional `language`) · `POST /intent` · `POST /chat/turn` ·
`POST /feedback` · `GET|DELETE /memory/{client_id}[/{id}]` · `GET /evaluation` · `GET /metrics/summary`.
Errors use one envelope: `{"error": {"code", "message"}}`.

## Security and reliability
Input limits (audio 5 MB, text 300 chars), allow-listed audio types, ASR timeout, parameterised SQL, per-IP rate limiting
(120/min all, 30/min for `/transcribe` and `/chat/turn`), security headers (CSP on the app shell, nosniff, frame deny, permissions policy),
no secrets in the repo (`.env.example`), graceful degradation (health reports `degraded`; typed English still works if a model fails to load).

## Model and data requirements: status
Dataset documented in `ml/data/README.md`; split before tuning with group-wise leakage control; policy tuned on validation only;
calibration evaluated; TF-IDF + LogReg kept as an experimental baseline only; seeds and configs stored in `ml/artifacts/`.
