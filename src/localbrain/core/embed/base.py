"""EmbeddingProvider 인터페이스 — 모델 교체의 경계."""
from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class EmbeddingProvider(Protocol):
    model_id: str  # 예: "fastembed:intfloat/multilingual-e5-large" — 컬렉션 버전 키
    dim: int       # 벡터 차원

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        ...
