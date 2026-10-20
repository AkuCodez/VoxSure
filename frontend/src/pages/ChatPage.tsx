import { useEffect, useRef, useState } from "react";
import Composer from "../components/Composer";
import MessageBubble from "../components/MessageBubble";
import SettingsPanel from "../components/SettingsPanel";
import Sidebar from "../components/Sidebar";
import StatusPill from "../components/StatusPill";
import { useChat } from "../hooks/useChat";
import { recorderSupport, useRecorder } from "../hooks/useRecorder";
import { ttsSupported } from "../lib/speech";

const EXAMPLES = [
  { icon: "📚", q: "When does the library open?", hint: "Clear question" },
  { icon: "💳", q: "How do I pay my tuition fees?", hint: "Clear question" },
  { icon: "📄", q: "I need a bonafide certificate", hint: "Clear question" },
  { icon: "🤔", q: "When does it open?", hint: "Ambiguous: I'll ask what you mean" },
  { icon: "🌦️", q: "What's the weather today?", hint: "Out of scope: I'll say so" },
  { icon: "🔧", q: "hostile fees for the box", hint: "Misheard: you can edit it" },
];

const btn = "rounded-lg border border-slate-300 bg-white px-3.5 py-2 text-sm font-medium text-slate-700 shadow-sm transition hover:bg-brand-50 disabled:opacity-40";

export default function ChatPage() {
  const chat = useChat();
  const [settings, setSettings] = useState(false);
  const end = useRef<HTMLDivElement>(null);
  const mic = recorderSupport();

  const rec = useRecorder(
    (blob) => void chat.sendAudio(blob),
    (e) => { chat.setError(e.message); chat.setStatus("error"); },
  );

  useEffect(() => {
    if (chat.items.length > 0) end.current?.scrollIntoView?.({ behavior: "smooth" });
  }, [chat.items.length, chat.status]);

  const status = rec.recording ? "listening" : chat.status;
  const onMic = () => {
    chat.stopAudio();
    if (rec.recording) rec.stop();
    else { chat.setError(null); chat.setStatus("listening"); void rec.start(); }
  };
  const ask = (q: string) => void chat.sendText(q);

  return (
    <div className="bg-app flex h-dvh w-full overflow-hidden">
      <Sidebar onAsk={ask} disabled={chat.busy || rec.recording} />

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200/80 bg-white/70 px-4 py-3 backdrop-blur sm:px-8">
          <div className="flex items-center gap-3">
            <div className="bg-orb grid h-9 w-9 place-items-center rounded-lg text-sm font-bold text-white lg:hidden" aria-hidden="true">V</div>
            <div>
              <h1 className="text-lg font-bold leading-tight text-navy-900">VoxSure <span className="font-medium text-slate-500">· Student support</span></h1>
              <p className="hidden text-sm text-slate-500 sm:block">Speak or type. I'll ask before I guess.</p>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <StatusPill status={status} />
            {chat.speaking && <button onClick={chat.stopAudio} className={btn}>■ Stop audio</button>}
            <button onClick={() => chat.toggleSpeak(!chat.speakOn)} aria-pressed={!chat.speakOn} disabled={!ttsSupported()} className={btn}>
              {chat.speakOn ? "Mute" : "Unmute"}
            </button>
            <button onClick={() => setSettings(true)} className={btn}>Settings</button>
            <button onClick={chat.reset} className={btn}>Reset</button>
          </div>
        </header>

        <p className="border-b border-amber-200 bg-amber-50 px-4 py-1.5 text-center text-sm text-amber-950 sm:px-8">
          Demo knowledge base: sample information for a fictional campus. This is not an official university service.
        </p>

        <main className="flex-1 overflow-y-auto" aria-label="Conversation">
          <div className="mx-auto w-full max-w-4xl px-4 py-6 sm:px-8">
            {chat.items.length === 0 ? (
              <div className="fade-up mx-auto mt-4 max-w-2xl text-center sm:mt-10">
                <div className="bg-orb float mx-auto grid h-24 w-24 place-items-center rounded-full shadow-2xl ring-8 ring-white/70" aria-hidden="true">
                  <svg width="42" height="42" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round">
                    <rect x="9" y="3" width="6" height="11" rx="3" fill="white" /><path d="M5 11a7 7 0 0014 0M12 18v3" />
                  </svg>
                </div>
                <h2 className="mt-6 text-3xl font-bold tracking-tight text-navy-900 sm:text-4xl">How can I help you today?</h2>
                <p className="mx-auto mt-3 max-w-xl text-lg text-slate-600">
                  Ask about the library, exams, fees, hostels, placements, scholarships, certificates or IT help.
                  If I'm unsure what you meant, I'll ask instead of guessing.
                </p>
                {!mic.ok && <p className="mt-4 rounded-lg bg-amber-100 p-3 text-sm text-amber-950">{mic.reason}</p>}
                <p className="mt-8 text-sm font-semibold uppercase tracking-wider text-slate-500">Try one of these</p>
                <div className="mt-3 grid gap-3 text-left sm:grid-cols-2">
                  {EXAMPLES.map((e) => (
                    <button key={e.q} onClick={() => ask(e.q)} disabled={chat.busy}
                      className="group flex items-start gap-3 rounded-xl border border-slate-200 bg-white p-4 shadow-sm transition hover:-translate-y-0.5 hover:border-brand-500 hover:shadow-md disabled:opacity-50">
                      <span aria-hidden="true" className="text-2xl">{e.icon}</span>
                      <span>
                        <span className="block font-semibold text-slate-900">{e.q}</span>
                        <span className="block text-sm text-slate-500">{e.hint}</span>
                      </span>
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              <ul className="space-y-5" aria-live="polite">
                {chat.items.map((it) => (
                  <MessageBubble key={it.id} item={it} memoryOn={chat.memoryOn} disabled={chat.busy || rec.recording}
                    onEdit={(i, t, r) => void chat.editAndResend(i, t, r)} onChoose={(i, l) => void chat.choose(i, l)}
                    onSpeak={chat.say} />
                ))}
              </ul>
            )}
            {chat.busy && (
              <div className="mt-4 flex items-center gap-3" aria-live="polite">
                <div className="bg-orb grid h-9 w-9 shrink-0 place-items-center rounded-full text-sm font-bold text-white" aria-hidden="true">V</div>
                <div className="rounded-2xl border border-slate-200 bg-white px-4 py-3 shadow-sm">
                  <span className="dots" aria-hidden="true"><span /><span /><span /></span>
                  <span className="sr-only">Working on it…</span>
                </div>
              </div>
            )}
            {chat.error && (
              <div role="alert" className="mt-4 rounded-xl border border-red-300 bg-red-50 p-4 text-red-900">
                <p className="font-semibold">Something needs attention</p>
                <p className="text-sm">{chat.error}</p>
                <p className="mt-1 text-sm">You can always type your question below.</p>
              </div>
            )}
            <div ref={end} />
          </div>
        </main>

        <Composer recording={rec.recording} seconds={rec.seconds} maxSeconds={rec.maxSeconds} busy={chat.busy}
          micAvailable={mic.ok} onMic={onMic} onSend={(t) => void chat.sendText(t)} />
      </div>

      <SettingsPanel open={settings} onClose={() => setSettings(false)} speakOn={chat.speakOn} onSpeak={chat.toggleSpeak}
        memoryOn={chat.memoryOn} onMemory={chat.toggleMemory} memory={chat.memory} onDelete={(id) => void chat.deleteMemory(id)} />
    </div>
  );
}
