# Model card

**Intent model** (`intent_model/`): `distilbert-base-uncased` fine-tuned for 16-way intent classification (English).
Config, seed, epochs, learning rate and the fitted calibration temperature are in `train_config.json`; labels in `label_map.json`.
Training: `ml/scripts/train_intent.py`; evaluation: `ml/scripts/evaluate_intent.py`; results: `ml/reports/intent_eval.json`.
Weights (`model.safetensors`, 256 MB) are tracked with Git LFS.

**Policy** (`policy.json`): thresholds tuned on validation data only, then frozen.

**Translation model** (`nllb-ct2/`, not committed, about 600 MB): `facebook/nllb-200-distilled-600M` converted to int8 CTranslate2 by
`ml/scripts/prepare_nllb.py`. Licence CC-BY-NC 4.0 (non-commercial).

**Intended use:** student-support questions in a bounded domain. **Not for:** open-domain questions, medical, legal or financial advice.
**Limitations:** author-written training data; small test set; English-trained classifier reached through machine translation for other
languages; accuracy figures are in the report with confidence intervals and caveats.
