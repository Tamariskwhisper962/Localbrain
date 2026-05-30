"""파일 단위 증분 추적 — 단일 책임: file_index 테이블 CRUD."""
from __future__ import annotations

import json
import sqlite3

from .models import FileRecord


class FileIndex:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def get(self, path: str) -> FileRecord | None:
        row = self._conn.execute("SELECT * FROM file_index WHERE path=?", (path,)).fetchone()
        return self._to_record(row) if row else None

    def upsert(self, rec: FileRecord) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO file_index(path,hash,mtime,size,chunk_ids,source_id) "
            "VALUES (?,?,?,?,?,?)",
            (rec.path, rec.hash, rec.mtime, rec.size, json.dumps(rec.chunk_ids), rec.source_id),
        )
        self._conn.commit()

    def delete(self, path: str) -> None:
        self._conn.execute("DELETE FROM file_index WHERE path=?", (path,))
        self._conn.commit()

    def paths_for_source(self, source_id: str) -> list[str]:
        rows = self._conn.execute(
            "SELECT path FROM file_index WHERE source_id=?", (source_id,)
        ).fetchall()
        return [r["path"] for r in rows]

    @staticmethod
    def _to_record(r: sqlite3.Row) -> FileRecord:
        return FileRecord(
            r["path"], r["hash"], r["mtime"], r["size"], json.loads(r["chunk_ids"]), r["source_id"]
        )
