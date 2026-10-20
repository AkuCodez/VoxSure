import type { Status } from "../types";

const META: Record<Status, { label: string; dot: string; cls: string }> = {
  ready: { label: "Ready", dot: "bg-slate-400", cls: "text-slate-200 border-slate-500/40 bg-slate-500/10" },
  listening: { label: "Listening", dot: "bg-red-400 animate-pulse", cls: "text-red-200 border-red-400/40 bg-red-500/10" },
  uploading: { label: "Uploading", dot: "bg-sky-400 animate-pulse", cls: "text-sky-200 border-sky-400/40 bg-sky-500/10" },
  transcribing: { label: "Transcribing", dot: "bg-sky-400 animate-pulse", cls: "text-sky-200 border-sky-400/40 bg-sky-500/10" },
  understanding: { label: "Understanding", dot: "bg-sky-400 animate-pulse", cls: "text-sky-200 border-sky-400/40 bg-sky-500/10" },
  clarifying: { label: "Needs clarification", dot: "bg-amber-400", cls: "text-amber-200 border-amber-400/40 bg-amber-500/10" },
  answered: { label: "Answered", dot: "bg-emerald-400", cls: "text-emerald-200 border-emerald-400/40 bg-emerald-500/10" },
  error: { label: "Error", dot: "bg-rose-400", cls: "text-rose-200 border-rose-400/40 bg-rose-500/10" },
};

/** Status is always conveyed by a text label (plus a dot), never by colour alone. */
export default function StatusPill({ status }: { status: Status }) {
  const m = META[status];
  return (
    <span role="status" aria-live="polite" data-testid="status"
      className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 text-sm font-medium ${m.cls}`}>
      <span aria-hidden="true" className={`h-2 w-2 rounded-full ${m.dot}`} />
      {m.label}
    </span>
  );
}
