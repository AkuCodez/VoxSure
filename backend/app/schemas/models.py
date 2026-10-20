from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

ClientId = Field(default=None, min_length=8, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")


class TranscribeResponse(BaseModel):
    transcript: str
    asr_confidence: float
    duration_s: float
    latency_ms: float


class IntentRequest(BaseModel):
    text: str = Field(min_length=1, max_length=300)


class IntentScore(BaseModel):
    intent: str
    probability: float


class IntentResponse(BaseModel):
    intent: str
    confidence: float
    in_scope: bool
    top: list[IntentScore]
    model_version: str


class TurnRequest(BaseModel):
    text: str = Field(min_length=1, max_length=300)
    input_mode: Literal["voice", "text"] = "text"
    asr_confidence: float | None = Field(default=None, ge=0, le=1)
    chosen_intent: str | None = Field(default=None, max_length=40)  # user picked a clarification option
    attempts: int = Field(default=0, ge=0, le=10)
    edited: bool = False
    client_id: str | None = ClientId
    use_memory: bool = False


class Option(BaseModel):
    intent: str
    label: str


class Candidate(BaseModel):
    intent: str
    label: str
    probability: float


class Thresholds(BaseModel):
    t_high: float
    margin: float
    t_low: float


class TurnResponse(BaseModel):
    turn_id: str
    transcript: str
    action: Literal["answer", "clarify", "fallback"]
    clarify_kind: Literal["disambiguate", "repair"] | None = None
    intent: str | None = None
    confidence: float
    response: str
    options: list[Option] = []
    candidates: list[Candidate] = []
    thresholds: Thresholds | None = None
    reason: str
    memory_applied: bool = False
    model_version: str
    latency_ms: float


class FeedbackRequest(BaseModel):
    turn_id: str | None = Field(default=None, max_length=40)
    client_id: str = Field(min_length=8, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")
    original_text: str = Field(min_length=1, max_length=300)
    corrected_text: str = Field(min_length=1, max_length=300)
    remember: bool = False  # explicit opt-in to store the correction


class MemoryItem(BaseModel):
    id: int
    original: str
    corrected: str


class FeedbackResponse(BaseModel):
    stored: bool
    item: MemoryItem | None = None


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    asr_ready: bool
    intent_ready: bool
    db_ready: bool
    model_version: str | None = None
    asr_model: str | None = None
