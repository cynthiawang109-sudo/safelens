from dataclasses import asdict, replace

import pytest
from test_chunk_embed import FakeProvider
from test_retrieval_index import populate

from safelens.ingest import Report
from safelens.reindex import reindex
from safelens.subset import CATEGORIES, select_subset


def test_subset_same_seed_same_manifest_after_deduplication():
    reports = [Report(str(c * 100 + i), "2015-10", 2015, "Synopsis", "Account",
                      [category], "Cruise", "B737")
               for c, category in enumerate(CATEGORIES, 1) for i in range(20)]
    first = select_subset(reports + reports, seed=42, size=12)
    assert first == select_subset(reports, seed=42, size=12)
    assert first == select_subset(list(reversed(reports)), seed=42, size=12)
    assert first["selected_acns"] != select_subset(reports, seed=43, size=12)["selected_acns"]
    assert len(first["selected_acns"]) == len(set(first["selected_acns"])) == 12
    assert first["deduplicated_source_reports"] == 80
    assert sum(first["year_distribution"].values()) == 12
    with pytest.raises(ValueError, match="Not enough"):
        select_subset(reports, size=100)


def test_subset_replacement_is_atomic_and_excludes_old_reports(database):
    conn, _, settings = database
    settings = replace(settings, embedding_dim=3)
    populate(conn, settings)
    old = reindex(conn, settings, FakeProvider)
    old_reports = conn.execute("SELECT * FROM reports ORDER BY acn").fetchall()
    old_chunks = conn.execute("SELECT * FROM chunks ORDER BY id").fetchall()
    report = Report("999", "2016-01", 2016, "New synopsis", "New runway account", ["A"], "Taxi", "A320")
    records = [{**asdict(report), "content_hash": report.content_hash}]

    def fail(c):
        assert c.execute("SELECT acn FROM reports").fetchall() == [("999",)]
        raise RuntimeError("subset swap failed")

    with pytest.raises(RuntimeError, match="subset swap"):
        reindex(conn, settings, FakeProvider, before_swap=fail, replacement_reports=records)
    assert conn.execute("SELECT * FROM reports ORDER BY acn").fetchall() == old_reports
    assert conn.execute("SELECT * FROM chunks ORDER BY id").fetchall() == old_chunks
    assert conn.execute("SELECT id FROM index_meta WHERE status='ready'").fetchone() == (old["build_id"],)
    result = reindex(conn, settings, FakeProvider, replacement_reports=records)
    assert result["reports"] == 1
    assert conn.execute("SELECT acn FROM reports").fetchall() == [("999",)]
    assert conn.execute("SELECT DISTINCT acn FROM chunks").fetchall() == [("999",)]
    assert conn.execute("SELECT acn FROM ingest_state").fetchall() == [("999",)]
