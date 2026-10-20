from __future__ import annotations

import asyncio
import re
import time
import uuid

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.concurrency import run_in_threadpool

from ..core.languages import LANGS, detect_text_language, display_name
from ..core.policy import OOS, decide
from ..schemas.models import (Source, Candidate, Thresholds, FeedbackRequest, FeedbackResponse, HealthResponse, IntentRequest,
                              IntentResponse, IntentScore, MemoryItem, Option, TranscribeResponse, WordScore,
                              TurnRequest, TurnResponse)
from ..services.asr import AudioDecodeError, NoSpeechError
from ..services.knowledge import numbers_preserved

router = APIRouter(prefix="/api/v1")

PERSONAL_QUESTION = re.compile(r"\b(my name|who am i|do you (know|remember) me|my age|how old am i|where do i live)\b", re.I)

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
    general_ready = s.general is not None and s.general.available()
    return HealthResponse(
        status="ok" if all(ready) else "degraded", asr_ready=ready[0], intent_ready=ready[1], general_ready=general_ready,
        translation_ready=s.translator is not None,
        general_provider=getattr(s.general, "provider_name", None) if s.general is not None else None,
        general_model=getattr(s.general, "model", None) if s.general is not None else None,
        asr_multilingual=bool(getattr(s.transcriber, "multilingual", False)),
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
        action, intent_name, kind, d_options, reason, conf = "answer", body.chosen_intent, None, [], "user_confirmed", 1.0
    else:
        probs = await run_in_threadpool(_classify, s, text_en)
        d = decide(probs, s.policy, asr_conf=body.asr_confidence, attempts=body.attempts)
        action, intent_name, kind, reason, d_options = d.action, d.intent, d.clarify_kind, d.reason, d.options
        conf = max(probs.values())
        candidates = [Candidate(intent=k, label=kb.label(k), probability=round(v, 4))
                      for k, v in sorted(probs.items(), key=lambda kv: kv[1], reverse=True)[:3]]

    # Questions about the USER's own details ("what is my name?") must never be answered with the assistant's own
    # introduction or a greeting, even if the classifier confuses them with "what is your name?".
    if (action == "answer" and intent_name in ("about_bot", "greeting") and body.chosen_intent is None
            and PERSONAL_QUESTION.search(text_en)):
        action, intent_name, kind, reason, d_options = "fallback", None, None, "out_of_scope", []

    def render(code: str) -> str:
        if action == "answer":
            return kb.answer(intent_name, code)
        if action == "fallback":
            return kb.fallback(reason, code)
        if kind == "disambiguate":
            return kb.clarification_question(d_options, code)
        return kb.repair(code, typed=body.input_mode == "text")

    response = render("en")
    options = [Option(intent=i, label=kb.label(i)) for i in d_options]
    response_en, mode, warning = None, None, False
    answer_source = "knowledge_base" if action == "answer" else "none"
    sources = [Source(**x) for x in kb.sources(intent_name)] if action == "answer" else []

    # Open-domain questions: the campus classifier says out-of-scope, so (if the user allows it and a key is
    # configured) a general AI model answers in the user's own language, clearly labelled as AI-generated.
    general_used = False
    # Not a confident campus question: either clearly off-topic, or the classifier is unsure about a message that
    # was heard fine (typed, or voice with decent recogniser confidence). Unsure + doubtful speech stays a "please
    # check what I heard" prompt; competing campus intents stay a targeted clarification.
    unsure_but_clear = (action == "clarify" and kind == "repair"
                        and reason in ("low_confidence", "medium_confidence", "uncertain_out_of_scope")
                        and (body.asr_confidence is None or body.asr_confidence >= s.policy.asr_low))
    off_topic = action == "fallback" and reason == "out_of_scope"
    if ((off_topic or unsure_but_clear) and body.chosen_intent is None and body.allow_general
            and s.general is not None and s.general.available()):
        hist = [{"role": h.role, "content": h.text} for h in body.history[-6:]]
        general_text = await run_in_threadpool(s.general.answer, text, hist)
        if general_text:
            general_used = True
            action, intent_name, kind, reason, d_options = "answer", "general_knowledge", None, "general_ai", []
            response, options, answer_source = general_text, [], "general_ai"
            sources = [Source(title=f"General answer written by an AI model ({getattr(s.general, 'provider_name', 'AI')}). It is not from the campus knowledge base and may be wrong.")]

    # Reply in the user's language. Curated (hand-written) text where available (hi, pa, de);
    # otherwise NLLB machine translation guarded by a numeric-consistency check.
    if lang != "en" and not general_used:
        response_en = response
        if kb.has_curated(lang):
            response = render(lang)
            options = [Option(intent=i, label=kb.label(i, lang)) for i in d_options]
            mode = "curated"
        elif tr is not None and translation_available:
            try:
                response = await run_in_threadpool(tr.translate, response_en, "en", lang)
                options = [Option(intent=o.intent, label=await run_in_threadpool(tr.translate, o.label, "en", lang))
                           for o in options]
                mode = "machine"
                warning = not numbers_preserved(response_en, response)
            except Exception:
                translation_available, response, response_en = False, render("en"), None
        else:
            translation_available = False
            response_en = None

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
        sources=sources, answer_source=answer_source,
        thresholds=Thresholds(t_high=s.policy.t_high, margin=s.policy.margin, t_low=s.policy.t_low),
        reason=reason, memory_applied=memory_applied, lang=lang, lang_name=display_name(lang),
        lang_verified=verified, translated_input=text_en if (lang != "en" and tr is not None) else None,
        translation_available=translation_available, response_en=response_en, translation_mode=mode,
        translation_warning=warning,
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


@router.get("/evaluation")
async def evaluation(request: Request) -> dict:
    """Measured results for the in-app dashboard (generated by ml/scripts/export_evaluation.py)."""
    path = state(request).settings.evaluation_path
    if not path.exists():
        raise err(404, "no_evaluation", "Evaluation results have not been generated yet.")
    import json
    return await run_in_threadpool(lambda: json.loads(path.read_text(encoding="utf-8")))


@router.get("/metrics/summary")
async def metrics_summary(request: Request) -> dict:
    return await run_in_threadpool(state(request).db.summary)


def _check_client(client_id: str) -> None:
    import re
    if not re.fullmatch(r"[A-Za-z0-9_-]{8,64}", client_id):
        raise err(422, "bad_client_id", "Invalid client id.")
