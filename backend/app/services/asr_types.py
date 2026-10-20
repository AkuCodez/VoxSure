"""Light-weight speech types shared by every transcriber backend (no heavy imports)."""
from __future__ import annotations

from dataclasses import dataclass, field


class NoSpeechError(Exception):
    """Audio decoded but contained no recognisable speech."""


class AsrUnavailableError(Exception):
    """The speech service could not be reached or refused the request (bad key, rate limit, outage)."""


class AudioDecodeError(Exception):
    """Audio could not be decoded."""


@dataclass
class WordInfo:
    word: str
    probability: float


@dataclass
class Transcription:
    text: str
    confidence: float      # exp(mean segment avg_logprob), in (0, 1]
    duration_s: float
    language: str
    language_probability: float = 1.0
    words: list[WordInfo] = field(default_factory=list)
