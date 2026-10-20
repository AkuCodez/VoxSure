import type { MemoryItem } from "../types";

interface Props {
  open: boolean;
  onClose: () => void;
  speakOn: boolean;
  onSpeak: (v: boolean) => void;
  memoryOn: boolean;
  onMemory: (v: boolean) => void;
  memory: MemoryItem[];
  onDelete: (id?: number) => void;
}

export default function SettingsPanel({ open, onClose, speakOn, onSpeak, memoryOn, onMemory, memory, onDelete }: Props) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-20 flex justify-end bg-black/40" onClick={onClose}>
      <aside role="dialog" aria-modal="true" aria-label="Settings and privacy"
        className="h-full w-full max-w-md overflow-y-auto bg-white p-5 shadow-xl" onClick={(e) => e.stopPropagation()}
        onKeyDown={(e) => e.key === "Escape" && onClose()}>
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-navy-900">Settings &amp; privacy</h2>
          <button autoFocus onClick={onClose} className="rounded-md border border-slate-300 px-3 py-1 text-sm">Close</button>
        </div>

        <section className="mt-5">
          <label className="flex items-start gap-3">
            <input type="checkbox" checked={speakOn} onChange={(e) => onSpeak(e.target.checked)} className="mt-1 h-5 w-5" />
            <span><span className="font-medium">Speak answers aloud</span><br />
              <span className="text-sm text-slate-600">Uses your browser's built-in speech. Turn off to mute.</span></span>
          </label>
        </section>

        <section className="mt-5">
          <label className="flex items-start gap-3">
            <input type="checkbox" checked={memoryOn} onChange={(e) => onMemory(e.target.checked)} className="mt-1 h-5 w-5" />
            <span><span className="font-medium">Correction memory (optional)</span><br />
              <span className="text-sm text-slate-600">
                When you edit a transcript you can choose to remember the correction, so the same mishearing is fixed next time.
                Nothing is saved unless you tick "Remember" while editing.
              </span></span>
          </label>
          {memoryOn && (
            <div className="mt-3">
              <h3 className="text-sm font-semibold">Saved corrections</h3>
              {memory.length === 0 ? <p className="mt-1 text-sm text-slate-600">None yet.</p> : (
                <ul className="mt-2 space-y-2">
                  {memory.map((m) => (
                    <li key={m.id} className="flex items-center justify-between gap-2 rounded-md border border-slate-200 p-2 text-sm">
                      <span>"{m.original}" → "{m.corrected}"</span>
                      <button onClick={() => onDelete(m.id)} className="text-red-700 underline" aria-label={`Delete correction ${m.original}`}>Delete</button>
                    </li>
                  ))}
                </ul>
              )}
              {memory.length > 0 && (
                <button onClick={() => onDelete()} className="mt-3 rounded-md border border-red-300 px-3 py-1.5 text-sm text-red-800">Delete all</button>
              )}
            </div>
          )}
        </section>

        <section className="mt-6 rounded-lg bg-brand-50 p-4 text-sm leading-relaxed text-slate-800">
          <h3 className="font-semibold text-navy-900">How your data is handled</h3>
          <ul className="mt-2 list-disc space-y-1 pl-5">
            <li>The microphone starts only when you press the button.</li>
            <li>Recordings are sent to the server for transcription and are <b>not stored</b>.</li>
            <li>Only anonymous metrics are logged (answer/clarify/fallback, timing). Your words are not logged.</li>
            <li>Corrections are saved only with your opt-in and can be deleted here at any time.</li>
          </ul>
        </section>
      </aside>
    </div>
  );
}
