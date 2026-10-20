---
title: VoxSure
emoji: 🎙️
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
---

# VoxSure: error-aware voice assistant

Voice in → Whisper speech recognition → fine-tuned DistilBERT intent classifier → recovery policy
(answer / clarify / fallback) → reviewed answer shown and optionally spoken. Domain: student support & campus
information (**sample data for a fictional campus; not an official service**).

* Report: [`docs/REPORT.md`](docs/REPORT.md) · Architecture: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) ·
  Traceability: [`docs/TRACEABILITY.md`](docs/TRACEABILITY.md) · Deployment: [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md)
* Live app: _add URL after deployment_

## Run locally (Windows / macOS / Linux, Python 3.10+, Node 20+)

```bash
python -m venv .venv && source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install torch==2.5.1 --index-url https://download.pytorch.org/whl/cpu
pip install -r ml/requirements-train.txt
cd frontend && npm install && npm run build && cd ..
cd backend && uvicorn app.main:app --port 8000             # open http://localhost:8000
```

First start downloads the Whisper `base.en` weights (~140 MB). Microphone access works on `localhost` and on HTTPS.
The model needs `ml/artifacts/intent_model/` (included via Git LFS, or regenerate it below).

Frontend development with hot reload: `cd frontend && npm run dev` (proxies `/api` to port 8000).

## Reproduce the model and every number in the report

```bash
python ml/scripts/build_dataset.py                 # dataset + splits (seed 42)
python ml/scripts/train_intent.py                  # fine-tune DistilBERT (~4 min on CPU)
python ml/scripts/evaluate_intent.py               # baseline, calibration, policy tuning, experiments A-E -> ml/reports/
powershell ml/scripts/synthesize_speech.ps1        # Windows only: synthetic test audio
python ml/scripts/evaluate_speech.py base.en       # WER, latency, audio-to-answer pipeline
```

A Colab version of the training step: `ml/notebooks/VoxSure_Train_Colab.ipynb`.

## Tests

```bash
cd backend && python -m pytest          # 34 tests: policy, all endpoints, failure paths, privacy
cd frontend && npm test                 # 7 component tests
```

## Configuration (`.env.example`)

`WHISPER_MODEL`, `WHISPER_COMPUTE_TYPE`, `DATABASE_URL` (SQLite default, PostgreSQL supported), `CORS_ORIGINS`
(only when the frontend is hosted separately), `MAX_AUDIO_BYTES`, `ASR_TIMEOUT_S`. No secrets are committed.

## API

`GET /api/v1/health` · `POST /api/v1/transcribe` (multipart `audio`) · `POST /api/v1/intent` ·
`POST /api/v1/chat/turn` · `POST /api/v1/feedback` · `GET|DELETE /api/v1/memory/{client_id}[/{id}]`.
Interactive docs at `/docs` when running.

## Privacy

Mic only after a button press; audio is processed in memory and never stored; logged events hold no transcript text;
correction memory is opt-in, inspectable and deletable (Settings).

## Known limitations

See report §7: small author-written dataset (optimistic metrics, high variance per class), ASR evaluated on synthetic
speech only, the safety-first policy asks a clarification on roughly a quarter of clear requests (report §5.2),
illustrative knowledge-base content, browser TTS varies by device.

Licence: MIT.
