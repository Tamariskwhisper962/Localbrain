"""대안 provider — sentence-transformers (인프로세스, PyTorch). 옵션 의존성 [st].

모델은 첫 embed_texts/dim 접근 시 lazy 로드 → AppContext/MCP 핸드셰이크는 즉시.
"""
from __future__ import annotations


class SentenceTransformerProvider:
    def __init__(self, model: str = "intfloat/multilingual-e5-large", fp16: bool = False) -> None:
        self.model_id = f"st:{model}"  # 모델 로드 없이 식별자 확보(컬렉션 명명용)
        self._name = model
        self._fp16 = fp16
        self._model = None  # lazy
        self._dim: int | None = None

    def _ensure(self) -> None:
        if self._model is None:
            import torch
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self._name)
            if self._fp16 and torch.cuda.is_available():  # GPU 에서만 half precision
                self._model.half()

    @property
    def dim(self) -> int:
        if self._dim is None:
            self._ensure()
            # 신 메서드(get_embedding_dimension) 우선 → 없으면 구 메서드. (FutureWarning 회피)
            get_dim = getattr(self._model, "get_embedding_dimension", None) \
                or self._model.get_sentence_embedding_dimension
            self._dim = int(get_dim())
        return self._dim

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        self._ensure()
        vecs = self._model.encode(texts, normalize_embeddings=True)
        return [list(map(float, v)) for v in vecs]
