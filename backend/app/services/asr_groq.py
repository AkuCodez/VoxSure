from __future__ import annotations

import json
import math
import urllib.error
import urllib.request
import uuid

from ..core.languages import LANGS
from .asr_types import AsrUnavailableError, AudioDecodeError, NoSpeechError, Transcription

# Whisper returns language names ("english"); map them back to ISO codes.
_NAME_TO_ISO = {name.lower(): iso for iso, (_, name) in LANGS.items()}
_NAME_TO_ISO.update({"mandarin": "zh", "castilian": "es", "flemish": "nl", "norwegian": "no"})


def _sniff_ext(b: bytes) -> str:
    if b[:4] == b"\x1aE\xdf\xa3":
        return "webm"
    if b[:4] == b"OggS":
        return "ogg"
    if b[4:8] == b"ftyp":
        return "m4a"
    if b[:4] == b"RIFF":
        return "wav"
    if b[:4] == b"fLaC":
        return "flac"
    if b[:3] == b"ID3" or b[:2] == b"\xff\xfb":
        return "mp3"
    return "webm"


class GroqTranscriber:
    """Whisper large-v3(-turbo) speech-to-text through Groq's OpenAI-compatible API (free tier available).

    Used by the lite deployment instead of a local model. Only the audio clip is sent. Per-word confidences are not
    returned by this API, so word-level highlighting is unavailable (the clip-level confidence still is).
    """

    multilingual = True

    def __init__(self, api_key: str, model: str = "whisper-large-v3-turbo",
                 url: str = "https://api.groq.com/openai/v1/audio/transcriptions", timeout_s: float = 30.0):
        self.api_key, self.model_name, self.url, self.timeout_s = api_key, model, url, timeout_s

    def _post(self, body: bytes, boundary: str) -> dict:
        req = urllib.request.Request(self.url, data=body, method="POST", headers={
            "Authorization": f"Bearer {self.api_key}", "Content-Type": f"multipart/form-data; boundary={boundary}"})
        with urllib.request.urlopen(req, timeout=self.timeout_s) as r:  # noqa: S310 (https URL from server config)
            return json.loads(r.read().decode("utf-8"))

    def transcribe(self, audio: bytes, language: str | None = None) -> Transcription:
        boundary = uuid.uuid4().hex
        fields = {"model": self.model_name, "response_format": "verbose_json", "temperature": "0"}
        if language:
            fields["language"] = language
        parts = []
        for k, v in fields.items():
            parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode())
        parts.append((f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="audio.{_sniff_ext(audio)}"\r\n'
                      f"Content-Type: application/octet-stream\r\n\r\n").encode() + audio + b"\r\n")
        parts.append(f"--{boundary}--\r\n".encode())
        try:
            data = self._post(b"".join(parts), boundary)
        except urllib.error.HTTPError as exc:
            if exc.code == 400:
                raise AudioDecodeError(f"http {exc.code}") from exc
            raise AsrUnavailableError(f"http {exc.code}") from exc   # 401 bad key, 429 rate limit, 5xx
        except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
            raise AsrUnavailableError(type(exc).__name__) from exc
        text = (data.get("text") or "").strip()
        segs = data.get("segments") or []
        if not text or (segs and all(s.get("no_speech_prob", 0) > 0.6 for s in segs)):
            raise NoSpeechError()
        lps = [s["avg_logprob"] for s in segs if "avg_logprob" in s]
        conf = math.exp(sum(lps) / len(lps)) if lps else 0.8
        lang = language or _NAME_TO_ISO.get(str(data.get("language", "")).lower(), "en")
        return Transcription(text=text, confidence=float(min(1.0, conf)), duration_s=float(data.get("duration") or 0.0),
                             language=lang, language_probability=-1.0, words=[])   # -1 = not provided by this API
