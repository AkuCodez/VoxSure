"""Download facebook/nllb-200-distilled-600M and convert it to an int8 CTranslate2 model.

Output: ml/artifacts/nllb-ct2/  (about 600 MB; not committed to git, rebuilt in the Docker image).
Licence note: NLLB-200 weights are CC-BY-NC 4.0 (non-commercial use; fine for this academic project).
"""
from __future__ import annotations

import sys
from pathlib import Path

from ctranslate2.converters import TransformersConverter
from huggingface_hub import snapshot_download

MODEL = "facebook/nllb-200-distilled-600M"


class _Converter(TransformersConverter):
    """ctranslate2 >= 4.8 passes `dtype=`; transformers 4.47 only knows `torch_dtype=`."""

    def load_model(self, model_class, model_name_or_path, **kwargs):
        if "dtype" in kwargs:
            kwargs["torch_dtype"] = kwargs.pop("dtype")
        return super().load_model(model_class, model_name_or_path, **kwargs)

OUT = Path(__file__).resolve().parents[1] / "artifacts" / "nllb-ct2"


def main() -> None:
    if (OUT / "model.bin").exists():
        print("already prepared:", OUT)
        return
    src = snapshot_download(MODEL, allow_patterns=["*.json", "*.model", "pytorch_model.bin", "*.txt"])
    print("downloaded to", src, flush=True)
    _Converter(src).convert(str(OUT), quantization="int8", force=True)
    # keep the sentencepiece model next to the CT2 weights so serving needs no hub access
    for f in Path(src).glob("sentencepiece.bpe.model"):
        (OUT / f.name).write_bytes(f.read_bytes())
    print("converted to", OUT)


if __name__ == "__main__":
    sys.exit(main())
