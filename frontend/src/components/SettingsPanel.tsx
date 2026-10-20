import type { MemoryItem } from "../types";

interface Props {
  open: boolean;
  onClose: () => void;
  speakOn: boolean;
  onSpeak: (v: boolean) => void;
  memoryOn: boolean;
  onMemory: (v: boolean) => void;
  memory: MemoryItem[];
  generalOn?: boolean;
  onGeneral?: (v: boolean) => void;
  onDelete: (id?: number) => void;
}

function Toggle({ checked, onChange, label, hint }: { checked: boolean; onChange: (v: boolean) => void; label: string; hint: string }) {
  return (
    <label className="flex cursor-pointer items-start gap-4">
      <span className="relative mt-0.5 inline-flex h-6 w-11 shrink-0">
        <input type="checkbox" checked={checked} onChange={(e) => onChange(e.target.checked)} className="peer sr-only" />
        <span className="absolute inset-0 rounded-full bg-slate-600 transition peer-checked:bg-blue-500 peer-focus-visible:outline peer-focus-visible:outline-3 peer-focus-visible:outline-amber-400" />
        <span className="absolute left-0.5 top-0.5 h-5 w-5 rounded-full bg-white shadow transition peer-checked:translate-x-5" />
      </span>
      <span><span className="font-medium text-slate-100">{label}</span><br /><span className="text-sm text-slate-400">{hint}</span></span>
    </label>
  );
}

export default function SettingsPanel({ open, onClose, speakOn, onSpeak, memoryOn, onMemory, memory, generalOn = true, onGeneral = () => {}, onDelete }: Props) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-30 flex justify-end bg-black/60 backdrop-blur-sm" onClick={onClose}>
      <div role="dialog" aria-modal="true" aria-label="Settings and privacy"
        className="panel-solid h-full w-full max-w-md overflow-y-auto p-6 shadow-2xl" onClick={(e) => e.stopPropagation()}
        onKeyDown={(e) => e.key === "Escape" && onClose()}>
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-white">Settings &amp; privacy</h2>
          <button autoFocus onClick={onClose} className="rounded-lg border border-white/15 px-3 py-1.5 text-sm text-slate-200 hover:bg-white/5">Close</button>
        </div>

        <section className="mt-6">
          <Toggle checked={speakOn} onChange={onSpeak} label="Speak answers aloud" hint="Uses your browser's built-in speech. Turn off to mute." />
        </section>

        <section className="mt-6">
          <Toggle checked={generalOn} onChange={onGeneral} label="Answer non-campus questions with AI"
            hint="Questions that are not about campus topics are sent to an external general AI model so I can answer almost anything. Those replies are labelled AI-generated and may be wrong. Turn off to keep every question on this server." />
        </section>

        <section className="mt-6">
          <Toggle checked={memoryOn} onChange={onMemory} label="Correction memory (optional)"
            hint='When you edit a transcript you can choose to remember the correction. Nothing is saved unless you tick "Remember" while editing.' />
          {memoryOn && (
            <div className="mt-4 rounded-xl border border-white/10 bg-white/[0.03] p-3">
              <h3 className="text-sm font-semibold text-slate-200">Saved corrections</h3>
              {memory.length === 0 ? <p className="mt-1 text-sm text-slate-400">None yet.</p> : (
                <ul className="mt-2 space-y-2">
                  {memory.map((m) => (
                    <li key={m.id} className="flex items-center justify-between gap-2 rounded-lg bg-white/[0.04] p-2 text-sm text-slate-200">
                      <span>"{m.original}" → "{m.corrected}"</span>
                      <button onClick={() => onDelete(m.id)} className="text-rose-300 underline" aria-label={`Delete correction ${m.original}`}>Delete</button>
                    </li>
                  ))}
                </ul>
              )}
              {memory.length > 0 && (
                <button onClick={() => onDelete()} className="mt-3 rounded-lg border border-rose-400/40 px-3 py-1.5 text-sm text-rose-300 hover:bg-rose-500/10">Delete all</button>
              )}
            </div>
          )}
        </section>

        <section className="mt-8 rounded-xl border border-blue-400/20 bg-blue-500/[0.06] p-4 text-sm leading-relaxed text-slate-300">
          <h3 className="font-semibold text-white">How your data is handled</h3>
          <ul className="mt-2 list-disc space-y-1 pl-5">
            <li>The microphone starts only when you press the button.</li>
            <li>Recordings are sent to the server for transcription and are <b className="text-white">not stored</b>.</li>
            <li>Only anonymous metrics are logged (answer/clarify/fallback, timing). Your words are not logged.</li>
            <li>Corrections are saved only with your opt-in and can be deleted here at any time.</li>
            <li>If AI answers are on, the text of a non-campus question and your last few messages are sent to the configured external AI provider (for example Anthropic, Groq or Google) to write the reply. Nothing else is sent: no audio, no identifiers.</li>
          </ul>
        </section>
      </div>
    </div>
  );
}
