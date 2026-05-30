"""변경 감지 — 단일 책임: 디스크 상태 vs file_index 비교 → ChangeSet.

2단계 시그니처: mtime+size 사전필터 → 달라진 것만 content hash 로 확정 (architecture §10.2).
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Iterator

from .file_index import FileIndex
from .loaders.registry import is_supported
from .models import ChangeSet, Source


def iter_files(source: Source) -> Iterator[Path]:
    base = Path(source.path)
    if base.is_file():
        if is_supported(base):
            yield base
        return
    for pattern in source.globs:
        globber = base.rglob if source.recursive else base.glob
        for p in globber(pattern):
            if p.is_file() and is_supported(p):
                yield p


def file_hash(path: Path) -> str:
    h = hashlib.sha1()
    h.update(path.read_bytes())
    return h.hexdigest()


class Scanner:
    def __init__(self, file_index: FileIndex) -> None:
        self._fi = file_index

    def scan(self, source: Source) -> ChangeSet:
        cs = ChangeSet(source_id=source.source_id)
        found: set[str] = set()

        for p in iter_files(source):
            ap = str(p.resolve())
            found.add(ap)
            st = p.stat()
            rec = self._fi.get(ap)
            if rec is None:
                cs.new.append(ap)
            elif rec.mtime == st.st_mtime and rec.size == st.st_size:
                continue  # 사전필터 통과 → 불변 (hash 생략)
            elif rec.hash != file_hash(p):
                cs.modified.append(ap)

        # 삭제 판정은 소스 범위로 한정 → 범위 밖 청크 오삭제 방지
        for ap in self._fi.paths_for_source(source.source_id):
            if ap not in found:
                cs.deleted.append(ap)
        return cs
