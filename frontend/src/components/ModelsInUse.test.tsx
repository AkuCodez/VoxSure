import { render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import ModelsInUse from "./ModelsInUse";

afterEach(() => vi.restoreAllMocks());
const health = { status: "ok", asr_ready: true, intent_ready: true, general_ready: true, translation_ready: false, db_ready: true,
  asr_model: "base.en", asr_multilingual: false, translation_engine: null, model_version: "distilbert-intent-v1", general_provider: "Groq", general_model: "llama-3.1-8b-instant" };

describe("ModelsInUse", () => {
  it("names each model, flags English-only speech and missing translation, and shows the AI provider", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => health }));
    render(<ModelsInUse />);
    await waitFor(() => expect(screen.getByText(/Whisper base.en \(English only\)/)).toBeInTheDocument());
    expect(screen.getByText(/DistilBERT · distilbert-intent-v1/)).toBeInTheDocument();
    expect(screen.getByText(/Groq · llama-3.1-8b-instant/)).toBeInTheDocument();
    expect(screen.getAllByText(/not available/).length).toBe(1); // translation
  });
  it("says AI answers are off when no provider is configured", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => ({ ...health, general_ready: false, general_provider: null, general_model: null }) }));
    render(<ModelsInUse />);
    await waitFor(() => expect(screen.getByText(/off \(no AI key configured\)/)).toBeInTheDocument());
  });
});
