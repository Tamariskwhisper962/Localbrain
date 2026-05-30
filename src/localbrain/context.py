"""Composition root — 모든 구성요소를 한 곳에서 조립한다.

어댑터(MCP/CLI/Web)는 이 AppContext 하나만 만들어 services 를 통해 사용한다.
"""
from __future__ import annotations

from .config import Config
from .core.db import connect
from .core.embed.registry import make_provider
from .core.file_index import FileIndex
from .core.indexer import Indexer
from .core.insights import Insights
from .core.rerank.registry import make_reranker
from .core.scanner import Scanner
from .core.search import Searcher
from .core.source_store import SourceStore
from .core.store import VectorStore


class AppContext:
    def __init__(self, config: Config | None = None) -> None:
        self.config = config or Config.load()

        # 임베딩 provider (config 로 교체 가능 — embedding-runtime.md)
        self.provider = make_provider(
            self.config.embedding.provider, self.config.embedding.model, self.config.embedding.fp16
        )

        # 영속 계층
        self.conn = connect(self.config.db_path)
        self.store = VectorStore(self.config.chroma_dir, self.provider.model_id)
        self.file_index = FileIndex(self.conn)
        self.sources = SourceStore(self.conn)

        # 인덱싱 파이프라인 (변경감지 / 적용 분리)
        self.scanner = Scanner(self.file_index)
        self.indexer = Indexer(
            self.provider, self.store, self.file_index,
            self.config.chunk.size, self.config.chunk.overlap,
        )

        # 검색 / 리랭킹 / 인사이트
        self.searcher = Searcher(self.provider, self.store)
        self.reranker = (
            make_reranker(self.config.rerank.provider, self.config.rerank.model,
                          self.config.rerank.fp16)
            if self.config.rerank.enabled else None
        )  # 모델은 첫 rerank 시 lazy 로드
        self.insights = Insights(self.conn, self.store)
