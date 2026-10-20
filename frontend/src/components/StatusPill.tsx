import type { Status } from "../types";

const META: Record<Status, { label: string; icon: string; cls: string }> = {
  ready: { label: "Ready", icon: "●", cls: "bg-slate-100 text-slate-700 border-slate-300" },
  listening: { label: "Listening", icon: "◉", cls: "bg-red-50 text-red-800 border-red-300" },
  uploading: { label: "Uploading", icon: "↑", cls: "bg-brand-50 text-navy-800 border-brand-500" },
  transcribing: { label: "Transcribing", icon: "…", cls: "bg-brand-50 text-navy-800 border-brand-500" },
  understanding: { label: "Understanding", icon: "…", cls: "bg-brand-50 text-navy-800 border-brand-500" },
  clarifying: { label: "Needs clarification", icon: "?", cls: "bg-amber-50 text-amber-900 border-amber-400" },
  answered: { label: "Answered", icon: "✓", cls: "bg-emerald-50 text-emerald-900 border-emerald-400" },
  error: { label: "Error", icon: "!", cls: "bg-red-50 text-red-900 border-red-400" },
};

/** Status is conveyed by text AND an icon, never by colour alone. */
export default function StatusPill({ status }: { status: Status }) {
  const m = META[status];
  return (
    <span role="status" aria-live="polite" data-testid="status"
      className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-sm font-medium ${m.cls}`}>
      <span aria-hidden="true">{m.icon}</span>
      {m.label}
    </span>
  );
}
