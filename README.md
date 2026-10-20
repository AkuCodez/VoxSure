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

Voice in → Whisper speech recognition → (translation to English if needed) → fine-tuned DistilBERT intent classifier →
recovery policy (answer / clarify / fallback) → reviewed answer in your language, shown and optionally spoken.
Domain: student support & campus information. The knowledge base uses illustrative values for a fictional campus and is not an official service.
In-app evaluation dashboard: `#/evaluation`.

* Report: [`docs/REPORT.md`](docs/REPORT.md) · Architecture: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) ·
  Traceability: [`docs/TRACEABILITY.md`](docs/TRACEABILITY.md) · Deployment: [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md)
* Live app: _add URL after deployment_
* Source code: https://github.com/AkuCodez/VoxSure

## Run locally (Windows / macOS / Linux, Python 3.10+, Node 20+)

```bash
python -m venv .venv && source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install torch==2.5.1 --index-url https://download.pytorch.org/whl/cpu
pip install -r ml/requirements-train.txt
cd frontend && npm install && npm run build && cd ..
cd backend && uvicorn app.main:app --port 8000             # open http://localhost:8000
```

First start downloads the Whisper `small` weights (~460 MB). For other languages, prepare the translation model once (downloads 2.4 GB, converts to ~600 MB; needs about 6 GB free disk): `python ml/scripts/prepare_nllb.py`. Without it the app still works in English and falls back to English replies. Microphone access works on `localhost` and on HTTPS.
The model needs `ml/artifacts/intent_model/` (included via Git LFS, or regenerate it below).

Frontend development with hot reload: `cd frontend && npm run dev` (proxies `/api` to port 8000).

## Reproduce the model and every number in the report

```bash
python ml/scripts/build_dataset.py                 # dataset + splits (seed 42)
python ml/scripts/train_intent.py                  # fine-tune DistilBERT (~4 min on CPU)
python ml/scripts/evaluate_intent.py               # baseline, calibration, policy tuning, experiments A-E -> ml/reports/
powershell ml/scripts/synthesize_speech.ps1        # Windows only: synthetic test audio
python ml/scripts/evaluate_speech.py small         # WER, latency, audio-to-answer pipeline
python ml/scripts/prepare_nllb.py                  # translation model (one-off)
python ml/scripts/multilingual_testset.py          # 47 sentences x en/hi/pa/de (author-written)
python ml/scripts/build_translations.py            # curated hi/pa/de replies
python ml/scripts/evaluate_multilingual.py         # per-language accuracy, language ID, MT number check
python ml/scripts/export_evaluation.py             # data for the in-app dashboard (#/evaluation)
```

A Colab version of the training step: `ml/notebooks/VoxSure_Train_Colab.ipynb`.

## Answering any question (optional, needs an AI provider)

Campus questions are always answered from the reviewed knowledge base. Questions that are *not* about campus topics are
normally declined ("outside what I can help with"). If you configure an AI provider, those questions are answered by a
general AI model instead, in the language the user wrote in, and the reply is labelled **General answer · AI-generated**.

* **Claude (paid, rate-limited):** set `ANTHROPIC_API_KEY` (optionally `GENERAL_MODEL=claude-haiku-5-5` for a cheaper, faster model).
* **Any OpenAI-compatible provider (several have free tiers with their own limits, check current terms):** set `GENERAL_PROVIDER=openai_compat`,
  `GENERAL_API_KEY`, `GENERAL_BASE_URL` (e.g. Groq `https://api.groq.com/openai/v1`, Google Gemini's compatible endpoint, OpenRouter) and `GENERAL_MODEL`.
* Put keys in `.env` or the host's secret settings, **never in code or chat**. `GENERAL_DAILY_CAP` (default 300) bounds usage across all users.
* **Privacy:** with this on, the text of a non-campus question and the last few messages go to the provider; nothing else (no audio, no identifiers).
  Users can switch it off in Settings; operators can disable it with `GENERAL_ANSWERS_ENABLED=false`.
* **Honesty:** AI answers can be wrong and are not verified. Tested with stand-in clients and a local mock server; a live call needs your key.

## Tests

```bash
cd backend && python -m pytest          # 83 tests: policy, all endpoints, multilingual, general answers, failure paths, privacy
cd frontend && npm test                 # 21 tests: components, evaluation page, axe accessibility audits
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
