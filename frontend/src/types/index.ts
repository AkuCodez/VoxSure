export type Status =
  | "ready" | "listening" | "uploading" | "transcribing"
  | "understanding" | "clarifying" | "answered" | "error";

export interface Option { intent: string; label: string }

export interface TurnResponse {
  turn_id: string;
  transcript: string;
  action: "answer" | "clarify" | "fallback";
  clarify_kind: "disambiguate" | "repair" | null;
  intent: string | null;
  confidence: number;
  response: string;
  options: Option[];
  reason: string;
  memory_applied: boolean;
  model_version: string;
  latency_ms: number;
}

export interface TranscribeResponse {
  transcript: string; asr_confidence: number; duration_s: number; latency_ms: number;
}

export interface MemoryItem { id: number; original: string; corrected: string }

export interface ChatItem {
  id: string;
  role: "user" | "assistant";
  text: string;
  mode?: "voice" | "text";
  turn?: TurnResponse;       // assistant items
  asrConfidence?: number;    // user voice items
  edited?: boolean;
  resolved?: boolean;        // clarification already answered
}

export class ApiError extends Error {
  constructor(public code: string, message: string) { super(message); }
}
