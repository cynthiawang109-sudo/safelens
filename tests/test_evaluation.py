import csv
import importlib.util
from pathlib import Path

import pytest

from safelens.config import Settings
from safelens.retrieve import RetrievalConfig

spec = importlib.util.spec_from_file_location("run_eval", Path("eval/run_eval.py"))
evaluation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(evaluation)


def test_benchmark_category_metadata_never_reaches_retrieval():
    calls = []

    def search(text, k, **kwargs):
        assert "category" not in kwargs
        calls.append(text)
        return [{"acn": "wrong-category"}, {"acn": "right-category"}]

    queries = [{"id": "q1", "query": "runway", "category": "A", "layer": 1}]
    rankings, latency = evaluation.execute_queries(
        queries, object(), Settings(), object(), RetrievalConfig(),
        searchers={method: search for method in evaluation.METHODS},
    )
    metrics = evaluation.category_metrics(
        queries, rankings, {"wrong-category": ["B"], "right-category": ["A"]}
    )
    assert calls == ["runway"] * 3
    assert set(latency) == set(evaluation.METHODS)
    assert all(row["retrieved"] == 2 and row["category_precision_at_10"] == .1
               and row["hit_at_10"] == 1 for row in metrics)


def test_queries_match_step3_counts_and_controls():
    queries = evaluation.load_queries(Path("eval/queries.jsonl"))
    assert len(queries) == 31
    controls = [q for q in queries if q["layer"] == "control"]
    assert len(controls) == 3
    assert all(q["expect"] == "insufficient_evidence" and q["category"] is None for q in controls)
    reports = {"1857031": {"synopsis": "A warning occurred.",
                           "narrative": "— Report 1 —\nAn approach warning.",
                           "report_month": "2021-11", "content_hash": "test"}}
    checks = evaluation.verify_controls(queries, reports, "snapshot")
    assert all(check["verified"] for check in checks.values())
    reports["999999999999999"] = reports["1857031"]
    with pytest.raises(ValueError, match="not verified absent"):
        evaluation.verify_controls(queries, reports, "snapshot")


def test_pool_is_exact_blinded_union_shuffled_and_ungraded(tmp_path):
    queries = [{"id": f"q{i}", "layer": 2} for i in range(8)]
    rankings = {q["id"]: {
        method: [{"acn": str(i)} for i in range(offset, offset + 10)]
        for method, offset in zip(evaluation.METHODS, (0, 5, 10))
    } for q in queries}
    reports = {str(i): {"synopsis": f"Synopsis {i}"} for i in range(20)}
    pool = evaluation.judging_pool(queries, rankings, reports, 42)
    assert len(pool) == 160
    assert len({(r["query_id"], r["acn"]) for r in pool}) == 160
    assert all(list(r) == evaluation.POOL_COLUMNS and r["grade"] == r["note"] == "" for r in pool)
    assert pool == evaluation.judging_pool(queries, rankings, reports, 42)
    assert pool != evaluation.judging_pool(queries, rankings, reports, 43)
    path = tmp_path / "judging_pool.csv"
    evaluation.write_pool(path, pool)
    with path.open(encoding="utf-8", newline="") as source:
        assert list(csv.DictReader(source)) == pool
    pool[0]["grade"] = "2"
    evaluation.write_pool(path, pool)
    with pytest.raises(ValueError, match="human work"):
        evaluation.write_pool(path, [])
