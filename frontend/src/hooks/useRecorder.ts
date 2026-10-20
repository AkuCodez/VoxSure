import { useCallback, useEffect, useRef, useState } from "react";

const MAX_SECONDS = 20;
const BARS = 48;

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
 * Start/stop microphone capture. Permission is requested only when start() is called.
 * `levels` is a rolling window of real input loudness (0..1) from a Web Audio analyser,
 * used to draw the live waveform.
 */
export function useRecorder(onFinished: (blob: Blob) => void, onError: (e: RecorderError) => void) {
  const [recording, setRecording] = useState(false);
  const [seconds, setSeconds] = useState(0);
  const [levels, setLevels] = useState<number[]>(() => new Array(BARS).fill(0));
  const rec = useRef<MediaRecorder | null>(null);
  const chunks = useRef<Blob[]>([]);
  const timer = useRef<number | undefined>(undefined);
  const raf = useRef<number | undefined>(undefined);
  const audioCtx = useRef<AudioContext | null>(null);
  const cbs = useRef({ onFinished, onError });
  cbs.current = { onFinished, onError };

  const stopMeter = useCallback(() => {
    if (raf.current !== undefined) cancelAnimationFrame(raf.current);
    raf.current = undefined;
    void audioCtx.current?.close().catch(() => undefined);
    audioCtx.current = null;
    setLevels(new Array(BARS).fill(0));
  }, []);

  const cleanup = useCallback(() => {
    window.clearInterval(timer.current);
    stopMeter();
    rec.current?.stream.getTracks().forEach((t) => t.stop());
    rec.current = null;
    setRecording(false);
    setSeconds(0);
  }, [stopMeter]);

  const stop = useCallback(() => {
    if (rec.current && rec.current.state !== "inactive") rec.current.stop();
  }, []);

  const startMeter = useCallback((stream: MediaStream) => {
    try {
      const Ctx = window.AudioContext ?? (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
      const ctx = new Ctx();
      const analyser = ctx.createAnalyser();
      analyser.fftSize = 512;
      ctx.createMediaStreamSource(stream).connect(analyser);
      audioCtx.current = ctx;
      const buf = new Uint8Array(analyser.fftSize);
      let last = 0;
      const tick = (t: number) => {
        raf.current = requestAnimationFrame(tick);
        if (t - last < 40) return;
        last = t;
        analyser.getByteTimeDomainData(buf);
        let sum = 0;
        for (const v of buf) { const d = (v - 128) / 128; sum += d * d; }
        const level = Math.min(1, Math.sqrt(sum / buf.length) * 5);
        setLevels((prev) => [...prev.slice(1), level]);
      };
      raf.current = requestAnimationFrame(tick);
    } catch { /* meter is cosmetic; recording still works */ }
  }, []);

  const start = useCallback(async () => {
    const sup = recorderSupport();
    if (!sup.ok) return cbs.current.onError({ code: "unsupported", message: sup.reason! });
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: true, noiseSuppression: true } });
      const mime = pickMime();
      const mr = new MediaRecorder(stream, mime ? { mimeType: mime } : undefined);
      chunks.current = [];
      mr.ondataavailable = (e) => { if (e.data.size) chunks.current.push(e.data); };
      mr.onstop = () => {
        const blob = new Blob(chunks.current, { type: mr.mimeType || mime || "audio/webm" });
        cleanup();
        cbs.current.onFinished(blob);
      };
      mr.start();
      rec.current = mr;
      setRecording(true);
      startMeter(stream);
      let s = 0;
      timer.current = window.setInterval(() => {
        s += 1; setSeconds(s);
        if (s >= MAX_SECONDS) stop();
      }, 1000);
    } catch (e) {
      const name = (e as DOMException).name;
      if (name === "NotAllowedError" || name === "SecurityError")
        cbs.current.onError({ code: "denied", message: "Microphone access is blocked. Allow the microphone for this site in your browser's address bar settings, then try again, or type your question." });
      else if (name === "NotFoundError" || name === "OverconstrainedError")
        cbs.current.onError({ code: "no_device", message: "No microphone was found. Connect one, or type your question." });
      else cbs.current.onError({ code: "failed", message: "I couldn't start the microphone. Please try again or type your question." });
    }
  }, [cleanup, startMeter, stop]);

  useEffect(() => () => {
    window.clearInterval(timer.current);
    stopMeter();
    rec.current?.stream.getTracks().forEach((t) => t.stop());
  }, [stopMeter]);

  return { recording, seconds, levels, start, stop, maxSeconds: MAX_SECONDS };
}
