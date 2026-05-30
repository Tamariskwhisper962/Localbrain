"""설정 — 데이터 경로 / 임베딩 provider / 청킹 파라미터. (단일 책임: 설정 로드·저장)"""
from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path


def _home() -> Path:
    override = os.environ.get("LOCALBRAIN_HOME")
    return Path(override) if override else Path.home() / ".localbrain"


@dataclass
class EmbeddingConfig:
    # 기본값은 추가 설치 없이 동작하는 fastembed 다국어 모델.
    # 더 강한 한국어 품질은 [st] 설치 후 provider="sentence-transformers", model="BAAI/bge-m3".
    provider: str = "fastembed"
    model: str = "intfloat/multilingual-e5-large"
    fp16: bool = False  # GPU 에서만 의미 (VRAM 절감·속도). CPU 에서는 무시.


@dataclass
class ChunkConfig:
    size: int = 1000
    overlap: int = 150


@dataclass
class RerankConfig:
    enabled: bool = True
    provider: str = "cross-encoder"
    model: str = "BAAI/bge-reranker-v2-m3"
    candidate_k: int = 30  # 벡터로 뽑아 reranker 에 넘길 후보 수
    fp16: bool = False      # GPU 에서만 의미. CPU 에서는 무시.


@dataclass
class Config:
    home: Path = field(default_factory=_home)
    embedding: EmbeddingConfig = field(default_factory=EmbeddingConfig)
    chunk: ChunkConfig = field(default_factory=ChunkConfig)
    rerank: RerankConfig = field(default_factory=RerankConfig)
    search_k: int = 5

    @property
    def db_path(self) -> Path:
        return self.home / "localbrain.db"

    @property
    def chroma_dir(self) -> Path:
        return self.home / "chroma"

    @property
    def config_path(self) -> Path:
        return self.home / "config.json"

    @classmethod
    def load(cls) -> "Config":
        cfg = cls()
        cfg.home.mkdir(parents=True, exist_ok=True)
        if cfg.config_path.exists():
            data = json.loads(cfg.config_path.read_text("utf-8"))
            if data.get("embedding"):
                cfg.embedding = EmbeddingConfig(**data["embedding"])
            if data.get("chunk"):
                cfg.chunk = ChunkConfig(**data["chunk"])
            if data.get("rerank"):
                cfg.rerank = RerankConfig(**data["rerank"])
            cfg.search_k = data.get("search_k", cfg.search_k)
        return cfg

    def save(self) -> None:
        self.home.mkdir(parents=True, exist_ok=True)
        self.config_path.write_text(
            json.dumps(
                {
                    "embedding": asdict(self.embedding),
                    "chunk": asdict(self.chunk),
                    "rerank": asdict(self.rerank),
                    "search_k": self.search_k,
                },
                ensure_ascii=False,
                indent=2,
            ),
            "utf-8",
        )
