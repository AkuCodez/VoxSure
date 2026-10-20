import { useState } from "react";
import { confidenceWords } from "../lib/speech";
import type { ChatItem } from "../types";

interface Props {
  item: ChatItem;
  memoryOn: boolean;
  disabled: boolean;
  onEdit: (item: ChatItem, text: string, remember: boolean) => void;
  onChoose: (intent: string, label: string) => void;
  onSpeak: (text: string) => void;
}

export default function MessageBubble({ item, memoryOn, disabled, onEdit, onChoose, onSpeak }: Props) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(item.text);
  const [remember, setRemember] = useState(false);

  if (item.role === "user") {
    const doubtful = item.mode === "voice" && item.asrConfidence !== undefined && item.asrConfidence < 0.6;
    return (
      <li className="flex justify-end">
        <div className="max-w-[85%] rounded-2xl rounded-br-sm bg-navy-800 px-4 py-3 text-white shadow-sm">
          <p className="text-xs uppercase tracking-wide text-brand-100/80">
            {item.mode === "voice" ? "You said (transcript)" : "You typed"}
            {item.edited ? " · edited" : ""}
          </p>
          {editing ? (
            <form className="mt-2 space-y-2" onSubmit={(e) => { e.preventDefault(); setEditing(false); onEdit(item, draft, remember); }}>
              <label className="sr-only" htmlFor={`edit-${item.id}`}>Edit transcript</label>
              <input id={`edit-${item.id}`} autoFocus value={draft} maxLength={300} onChange={(e) => setDraft(e.target.value)}
                className="w-full rounded-md border border-white/40 bg-white px-3 py-2 text-base text-slate-900" />
              {memoryOn && (
                <label className="flex items-center gap-2 text-sm text-brand-100">
                  <input type="checkbox" checked={remember} onChange={(e) => setRemember(e.target.checked)} className="h-4 w-4" />
                  Remember this correction for next time
                </label>
              )}
              <div className="flex gap-2">
                <button type="submit" disabled={disabled || !draft.trim()}
                  className="rounded-md bg-white px-3 py-1.5 text-sm font-semibold text-navy-900 disabled:opacity-50">Resend</button>
                <button type="button" onClick={() => { setEditing(false); setDraft(item.text); }}
                  className="rounded-md border border-white/50 px-3 py-1.5 text-sm">Cancel</button>
              </div>
            </form>
          ) : (
            <>
              <p className="mt-1 text-base" data-testid="user-text">{item.text}</p>
              {doubtful && <p className="mt-1 text-sm text-amber-200">I may have misheard this. Please check it.</p>}
              <button type="button" disabled={disabled} onClick={() => { setDraft(item.text); setEditing(true); }}
                className="mt-2 text-sm font-medium underline underline-offset-2 hover:text-brand-100 disabled:opacity-50"
                aria-label={`Edit transcript: ${item.text}`}>
                Edit
              </button>
            </>
          )}
        </div>
      </li>
    );
  }

  const t = item.turn!;
  const tone =
    t.action === "answer" ? "border-emerald-300" : t.action === "clarify" ? "border-amber-300" : "border-slate-300";
  const tag = t.action === "answer" ? "Answer" : t.action === "clarify" ? "I need to check" : "I can't help with that";
  return (
    <li className="flex justify-start">
      <div className={`max-w-[90%] rounded-2xl rounded-bl-sm border-2 bg-white px-4 py-3 shadow-sm ${tone}`}>
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-600">{tag}</p>
        <p className="mt-1 whitespace-pre-line text-base leading-relaxed text-slate-900" data-testid="assistant-text">{item.text}</p>
        {t.memory_applied && <p className="mt-1 text-sm text-brand-600">Used your saved correction.</p>}
        {t.action === "answer" && t.reason !== "user_confirmed" && t.intent !== "greeting" && t.intent !== "thanks_bye" && (
          <p className="mt-2 text-sm text-slate-600">{confidenceWords(t.confidence)} If that isn't right, edit what you asked.</p>
        )}
        {t.action === "clarify" && t.clarify_kind === "disambiguate" && !item.resolved && (
          <div className="mt-3 flex flex-wrap gap-2" role="group" aria-label="Choose what you meant">
            {t.options.map((o) => (
              <button key={o.intent} type="button" disabled={disabled} onClick={() => onChoose(o.intent, o.label)}
                className="rounded-full border border-brand-600 bg-brand-50 px-4 py-2 text-sm font-medium text-navy-900 hover:bg-brand-100 disabled:opacity-50">
                {o.label}
              </button>
            ))}
          </div>
        )}
        <button type="button" onClick={() => onSpeak(item.text)}
          className="mt-2 text-sm font-medium text-brand-600 underline underline-offset-2">Play aloud</button>
      </div>
    </li>
  );
}
