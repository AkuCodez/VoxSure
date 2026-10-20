import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import SettingsPanel from "./SettingsPanel";

describe("SettingsPanel", () => {
  const props = { open: true, onClose: vi.fn(), speakOn: true, onSpeak: vi.fn(), memoryOn: false, onMemory: vi.fn(), memory: [], onDelete: vi.fn() };

  it("lets the user turn off AI answers for non-campus questions, and discloses what is sent", () => {
    const onGeneral = vi.fn();
    render(<SettingsPanel {...props} generalOn onGeneral={onGeneral} />);
    const toggle = screen.getByRole("checkbox", { name: /Answer non-campus questions with AI/ });
    expect(toggle).toBeChecked();
    fireEvent.click(toggle);
    expect(onGeneral).toHaveBeenCalledWith(false);
    expect(screen.getByText(/sent to the configured external AI provider/)).toBeInTheDocument();
  });
});
