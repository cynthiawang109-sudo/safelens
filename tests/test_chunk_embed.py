import re
from dataclasses import replace
from itertools import pairwise

import numpy as np
import pytest

from safelens.chunk import chunk_report
from safelens.config import Settings
from safelens.embed import LocalEmbeddingProvider


class WordTokenizer:
    def __call__(self, text, **kwargs):
        return {"offset_mapping": [(m.start(), m.end()) for m in re.finditer(r"\S+", text)]}

    def encode(self, text, **kwargs):
        return text.split() + ["[CLS]", "[SEP]"]


class FakeProvider:
    max_tokens = 512
    tokenizer = WordTokenizer()

    def __init__(self, settings):
        self.dimension = settings.embedding_dim

    def count_tokens(self, text):
        return len(self.tokenizer.encode(text))

    def embed_documents(self, texts):
        return [[1.0] + [0.0] * (self.dimension - 1) for text in texts]

    def embed_query(self, text):
        return [1.0] + [0.0] * (self.dimension - 1)


def test_token_budget_overlap_and_source_coverage():
    settings = Settings()
    provider = FakeProvider(settings)
    words = [f"word{i}" for i in range(1300)]
    chunks = chunk_report("Synopsis", " ".join(words), provider, settings)
    assert all(chunk.startswith("Synopsis\n\n") for chunk in chunks)
    assert all(provider.count_tokens(chunk) <= 500 for chunk in chunks)
    assert all(provider.count_tokens(chunk) >= 400 for chunk in chunks[:-1])
    windows = [chunk.split("\n\n")[1].split() for chunk in chunks]
    assert set().union(*(set(window) for window in windows)) == set(words)
    for previous, current in pairwise(windows):
        overlap = round(len(previous) * .15)
        assert current[:overlap] == previous[-overlap:]


def test_paragraph_boundary_short_tail_and_model_limit():
    settings = Settings()
    provider = FakeProvider(settings)
    narrative = " ".join(["first"] * 420) + "\n\n" + " ".join(["second"] * 300)
    chunks = chunk_report("Synopsis", narrative, provider, settings)
    assert "second" not in chunks[0]
    assert "second" in chunks[1]
    assert chunk_report("Synopsis", "Short account.", provider, settings) == ["Synopsis\n\nShort account."]
    chunks = chunk_report("Synopsis", "word " * 1500, provider, replace(settings, chunk_tokens=600))
    assert max(map(provider.count_tokens, chunks)) <= provider.max_tokens
    with pytest.raises(ValueError, match="Synopsis"):
        chunk_report("word " * 600, "Account", provider, settings)


def test_provider_query_prefix_documents_and_no_truncation():
    calls = []

    class Model:
        def encode(self, texts, **kwargs):
            calls.append((texts, kwargs))
            return np.asarray([[1.0, 0.0] for _ in texts])

    provider = LocalEmbeddingProvider.__new__(LocalEmbeddingProvider)
    provider.settings = replace(Settings(), embed_query_prefix="instruction: ")
    provider.tokenizer = WordTokenizer()
    provider.max_tokens = 512
    provider.dimension = 2
    provider.model = Model()
    assert provider.embed_documents(["Document"])[0] == [1.0, 0.0]
    assert calls[-1][0] == ["Document"]
    provider.embed_query("Question")
    assert calls[-1][0] == ["instruction: Question"]
    assert calls[-1][1]["normalize_embeddings"] is True
    assert calls[-1][1]["prompt"] == ""
    with pytest.raises(ValueError, match="silent truncation"):
        provider.embed_documents(["word " * 600])
