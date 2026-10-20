import { useState } from "react";

interface Props {
  recording: boolean;
  seconds: number;
  maxSeconds: number;
  busy: boolean;
  micAvailable: boolean;
  onMic: () => void;
  onSend: (text: string) => void;
}

export default function Composer({ recording, seconds, maxSeconds, busy, micAvailable, onMic, onSend }: Props) {
  const [text, setText] = useState("");
  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!text.trim() || busy || recording) return;
    onSend(text);
    setText("");
  };
  return (
    <form onSubmit={submit} className="px-4 pb-5 pt-2 sm:px-8">
      <div className="glass mx-auto flex w-full max-w-4xl items-center gap-4 rounded-2xl border border-slate-200 p-3 shadow-xl shadow-navy-900/10">
        <button type="button" onClick={onMic} disabled={busy || !micAvailable}
          aria-pressed={recording}
          aria-label={recording ? "Stop recording" : "Start recording"}
          title={micAvailable ? undefined : "Microphone not available. Use the text box."}
          className={`grid h-16 w-16 shrink-0 place-items-center rounded-full text-white shadow-lg ring-4 ring-white transition hover:scale-105 disabled:opacity-40 disabled:hover:scale-100 ${
            recording ? "recording bg-red-600" : "bg-orb"}`}>
          {recording ? (
            <svg width="24" height="24" viewBox="0 0 24 24" aria-hidden="true"><rect x="6" y="6" width="12" height="12" rx="2" fill="currentColor" /></svg>
          ) : (
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden="true">
              <rect x="9" y="3" width="6" height="11" rx="3" fill="currentColor" /><path d="M5 11a7 7 0 0014 0M12 18v3" />
            </svg>
          )}
        </button>

        <div className="min-w-0 flex-1">
          {recording && (
            <div className="mb-1 flex items-center gap-3">
              <span className="wave" aria-hidden="true"><span /><span /><span /><span /><span /><span /><span /></span>
              <span className="text-sm font-medium text-red-700" aria-live="polite">Recording… {seconds}s / {maxSeconds}s · tap to stop</span>
            </div>
          )}
          {!recording && (
            <p className="mb-1 text-sm text-slate-600" aria-live="polite">
              {micAvailable ? "Tap the microphone and ask your question, or type below." : "Microphone unavailable here. Please type your question."}
            </p>
          )}
          <div className="flex gap-2">
            <label htmlFor="typed" className="sr-only">Type your question</label>
            <input id="typed" value={text} onChange={(e) => setText(e.target.value)} maxLength={300}
              disabled={recording} placeholder="Type a question, e.g. When does the library open?"
              className="min-w-0 flex-1 rounded-xl border border-slate-300 bg-white px-4 py-3 text-base shadow-inner placeholder:text-slate-400" />
            <button type="submit" disabled={!text.trim() || busy || recording}
              className="rounded-xl bg-brand-600 px-5 py-3 font-semibold text-white shadow transition hover:bg-navy-700 disabled:opacity-40">
              Send
            </button>
          </div>
        </div>
      </div>
      <p className="mx-auto mt-2 max-w-4xl text-center text-xs text-slate-500">
        VoxSure asks before guessing. Always check important details with the official office.
      </p>
    </form>
  );
}
