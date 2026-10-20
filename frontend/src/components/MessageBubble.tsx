import { useState } from "react";
import { confidenceWords } from "../lib/speech";
import type { ChatItem } from "../types";
import { CheckIcon, EditIcon, HelpIcon, MicIcon, SlashIcon, VolumeIcon } from "./Icons";

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
    <div className="orb mt-0.5 grid h-9 w-9 shrink-0 place-items-center rounded-full text-white shadow-lg ring-1 ring-white/20" aria-hidden="true">
      <MicIcon size={16} />
    </div>
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
        <div className="max-w-[88%] rounded-2xl rounded-br-md bg-gradient-to-br from-[#2f6be0] to-[#1d3f94] px-5 py-3.5 text-white shadow-lg shadow-blue-950/40 ring-1 ring-white/10 sm:max-w-[72%]">
          <p className="flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-[0.12em] text-blue-100/80">
            <span aria-hidden="true">{item.mode === "voice" ? <MicIcon size={12} /> : <EditIcon size={12} />}</span>
            <span>{item.mode === "voice" ? "You said (transcript)" : "You typed"}</span>
            {item.edited ? <span>· edited</span> : null}
          </p>
          {editing ? (
            <form className="mt-2 space-y-2" onSubmit={(e) => { e.preventDefault(); setEditing(false); onEdit(item, draft, remember); }}>
              <label className="sr-only" htmlFor={`edit-${item.id}`}>Edit transcript</label>
              <input id={`edit-${item.id}`} autoFocus value={draft} maxLength={300} onChange={(e) => setDraft(e.target.value)}
                className="w-full rounded-lg border border-white/30 bg-ink-950/70 px-3 py-2 text-base text-white placeholder:text-slate-400" />
              {memoryOn && (
                <label className="flex items-center gap-2 text-sm text-blue-100">
                  <input type="checkbox" checked={remember} onChange={(e) => setRemember(e.target.checked)} className="h-4 w-4" />
                  Remember this correction for next time
                </label>
              )}
              <div className="flex gap-2">
                <button type="submit" disabled={disabled || !draft.trim()}
                  className="rounded-lg bg-white px-3.5 py-1.5 text-sm font-semibold text-blue-900 disabled:opacity-50">Resend</button>
                <button type="button" onClick={() => { setEditing(false); setDraft(item.text); }}
                  className="rounded-lg border border-white/40 px-3.5 py-1.5 text-sm">Cancel</button>
              </div>
            </form>
          ) : (
            <>
              <p className="mt-1 text-[17px] leading-snug" data-testid="user-text">{item.text}</p>
              {doubtful && <p className="mt-1.5 rounded-md bg-amber-300/20 px-2 py-1 text-sm text-amber-100">I may have misheard this. Please check it.</p>}
              <button type="button" disabled={disabled} onClick={() => { setDraft(item.text); setEditing(true); }}
                className="mt-2 inline-flex items-center gap-1 text-sm font-medium text-blue-100 underline underline-offset-2 hover:text-white disabled:opacity-50"
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
  const accent = t.action === "answer" ? "before:bg-emerald-400" : t.action === "clarify" ? "before:bg-amber-400" : "before:bg-slate-400";
  const tagCls = t.action === "answer" ? "bg-emerald-400/10 text-emerald-300 ring-emerald-400/30" : t.action === "clarify" ? "bg-amber-400/10 text-amber-300 ring-amber-400/30" : "bg-slate-400/10 text-slate-300 ring-slate-400/30";
  const TagIcon = t.action === "answer" ? CheckIcon : t.action === "clarify" ? HelpIcon : SlashIcon;
  const tag = t.action === "answer" ? "Answer" : t.action === "clarify" ? "I need to check" : "I can't help with that";
  return (
    <li className="fade-up flex items-start gap-3">
      <Avatar />
      <div className={`panel relative max-w-[92%] overflow-hidden rounded-2xl rounded-tl-md py-4 pl-6 pr-5 shadow-xl shadow-black/30 before:absolute before:inset-y-0 before:left-0 before:w-1 sm:max-w-[78%] ${accent}`}>
        <p className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[11px] font-semibold uppercase tracking-[0.12em] ring-1 ${tagCls}`}>
          <TagIcon size={12} />{tag}
        </p>
        <p className="mt-2.5 whitespace-pre-line text-[17px] leading-relaxed text-slate-100" data-testid="assistant-text">{item.text}</p>
        {t.memory_applied && <p className="mt-1.5 text-sm text-cyan-300">Used your saved correction.</p>}
        {t.action === "answer" && t.reason !== "user_confirmed" && !["greeting", "thanks_bye", "about_bot", "help_capabilities"].includes(t.intent ?? "") && (
          <p className="mt-2 text-sm text-slate-400">{confidenceWords(t.confidence)} If that isn't right, edit what you asked.</p>
        )}
        {t.action === "clarify" && t.clarify_kind === "disambiguate" && !item.resolved && (
          <div className="mt-3.5 flex flex-wrap gap-2" role="group" aria-label="Choose what you meant">
            {t.options.map((o) => (
              <button key={o.intent} type="button" disabled={disabled} onClick={() => onChoose(o.intent, o.label)}
                className="rounded-full border border-blue-400/50 bg-blue-500/10 px-4 py-2 text-sm font-semibold text-blue-100 transition hover:bg-blue-500 hover:text-white disabled:opacity-50">
                {o.label}
              </button>
            ))}
          </div>
        )}
        <button type="button" onClick={() => onSpeak(item.text)}
          className="mt-3.5 inline-flex items-center gap-1.5 text-sm font-medium text-blue-300 transition hover:text-white">
          <VolumeIcon size={15} />Play aloud
        </button>
      </div>
    </li>
  );
}
