"""Error-aware recovery policy (the VoxSure differentiator).

Pure function of calibrated class probabilities (+ optional ASR confidence and the
number of failed attempts). No ML imports so it can be unit-tested and tuned offline.

Actions
  answer    - confident, in-scope: answer from the reviewed knowledge base
  clarify   - ask a targeted question; `clarify_kind` is
                "disambiguate" (competing intents -> selectable options) or
                "repair"       (low confidence / likely mis-heard -> edit or repeat)
  fallback  - out of scope or repeated failure: transparent fallback
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
from pathlib import Path

OOS = "out_of_scope"
SMALLTALK = {"greeting", "thanks_bye"}


@dataclass(frozen=True)
class PolicyParams:
    t_high: float = 0.80      # min top probability to answer
    margin: float = 0.25      # min gap between top-1 and top-2 to answer
    t_low: float = 0.35       # below this: likely corrupted -> repair
    t_oos: float = 0.50       # min top probability to declare out-of-scope
    asr_low: float = 0.40     # Whisper-derived confidence below which we distrust the transcript
    asr_override: float = 0.97  # ...unless the intent model is extremely sure
    min_candidate: float = 0.08
    max_options: int = 3
    max_attempts: int = 2     # after this many failed clarifications, stop looping

    @classmethod
    def load(cls, path: Path) -> "PolicyParams":
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            allowed = {k: v for k, v in data.get("params", data).items() if k in cls.__dataclass_fields__}
            return cls(**allowed)
        return cls()


@dataclass
class Decision:
    action: str                       # answer | clarify | fallback
    intent: str | None = None         # intent to answer with (action == answer)
    clarify_kind: str | None = None   # disambiguate | repair
    options: list[str] = field(default_factory=list)  # candidate intents for disambiguation
    reason: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def decide(probs: dict[str, float], params: PolicyParams, *, asr_conf: float | None = None,
           attempts: int = 0) -> Decision:
    ranked = sorted(probs.items(), key=lambda kv: kv[1], reverse=True)
    top, p1 = ranked[0]
    p2 = ranked[1][1] if len(ranked) > 1 else 0.0
    margin = p1 - p2
    asr_doubtful = asr_conf is not None and asr_conf < params.asr_low

    def give_up_or(d: Decision) -> Decision:
        if attempts >= params.max_attempts:
            return Decision("fallback", reason="repeated_failure")
        return d

    if top == OOS:
        if p1 >= params.t_oos and not asr_doubtful:
            return Decision("fallback", reason="out_of_scope")
        return give_up_or(Decision("clarify", clarify_kind="repair", reason="uncertain_out_of_scope"))

    if p1 < params.t_low:
        return give_up_or(Decision("clarify", clarify_kind="repair", reason="low_confidence"))

    if asr_doubtful and p1 < params.asr_override:
        return give_up_or(Decision("clarify", clarify_kind="repair", reason="low_asr_confidence"))

    if p1 >= params.t_high and (margin >= params.margin or top in SMALLTALK):
        return Decision("answer", intent=top, reason="confident")

    options = [l for l, p in ranked
               if l not in (OOS,) and l not in SMALLTALK and p >= params.min_candidate][:params.max_options]
    if len(options) >= 2:
        return give_up_or(Decision("clarify", clarify_kind="disambiguate", options=options,
                                   reason="competing_intents"))
    return give_up_or(Decision("clarify", clarify_kind="repair", reason="medium_confidence"))
