"""Reranker 인터페이스 — query·문서쌍의 관련도 점수 산출의 경계."""
from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class Reranker(Protocol):
    model_id: str

    def rerank(self, query: str, docs: list[str]) -> list[float]:
        """각 문서의 query 관련도 점수(0~1)를 docs 와 같은 순서로 반환."""
        ...
