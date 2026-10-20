from __future__ import annotations

import datetime as dt
import json
import logging
import threading
import urllib.error
import urllib.request

import anthropic

log = logging.getLogger("voxsure.general")

SYSTEM = (
    "You are VoxSure, a friendly voice assistant for students. The user asked something outside the campus knowledge base, "
    "so answer it as a helpful general assistant.\n"
    "Style: this will be read aloud, so use short, plain sentences, no markdown, no bullet symbols, and keep it under about 120 words "
    "unless the user clearly needs more.\n"
    "Language: reply in the same language and script the user wrote in (if they wrote Romanised Hindi, Gujarati or similar, reply in the same style).\n"
    "Honesty: do not invent facts. If you are not sure, or the question needs current information you do not have, say so plainly. "
    "Never state specific facts about the user's own college (hours, fees, deadlines, rules): say you do not have verified information "
    "and suggest contacting the relevant office. For medical, legal or financial questions give only general information and suggest a professional."
)


class _Capped:
    """Shared daily cap (bounds usage and spend). Any provider failure returns None so the caller falls back."""

    provider_name = "AI model"

    def __init__(self, daily_cap: int):
        self.daily_cap = daily_cap
        self._lock = threading.Lock()
        self._day = dt.date.today()
        self._count = 0

    def _take(self) -> bool:
        with self._lock:
            today = dt.date.today()
            if today != self._day:
                self._day, self._count = today, 0
            if self._count >= self.daily_cap:
                return False
            self._count += 1
            return True

    def available(self) -> bool:
        with self._lock:
            return dt.date.today() != self._day or self._count < self.daily_cap

    @staticmethod
    def _messages(text: str, history: list[dict] | None) -> list[dict]:
        msgs = [m for m in (history or []) if m.get("role") in ("user", "assistant") and m.get("content")]
        while msgs and msgs[0]["role"] != "user":   # providers require the first turn to be a user turn
            msgs.pop(0)
        msgs.append({"role": "user", "content": text})
        return msgs


class GeneralAnswerer(_Capped):
    """Open-domain answers via the Anthropic (Claude) API. Sends only the user's message and a few recent turns."""

    provider_name = "Claude"

    def __init__(self, model: str = "claude-opus-5-5", timeout_s: float = 25.0, daily_cap: int = 300,
                 effort: str = "low", client: object | None = None, api_key: str | None = None):
        super().__init__(daily_cap)
        self.model = model
        self.effort = effort
        self.client = client or anthropic.Anthropic(api_key=api_key or None, timeout=timeout_s, max_retries=1)

    def answer(self, text: str, history: list[dict] | None = None) -> str | None:
        if not self._take():
            log.warning("general-answer daily cap reached")
            return None
        kwargs = dict(
            model=self.model, max_tokens=2000, system=SYSTEM, messages=self._messages(text, history),
            # Server-side refusal fallback (opt-in header) and low effort for fast, cheap chat replies.
            extra_headers={"anthropic-beta": "server-side-fallback-2026-07-01"},
            extra_body={"fallbacks": "default", "output_config": {"effort": self.effort}},
        )
        try:
            try:
                resp = self.client.messages.create(**kwargs)
            except anthropic.BadRequestError:
                # Fallback/effort fields not accepted for this model or account: retry without the extras.
                kwargs.pop("extra_headers"); kwargs.pop("extra_body")
                resp = self.client.messages.create(**kwargs)
        except anthropic.APIError as exc:       # auth, rate limit, network, server errors
            log.warning("general answer failed: %s", type(exc).__name__)
            return None
        if getattr(resp, "stop_reason", None) == "refusal":
            return None
        out = " ".join(b.text.strip() for b in resp.content if getattr(b, "type", "") == "text" and b.text.strip()).strip()
        return out or None


class OpenAICompatAnswerer(_Capped):
    """Open-domain answers via any OpenAI-compatible chat-completions endpoint (Groq, Google Gemini's compat
    endpoint, OpenRouter, a local server, ...). Many offer free tiers with rate limits; check the provider's current terms."""

    def __init__(self, base_url: str, api_key: str, model: str, timeout_s: float = 25.0, daily_cap: int = 300,
                 provider_name: str = "AI model"):
        super().__init__(daily_cap)
        self.url = base_url.rstrip("/") + "/chat/completions"
        self.api_key, self.model, self.timeout_s = api_key, model, timeout_s
        self.provider_name = provider_name

    def _post(self, payload: dict) -> dict:
        req = urllib.request.Request(
            self.url, data=json.dumps(payload).encode("utf-8"), method="POST",
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"})
        with urllib.request.urlopen(req, timeout=self.timeout_s) as r:  # noqa: S310 (https URL from server config)
            return json.loads(r.read().decode("utf-8"))

    def answer(self, text: str, history: list[dict] | None = None) -> str | None:
        if not self._take():
            log.warning("general-answer daily cap reached")
            return None
        payload = {"model": self.model, "max_tokens": 600, "temperature": 0.4,
                   "messages": [{"role": "system", "content": SYSTEM}, *self._messages(text, history)]}
        try:
            data = self._post(payload)
            out = (data["choices"][0]["message"].get("content") or "").strip()
        except (urllib.error.URLError, TimeoutError, KeyError, IndexError, ValueError, OSError) as exc:
            log.warning("general answer failed: %s", type(exc).__name__)
            return None
        return out or None
