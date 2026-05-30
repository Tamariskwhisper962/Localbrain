"""인프로세스 ONNX 임베딩 (fastembed) — 외부 데몬 불필요. 권장 provider.

모델은 첫 embed_texts 호출 시 lazy 로드 → AppContext/MCP 핸드셰이크는 즉시.
"""
from __future__ import annotations


class FastEmbedProvider:
    def __init__(self, model: str = "intfloat/multilingual-e5-large", fp16: bool = False) -> None:
        # fp16 은 ONNX 경로에 직접 적용되지 않으므로 무시(시그니처 호환용).
        self.model_id = f"fastembed:{model}"  # 모델 로드 없이 식별자 확보(컬렉션 명명용)
        self._name = model
        self._model = None  # lazy
        self._dim: int | None = None

    def _ensure(self) -> None:
        if self._model is None:
            from fastembed import TextEmbedding

            self._model = TextEmbedding(model_name=self._name)

    @property
    def dim(self) -> int:
        if self._dim is None:
            self._dim = len(self.embed_texts(["_probe_"])[0])
        return self._dim

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        self._ensure()
        return [list(map(float, v)) for v in self._model.embed(texts)]
