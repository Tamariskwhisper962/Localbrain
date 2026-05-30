"""인프로세스 ONNX 임베딩 (fastembed) — 외부 데몬 불필요. 권장 provider."""
from __future__ import annotations


class FastEmbedProvider:
    def __init__(self, model: str = "intfloat/multilingual-e5-large", fp16: bool = False) -> None:
        # fp16 은 ONNX 경로에 직접 적용되지 않으므로 무시(시그니처 호환용).
        from fastembed import TextEmbedding

        self._model = TextEmbedding(model_name=model)
        self.model_id = f"fastembed:{model}"
        self._dim: int | None = None

    @property
    def dim(self) -> int:
        if self._dim is None:
            self._dim = len(self.embed_texts(["_probe_"])[0])
        return self._dim

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [list(map(float, v)) for v in self._model.embed(texts)]
