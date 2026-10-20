import { useEffect, useState } from "react";
import { fetchHealth } from "../lib/api";
import type { Health } from "../types";

function Row({ label, value, ok }: { label: string; value: string; ok: boolean }) {
  return (
    <div className="flex items-start justify-between gap-3 border-t border-white/[0.06] py-2 first:border-t-0">
      <dt className="text-sm text-slate-400">{label}</dt>
      <dd className="text-right text-sm text-slate-100">
        {value} <span className={ok ? "text-emerald-300" : "text-amber-300"}>{ok ? "· ready" : "· not available"}</span>
      </dd>
    </div>
  );
}

/** Shows which models are actually running right now (from /health; never includes keys). */
export default function ModelsInUse() {
  const [h, setH] = useState<Health | null>(null);
  const [err, setErr] = useState(false);
  useEffect(() => { fetchHealth().then(setH).catch(() => setErr(true)); }, []);
  return (
    <section className="mt-8 rounded-xl border border-white/10 bg-white/[0.03] p-4" aria-label="Models in use">
      <h3 className="text-sm font-semibold text-white">Models in use</h3>
      {err && <p className="mt-2 text-sm text-amber-300">Could not reach the server.</p>}
      {!h && !err && <p className="mt-2 text-sm text-slate-400">Loading…</p>}
      {h && (
        <dl className="mt-2">
          <Row label="Speech recognition" ok={h.asr_ready}
            value={`${(h.asr_model ?? "?").toLowerCase().startsWith("whisper") ? "" : "Whisper "}${h.asr_model ?? "?"}${h.asr_model ? (h.asr_multilingual ? " (multilingual)" : " (English only)") : ""}`} />
          <Row label="Intent classifier" ok={h.intent_ready} value={`DistilBERT · ${h.model_version ?? "?"}`} />
          <Row label="Translation" ok={h.translation_ready} value={h.translation_engine ?? "none"} />
          <Row label="Non-campus answers" ok={h.general_ready}
            value={h.general_provider ? `${h.general_provider} · ${h.general_model ?? "?"}` : "off (no AI key configured)"} />
        </dl>
      )}
    </section>
  );
}
