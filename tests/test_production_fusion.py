from dataclasses import replace

from test_chunk_embed import FakeProvider
from test_retrieval_index import populate

from safelens.bm25 import ready_index
from safelens.reindex import reindex
from safelens.retrieve import RetrievalConfig, aggregate, fuse


def test_production_weight_endpoints_and_equal_weight():
    lexical = aggregate([("1", 1, "a", 2), ("2", 2, "b", 1)], "lexical", 50)
    dense = aggregate([("2", 2, "b", .9), ("1", 1, "a", .7)], "dense", 50)
    equal = fuse(lexical, dense, RetrievalConfig(), 1, 1)
    assert equal == fuse(lexical, dense, RetrievalConfig())
    assert equal[0]["score"] == 1 / 61 + 1 / 62
    assert fuse(lexical, dense, RetrievalConfig(), 10, 0) == dense


def test_bm25_cache_reuse_and_ready_build_invalidation(database):
    conn, _, settings = database
    settings = replace(settings, embedding_dim=3)
    populate(conn, settings)
    first = reindex(conn, settings, FakeProvider)
    a, stats = ready_index(conn)
    assert ready_index(conn)[0] is a and stats["build_id"] == first["build_id"]
    second = reindex(conn, settings, FakeProvider)
    b, stats2 = ready_index(conn)
    assert b is not a and stats2["build_id"] == second["build_id"]
    assert stats2["build_ms"] > 0
