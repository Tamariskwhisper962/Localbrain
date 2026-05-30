"""자가개선 루프 — 단일 책임: 질의 로깅 + 질의 임베딩 적재 (축 ①).

클러스터링(축 ②, FAQ/지식공백)은 Phase 2. 질의 텍스트·임베딩을 미리 쌓아둔다.
"""
from __future__ import annotations

import sqlite3
import time
import uuid

from .clustering import cluster_embeddings, medoid_index
from .models import SearchHit
from .store import VectorStore


class Insights:
    def __init__(self, conn: sqlite3.Connection, store: VectorStore) -> None:
        self._conn = conn
        self._store = store

    def log_query(self, text: str, embedding: list[float], hits: list[SearchHit]) -> None:
        qid = uuid.uuid4().hex
        top = hits[0].score if hits else None
        self._conn.execute(
            "INSERT INTO queries(id, text, ts, hit, top_score) VALUES (?,?,?,?,?)",
            (qid, text, time.time(), int(bool(hits)), top),
        )
        self._conn.commit()
        self._store.add_query(qid, embedding, text, {"hit": bool(hits), "top_score": top or 0.0})

    def cluster(self, min_similarity: float = 0.80, min_queries: int = 3,
                gap_score: float = 0.5) -> dict:
        """질의 임베딩을 군집화해 FAQ(인기 질문군)와 지식공백(무응답·저점수)을 리포트한다."""
        ids, vectors, texts, metas = self._store.all_queries()
        total = len(ids)
        if total < min_queries:
            return {"total_queries": total, "clusters": [], "gaps": [],
                    "note": f"질의가 {total}건 — 군집화에 최소 {min_queries}건 권장"}

        labels = cluster_embeddings(vectors, min_similarity)
        groups: dict[int, list[int]] = {}
        for i, lab in enumerate(labels):
            groups.setdefault(lab, []).append(i)

        clusters = []
        for idxs in groups.values():
            rep = medoid_index(vectors, idxs)
            scores = [float(metas[i].get("top_score", 0.0)) for i in idxs]
            misses = sum(1 for i in idxs if not metas[i].get("hit", True))
            clusters.append({
                "size": len(idxs),
                "representative": texts[rep],
                "samples": [texts[i] for i in idxs[:5]],
                "avg_top_score": round(sum(scores) / len(scores), 3),
                "miss_rate": round(misses / len(idxs), 2),
            })
        clusters.sort(key=lambda c: c["size"], reverse=True)

        # 지식공백: 검색 실패(hit=false)거나 최고점수가 낮은 질의
        gaps = [
            {"text": texts[i],
             "top_score": float(metas[i].get("top_score", 0.0)),
             "hit": bool(metas[i].get("hit", False))}
            for i in range(total)
            if not metas[i].get("hit", True) or float(metas[i].get("top_score", 0.0)) < gap_score
        ]
        gaps.sort(key=lambda g: g["top_score"])
        return {"total_queries": total, "clusters": clusters, "gaps": gaps[:20]}
