from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import Settings  # noqa: E402
from app.core.policy import PolicyParams  # noqa: E402
from app.db.database import Database  # noqa: E402
from app.main import VoxState, create_app  # noqa: E402
from app.services.asr import AudioDecodeError, NoSpeechError, Transcription  # noqa: E402
from app.services.knowledge import KnowledgeBase  # noqa: E402

LABELS = ["library_hours", "fee_payment", "exam_info", "hostel_info", "greeting", "out_of_scope"]


def dist(**kw: float) -> dict[str, float]:
    rest = (1 - sum(kw.values())) / max(1, len(LABELS) - len(kw))
    return {l: kw.get(l, rest) for l in LABELS}


class FakeClassifier:
    version = "fake-v0"

    def __init__(self):
        self.table = {
            "when does the library open": dist(library_hours=0.97),
            "hello": dist(greeting=0.98),
            "what is my name": dist(greeting=0.97),   # classifier confuses it with "what is your name"
            "when does it open": dist(library_hours=0.45, hostel_info=0.40),
            "gibberish words": dist(library_hours=0.20, fee_payment=0.19, exam_info=0.18),
            "what is the weather": dist(out_of_scope=0.95),
        }

    def predict(self, text: str):
        return self.table.get(text.lower().strip("?. "), dist(out_of_scope=0.9))


class FakeTranslator:
    """Deterministic stand-in for NLLB: known phrases map to English, replies get a language prefix."""
    TO_EN = {"पुस्तकालय कब खुलता है": "when does the library open",
             "ਲਾਇਬ੍ਰੇਰੀ ਕਦੋਂ ਖੁੱਲ੍ਹਦੀ ਹੈ": "when does the library open",
             "wann öffnet die bibliothek": "when does the library open"}

    def translate(self, text, src, tgt):
        if src == tgt:
            return text
        if tgt == "en":
            return self.TO_EN.get(text.strip("?. ").lower(), text)
        return f"[{tgt}] {text}"


class FakeTranscriber:
    model_name = "fake.en"

    def __init__(self):
        self.mode = "ok"

    def transcribe(self, audio: bytes, language=None):
        self.last_language = language
        if self.mode == "nospeech":
            raise NoSpeechError()
        if self.mode == "decode":
            raise AudioDecodeError("bad")
        if self.mode == "slow":
            import time
            time.sleep(0.5)
        return Transcription(text="when does the library open", confidence=0.91, duration_s=2.0, language="en")


@pytest.fixture
def vox(tmp_path):
    settings = Settings(_env_file=None, database_url=f"sqlite:///{tmp_path/'t.db'}", max_audio_bytes=1000,
                        asr_timeout_s=0.2, frontend_dist=tmp_path / "nodist")
    return VoxState(settings=settings, kb=KnowledgeBase(settings.knowledge_base_path),
                    policy=PolicyParams(), db=Database(settings.database_url),
                    classifier=FakeClassifier(), transcriber=FakeTranscriber(), translator=FakeTranslator())


@pytest.fixture
def client(vox):
    return TestClient(create_app(vox))
