"""Unfiltered report-level category agreement and a blinded, ungraded pool.

No generation calls or automatic judgments. Layer-2 scoring requires human qrels.
"""

import argparse
import csv
import hashlib
import importlib.metadata
import json
import math
import platform
import random
import re
from collections import Counter
from dataclasses import asdict, replace
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean
from time import perf_counter

import psycopg
from psycopg.rows import dict_row

from safelens.config import Settings
from safelens.embed import LocalEmbeddingProvider
from safelens.evaluation import judged_metrics, load_qrels
from safelens.ingest import require_active_index
from safelens.reindex import LOCK
from safelens.retrieve import (
    RetrievalConfig,
    search_dense,
    search_hybrid,
    search_lexical,
)
from safelens.scale_report import comparison, missing_judgments, render_scaleup
from safelens.subset import CATEGORIES

METHODS = {"lexical": search_lexical, "dense": search_dense, "hybrid": search_hybrid}
POOL_COLUMNS = ["query_id", "acn", "synopsis", "grade", "note"]


def file_hash(path):
    if not Path(path).exists():
        return None
    with Path(path).open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def load_queries(path):
    with Path(path).open(encoding="utf-8") as source:
        queries = [json.loads(line) for line in source if line.strip()]
    if len({q["id"] for q in queries}) != len(queries):
        raise ValueError("Duplicate query IDs")
    if Counter(q["layer"] for q in queries) != {1: 20, 2: 8, "control": 3}:
        raise ValueError("Step 3 requires 20 Layer-1, 8 Layer-2, and 3 control queries")
    for layer, expected in ((1, 5), (2, 2)):
        counts = Counter(q["category"] for q in queries if q["layer"] == layer)
        if counts != {c: expected for c in CATEGORIES}:
            raise ValueError(f"Layer {layer} category counts do not match Step 3")
    for query in queries:
        if not query["query"].strip():
            raise ValueError("Empty query")
        if query["layer"] == "control" and (
            query["category"] is not None or query.get("expect") != "insufficient_evidence"
        ):
            raise ValueError("Control requires category=null and expect=insufficient_evidence")
    return queries


def verify_controls(queries, reports, snapshot_hash):
    checks = {}
    for query in queries:
        if query["layer"] != "control":
            continue
        rule = query["verification"]
        kind = rule["kind"]
        if kind == "absent_acn":
            passed = rule["acn"] not in reports
            evidence = {"acn": rule["acn"], "present": not passed}
        elif kind == "absent_phrases":
            matches = {phrase: sum(phrase.casefold() in (r["synopsis"] + "\n" + r["narrative"]).casefold()
                                   for r in reports.values()) for phrase in rule["phrases"]}
            passed = not any(matches.values())
            evidence = {"matching_report_counts": matches}
        elif kind == "month_only_report":
            report = reports[rule["acn"]]
            text = (report["synopsis"] + "\n" + report["narrative"]).replace(
                "— Report 1 —", ""
            ).replace("— Report 2 —", "")
            # The chosen short account was manually read in full. Keep the automated
            # guard deliberately strict: no digits, months, days, or clock words.
            temporal = re.search(
                r"\d|\b(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday|"
                r"january|february|march|april|may|june|july|august|september|october|november|"
                r"december|yesterday|today|tomorrow|noon|midnight|utc|gmt|am|pm)\b",
                text, re.IGNORECASE,
            )
            passed = report["report_month"] == rule["report_month"] and temporal is None
            evidence = {"acn": rule["acn"], "report_month": report["report_month"],
                        "content_hash": report["content_hash"], "temporal_marker_found": bool(temporal),
                        "manual_full_text_inspection": rule["reason"]}
        else:
            raise ValueError(f"Unknown control verification kind: {kind}")
        if not passed:
            raise ValueError(f"Control fact is not verified absent: {query['id']}: {evidence}")
        checks[query["id"]] = {"verified": True, "snapshot_sha256": snapshot_hash,
                               "expect": query["expect"], "evidence": evidence,
                               "generation_outcome": "not_run_step3"}
    return checks


def execute_queries(queries, conn, settings, provider, config, searchers=None):
    """Category is evaluation metadata and is NEVER sent to retrieval."""
    searchers = METHODS if searchers is None else searchers
    rankings, latency = {}, {name: [] for name in searchers}
    for query in queries:
        rankings[query["id"]] = {}
        for name, search in searchers.items():
            extra = {} if name == "lexical" else {"provider": provider}
            started = perf_counter()
            hits = search(query["query"], 10, conn=conn, settings=settings, config=config, **extra)
            latency[name].append((perf_counter() - started) * 1000)
            if len(hits) != len({h["acn"] for h in hits}) or len(hits) > 10:
                raise ValueError("Retriever returned duplicate ACNs or more than ten reports")
            rankings[query["id"]][name] = hits
    return rankings, latency


def category_metrics(queries, rankings, labels):
    rows = []
    for query in queries:
        if query["category"] is None:
            continue
        for method, hits in rankings[query["id"]].items():
            correct = sum(query["category"] in labels[h["acn"]] for h in hits)
            rows.append({"query_id": query["id"], "layer": query["layer"], "method": method,
                         "retrieved": len(hits), "category_matches": correct,
                         "category_precision_at_10": correct / 10, "hit_at_10": int(correct > 0)})
    return rows


def average_metrics(rows):
    return {method: {
        "queries": len(selected := [r for r in rows if r["method"] == method]),
        "category_precision_at_10": mean(r["category_precision_at_10"] for r in selected),
        "hit_at_10": mean(r["hit_at_10"] for r in selected),
    } for method in METHODS}


def judging_pool(queries, rankings, reports, seed):
    rows = []
    for query in queries:
        if query["layer"] != 2:
            continue
        acns = sorted({hit["acn"] for hits in rankings[query["id"]].values() for hit in hits})
        rows.extend({"query_id": query["id"], "acn": acn, "synopsis": reports[acn]["synopsis"],
                     "grade": "", "note": ""} for acn in acns)
    random.Random(seed).shuffle(rows)
    if len(rows) > 240 or len(rows) != len({(r["query_id"], r["acn"]) for r in rows}):
        raise ValueError("Invalid judging pool size or duplicates")
    return rows


def write_pool(path, rows, preserve_judgments=False):
    if path.exists():
        with path.open(encoding="utf-8", newline="") as source:
            reader = csv.DictReader(source)
            existing = list(reader)
            if any(r["grade"] or r["note"] for r in existing):
                if preserve_judgments and reader.fieldnames == POOL_COLUMNS and {
                    (r["query_id"], r["acn"], r["synopsis"]) for r in existing
                } == {(r["query_id"], r["acn"], r["synopsis"]) for r in rows} and len(existing) == len(rows):
                    return
                raise ValueError("Judging pool already contains human work; refusing to overwrite")
    with path.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=POOL_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def render_results(record):
    lines = ["# Mini Layer-1 evaluation and judging pool", "",
             "Benchmark retrieval is **unfiltered**. Category labels measure coarse topical agreement, not query-level relevance.",
             "Missing ranks in an underfilled top ten count as misses (fixed denominator 10). Hit@10 means at least one matching report.",
             "", f"Corpus: **{record['corpus']['reports']} reports**, **{record['corpus']['chunks']} chunks**; ready build **{record['index']['id']}**.",
             f"Selection seed: **{record['corpus']['selection_seed']}**. Candidate chunks/reports: **100/50**; report-level max chunk score before RRF, **k=60**; ties by ACN.", ""]
    for title, key in (("20 dedicated Layer-1 queries (five per category)", "layer1_primary"),
                       ("All 28 category queries (including eight future judged queries)", "all_category_queries")):
        lines.extend([f"## {title}", "", "| Retriever | Category Precision@10 | Hit@10 |", "|---|---:|---:|"])
        for method, values in record[key].items():
            lines.append(f"| {method} | {values['category_precision_at_10']:.3f} | {values['hit_at_10']:.3f} |")
        lines.append("")
    primary = record["layer1_primary"]
    underfilled = sum(r["layer"] == 1 and r["method"] == "lexical" and r["retrieved"] < 10 for r in record["per_query"])
    empty = sum(r["layer"] == 1 and r["method"] == "lexical" and r["retrieved"] == 0 for r in record["per_query"])
    lines.extend(["## Findings", "",
                  f"On the 20 primary queries, hybrid Category Precision@10 is {primary['hybrid']['category_precision_at_10']:.3f}, compared with dense {primary['dense']['category_precision_at_10']:.3f} and lexical {primary['lexical']['category_precision_at_10']:.3f}.",
                  f"PostgreSQL FTS underfilled the top ten on {underfilled}/20 primary queries, including {empty} with zero matches under its conjunctive websearch/simple semantics. Queries and defaults were not tuned after seeing results.",
                  "These findings describe category agreement only; human relevance judging is still pending.", "",
                  "## Per-query category agreement", "", "Layer 2 rows below are category agreement only; no human relevance scores have been assigned.", "",
                  "| Query | Layer | Retriever | Retrieved | Category Precision@10 | Hit@10 |", "|---|---:|---|---:|---:|---:|"])
    for row in record["per_query"]:
        lines.append(f"| {row['query_id']} | {row['layer']} | {row['method']} | {row['retrieved']} | {row['category_precision_at_10']:.3f} | {row['hit_at_10']} |")
    lines.extend(["", "## Retrieval latency", "", "Single local run, warmed model; excludes model initialization and generation. Timed across all 31 queries. p95 is nearest-rank.", "",
                  "| Retriever | Mean ms | p95 ms |", "|---|---:|---:|"])
    for method, values in record["latency_ms"].items():
        lines.append(f"| {method} | {values['mean']:.2f} | {values['p95']:.2f} |")
    lines.extend(["", "## Candidate-depth check", "", "Defaults remain 100/50. Doubling candidate chunks to 200 is a separately recorded sensitivity check over all 28 category queries.", "",
                  "| Retriever | Queries with changed top-10 ACN order | Change in mean Category Precision@10 |", "|---|---:|---:|"])
    for method, values in record["candidate_depth_sensitivity"].items():
        lines.append(f"| {method} | {values['changed_top10_queries']}/28 | {values['category_precision_at_10_delta']:+.3f} |")
    relevance = record.get("judged_relevance", {"status": "pending"})
    lines.extend(["", "## Layer-2 judging", "",
                  f"`judging_pool.csv` contains **{record['judging_pool']['rows']}** unique (query_id, acn) pairs for eight queries, shuffled with seed {record['judging_pool']['shuffle_seed']}.",
                  f"The sheet contains no retriever identity or ranks. Filled grades: {record['judging_pool']['grades_assigned']}; filled notes: {record['judging_pool']['notes_assigned']}. No automated judgments are assigned.",
                  "Cynthia: read synopsis first, consult the indexed full narrative if ambiguous, then use grades 2=directly relevant, 1=partially relevant, 0=irrelevant. Record notes as needed.",
                  "After human grading, run `uv run python eval/import_judgments.py`, then rerun this evaluator. Unjudged top-ten reports cause an error rather than being assumed irrelevant."])
    if relevance["status"] == "ready":
        lines.extend(["", "### Judged relevance (macro averages)", "",
                      "Precision@10 and MRR treat grade >=1 as relevant. MRR uses the retrieved top ten. nDCG@10 uses linear gains 2/1/0 and the pooled ideal ranking.",
                      "These eight queries are a development set, not an independent held-out test; pooling does not establish complete corpus relevance.", "",
                      "| Retriever | Precision@10 | MRR | nDCG@10 |", "|---|---:|---:|---:|"])
        for method, scores in relevance["averages"].items():
            lines.append(f"| {method} | {scores['precision_at_10']:.3f} | {scores['mrr']:.3f} | {scores['ndcg_at_10']:.3f} |")
        lines.extend(["", "### Per-query judged relevance", "",
                      "| Query | Retriever | Precision@10 | MRR | nDCG@10 |", "|---|---|---:|---:|---:|"])
        for row in relevance["per_query"]:
            lines.append(f"| {row['query_id']} | {row['method']} | {row['precision_at_10']:.3f} | {row['mrr']:.3f} | {row['ndcg_at_10']:.3f} |")
    else:
        lines.extend(["", "Human relevance metrics are pending: `qrels.jsonl` does not exist. No grades have been invented."])
    lines.extend([
                  "", "## Abstention controls", "",
                  "Controls are present with `expect: insufficient_evidence`. Absence was checked against this frozen subset. This retrieval evaluator does not call generation; Step 4 generation smoke outcomes are recorded separately in `docs/STEP4_NOTES.md`.", ""])
    for name, control in record["controls"].items():
        lines.append(f"- `{name}`: absence verified; `{json.dumps(control['evidence'], ensure_ascii=False)}`")
    lines.extend(["", "## Limitations and experiment record", "",
                  "Layer-1 category metrics are not judged relevance or proof that any method is better at answering questions. Judged relevance, when available above, is reported separately. Twenty-eight hand-written queries are a development set, not an independent held-out test.",
                  "The category-balanced subset includes every available runway-incursion report; category overlap and year skew are recorded in the manifest and DATA_NOTES. Synopsis text is included in indexing and may simplify retrieval.",
                  "PostgreSQL FTS uses simple configuration and websearch query semantics; long conjunctive queries may underfill the top ten. This baseline is not BM25. Exact cosine search uses no ANN index.",
                  "Candidate-depth changes above must be considered before interpreting hybrid results; the default was not silently tuned.",
                  "The complete experiment configuration, corpus/content hashes, query/qrels hashes, per-query metrics and latency samples, software/hardware notes, and timestamp are in `experiment.json`.",
                  "No generation or human judging is performed by this evaluator.", ""])
    return "\n".join(lines)


def run(conn, settings, provider, queries_path, manifest_path, output, pool_seed,
        rankings_path=Path("data/eval_rankings.json")):
    queries = load_queries(queries_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    scaleup = manifest.get("manifest_type") == "flagship_year_stratified_v1"
    if scaleup and rankings_path == Path("data/eval_rankings.json"):
        rankings_path = Path("data/eval_rankings_20k.json")
    if not conn.execute("SELECT pg_try_advisory_lock_shared(%s)", (LOCK,)).fetchone()[0]:
        raise RuntimeError("Offline build is active; evaluate only a ready corpus")
    try:
        require_active_index(conn, settings)
        with conn.cursor(row_factory=dict_row) as cursor:
            reports = {r["acn"]: r for r in cursor.execute("SELECT * FROM reports ORDER BY acn COLLATE \"C\"").fetchall()}
            index = cursor.execute("SELECT * FROM index_meta WHERE status='ready'").fetchone()
        snapshot = hashlib.sha256("".join(f"{acn}:{r['content_hash']}\n" for acn, r in reports.items()).encode("utf-8")).hexdigest()
        if sorted(reports) != manifest["selected_acns"] or snapshot != manifest["snapshot_sha256"]:
            raise ValueError("Active corpus differs from the subset manifest")
        counts = conn.execute("SELECT count(*), count(DISTINCT acn), count(embedding) FROM chunks").fetchone()
        if counts[0] != counts[2] or counts[1] != len(reports) or index["report_count"] != len(reports):
            raise ValueError("Index count/embedding validation failed")
        controls = verify_controls(queries, reports, snapshot)
        config = RetrievalConfig()
        provider.embed_query("aviation safety")
        rankings, timings = execute_queries(queries, conn, settings, provider, config)
        rows = category_metrics(queries, rankings, {acn: r["anomaly_codes"] for acn, r in reports.items()})
        deep, _ = execute_queries(queries, conn, settings, provider, replace(config, candidate_chunks=200))
        deep_rows = category_metrics(queries, deep, {acn: r["anomaly_codes"] for acn, r in reports.items()})
        summary, deep_summary = average_metrics(rows), average_metrics(deep_rows)
        pool = judging_pool(queries, rankings, reports, pool_seed)
        qrels_path = output / "qrels.jsonl"
        relevance = {"status": "pending", "reason": "qrels.jsonl absent; human judging not performed"}
        if qrels_path.exists():
            qrels = load_qrels(qrels_path, {q["id"] for q in queries if q["layer"] == 2})
            missing = missing_judgments(queries, rankings, qrels)
            if scaleup and missing:
                relevance = {"status": "needs_judgments", "missing_pairs": missing,
                             "reason": "Expanded corpus top-ten coverage incomplete; unjudged documents are not irrelevant"}
            else:
                relevance = judged_metrics(queries, rankings, qrels)
        output.mkdir(parents=True, exist_ok=True)
        pool_path = output / ("judging_pool_20k.csv" if scaleup else "judging_pool.csv")
        write_pool(pool_path, pool, preserve_judgments=True)
        if scaleup and relevance["status"] == "needs_judgments":
            missing_set = set(map(tuple, relevance["missing_pairs"]))
            write_pool(output / "judging_pool_20k_additions.csv",
                       [r for r in pool if (r["query_id"], r["acn"]) in missing_set], preserve_judgments=True)
        with pool_path.open(encoding="utf-8", newline="") as source:
            saved_pool = list(csv.DictReader(source))
        index["built_at"] = index["built_at"].isoformat()
        record = {
            "timestamp": datetime.now(UTC).isoformat(), "unfiltered": True,
            "corpus": {"source_dataset": manifest["source_dataset"], "source_revision": manifest["source_revision"],
                       "selection_seed": manifest["seed"], "reports": len(reports), "chunks": counts[0],
                       "snapshot_sha256": snapshot, "manifest_sha256": file_hash(manifest_path)},
            "manifest_path": str(manifest_path), "split": "development",
            "index": index, "retrieval_config": asdict(config),
            "embedding_runtime": {"device": "cpu", "normalized": True, "batch_size": settings.embedding_batch_size,
                                  "threads": settings.embedding_threads, "build_batch_order": "token_length_descending"},
            "query_file_sha256": file_hash(queries_path), "qrels_file_sha256": file_hash(output / "qrels.jsonl"),
            "query_order": [q["id"] for q in queries],
            "timing_scope": "31 queries; retrieval plus query embeddings; excludes model initialization and generation",
            "judging_pool": {"rows": len(pool), "unique_queries": len({r['query_id'] for r in pool}),
                             "shuffle_seed": pool_seed, "sha256": file_hash(pool_path), "path": str(pool_path),
                             "grades_assigned": sum(bool(r["grade"]) for r in saved_pool),
                             "notes_assigned": sum(bool(r["note"]) for r in saved_pool)},
            "judged_relevance": relevance,
            "layer1_primary": average_metrics([r for r in rows if r["layer"] == 1]),
            "all_category_queries": summary, "per_query": rows, "controls": controls,
            "latency_ms": {name: {"n": len(values), "samples": values, "mean": mean(values),
                                   "p95": sorted(values)[math.ceil(.95 * len(values)) - 1]} for name, values in timings.items()},
            "candidate_depth_sensitivity": {method: {
                "changed_top10_queries": sum([h["acn"] for h in rankings[q["id"]][method]] !=
                                             [h["acn"] for h in deep[q["id"]][method]] for q in queries if q["category"]),
                "category_precision_at_10_delta": deep_summary[method]["category_precision_at_10"] - summary[method]["category_precision_at_10"],
            } for method in METHODS},
            "sensitivity_retrieval_config": asdict(replace(config, candidate_chunks=200)),
            "sensitivity_per_query": deep_rows,
            "detailed_rankings_local_path": str(rankings_path),
            "hardware": {"processor": platform.processor(), "platform": platform.platform()},
            "software": {"python": platform.python_version(), **{
                name: importlib.metadata.version(name)
                for name in ("torch", "sentence-transformers", "transformers", "psycopg")}},
            "postgres_version": conn.execute("SHOW server_version").fetchone()[0],
            "pgvector_version": conn.execute("SELECT extversion FROM pg_extension WHERE extname='vector'").fetchone()[0],
        }
        if scaleup:
            baseline = json.loads((output / "experiment_5k.json").read_text(encoding="utf-8"))
            record["comparison_to_5k"] = comparison(record, baseline)
            record["manifest_switch"] = {"previous": "eval/subset_manifest.json", "current": str(manifest_path),
                                          "previous_manifest_sha256": baseline["corpus"]["manifest_sha256"],
                                          "current_manifest_sha256": file_hash(manifest_path),
                                          "baseline_experiment": "eval/experiment_5k.json"}
            previous = (output / "results.md").read_text(encoding="utf-8").split("<!-- corpus-scaleup-20000 -->")[0]
            (output / "results.md").write_text(previous.rstrip() + "\n\n" + render_scaleup(record), encoding="utf-8")
        else:
            (output / "results.md").write_text(render_results(record), encoding="utf-8")
        (output / "experiment.json").write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        rankings_path.write_text(json.dumps(rankings, ensure_ascii=False), encoding="utf-8")
        print(json.dumps({"corpus": record["corpus"], "layer1_primary": record["layer1_primary"],
                          "judging_pool": record["judging_pool"], "controls_verified": list(controls)}, indent=2))
        return record
    finally:
        conn.execute("SELECT pg_advisory_unlock_shared(%s)", (LOCK,))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queries", type=Path, default=Path("eval/queries.jsonl"))
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--output", type=Path, default=Path("eval"))
    parser.add_argument("--pool-seed", type=int, default=20261116)
    args = parser.parse_args()
    if args.manifest is None:
        designation = Path("eval/current_corpus.json")
        args.manifest = Path(json.loads(designation.read_text(encoding="utf-8"))["manifest"]) if designation.exists() else Path("eval/subset_manifest.json")
    settings = Settings.from_env()
    provider = LocalEmbeddingProvider(settings)
    with psycopg.connect(settings.database_url, autocommit=True, connect_timeout=10) as conn:
        run(conn, settings, provider, args.queries, args.manifest, args.output, args.pool_seed)


if __name__ == "__main__":
    main()
