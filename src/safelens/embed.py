"""Local sentence-transformers provider with asymmetric query instructions."""

import math

from safelens.config import Settings


class LocalEmbeddingProvider:
    def __init__(self, settings: Settings):
        import torch
        from sentence_transformers import SentenceTransformer

        torch.set_num_threads(settings.embedding_threads)
        self.settings = settings
        self.model = SentenceTransformer(
            settings.embedding_model, revision=settings.embedding_revision,
            device="cpu", trust_remote_code=False, cache_folder="data/models",
        )
        self.tokenizer = self.model.tokenizer
        self.max_tokens = self.model.max_seq_length
        self.dimension = self.model.get_sentence_embedding_dimension()
        if self.dimension != settings.embedding_dim:
            raise ValueError(f"Model dimension {self.dimension} != configured {settings.embedding_dim}")

    def count_tokens(self, text):
        return len(self.tokenizer.encode(text, add_special_tokens=True, truncation=False))

    def _encode(self, texts):
        texts = list(texts)
        if any(self.count_tokens(text) > self.max_tokens for text in texts):
            raise ValueError("Embedding input exceeds model token limit; refusing silent truncation")
        if not texts:
            return []
        vectors = self.model.encode(
            texts, batch_size=self.settings.embedding_batch_size,
            normalize_embeddings=True, convert_to_numpy=True,
            show_progress_bar=False, prompt="",
        ).tolist()
        if any(len(v) != self.dimension or not all(math.isfinite(x) for x in v) for v in vectors):
            raise ValueError("Invalid embedding output")
        return vectors

    def embed_documents(self, texts):
        return self._encode(texts)

    def embed_query(self, text):
        return self._encode([self.settings.embed_query_prefix + text])[0]
