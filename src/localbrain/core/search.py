"""검색 — 단일 책임: 벡터로 문서 조회 → SearchHit. (질의 로깅은 service/insights 가 담당)"""
from __future__ import annotations

from .embed.base import EmbeddingProvider
from .models import SearchHit
from .store import VectorStore


class Searcher:
    def __init__(self, provider: EmbeddingProvider, store: VectorStore) -> None:
        self._provider = provider
        self._store = store

    def embed_query(self, query: str) -> list[float]:
        return self._provider.embed_texts([query])[0]

    def search_by_vector(self, embedding: list[float], k: int = 5,
                         path_prefix: str | None = None) -> list[SearchHit]:
        # path_prefix 필터는 후처리 — 넉넉히 가져와서 거른다
        fetch = k * 3 if path_prefix else k
        hits: list[SearchHit] = []
        for cid, doc, meta, dist in self._store.query_documents(embedding, fetch):
            source_path = meta.get("source_path", "")
            if path_prefix and not source_path.startswith(path_prefix):
                continue
            hits.append(SearchHit(cid, doc, source_path, score=1.0 - dist, metadata=meta))
        return hits[:k]
