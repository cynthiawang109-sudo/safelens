"""Environment-driven configuration; no model initialization at import time."""

import math
import os
from dataclasses import dataclass, field

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    database_url: str = "postgresql://safelens:safelens@127.0.0.1:5432/safelens"
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    embedding_dim: int = 384
    embedding_revision: str = "5c38ec7c405ec4b44b94cc5a9bb96e735b38267a"
    embedding_batch_size: int = 32
    embedding_threads: int = 4
    embed_query_prefix: str = "Represent this sentence for searching relevant passages: "
    llm_provider: str = "openai"
    llm_model: str = "gpt-4o-mini"
    llm_max_output_tokens: int = 800
    llm_timeout: float = 30.0
    llm_temperature: float = 0.0
    openai_api_key: str = field(default="", repr=False)
    chunk_tokens: int = 500
    chunk_overlap: float = 0.15
    lexical_backend: str = "bm25"
    retrieval_mode: str = "hybrid"
    rrf_dense_weight: float = 10.0
    rrf_lexical_weight: float = 1.0
    agent_enabled: bool = True
    agent_max_retries: int = 2
    agent_max_calls: int = 6
    rerank_enabled: bool = False
    rerank_model: str = "cross-encoder/ms-marco-MiniLM-L6-v2"
    rerank_revision: str = "233902d25c440f23af6f7d6e94d2946bac0bee0a"

    def __post_init__(self):
        if self.embedding_dim <= 0 or not 400 <= self.chunk_tokens <= 600:
            raise ValueError("Embedding dimension must be positive; chunk tokens must be 400..600")
        if not 0 <= self.chunk_overlap < 1:
            raise ValueError("Chunk overlap must be in [0, 1)")
        if self.embedding_batch_size <= 0 or self.embedding_threads <= 0:
            raise ValueError("Embedding batch size and thread count must be positive")
        if self.llm_max_output_tokens <= 0 or self.llm_timeout <= 0:
            raise ValueError("LLM output limit and timeout must be positive")
        if not 0 <= self.llm_temperature <= 2:
            raise ValueError("LLM temperature must be in [0, 2]")
        if self.lexical_backend not in ("bm25", "fts") or self.retrieval_mode not in ("hybrid", "dense"):
            raise ValueError("Unknown retrieval backend/mode")
        if (not all(math.isfinite(w) for w in (self.rrf_dense_weight, self.rrf_lexical_weight))
                or min(self.rrf_dense_weight, self.rrf_lexical_weight) < 0
                or self.rrf_dense_weight + self.rrf_lexical_weight <= 0):
            raise ValueError("RRF weights must be nonnegative and not both zero")
        if not 0 <= self.agent_max_retries <= 2 or not 1 <= self.agent_max_calls <= 6:
            raise ValueError("Agent caps: at most two retries and six model calls")

    @property
    def chunk_config(self) -> dict:
        return {
            "tokens": self.chunk_tokens,
            "overlap": self.chunk_overlap,
            "text_construction": "synopsis+all_labeled_narratives; synopsis_per_chunk",
            "lexical_config": "simple",
            "embedding_revision": self.embedding_revision,
            "algorithm": "paragraph_offsets_v1",
            "token_limit": "min(target, model_max_seq_length); includes synopsis and special tokens",
            "overlap_policy": "configured fraction of previous narrative window tokens; synopsis repeated separately",
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
            embedding_revision=os.getenv("EMBEDDING_REVISION", defaults.embedding_revision),
            embedding_batch_size=int(os.getenv("EMBEDDING_BATCH_SIZE", defaults.embedding_batch_size)),
            embedding_threads=int(os.getenv("EMBEDDING_THREADS", defaults.embedding_threads)),
            embed_query_prefix=os.getenv("EMBED_QUERY_PREFIX", defaults.embed_query_prefix),
            llm_provider=os.getenv("LLM_PROVIDER", defaults.llm_provider),
            llm_model=os.getenv("LLM_MODEL", defaults.llm_model),
            llm_max_output_tokens=int(os.getenv("LLM_MAX_OUTPUT_TOKENS", defaults.llm_max_output_tokens)),
            llm_timeout=float(os.getenv("LLM_TIMEOUT", defaults.llm_timeout)),
            llm_temperature=float(os.getenv("LLM_TEMPERATURE", defaults.llm_temperature)),
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            chunk_tokens=int(os.getenv("CHUNK_TOKENS", defaults.chunk_tokens)),
            chunk_overlap=float(os.getenv("CHUNK_OVERLAP", defaults.chunk_overlap)),
            lexical_backend=os.getenv("LEXICAL_BACKEND", defaults.lexical_backend),
            retrieval_mode=os.getenv("RETRIEVAL_MODE", defaults.retrieval_mode),
            rrf_dense_weight=float(os.getenv("RRF_DENSE_WEIGHT", defaults.rrf_dense_weight)),
            rrf_lexical_weight=float(os.getenv("RRF_LEXICAL_WEIGHT", defaults.rrf_lexical_weight)),
            agent_enabled=os.getenv("AGENT_ENABLED", "true").lower() == "true",
            agent_max_retries=int(os.getenv("AGENT_MAX_RETRIES", defaults.agent_max_retries)),
            agent_max_calls=int(os.getenv("AGENT_MAX_CALLS", defaults.agent_max_calls)),
            rerank_enabled=os.getenv("RERANK_ENABLED", "false").lower() == "true",
            rerank_model=os.getenv("RERANK_MODEL", defaults.rerank_model),
            rerank_revision=os.getenv("RERANK_REVISION", defaults.rerank_revision),
        )
