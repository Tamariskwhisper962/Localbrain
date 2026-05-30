"""클러스터링 알고리즘 — 단일 책임: 벡터 → 라벨 / 대표(medoid) 산출.

기본은 numpy 만으로 도는 **그리디 코사인-임계 응집**(소규모 질의 집합에 적합, 무의존).
대규모/정교함이 필요하면 이 모듈만 HDBSCAN 구현으로 교체하면 된다 (architecture §5).
"""
from __future__ import annotations


def cluster_embeddings(vectors: list[list[float]], min_similarity: float = 0.80) -> list[int]:
    """각 벡터에 클러스터 라벨을 부여한다. 인접 평균 유사도가 임계 이상이면 같은 군집."""
    import numpy as np

    if not vectors:
        return []
    X = np.asarray(vectors, dtype="float32")
    norms = np.linalg.norm(X, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    Xn = X / norms

    labels: list[int] = [-1] * len(Xn)
    sums: list[np.ndarray] = []   # 군집별 벡터 합
    counts: list[int] = []        # 군집별 멤버 수
    for i, v in enumerate(Xn):
        best, best_sim = -1, -1.0
        for c in range(len(sums)):
            centroid = sums[c] / counts[c]
            n = np.linalg.norm(centroid) or 1.0
            sim = float(np.dot(v, centroid / n))
            if sim > best_sim:
                best_sim, best = sim, c
        if best_sim >= min_similarity:
            labels[i] = best
            sums[best] += v
            counts[best] += 1
        else:
            labels[i] = len(sums)
            sums.append(v.copy())
            counts.append(1)
    return labels


def medoid_index(vectors: list[list[float]], indices: list[int]) -> int:
    """군집 내에서 다른 멤버와 평균 유사도가 가장 높은 대표(medoid)의 전역 인덱스."""
    import numpy as np

    if len(indices) == 1:
        return indices[0]
    X = np.asarray([vectors[i] for i in indices], dtype="float32")
    norms = np.linalg.norm(X, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    Xn = X / norms
    sims = Xn @ Xn.T
    avg = (sims.sum(axis=1) - 1.0) / (len(indices) - 1)
    return indices[int(avg.argmax())]
