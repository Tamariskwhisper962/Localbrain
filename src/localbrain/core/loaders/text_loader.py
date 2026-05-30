"""평문 텍스트/마크다운/코드 로더. (MVP 범위: pdf/docx 는 별도 loader 로 추후 추가)"""
from __future__ import annotations

from pathlib import Path


class TextLoader:
    EXTENSIONS = {
        ".txt", ".md", ".markdown", ".rst", ".log",
        ".py", ".js", ".ts", ".tsx", ".java", ".cs", ".go", ".rb",
        ".json", ".yaml", ".yml", ".toml", ".ini", ".csv",
        ".html", ".css", ".sql",
    }

    def supports(self, path: Path) -> bool:
        return path.suffix.lower() in self.EXTENSIONS

    def load(self, path: Path) -> str:
        return path.read_text(encoding="utf-8", errors="replace")
