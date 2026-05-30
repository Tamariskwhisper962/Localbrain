"""Cross-Encoder reranker (sentence-transformers). 기본: BAAI/bge-reranker-v2-m3.

모델은 첫 rerank 호출 시 lazy 로드 → 시작·stats 는 비용 없음.
참고: sentence-transformers 의 CrossEncoder.predict 는 이미 0~1 관련도 점수를 반환하므로
추가 활성함수(sigmoid)를 씌우면 안 된다(이중 적용 → 점수가 0.5로 뭉개짐).
"""
from __future__ import annotations


class CrossEncoderReranker:
    def __init__(self, model: str = "BAAI/bge-reranker-v2-m3", fp16: bool = False) -> None:
        self.model_id = f"ce:{model}"
        self._name = model
        self._fp16 = fp16
        self._model = None  # lazy

    def _ensure(self) -> None:
        if self._model is None:
            import torch
            from sentence_transformers import CrossEncoder

            self._model = CrossEncoder(self._name)
            if self._fp16 and torch.cuda.is_available():  # GPU 에서만 half
                self._model.model.half()

    def rerank(self, query: str, docs: list[str]) -> list[float]:
        if not docs:
            return []
        self._ensure()
        scores = self._model.predict([(query, d) for d in docs])
        return [float(s) for s in scores]
