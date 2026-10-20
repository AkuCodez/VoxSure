from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

import ctranslate2
import sentencepiece as spm

from ..core.languages import nllb_code

_SENT = re.compile(r"(?<=[.!?।])\s+")


class Translator:
    """NLLB-200 distilled 600M (int8, CTranslate2) any<->English translation, CPU."""

    def __init__(self, model_dir: Path, threads: int = 4):
        self.dir = Path(model_dir)
        self.model = ctranslate2.Translator(str(self.dir), device="cpu", compute_type="int8", intra_threads=threads)
        self.sp = spm.SentencePieceProcessor()
        self.sp.load(str(self.dir / "sentencepiece.bpe.model"))

    def _translate_sentences(self, sentences: list[str], src: str, tgt: str) -> list[str]:
        toks = [[src] + self.sp.encode(s, out_type=str) + ["</s>"] for s in sentences]
        res = self.model.translate_batch(toks, target_prefix=[[tgt]] * len(toks), beam_size=3,
                                         max_decoding_length=256, repetition_penalty=1.1)
        out = []
        for r in res:
            pieces = r.hypotheses[0]
            if pieces and pieces[0] == tgt:
                pieces = pieces[1:]
            out.append(self.sp.decode(pieces))
        return out

    def translate(self, text: str, src_iso: str, tgt_iso: str) -> str:
        if src_iso == tgt_iso:
            return text
        src, tgt = nllb_code(src_iso), nllb_code(tgt_iso)
        if not src or not tgt:
            return text
        return self._cached(text, src, tgt)

    @lru_cache(maxsize=2048)
    def _cached(self, text: str, src: str, tgt: str) -> str:
        sentences = [s for s in _SENT.split(text.strip()) if s]
        return " ".join(self._translate_sentences(sentences, src, tgt)) if sentences else text
