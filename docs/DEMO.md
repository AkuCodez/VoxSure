# Demo script and test prompts

Outputs below were recorded from the running app (local run, model `distilbert-intent-v1`). Say each prompt aloud with the
microphone, or type it. Confidence is shown for the reader only; the UI deliberately does not show raw scores.

| # | Case | Prompt | Observed behaviour |
|---|---|---|---|
| 1 | Normal | "When does the library open?" | Answer (library hours), confidence 0.97 |
| 2 | Normal | "How do I get a bonafide certificate?" | Answer (certificates), 0.97 |
| 3 | Normal | "I forgot my student portal password" | Answer (IT helpdesk), 0.97 |
| 4 | Small talk | "Hello" / "Thanks, bye" | Greeting / goodbye answer |
| 5 | Ambiguous | "Can I get a receipt?" / "I want to renew" | **Clarify** with a targeted question, e.g. "Just to be sure, do you mean transcripts, bonafide or other certificates or paying fees or fee receipts?" plus option buttons; tapping one gives the answer |
| 6 | Ambiguous | "I need help with my form" | **Clarify**: options *Exams, hall tickets and results* / *Scholarships and financial aid* |
| 7 | Mis-heard, then corrected | "hostile fees for the box" | **Clarify** (library borrowing vs fees). Tap **Edit**, change to "how do I pay the fees", **Resend** → fee-payment answer; bubble marked "edited" |
| 8 | Not about campus | "What is the capital of France?" / "Tell me a joke" | With an AI provider configured: a **General answer · AI-generated** reply in the user's language. Without one (or with the Settings toggle off): a fallback listing supported topics |
| 8b | Other language | "पुस्तकालय कब खुलता है" | Hindi reply (hand-written), badge "Hindi · verified", "Understood as: when does the library open" |
| 9 | Gibberish | "asdf qwer zxcv" | Fallback (treated as out of scope) |
| 10 | Repeated failure | Ask "I need help with my form" again after two failed clarifications | Fallback: "type your question instead, rephrase it, or press Reset" (no endless loop) |
| 11 | Correction memory | Settings → enable *Correction memory*. Edit a transcript, tick *Remember this correction*, resend. Repeat the original wording | "Used your saved correction." Review/delete the entry in Settings |
| 12 | Speech output | Answers are read aloud; **Mute** / **Stop audio** / **Play aloud** | Depends on the browser's speech synthesis |
| 13 | Mic denied / unsupported | Block the microphone in browser settings, press the mic | Guidance message; typed box still works |

## Suggested live-demo order (about 3 minutes)

1. Say prompt 1 (voice) → transcript visible, answer, spoken reply.
2. Say prompt 5 → clarification buttons → tap *Library opening hours*.
3. Prompt 7 → show **Edit and Resend**.
4. Prompt 8 → transparent fallback.
5. Open Settings → privacy text, memory opt-in, delete.

## Known issues (honest list)

* Roughly 1 in 4 clear requests triggers an unnecessary clarification (see report §5.2); some ambiguous prompts are still answered confidently (e.g. "How do I apply?", "When does it open?" are currently answered).
* AI-generated general answers were tested with stand-in providers only; a live provider call needs the owner's key. They can be wrong.
* The knowledge base is sample data for a fictional campus.
* Real-microphone behaviour across devices and accents has not been measured.
* Free hosting may need a minute to wake after inactivity.
