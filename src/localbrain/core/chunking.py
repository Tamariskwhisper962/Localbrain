"""청킹 — 문단 우선 그리디 분할 + 인접 청크 overlap. (단일 책임: 텍스트 → 청크)"""
from __future__ import annotations


def chunk_text(text: str, size: int = 1000, overlap: int = 150) -> list[str]:
    text = text.strip()
    if not text:
        return []

    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []
    buf = ""
    for p in paragraphs:
        if len(buf) + len(p) + 2 <= size:
            buf = f"{buf}\n\n{p}" if buf else p
            continue
        if buf:
            chunks.append(buf)
            buf = ""
        if len(p) <= size:
            buf = p
        else:  # 한 문단이 size 보다 크면 문자 윈도우로 분할
            step = max(1, size - overlap)
            for i in range(0, len(p), step):
                chunks.append(p[i:i + size])
    if buf:
        chunks.append(buf)

    if overlap > 0 and len(chunks) > 1:  # 인접 청크 앞에 이전 꼬리를 덧붙여 문맥 연결
        merged = [chunks[0]]
        for prev, cur in zip(chunks, chunks[1:]):
            merged.append(f"{prev[-overlap:]}\n{cur}")
        return merged
    return chunks
