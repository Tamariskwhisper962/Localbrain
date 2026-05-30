"""provider 레지스트리 — config 의 이름으로 구현체를 만든다. (lazy import)"""
from __future__ import annotations

from .base import EmbeddingProvider


def make_provider(provider: str, model: str, fp16: bool = False) -> EmbeddingProvider:
    if provider == "fastembed":
        from .fastembed_provider import FastEmbedProvider

        return FastEmbedProvider(model, fp16)
    if provider == "ollama":
        from .ollama_provider import OllamaProvider

        return OllamaProvider(model, fp16=fp16)
    if provider == "sentence-transformers":
        from .st_provider import SentenceTransformerProvider

        return SentenceTransformerProvider(model, fp16)
    raise ValueError(f"unknown embedding provider: {provider!r}")
