"""CLI 어댑터 — add-source / list-sources / index / search / stats."""
from __future__ import annotations

import argparse
import json
import sys

from .. import __version__
from ..context import AppContext
from ..services.indexing_service import IndexingService
from ..services.insights_service import InsightsService
from ..services.search_service import SearchService


def main(argv: list[str] | None = None) -> int:
    # Windows 콘솔(cp949 등)에서도 한국어/특수문자 출력이 깨지지 않게 UTF-8 로 고정
    for _stream in (sys.stdout, sys.stderr):
        try:
            _stream.reconfigure(encoding="utf-8")
        except Exception:
            pass

    parser = argparse.ArgumentParser(prog="localbrain", description="로컬 RAG MCP 도구")
    parser.add_argument("--version", action="version", version=f"localbrain {__version__}")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_add = sub.add_parser("add-source", help="폴더/파일 경로 등록")
    p_add.add_argument("path")
    p_add.add_argument("--globs", default="*.md,*.txt")
    p_add.add_argument("--no-recursive", action="store_true")

    sub.add_parser("list-sources", help="등록된 소스 목록")

    p_idx = sub.add_parser("index", help="증분 인덱싱 실행")
    p_idx.add_argument("--source-id", default=None)
    p_idx.add_argument("--rebuild", action="store_true", help="전체 재구축(모델 교체 후 등)")

    p_search = sub.add_parser("search", help="의미 검색")
    p_search.add_argument("query")
    p_search.add_argument("-k", type=int, default=None)
    p_search.add_argument("--path-prefix", default=None)
    p_search.add_argument("--no-rerank", action="store_true", help="리랭킹 끄고 벡터 순서로")

    sub.add_parser("stats", help="인덱스 상태")

    p_ins = sub.add_parser("insights", help="질의 클러스터링(FAQ)·지식공백 리포트")
    p_ins.add_argument("--min-similarity", type=float, default=0.80)

    args = parser.parse_args(argv)
    ctx = AppContext()
    indexing = IndexingService(ctx)
    search = SearchService(ctx)
    insights = InsightsService(ctx)

    if args.cmd == "add-source":
        src = indexing.add_source(args.path, tuple(args.globs.split(",")), not args.no_recursive)
        print(f"added [{src.source_id}] {src.path}")
    elif args.cmd == "list-sources":
        for s in indexing.list_sources():
            print(f"{s.source_id}  {s.path}  ({','.join(s.globs)})")
    elif args.cmd == "index":
        for ev in indexing.run(args.source_id, rebuild=args.rebuild):
            print(json.dumps(ev, ensure_ascii=False))
    elif args.cmd == "search":
        hits = search.search(args.query, args.k, args.path_prefix, rerank=not args.no_rerank)
        if not hits:
            print("(결과 없음)")
        for h in hits:
            print(f"[{h.score:.3f}] {h.source_path}\n  {h.text[:140].strip()}...")
    elif args.cmd == "stats":
        print(json.dumps(search.stats(), ensure_ascii=False, indent=2))
    elif args.cmd == "insights":
        report = insights.report(args.min_similarity)
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
