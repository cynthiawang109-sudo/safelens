"""Read-only Step 3 acceptance: exact subset, complete index, ungraded pool."""

import csv
import hashlib
import json
import runpy
from pathlib import Path

import psycopg
from psycopg.rows import dict_row

from safelens.config import Settings
from safelens.ingest import require_active_index
from safelens.subset import DEFAULT_PATHS, read_corpus, select_subset


def main():
    evaluator = runpy.run_path("eval/run_eval.py")
    manifest = json.loads(Path("eval/subset_manifest.json").read_text(encoding="utf-8"))
    actual_manifest = select_subset(read_corpus(DEFAULT_PATHS).values(), manifest["seed"], manifest["size"])
    assert manifest == actual_manifest, "Subset manifest is not deterministic/reproducible"
    queries = evaluator["load_queries"](Path("eval/queries.jsonl"))
    experiment = json.loads(Path("eval/experiment.json").read_text(encoding="utf-8"))
    rankings = json.loads(Path("data/eval_rankings.json").read_text(encoding="utf-8"))
    settings = Settings.from_env()
    with psycopg.connect(settings.database_url, autocommit=True, connect_timeout=10) as conn:
        require_active_index(conn, settings)
        with conn.cursor(row_factory=dict_row) as cursor:
            reports = {r["acn"]: r for r in cursor.execute("SELECT * FROM reports ORDER BY acn COLLATE \"C\"").fetchall()}
            builds = cursor.execute("SELECT * FROM index_meta WHERE status='ready'").fetchall()
        assert len(builds) == 1 and builds[0]["report_count"] == len(reports) == 5000
        assert builds[0]["id"] == experiment["index"]["id"]
        assert sorted(reports) == manifest["selected_acns"]
        digest = hashlib.sha256("".join(f"{acn}:{r['content_hash']}\n" for acn, r in reports.items()).encode("utf-8")).hexdigest()
        assert digest == manifest["snapshot_sha256"] == experiment["corpus"]["snapshot_sha256"]
        counts = conn.execute("SELECT count(*), count(embedding), count(DISTINCT acn) FROM chunks").fetchone()
        assert counts[0] == counts[1] == experiment["corpus"]["chunks"] and counts[2] == 5000
        assert not conn.execute("SELECT 1 FROM chunks GROUP BY acn,chunk_idx HAVING count(*)>1").fetchone()
        assert not conn.execute("SELECT 1 FROM chunks WHERE vector_dims(embedding) <> %s", (settings.embedding_dim,)).fetchone()
        assert not conn.execute(
            "SELECT 1 FROM chunks c JOIN reports r USING(acn) WHERE "
            "c.anomaly_codes IS DISTINCT FROM r.anomaly_codes OR "
            "c.flight_phase IS DISTINCT FROM r.flight_phase OR "
            "c.aircraft_category IS DISTINCT FROM r.aircraft_category OR "
            "c.report_month IS DISTINCT FROM r.report_month OR "
            "c.report_year IS DISTINCT FROM r.report_year"
        ).fetchone()
        controls = evaluator["verify_controls"](queries, reports, digest)
        with Path("eval/judging_pool.csv").open(encoding="utf-8", newline="") as source:
            reader = csv.DictReader(source)
            assert reader.fieldnames == evaluator["POOL_COLUMNS"]
            pool = list(reader)
        assert 0 < len(pool) <= 240
        assert len(pool) == len({(r["query_id"], r["acn"]) for r in pool})
        assert all(r["grade"] == r["note"] == "" for r in pool)
        assert pool == evaluator["judging_pool"](queries, rankings, reports, experiment["judging_pool"]["shuffle_seed"])
        assert experiment["unfiltered"] is True
        assert all(experiment["layer1_primary"][m]["queries"] == 20 for m in evaluator["METHODS"])
        assert all(experiment["all_category_queries"][m]["queries"] == 28 for m in evaluator["METHODS"])
        assert experiment["query_file_sha256"] == evaluator["file_hash"](Path("eval/queries.jsonl"))
        assert experiment["corpus"]["manifest_sha256"] == evaluator["file_hash"](Path("eval/subset_manifest.json"))
        assert experiment["judging_pool"]["sha256"] == evaluator["file_hash"](Path("eval/judging_pool.csv"))
        print(json.dumps({"status": "passed", "reports": len(reports), "embedded_chunks": counts[0],
                          "ready_build_id": builds[0]["id"], "queries": len(queries),
                          "judging_pool_rows": len(pool), "all_grades_and_notes_blank": True,
                          "controls_verified": list(controls), "snapshot_sha256": digest}, indent=2))


if __name__ == "__main__":
    main()
