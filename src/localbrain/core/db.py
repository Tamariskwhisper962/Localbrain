"""SQLite 연결·스키마 (단일 책임: DB 부트스트랩). 테이블 접근은 각 store 모듈이 담당."""
from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS sources (
    source_id TEXT PRIMARY KEY,
    path      TEXT NOT NULL,
    globs     TEXT NOT NULL,
    recursive INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS file_index (
    path       TEXT PRIMARY KEY,
    hash       TEXT NOT NULL,
    mtime      REAL NOT NULL,
    size       INTEGER NOT NULL,
    chunk_ids  TEXT NOT NULL,
    source_id  TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_file_source ON file_index(source_id);
CREATE TABLE IF NOT EXISTS queries (
    id        TEXT PRIMARY KEY,
    text      TEXT NOT NULL,
    ts        REAL NOT NULL,
    hit       INTEGER NOT NULL,
    top_score REAL
);
"""


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.executescript(SCHEMA)
    return conn
