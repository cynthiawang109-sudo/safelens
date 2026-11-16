from dataclasses import asdict, replace

import pytest
from test_chunk_embed import FakeProvider
from test_retrieval_index import populate

from safelens.corpus import select_expanded_corpus
from safelens.ingest import Report
from safelens.reindex import reindex
from safelens.scale_report import comparison, missing_judgments


def test_year_stratified_growth_is_deterministic_and_superset():
    reports = [Report(str(year * 100 + i), f"{year}-01", year, "Synopsis", "Account",
                      [f"label{i % 3}"], "Cruise", "B737")
               for year, count in ((2012, 20), (2013, 40), (2014, 60)) for i in range(count)]
    mini = {"selected_acns": [r.acn for r in reports[:5]], "snapshot_sha256": "base"}
    first = select_expanded_corpus(reports + reports, mini, seed=42, size=55)
    assert first == select_expanded_corpus(list(reversed(reports)), mini, seed=42, size=55)
    assert first["selected_acns"] != select_expanded_corpus(reports, mini, seed=43, size=55)["selected_acns"]
    assert set(mini["selected_acns"]) <= set(first["selected_acns"])
    assert len(first["selected_acns"]) == 55 and len(first["added_acns"]) == 50
    assert not set(first["added_acns"]) & set(mini["selected_acns"])
    assert sum(first["addition_year_counts"].values()) == 50
    for year, quota in first["addition_year_counts"].items():
        ideal = 50 * first["remaining_year_population"][year] / 115
        assert abs(quota - ideal) < 1


def test_incremental_growth_reuses_vectors_and_is_idempotent(database):
    conn, _, settings = database
    settings = replace(settings, embedding_dim=3)
    populate(conn, settings)
    reindex(conn, settings, FakeProvider)
    original = conn.execute("SELECT * FROM chunks ORDER BY id").fetchall()
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM reports")
        records = [dict(zip([c.name for c in cursor.description], row)) for row in cursor.fetchall()]
    new = Report("999", "2015-10", 2015, "New synopsis", "New account", ["A"], "Cruise", "A320")
    records.append({**asdict(new), "content_hash": new.content_hash})
    embedded = []

    class Counting(FakeProvider):
        def embed_documents(self, texts):
            embedded.extend(texts)
            return super().embed_documents(texts)

    result = reindex(conn, settings, Counting, replacement_reports=records, incremental=True)
    assert result["processed_reports"] == 1 and result["skipped_reports"] == 3
    assert result["reused_chunks"] == 3 and result["embedded_chunks"] == len(embedded) == 1
    assert conn.execute("SELECT * FROM chunks WHERE acn<>'999' ORDER BY id").fetchall() == original

    def never_initialize(settings):
        pytest.fail("Idempotent growth must not initialize or call the embedding model")

    again = reindex(conn, settings, never_initialize, replacement_reports=records, incremental=True)
    assert again["build_id"] == result["build_id"]
    assert again["processed_reports"] == 0 and again["skipped_reports"] == 4
    with pytest.raises(ValueError, match="cannot delete"):
        reindex(conn, settings, FakeProvider, replacement_reports=records[:1], incremental=True)


def test_scale_comparison_does_not_turn_unjudged_into_zero():
    queries = [{"id": "q", "layer": 2}]
    rankings = {"q": {"dense": [{"acn": "old"}, {"acn": "new"}]}}
    missing = missing_judgments(queries, rankings, {("q", "old"): 2})
    assert missing == [("q", "new")]
    base = {"corpus": {"reports": 5000, "snapshot_sha256": "base"},
            "all_category_queries": {"dense": {"category_precision_at_10": .9, "hit_at_10": 1}},
            "judged_relevance": {"averages": {"dense": {"precision_at_10": .8, "mrr": 1, "ndcg_at_10": .8}}}}
    current = {"all_category_queries": {"dense": {"category_precision_at_10": .8, "hit_at_10": 1}},
               "judged_relevance": {"status": "needs_judgments", "missing_pairs": missing}}
    result = comparison(current, base)
    assert result["layer1"]["dense"]["category_precision_at_10"]["delta"] == pytest.approx(-.1)
    assert result["layer2"]["dense"]["precision_at_10"]["20000"] is None
    assert result["layer2"]["dense"]["precision_at_10"]["delta"] is None


def test_failed_incremental_publish_keeps_old_corpus_and_vectors(database):
    conn, _, settings = database
    settings = replace(settings, embedding_dim=3)
    populate(conn, settings)
    old = reindex(conn, settings, FakeProvider)
    old_chunks = conn.execute("SELECT * FROM chunks ORDER BY id").fetchall()
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM reports")
        records = [dict(zip([c.name for c in cursor.description], row)) for row in cursor.fetchall()]
    report = Report("999", "2015-10", 2015, "New", "New account", ["A"], "Cruise", "B737")
    records.append({**asdict(report), "content_hash": report.content_hash})

    def fail(c):
        assert c.execute("SELECT count(*) FROM reports").fetchone() == (4,)
        raise RuntimeError("forced growth publication failure")

    with pytest.raises(RuntimeError, match="forced growth"):
        reindex(conn, settings, FakeProvider, before_swap=fail, replacement_reports=records, incremental=True)
    assert conn.execute("SELECT * FROM chunks ORDER BY id").fetchall() == old_chunks
    assert conn.execute("SELECT count(*) FROM reports").fetchone() == (3,)
    assert conn.execute("SELECT id,report_count FROM index_meta WHERE status='ready'").fetchone() == (old["build_id"], 3)
