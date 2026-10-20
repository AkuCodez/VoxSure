import { useCallback, useEffect, useRef, useState } from "react";

const MAX_SECONDS = 20;
const BARS = 48;
const PERMISSION_TIMEOUT_MS = 12_000;
const STOP_FALLBACK_MS = 1_500;
const SPEECH_LEVEL = 0.12;     // loudness that counts as speech
const SILENCE_STOP_MS = 1_800; // stop automatically this long after speech ends

function pickMime(): string | undefined {
  const cands = ["audio/webm;codecs=opus", "audio/webm", "audio/mp4", "audio/ogg;codecs=opus"];
  return cands.find((m) => typeof MediaRecorder !== "undefined" && MediaRecorder.isTypeSupported(m));
}

export function recorderSupport(): { ok: boolean; reason?: string } {
  if (typeof window === "undefined") return { ok: false, reason: "No browser." };
  if (!window.isSecureContext)
    return { ok: false, reason: "Microphone access needs a secure (HTTPS) connection. You can type instead." };
  if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === "undefined")
    return { ok: false, reason: "This browser can't record audio. Try a recent Chrome, Edge, Firefox or Safari, or type instead." };
  return { ok: true };
}

export interface RecorderError { code: "denied" | "no_device" | "unsupported" | "failed"; message: string }

/**
 * Microphone capture with explicit states: idle -> starting (waiting for permission) -> recording.
 * - `starting` can be cancelled and times out, so the UI can never get stuck waiting.
 * - stop() always finishes (falls back if MediaRecorder never fires `onstop`).
 * - Recording stops by itself ~1.8 s after you stop speaking, or after 20 s.
 * `levels` is a rolling window of real input loudness (0..1) used to draw the waveform.
 */
export function useRecorder(onFinished: (blob: Blob) => void, onError: (e: RecorderError) => void) {
  const [recording, setRecording] = useState(false);
  const [starting, setStarting] = useState(false);
  const [seconds, setSeconds] = useState(0);
  const [levels, setLevels] = useState<number[]>(() => new Array(BARS).fill(0));

  const rec = useRef<MediaRecorder | null>(null);
  const stream = useRef<MediaStream | null>(null);
  const chunks = useRef<Blob[]>([]);
  const mime = useRef<string>("audio/webm");
  const timer = useRef<number | undefined>(undefined);
  const permTimer = useRef<number | undefined>(undefined);
  const stopTimer = useRef<number | undefined>(undefined);
  const meterTimer = useRef<number | undefined>(undefined);
  const audioCtx = useRef<AudioContext | null>(null);
  const phase = useRef<"idle" | "starting" | "recording">("idle");
  const cancelled = useRef(false);
  const delivered = useRef(false);
  const cbs = useRef({ onFinished, onError });
  cbs.current = { onFinished, onError };

  const stopMeter = useCallback(() => {
    window.clearInterval(meterTimer.current);
    meterTimer.current = undefined;
    void audioCtx.current?.close().catch(() => undefined);
    audioCtx.current = null;
    setLevels(new Array(BARS).fill(0));
  }, []);

  const release = useCallback(() => {
    window.clearInterval(timer.current);
    window.clearTimeout(permTimer.current);
    window.clearTimeout(stopTimer.current);
    stopMeter();
    stream.current?.getTracks().forEach((t) => t.stop());
    stream.current = null;
    rec.current = null;
    phase.current = "idle";
    setRecording(false);
    setStarting(false);
    setSeconds(0);
  }, [stopMeter]);

  /** Deliver the captured audio exactly once, then free the microphone. */
  const finish = useCallback(() => {
    if (delivered.current) return;
    delivered.current = true;
    const blob = new Blob(chunks.current, { type: mime.current });
    release();
    cbs.current.onFinished(blob);
  }, [release]);

  const stop = useCallback(() => {
    const mr = rec.current;
    if (phase.current === "starting") {  // still waiting for permission: abort cleanly
      cancelled.current = true;
      release();
      return;
    }
    if (!mr) return;
    if (mr.state !== "inactive") {
      try { mr.stop(); } catch { /* fall through to the fallback */ }
    }
    // Some browsers occasionally never fire `onstop`; never leave the user stuck.
    window.clearTimeout(stopTimer.current);
    stopTimer.current = window.setTimeout(finish, STOP_FALLBACK_MS);
  }, [finish, release]);

  const startMeter = useCallback((s: MediaStream) => {
    try {
      const Ctx = window.AudioContext ?? (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
      const ctx = new Ctx();
      void ctx.resume().catch(() => undefined);
      const analyser = ctx.createAnalyser();
      analyser.fftSize = 512;
      ctx.createMediaStreamSource(s).connect(analyser);
      audioCtx.current = ctx;
      const buf = new Uint8Array(analyser.fftSize);
      let heardSpeech = false;
      let silentSince = 0;
      const tick = () => {
        const t = performance.now();
        analyser.getByteTimeDomainData(buf);
        let sum = 0;
        for (const v of buf) { const d = (v - 128) / 128; sum += d * d; }
        const level = Math.min(1, Math.sqrt(sum / buf.length) * 5);
        setLevels((prev) => [...prev.slice(1), level]);
        if (level > SPEECH_LEVEL) { heardSpeech = true; silentSince = 0; }
        else if (heardSpeech) {
          if (!silentSince) silentSince = t;
          else if (t - silentSince > SILENCE_STOP_MS) { heardSpeech = false; stop(); }
        }
      };
      meterTimer.current = window.setInterval(tick, 50);
    } catch { /* the meter is cosmetic; recording still works */ }
  }, [stop]);

  const start = useCallback(async () => {
    if (phase.current !== "idle") return;           // ignore double clicks
    const sup = recorderSupport();
    if (!sup.ok) return cbs.current.onError({ code: "unsupported", message: sup.reason! });
    phase.current = "starting";
    cancelled.current = false;
    delivered.current = false;
    setStarting(true);
    permTimer.current = window.setTimeout(() => {
      if (phase.current !== "starting") return;
      cancelled.current = true;
      release();
      cbs.current.onError({ code: "failed", message: "I'm still waiting for microphone permission. Click Allow in your browser's prompt (near the address bar), then press the mic again, or type your question." });
    }, PERMISSION_TIMEOUT_MS);
    try {
      const s = await navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: true, noiseSuppression: true } });
      if (cancelled.current) { s.getTracks().forEach((t) => t.stop()); return; }
      window.clearTimeout(permTimer.current);
      const m = pickMime();
      mime.current = m ?? "audio/webm";
      const mr = new MediaRecorder(s, m ? { mimeType: m } : undefined);
      stream.current = s;
      chunks.current = [];
      mr.ondataavailable = (e) => { if (e.data.size) chunks.current.push(e.data); };
      mr.onstop = () => { mime.current = mr.mimeType || mime.current; finish(); };
      mr.onerror = () => finish();
      mr.start(250);
      rec.current = mr;
      phase.current = "recording";
      setStarting(false);
      setRecording(true);
      startMeter(s);
      let sec = 0;
      timer.current = window.setInterval(() => {
        sec += 1; setSeconds(sec);
        if (sec >= MAX_SECONDS) stop();
      }, 1000);
    } catch (e) {
      if (cancelled.current) return;
      release();
      const name = (e as DOMException).name;
      if (name === "NotAllowedError" || name === "SecurityError")
        cbs.current.onError({ code: "denied", message: "Microphone access is blocked. Allow the microphone for this site in your browser's address bar settings, then try again, or type your question." });
      else if (name === "NotFoundError" || name === "OverconstrainedError")
        cbs.current.onError({ code: "no_device", message: "No microphone was found. Connect one, or type your question." });
      else cbs.current.onError({ code: "failed", message: "I couldn't start the microphone. Please try again or type your question." });
    }
  }, [finish, release, startMeter, stop]);

  useEffect(() => () => { cancelled.current = true; release(); }, [release]);

  return { recording, starting, seconds, levels, start, stop, maxSeconds: MAX_SECONDS };
}
