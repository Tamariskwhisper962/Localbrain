"""웹 어댑터 — 로컬 운영 UI 백엔드.

브라우저는 조종판일 뿐, 파일은 이 백엔드(같은 PC)가 제자리에서 읽는다 (ui-review.md).
127.0.0.1 루프백에만 바인딩 → 외부 비노출.
"""
from __future__ import annotations

import asyncio
import json
import queue
import threading
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel

from ...context import AppContext
from ...services.indexing_service import IndexingService
from ...services.insights_service import InsightsService
from ...services.model_service import ModelService
from ...services.search_service import SearchService

app = FastAPI(title="localbrain")
_ctx = AppContext()
_indexing = IndexingService(_ctx)
_search = SearchService(_ctx)
_model = ModelService(_ctx)
_insights = InsightsService(_ctx)
_STATIC = Path(__file__).parent / "static"


@app.get("/")
def index_page():
    return FileResponse(_STATIC / "index.html")


# --- Sources / 파일시스템 탐색 (서버측 = 내 PC) ---
@app.get("/api/fs/list")
def fs_list(path: str = ""):
    base = Path(path) if path else Path.home()
    if not base.exists() or not base.is_dir():
        return JSONResponse({"error": "not a directory"}, status_code=404)
    items = [
        {"name": c.name, "dir": c.is_dir(), "path": str(c)}
        for c in sorted(base.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
    ]
    return {"path": str(base), "parent": str(base.parent), "items": items}


class SourceIn(BaseModel):
    path: str
    globs: str = "*.md,*.txt"
    recursive: bool = True


@app.get("/api/sources")
def get_sources():
    return [vars(s) for s in _indexing.list_sources()]


@app.post("/api/sources")
def add_source(body: SourceIn):
    return vars(_indexing.add_source(body.path, tuple(body.globs.split(",")), body.recursive))


@app.delete("/api/sources/{source_id}")
def delete_source(source_id: str):
    _indexing.remove_source(source_id)
    return {"removed": source_id}


# --- Indexing (진행 SSE) ---
@app.get("/api/index/stream")
def index_stream(source_id: str | None = None, rebuild: bool = False):
    q: queue.Queue = queue.Queue()

    def worker():
        try:
            for ev in _indexing.run(source_id, rebuild=rebuild):
                q.put(ev)
        except Exception as e:  # noqa: BLE001 — UI 로 에러 전달
            q.put({"phase": "error", "message": str(e)})
        finally:
            q.put(None)

    threading.Thread(target=worker, daemon=True).start()

    async def gen():
        while True:
            ev = await asyncio.to_thread(q.get)
            if ev is None:
                break
            yield f"data: {json.dumps(ev, ensure_ascii=False)}\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream")


# --- Search ---
class SearchIn(BaseModel):
    query: str
    k: int | None = None
    path_prefix: str | None = None


@app.post("/api/search")
def search(body: SearchIn):
    return [vars(h) for h in _search.search(body.query, body.k, body.path_prefix)]


@app.get("/api/stats")
def stats():
    return _search.stats()


@app.get("/api/insights")
def insights(min_similarity: float = 0.80):
    return _insights.report(min_similarity)


# --- Model ---
@app.get("/api/model")
def get_model():
    return _model.current()


class ModelIn(BaseModel):
    provider: str
    model: str


@app.post("/api/model/switch")
def switch_model(body: ModelIn):
    return _model.switch(body.provider, body.model)


def main() -> None:
    import os

    import uvicorn

    # 기본은 루프백(외부 비노출). Docker 등에선 LOCALBRAIN_HOST=0.0.0.0 로 개방.
    host = os.environ.get("LOCALBRAIN_HOST", "127.0.0.1")
    port = int(os.environ.get("LOCALBRAIN_PORT", "8765"))
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
