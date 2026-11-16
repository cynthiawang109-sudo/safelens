import pytest

from safelens.lexical_bakeoff import (
    BM25Reference,
    coverage_metrics,
    lexical_or,
    or_tsquery,
)
from safelens.retrieve import RetrievalConfig


def test_or_builder_stopwords_empty_and_operator_safety():
    assert or_tsquery("the and is OR") == ""
    assert or_tsquery("") == ""
    assert or_tsquery("Runway runway clearance | ! ' &") == "'clearance' | 'runway'"
    assert or_tsquery("TCAS RA") == "'ra' | 'tcas'"


def test_coverage_removes_unknowns_without_inventing_zero_grades():
    qrels = {("q", "a"): 0, ("q", "b"): 2}
    row = coverage_metrics([{"acn": "unknown"}, {"acn": "a"}, {"acn": "b"}], "q", qrels)
    assert row["judged"] == 2 and row["coverage_at_10"] == .2
    assert row["coverage_of_returned"] == pytest.approx(2 / 3)
    assert row["precision_at_10"] == .5 and row["mrr"] == .5
    assert row["ndcg_at_10"] == pytest.approx(1 / 1.584962500721156)
    empty = coverage_metrics([{"acn": "unknown"}], "q", qrels)
    assert empty["precision_at_10"] is None and empty["mrr"] is None
    assert empty["ndcg_at_10"] is None and empty["coverage_at_10"] == 0
    assert coverage_metrics([], "q", qrels)["coverage_of_returned"] is None


def test_bm25_candidate_chunk_limit_precedes_report_aggregation():
    reference = BM25Reference([("1", 1, "runway runway"), ("1", 2, "runway runway"),
                               ("2", 3, "runway"), ("3", 4, "engine"),
                               ("4", 5, "hydraulics"), ("5", 6, "turbulence"),
                               ("6", 7, "weather")])
    hits = reference.search("runway", RetrievalConfig(candidate_chunks=2, candidate_reports=50))
    assert [h["acn"] for h in hits] == ["1"]
    assert hits[0]["chunk_id"] == 1
    assert reference.search("the and", RetrievalConfig()) == []


def test_or_sql_contract_and_report_collapse():
    class Connection:
        def execute(self, sql, args):
            assert "to_tsquery('simple',%s)" in sql
            assert "anomaly" not in sql
            assert args == ("'clearance' | 'runway'", "'clearance' | 'runway'", 100)
            return self

        def fetchall(self):
            return [("200", 2, "text", 1.), ("100", 3, "text", 1.),
                    ("100", 1, "text", 1.)]

    hits = lexical_or(Connection(), "the runway clearance", RetrievalConfig())
    assert [h["acn"] for h in hits] == ["100", "200"]
    assert hits[0]["chunk_id"] == 1
    assert lexical_or(None, "the and", RetrievalConfig()) == []
