"""모델 서비스 — 활성 임베딩 모델 조회/교체.

MVP: config 갱신 + "재시작 후 reindex" 안내. 원자적 재구축은 Phase 후속 (architecture §9).
"""
from __future__ import annotations

from ..context import AppContext


class ModelService:
    def __init__(self, ctx: AppContext) -> None:
        self._ctx = ctx

    def current(self) -> dict:
        return {"model_id": self._ctx.provider.model_id, "dim": self._ctx.provider.dim}

    def switch(self, provider: str, model: str) -> dict:
        cfg = self._ctx.config
        cfg.embedding.provider = provider
        cfg.embedding.model = model
        cfg.save()
        return {
            "status": "config-updated",
            "model": f"{provider}:{model}",
            "note": "재시작 후 `localbrain index --rebuild` 로 새 모델 컬렉션을 구축하세요 (architecture §9).",
        }
