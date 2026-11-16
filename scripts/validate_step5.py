"""Validate 20k growth, preserved Mini assets/vectors, and evaluation coverage."""

import hashlib
import json
from dataclasses import asdict
from pathlib import Path

import psycopg

from safelens.config import Settings
from safelens.corpus import select_expanded_corpus
from safelens.reindex import reindex
from safelens.subset import DEFAULT_PATHS, read_corpus


def main():
    protected = json.loads(Path("data/step5_protected_assets.json").read_text(encoding="utf-8"))
    for path, digest in protected.items():
        assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest, f"Protected asset changed: {path}"
    mini = json.loads(Path("eval/subset_manifest.json").read_text(encoding="utf-8"))
    manifest = json.loads(Path("eval/corpus_manifest_20k.json").read_text(encoding="utf-8"))
    source = read_corpus(DEFAULT_PATHS)
    recreated = select_expanded_corpus(source.values(), mini, manifest["seed"], manifest["size"])
    assert manifest == recreated
    assert set(mini["selected_acns"]) <= set(manifest["selected_acns"])
    assert len(manifest["selected_acns"]) == len(set(manifest["selected_acns"])) == 20000
    with Path("eval/qrels.jsonl").open(encoding="utf-8") as source_qrels:
        assert {json.loads(line)["acn"] for line in source_qrels if line.strip()} <= set(manifest["selected_acns"])
    records = [{**asdict(source[acn]), "content_hash": source[acn].content_hash} for acn in manifest["selected_acns"]]
    experiment = json.loads(Path("eval/experiment.json").read_text(encoding="utf-8"))
    designation = json.loads(Path("eval/current_corpus.json").read_text(encoding="utf-8"))
    assert Path(designation["manifest"]).resolve() == Path(experiment["manifest_path"]).resolve()
    settings = Settings.from_env()
    with psycopg.connect(settings.database_url, autocommit=True, connect_timeout=10) as conn:
        ready = conn.execute("SELECT id,report_count FROM index_meta WHERE status='ready'").fetchall()
        assert len(ready) == 1 and ready[0][1] == 20000
        acns = [r[0] for r in conn.execute("SELECT acn FROM reports ORDER BY acn COLLATE \"C\"").fetchall()]
        assert acns == manifest["selected_acns"]
        counts = conn.execute("SELECT count(*),count(embedding),count(DISTINCT acn) FROM chunks").fetchone()
        assert counts[0] == counts[1] and counts[0] > counts[2] == 20000
        assert conn.execute("SELECT count(*) FROM ingest_state").fetchone() == (20000,)
        rows = conn.execute("SELECT id,acn,chunk_idx,md5(text),md5(embedding::text) FROM chunks WHERE acn=ANY(%s) ORDER BY id",
                            (mini["selected_acns"],)).fetchall()
        original = json.loads(Path("data/step5_original_chunks.json").read_text(encoding="utf-8"))
        assert list(map(list, rows)) == original, "Mini chunk IDs, text, or embeddings changed"
        hashes = conn.execute("SELECT acn,content_hash FROM reports ORDER BY acn COLLATE \"C\"").fetchall()
        snapshot = hashlib.sha256("".join(f"{acn}:{digest}\n" for acn, digest in hashes).encode("utf-8")).hexdigest()
        assert snapshot == manifest["snapshot_sha256"] == experiment["corpus"]["snapshot_sha256"]

        def forbidden(settings):
            raise AssertionError("Idempotent repeat must not initialize the embedding provider")

        repeat = reindex(conn, settings, forbidden, replacement_reports=records, incremental=True)
        assert repeat["build_id"] == ready[0][0] and repeat["processed_reports"] == repeat["embedded_chunks"] == 0
        assert repeat["skipped_reports"] == 20000
    assert all(experiment["all_category_queries"][m]["queries"] == 28 for m in ("lexical", "dense", "hybrid"))
    text = Path("eval/results.md").read_text(encoding="utf-8")
    assert "20,000-report corpus" in text and "Layer-2 judged relevance" in text and "Delta" in text
    outcome = {"index_acceptance": "passed", "ready_build": ready[0][0], "reports": 20000,
               "chunks": counts[0], "null_embeddings": counts[0] - counts[1], "retained_mini_reports": len(mini["selected_acns"]),
               "unchanged_mini_chunks": len(rows), "idempotent_repeat": repeat,
               "protected_assets_unchanged": True, "deterministic_manifest": True,
               "layer2_status": experiment["judged_relevance"]["status"],
               "unjudged_top10_pairs": len(experiment["judged_relevance"].get("missing_pairs", []))}
    Path("docs/STEP5_VALIDATION.json").write_text(json.dumps(outcome, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(outcome, indent=2))


if __name__ == "__main__":
    main()
