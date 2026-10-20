from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    intent_model_dir: Path = REPO_ROOT / "ml" / "artifacts" / "intent_model"
    policy_path: Path = REPO_ROOT / "ml" / "artifacts" / "policy.json"
    knowledge_base_path: Path = REPO_ROOT / "backend" / "app" / "data" / "knowledge_base.json"
    frontend_dist: Path = REPO_ROOT / "frontend" / "dist"

    nllb_dir: Path = REPO_ROOT / "ml" / "artifacts" / "nllb-ct2"
    language_status_path: Path = REPO_ROOT / "backend" / "app" / "data" / "language_status.json"
    whisper_model: str = "small"  # multilingual; use base.en for English-only/lower latency
    whisper_compute_type: str = "int8"
    whisper_cache_dir: str | None = None
    asr_timeout_s: float = 45.0

    max_audio_bytes: int = 5 * 1024 * 1024
    max_text_chars: int = 300

    database_url: str = "sqlite:///./voxsure.db"
    cors_origins: str = ""  # comma-separated; empty = same-origin only
    log_metrics: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()
