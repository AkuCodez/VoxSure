from __future__ import annotations

import io
import math
from dataclasses import dataclass, field

from faster_whisper import WhisperModel

# Biases decoding toward the domain vocabulary. Only used when the language is known to be English:
# an English prompt can distort non-English decoding.
DOMAIN_PROMPT = ("Student support questions: library, hostel, hall ticket, exam timetable, "
                 "tuition fees, bonafide certificate, scholarship, placement, semester, wifi, "
                 "transcript, canteen.")


class NoSpeechError(Exception):
    """Audio decoded but contained no recognisable speech."""


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


class Transcriber:
    def __init__(self, model_name: str = "small", compute_type: str = "int8",
                 cache_dir: str | None = None):
        self.model_name = model_name
        self.multilingual = not model_name.endswith(".en")
        self.model = WhisperModel(model_name, device="cpu", compute_type=compute_type,
                                  download_root=cache_dir)

    def transcribe(self, audio: bytes, language: str | None = None) -> Transcription:
        """`language`: ISO code to force, or None to auto-detect (multilingual models only)."""
        lang = "en" if not self.multilingual else language
        try:
            segments, info = self.model.transcribe(
                io.BytesIO(audio), beam_size=1, language=lang, vad_filter=True,
                initial_prompt=DOMAIN_PROMPT if lang == "en" else None,
                condition_on_previous_text=False, no_speech_threshold=0.6, word_timestamps=True)
            segs = list(segments)
        except Exception as exc:  # PyAV raises various errors on undecodable input
            raise AudioDecodeError(str(exc)) from exc
        text = " ".join(s.text.strip() for s in segs).strip()
        if not text:
            raise NoSpeechError()
        total = sum(max(s.end - s.start, 1e-3) for s in segs)
        avg_lp = sum(s.avg_logprob * max(s.end - s.start, 1e-3) for s in segs) / total
        words = [WordInfo(w.word.strip(), float(w.probability)) for s in segs for w in (s.words or []) if w.word.strip()]
        return Transcription(text=text, confidence=float(math.exp(avg_lp)), duration_s=float(info.duration),
                             language=info.language, language_probability=float(info.language_probability),
                             words=words)
