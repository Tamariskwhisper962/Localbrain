"""검색 서비스 — 질의 임베딩 → (후보 검색 → 리랭킹) → 질의 로깅."""
from __future__ import annotations

import sys

from ..context import AppContext
from ..core.models import SearchHit


class SearchService:
    def __init__(self, ctx: AppContext) -> None:
        self._ctx = ctx

    def search(self, query: str, k: int | None = None,
               path_prefix: str | None = None, rerank: bool = True) -> list[SearchHit]:
        cfg = self._ctx.config
        k = k or cfg.search_k
        reranker = self._ctx.reranker if rerank else None

        # reranker 가 있으면 후보를 넉넉히(candidate_k) 뽑아서 재정렬
        fetch = cfg.rerank.candidate_k if reranker else k
        embedding = self._ctx.searcher.embed_query(query)            # 임베딩 1회 계산
        hits = self._ctx.searcher.search_by_vector(embedding, fetch, path_prefix)

        if reranker and hits:
            try:
                scores = reranker.rerank(query, [h.text for h in hits])
                for h, s in zip(hits, scores):
                    h.score = s                                      # 점수를 reranker 관련도로 교체
                hits.sort(key=lambda h: h.score, reverse=True)
            except Exception as e:  # noqa: BLE001 — 리랭커 실패 시 벡터 순서로 폴백
                print(f"[rerank skipped] {e}", file=sys.stderr)

        hits = hits[:k]
        self._ctx.insights.log_query(query, embedding, hits)         # 임베딩 재사용(축 ①)
        return hits

    def stats(self) -> dict:
        return {
            "documents": self._ctx.store.count_documents(),
            "model": self._ctx.provider.model_id,
            "reranker": self._ctx.reranker.model_id if self._ctx.reranker else None,
            "sources": len(self._ctx.sources.list()),
        }
