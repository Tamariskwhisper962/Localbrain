"""벡터 저장소 (Chroma 래퍼) — 단일 책임: 벡터 add/delete/query.

모델별 컬렉션(docs__/queries__)을 분리해 모델 교체 시 벡터가 섞이지 않게 한다 (architecture §9).
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any


def _safe(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]", "_", name)


class VectorStore:
    def __init__(self, persist_dir: Path, model_id: str) -> None:
        import chromadb

        persist_dir.mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(path=str(persist_dir))
        tag = _safe(model_id)
        # 코사인 space → distance = 1 - 코사인유사도 → score(1-distance)가 코사인 유사도(해석 용이).
        cosine = {"hnsw:space": "cosine"}
        self._docs = self._client.get_or_create_collection(f"docs__{tag}", metadata=cosine)
        self._queries = self._client.get_or_create_collection(f"queries__{tag}", metadata=cosine)

    def add_documents(self, ids: list[str], embeddings: list[list[float]],
                      texts: list[str], metadatas: list[dict[str, Any]]) -> None:
        if ids:
            self._docs.add(ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas)

    def delete_documents(self, ids: list[str]) -> None:
        if ids:
            self._docs.delete(ids=ids)

    def query_documents(self, embedding: list[float], k: int,
                        where: dict | None = None) -> list[tuple[str, str, dict, float]]:
        res = self._docs.query(query_embeddings=[embedding], n_results=k, where=where)
        if not res["ids"] or not res["ids"][0]:
            return []
        return [
            (cid, doc, meta or {}, dist)
            for cid, doc, meta, dist in zip(
                res["ids"][0], res["documents"][0], res["metadatas"][0], res["distances"][0]
            )
        ]

    def add_query(self, qid: str, embedding: list[float], text: str, metadata: dict[str, Any]) -> None:
        self._queries.add(ids=[qid], embeddings=[embedding], documents=[text], metadatas=[metadata])

    def all_queries(self) -> tuple[list[str], list[list[float]], list[str], list[dict]]:
        """저장된 모든 질의(임베딩 포함) — 클러스터링용.

        주의: Chroma 의 get(include=["embeddings"]) 는 numpy ndarray 를 돌려주므로
        `or []` 같은 truthiness 평가를 쓰면 ValueError(ambiguous) 가 난다 → None 체크로 처리.
        """
        res = self._queries.get(include=["embeddings", "documents", "metadatas"])
        raw = res.get("embeddings")
        embeddings = [list(map(float, e)) for e in raw] if raw is not None else []
        return (
            res.get("ids") or [],
            embeddings,
            list(res.get("documents") or []),
            list(res.get("metadatas") or []),
        )

    def count_documents(self) -> int:
        return self._docs.count()
