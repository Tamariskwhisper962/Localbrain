"""클러스터링 알고리즘 단위 테스트 (numpy 만 필요).

실행: pip install -e . && pip install pytest numpy && pytest
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from localbrain.core.clustering import cluster_embeddings, medoid_index  # noqa: E402


def test_two_clear_groups():
    # 좌측(1,0 근처) 3개 + 우측(0,1 근처) 2개 → 군집 2개
    vecs = [
        [1.0, 0.0], [0.98, 0.02], [0.95, 0.05],
        [0.0, 1.0], [0.03, 0.97],
    ]
    labels = cluster_embeddings(vecs, min_similarity=0.9)
    assert len({labels[0], labels[1], labels[2]}) == 1          # 좌측 한 군집
    assert len({labels[3], labels[4]}) == 1                      # 우측 한 군집
    assert labels[0] != labels[3]                                # 서로 다른 군집
    assert len(set(labels)) == 2


def test_singletons_when_dissimilar():
    vecs = [[1.0, 0.0], [0.0, 1.0]]
    labels = cluster_embeddings(vecs, min_similarity=0.9)
    assert len(set(labels)) == 2


def test_medoid_is_member():
    vecs = [[1.0, 0.0], [0.9, 0.1], [0.8, 0.2]]
    idx = medoid_index(vecs, [0, 1, 2])
    assert idx in (0, 1, 2)


def test_empty():
    assert cluster_embeddings([]) == []
