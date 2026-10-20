import { useEffect, useRef, useState } from "react";
import Composer from "../components/Composer";
import { MicIcon, MuteIcon, PanelIcon, ResetIcon, SettingsIcon, SparkIcon, StopIcon, VolumeIcon } from "../components/Icons";
import MessageBubble from "../components/MessageBubble";
import PipelinePanel from "../components/PipelinePanel";
import SettingsPanel from "../components/SettingsPanel";
import StatusPill from "../components/StatusPill";
import { useChat } from "../hooks/useChat";
import { recorderSupport, useRecorder } from "../hooks/useRecorder";
import { ttsSupported } from "../lib/speech";

const TOPICS = [
  "Library", "Exams & results", "Fee payment", "Hostel", "IT helpdesk",
  "Placements", "Scholarships", "Certificates", "Academic calendar", "Campus services",
];

const EXAMPLES = [
  { q: "When does the library open?", tag: "Clear request", tone: "text-emerald-300" },
  { q: "How do I pay my tuition fees?", tag: "Clear request", tone: "text-emerald-300" },
  { q: "When does it open?", tag: "Ambiguous · I'll ask what you mean", tone: "text-amber-300" },
  { q: "hostile fees for the box", tag: "Misheard · you can edit it", tone: "text-sky-300" },
  { q: "What's the weather today?", tag: "Out of scope · honest fallback", tone: "text-slate-400" },
  { q: "What can you do?", tag: "About the assistant", tone: "text-emerald-300" },
];

const iconBtn = "inline-flex items-center gap-2 rounded-xl border border-white/10 bg-white/[0.04] px-3 py-2 text-sm font-medium text-slate-200 transition hover:bg-white/10 disabled:opacity-40";

export default function ChatPage() {
  const chat = useChat();
  const [settings, setSettings] = useState(false);
  const [insights, setInsights] = useState(true);
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
  const locked = chat.busy || rec.recording;

  return (
    <div className="bg-console flex h-dvh w-full flex-col overflow-hidden">
      <header className="flex flex-wrap items-center justify-between gap-3 border-b border-white/[0.07] bg-ink-950/60 px-4 py-3 backdrop-blur-xl sm:px-6">
        <div className="flex items-center gap-3">
          <div className="orb orb-glow grid h-10 w-10 place-items-center rounded-xl text-white" aria-hidden="true"><MicIcon size={20} /></div>
          <div>
            <h1 className="text-lg font-bold leading-tight tracking-tight text-white">VoxSure</h1>
            <p className="text-xs text-slate-400">Error-aware voice assistant · Student support</p>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <StatusPill status={status} />
          {chat.speaking && <button onClick={chat.stopAudio} className={iconBtn}><StopIcon size={16} />Stop audio</button>}
          <button onClick={() => chat.toggleSpeak(!chat.speakOn)} aria-pressed={!chat.speakOn} disabled={!ttsSupported()} className={iconBtn}>
            {chat.speakOn ? <VolumeIcon size={16} /> : <MuteIcon size={16} />}{chat.speakOn ? "Mute" : "Unmute"}
          </button>
          <button onClick={() => setInsights((v) => !v)} aria-pressed={insights} className={`${iconBtn} hidden xl:inline-flex`}>
            <PanelIcon size={16} />Insights
          </button>
          <button onClick={() => setSettings(true)} className={iconBtn}><SettingsIcon size={16} />Settings</button>
          <button onClick={chat.reset} className={iconBtn}><ResetIcon size={16} />Reset</button>
        </div>
      </header>

      <div className="flex min-h-0 flex-1">
        <div className="flex min-w-0 flex-1 flex-col">
          <main className="flex-1 overflow-y-auto" aria-label="Conversation">
            <div className="mx-auto w-full max-w-3xl px-4 py-6 sm:px-8">
              {chat.items.length === 0 ? (
                <div className="fade-up mx-auto mt-2 text-center sm:mt-8">
                  <div className="orb orb-glow float mx-auto grid h-28 w-28 place-items-center rounded-full text-white ring-8 ring-blue-400/10" aria-hidden="true">
                    <MicIcon size={46} />
                  </div>
                  <p className="mt-7 inline-flex items-center gap-1.5 rounded-full border border-white/10 bg-white/[0.04] px-3 py-1 text-xs font-medium uppercase tracking-[0.14em] text-cyan-300">
                    <SparkIcon size={13} />Whisper · DistilBERT · Recovery policy
                  </p>
                  <h2 className="text-grad mt-4 text-4xl font-bold tracking-tight sm:text-5xl">How can I help you today?</h2>
                  <p className="mx-auto mt-4 max-w-xl text-lg leading-relaxed text-slate-400">
                    Ask out loud or type. If I'm not sure what you meant, I'll ask instead of guessing.
                  </p>
                  {!mic.ok && <p className="mx-auto mt-4 max-w-md rounded-xl bg-amber-400/10 p-3 text-sm text-amber-200">{mic.reason}</p>}

                  <ul className="mt-7 flex flex-wrap justify-center gap-2" aria-label="Topics I can help with">
                    {TOPICS.map((t) => (
                      <li key={t} className="rounded-full border border-white/10 bg-white/[0.04] px-3.5 py-1.5 text-sm text-slate-300">{t}</li>
                    ))}
                  </ul>

                  <p className="mt-10 text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Try one of these</p>
                  <div className="mt-3 grid gap-3 text-left sm:grid-cols-2">
                    {EXAMPLES.map((e) => (
                      <button key={e.q} onClick={() => ask(e.q)} disabled={locked}
                        className="panel group rounded-2xl p-4 transition hover:-translate-y-0.5 hover:border-blue-400/40 hover:bg-white/[0.06] disabled:opacity-50">
                        <span className="block font-semibold text-slate-100">{e.q}</span>
                        <span className={`mt-1 block text-xs ${e.tone}`}>{e.tag}</span>
                      </button>
                    ))}
                  </div>
                </div>
              ) : (
                <ul className="space-y-5" aria-live="polite">
                  {chat.items.map((it) => (
                    <MessageBubble key={it.id} item={it} memoryOn={chat.memoryOn} disabled={locked}
                      onEdit={(i, t, r) => void chat.editAndResend(i, t, r)} onChoose={(i, l) => void chat.choose(i, l)}
                      onSpeak={chat.say} />
                  ))}
                </ul>
              )}
              {chat.busy && (
                <div className="mt-5 flex items-center gap-3" aria-live="polite">
                  <div className="orb grid h-9 w-9 shrink-0 place-items-center rounded-full text-white" aria-hidden="true"><MicIcon size={16} /></div>
                  <div className="panel rounded-2xl px-4 py-3">
                    <span className="dots" aria-hidden="true"><span /><span /><span /></span>
                    <span className="sr-only">Working on it…</span>
                  </div>
                </div>
              )}
              {chat.error && (
                <div role="alert" className="mt-5 rounded-2xl border border-rose-400/30 bg-rose-500/10 p-4 text-rose-100">
                  <p className="font-semibold">Something needs attention</p>
                  <p className="text-sm">{chat.error}</p>
                  <p className="mt-1 text-sm text-rose-200/80">You can always type your question below.</p>
                </div>
              )}
              <div ref={end} />
            </div>
          </main>

          <Composer recording={rec.recording} seconds={rec.seconds} maxSeconds={rec.maxSeconds} busy={chat.busy}
            micAvailable={mic.ok} levels={rec.levels} onMic={onMic} onSend={(t) => void chat.sendText(t)} />
        </div>

        {insights && <PipelinePanel insight={chat.insight} counts={chat.counts} />}
      </div>

      <SettingsPanel open={settings} onClose={() => setSettings(false)} speakOn={chat.speakOn} onSpeak={chat.toggleSpeak}
        memoryOn={chat.memoryOn} onMemory={chat.toggleMemory} memory={chat.memory} onDelete={(id) => void chat.deleteMemory(id)} />
    </div>
  );
}
