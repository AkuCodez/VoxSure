import { useEffect, useRef, useState } from "react";
import Composer from "../components/Composer";
import MessageBubble from "../components/MessageBubble";
import SettingsPanel from "../components/SettingsPanel";
import StatusPill from "../components/StatusPill";
import { useChat } from "../hooks/useChat";
import { recorderSupport, useRecorder } from "../hooks/useRecorder";
import { ttsSupported } from "../lib/speech";

const EXAMPLES = [
  "When does the library open?",
  "How do I pay my tuition fees?",
  "I need a bonafide certificate",
  "When does it open?",
  "What's the weather today?",
];

export default function ChatPage() {
  const chat = useChat();
  const [settings, setSettings] = useState(false);
  const end = useRef<HTMLDivElement>(null);
  const mic = recorderSupport();

  const rec = useRecorder(
    (blob) => void chat.sendAudio(blob),
    (e) => { chat.setError(e.message); chat.setStatus("error"); },
  );

  useEffect(() => { end.current?.scrollIntoView?.({ behavior: "smooth" }); }, [chat.items.length, chat.status]);

  const status = rec.recording ? "listening" : chat.status;
  const onMic = () => {
    chat.stopAudio();
    if (rec.recording) rec.stop();
    else { chat.setError(null); chat.setStatus("listening"); void rec.start(); }
  };

  return (
    <div className="mx-auto flex h-full max-w-3xl flex-col bg-white shadow-sm">
      <header className="flex flex-wrap items-center justify-between gap-2 bg-navy-900 px-4 py-3 text-white">
        <div>
          <h1 className="text-xl font-bold tracking-tight">VoxSure</h1>
          <p className="text-sm text-brand-100">Student support voice assistant</p>
        </div>
        <div className="flex items-center gap-2">
          <StatusPill status={status} />
          {chat.speaking && (
            <button onClick={chat.stopAudio} className="rounded-md border border-white/60 px-3 py-1.5 text-sm">Stop audio</button>
          )}
          <button onClick={() => chat.toggleSpeak(!chat.speakOn)} aria-pressed={!chat.speakOn}
            disabled={!ttsSupported()}
            className="rounded-md border border-white/60 px-3 py-1.5 text-sm disabled:opacity-40">
            {chat.speakOn ? "Mute" : "Unmute"}
          </button>
          <button onClick={() => setSettings(true)} className="rounded-md border border-white/60 px-3 py-1.5 text-sm">Settings</button>
          <button onClick={chat.reset} className="rounded-md border border-white/60 px-3 py-1.5 text-sm">Reset</button>
        </div>
      </header>

      <p className="border-b border-amber-200 bg-amber-50 px-4 py-2 text-sm text-amber-950">
        Demo knowledge base: sample information for a fictional campus. This is not an official university service.
      </p>

      <main className="flex-1 overflow-y-auto bg-slate-50 px-4 py-4" aria-label="Conversation">
        {chat.items.length === 0 ? (
          <div className="mx-auto mt-6 max-w-md text-center">
            <h2 className="text-lg font-semibold text-navy-900">Ask me about campus life</h2>
            <p className="mt-1 text-slate-700">
              Library, exams, fees, hostels, placements, scholarships, certificates and IT help. If I'm unsure what you meant,
              I'll ask instead of guessing.
            </p>
            {!mic.ok && <p className="mt-3 rounded-md bg-amber-100 p-3 text-sm text-amber-950">{mic.reason}</p>}
            <p className="mt-4 text-sm font-medium text-slate-700">Try one of these:</p>
            <div className="mt-2 flex flex-wrap justify-center gap-2">
              {EXAMPLES.map((e) => (
                <button key={e} onClick={() => void chat.sendText(e)} disabled={chat.busy}
                  className="rounded-full border border-slate-300 bg-white px-3 py-1.5 text-sm hover:bg-brand-50">{e}</button>
              ))}
            </div>
          </div>
        ) : (
          <ul className="space-y-4" aria-live="polite">
            {chat.items.map((it) => (
              <MessageBubble key={it.id} item={it} memoryOn={chat.memoryOn} disabled={chat.busy || rec.recording}
                onEdit={(i, t, r) => void chat.editAndResend(i, t, r)} onChoose={(i, l) => void chat.choose(i, l)}
                onSpeak={chat.say} />
            ))}
          </ul>
        )}
        {chat.busy && <p className="mt-4 text-sm text-slate-600" aria-live="polite">Working on it…</p>}
        {chat.error && (
          <div role="alert" className="mt-4 rounded-lg border border-red-300 bg-red-50 p-3 text-red-900">
            <p className="font-medium">Something needs attention</p>
            <p className="text-sm">{chat.error}</p>
            <p className="mt-1 text-sm">You can always type your question below.</p>
          </div>
        )}
        <div ref={end} />
      </main>

      <Composer recording={rec.recording} seconds={rec.seconds} maxSeconds={rec.maxSeconds} busy={chat.busy}
        micAvailable={mic.ok} onMic={onMic} onSend={(t) => void chat.sendText(t)} />

      <SettingsPanel open={settings} onClose={() => setSettings(false)} speakOn={chat.speakOn} onSpeak={chat.toggleSpeak}
        memoryOn={chat.memoryOn} onMemory={chat.toggleMemory} memory={chat.memory} onDelete={(id) => void chat.deleteMemory(id)} />
    </div>
  );
}
