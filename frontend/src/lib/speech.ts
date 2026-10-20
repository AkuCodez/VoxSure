export const ttsSupported = () => typeof window !== "undefined" && "speechSynthesis" in window;

export function speak(text: string, onEnd?: () => void) {
  if (!ttsSupported()) return;
  window.speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(text);
  u.lang = "en-US";
  u.rate = 1;
  if (onEnd) { u.onend = onEnd; u.onerror = onEnd; }
  window.speechSynthesis.speak(u);
}

export function stopSpeaking() {
  if (ttsSupported()) window.speechSynthesis.cancel();
}

export function confidenceWords(c: number): string {
  if (c >= 0.9) return "I'm quite sure about this.";
  if (c >= 0.6) return "I think this is what you meant.";
  return "I'm not very sure, so please check this.";
}
