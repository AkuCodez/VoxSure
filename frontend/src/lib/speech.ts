export const ttsSupported = () => typeof window !== "undefined" && "speechSynthesis" in window;

const BCP47: Record<string, string> = {
  en: "en-US", hi: "hi-IN", pa: "pa-IN", de: "de-DE", fr: "fr-FR", es: "es-ES", pt: "pt-PT", it: "it-IT",
  nl: "nl-NL", ru: "ru-RU", ar: "ar-SA", zh: "zh-CN", ja: "ja-JP", ko: "ko-KR", tr: "tr-TR", ur: "ur-PK",
  bn: "bn-IN", ta: "ta-IN", te: "te-IN", mr: "mr-IN", gu: "gu-IN", kn: "kn-IN", ml: "ml-IN", ne: "ne-NP",
  pl: "pl-PL", uk: "uk-UA", id: "id-ID", vi: "vi-VN", th: "th-TH", sv: "sv-SE",
};

/** True if this browser/device has a voice for the language (so the reply can really be spoken). */
export function hasVoiceFor(lang: string): boolean {
  if (!ttsSupported()) return false;
  const prefix = (BCP47[lang] ?? lang).slice(0, 2).toLowerCase();
  return window.speechSynthesis.getVoices().some((v) => v.lang.toLowerCase().startsWith(prefix));
}

export function speak(text: string, onEnd?: () => void, lang = "en") {
  if (!ttsSupported()) return;
  window.speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(text);
  u.lang = BCP47[lang] ?? "en-US";
  const prefix = u.lang.slice(0, 2).toLowerCase();
  const voice = window.speechSynthesis.getVoices().find((v) => v.lang.toLowerCase().startsWith(prefix));
  if (voice) u.voice = voice;
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
