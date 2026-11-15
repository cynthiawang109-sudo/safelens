"""Thin embedding/LLM provider contracts; local embeddings live in embed.py."""

from collections.abc import Sequence
from typing import Any, Protocol


class EmbeddingProvider(Protocol):
    """Implementations apply the configured instruction only to queries."""

    tokenizer: Any
    max_tokens: int
    dimension: int

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]: ...

    def embed_query(self, text: str) -> list[float]: ...

    def count_tokens(self, text: str) -> int: ...


class LLMProvider(Protocol):
    def generate(self, prompt: str) -> str: ...
