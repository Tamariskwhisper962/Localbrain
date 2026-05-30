"""reranker 레지스트리 — config 이름으로 구현체 생성 (lazy import)."""
from __future__ import annotations

from .base import Reranker


def make_reranker(provider: str, model: str, fp16: bool = False) -> Reranker:
    if provider in ("cross-encoder", "sentence-transformers"):
        from .cross_encoder import CrossEncoderReranker

        return CrossEncoderReranker(model, fp16)
    raise ValueError(f"unknown reranker provider: {provider!r}")
