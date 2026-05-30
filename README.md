# localbrain

[![PyPI](https://img.shields.io/pypi/v/localbrain-rag.svg)](https://pypi.org/project/localbrain-rag/)
[![Python](https://img.shields.io/pypi/pyversions/localbrain-rag.svg)](https://pypi.org/project/localbrain-rag/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![CI](https://github.com/sinwoo0225/Localbrain/actions/workflows/ci.yml/badge.svg)](https://github.com/sinwoo0225/Localbrain/actions/workflows/ci.yml)

**Local-first general-purpose RAG** — point it at folders/files, index them, and search by meaning
through an **MCP server** (for Claude Code etc.), a **CLI**, and a **web console**.
Everything runs on your machine; generation is done by your MCP client (e.g. Claude), so localbrain
only needs a small **embedding** model — no local LLM, no Ollama daemon required.

- 🔎 Semantic search + Cross-Encoder **reranking**
- 🧩 **MCP** tools (`search`, `add_path`, `reindex`, `query_insights`, …)
- 🖥️ Web console: source management · manual indexing (live progress) · search test · model swap
- ♻️ Incremental indexing (only changed files), swappable embedding model
- 📈 Query **clustering insights** (FAQs & knowledge gaps) — a self-improving loop
- 🔒 Fully local; pluggable providers (fastembed ONNX / sentence-transformers / Ollama)

## Install

> Installed as **`localbrain-rag`** on PyPI; the command and import stay **`localbrain`**.

### Default (CPU, no extra setup)
```bash
pip install localbrain-rag
```
Uses **fastembed** (ONNX, multilingual e5) — works on CPU with no PyTorch. Good enough to start.

### Best quality (GPU + bge-m3) — recommended
1. Install a CUDA build of PyTorch matching your GPU (example: CUDA 12.6):
   ```bash
   pip install torch --index-url https://download.pytorch.org/whl/cu126
   ```
2. Install localbrain with sentence-transformers:
   ```bash
   pip install "localbrain-rag[st]"
   ```
3. Point the config at bge-m3 (see [Configuration](#configuration)). Models auto-download on first use.

> No NVIDIA GPU? Skip step 1 — `pip install "localbrain-rag[st]"` installs a CPU PyTorch and still works (slower).

## Quick start

```bash
# CLI
localbrain add-source "C:\Users\me\notes" --globs "*.md,*.txt"
localbrain index
localbrain search "what did we decide about delivery delays"
localbrain insights          # FAQ clusters + knowledge gaps
localbrain stats
localbrain --version

# Web console  →  http://127.0.0.1:8765
localbrain-web

# MCP server (stdio) — register with Claude Code
localbrain-mcp
```

## Configuration

Config lives at `~/.localbrain/config.json` (override the dir with `LOCALBRAIN_HOME`).
Data (SQLite + Chroma vectors + model-by-model collections) also lives under `~/.localbrain`.

```json
{
  "embedding": { "provider": "sentence-transformers", "model": "BAAI/bge-m3", "fp16": false },
  "chunk": { "size": 1000, "overlap": 150 },
  "rerank": { "enabled": true, "provider": "cross-encoder",
              "model": "BAAI/bge-reranker-v2-m3", "candidate_k": 30, "fp16": false },
  "search_k": 5
}
```

- **Swap models freely** — change `embedding.model`, then `localbrain index --rebuild` (text is kept, so it
  re-embeds without re-reading files). Each model uses its own vector collection (cosine distance).
- **`fp16: true`** halves VRAM and speeds up inference **on GPU** (ignored on CPU). Handy for ~6 GB cards.
- **Reranking** improves accuracy; scores become Cross-Encoder relevance (≈0.8+ strong match, ≈0 none).

## Models & first run

First search/index downloads models from Hugging Face into the HF cache (`HF_HOME`):
bge-m3 (~2 GB) + bge-reranker-v2-m3 (~2 GB). Subsequent runs are cached/offline.
fastembed default models are much smaller.

## ⚠️ One process owns writes

The web server and CLI share the same on-disk vector store. **ChromaDB does not reflect writes made
by another process while a server is running.** So:

- Index from the **web console** (Indexing tab), **or**
- stop `localbrain-web` → run `localbrain index` → restart the server.

Don't run `localbrain index` while `localbrain-web` is up — the running server won't see the new docs.

## Docker (optional, server scenario)

A container only sees **mounted volumes**, so the "browse & index any local folder" UX is limited —
use Docker to serve a **mounted documents folder**. GPU works via NVIDIA Container Toolkit (Windows: Docker
Desktop + WSL2). See `Dockerfile` / `docker-compose.yml`:

```bash
DOCS_DIR=/path/to/docs docker compose up --build   # http://localhost:8765 ; add /docs as a source
```

## Architecture

```
core/        pure library (single-responsibility modules: ingest, embed, rerank, store, search, insights)
services/    orchestration (indexing / search / insights / model)
adapters/    thin entry points: cli · mcp_server · web   (all share core via context.py)
```

## License

MIT — see [LICENSE](LICENSE). Design notes in [`docs/spec/`](docs/spec/README.md).
