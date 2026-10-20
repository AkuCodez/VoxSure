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

function Avatar() {
  return (
    <div className="bg-orb mt-1 grid h-9 w-9 shrink-0 place-items-center rounded-full text-sm font-bold text-white shadow ring-2 ring-white" aria-hidden="true">V</div>
  );
}

export default function MessageBubble({ item, memoryOn, disabled, onEdit, onChoose, onSpeak }: Props) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(item.text);
  const [remember, setRemember] = useState(false);

  if (item.role === "user") {
    const doubtful = item.mode === "voice" && item.asrConfidence !== undefined && item.asrConfidence < 0.6;
    return (
      <li className="fade-up flex justify-end">
        <div className="max-w-[88%] rounded-2xl rounded-br-md bg-gradient-to-br from-navy-700 to-navy-900 px-5 py-3.5 text-white shadow-md sm:max-w-[75%]">
          <p className="flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wider text-brand-100/80">
            <span aria-hidden="true">{item.mode === "voice" ? "🎙️" : "⌨️"}</span>
            <span>{item.mode === "voice" ? "You said (transcript)" : "You typed"}</span>
            {item.edited ? <span>· edited</span> : null}
          </p>
          {editing ? (
            <form className="mt-2 space-y-2" onSubmit={(e) => { e.preventDefault(); setEditing(false); onEdit(item, draft, remember); }}>
              <label className="sr-only" htmlFor={`edit-${item.id}`}>Edit transcript</label>
              <input id={`edit-${item.id}`} autoFocus value={draft} maxLength={300} onChange={(e) => setDraft(e.target.value)}
                className="w-full rounded-lg border border-white/40 bg-white px-3 py-2 text-base text-slate-900" />
              {memoryOn && (
                <label className="flex items-center gap-2 text-sm text-brand-100">
                  <input type="checkbox" checked={remember} onChange={(e) => setRemember(e.target.checked)} className="h-4 w-4" />
                  Remember this correction for next time
                </label>
              )}
              <div className="flex gap-2">
                <button type="submit" disabled={disabled || !draft.trim()}
                  className="rounded-lg bg-white px-3.5 py-1.5 text-sm font-semibold text-navy-900 disabled:opacity-50">Resend</button>
                <button type="button" onClick={() => { setEditing(false); setDraft(item.text); }}
                  className="rounded-lg border border-white/50 px-3.5 py-1.5 text-sm">Cancel</button>
              </div>
            </form>
          ) : (
            <>
              <p className="mt-1 text-[17px] leading-snug" data-testid="user-text">{item.text}</p>
              {doubtful && <p className="mt-1.5 rounded-md bg-amber-300/20 px-2 py-1 text-sm text-amber-100">I may have misheard this. Please check it.</p>}
              <button type="button" disabled={disabled} onClick={() => { setDraft(item.text); setEditing(true); }}
                className="mt-2 text-sm font-medium text-brand-100 underline underline-offset-2 hover:text-white disabled:opacity-50"
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
  const accent = t.action === "answer" ? "border-l-emerald-500" : t.action === "clarify" ? "border-l-amber-400" : "border-l-slate-400";
  const tagCls = t.action === "answer" ? "bg-emerald-50 text-emerald-800" : t.action === "clarify" ? "bg-amber-50 text-amber-900" : "bg-slate-100 text-slate-700";
  const tagIcon = t.action === "answer" ? "✓" : t.action === "clarify" ? "?" : "○";
  const tag = t.action === "answer" ? "Answer" : t.action === "clarify" ? "I need to check" : "I can't help with that";
  return (
    <li className="fade-up flex items-start gap-3">
      <Avatar />
      <div className={`max-w-[90%] rounded-2xl rounded-tl-md border border-l-4 border-slate-200 bg-white px-5 py-4 shadow-md sm:max-w-[78%] ${accent}`}>
        <p className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[11px] font-semibold uppercase tracking-wider ${tagCls}`}>
          <span aria-hidden="true">{tagIcon}</span>{tag}
        </p>
        <p className="mt-2 whitespace-pre-line text-[17px] leading-relaxed text-slate-900" data-testid="assistant-text">{item.text}</p>
        {t.memory_applied && <p className="mt-1.5 text-sm text-brand-600">Used your saved correction.</p>}
        {t.action === "answer" && t.reason !== "user_confirmed" && t.intent !== "greeting" && t.intent !== "thanks_bye" && (
          <p className="mt-2 text-sm text-slate-600">{confidenceWords(t.confidence)} If that isn't right, edit what you asked.</p>
        )}
        {t.action === "clarify" && t.clarify_kind === "disambiguate" && !item.resolved && (
          <div className="mt-3 flex flex-wrap gap-2" role="group" aria-label="Choose what you meant">
            {t.options.map((o) => (
              <button key={o.intent} type="button" disabled={disabled} onClick={() => onChoose(o.intent, o.label)}
                className="rounded-full border-2 border-brand-600 bg-brand-50 px-4 py-2 text-sm font-semibold text-navy-900 transition hover:bg-brand-600 hover:text-white disabled:opacity-50">
                {o.label}
              </button>
            ))}
          </div>
        )}
        <button type="button" onClick={() => onSpeak(item.text)}
          className="mt-3 inline-flex items-center gap-1.5 text-sm font-medium text-brand-600 underline underline-offset-2">
          <span aria-hidden="true">🔊</span>Play aloud
        </button>
      </div>
    </li>
  );
}
