"""Loader 인터페이스 — 포맷 확장의 경계."""
from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable


@runtime_checkable
class Loader(Protocol):
    def supports(self, path: Path) -> bool:
        ...

    def load(self, path: Path) -> str:
        ...
