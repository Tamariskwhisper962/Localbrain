"""인덱싱 서비스 — 소스 관리 + 증분 인덱싱 실행(진행 이벤트 스트림)."""
from __future__ import annotations

import uuid
from typing import Iterator

from ..context import AppContext
from ..core.models import Source


class IndexingService:
    def __init__(self, ctx: AppContext) -> None:
        self._ctx = ctx

    def add_source(self, path: str, globs: tuple[str, ...] = ("*.md", "*.txt"),
                   recursive: bool = True) -> Source:
        src = Source(uuid.uuid4().hex[:8], str(path), tuple(globs), recursive)
        self._ctx.sources.add(src)
        return src

    def remove_source(self, source_id: str) -> None:
        # 소스에 속한 모든 파일의 청크 제거 후 소스 삭제
        for ap in self._ctx.file_index.paths_for_source(source_id):
            rec = self._ctx.file_index.get(ap)
            if rec:
                self._ctx.store.delete_documents(rec.chunk_ids)
            self._ctx.file_index.delete(ap)
        self._ctx.sources.remove(source_id)

    def list_sources(self) -> list[Source]:
        return self._ctx.sources.list()

    def run(self, source_id: str | None = None, rebuild: bool = False) -> Iterator[dict]:
        """증분 인덱싱 실행. source_id 가 없으면 전체 소스. dict 진행 이벤트를 yield.

        rebuild=True 면 해당 소스의 file_index 기록을 비워 전부 다시 임베딩한다
        (모델 교체 후 새 컬렉션 채우기 등).
        """
        sources = [self._ctx.sources.get(source_id)] if source_id else self._ctx.sources.list()
        for src in filter(None, sources):
            if rebuild:
                for ap in self._ctx.file_index.paths_for_source(src.source_id):
                    self._ctx.file_index.delete(ap)
            cs = self._ctx.scanner.scan(src)
            yield {
                "phase": "scan", "source_id": src.source_id,
                "new": len(cs.new), "modified": len(cs.modified), "deleted": len(cs.deleted),
            }
            yield from self._ctx.indexer.apply(src, cs)
