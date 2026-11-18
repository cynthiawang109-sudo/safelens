"""Validate five human additions and complete only the development hybrid row."""

import csv
import hashlib
import io
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import psycopg

from safelens.config import Settings
from safelens.embed import LocalEmbeddingProvider
from safelens.evaluation import import_judgments, judged_metrics, load_qrels
from safelens.ingest import require_active_index
from safelens.reindex import LOCK
from safelens.retrieve import search_hybrid


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    work = Path("data/post_freeze_step7_import")
    work.mkdir(parents=True, exist_ok=True)
    pool_path = Path("eval/judging_pool_step7_additions.csv")
    pool = list(csv.DictReader(io.StringIO(pool_path.read_text(encoding="utf-8"))))
    original_pool = list(csv.DictReader(io.StringIO(subprocess.check_output(
        ["git", "show", "HEAD:eval/judging_pool_step7_additions.csv"]).decode("utf-8"))))
    identity = lambda rows: [(r["query_id"], r["acn"], r["synopsis"]) for r in rows]
    if len(pool) != 5 or identity(pool) != identity(original_pool) or any(r["grade"].strip() not in ("0", "1", "2") for r in pool):
        raise ValueError("Expected the identical five-row pool with all human grades filled")
    qrels_path, record_path, results_path = map(Path, (
        "eval/qrels.jsonl", "eval/experiment_step7_part1.json", "eval/results.md"))
    prior_raw = qrels_path.read_bytes()
    prior_record_raw, prior_results = record_path.read_bytes(), results_path.read_bytes()
    record = json.loads(prior_record_raw)
    before_relevance = json.loads(json.dumps(record["judged_relevance"]))
    queries = [json.loads(line) for line in Path("eval/queries.jsonl").read_text(encoding="utf-8").splitlines() if line]
    judged = [q for q in queries if q["layer"] == 2]
    prior = load_qrels(qrels_path, {q["id"] for q in judged})
    expected = {tuple(pair) for pair in before_relevance["missing_pairs"]}
    if len(prior) != 134 or {(r["query_id"], r["acn"]) for r in pool} != expected or expected & prior.keys():
        raise ValueError("Pool must be exactly the five missing pairs, disjoint from the 134 prior qrels")
    saved_rankings = json.loads(Path("data/eval_rankings_step7.json").read_text(encoding="utf-8"))
    settings = Settings.from_env()
    provider = LocalEmbeddingProvider(settings)
    current = {}
    with psycopg.connect(settings.database_url, autocommit=True) as conn:
        if not conn.execute("SELECT pg_try_advisory_lock_shared(%s)", (LOCK,)).fetchone()[0]:
            raise RuntimeError("Offline operation active")
        require_active_index(conn, settings)
        manifest = json.loads(Path("eval/corpus_manifest_20k.json").read_text(encoding="utf-8"))
        rows = conn.execute("SELECT acn,content_hash FROM reports ORDER BY acn COLLATE \"C\"").fetchall()
        snapshot = digest("".join(f"{acn}:{h}\n" for acn, h in rows).encode("utf-8"))
        if snapshot != manifest["snapshot_sha256"] or len(rows) != 20000:
            raise ValueError("Corpus differs from the 20k manifest")
        for row in pool:
            synopsis = conn.execute("SELECT synopsis FROM reports WHERE acn=%s", (row["acn"],)).fetchone()[0]
            if synopsis != row["synopsis"]:
                raise ValueError("Judging synopsis differs from indexed report")
        for query in judged:
            hits = search_hybrid(query["query"], 10, conn=conn, settings=settings, provider=provider)
            if [h["acn"] for h in hits] != [h["acn"] for h in saved_rankings[query["id"]]["hybrid"]]:
                raise ValueError("Production ranking changed; do not silently replace the judging pool")
            current[query["id"]] = {"hybrid": hits}
    missing = {(qid, h["acn"]) for qid, methods in current.items() for h in methods["hybrid"] if (qid, h["acn"]) not in prior}
    if missing != expected:
        raise ValueError("Current production top-ten missing-pair set differs from the five additions")
    # The existing validator requires complete coverage within its query scope.
    # Scope this partial import to its four development query IDs; keep the
    # exact five-pair whitelist and the full 20k manifest validation unchanged.
    scope = work / "development_query_scope.jsonl"
    scope.write_text("".join(json.dumps(q) + "\n" for q in judged if q["id"] in {r["query_id"] for r in pool}), encoding="utf-8")
    imported_path = work / "validated_five.jsonl"
    imported = import_judgments(pool_path, imported_path, scope, Path("eval/corpus_manifest_20k.json"), expected)
    additions = [json.loads(line) for line in imported_path.read_text(encoding="utf-8").splitlines()]
    eol = b"\r\n" if b"\r\n" in prior_raw else b"\n"
    if not prior_raw.endswith(b"\n"):
        raise ValueError("Prior JSONL must end with a newline to append without changing prior bytes")
    merged = prior_raw + b"".join(json.dumps(row, ensure_ascii=False).encode("utf-8") + eol for row in additions)
    merged_path = work / "merged_qrels.jsonl"
    merged_path.write_bytes(merged)
    qrels = load_qrels(merged_path, {q["id"] for q in judged})
    assert imported == 5 and len(qrels) == 139 and all(qrels[key] == grade for key, grade in prior.items())
    metrics = judged_metrics(queries, current, qrels)
    dense_pairs = {(qid, h["acn"]) for qid in current for h in saved_rankings[qid]["dense"][:10]}
    assert not expected & dense_pairs
    ideal_changes = [qid for qid in current
                     if sorted((g for (q, _), g in prior.items() if q == qid), reverse=True)[:10]
                     != sorted((g for (q, _), g in qrels.items() if q == qid), reverse=True)[:10]]
    completion = {"completed_at_utc": datetime.now(UTC).isoformat(), "split": "development only",
                  "imported_rows": imported, "qrels_rows_before": 134, "qrels_rows_after": 139,
                  "prior_qrels_sha256": digest(prior_raw), "qrels_sha256": digest(merged),
                  "prior_rows_byte_unchanged": merged[:len(prior_raw)] == prior_raw,
                  "pool_sha256": digest(pool_path.read_bytes()), "ranking_orders_unchanged": True,
                  "hybrid_coverage_at_10": 1.0, "hybrid": metrics["averages"]["hybrid"],
                  "retained_dense_and_lexical_qrels_rows": 134,
                  "retained_dense_and_lexical_qrels_sha256": digest(prior_raw),
                  "dense_metrics_unchanged": True, "extended_pool_changes_ideal_for": ideal_changes,
                  "ndcg_comparison_note": "Hybrid uses the extended 139-qrel pooled ideal. Dense/legacy lexical remain historical at 134 qrels; do not treat their nDCG as a new common-pool comparison.",
                  "new_judgments": additions, "frozen_test_rerun": False}
    relevance = record["judged_relevance"]
    relevance.update(status="ready", definitions=metrics["definitions"])
    relevance.pop("missing_pairs", None)
    relevance.pop("reason", None)
    relevance["averages"]["hybrid"] = metrics["averages"]["hybrid"]
    relevance["per_query"].extend(metrics["per_query"])
    assert relevance["averages"]["dense"] == before_relevance["averages"]["dense"]
    assert [r for r in relevance["per_query"] if r["method"] == "dense"] == [r for r in before_relevance["per_query"] if r["method"] == "dense"]
    record["qrels_file_sha256"] = digest(merged)
    record["post_freeze_judgment_completion"] = completion
    start = prior_results.index(b"<!-- production-step7-part1 -->")
    end = prior_results.index(b"<!-- agent-ablation-step7 -->", start)
    section = prior_results[start:end]
    lines = section.splitlines(keepends=True)
    m = metrics["averages"]["hybrid"]
    replacement_note = ("Post-freeze judgment completion: the five human additions are imported (139 development qrels). "
                        "Production hybrid top-ten coverage is 100%; all rankings are unchanged. "
                        "Dense and legacy lexical rows remain historical at 134 qrels. Hybrid nDCG uses the extended "
                        "139-qrel pooled ideal; the ideal changes for nmac-l2-1, so these nDCG rows are not a new "
                        "common-pool comparison. See docs/POST_FREEZE_STEP7_JUDGMENTS.md.\n")
    for i, line in enumerate(lines):
        if line.startswith(b"| hybrid | "):
            for field in ("precision_at_10", "mrr", "ndcg_at_10"):
                line = line.replace(b"pending judgments", f"{m[field]:.4f}".encode("ascii"), 1)
            lines[i] = line
        if line.startswith(b"Hybrid Layer-2 has "):
            lines[i] = replacement_note.encode("utf-8").replace(b"\n", eol)
    updated_results = prior_results[:start] + b"".join(lines) + prior_results[end:]
    frozen_marker = b"<!-- frozen-final-test-step7d -->"
    assert updated_results.split(frozen_marker, 1)[1] == prior_results.split(frozen_marker, 1)[1]
    for name, raw in (("prior_qrels.jsonl", prior_raw), ("prior_experiment.json", prior_record_raw), ("prior_results.md", prior_results)):
        (work / name).write_bytes(raw)
    qrels_path.write_bytes(merged)
    record_eol = b"\r\n" if b"\r\n" in prior_record_raw else b"\n"
    record_path.write_bytes((json.dumps(record, indent=2, ensure_ascii=False) + "\n").encode("utf-8").replace(b"\n", record_eol))
    results_path.write_bytes(updated_results)
    Path("docs/POST_FREEZE_STEP7_JUDGMENTS.json").write_text(json.dumps(completion, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(completion, indent=2))


if __name__ == "__main__":
    main()
