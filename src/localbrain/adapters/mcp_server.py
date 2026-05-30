"""MCP 어댑터 — Claude Code 가 stdio 로 연결해 쓰는 도구들 (FastMCP)."""
from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from ..context import AppContext
from ..services.indexing_service import IndexingService
from ..services.insights_service import InsightsService
from ..services.search_service import SearchService

mcp = FastMCP("localbrain")
_ctx = AppContext()
_indexing = IndexingService(_ctx)
_search = SearchService(_ctx)
_insights = InsightsService(_ctx)


@mcp.tool()
def search(query: str, k: int = 5, path_prefix: str | None = None) -> list[dict]:
    """인덱싱된 문서에서 의미 검색. path_prefix 로 특정 폴더만 제한 가능."""
    return [vars(h) for h in _search.search(query, k, path_prefix)]


@mcp.tool()
def add_path(path: str, globs: str = "*.md,*.txt", recursive: bool = True) -> dict:
    """폴더/파일 경로를 인덱싱 소스로 등록."""
    s = _indexing.add_source(path, tuple(globs.split(",")), recursive)
    return {"source_id": s.source_id, "path": s.path}


@mcp.tool()
def remove_path(source_id: str) -> dict:
    """소스 제거(해당 청크도 삭제)."""
    _indexing.remove_source(source_id)
    return {"removed": source_id}


@mcp.tool()
def list_sources() -> list[dict]:
    """등록된 소스 목록."""
    return [vars(s) for s in _indexing.list_sources()]


@mcp.tool()
def reindex(source_id: str | None = None, rebuild: bool = False) -> list[dict]:
    """변경분 증분 인덱싱 실행. rebuild=True 면 전체 재구축(모델 교체 후 등)."""
    return list(_indexing.run(source_id, rebuild=rebuild))


@mcp.tool()
def stats() -> dict:
    """인덱스 규모·활성 모델·소스 수."""
    return _search.stats()


@mcp.tool()
def query_insights(min_similarity: float = 0.80) -> dict:
    """누적된 사용자 질의를 군집화해 자주 묻는 질문군(FAQ)과 지식공백(무응답·저점수)을 리포트."""
    return _insights.report(min_similarity)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
