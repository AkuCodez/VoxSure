from __future__ import annotations

import asyncio
import time
import uuid

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.concurrency import run_in_threadpool

from ..core.languages import LANGS, detect_text_language, display_name
from ..core.policy import OOS, decide
from ..schemas.models import (Candidate, Thresholds, FeedbackRequest, FeedbackResponse, HealthResponse, IntentRequest,
                              IntentResponse, IntentScore, MemoryItem, Option, TranscribeResponse, WordScore,
                              TurnRequest, TurnResponse)
from ..services.asr import AudioDecodeError, NoSpeechError

router = APIRouter(prefix="/api/v1")

ALLOWED_AUDIO_PREFIXES = ("audio/",)
ALLOWED_AUDIO_EXACT = {"video/webm", "video/mp4", "application/ogg"}


def err(status: int, code: str, message: str) -> HTTPException:
    return HTTPException(status_code=status, detail={"code": code, "message": message})


def state(request: Request):
    return request.app.state.vox


@router.get("/health", response_model=HealthResponse)
async def health(request: Request) -> HealthResponse:
    s = state(request)
    ready = (s.transcriber is not None, s.classifier is not None, s.db.ping())
    return HealthResponse(
        status="ok" if all(ready) else "degraded", asr_ready=ready[0], intent_ready=ready[1],
        db_ready=ready[2], model_version=getattr(s.classifier, "version", None),
        asr_model=getattr(s.transcriber, "model_name", None))


@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe(request: Request, audio: UploadFile = File(...), language: str | None = Form(None)) -> TranscribeResponse:
    s = state(request)
    if s.transcriber is None:
        raise err(503, "asr_unavailable", "Speech recognition is unavailable. Please type your question.")
    ctype = (audio.content_type or "").split(";")[0].strip().lower()
    if not (ctype.startswith(ALLOWED_AUDIO_PREFIXES) or ctype in ALLOWED_AUDIO_EXACT):
        raise err(415, "unsupported_type", "Unsupported audio type.")
    data = await audio.read(s.settings.max_audio_bytes + 1)
    if len(data) == 0:
        raise err(400, "empty_audio", "No audio was received. Please try recording again.")
    if len(data) > s.settings.max_audio_bytes:
        raise err(413, "audio_too_large", "That recording is too long. Please keep it under about 30 seconds.")
    if language in (None, "", "auto"):
        language = None
    elif language not in LANGS:
        raise err(422, "unsupported_language", "That language is not supported.")
    t0 = time.perf_counter()
    try:
        async with s.asr_lock:
            result = await asyncio.wait_for(run_in_threadpool(s.transcriber.transcribe, data, language),
                                            timeout=s.settings.asr_timeout_s)
    except asyncio.TimeoutError:
        raise err(504, "asr_timeout", "Speech recognition timed out. Please try again or type your question.")
    except NoSpeechError:
        raise err(422, "no_speech", "I couldn't hear any speech. Please try again, closer to the microphone.")
    except AudioDecodeError:
        raise err(422, "decode_failed", "I couldn't read that audio. Please try again or type your question.")
    return TranscribeResponse(transcript=result.text, asr_confidence=round(result.confidence, 4),
                              duration_s=round(result.duration_s, 2),
                              latency_ms=round((time.perf_counter() - t0) * 1000, 1),
                              language=result.language, language_name=display_name(result.language),
                              language_probability=round(result.language_probability, 3),
                              words=[WordScore(word=w.word, probability=round(w.probability, 3)) for w in result.words])


def _classify(s, text: str) -> dict[str, float]:
    if s.classifier is None:
        raise err(503, "model_unavailable", "The language model is unavailable. Please try again later.")
    return s.classifier.predict(text)


@router.post("/intent", response_model=IntentResponse)
async def intent(request: Request, body: IntentRequest) -> IntentResponse:
    s = state(request)
    text = body.text.strip()
    if not text:
        raise err(422, "empty_text", "Text must not be empty.")
    probs = await run_in_threadpool(_classify, s, text)
    ranked = sorted(probs.items(), key=lambda kv: kv[1], reverse=True)
    return IntentResponse(intent=ranked[0][0], confidence=round(ranked[0][1], 4),
                          in_scope=ranked[0][0] != OOS,
                          top=[IntentScore(intent=k, probability=round(v, 4)) for k, v in ranked[:3]],
                          model_version=s.classifier.version)


@router.post("/chat/turn", response_model=TurnResponse)
async def chat_turn(request: Request, body: TurnRequest) -> TurnResponse:
    s = state(request)
    t0 = time.perf_counter()
    text = body.text.strip()
    if not text:
        raise err(422, "empty_text", "Text must not be empty.")

    lang = body.lang if body.lang in LANGS else detect_text_language(text)
    tr = s.translator
    translation_available = lang == "en" or tr is not None

    memory_applied = False
    if body.use_memory and body.client_id:
        remembered = await run_in_threadpool(s.db.lookup, body.client_id, text)
        if remembered:
            text, memory_applied = remembered, True

    # The classifier and knowledge base are English: translate non-English input to English first.
    text_en = text
    if lang != "en" and tr is not None:
        try:
            text_en = await run_in_threadpool(tr.translate, text, lang, "en")
        except Exception:
            translation_available = False

    kb = s.kb
    candidates: list[Candidate] = []
    if body.chosen_intent is not None:
        if not kb.has(body.chosen_intent):
            raise err(422, "unknown_intent", "Unknown intent selection.")
        action, intent_name, kind, options, reason, conf = "answer", body.chosen_intent, None, [], "user_confirmed", 1.0
        response = kb.answer(intent_name)
    else:
        probs = await run_in_threadpool(_classify, s, text_en)
        d = decide(probs, s.policy, asr_conf=body.asr_confidence, attempts=body.attempts)
        action, intent_name, kind, reason = d.action, d.intent, d.clarify_kind, d.reason
        conf = max(probs.values())
        candidates = [Candidate(intent=k, label=kb.label(k), probability=round(v, 4))
                      for k, v in sorted(probs.items(), key=lambda kv: kv[1], reverse=True)[:3]]
        options = [Option(intent=i, label=kb.label(i)) for i in d.options]
        if action == "answer":
            response = kb.answer(intent_name)
        elif action == "fallback":
            response = kb.fallback_repeated if reason == "repeated_failure" else kb.fallback_oos
        elif kind == "disambiguate":
            response = kb.clarify_prompt
        else:
            response = kb.repair_prompt

    # Reply in the user's language (static answers are cached after the first translation).
    if lang != "en" and tr is not None and translation_available:
        try:
            response = await run_in_threadpool(tr.translate, response, "en", lang)
            options = [Option(intent=o.intent, label=await run_in_threadpool(tr.translate, o.label, "en", lang))
                       for o in options]
            candidates = [c.model_copy(update={"label": c.label}) for c in candidates]
        except Exception:
            translation_available = False

    latency = (time.perf_counter() - t0) * 1000
    turn_id = uuid.uuid4().hex[:16]
    if s.settings.log_metrics:
        try:
            await run_in_threadpool(lambda: s.db.log_event(
                turn_id=turn_id, input_mode=body.input_mode, action=action, intent=intent_name,
                clarify_kind=kind, top_prob=float(conf), latency_ms=latency, edited=int(body.edited)))
        except Exception:  # metrics must never break the user flow
            pass
    verified = lang == "en" or lang in s.language_status.get("verified", [])
    return TurnResponse(
        turn_id=turn_id, transcript=text, action=action, clarify_kind=kind, intent=intent_name,
        confidence=round(float(conf), 4), response=response, options=options, candidates=candidates,
        thresholds=Thresholds(t_high=s.policy.t_high, margin=s.policy.margin, t_low=s.policy.t_low),
        reason=reason, memory_applied=memory_applied, lang=lang, lang_name=display_name(lang),
        lang_verified=verified, translated_input=text_en if (lang != "en" and tr is not None) else None,
        translation_available=translation_available,
        model_version=getattr(s.classifier, "version", "n/a"), latency_ms=round(latency, 1))


@router.post("/feedback", response_model=FeedbackResponse)
async def feedback(request: Request, body: FeedbackRequest) -> FeedbackResponse:
    s = state(request)
    if not body.remember:  # nothing is stored without explicit opt-in
        return FeedbackResponse(stored=False)
    row = await run_in_threadpool(s.db.remember, body.client_id, body.original_text.strip(),
                                  body.corrected_text.strip())
    return FeedbackResponse(stored=True, item=MemoryItem(id=row.id, original=row.original_norm,
                                                         corrected=row.corrected_text))


@router.get("/memory/{client_id}", response_model=list[MemoryItem])
async def list_memory(request: Request, client_id: str) -> list[MemoryItem]:
    _check_client(client_id)
    rows = await run_in_threadpool(state(request).db.list_memory, client_id)
    return [MemoryItem(id=r.id, original=r.original_norm, corrected=r.corrected_text) for r in rows]


@router.delete("/memory/{client_id}")
async def delete_all_memory(request: Request, client_id: str) -> dict:
    _check_client(client_id)
    return {"deleted": await run_in_threadpool(state(request).db.delete_memory, client_id)}


@router.delete("/memory/{client_id}/{item_id}")
async def delete_memory_item(request: Request, client_id: str, item_id: int) -> dict:
    _check_client(client_id)
    n = await run_in_threadpool(state(request).db.delete_memory, client_id, item_id)
    if n == 0:
        raise err(404, "not_found", "No such memory item.")
    return {"deleted": n}


@router.get("/metrics/summary")
async def metrics_summary(request: Request) -> dict:
    return await run_in_threadpool(state(request).db.summary)


def _check_client(client_id: str) -> None:
    import re
    if not re.fullmatch(r"[A-Za-z0-9_-]{8,64}", client_id):
        raise err(422, "bad_client_id", "Invalid client id.")
