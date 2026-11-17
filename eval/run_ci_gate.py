"""Development-only CI gate. Never imports or executes a final-test evaluator."""

import argparse
import hashlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean

import httpx
import psycopg
from psycopg.rows import dict_row

from safelens.aggregate import execute_count, map_count_filters
from safelens.config import Settings
from safelens.embed import LocalEmbeddingProvider
from safelens.evaluation import load_qrels
from safelens.ingest import require_active_index
from safelens.reindex import LOCK
from safelens.retrieve import search_dense, search_hybrid


def judged_precision(query_id, hits, qrels):
    """CI's explicit judged-only statistic; not the strict pooled evaluator."""
    keys = [(query_id, hit["acn"]) for hit in hits[:10]]
    known = [qrels[key] for key in keys if key in qrels]
    return {"query_id": query_id, "returned": len(keys), "judged": len(known),
            "coverage_at_10": len(known) / 10,
            "precision_on_judged": mean(g >= 1 for g in known) if known else None,
            "missing_acns": [acn for qid, acn in keys if (qid, acn) not in qrels]}


def load_development(config):
    # Paths are fixed: even a modified gate config cannot select the spent final set.
    if (config["split"], config["queries"], config["qrels"], config["corpus_manifest"]) != (
        "development", "eval/queries.jsonl", "eval/qrels.jsonl", "eval/corpus_manifest_20k.json"
    ):
        raise ValueError("CI accepts only the fixed development assets")
    queries = [json.loads(line) for line in Path(config["queries"]).read_text(encoding="utf-8").splitlines() if line]
    if len(queries) != 31 or any(q["id"].startswith("ft-") or q["layer"] not in (1, 2, "control") for q in queries):
        raise ValueError("Expected the 31 development queries only")
    ids = {q["id"]: q for q in queries}
    if len(ids) != len(queries) or any(ids[qid]["layer"] != 2 for qid in config["ask"]["mechanism_query_ids"]):
        raise ValueError("Ask mechanisms must be development Layer-2 queries")
    if ids[config["ask"]["control_query_id"]]["layer"] != "control":
        raise ValueError("Ask control must be a development control")
    return queries, ids


def run(config, base_url, result=None):
    queries, by_id = load_development(config)
    qrels = load_qrels(config["qrels"], {q["id"] for q in queries if q["layer"] == 2})
    manifest = json.loads(Path(config["corpus_manifest"]).read_text(encoding="utf-8"))
    settings = Settings.from_env()
    result = result if result is not None else {}
    result.update({"split": "development", "started_at": datetime.now(UTC).isoformat(),
              "github_run_id": os.getenv("GITHUB_RUN_ID"), "checks": [], "layer1": {}, "layer2": {},
              "aggregate": [], "ask": [], "provenance": {
                  p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
                  for p in (config["queries"], config["qrels"], config["corpus_manifest"], "eval/gates.json")}})

    def check(name, passed, **details):
        result["checks"].append({"name": name, "passed": bool(passed), **details})

    with psycopg.connect(settings.database_url, autocommit=True) as conn:
        if not conn.execute("SELECT pg_try_advisory_lock_shared(%s)", (LOCK,)).fetchone()[0]:
            raise RuntimeError("Offline index operation active")
        require_active_index(conn, settings)
        with conn.cursor(row_factory=dict_row) as cursor:
            corpus = cursor.execute("SELECT acn,content_hash,anomaly_codes FROM reports ORDER BY acn").fetchall()
        digest = hashlib.sha256("".join(f"{r['acn']}:{r['content_hash']}\n" for r in corpus).encode("utf-8")).hexdigest()
        if len(corpus) != 20000 or digest != manifest["snapshot_sha256"] or {r["acn"] for r in corpus} != set(manifest["selected_acns"]):
            raise ValueError("Active corpus does not match the sealed 20k development manifest")
        result["corpus"] = {"reports": len(corpus), "snapshot_sha256": digest}
        labels = {r["acn"]: r["anomaly_codes"] or [] for r in corpus}
        provider = LocalEmbeddingProvider(settings)
        category, judged = {"dense": [], "hybrid": []}, []
        for query in queries:
            if query["layer"] not in (1, 2):
                continue
            for method, search in (("dense", search_dense), ("hybrid", search_hybrid)):
                hits = search(query["query"], 10, conn=conn, settings=settings, provider=provider)
                if len({h["acn"] for h in hits}) != len(hits):
                    raise ValueError("Duplicate report in ranking")
                score = sum(query["category"] in labels[h["acn"]] for h in hits) / 10
                category[method].append({"query_id": query["id"], "category_precision_at_10": score})
                if method == "dense" and query["layer"] == 2:
                    judged.append(judged_precision(query["id"], hits, qrels))
        for method, rows in category.items():
            score = mean(r["category_precision_at_10"] for r in rows)
            result["layer1"][method] = {"category_precision_at_10": score, "queries": len(rows), "per_query": rows}
            check(f"layer1_{method}", score >= config["layer1"][method]["minimum"], actual=score, **config["layer1"][method])
        complete = all(r["precision_on_judged"] is not None for r in judged)
        score = mean(r["precision_on_judged"] for r in judged) if complete else None
        result["layer2"] = {"method": "dense", "precision_on_judged": score,
                            "coverage_at_10": sum(r["judged"] for r in judged) / (10 * len(judged)),
                            "definition": config["layer2"]["definition"], "per_query": judged}
        check("layer2_dense", score is not None and score >= config["layer2"]["minimum"], actual=score, minimum=config["layer2"]["minimum"])
        for expected in config["aggregate"]:
            mapped = map_count_filters(expected["question"])
            actual = execute_count(conn, mapped) if mapped == expected["filters"] else None
            passed = actual is not None and all(actual[k] == expected[k] for k in ("count", "denominator", "filters"))
            result["aggregate"].append({"id": expected["id"], "expected": expected, "actual": actual, "passed": passed})
            check(expected["id"], passed)
    if not os.getenv("OPENAI_API_KEY"):
        check("ask_smoke", False, blocked="Repository secret OPENAI_API_KEY is missing; no Ask requests attempted")
    else:
        with httpx.Client(base_url=base_url, timeout=240) as client:
            for qid in [*config["ask"]["mechanism_query_ids"], config["ask"]["control_query_id"]]:
                query = by_id[qid]
                response = client.post("/ask", json={"question": query["query"]})
                response.raise_for_status()
                body = response.json()
                valid = not body["validation"]["flagged"] and not body["validation"]["invalid_acns"]
                passed = valid and (body["status"] == "insufficient_evidence" and not body["citations"] if query["layer"] == "control"
                                    else body["status"] in ("answered", "partial") and bool(body["citations"]))
                result["ask"].append({"query_id": qid, "status": body["status"], "citations": len(body["citations"]), "passed": passed, "usage": body["usage"]})
                check(f"ask_{qid}", passed)
    result["passed"] = all(c["passed"] for c in result["checks"])
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--output", type=Path, default=Path("data/ci-eval.json"))
    args = parser.parse_args()
    result = {}
    try:
        run(json.loads(Path("eval/gates.json").read_text(encoding="utf-8")), args.base_url, result)
    except (OSError, ValueError, RuntimeError, httpx.HTTPError, psycopg.Error, KeyError) as error:
        # Do not serialize provider error bodies or credentials into public artifacts.
        result.update({"passed": False, "error_type": type(error).__name__, "message": "Gate execution failed; see workflow stage and protected integrity checks"})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k not in ("provenance",)}, indent=2))
    raise SystemExit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
