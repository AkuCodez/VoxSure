import { useState } from "react";
import { MicIcon, SendIcon, StopIcon } from "./Icons";

interface Props {
  recording: boolean;
  seconds: number;
  maxSeconds: number;
  busy: boolean;
  micAvailable: boolean;
  levels?: number[];
  onMic: () => void;
  onSend: (text: string) => void;
}

function Waveform({ levels }: { levels: number[] }) {
  return (
    <div className="flex h-9 flex-1 items-center gap-[3px]" aria-hidden="true">
      {levels.map((l, i) => (
        <span key={i} className="w-[3px] rounded-full bg-gradient-to-t from-red-500 to-orange-300 transition-[height] duration-75"
          style={{ height: `${Math.max(8, Math.round(l * 100))}%`, opacity: 0.45 + l * 0.55 }} />
      ))}
    </div>
  );
}

export default function Composer({ recording, seconds, maxSeconds, busy, micAvailable, levels = [], onMic, onSend }: Props) {
  const [text, setText] = useState("");
  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!text.trim() || busy || recording) return;
    onSend(text);
    setText("");
  };
  return (
    <form onSubmit={submit} className="px-4 pb-5 pt-1 sm:px-8">
      <div className="panel mx-auto flex w-full max-w-3xl items-center gap-4 rounded-3xl p-3 shadow-2xl shadow-black/40">
        <button type="button" onClick={onMic} disabled={busy || !micAvailable}
          aria-pressed={recording}
          aria-label={recording ? "Stop recording" : "Start recording"}
          title={micAvailable ? undefined : "Microphone not available. Use the text box."}
          className={`grid h-16 w-16 shrink-0 place-items-center rounded-full text-white transition hover:scale-105 disabled:opacity-40 disabled:hover:scale-100 ${
            recording ? "recording bg-red-500 ring-4 ring-red-500/25" : "orb orb-glow"}`}>
          {recording ? <StopIcon size={26} /> : <MicIcon size={28} />}
        </button>

        <div className="min-w-0 flex-1">
          {recording ? (
            <div className="flex items-center gap-4 py-1.5">
              <Waveform levels={levels} />
              <span className="shrink-0 font-mono text-sm tabular-nums text-red-300" aria-live="polite">
                Recording… {seconds}s / {maxSeconds}s
              </span>
              <span className="hidden shrink-0 text-xs text-slate-400 sm:inline">tap to stop</span>
            </div>
          ) : (
            <>
              <p className="mb-1.5 text-xs text-slate-400" aria-live="polite">
                {micAvailable ? "Tap the microphone and ask your question, or type below." : "Microphone unavailable here. Please type your question."}
              </p>
              <div className="flex gap-2">
                <label htmlFor="typed" className="sr-only">Type your question</label>
                <input id="typed" value={text} onChange={(e) => setText(e.target.value)} maxLength={300}
                  placeholder="Type a question, e.g. When does the library open?"
                  className="min-w-0 flex-1 rounded-xl border border-white/10 bg-ink-950/70 px-4 py-3 text-base text-slate-100 placeholder:text-slate-500 focus:border-blue-400/60" />
                <button type="submit" disabled={!text.trim() || busy}
                  className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-br from-blue-500 to-blue-700 px-5 py-3 font-semibold text-white shadow-lg shadow-blue-900/40 transition hover:brightness-110 disabled:opacity-35">
                  <span>Send</span><SendIcon size={16} />
                </button>
              </div>
            </>
          )}
        </div>
      </div>
      <p className="mx-auto mt-2 max-w-3xl text-center text-xs text-slate-500">
        VoxSure asks before guessing. Always confirm important details with the official office.
      </p>
    </form>
  );
}
