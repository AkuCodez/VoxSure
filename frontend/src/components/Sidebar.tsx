const TOPICS: { icon: string; name: string; ask: string }[] = [
  { icon: "📚", name: "Library", ask: "When does the library open?" },
  { icon: "📝", name: "Exams & results", ask: "How do I download my hall ticket?" },
  { icon: "💳", name: "Fee payment", ask: "How do I pay my tuition fees?" },
  { icon: "🏠", name: "Hostel", ask: "What are the hostel curfew timings?" },
  { icon: "💻", name: "IT helpdesk", ask: "I forgot my student portal password" },
  { icon: "💼", name: "Placements", ask: "How does the campus placement process work?" },
  { icon: "🎓", name: "Scholarships", ask: "What scholarships are available for students?" },
  { icon: "📄", name: "Certificates", ask: "How can I apply for a bonafide certificate?" },
  { icon: "🗓️", name: "Academic calendar", ask: "When does the next semester start?" },
  { icon: "🏫", name: "Campus services", ask: "What time does the canteen open?" },
];

const STEPS = [
  ["1", "Speak", "Tap the mic and ask in your own words."],
  ["2", "Check", "See the transcript and fix it if I misheard."],
  ["3", "Answer", "I answer, or ask you a quick question if unsure."],
];

export default function Sidebar({ onAsk, disabled }: { onAsk: (q: string) => void; disabled: boolean }) {
  return (
    <aside className="bg-side hidden w-80 shrink-0 flex-col overflow-y-auto text-white lg:flex xl:w-96" aria-label="About VoxSure">
      <div className="flex items-center gap-3 px-6 pb-4 pt-7">
        <div className="bg-orb grid h-11 w-11 place-items-center rounded-xl shadow-lg ring-1 ring-white/20" aria-hidden="true">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round">
            <rect x="9" y="3" width="6" height="11" rx="3" fill="white" /><path d="M5 11a7 7 0 0014 0M12 18v3" />
          </svg>
        </div>
        <div>
          <p className="text-xl font-bold leading-tight tracking-tight">VoxSure</p>
          <p className="text-sm text-brand-100/80">Error-aware voice assistant</p>
        </div>
      </div>

      <section className="px-6 py-3">
        <h2 className="text-xs font-semibold uppercase tracking-wider text-brand-100/60">What you can ask</h2>
        <ul className="mt-3 grid gap-1.5">
          {TOPICS.map((t) => (
            <li key={t.name}>
              <button type="button" disabled={disabled} onClick={() => onAsk(t.ask)}
                className="group flex w-full items-center gap-3 rounded-lg px-3 py-2 text-left text-[15px] text-white/90 transition hover:bg-white/10 disabled:opacity-50">
                <span aria-hidden="true" className="text-lg">{t.icon}</span>
                <span className="flex-1">{t.name}</span>
                <span aria-hidden="true" className="text-white/30 transition group-hover:translate-x-0.5 group-hover:text-white/70">›</span>
              </button>
            </li>
          ))}
        </ul>
      </section>

      <section className="px-6 py-4">
        <h2 className="text-xs font-semibold uppercase tracking-wider text-brand-100/60">How it works</h2>
        <ol className="mt-3 space-y-3">
          {STEPS.map(([n, h, d]) => (
            <li key={n} className="flex gap-3">
              <span className="grid h-7 w-7 shrink-0 place-items-center rounded-full bg-white/15 text-sm font-semibold">{n}</span>
              <p className="text-sm leading-snug text-white/80"><b className="text-white">{h}.</b> {d}</p>
            </li>
          ))}
        </ol>
      </section>

      <div className="mt-auto px-6 pb-6 pt-2">
        <p className="rounded-lg bg-white/10 p-3 text-xs leading-relaxed text-white/75">
          🔒 Your voice is never stored. Demo knowledge base: sample information for a fictional campus, not an official university service.
        </p>
      </div>
    </aside>
  );
}
