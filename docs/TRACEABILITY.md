# Requirements traceability

Status values: **Done** = implemented and covered by an automated test or a recorded manual check;
**Manual** = verified by hand only (stated how); **Pending** = needs a step outside this repo (e.g. public deployment).

| ID | Requirement | Implementation | Verification | Status |
|---|---|---|---|---|
| FR-01 | Voice capture, clear denial/unsupported guidance | `frontend/src/hooks/useRecorder.ts`, `Composer.tsx` | `components.test.tsx` (typed fallback, stop control); denial paths by code review | Done / browser mic: Manual |
| FR-02 | Transcript visible | `MessageBubble.tsx` ("You said (transcript)") | `components.test.tsx` | Done |
| FR-03 | Edit and resubmit transcript | `MessageBubble.tsx`, `useChat.editAndResend` | `components.test.tsx` | Done |
| FR-04 | DL intent + confidence | `services/intent.py`, `POST /intent` | `test_api.py::test_intent_*`; model metrics in report | Done |
| FR-05 | Uncertainty recovery | `core/policy.py` | `test_policy.py` (9 tests); experiments B/C | Done |
| FR-06 | Grounded response | `knowledge_base.json`, `chat_turn` | `test_api.py::test_turn_answer` | Done (sample data) |
| FR-07 | Speech output play/mute/stop | `lib/speech.ts`, header controls | Manual (browser TTS) | Manual |
| FR-08 | Opt-in correction memory, reviewable, deletable | `db/database.py`, `SettingsPanel.tsx` | `test_api.py::test_memory_*`, `test_feedback_*` | Done |
| FR-09 | Turn separation + reset | `ChatPage.tsx`, `useChat.reset` | Manual | Manual |
| FR-10 | Minimal metrics, no raw audio | `EvalEvent` table | `test_turn_logs_metrics_without_text` | Done |
| FR-11 | Public HTTPS deployment | `Dockerfile`, `docs/DEPLOYMENT.md` | Live URL smoke test | **Pending: see README** |
| FR-12 | Failure handling | uniform error envelope, UI alert + typed fallback | `test_transcribe_*`, `test_intent_model_unavailable` | Done |
