import { render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import EvaluationPage from "./EvaluationPage";

const counts = (w: number, c: number) => ({ n: 100, wrong_answer_rate: w, clarification_rate: c, task_completion_one_turn: 0.7,
  task_completion_with_option_click: 0.8, correct_answer: 1, wrong_answer: 1, appropriate_clarify: 1, unnecessary_clarify: 1 });
const data = {
  generated_at: "2026-10-20T00:00:00+00:00",
  dataset: { seed_utterances: 10, sizes: { train: 8, val: 1, test: 1 }, classes: ["a", "b"], provenance: "test" },
  model: { name: "m", base: "b", epochs: 1, best_val_acc: 0.9, temperature: 1, seed: 42 },
  intent: { baseline: { accuracy: 0.5, macro_f1: 0.45 }, distilbert: { accuracy: 0.8, macro_f1: 0.77 },
    per_class: { a: { distilbert_f1: 0.9, baseline_f1: 0.5, support: 5 }, b: { distilbert_f1: 0.6, baseline_f1: 0.4, support: 5 } },
    confusion_matrix: [[4, 1], [2, 3]],
    calibration: { ece_test_uncalibrated: 0.1, ece_test_calibrated: 0.05, temperature: 1.2, mean_conf_test_calibrated: 0.8, acc_test: 0.8 },
    bootstrap_95ci: { n_resamples: 1000, macro_f1_distilbert: [0.7, 0.8], macro_f1_baseline: [0.4, 0.5], wrong_answer_rate_B: [0.2, 0.3],
      wrong_answer_rate_C: [0.02, 0.06], wrong_answer_rate_reduction_B_minus_C: [0.15, 0.25], clarification_rate_C: [0.3, 0.4] } },
  policy: { params: { t_high: 0.8 }, tuned_on: "val" },
  recovery: { B_no_clarification: counts(0.25, 0), C_error_aware: counts(0.04, 0.33), stress_B: counts(0.3, 0), stress_C: counts(0.05, 0.5), stress_text_accuracy: 0.7 },
  memory_ablation: { pass2_correct_answer_rate_memory_off: 0.4, pass2_correct_answer_rate_memory_on: 0.55, n_stressed_utterances: 10, caveat: "exact repeats only" },
  speech: null, multilingual: null, limitations: ["Small test set."],
};

afterEach(() => vi.restoreAllMocks());

describe("EvaluationPage", () => {
  it("renders the measured numbers it was given, with limitations", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => data }));
    render(<EvaluationPage />);
    await waitFor(() => expect(screen.getByText("Intent macro-F1")).toBeInTheDocument());
    expect(screen.getAllByText("0.770").length).toBeGreaterThan(0);
    expect(screen.getAllByText("4.0%").length).toBeGreaterThan(0);
    expect(screen.getByText("Small test set.")).toBeInTheDocument();
    expect(screen.getByText(/Not measured yet/)).toBeInTheDocument(); // multilingual absent -> says so
  });

  it("shows a clear error if results are unavailable", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: false, json: async () => ({ error: { code: "no_evaluation", message: "Evaluation results have not been generated yet." } }) }));
    render(<EvaluationPage />);
    await waitFor(() => expect(screen.getByRole("alert")).toHaveTextContent("have not been generated"));
  });
});
