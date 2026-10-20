import type { ReactNode } from "react";
import type { Insight } from "../types";

const REASONS: Record<string, string> = {
  confident: "Confident and in scope, so I answered.",
  user_confirmed: "You picked this option, so I answered directly.",
  competing_intents: "Two or more intents were plausible, so I asked.",
  low_confidence: "Too uncertain; the request may be misheard.",
  medium_confidence: "Not certain enough to answer safely.",
  low_asr_confidence: "The speech recogniser was unsure about the audio.",
  out_of_scope: "Outside the topics this assistant supports.",
  uncertain_out_of_scope: "Might be off-topic or misheard; asking to check.",
  repeated_failure: "Several clarifications failed, so I stopped looping.",
  general_ai: "Not about campus topics, so a general AI model wrote this answer.",
};

const pct = (x: number) => `${Math.round(x * 100)}%`;

function Stage({ n, title, tag, children }: { n: number; title: string; tag: string; children: ReactNode }) {
  return (
    <section className="rounded-2xl border border-white/[0.07] bg-white/[0.03] p-4">
      <header className="flex items-center gap-3">
        <span className="grid h-6 w-6 shrink-0 place-items-center rounded-full bg-blue-500/20 font-mono text-xs font-semibold text-blue-200 ring-1 ring-blue-400/30">{n}</span>
        <h3 className="text-sm font-semibold text-slate-100">{title}</h3>
        <span className="ml-auto rounded-md bg-white/5 px-2 py-0.5 font-mono text-[10px] uppercase tracking-wider text-slate-400">{tag}</span>
      </header>
      <div className="mt-3 text-sm text-slate-300">{children}</div>
    </section>
  );
}

function Bar({ value, tone = "bg-blue-400", marker }: { value: number; tone?: string; marker?: number }) {
  return (
    <div className="relative h-2 overflow-hidden rounded-full bg-white/[0.07]" role="img" aria-label={`${pct(value)}`}>
      <div className={`h-full rounded-full ${tone} transition-all duration-500`} style={{ width: pct(Math.max(0.02, value)) }} />
      {marker !== undefined && <div className="absolute inset-y-0 w-px bg-white/70" style={{ left: pct(marker) }} />}
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl bg-white/[0.04] px-3 py-2">
      <p className="text-[10px] uppercase tracking-wider text-slate-400">{label}</p>
      <p className="mt-0.5 font-mono text-base font-semibold text-slate-100">{value}</p>
    </div>
  );
}

export default function PipelinePanel({ insight, counts }: { insight: Insight | null; counts: { answer: number; clarify: number; fallback: number } }) {
  const turns = counts.answer + counts.clarify + counts.fallback;
  return (
    <aside className="panel-solid hidden w-[380px] shrink-0 flex-col overflow-y-auto xl:flex" aria-label="Pipeline insights">
      <div className="border-b border-white/[0.07] px-5 py-4">
        <h2 className="text-sm font-semibold uppercase tracking-[0.14em] text-slate-300">Pipeline insights</h2>
        <p className="mt-1 text-xs text-slate-400">What happened to your last request, stage by stage. Scores are model estimates, not guarantees.</p>
      </div>

      {!insight ? (
        <div className="flex flex-1 flex-col items-center justify-center gap-3 px-8 text-center">
          <div className="breathe grid h-14 w-14 place-items-center rounded-full border border-blue-400/30 bg-blue-500/10 text-blue-300" aria-hidden="true">
            <span className="font-mono text-lg">ƒ</span>
          </div>
          <p className="text-sm text-slate-400">Ask something and the speech recognition, intent model and recovery policy will appear here.</p>
        </div>
      ) : (
        <div className="space-y-3 p-4">
          <Stage n={1} title="Speech recognition" tag="Whisper base.en">
            {insight.mode === "voice" && insight.language && (
              <p className="mb-2 text-xs text-slate-400">Detected language: <span className="font-semibold text-slate-200">{insight.turn.lang_name}</span>
                {insight.languageProbability !== undefined ? ` (${Math.round(insight.languageProbability * 100)}%)` : ""}</p>
            )}
            {insight.mode === "voice" && insight.asrConfidence !== undefined ? (
              <>
                <div className="flex items-baseline justify-between">
                  <span>Recogniser confidence</span>
                  <span className="font-mono text-slate-100">{pct(insight.asrConfidence)}</span>
                </div>
                <div className="mt-2"><Bar value={insight.asrConfidence} tone={insight.asrConfidence < 0.4 ? "bg-amber-400" : "bg-cyan-400"} /></div>
                <div className="mt-3 grid grid-cols-2 gap-2">
                  <Metric label="Audio length" value={insight.durationS !== undefined ? `${insight.durationS.toFixed(1)} s` : "–"} />
                  <Metric label="Transcribe time" value={insight.asrMs !== undefined ? `${Math.round(insight.asrMs)} ms` : "–"} />
                </div>
              </>
            ) : (
              <p className="text-slate-400">Typed input: speech recognition was skipped.</p>
            )}
          </Stage>

          <Stage n={2} title="Intent classifier" tag="DistilBERT">
            {insight.turn.translated_input && (
              <p className="mb-3 rounded-lg bg-white/[0.04] p-2 text-xs text-slate-400">
                <span className="font-semibold text-slate-300">{insight.turn.lang_name} → English (NLLB-200): </span>
                “{insight.turn.translated_input}”
              </p>
            )}
            {insight.turn.candidates.length > 0 ? (
              <ul className="space-y-2.5">
                {insight.turn.candidates.map((c, i) => (
                  <li key={c.intent}>
                    <div className="flex items-baseline justify-between gap-3">
                      <span className={`truncate ${i === 0 ? "font-medium text-slate-100" : "text-slate-400"}`}>{c.label}</span>
                      <span className="font-mono text-xs text-slate-300">{pct(c.probability)}</span>
                    </div>
                    <div className="mt-1"><Bar value={c.probability} tone={i === 0 ? "bg-blue-400" : "bg-slate-500"}
                      marker={i === 0 ? insight.turn.thresholds?.t_high : undefined} /></div>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-slate-400">Skipped: you chose an option directly.</p>
            )}
            {insight.turn.thresholds && insight.turn.candidates.length > 0 && (
              <p className="mt-3 text-xs text-slate-400">White tick marks the {pct(insight.turn.thresholds.t_high)} answer threshold.</p>
            )}
          </Stage>

          <Stage n={3} title="Recovery policy" tag="Rules">
            <div className="flex items-center gap-2">
              <span className={`rounded-full px-2.5 py-0.5 text-xs font-semibold uppercase tracking-wider ring-1 ${
                insight.turn.action === "answer" ? "bg-emerald-400/10 text-emerald-300 ring-emerald-400/30"
                : insight.turn.action === "clarify" ? "bg-amber-400/10 text-amber-300 ring-amber-400/30"
                : "bg-slate-400/10 text-slate-300 ring-slate-400/30"}`}>
                {insight.turn.action === "clarify" && insight.turn.clarify_kind ? `clarify · ${insight.turn.clarify_kind}` : insight.turn.action}
              </span>
            </div>
            <p className="mt-2 leading-snug">{REASONS[insight.turn.reason] ?? insight.turn.reason}</p>
            {insight.turn.thresholds && insight.turn.reason !== "general_ai" && (
              <p className="mt-2 text-xs text-slate-400">
                Rule: answer when top ≥ {pct(insight.turn.thresholds.t_high)} and lead ≥ {Math.round(insight.turn.thresholds.margin * 100)} pts.
              </p>
            )}
          </Stage>

          <Stage n={4} title="Response" tag={insight.turn.answer_source === "general_ai" ? "AI provider" : "Knowledge base"}>
            <div className="grid grid-cols-2 gap-2">
              <Metric label="Decision time" value={`${Math.round(insight.turn.latency_ms)} ms`} />
              <Metric label="Model" value={insight.turn.model_version.replace("distilbert-", "")} />
            </div>
          </Stage>
        </div>
      )}

      <div className="mt-auto border-t border-white/[0.07] p-4">
        <p className="mb-2 text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-400">This session · {turns} turn{turns === 1 ? "" : "s"}</p>
        <div className="grid grid-cols-3 gap-2 text-center">
          <Metric label="Answered" value={String(counts.answer)} />
          <Metric label="Clarified" value={String(counts.clarify)} />
          <Metric label="Fallback" value={String(counts.fallback)} />
        </div>
      </div>
    </aside>
  );
}
