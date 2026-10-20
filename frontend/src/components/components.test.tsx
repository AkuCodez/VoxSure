import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import MessageBubble from "./MessageBubble";
import StatusPill from "./StatusPill";
import Composer from "./Composer";
import type { ChatItem, TurnResponse } from "../types";

const turn = (over: Partial<TurnResponse>): TurnResponse => ({
  turn_id: "t1", transcript: "x", action: "answer", clarify_kind: null, intent: "library_hours",
  confidence: 0.95, response: "The library opens at 8.", options: [], candidates: [], sources: [], thresholds: null, lang: "en", lang_name: "English", lang_verified: true, translated_input: null, translation_available: true, response_en: null, translation_mode: null, translation_warning: false, answer_source: "knowledge_base" as const, reason: "confident",
  memory_applied: false, model_version: "v", latency_ms: 5, ...over,
});

describe("StatusPill", () => {
  it("shows text label, not only colour", () => {
    render(<StatusPill status="clarifying" />);
    expect(screen.getByTestId("status")).toHaveTextContent("Needs clarification");
  });
});

describe("MessageBubble", () => {
  const base = { memoryOn: true, disabled: false, onEdit: vi.fn(), onChoose: vi.fn(), onSpeak: vi.fn() };

  it("lets the user edit a voice transcript and resend", () => {
    const onEdit = vi.fn();
    const item: ChatItem = { id: "u1", role: "user", text: "when does the libary open", mode: "voice", asrConfidence: 0.9 };
    render(<MessageBubble item={item} {...base} onEdit={onEdit} />);
    expect(screen.getByText("You said (transcript)")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /edit transcript/i }));
    fireEvent.change(screen.getByLabelText("Edit transcript"), { target: { value: "when does the library open" } });
    fireEvent.click(screen.getByLabelText(/remember this correction/i));
    fireEvent.click(screen.getByRole("button", { name: "Resend" }));
    expect(onEdit).toHaveBeenCalledWith(item, "when does the library open", true);
  });

  it("warns when the recogniser was unsure", () => {
    const item: ChatItem = { id: "u2", role: "user", text: "hostile", mode: "voice", asrConfidence: 0.3 };
    render(<MessageBubble item={item} {...base} />);
    expect(screen.getByText(/may have misheard/i)).toBeInTheDocument();
  });

  it("renders selectable clarification options", () => {
    const onChoose = vi.fn();
    const t = turn({ action: "clarify", clarify_kind: "disambiguate", intent: null,
      response: "Which do you mean?", options: [{ intent: "library_hours", label: "Library opening hours" }, { intent: "hostel_info", label: "Hostel rooms" }] });
    render(<MessageBubble item={{ id: "a1", role: "assistant", text: t.response, turn: t }} {...base} onChoose={onChoose} />);
    fireEvent.click(screen.getByRole("button", { name: "Hostel rooms" }));
    expect(onChoose).toHaveBeenCalledWith("hostel_info", "Hostel rooms");
  });

  it("hides options once resolved and never shows model scores as numbers", () => {
    const t = turn({ action: "clarify", clarify_kind: "disambiguate", options: [{ intent: "a", label: "A" }], confidence: 0.4 });
    render(<MessageBubble item={{ id: "a2", role: "assistant", text: "Which?", turn: t, resolved: true }} {...base} />);
    expect(screen.queryByRole("button", { name: "A" })).toBeNull();
    expect(screen.queryByText(/0\.4|40%/)).toBeNull();
  });
});

describe("Composer", () => {
  it("typed fallback works when the microphone is unavailable", () => {
    const onSend = vi.fn();
    render(<Composer recording={false} seconds={0} maxSeconds={20} busy={false} micAvailable={false} onMic={vi.fn()} onSend={onSend} />);
    expect(screen.getByRole("button", { name: "Start recording" })).toBeDisabled();
    expect(screen.getByText(/microphone unavailable/i)).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Type your question"), { target: { value: "hello" } });
    fireEvent.click(screen.getByRole("button", { name: "Send" }));
    expect(onSend).toHaveBeenCalledWith("hello");
  });

  it("toggles to a stop control while recording", () => {
    const onMic = vi.fn();
    render(<Composer recording seconds={3} maxSeconds={20} busy={false} micAvailable onMic={onMic} onSend={vi.fn()} />);
    fireEvent.click(screen.getByRole("button", { name: "Stop recording" }));
    expect(onMic).toHaveBeenCalled();
    expect(screen.getByText(/Recording… 3s/)).toBeInTheDocument();
  });
});

describe("trust features", () => {
  const base = { memoryOn: false, disabled: false, onEdit: vi.fn(), onChoose: vi.fn(), onSpeak: vi.fn() };

  it("underlines only the words the recogniser was unsure about", () => {
    const item: ChatItem = { id: "w1", role: "user", text: "when does the libary open", mode: "voice", asrConfidence: 0.8,
      words: [{ word: "when", probability: 0.99 }, { word: "does", probability: 0.98 }, { word: "the", probability: 0.97 },
              { word: "libary", probability: 0.2 }, { word: "open", probability: 0.95 }] };
    const { container } = render(<MessageBubble item={item} {...base} />);
    const low = container.querySelectorAll("[data-low]");
    expect(low).toHaveLength(1);
    expect(low[0]).toHaveTextContent("libary");
    expect(screen.getByText(/Underlined words were hard to hear/)).toBeInTheDocument();
  });

  it("shows the language badge and the English text the model understood", () => {
    const item: ChatItem = { id: "h1", role: "user", text: "पुस्तकालय कब खुलता है", mode: "text", lang: "hi", langName: "Hindi",
      langVerified: true, translated: "when does the library open" };
    render(<MessageBubble item={item} {...base} />);
    expect(screen.getByText(/Hindi · verified/)).toBeInTheDocument();
    expect(screen.getByText(/Understood as: “when does the library open”/)).toBeInTheDocument();
  });

  it("labels unverified languages as best effort", () => {
    const t = turn({ lang: "fr", lang_name: "French", lang_verified: false, response: "Bonjour" });
    render(<MessageBubble item={{ id: "a9", role: "assistant", text: t.response, turn: t }} {...base} />);
    expect(screen.getByText(/Best-effort translation/)).toBeInTheDocument();
  });

  it("shows the source with its last-updated date and only links when a URL exists", () => {
    const t = turn({ sources: [{ title: "Demo KB entry", url: null, last_updated: "2026-10-20" }] });
    const { rerender } = render(<MessageBubble item={{ id: "s1", role: "assistant", text: t.response, turn: t }} {...base} />);
    expect(screen.getByLabelText("Sources")).toHaveTextContent("Demo KB entry");
    expect(screen.getByLabelText("Sources")).toHaveTextContent(/Last updated/);
    expect(screen.queryByRole("link")).toBeNull();
    const t2 = turn({ sources: [{ title: "Library page", url: "https://example.org/lib", last_updated: null }] });
    rerender(<MessageBubble item={{ id: "s2", role: "assistant", text: t2.response, turn: t2 }} {...base} />);
    expect(screen.getByRole("link", { name: "Library page" })).toHaveAttribute("rel", expect.stringContaining("noopener"));
  });
});

describe("translated replies", () => {
  const base = { memoryOn: false, disabled: false, onEdit: vi.fn(), onChoose: vi.fn(), onSpeak: vi.fn() };
  it("offers the English original and says whether the translation was hand-written", () => {
    const t = turn({ lang: "hi", lang_name: "Hindi", response: "पुस्तकालय 08:00 से 22:00", response_en: "The library is open 08:00 to 22:00", translation_mode: "curated" });
    render(<MessageBubble item={{ id: "h", role: "assistant", text: t.response, turn: t }} {...base} />);
    expect(screen.getByText(/English original · hand-written translation/)).toBeInTheDocument();
    expect(screen.getByText("The library is open 08:00 to 22:00")).toBeInTheDocument();
    expect(screen.queryByRole("alert")).toBeNull();
  });
  it("warns when machine translation changed a number", () => {
    const t = turn({ lang: "fr", lang_name: "French", lang_verified: false, response: "ouvert", response_en: "Open 08:00", translation_mode: "machine", translation_warning: true });
    render(<MessageBubble item={{ id: "f", role: "assistant", text: t.response, turn: t }} {...base} />);
    expect(screen.getByRole("alert")).toHaveTextContent(/changed a number or time/);
    expect(screen.getByText(/machine translated \(NLLB-200\)/)).toBeInTheDocument();
  });
});

describe("general AI answers", () => {
  const base = { memoryOn: false, disabled: false, onEdit: vi.fn(), onChoose: vi.fn(), onSpeak: vi.fn() };
  it("labels AI-generated answers clearly and cites no campus source", () => {
    const t = turn({ intent: "general_knowledge", answer_source: "general_ai", reason: "general_ai", confidence: 0.9, response: "Paris.",
      sources: [{ title: "General answer written by an AI model (Groq). It is not from the campus knowledge base and may be wrong.", url: null, last_updated: null }] });
    render(<MessageBubble item={{ id: "g", role: "assistant", text: t.response, turn: t }} {...base} />);
    expect(screen.getByText(/General answer · AI-generated/)).toBeInTheDocument();
    expect(screen.getByLabelText("Sources")).toHaveTextContent(/not from the campus knowledge base/);
    expect(screen.queryByText(/I'm quite sure/)).toBeNull(); // no confidence claim on AI answers
  });
});
