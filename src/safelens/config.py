"""Environment-driven configuration; no model initialization at import time."""

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    database_url: str = "postgresql://safelens:safelens@127.0.0.1:5432/safelens"
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    embedding_dim: int = 384
    embed_query_prefix: str = "Represent this sentence for searching relevant passages: "
    llm_provider: str = "openai"
    llm_model: str = "gpt-4o-mini"
    openai_api_key: str = field(default="", repr=False)
    chunk_tokens: int = 500
    chunk_overlap: float = 0.15

    def __post_init__(self):
        if self.embedding_dim <= 0 or not 400 <= self.chunk_tokens <= 600:
            raise ValueError("Embedding dimension must be positive; chunk tokens must be 400..600")
        if not 0 <= self.chunk_overlap < 1:
            raise ValueError("Chunk overlap must be in [0, 1)")

    @property
    def chunk_config(self) -> dict:
        return {
            "tokens": self.chunk_tokens,
            "overlap": self.chunk_overlap,
            "text_construction": "synopsis+all_labeled_narratives; synopsis_per_chunk",
            "lexical_config": "simple",
        }

    @property
    def index_config(self) -> dict:
        return {
            "embedding_model": self.embedding_model,
            "embedding_dim": self.embedding_dim,
            "embed_query_prefix": self.embed_query_prefix,
            "chunk_config": self.chunk_config,
        }

    @classmethod
    def from_env(cls):
        load_dotenv(encoding="utf-8")
        defaults = cls()
        return cls(
            database_url=os.getenv("DATABASE_URL", defaults.database_url),
            embedding_model=os.getenv("EMBEDDING_MODEL", defaults.embedding_model),
            embedding_dim=int(os.getenv("EMBEDDING_DIM", defaults.embedding_dim)),
            embed_query_prefix=os.getenv("EMBED_QUERY_PREFIX", defaults.embed_query_prefix),
            llm_provider=os.getenv("LLM_PROVIDER", defaults.llm_provider),
            llm_model=os.getenv("LLM_MODEL", defaults.llm_model),
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            chunk_tokens=int(os.getenv("CHUNK_TOKENS", defaults.chunk_tokens)),
            chunk_overlap=float(os.getenv("CHUNK_OVERLAP", defaults.chunk_overlap)),
        )
