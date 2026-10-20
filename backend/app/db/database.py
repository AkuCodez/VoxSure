"""Minimal persistence: opt-in correction memory + metrics-only evaluation events.

No raw audio and no transcripts are stored in eval_events. Correction memory stores
only text the user explicitly chose to remember, keyed by an anonymous client id.
All access is through SQLAlchemy parameterised statements.
"""
from __future__ import annotations

import re
import time
from contextlib import contextmanager
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, Integer, String, create_engine, delete, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker


class Base(DeclarativeBase):
    pass


class CorrectionMemory(Base):
    __tablename__ = "correction_memory"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    client_id: Mapped[str] = mapped_column(String(64), index=True)
    original_norm: Mapped[str] = mapped_column(String(300))
    corrected_text: Mapped[str] = mapped_column(String(300))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                 default=lambda: datetime.now(timezone.utc))


class EvalEvent(Base):
    __tablename__ = "eval_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    turn_id: Mapped[str] = mapped_column(String(40), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                 default=lambda: datetime.now(timezone.utc))
    input_mode: Mapped[str] = mapped_column(String(10))
    action: Mapped[str] = mapped_column(String(10))
    intent: Mapped[str | None] = mapped_column(String(40), nullable=True)
    clarify_kind: Mapped[str | None] = mapped_column(String(16), nullable=True)
    top_prob: Mapped[float] = mapped_column(Float)
    latency_ms: Mapped[float] = mapped_column(Float)
    edited: Mapped[int] = mapped_column(Integer, default=0)


def normalise(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9' ]", " ", text.lower())).strip()


class Database:
    def __init__(self, url: str):
        kwargs = {"connect_args": {"check_same_thread": False}} if url.startswith("sqlite") else {"pool_pre_ping": True}
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+psycopg://", 1)
        elif url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+psycopg://", 1)
        self.engine = create_engine(url, **kwargs)
        Base.metadata.create_all(self.engine)
        self._Session = sessionmaker(self.engine, expire_on_commit=False)

    @contextmanager
    def session(self):
        s = self._Session()
        try:
            yield s
            s.commit()
        except Exception:
            s.rollback()
            raise
        finally:
            s.close()

    def ping(self) -> bool:
        try:
            with self.session() as s:
                s.execute(select(1))
            return True
        except Exception:
            return False

    # ---- correction memory ----
    def remember(self, client_id: str, original: str, corrected: str) -> CorrectionMemory:
        norm = normalise(original)
        with self.session() as s:
            row = s.scalars(select(CorrectionMemory).where(
                CorrectionMemory.client_id == client_id, CorrectionMemory.original_norm == norm)).first()
            if row:
                row.corrected_text = corrected
            else:
                row = CorrectionMemory(client_id=client_id, original_norm=norm, corrected_text=corrected)
                s.add(row)
            s.flush()
            return row

    def lookup(self, client_id: str, text: str) -> str | None:
        with self.session() as s:
            row = s.scalars(select(CorrectionMemory).where(
                CorrectionMemory.client_id == client_id,
                CorrectionMemory.original_norm == normalise(text))).first()
            return row.corrected_text if row else None

    def list_memory(self, client_id: str) -> list[CorrectionMemory]:
        with self.session() as s:
            return list(s.scalars(select(CorrectionMemory).where(
                CorrectionMemory.client_id == client_id).order_by(CorrectionMemory.id)))

    def delete_memory(self, client_id: str, item_id: int | None = None) -> int:
        stmt = delete(CorrectionMemory).where(CorrectionMemory.client_id == client_id)
        if item_id is not None:
            stmt = stmt.where(CorrectionMemory.id == item_id)
        with self.session() as s:
            return s.execute(stmt).rowcount or 0

    # ---- metrics ----
    def log_event(self, **kw) -> None:
        with self.session() as s:
            s.add(EvalEvent(**kw))

    def summary(self) -> dict:
        with self.session() as s:
            rows = list(s.scalars(select(EvalEvent)))
        n = len(rows)
        lat = sorted(r.latency_ms for r in rows)
        pct = lambda p: lat[min(n - 1, int(p * n))] if n else None
        return {
            "turns": n,
            "answer": sum(r.action == "answer" for r in rows),
            "clarify": sum(r.action == "clarify" for r in rows),
            "fallback": sum(r.action == "fallback" for r in rows),
            "edited": sum(r.edited for r in rows),
            "latency_ms_median": pct(0.5), "latency_ms_p95": pct(0.95),
        }


def now_ms() -> float:
    return time.perf_counter() * 1000
