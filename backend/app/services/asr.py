from __future__ import annotations

import io
import math
from dataclasses import dataclass

from faster_whisper import WhisperModel

# Biases decoding toward the supported domain vocabulary (reduces mishearing of
# "bonafide", "hostel", "wifi", ...). Documented in the report as part of the ASR setup.
DOMAIN_PROMPT = ("Student support questions: library, hostel, hall ticket, exam timetable, "
                 "tuition fees, bonafide certificate, scholarship, placement, semester, wifi, "
                 "transcript, canteen.")


class NoSpeechError(Exception):
    """Audio decoded but contained no recognisable speech."""


class AudioDecodeError(Exception):
    """Audio could not be decoded."""


@dataclass
class Transcription:
    text: str
    confidence: float      # exp(mean avg_logprob) over segments, in (0, 1]
    duration_s: float
    language: str


class Transcriber:
    def __init__(self, model_name: str = "base.en", compute_type: str = "int8",
                 cache_dir: str | None = None):
        self.model_name = model_name
        self.model = WhisperModel(model_name, device="cpu", compute_type=compute_type,
                                  download_root=cache_dir)

    def transcribe(self, audio: bytes) -> Transcription:
        try:
            segments, info = self.model.transcribe(
                io.BytesIO(audio), beam_size=1, language="en" if self.model_name.endswith(".en") else None,
                vad_filter=True, initial_prompt=DOMAIN_PROMPT, condition_on_previous_text=False,
                no_speech_threshold=0.6)
            segs = list(segments)
        except Exception as exc:  # PyAV raises various errors on undecodable input
            raise AudioDecodeError(str(exc)) from exc
        text = " ".join(s.text.strip() for s in segs).strip()
        if not text:
            raise NoSpeechError()
        total = sum(max(s.end - s.start, 1e-3) for s in segs)
        avg_lp = sum(s.avg_logprob * max(s.end - s.start, 1e-3) for s in segs) / total
        return Transcription(text=text, confidence=float(math.exp(avg_lp)),
                             duration_s=float(info.duration), language=info.language)
