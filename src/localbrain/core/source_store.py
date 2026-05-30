"""등록된 소스(경로) 관리 — 단일 책임: sources 테이블 CRUD."""
from __future__ import annotations

import sqlite3

from .models import Source


class SourceStore:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def add(self, source: Source) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO sources(source_id, path, globs, recursive) VALUES (?,?,?,?)",
            (source.source_id, source.path, ",".join(source.globs), int(source.recursive)),
        )
        self._conn.commit()

    def remove(self, source_id: str) -> None:
        self._conn.execute("DELETE FROM sources WHERE source_id=?", (source_id,))
        self._conn.commit()

    def get(self, source_id: str) -> Source | None:
        row = self._conn.execute("SELECT * FROM sources WHERE source_id=?", (source_id,)).fetchone()
        return self._to_source(row) if row else None

    def list(self) -> list[Source]:
        rows = self._conn.execute("SELECT * FROM sources ORDER BY path").fetchall()
        return [self._to_source(r) for r in rows]

    @staticmethod
    def _to_source(r: sqlite3.Row) -> Source:
        return Source(r["source_id"], r["path"], tuple(r["globs"].split(",")), bool(r["recursive"]))
