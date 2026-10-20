import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../lib/api";
import { speak, stopSpeaking } from "../lib/speech";
import { ApiError, type ChatItem, type Insight, type MemoryItem, type Status, type TurnResponse } from "../types";

const uid = () => Math.random().toString(36).slice(2, 10);

function safeGet(key: string): string | null {
  try { return localStorage.getItem(key); } catch { return null; }
}
function safeSet(key: string, value: string) {
  try { localStorage.setItem(key, value); } catch { /* storage unavailable */ }
}

function clientId(): string {
  let id = safeGet("voxsure.client");
  if (!id) {
    id = (crypto.randomUUID?.() ?? uid() + uid() + uid()).replace(/[^A-Za-z0-9_-]/g, "");
    safeSet("voxsure.client", id);
  }
  return id;
}

export function useChat() {
  const [items, setItems] = useState<ChatItem[]>([]);
  const [status, setStatus] = useState<Status>("ready");
  const [error, setError] = useState<string | null>(null);
  const [speakOn, setSpeakOn] = useState(() => safeGet("voxsure.speak") !== "0");
  const [speaking, setSpeaking] = useState(false);
  const [memoryOn, setMemoryOn] = useState(() => safeGet("voxsure.memory") === "1");
  const [memory, setMemory] = useState<MemoryItem[]>([]);
  const [insight, setInsight] = useState<Insight | null>(null);
  const [counts, setCounts] = useState({ answer: 0, clarify: 0, fallback: 0 });
  const attempts = useRef(0);
  const cid = useRef(clientId());
  const busy = status === "uploading" || status === "transcribing" || status === "understanding";

  const refreshMemory = useCallback(async () => {
    try { setMemory(await api.listMemory(cid.current)); } catch { /* non-critical */ }
  }, []);
  useEffect(() => { if (memoryOn) void refreshMemory(); }, [memoryOn, refreshMemory]);

  const toggleSpeak = (v: boolean) => { setSpeakOn(v); safeSet("voxsure.speak", v ? "1" : "0"); if (!v) { stopSpeaking(); setSpeaking(false); } };
  const toggleMemory = (v: boolean) => { setMemoryOn(v); safeSet("voxsure.memory", v ? "1" : "0"); };

  const say = useCallback((text: string) => {
    setSpeaking(true);
    speak(text, () => setSpeaking(false));
  }, []);

  const stopAudio = useCallback(() => { stopSpeaking(); setSpeaking(false); }, []);

  const runTurn = useCallback(async (
    text: string, mode: "voice" | "text",
    opts: { asr?: number; asrMs?: number; durationS?: number; chosen?: string; edited?: boolean } = {},
  ): Promise<TurnResponse | null> => {
    stopAudio();
    setError(null);
    setStatus("understanding");
    try {
      const turn = await api.turn({
        text, input_mode: mode, asr_confidence: opts.asr, chosen_intent: opts.chosen,
        attempts: attempts.current, edited: !!opts.edited, client_id: cid.current, use_memory: memoryOn,
      });
      attempts.current = turn.action === "answer" ? 0 : attempts.current + 1;
      setInsight({ mode, asrConfidence: opts.asr, asrMs: opts.asrMs, durationS: opts.durationS, turn });
      setCounts((c) => ({ ...c, [turn.action]: c[turn.action] + 1 }));
      setItems((prev) => {
        const next = prev.map((i) => (i.turn?.action === "clarify" && !i.resolved ? { ...i, resolved: true } : i));
        // reflect memory substitution in the visible user bubble
        if (turn.memory_applied) {
          for (let k = next.length - 1; k >= 0; k--)
            if (next[k].role === "user") { next[k] = { ...next[k], text: turn.transcript }; break; }
        }
        return [...next, { id: uid(), role: "assistant", text: turn.response, turn }];
      });
      setStatus(turn.action === "clarify" ? "clarifying" : "answered");
      if (speakOn) say(turn.response);
      return turn;
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Something went wrong. Please try again.");
      setStatus("error");
      return null;
    }
  }, [memoryOn, say, speakOn, stopAudio]);

  const sendText = useCallback(async (text: string) => {
    const t = text.trim();
    if (!t) return;
    setItems((p) => [...p, { id: uid(), role: "user", text: t, mode: "text" }]);
    await runTurn(t, "text");
  }, [runTurn]);

  const sendAudio = useCallback(async (blob: Blob) => {
    stopAudio();
    setError(null);
    setStatus("uploading");
    if (blob.size === 0) { setError("No audio was captured. Please try again."); setStatus("error"); return; }
    try {
      setStatus("transcribing");
      const r = await api.transcribe(blob);
      setItems((p) => [...p, { id: uid(), role: "user", text: r.transcript, mode: "voice", asrConfidence: r.asr_confidence,
        asrMs: r.latency_ms, durationS: r.duration_s }]);
      await runTurn(r.transcript, "voice", { asr: r.asr_confidence, asrMs: r.latency_ms, durationS: r.duration_s });
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Something went wrong. Please try again.");
      setStatus("error");
    }
  }, [runTurn, stopAudio]);

  /** User corrected a transcript: resubmit and optionally remember the correction (opt-in). */
  const editAndResend = useCallback(async (item: ChatItem, corrected: string, remember: boolean) => {
    const c = corrected.trim();
    if (!c) return;
    setItems((p) => p.map((i) => (i.id === item.id ? { ...i, text: c, edited: true } : i)));
    if (remember && memoryOn && c.toLowerCase() !== item.text.trim().toLowerCase()) {
      try { await api.feedback({ client_id: cid.current, original_text: item.text, corrected_text: c, remember: true }); await refreshMemory(); }
      catch { /* storing a preference is best-effort */ }
    }
    attempts.current = 0;
    await runTurn(c, item.mode ?? "text", { edited: true, asr: undefined });
  }, [memoryOn, refreshMemory, runTurn]);

  const choose = useCallback(async (intent: string, label: string) => {
    setItems((p) => [...p, { id: uid(), role: "user", text: label, mode: "text" }]);
    await runTurn(label, "text", { chosen: intent });
  }, [runTurn]);

  const reset = useCallback(() => {
    stopAudio(); setItems([]); setError(null); setStatus("ready"); attempts.current = 0;
    setInsight(null); setCounts({ answer: 0, clarify: 0, fallback: 0 });
  }, [stopAudio]);

  const deleteMemory = useCallback(async (id?: number) => {
    try { await api.deleteMemory(cid.current, id); await refreshMemory(); }
    catch (e) { setError(e instanceof ApiError ? e.message : "Could not delete."); }
  }, [refreshMemory]);

  return {
    items, insight, counts, status, setStatus, error, setError, busy, speakOn, toggleSpeak, speaking, say, stopAudio,
    memoryOn, toggleMemory, memory, deleteMemory, sendText, sendAudio, editAndResend, choose, reset,
  };
}
