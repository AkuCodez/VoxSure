export interface Counts {
  n: number; wrong_answer_rate: number; clarification_rate: number;
  task_completion_one_turn: number; task_completion_with_option_click: number;
  correct_answer: number; wrong_answer: number; appropriate_clarify: number; unnecessary_clarify: number;
}
export interface SpeechCondition {
  wer: number; wer_no_prompt: number; latency_median_s: number; latency_p95_s: number;
  pipeline_B: { wrong_answer_rate: number; clarification_rate: number; task_completion_one_turn: number };
  pipeline_C: { wrong_answer_rate: number; clarification_rate: number; task_completion_one_turn: number };
}
export interface LangResult {
  name: string; n: number; accuracy: number; macro_f1?: number; lang_id_accuracy: number;
  wrong_answer_rate_B: number; wrong_answer_rate_C: number; clarification_rate_C: number; verified: boolean;
  [k: string]: unknown;
}
export interface Evaluation {
  generated_at: string;
  dataset: { seed_utterances: number | null; sizes: Record<string, number>; classes: string[]; provenance: string };
  model: { name: string; base: string; epochs: number; best_val_acc: number; temperature: number; seed: number };
  intent: {
    baseline: { accuracy: number; macro_f1: number };
    distilbert: { accuracy: number; macro_f1: number };
    per_class: Record<string, { distilbert_f1: number; baseline_f1: number; support: number }>;
    confusion_matrix: number[][];
    calibration: { ece_test_uncalibrated: number; ece_test_calibrated: number; temperature: number; mean_conf_test_calibrated: number; acc_test: number };
    bootstrap_95ci: null | {
      n_resamples: number; macro_f1_distilbert: [number, number]; macro_f1_baseline: [number, number];
      wrong_answer_rate_B: [number, number]; wrong_answer_rate_C: [number, number];
      wrong_answer_rate_reduction_B_minus_C: [number, number]; clarification_rate_C: [number, number];
    };
  };
  policy: { params: Record<string, number>; tuned_on: string };
  recovery: { B_no_clarification: Counts; C_error_aware: Counts; stress_B: Counts; stress_C: Counts; stress_text_accuracy: number };
  memory_ablation: Record<string, number | string>;
  speech: null | { asr_model: string; n_utterances: number; voices: string[]; audio_kind: string; conditions: Record<string, SpeechCondition> };
  human_speech?: null | { asr_model: string; notes: string[]; missing_clips: string[]; languages: Record<string, { name: string; n: number; wer_forced_language: number; cer_forced_language: number; wer_auto_detect: number; language_detect_accuracy: number; latency_s_median: number; end_to_end: { wrong_answer_rate: number | null; answered_correctly: number | null } }> };
  multilingual: null | { languages: Record<string, LangResult>; notes?: string[]; [k: string]: unknown };
  limitations: string[];
}
