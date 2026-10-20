import { describe, expect, it } from "vitest";
import { conversationHistory } from "./useChat";
import type { ChatItem, TurnResponse } from "../types";

const turn = (action: TurnResponse["action"]) => ({ action } as TurnResponse);

describe("conversationHistory", () => {
  it("keeps user messages and real answers, drops clarifications and fallbacks, and caps at 6", () => {
    const items: ChatItem[] = [
      { id: "1", role: "user", text: "hello, what is my name?" },
      { id: "2", role: "assistant", text: "I'm not confident I heard that correctly.", turn: turn("clarify") },
      { id: "3", role: "user", text: "I never told you" },
      { id: "4", role: "assistant", text: "Right, I don't know your name.", turn: turn("answer") },
      { id: "5", role: "assistant", text: "That's outside what I can help with", turn: turn("fallback") },
    ];
    const h = conversationHistory(items);
    expect(h.map((x) => x.text)).toEqual(["hello, what is my name?", "I never told you", "Right, I don't know your name."]);
    const many = Array.from({ length: 10 }, (_, i): ChatItem => ({ id: String(i), role: "user", text: `m${i}` }));
    expect(conversationHistory(many)).toHaveLength(6);
    expect(conversationHistory(many)[5].text).toBe("m9");
  });
});
