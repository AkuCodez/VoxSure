import { useEffect, useState, type ReactNode } from "react";
import { fetchEvaluation } from "../lib/api";
import type { Evaluation } from "../types/evaluation";

const pct = (x: number, d = 1) => `${(x * 100).toFixed(d)}%`;
const ci = (v?: [number, number]) => (v ? `${pct(v[0])} – ${pct(v[1])}` : "–");

function Card({ title, children, note }: { title: string; children: ReactNode; note?: string }) {
  return (
    <section className="panel rounded-2xl p-5">
      <h2 className="text-sm font-semibold uppercase tracking-[0.14em] text-slate-300">{title}</h2>
      <div className="mt-4">{children}</div>
      {note && <p className="mt-3 text-xs leading-relaxed text-slate-400">{note}</p>}
    </section>
  );
}

function Kpi({ label, value, sub, tone = "text-white" }: { label: string; value: string; sub?: string; tone?: string }) {
  return (
    <div className="panel rounded-2xl p-5">
      <p className="text-xs uppercase tracking-wider text-slate-400">{label}</p>
      <p className={`mt-2 font-mono text-3xl font-bold ${tone}`}>{value}</p>
      {sub && <p className="mt-1 text-xs text-slate-400">{sub}</p>}
    </div>
  );
}

function Bar({ value, max = 1, tone }: { value: number; max?: number; tone: string }) {
  return (
    <div className="h-2.5 overflow-hidden rounded-full bg-white/[0.07]" role="img" aria-label={pct(value)}>
      <div className={`h-full rounded-full ${tone}`} style={{ width: `${Math.min(100, (value / max) * 100)}%` }} />
    </div>
  );
}

function Compare({ rows }: { rows: { label: string; a: number; b: number; fmt?: (x: number) => string }[] }) {
  return (
    <div className="space-y-4">
      {rows.map((r) => (
        <div key={r.label}>
          <p className="mb-1.5 text-sm text-slate-300">{r.label}</p>
          {[["No recovery (always answer)", r.a, "bg-rose-400"], ["VoxSure error-aware", r.b, "bg-emerald-400"]].map(([n, v, tone]) => (
            <div key={n as string} className="mb-1.5 grid grid-cols-[170px_1fr_64px] items-center gap-3 text-xs text-slate-400">
              <span>{n as string}</span><Bar value={v as number} tone={tone as string} />
              <span className="text-right font-mono text-slate-200">{(r.fmt ?? pct)(v as number)}</span>
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}

function Confusion({ m, labels }: { m: number[][]; labels: string[] }) {
  const max = Math.max(...m.flat(), 1);
  const short = (l: string) => l.replace(/_/g, " ");
  return (
    <div className="overflow-x-auto">
      <table className="border-separate border-spacing-0.5 text-[11px]" aria-label="Confusion matrix: rows are true intents, columns are predicted intents">
        <thead>
          <tr>
            <th className="p-1" />
            {labels.map((l) => (
              <th key={l} className="h-24 w-8 p-0 align-bottom font-normal text-slate-400"><div className="-rotate-60 origin-bottom-left translate-x-3 whitespace-nowrap">{short(l)}</div></th>
            ))}
          </tr>
        </thead>
        <tbody>
          {m.map((row, i) => (
            <tr key={labels[i]}>
              <th className="whitespace-nowrap pr-2 text-right font-normal text-slate-400">{short(labels[i])}</th>
              {row.map((v, j) => (
                <td key={j} title={`true ${short(labels[i])} → predicted ${short(labels[j])}: ${v}`}
                  className={`h-8 w-8 rounded text-center font-mono ${i === j ? "ring-1 ring-emerald-300/30" : ""}`}
                  style={{ background: v === 0 ? "rgba(255,255,255,0.03)" : `rgba(${i === j ? "52,211,153" : "251,113,133"},${0.18 + 0.75 * (v / max)})`, color: v ? "#fff" : "#475569" }}>
                  {v || ""}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      <p className="mt-2 text-xs text-slate-400">Green diagonal = correct. Red = confusions. Rows: true intent; columns: predicted intent.</p>
    </div>
  );
}

export default function EvaluationPage() {
  const [data, setData] = useState<Evaluation | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchEvaluation().then(setData).catch((e: Error) => setError(e.message));
  }, []);

  return (
    <div className="bg-console h-dvh overflow-y-auto">
      <header className="sticky top-0 z-10 flex items-center justify-between gap-3 border-b border-white/[0.07] bg-ink-950/80 px-4 py-3 backdrop-blur-xl sm:px-8">
        <div>
          <h1 className="text-lg font-bold text-white">Evaluation dashboard</h1>
          <p className="text-xs text-slate-400">Measured results only. Every number comes from a reproducible run in this repository.</p>
        </div>
        <a href="#/" className="rounded-xl border border-white/10 bg-white/[0.04] px-4 py-2 text-sm font-medium text-slate-200 hover:bg-white/10">← Back to assistant</a>
      </header>

      <main className="mx-auto max-w-6xl space-y-6 px-4 py-8 sm:px-8">
        {error && <p role="alert" className="rounded-xl border border-rose-400/30 bg-rose-500/10 p-4 text-rose-100">{error}</p>}
        {!data && !error && <p className="text-slate-400" aria-live="polite">Loading results…</p>}
        {data && <Body d={data} />}
      </main>
    </div>
  );
}

function Body({ d }: { d: Evaluation }) {
  const b = d.intent.bootstrap_95ci;
  const B = d.recovery.B_no_clarification, C = d.recovery.C_error_aware;
  const clean = d.speech?.conditions.clean;
  return (
    <>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Kpi label="Intent macro-F1" value={d.intent.distilbert.macro_f1.toFixed(3)} sub={`95% CI ${b ? `${b.macro_f1_distilbert[0].toFixed(2)}–${b.macro_f1_distilbert[1].toFixed(2)}` : "n/a"} · baseline ${d.intent.baseline.macro_f1.toFixed(3)}`} tone="text-cyan-300" />
        <Kpi label="Wrong-answer rate" value={pct(C.wrong_answer_rate)} sub={`vs ${pct(B.wrong_answer_rate)} without recovery`} tone="text-emerald-300" />
        <Kpi label="Clarification rate" value={pct(C.clarification_rate)} sub="the price paid for fewer wrong answers" tone="text-amber-300" />
        <Kpi label="Speech WER (clean)" value={clean ? pct(clean.wer) : "n/a"} sub={clean ? `${d.speech?.n_utterances} synthetic clips · p50 ${clean.latency_median_s.toFixed(2)} s` : "not measured"} tone="text-blue-300" />
      </div>

      <Card title="Proposed system vs TF-IDF + Logistic Regression baseline" note={`Same held-out test set (n = ${d.dataset.sizes.test}). Intervals are 95% bootstrap CIs (${b?.n_resamples ?? "–"} resamples).`}>
        <Compare rows={[
          { label: "Macro-F1 (higher is better)", a: d.intent.baseline.macro_f1, b: d.intent.distilbert.macro_f1, fmt: (x) => x.toFixed(3) },
          { label: "Accuracy (higher is better)", a: d.intent.baseline.accuracy, b: d.intent.distilbert.accuracy },
        ]} />
        <p className="mt-4 text-sm text-slate-400">Baseline names: <b className="text-rose-300">TF-IDF + LogReg</b> (top bar) vs <b className="text-emerald-300">fine-tuned DistilBERT</b> (bottom bar). CIs: DistilBERT {ci(b?.macro_f1_distilbert)}, baseline {ci(b?.macro_f1_baseline)}.</p>
      </Card>

      <Card title="Error-aware recovery vs always answering" note={`Test turns: ${B.n} (clear requests plus 25 deliberately ambiguous ones). A 'wrong answer' is a wrong intent, an answered out-of-scope request, or an answered ambiguous request.`}>
        <Compare rows={[
          { label: "Wrong-answer rate (lower is better)", a: B.wrong_answer_rate, b: C.wrong_answer_rate },
          { label: "Task completion in one turn on clear requests (higher is better)", a: B.task_completion_one_turn, b: C.task_completion_one_turn },
          { label: "Clarification rate", a: B.clarification_rate, b: C.clarification_rate },
          { label: `Under heavy noise (stress): wrong-answer rate`, a: d.recovery.stress_B.wrong_answer_rate, b: d.recovery.stress_C.wrong_answer_rate },
        ]} />
        <p className="mt-4 text-sm text-slate-400">Wrong-answer rate 95% CI: without recovery {ci(b?.wrong_answer_rate_B)}, with recovery {ci(b?.wrong_answer_rate_C)}; reduction {ci(b?.wrong_answer_rate_reduction_B_minus_C)}. With one option tap, completion reaches {pct(C.task_completion_with_option_click)}.</p>
      </Card>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card title="Per-class F1 (test)" note="Each class has few distinct held-out phrasings, so single-class scores are high-variance.">
          <ul className="space-y-2.5">
            {Object.entries(d.intent.per_class).sort((x, y) => y[1].distilbert_f1 - x[1].distilbert_f1).map(([k, v]) => (
              <li key={k} className="grid grid-cols-[130px_1fr_44px] items-center gap-3 text-xs text-slate-400">
                <span className="truncate">{k.replace(/_/g, " ")}</span>
                <div className="space-y-1"><Bar value={v.distilbert_f1} tone="bg-emerald-400" /><Bar value={v.baseline_f1} tone="bg-rose-400/70" /></div>
                <span className="text-right font-mono text-slate-200">{v.distilbert_f1.toFixed(2)}</span>
              </li>
            ))}
          </ul>
          <p className="mt-3 text-xs text-slate-400"><span className="text-emerald-300">Green</span> DistilBERT · <span className="text-rose-300">red</span> baseline.</p>
        </Card>

        <Card title="Calibration and policy" note="Temperature scaling was fitted on validation data only. Policy thresholds were tuned on validation data, then frozen before test evaluation.">
          <dl className="grid grid-cols-2 gap-3 text-sm">
            {[["ECE before", d.intent.calibration.ece_test_uncalibrated.toFixed(3)], ["ECE after", d.intent.calibration.ece_test_calibrated.toFixed(3)],
              ["Temperature", d.intent.calibration.temperature.toFixed(2)], ["Mean confidence", pct(d.intent.calibration.mean_conf_test_calibrated)],
              ["Test accuracy", pct(d.intent.calibration.acc_test)], ["Answer threshold", pct(d.policy.params.t_high, 0)]].map(([k, v]) => (
              <div key={k} className="rounded-xl bg-white/[0.04] p-3"><dt className="text-[10px] uppercase tracking-wider text-slate-400">{k}</dt><dd className="mt-0.5 font-mono text-lg text-slate-100">{v}</dd></div>
            ))}
          </dl>
        </Card>
      </div>

      <Card title="Confusion matrix (DistilBERT, test set)"><Confusion m={d.intent.confusion_matrix} labels={d.dataset.classes} /></Card>

      {d.speech && (
        <Card title="Speech recognition and latency" note={`${d.speech.audio_kind}. Model: Whisper ${d.speech.asr_model}. White noise added at the stated SNR. Latency measured on the author's laptop CPU. These WERs are lower bounds; real accents and microphones were not measured.`}>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="text-xs uppercase tracking-wider text-slate-400"><tr><th className="py-2">Condition</th><th>WER</th><th>Latency p50 / p95</th><th>Wrong answers (always answer → VoxSure)</th></tr></thead>
              <tbody className="text-slate-300">
                {Object.entries(d.speech.conditions).map(([c, v]) => (
                  <tr key={c} className="border-t border-white/[0.06]">
                    <td className="py-2 font-medium">{c === "clean" ? "Clean" : c.replace("snr", "SNR ") + " dB"}</td>
                    <td className="font-mono">{pct(v.wer)}</td>
                    <td className="font-mono">{v.latency_median_s.toFixed(2)} s / {v.latency_p95_s.toFixed(2)} s</td>
                    <td className="font-mono">{pct(v.pipeline_B.wrong_answer_rate)} → {pct(v.pipeline_C.wrong_answer_rate)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {d.multilingual ? (
        <Card title="Multilingual (typed input → translation → classifier → translated reply)" note={(d.multilingual.notes ?? []).join(" ")}>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="text-xs uppercase tracking-wider text-slate-400"><tr><th className="py-2">Language</th><th>n</th><th>Accuracy</th><th>Language ID</th><th>Wrong answers (always answer → VoxSure)</th><th>Status</th></tr></thead>
              <tbody className="text-slate-300">
                {Object.entries(d.multilingual.languages).map(([c, v]) => (
                  <tr key={c} className="border-t border-white/[0.06]">
                    <td className="py-2 font-medium">{v.name}</td><td className="font-mono">{v.n}</td><td className="font-mono">{pct(v.accuracy)}</td>
                    <td className="font-mono">{pct(v.lang_id_accuracy)}</td>
                    <td className="font-mono">{pct(v.wrong_answer_rate_B)} → {pct(v.wrong_answer_rate_C)}</td>
                    <td>{v.verified ? <span className="text-emerald-300">verified</span> : <span className="text-amber-300">best effort</span>}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      ) : (
        <Card title="Multilingual"><p className="text-sm text-slate-400">Not measured yet. Languages are labelled “best effort” until a measured result appears here.</p></Card>
      )}

      <Card title="Correction memory (simulation)" note={String(d.memory_ablation.caveat ?? "")}>
        <p className="text-sm text-slate-300">
          Correct-answer rate on repeated mis-heard utterances: <b className="font-mono text-slate-100">{pct(Number(d.memory_ablation.pass2_correct_answer_rate_memory_off))}</b> without memory vs{" "}
          <b className="font-mono text-emerald-300">{pct(Number(d.memory_ablation.pass2_correct_answer_rate_memory_on))}</b> with memory (n = {String(d.memory_ablation.n_stressed_utterances)}).
        </p>
      </Card>

      <Card title="Limitations (read before trusting any number)">
        <ul className="list-disc space-y-1.5 pl-5 text-sm text-slate-300">{d.limitations.map((l) => <li key={l}>{l}</li>)}</ul>
        <p className="mt-3 text-xs text-slate-400">Generated {new Date(d.generated_at).toLocaleString()} · dataset: {d.dataset.provenance} · model {d.model.name}, seed {d.model.seed}.</p>
      </Card>
    </>
  );
}
