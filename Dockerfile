# Single-image deployment: React build + FastAPI (Whisper + DistilBERT) on one origin.
# Works on Hugging Face Spaces (Docker SDK, port 7860), Render, Fly.io, Railway, etc.

FROM node:22-slim AS web
WORKDIR /web
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

FROM python:3.10-slim AS app
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 HF_HOME=/app/.cache/huggingface \
    WHISPER_CACHE_DIR=/app/.cache/whisper PORT=7860
WORKDIR /app

# CPU-only torch keeps the image small (~200 MB instead of ~2.5 GB)
RUN pip install torch==2.5.1 --index-url https://download.pytorch.org/whl/cpu
COPY backend/requirements.txt backend/requirements.txt
RUN pip install -r backend/requirements.txt

# Bake the Whisper weights into the image so the first request is not a cold download
RUN python -c "from faster_whisper import WhisperModel; WhisperModel('small', device='cpu', compute_type='int8', download_root='/app/.cache/whisper')"

# Translation model (NLLB-200 distilled 600M -> int8 CTranslate2, ~600 MB). Downloads 2.4 GB at build time,
# converts, then deletes the download cache so the image keeps only the converted model.
COPY ml/scripts/prepare_nllb.py ml/scripts/prepare_nllb.py
RUN python ml/scripts/prepare_nllb.py && rm -rf /app/.cache/huggingface

COPY backend/app backend/app
COPY ml/artifacts ml/artifacts
COPY --from=web /web/dist frontend/dist

# Hugging Face Spaces runs as uid 1000
RUN useradd -m -u 1000 user && chown -R user:user /app
USER user
EXPOSE 7860
WORKDIR /app/backend
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
