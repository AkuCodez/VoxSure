from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .api.routes import router
from .core.config import Settings, get_settings
from .core.policy import PolicyParams
from .db.database import Database
from .services.knowledge import KnowledgeBase

log = logging.getLogger("voxsure")


@dataclass
class VoxState:
    settings: Settings
    kb: KnowledgeBase
    policy: PolicyParams
    db: Database
    classifier: Any = None
    transcriber: Any = None
    translator: Any = None
    general: Any = None
    language_status: dict = field(default_factory=dict)
    asr_lock: asyncio.Lock = field(default_factory=asyncio.Lock)


def build_general(settings: Settings):
    """Pick the general-answer provider from environment variables (keys are never stored in code)."""
    if not settings.general_answers_enabled:
        return None
    provider = settings.general_provider
    anthropic_key = settings.anthropic_api_key
    compat_key = settings.general_api_key
    if provider in ("auto", "anthropic") and anthropic_key:
        from .services.general import GeneralAnswerer
        return GeneralAnswerer(settings.general_model or "claude-opus-5-5", settings.general_timeout_s,
                               settings.general_daily_cap, settings.general_effort, api_key=anthropic_key)
    if provider in ("auto", "openai_compat") and compat_key and settings.general_base_url and settings.general_model:
        from .services.general import OpenAICompatAnswerer
        return OpenAICompatAnswerer(settings.general_base_url, compat_key, settings.general_model,
                                    settings.general_timeout_s, settings.general_daily_cap,
                                    settings.general_provider_name)
    return None


def build_lite_state(settings: Settings, state: "VoxState") -> None:
    """Lite mode: ONNX classifier + hosted Whisper (Groq) + LLM translation. No PyTorch, faster-whisper or NLLB."""
    settings.max_audio_bytes = min(settings.max_audio_bytes, 4_000_000)   # Vercel rejects request bodies over 4.5 MB
    try:
        from .services.intent_onnx import OnnxIntentClassifier
        state.classifier = OnnxIntentClassifier(settings.intent_onnx_dir)
    except Exception:
        log.exception("ONNX intent model failed to load")
    if settings.groq_api_key:
        from .services.asr_groq import GroqTranscriber
        state.transcriber = GroqTranscriber(settings.groq_api_key, settings.stt_model, settings.stt_url)
    else:
        log.info("No GROQ_API_KEY: voice input is off in lite mode (typed input still works)")
    if state.general is not None:
        from .services.translate_llm import LLMTranslator
        state.translator = LLMTranslator(state.general, settings.translate_daily_cap)
    else:
        log.info("No AI provider configured: non-English input and non-campus questions are limited in lite mode")


def build_full_state(settings: Settings, state: "VoxState") -> None:
    """Full mode: PyTorch DistilBERT, local faster-whisper and local NLLB translation."""
    try:
        from .services.intent import IntentClassifier
        state.classifier = IntentClassifier(settings.intent_model_dir)
    except Exception:
        log.exception("intent model failed to load")
    try:
        if (settings.nllb_dir / "model.bin").exists():
            from .services.translate import Translator
            state.translator = Translator(settings.nllb_dir)
        else:
            log.warning("NLLB model not found at %s; non-English requests fall back to English", settings.nllb_dir)
    except Exception:
        log.exception("translation model failed to load")
    try:
        from .services.asr import Transcriber
        state.transcriber = Transcriber(settings.whisper_model, settings.whisper_compute_type,
                                        settings.whisper_cache_dir)
    except Exception:
        log.exception("ASR model failed to load")


def resolve_db_url(url: str) -> str:
    """On Vercel the project folder is read-only; a relative SQLite path moves to /tmp (writable but ephemeral)."""
    if os.environ.get("VERCEL") and url.startswith("sqlite:///") and not url.startswith("sqlite:////"):
        return "sqlite:////tmp/voxsure.db"
    return url


def build_state(settings: Settings) -> VoxState:
    """Load models. Failures degrade gracefully: /health reports it, typed fallback still works."""
    db_url = resolve_db_url(settings.database_url)
    state = VoxState(settings=settings, kb=KnowledgeBase(settings.knowledge_base_path),
                     policy=PolicyParams.load(settings.policy_path), db=Database(db_url))
    try:
        if settings.language_status_path.exists():
            state.language_status = json.loads(settings.language_status_path.read_text(encoding="utf-8"))
    except Exception:
        log.exception("language status failed to load")
    try:
        state.general = build_general(settings)
        if state.general is None:
            log.info("General AI answers are off (set ANTHROPIC_API_KEY, or GENERAL_API_KEY + GENERAL_BASE_URL + GENERAL_MODEL)")
    except Exception:
        log.exception("general answerer failed to initialise")
    (build_lite_state if settings.mode == "lite" else build_full_state)(settings, state)
    return state


def create_app(state: VoxState | None = None) -> FastAPI:
    settings = state.settings if state else get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Models load once at startup (not at import), so tests and tooling stay fast.
        if not hasattr(app.state, "vox"):
            app.state.vox = await run_in_threadpool(build_state, settings)
        yield

    app = FastAPI(title="VoxSure API", version="1.0.0", lifespan=lifespan)
    if state is not None:
        app.state.vox = state


    # ---- security headers + per-IP rate limiting (in-memory sliding window) ----
    hits: dict[tuple[str, str], deque] = defaultdict(deque)
    HEAVY = ("/api/v1/transcribe", "/api/v1/chat/turn")

    @app.middleware("http")
    async def _guard(request: Request, call_next):
        path = request.url.path
        if path.startswith("/api/"):
            fwd = request.headers.get("x-forwarded-for", "")
            ip = fwd.split(",")[0].strip() or (request.client.host if request.client else "unknown")
            now = time.monotonic()
            for bucket, limit in (("all", settings.rate_limit_per_min),
                                  ("heavy", settings.rate_limit_heavy_per_min if path in HEAVY else 0)):
                if not limit:
                    continue
                q = hits[(ip, bucket)]
                while q and now - q[0] > 60:
                    q.popleft()
                if len(q) >= limit:
                    return JSONResponse({"error": {"code": "rate_limited",
                                                   "message": "Too many requests. Please wait a moment and try again."}},
                                        status_code=429, headers={"Retry-After": "30"})
                q.append(now)
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault("Permissions-Policy", "microphone=(self), camera=(), geolocation=()")
        if not path.startswith("/api/"):
            response.headers.setdefault("Content-Security-Policy",
                "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data:; media-src 'self' blob:; connect-src 'self'; frame-ancestors 'none'")
        return response

    if settings.cors_origins:
        app.add_middleware(CORSMiddleware, allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
                           allow_methods=["*"], allow_headers=["*"])

    @app.exception_handler(HTTPException)
    async def _http_exc(_: Request, exc: HTTPException):
        if isinstance(exc.detail, dict) and "code" in exc.detail:
            return JSONResponse({"error": exc.detail}, status_code=exc.status_code)
        return JSONResponse({"error": {"code": "http_error", "message": str(exc.detail)}},
                            status_code=exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def _validation(_: Request, exc: RequestValidationError):
        return JSONResponse({"error": {"code": "invalid_request",
                                       "message": "The request was not valid."}}, status_code=422)

    @app.exception_handler(Exception)
    async def _unhandled(_: Request, exc: Exception):
        log.exception("unhandled error")
        return JSONResponse({"error": {"code": "server_error",
                                       "message": "Something went wrong. Please try again."}}, status_code=500)

    app.include_router(router)

    dist = settings.frontend_dist
    if dist.exists():
        app.mount("/assets", StaticFiles(directory=dist / "assets"), name="assets")

        @app.get("/{path:path}", include_in_schema=False)
        async def spa(path: str):
            if path.startswith("api/"):
                raise HTTPException(404, "Not found")
            f = (dist / path).resolve()
            if path and f.is_file() and dist.resolve() in f.parents:
                return FileResponse(f)
            return FileResponse(dist / "index.html")

    return app


app = create_app()
