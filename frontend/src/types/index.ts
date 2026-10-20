export type Status =
  | "ready" | "listening" | "uploading" | "transcribing"
  | "understanding" | "clarifying" | "answered" | "error";

export interface Option { intent: string; label: string }

export interface Source { title: string; url: string | null; last_updated: string | null }
export interface WordScore { word: string; probability: number }
export interface Candidate { intent: string; label: string; probability: number }
export interface Thresholds { t_high: number; margin: number; t_low: number }

export interface Insight {
  mode: "voice" | "text";
  language?: string;
  languageProbability?: number;
  asrConfidence?: number;
  asrMs?: number;
  durationS?: number;
  turn: TurnResponse;
}

export interface TurnResponse {
  turn_id: string;
  transcript: string;
  action: "answer" | "clarify" | "fallback";
  clarify_kind: "disambiguate" | "repair" | null;
  intent: string | null;
  confidence: number;
  response: string;
  options: Option[];
  candidates: Candidate[];
  sources: Source[];
  thresholds: Thresholds | null;
  lang: string;
  lang_name: string;
  lang_verified: boolean;
  translated_input: string | null;
  translation_available: boolean;
  response_en: string | null;
  translation_mode: "curated" | "machine" | null;
  translation_warning: boolean;
  answer_source: "knowledge_base" | "general_ai" | "none";
  reason: string;
  memory_applied: boolean;
  model_version: string;
  latency_ms: number;
}

export interface TranscribeResponse {
  transcript: string; asr_confidence: number; duration_s: number; latency_ms: number;
  language: string; language_name: string; language_probability: number; words: WordScore[];
}

export interface MemoryItem { id: number; original: string; corrected: string }

export interface ChatItem {
  id: string;
  role: "user" | "assistant";
  text: string;
  mode?: "voice" | "text";
  turn?: TurnResponse;       // assistant items
  asrConfidence?: number;    // user voice items
  asrMs?: number;
  durationS?: number;
  words?: WordScore[];       // per-word recogniser confidence (voice items)
  lang?: string;
  langName?: string;
  langVerified?: boolean;
  translated?: string | null; // English text the model actually used (non-English input)
  edited?: boolean;
  resolved?: boolean;        // clarification already answered
}

export interface Health {
  status: "ok" | "degraded";
  asr_ready: boolean; intent_ready: boolean; general_ready: boolean; translation_ready: boolean; translation_engine: string | null; db_ready: boolean;
  asr_model: string | null; asr_multilingual: boolean; model_version: string | null;
  general_provider: string | null; general_model: string | null;
}

export class ApiError extends Error {
  constructor(public code: string, message: string) { super(message); }
}
