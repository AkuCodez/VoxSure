from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(REPO_ROOT / ".env", REPO_ROOT / "backend" / ".env"), extra="ignore",
                                      populate_by_name=True)

    intent_model_dir: Path = REPO_ROOT / "ml" / "artifacts" / "intent_model"
    policy_path: Path = REPO_ROOT / "ml" / "artifacts" / "policy.json"
    knowledge_base_path: Path = REPO_ROOT / "backend" / "app" / "data" / "knowledge_base.json"
    frontend_dist: Path = REPO_ROOT / "frontend" / "dist"

    nllb_dir: Path = REPO_ROOT / "ml" / "artifacts" / "nllb-ct2"
    language_status_path: Path = REPO_ROOT / "backend" / "app" / "data" / "language_status.json"
    # full = local Whisper/NLLB/PyTorch; lite = hosted speech + LLM translation + ONNX (free serverless hosts).
    # Lite switches on automatically on Vercel; override with VOXSURE_MODE=full|lite.
    mode: str = Field(default_factory=lambda: "lite" if os.environ.get("VERCEL") else "full", validation_alias="VOXSURE_MODE")
    intent_onnx_dir: Path = REPO_ROOT / "ml" / "artifacts" / "intent_onnx"
    groq_api_key: str = ""                  # GROQ_API_KEY: Whisper speech-to-text in lite mode
    stt_model: str = "whisper-large-v3-turbo"
    stt_url: str = "https://api.groq.com/openai/v1/audio/transcriptions"
    translate_daily_cap: int = 600          # lite mode: LLM translation calls per day
    whisper_model: str = "small"  # multilingual; use base.en for English-only/lower latency
    whisper_compute_type: str = "int8"
    whisper_cache_dir: str | None = None
    asr_timeout_s: float = 45.0

    max_audio_bytes: int = 5 * 1024 * 1024
    max_text_chars: int = 300

    database_url: str = "sqlite:///./voxsure.db"
    cors_origins: str = ""  # comma-separated; empty = same-origin only
    log_metrics: bool = True
    anthropic_api_key: str = ""             # ANTHROPIC_API_KEY (env or .env); never commit it
    general_api_key: str = ""               # GENERAL_API_KEY for openai_compat providers
    general_answers_enabled: bool = True
    general_provider: str = "auto"          # auto | anthropic | openai_compat
    general_model: str = ""                 # empty = provider default (anthropic: claude-opus-5-5)
    general_base_url: str = ""              # openai_compat only, e.g. https://api.groq.com/openai/v1
    general_provider_name: str = "AI model" # shown to users, e.g. "Groq"
    general_effort: str = "low"
    general_daily_cap: int = 300            # global cap on general answers per day (bounds the bill)
    general_timeout_s: float = 25.0
    rate_limit_per_min: int = 120      # all /api requests per client IP
    rate_limit_heavy_per_min: int = 30  # /transcribe and /chat/turn per client IP
    evaluation_path: Path = REPO_ROOT / "backend" / "app" / "data" / "evaluation.json"


@lru_cache
def get_settings() -> Settings:
    return Settings()
