# VoxSure: Design brief (as built)

**Direction.** A dark "voice console": deep navy surfaces, blue/cyan accents, restrained use of amber (needs attention) and green
(answered). The spec asked for navy/blue/neutral; the dark treatment keeps that palette.

**States (text label always shown, never colour alone):** Ready, Listening, Uploading, Transcribing, Understanding, Needs clarification, Answered, Error.

**Key screens.** Chat (hero mic, topic chips, example cards, conversation, composer with live waveform), Pipeline insights panel
(ASR confidence, detected language, translation, intent probabilities, policy decision and reason, timings), Settings and privacy,
Evaluation dashboard (`#/evaluation`).

**Trust.** Doubtful words are underlined (and explained on hover/tap), clarification names the competing intents, answers show their
source and last-updated date, non-verified languages are labelled "best effort", and model scores are shown as estimates.

**Accessibility.** Labelled controls, `aria-live` status and conversation, visible focus ring, typed fallback, keyboard-reachable
controls, reduced-motion support. An automated axe audit has **not** been run.

**Responsive.** Single column below `xl`; insights panel appears on wide screens; no horizontal scroll at 375 px (checked in an emulated viewport).
