# Dataset card: VoxSure intents

* **Provenance:** author-written seed utterances in `ml/scripts/build_dataset.py` (no external data, no licence issues).
* **Generation:** deterministic (seed 42): fillers, ASR-style normalisation, plausible ASR word substitutions.
* **Files:** `train.jsonl` (1326), `val.jsonl` (238), `test.jsonl` (238), `ambiguous_val.jsonl` (25), `ambiguous_test.jsonl` (25), `stats.json`.
* **Split:** by seed group within each class (70/15/15) so near-duplicates never cross splits; exact-text overlap between splits is 0 (see `stats.json`).
* **Classes (16):** 11 campus-domain intents, greeting, thanks_bye, about_bot, help_capabilities, out_of_scope. Class balance is in `stats.json`; out_of_scope is the largest class by design.
* **Ambiguous sets** are used for evaluation only, never for training.
* **Limitations:** single author's phrasing; templated variants; no real users or real ASR transcripts; metrics are optimistic compared with deployment.
