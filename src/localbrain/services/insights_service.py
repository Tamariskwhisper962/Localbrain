"""인사이트 서비스 — 질의 클러스터링(FAQ)·지식공백 리포트 진입점 (축 ②)."""
from __future__ import annotations

from ..context import AppContext


class InsightsService:
    def __init__(self, ctx: AppContext) -> None:
        self._ctx = ctx

    def report(self, min_similarity: float = 0.80, gap_score: float = 0.5) -> dict:
        return self._ctx.insights.cluster(min_similarity=min_similarity, gap_score=gap_score)
