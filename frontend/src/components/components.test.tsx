import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import MessageBubble from "./MessageBubble";
import StatusPill from "./StatusPill";
import Composer from "./Composer";
import type { ChatItem, TurnResponse } from "../types";

const turn = (over: Partial<TurnResponse>): TurnResponse => ({
  turn_id: "t1", transcript: "x", action: "answer", clarify_kind: null, intent: "library_hours",
  confidence: 0.95, response: "The library opens at 8.", options: [], reason: "confident",
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
