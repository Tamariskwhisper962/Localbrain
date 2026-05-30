"""ChangeSet 적용 — 단일 책임: load→chunk→embed→store + file_index 갱신, 진행 이벤트 yield."""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Iterator

from .chunking import chunk_text
from .embed.base import EmbeddingProvider
from .file_index import FileIndex
from .loaders.registry import get_loader
from .models import ChangeSet, FileRecord, Source
from .scanner import file_hash
from .store import VectorStore


def _path_key(ap: str) -> str:
    return hashlib.sha1(ap.encode()).hexdigest()[:12]


class Indexer:
    def __init__(self, provider: EmbeddingProvider, store: VectorStore,
                 file_index: FileIndex, chunk_size: int, overlap: int) -> None:
        self._provider = provider
        self._store = store
        self._fi = file_index
        self._size = chunk_size
        self._overlap = overlap

    def apply(self, source: Source, cs: ChangeSet) -> Iterator[dict]:
        targets = cs.new + cs.modified
        total = len(targets) + len(cs.deleted)
        done = 0

        for ap in cs.deleted:
            rec = self._fi.get(ap)
            if rec:
                self._store.delete_documents(rec.chunk_ids)
                self._fi.delete(ap)
            done += 1
            yield {"phase": "delete", "path": ap, "done": done, "total": total}

        for ap in targets:
            old = self._fi.get(ap)
            if old:  # 수정: 옛 청크 먼저 제거
                self._store.delete_documents(old.chunk_ids)
            self._index_file(ap, source.source_id)
            done += 1
            yield {"phase": "index", "path": ap, "done": done, "total": total}

        yield {"phase": "done", "done": done, "total": total}

    def _index_file(self, ap: str, source_id: str) -> None:
        path = Path(ap)
        loader = get_loader(path)
        if loader is None:
            return
        st = path.stat()
        chunks = chunk_text(loader.load(path), self._size, self._overlap)
        if not chunks:
            self._fi.upsert(FileRecord(ap, file_hash(path), st.st_mtime, st.st_size, [], source_id))
            return
        key = _path_key(ap)
        ids = [f"{key}-{i}" for i in range(len(chunks))]
        embeddings = self._provider.embed_texts(chunks)
        metas = [
            {"source_path": ap, "chunk_index": i, "file_type": path.suffix.lower()}
            for i in range(len(chunks))
        ]
        self._store.add_documents(ids, embeddings, chunks, metas)
        self._fi.upsert(FileRecord(ap, file_hash(path), st.st_mtime, st.st_size, ids, source_id))
