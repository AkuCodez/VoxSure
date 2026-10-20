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
    <form onSubmit={submit} className="flex items-end gap-3 border-t border-slate-200 bg-white px-4 py-3">
      <button type="button" onClick={onMic} disabled={busy || !micAvailable}
        aria-pressed={recording}
        aria-label={recording ? "Stop recording" : "Start recording"}
        title={micAvailable ? undefined : "Microphone not available. Use the text box."}
        className={`grid h-16 w-16 shrink-0 place-items-center rounded-full text-white shadow-md transition disabled:opacity-40 ${
          recording ? "recording bg-red-600" : "bg-navy-900 hover:bg-navy-700"}`}>
        {recording ? (
          <svg width="26" height="26" viewBox="0 0 24 24" aria-hidden="true"><rect x="6" y="6" width="12" height="12" rx="2" fill="currentColor" /></svg>
        ) : (
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden="true">
            <rect x="9" y="3" width="6" height="11" rx="3" fill="currentColor" /><path d="M5 11a7 7 0 0014 0M12 18v3" />
          </svg>
        )}
      </button>
      <div className="min-w-0 flex-1">
        <p className="mb-1 text-sm text-slate-600" aria-live="polite">
          {recording ? `Recording… ${seconds}s / ${maxSeconds}s. Tap the button to stop.`
            : micAvailable ? "Tap the microphone and ask your question, or type below."
            : "Microphone unavailable here. Please type your question."}
        </p>
        <div className="flex gap-2">
          <label htmlFor="typed" className="sr-only">Type your question</label>
          <input id="typed" value={text} onChange={(e) => setText(e.target.value)} maxLength={300}
            disabled={recording} placeholder="Type a question, e.g. When does the library open?"
            className="min-w-0 flex-1 rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-base" />
          <button type="submit" disabled={!text.trim() || busy || recording}
            className="rounded-lg bg-brand-600 px-4 py-2.5 font-semibold text-white hover:bg-navy-700 disabled:opacity-40">
            Send
          </button>
        </div>
      </div>
    </form>
  );
}
