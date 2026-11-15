"""Provider contracts only; concrete model integrations belong to later steps."""

from collections.abc import Sequence
from typing import Protocol


class EmbeddingProvider(Protocol):
    """Implementations apply the configured instruction only to queries."""

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]: ...

    def embed_query(self, text: str) -> list[float]: ...

    def count_tokens(self, text: str) -> int: ...


class LLMProvider(Protocol):
    def generate(self, prompt: str) -> str: ...
