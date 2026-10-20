import { ApiError, type MemoryItem, type TranscribeResponse, type TurnResponse } from "../types";

const BASE = (import.meta.env.VITE_API_BASE as string | undefined) ?? "";
const TIMEOUT_MS = 60_000;

async function request<T>(path: string, init: RequestInit = {}, timeout = TIMEOUT_MS): Promise<T> {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), timeout);
  let res: Response;
  try {
    res = await fetch(`${BASE}${path}`, { ...init, signal: ctrl.signal });
  } catch (e) {
    if ((e as Error).name === "AbortError")
      throw new ApiError("timeout", "The server took too long to respond. Please try again.");
    throw new ApiError("network", "I can't reach the server. Check your connection and try again.");
  } finally {
    clearTimeout(timer);
  }
  if (!res.ok) {
    let code = "server_error";
    let message = "Something went wrong. Please try again.";
    try {
      const body = await res.json();
      if (body?.error) { code = body.error.code; message = body.error.message; }
    } catch { /* non-JSON error body */ }
    throw new ApiError(code, message);
  }
  return res.json() as Promise<T>;
}

const json = (body: unknown): RequestInit => ({
  method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
});

export const api = {
  transcribe(blob: Blob, language?: string): Promise<TranscribeResponse> {
    const form = new FormData();
    if (language) form.append("language", language);
    const ext = blob.type.includes("mp4") ? "m4a" : blob.type.includes("ogg") ? "ogg" : "webm";
    form.append("audio", blob, `recording.${ext}`);
    return request("/api/v1/transcribe", { method: "POST", body: form }, 90_000);
  },
  turn(body: {
    text: string; input_mode: "voice" | "text"; asr_confidence?: number; chosen_intent?: string;
    attempts: number; edited: boolean; client_id?: string; use_memory: boolean; lang?: string;
    allow_general: boolean; history: { role: "user" | "assistant"; text: string }[];
  }): Promise<TurnResponse> {
    return request("/api/v1/chat/turn", json(body));
  },
  feedback(body: { client_id: string; original_text: string; corrected_text: string; remember: boolean }) {
    return request<{ stored: boolean; item: MemoryItem | null }>("/api/v1/feedback", json(body));
  },
  listMemory: (id: string) => request<MemoryItem[]>(`/api/v1/memory/${id}`),
  deleteMemory: (id: string, item?: number) =>
    request<{ deleted: number }>(`/api/v1/memory/${id}${item ? `/${item}` : ""}`, { method: "DELETE" }),
};

export const fetchHealth = () => request<import("../types").Health>("/api/v1/health");

export async function fetchEvaluation(): Promise<import("../types/evaluation").Evaluation> {
  return request("/api/v1/evaluation");
}
