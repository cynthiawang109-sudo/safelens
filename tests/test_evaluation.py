import csv
import hashlib
import importlib.util
import json
from dataclasses import replace
from pathlib import Path

import pytest
from psycopg.rows import dict_row
from test_chunk_embed import FakeProvider
from test_retrieval_index import populate

from safelens.config import Settings
from safelens.reindex import reindex
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


def test_eval_runner_consumes_toy_qrels_and_preserves_filled_pool(database, tmp_path):
    conn, _, settings = database
    settings = replace(settings, embedding_dim=3)
    populate(conn, settings)
    reindex(conn, settings, FakeProvider)
    queries = evaluation.load_queries(Path("eval/queries.jsonl"))
    for query in queries:
        if query["id"] == "control-time":
            query["verification"].update(acn="100", report_month="2015-10")
    query_path = tmp_path / "queries.jsonl"
    query_path.write_text("".join(json.dumps(q) + "\n" for q in queries), encoding="utf-8")
    with conn.cursor(row_factory=dict_row) as cursor:
        reports = {r["acn"]: r for r in cursor.execute("SELECT * FROM reports ORDER BY acn").fetchall()}
    snapshot = hashlib.sha256("".join(f"{acn}:{r['content_hash']}\n" for acn, r in reports.items()).encode("utf-8")).hexdigest()
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps({"selected_acns": sorted(reports), "snapshot_sha256": snapshot,
                                         "source_dataset": "synthetic", "source_revision": "synthetic", "seed": 42}), encoding="utf-8")
    judged_ids = [q["id"] for q in queries if q["layer"] == 2]
    (tmp_path / "qrels.jsonl").write_text("".join(json.dumps({"query_id": qid, "acn": acn, "grade": grade}) + "\n"
                                                for qid in judged_ids for acn, grade in zip(sorted(reports), (0, 1, 2))), encoding="utf-8")
    provider = FakeProvider(settings)
    record = evaluation.run(conn, settings, provider, query_path, manifest_path, tmp_path, 42,
                            rankings_path=tmp_path / "rankings.json")
    assert record["judged_relevance"]["status"] == "ready"
    assert record["judged_relevance"]["averages"]["dense"]["precision_at_10"] == pytest.approx(.2)
    assert "Per-query judged relevance" in (tmp_path / "results.md").read_text(encoding="utf-8")
    pool_path = tmp_path / "judging_pool.csv"
    with pool_path.open(encoding="utf-8", newline="") as source:
        rows = list(csv.DictReader(source))
    rows[0]["grade"] = "2"
    rows[0]["note"] = "Synthetic fixture only"
    with pool_path.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=evaluation.POOL_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    before = pool_path.read_bytes()
    evaluation.run(conn, settings, provider, query_path, manifest_path, tmp_path, 42,
                   rankings_path=tmp_path / "rankings.json")
    assert pool_path.read_bytes() == before
