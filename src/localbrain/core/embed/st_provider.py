"""대안 provider — sentence-transformers (인프로세스, PyTorch). 옵션 의존성 [st]."""
from __future__ import annotations


class SentenceTransformerProvider:
    def __init__(self, model: str = "intfloat/multilingual-e5-large", fp16: bool = False) -> None:
        import torch
        from sentence_transformers import SentenceTransformer

        self._model = SentenceTransformer(model)
        if fp16 and torch.cuda.is_available():  # GPU 에서만 half precision
            self._model.half()
        self.model_id = f"st:{model}"
        self._dim: int | None = None

    @property
    def dim(self) -> int:
        if self._dim is None:
            # 신 메서드(get_embedding_dimension) 우선 → 없으면 구 메서드. (FutureWarning 회피)
            get_dim = getattr(self._model, "get_embedding_dimension", None) \
                or self._model.get_sentence_embedding_dimension
            self._dim = int(get_dim())
        return self._dim

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        vecs = self._model.encode(texts, normalize_embeddings=True)
        return [list(map(float, v)) for v in vecs]
