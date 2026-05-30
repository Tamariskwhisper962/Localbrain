"""대안 provider — 로컬 Ollama 데몬 사용. (provider 교체 예시; 기본은 fastembed)"""
from __future__ import annotations

import json
import urllib.request


class OllamaProvider:
    def __init__(self, model: str = "bge-m3", host: str = "http://localhost:11434",
                 fp16: bool = False) -> None:
        # fp16 은 Ollama 서버 설정 사항이므로 여기선 무시(시그니처 호환용).
        self.model_id = f"ollama:{model}"
        self._model = model
        self._host = host.rstrip("/")
        self._dim: int | None = None

    @property
    def dim(self) -> int:
        if self._dim is None:
            self._dim = len(self.embed_texts(["_probe_"])[0])
        return self._dim

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        out: list[list[float]] = []
        for t in texts:
            req = urllib.request.Request(
                f"{self._host}/api/embeddings",
                data=json.dumps({"model": self._model, "prompt": t}).encode(),
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req) as r:
                out.append(json.loads(r.read())["embedding"])
        return out
