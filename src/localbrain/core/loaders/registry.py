"""loader 레지스트리 — 경로에 맞는 loader 선택."""
from __future__ import annotations

from pathlib import Path

from .base import Loader
from .text_loader import TextLoader

_LOADERS: list[Loader] = [TextLoader()]


def get_loader(path: Path) -> Loader | None:
    for loader in _LOADERS:
        if loader.supports(path):
            return loader
    return None


def is_supported(path: Path) -> bool:
    return get_loader(path) is not None
