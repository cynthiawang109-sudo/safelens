from dataclasses import replace

import psycopg
import pytest
from test_chunk_embed import FakeProvider

from safelens.ingest import Report, upsert_report
from safelens.reindex import LOCK, reindex
from safelens.retrieve import (
    RetrievalConfig,
    aggregate,
    fuse,
    search_dense,
    search_hybrid,
    search_lexical,
)


def populate(conn, settings):
    for acn in ("100", "200", "300"):
        upsert_report(conn, Report(acn, "2015-10", 2015, "Synopsis",
                                  "runway runway" if acn == "100" else "runway",
                                  ["A"] if acn == "100" else ["B"], "Cruise", "B737"), settings)


def test_report_aggregation_before_rrf_and_ties():
    lexical = aggregate([("B", 2, "B", 8), ("A", 3, "A3", 9), ("A", 1, "A1", 9)], "lexical", 50)
    dense = aggregate([("B", 2, "B", 1), ("A", 3, "A3", .5)], "dense", 50)
    assert [hit["acn"] for hit in lexical] == ["A", "B"]
    assert lexical[0]["chunk_id"] == 1
    results = fuse(lexical, dense, RetrievalConfig())
    assert [hit["acn"] for hit in results] == ["A", "B"]
    assert results[0]["score"] == pytest.approx(1 / 61 + 1 / 62)
    assert results[0]["ranks"] == {"lexical": 1, "dense": 2}
    assert results[0]["components"]["dense"]["chunk_id"] == 3


def test_build_search_unique_acns_filters_and_candidate_order(database):
    conn, _, settings = database
    settings = replace(settings, embedding_dim=3, lexical_backend="fts", rrf_dense_weight=1)
    populate(conn, settings)
    built = reindex(conn, settings, FakeProvider)
    assert (built["reports"], built["chunks"]) == (3, 3)
    conn.execute(
        "INSERT INTO chunks (acn, chunk_idx, text, embedding, anomaly_codes) "
        "SELECT acn, 1, text, embedding, anomaly_codes FROM chunks WHERE acn='100'"
    )
    options = {"conn": conn, "settings": settings}
    for function in (search_lexical, search_dense, search_hybrid):
        extra = {} if function == search_lexical else {"provider": FakeProvider(settings)}
        results = function("runway", 10, **options, **extra)
        assert [hit["acn"] for hit in results] == ["100", "200", "300"]
        assert len({hit["acn"] for hit in results}) == len(results)
        assert {hit["acn"] for hit in function("runway", 10, category="B", **options, **extra)} == {"200", "300"}
        starved = function("runway", 10, config=RetrievalConfig(candidate_chunks=2), **options, **extra)
        assert [hit["acn"] for hit in starved] == ["100"]
    with pytest.raises(ValueError, match="matching ready"):
        search_lexical("runway", conn=conn, settings=replace(settings, embed_query_prefix="wrong"))


def test_failed_rebuild_preserves_index_and_dimension(database):
    conn, dsn, settings = database
    populate(conn, settings)
    old = reindex(conn, settings, FakeProvider)
    chunks = conn.execute("SELECT * FROM chunks ORDER BY id").fetchall()
    changed = replace(settings, embedding_dim=3)

    def fail(c):
        with (psycopg.connect(dsn, autocommit=True) as reader,
              pytest.raises(RuntimeError, match="unavailable")):
            search_lexical("runway", conn=reader, settings=settings)
        raise RuntimeError("forced swap failure")

    with pytest.raises(RuntimeError, match="forced swap"):
        reindex(conn, changed, FakeProvider, before_swap=fail)
    assert conn.execute("SELECT * FROM chunks ORDER BY id").fetchall() == chunks
    assert conn.execute("SELECT id FROM index_meta WHERE status='ready'").fetchone() == (old["build_id"],)
    assert conn.execute("SELECT count(*) FROM index_meta WHERE status='failed'").fetchone() == (1,)
    assert search_dense("runway", conn=conn, settings=settings, provider=FakeProvider(settings))
    new = reindex(conn, changed, FakeProvider)
    assert conn.execute("SELECT status FROM index_meta WHERE id=%s", (old["build_id"],)).fetchone() == ("superseded",)
    assert conn.execute("SELECT id FROM index_meta WHERE status='ready'").fetchone() == (new["build_id"],)
    assert search_dense("runway", conn=conn, settings=changed, provider=FakeProvider(changed))


def test_build_lock_and_abandoned_build_recovery(database):
    conn, dsn, settings = database
    populate(conn, settings)
    built = reindex(conn, settings, FakeProvider)
    conn.execute("UPDATE index_meta SET status='building' WHERE id=%s", (built["build_id"],))
    with psycopg.connect(dsn, autocommit=True) as other:
        other.execute("SELECT pg_advisory_lock(%s)", (LOCK,))
        with pytest.raises(RuntimeError, match="active"):
            reindex(conn, settings, FakeProvider)
    reindex(conn, settings, FakeProvider)
    assert conn.execute("SELECT status FROM index_meta WHERE id=%s", (built["build_id"],)).fetchone() == ("failed",)
