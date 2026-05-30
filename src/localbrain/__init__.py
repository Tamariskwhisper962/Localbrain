"""localbrain — 범용 로컬 RAG MCP 도구."""
from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("localbrain-rag")  # PyPI 배포명 (import/명령어는 localbrain)
except PackageNotFoundError:  # 소스에서 직접 실행(미설치) 시
    __version__ = "0.0.0+dev"
