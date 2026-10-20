# Dataset card: VoxSure intents

* **Provenance:** author-written seed utterances in `ml/scripts/build_dataset.py` (340 seeds; no external data, no licence issues).
* **Generation:** deterministic (seed 42): conversational fillers, ASR-style normalisation, plausible ASR word substitutions.
* **Classes (16):** 11 campus-domain intents, `greeting`, `thanks_bye`, `about_bot`, `help_capabilities`, `out_of_scope`. Per-split class counts are in `stats.json`.
* **Files:**
  * `train.jsonl` (1582), `val.jsonl` (337), `test.jsonl` (337), `stats.json`
  * `ambiguous_val.jsonl` (25), `ambiguous_test.jsonl` (25): under-specified requests used for evaluation only, never for training
  * `multilingual_test.jsonl`: 47 sentences each in English, Hindi, Punjabi and German (typed-text evaluation, never trained on)
  * `recording_script.md`: sentences for optional human recordings (see `ml/scripts/evaluate_human_recordings.py`)
* **Split:** by seed group within each class so near-duplicates never cross splits; exact-text overlap between splits is 0 (checked in `stats.json`).
* **History (disclosed):** the dataset was revised several times after observing weak results (conversational intents added; more small-talk seeds;
  more varied seeds for weak classes with a larger test set). Each revision regenerated the splits and every result. This is a mild form of test-set feedback; see `docs/REPORT.md` §3.
* **Limitations:** a single author's phrasing; templated variants; no real users or real ASR transcripts; only a few distinct held-out phrasings per class;
  multilingual sentences and hand-written translations are not native-speaker verified. Metrics are therefore optimistic compared with real deployment.
