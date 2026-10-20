import { render, waitFor } from "@testing-library/react";
import { axe, toHaveNoViolations } from "jest-axe";
import { afterEach, describe, expect, it, vi } from "vitest";
import ChatPage from "./ChatPage";
import EvaluationPage from "./EvaluationPage";
import MessageBubble from "../components/MessageBubble";
import SettingsPanel from "../components/SettingsPanel";
import type { ChatItem } from "../types";

expect.extend(toHaveNoViolations);
afterEach(() => vi.restoreAllMocks());

// jsdom has no layout engine, so colour-contrast cannot be evaluated here; every other axe rule runs.
const opts = { rules: { "color-contrast": { enabled: false } } };

describe("automated accessibility (axe)", () => {
  it("chat page has no violations", async () => {
    const { container } = render(<ChatPage />);
    expect(await axe(container, opts)).toHaveNoViolations();
  });

  it("conversation messages with options, sources and highlighted words have no violations", async () => {
    const turn = { turn_id: "t", transcript: "x", action: "clarify" as const, clarify_kind: "disambiguate" as const, intent: null, confidence: 0.5,
      response: "Just to be sure, do you mean A or B?", options: [{ intent: "a", label: "A" }, { intent: "b", label: "B" }], candidates: [],
      sources: [{ title: "Demo", url: null, last_updated: "2026-10-20" }], thresholds: null, lang: "hi", lang_name: "Hindi", lang_verified: false,
      translated_input: "when does it open", translation_available: true, response_en: "Just to be sure, do you mean A or B?", translation_mode: "machine" as const, translation_warning: true, answer_source: "knowledge_base" as const, reason: "competing_intents", memory_applied: false, model_version: "v", latency_ms: 1 };
    const items: ChatItem[] = [
      { id: "u", role: "user", text: "kab khulta", mode: "voice", asrConfidence: 0.4, lang: "hi", langName: "Hindi", langVerified: false,
        translated: "when does it open", words: [{ word: "kab", probability: 0.2 }, { word: "khulta", probability: 0.9 }] },
      { id: "a", role: "assistant", text: turn.response, turn },
    ];
    const { container } = render(<ul>{items.map((i) => <MessageBubble key={i.id} item={i} memoryOn disabled={false} onEdit={() => {}} onChoose={() => {}} onSpeak={() => {}} />)}</ul>);
    expect(await axe(container, opts)).toHaveNoViolations();
  });

  it("settings dialog has no violations", async () => {
    const { container } = render(<SettingsPanel open onClose={() => {}} speakOn onSpeak={() => {}} memoryOn onMemory={() => {}}
      memory={[{ id: 1, original: "libary", corrected: "library" }]} onDelete={() => {}} />);
    expect(await axe(container, opts)).toHaveNoViolations();
  });

  it("evaluation dashboard has no violations", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: false, json: async () => ({ error: { code: "x", message: "unavailable" } }) }));
    const { container, getByRole } = render(<EvaluationPage />);
    await waitFor(() => getByRole("alert"));
    expect(await axe(container, opts)).toHaveNoViolations();
  });
});
