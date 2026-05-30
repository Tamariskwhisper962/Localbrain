"""도메인 모델 (데이터 구조만). 로직 없음 → 변경에 강함."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Source:
    """인덱싱 대상으로 등록된 경로(폴더/파일)."""
    source_id: str
    path: str
    globs: tuple[str, ...] = ("*.md", "*.txt")
    recursive: bool = True


@dataclass
class FileRecord:
    """증분 추적용 파일 단위 기록."""
    path: str
    hash: str
    mtime: float
    size: int
    chunk_ids: list[str]
    source_id: str


@dataclass
class Chunk:
    id: str
    text: str
    source_path: str
    chunk_index: int
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SearchHit:
    chunk_id: str
    text: str
    source_path: str
    score: float
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ChangeSet:
    """스캔 결과 — 신규/수정/삭제 경로 목록."""
    source_id: str
    new: list[str] = field(default_factory=list)
    modified: list[str] = field(default_factory=list)
    deleted: list[str] = field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        return not (self.new or self.modified or self.deleted)
