"""Construct Step 7C final assets once; no Ask, generation, grading, or scoring."""

import argparse
import csv
import hashlib
import importlib.metadata
import io
import json
import platform
import random
import re
import subprocess
from collections import Counter
from dataclasses import asdict
from datetime import UTC, date, datetime
from pathlib import Path

import psycopg
from psycopg.rows import dict_row

from safelens.aggregate import execute_count
from safelens.config import Settings
from safelens.embed import LocalEmbeddingProvider
from safelens.ingest import require_active_index
from safelens.reindex import LOCK
from safelens.retrieve import RetrievalConfig, search_dense, search_hybrid

QUERY_PATH = Path("eval/queries_final.jsonl")
POOL_PATH = Path("eval/judging_pool_final.csv")
RECORD_PATH = Path("eval/experiment_final_freeze.json")
DOC_PATH = Path("docs/FINAL_TEST_FREEZE.md")
LOCAL_PATH = Path("data/final_pool_construction_rankings.json")
SHUFFLE_SEED = 20261118
EXPECTED_IDS = ["ft-ri-1", "ft-ri-2", "ft-alt-1", "ft-alt-2", "ft-nmac-1", "ft-nmac-2",
                "ft-eq-1", "ft-eq-2", "ft-ctl-1", "ft-ctl-2", "ft-cnt-1", "ft-cnt-2"]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def file_hash(path):
    return sha(Path(path).read_bytes())


def frozen_inputs():
    paths = [*Path("src/safelens").rglob("*.py"), *Path("db/migrations").glob("*.sql"),
             Path("pyproject.toml"), Path("uv.lock"), Path("eval/queries.jsonl"), Path("eval/qrels.jsonl"),
             Path("eval/current_corpus.json"), Path("eval/subset_manifest.json"), Path("eval/corpus_manifest_20k.json"),
             Path("eval/judging_pool_step7_ablation_additions.csv"), Path("eval/results.md")]
    return {p.as_posix(): file_hash(p) for p in sorted(paths)}


def queries_from_kickoff():
    section = Path("CODEX_KICKOFF.md").read_text(encoding="utf-8").split("## Step 7C —", 1)[1]
    authored = re.findall(r'^- (ft-[a-z]+-\d+): "([^\n]+)"\r?$', section, re.MULTILINE)
    if [qid for qid, _ in authored] != EXPECTED_IDS:
        raise ValueError("Step 7C must contain exactly the twelve expected query IDs in order")
    queries = [{"id": qid, "layer": "final", "kind": "control" if qid.startswith("ft-ctl-")
                else "count" if qid.startswith("ft-cnt-") else "mechanism", "question": wording}
               for qid, wording in authored]
    data = "".join(json.dumps(q, ensure_ascii=False, separators=(",", ":")) + "\n" for q in queries).encode("utf-8")
    if Counter(q["kind"] for q in queries) != {"mechanism": 8, "control": 2, "count": 2}:
        raise ValueError("Invalid final query kind counts")
    # Compare the exact UTF-8 bytes of the question strings to the kickoff wording.
    parsed = [json.loads(line) for line in data.decode("utf-8").splitlines()]
    if any(row["question"].encode("utf-8") != wording.encode("utf-8")
           for row, (_, wording) in zip(parsed, authored)):
        raise ValueError("Final query wording changed during serialization")
    return queries, data


def render_doc(record, record_hash):
    lines = ["# Final test freeze — Step 7C", "",
             f"Freeze date: **{record['freeze_date']} (America/New_York)**. UTC construction timestamp: {record['timestamp_utc']}.", "",
             ("This is **construction only**. Evaluation runs: **0**. Final-query Ask/generation calls: **0**. "
             "No final pool row has been graded. No prompt, threshold, production code, or retrieval setting was changed."), "",
             "## Frozen artifacts", "",
             f"- `eval/queries_final.jsonl`: SHA-256 `{record['queries_sha256']}`.",
             f"- Original blank `eval/judging_pool_final.csv`: SHA-256 `{record['pool']['blank_csv_sha256']}`.",
             f"- Pool identity (sorted query/ACN/synopsis tuples, excluding grade/note): SHA-256 `{record['pool']['identity_sha256']}`.",
             f"- `eval/experiment_final_freeze.json`: SHA-256 `{record_hash}`.", "",
             ("The JSONL contains exactly the twelve supplied queries, with fields `id`, `layer=final`, `kind`, and "
             "`question`, in kickoff order. Question text is copied verbatim from CODEX_KICKOFF.md and checked byte-for-byte. "
             "Encoding is UTF-8 without BOM, LF newlines, final newline. There are eight mechanism queries, two controls, and two counts."), "",
             "## Corpus and construction checks", "",
             (f"Active corpus: **{record['corpus']['reports']:,} reports**, **{record['corpus']['chunks']:,} embedded chunks**, "
             f"ready build **{record['index']['id']}**. Snapshot SHA-256 `{record['corpus']['snapshot_sha256']}`. "
             "The active identity set and snapshot match `eval/corpus_manifest_20k.json`."), "",
             ("The exact fabricated ACN for `ft-ctl-2` was checked against the indexed report table and selected ACN manifest "
             "and is absent. Construction would stop if it existed; no substitution is permitted. The other control was not "
             "submitted to retrieval or Ask during construction."), "",
             ("Both count answers were computed directly by the production `safelens.aggregate.execute_count` SQL executor, "
             "with explicit metadata filters bound from the fixed questions. This is ground-truth construction, not a test of "
             "natural-language routing. The record stores the SQL, parameters, filters, count, and corpus denominator under "
             "`sealed_ground_truth`, with a canonical payload hash. These frozen answers are not printed here and were not "
             "submitted to Ask. The seal is an integrity freeze, not encryption; do not use the answers to tune the system."), "",
             "## Blinded mechanism judging pool", "",
             ("Only the eight mechanism questions were sent to dense retrieval and the frozen production hybrid "
             "(dense:BM25 10:1, report-level RRF k=60). Each leg uses 100 candidate chunks, max-score folding by ACN, "
             "then 50 candidate reports; pooling uses the returned top ten. No category filter, generation, grader, rewrite, "
             "reranker, evaluation metric, or relevance label was used. Both retrievers returned ten distinct reports per query."), "",
             (f"The union contains **{record['pool']['rows']} unique (query_id, ACN) pairs**, shuffled with seed **{SHUFFLE_SEED}**. "
             "CSV columns are exactly `query_id,acn,synopsis,grade,note`; all grade/note fields are blank. "
             "It hides retriever identity, ranks, and scores. The separate construction provenance remains in ignored `data/`; "
             "Cynthia should not consult retrieval provenance while judging."), "",
             "| Mechanism query | Unique report pairs |", "|---|---:|"]
    for qid, count in record["pool"]["per_query_counts"].items():
        lines.append(f"| {qid} | {count} |")
    lines += [f"| Total | {record['pool']['rows']} |", "", "## Freeze rules and handoff", "",
              ("1. Cynthia judges the mechanism pool **once**, blind to proposing retrievers: 2=directly relevant, "
              "1=partially relevant, 0=irrelevant. Read synopsis first and consult the indexed full narrative when needed. "
              "Reporter accounts are unverified; judge relevance to the exact question. Edit only grade/note; retain the "
              "frozen query/ACN identities and synopsis text. The initial blank-sheet hash changes when grades are filled; "
              "the pool identity hash must remain stable. Never copy development qrels onto different final questions."),
              ("2. No system may be run for scoring, generation, answer inspection, or tuning against these final questions "
              "during Step 7C. The sixteen retrieval calls above are solely for the expressly authorized pool construction, "
              "and the two SQL calls solely for sealed count truth. No result metrics or final answers were generated."),
              ("3. After human judgments are complete, **exactly one final evaluation run follows in Step 7D**. "
              "Do not run it now, repeatedly inspect scores, expand the pool opportunistically, or tune prompts/parameters "
              "against this set. Keep all development artifacts separate."),
              ("4. The experiment record seals all production Python/migration/dependency hashes and the public runtime "
              "configuration, including retrieval, generation, grader, model revisions, budgets, and calibrated prompts. "
              "Any retrieval/generation/grader code or configuration change after this freeze must be disclosed alongside "
              "any later re-run, with both source/config versions and the reason. Never silently overwrite or replace this test."),
              ("5. The construction command refuses to overwrite any final artifact. Verify the query hash and pool identities "
              "before importing judgments or running Step 7D. No final qrels are created until Cynthia supplies human grades."), "",
              ("Production source, development queries/qrels, corpus manifests, and historical results were checked unchanged "
              "by hash. The experiment records the construction-only checks. Prior tests run separately on their synthetic/development "
              "fixtures; they do not run this final test. Step 7D and Step 8 have not started."), ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--freeze-date", required=True, type=date.fromisoformat,
                        help="Client-local freeze date in America/New_York")
    args = parser.parse_args()
    destinations = [QUERY_PATH, POOL_PATH, RECORD_PATH, DOC_PATH, LOCAL_PATH]
    if any(p.exists() for p in destinations):
        raise SystemExit("Final artifacts already exist; refusing to reconstruct or overwrite the frozen test")
    protected = frozen_inputs()
    queries, query_data = queries_from_kickoff()
    settings = Settings.from_env()
    if (settings.lexical_backend, settings.retrieval_mode, settings.rrf_dense_weight,
            settings.rrf_lexical_weight) != ("bm25", "hybrid", 10, 1):
        raise ValueError("Construction requires the frozen production dense:BM25 10:1 default")
    calibration = json.loads(Path("eval/step7b_calibration_batch.json").read_text(encoding="utf-8"))
    if any(file_hash(p) != h for p, h in calibration["sources"].items()):
        raise ValueError("Production has changed since the final Step 7B calibration")
    manifest = json.loads(Path("eval/corpus_manifest_20k.json").read_text(encoding="utf-8"))
    config = RetrievalConfig()
    with psycopg.connect(settings.database_url, autocommit=True, connect_timeout=10) as conn:
        if not conn.execute("SELECT pg_try_advisory_lock_shared(%s)", (LOCK,)).fetchone()[0]:
            raise RuntimeError("Offline build active; freeze requires a stable ready corpus")
        try:
            require_active_index(conn, settings)
            with conn.cursor(row_factory=dict_row) as cursor:
                index = cursor.execute("SELECT * FROM index_meta WHERE status='ready'").fetchone()
            source_rows = conn.execute('SELECT acn,content_hash FROM reports ORDER BY acn COLLATE "C"').fetchall()
            snapshot = sha("".join(f"{a}:{h}\n" for a,h in source_rows).encode("utf-8"))
            counts = conn.execute("SELECT count(*),count(embedding),count(DISTINCT acn) FROM chunks").fetchone()
            if ([r[0] for r in source_rows] != manifest["selected_acns"] or snapshot != manifest["snapshot_sha256"]
                    or len(source_rows) != 20000 or index["report_count"] != 20000 or counts[0] != counts[1]
                    or counts[2] != 20000):
                raise ValueError("Active corpus differs from the ready 20k manifest")
            fake_acn = "777777777777777"
            control_question = next(q["question"] for q in queries if q["id"] == "ft-ctl-2")
            if re.search(r"ACN (\d+)", control_question).group(1) != fake_acn:
                raise ValueError("Absence check does not match the fixed control wording")
            exists = conn.execute("SELECT EXISTS(SELECT 1 FROM reports WHERE acn=%s)", (fake_acn,)).fetchone()[0]
            if exists or fake_acn in manifest["selected_acns"]:
                raise SystemExit("The specified final control ACN exists; stop without substitution")
            # Explicit truth filters only; do NOT invoke Ask or test the question router.
            count_truth = {
                "ft-cnt-1": execute_count(conn, {"year_start": 2019, "year_end": 2019, "anomaly_category": "Conflict NMAC"}),
                "ft-cnt-2": execute_count(conn, {"year_start": 2015, "year_end": 2015, "anomaly_category": None}),
            }
            provider = LocalEmbeddingProvider(settings)
            pool, rankings, per_query = [], {}, {}
            for q in queries:
                if q["kind"] != "mechanism":
                    continue
                rankings[q["id"]] = {}
                for name, search in (("dense", search_dense), ("hybrid", search_hybrid)):
                    # No category filter or evaluation metric is used; these are pooling calls only.
                    hits = search(q["question"], 10, conn=conn, settings=settings, provider=provider, config=config)
                    acns = [h["acn"] for h in hits]
                    if len(acns) != 10 or len(set(acns)) != 10:
                        raise ValueError("Expected ten unique report hits for each pooling leg")
                    rankings[q["id"]][name] = acns
                union = sorted({a for hits in rankings[q["id"]].values() for a in hits})
                per_query[q["id"]] = len(union)
                synopses = dict(conn.execute("SELECT acn,synopsis FROM reports WHERE acn=ANY(%s)", (union,)))
                pool.extend({"query_id": q["id"], "acn": a, "synopsis": synopses[a], "grade": "", "note": ""} for a in union)
                print(json.dumps({"construction_query": q["id"], "unique_pool_pairs": len(union)}), flush=True)
        finally:
            conn.execute("SELECT pg_advisory_unlock_shared(%s)", (LOCK,))
    random.Random(SHUFFLE_SEED).shuffle(pool)
    if len(pool) > 160 or len({(r["query_id"], r["acn"]) for r in pool}) != len(pool):
        raise ValueError("Invalid mechanism pool")
    csv_buffer = io.StringIO(newline="")
    writer = csv.DictWriter(csv_buffer, fieldnames=["query_id", "acn", "synopsis", "grade", "note"], lineterminator="\n")
    writer.writeheader()
    writer.writerows(pool)
    pool_data = csv_buffer.getvalue().encode("utf-8")
    identities = [{k:r[k] for k in ("query_id", "acn", "synopsis")} for r in sorted(pool, key=lambda r:(r["query_id"],r["acn"]))]
    identity_data = json.dumps(identities, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    local_data = json_bytes({"purpose": "pool construction provenance only; not evaluation and not for blinded judging", "rankings": rankings})
    if protected != frozen_inputs():
        raise RuntimeError("Protected production/development assets changed during construction")
    index["built_at"] = index["built_at"].isoformat()
    record = {
        "phase": "final_test_construction_only", "freeze_date": args.freeze_date.isoformat(),
        "freeze_date_timezone": "America/New_York", "timestamp_utc": datetime.now(UTC).isoformat(),
        "evaluation_runs": 0, "final_ask_calls": 0, "generation_calls": 0, "human_grades_assigned": 0,
        "pool_retrieval_calls": 16, "sql_ground_truth_calls": 2,
        "queries_path": QUERY_PATH.as_posix(), "queries_sha256": sha(query_data),
        "query_counts": dict(Counter(q["kind"] for q in queries)),
        "query_wording_verification": "question UTF-8 bytes exactly match the Step 7C kickoff strings; canonical JSONL fields id/layer/kind/question",
        "kickoff_sha256": file_hash("CODEX_KICKOFF.md"),
        "control_verification": {"query_id": "ft-ctl-2", "acn": fake_acn, "present_in_reports": False,
                                 "present_in_manifest": False, "snapshot_sha256": snapshot},
        "sealed_ground_truth": {"status": "sealed_for_step7d_only", "answers": count_truth,
                                "payload_sha256": sha(json_bytes(count_truth)),
                                "method": "production aggregate.execute_count; explicit metadata filter bindings, no Ask/router/generation"},
        "corpus": {"reports": len(source_rows), "chunks": counts[0], "null_embeddings": counts[0]-counts[1],
                   "snapshot_sha256": snapshot, "manifest_path": "eval/corpus_manifest_20k.json",
                   "manifest_sha256": file_hash("eval/corpus_manifest_20k.json"),
                   "source_dataset": manifest["source_dataset"], "source_revision": manifest["source_revision"]},
        "index": index, "retrieval_config": asdict(config),
        "production_configuration": {"index": settings.index_config, "lexical_backend": settings.lexical_backend,
             "retrieval_mode": settings.retrieval_mode, "rrf_dense_weight": settings.rrf_dense_weight,
             "rrf_lexical_weight": settings.rrf_lexical_weight, "bm25": {"k1":1.5,"b":.75,"epsilon":.25,
                  "preprocessing":"lowercase ASCII alphanumeric terms minus fixed sklearn English stoplist"},
             "agent_enabled": settings.agent_enabled, "agent_max_retries": settings.agent_max_retries,
             "agent_max_calls": settings.agent_max_calls, "rerank_enabled": settings.rerank_enabled,
             "rerank_model": settings.rerank_model, "rerank_revision": settings.rerank_revision,
             "llm_provider": settings.llm_provider, "llm_model": settings.llm_model,
             "llm_temperature": settings.llm_temperature, "llm_max_output_tokens": settings.llm_max_output_tokens,
             "llm_timeout": settings.llm_timeout},
        "pool": {"path": POOL_PATH.as_posix(), "rows": len(pool), "per_query_counts": per_query,
                 "blank_csv_sha256": sha(pool_data), "identity_sha256": sha(identity_data), "shuffle_seed": SHUFFLE_SEED,
                 "grades_assigned": 0, "notes_assigned": 0, "blinded": True,
                 "retrievers": ["dense", "production hybrid dense:BM25 10:1"],
                 "local_provenance_path": LOCAL_PATH.as_posix(), "local_provenance_sha256": sha(local_data)},
        "protected_sha256_before": protected, "protected_sha256_after": frozen_inputs(),
        "software": {"python": platform.python_version(), **{n:importlib.metadata.version(n) for n in
                     ("sentence-transformers", "torch", "rank-bm25", "scikit-learn", "psycopg", "langgraph", "openai")}},
        "git_head": subprocess.run(["git", "rev-parse", "HEAD"], check=True, capture_output=True, encoding="utf-8").stdout.strip(),
        "freeze_rules": {"human_judging_passes":1,"authorized_future_evaluation":"exactly one run in Step 7D, after Cynthia's judgments",
             "post_freeze_changes":"disclose code/config changes with any later rerun; never silently tune or replace the test"},
        "acceptance": {"wording_exact": True, "fake_acn_absent": True, "count_truth_sealed": True,
                       "pool_blank": True, "protected_assets_unchanged": True, "evaluation_not_run": True},
    }
    record_data = json_bytes(record)
    doc_data = render_doc(record, sha(record_data)).encode("utf-8")
    # Exclusive writes: a second invocation must not replace or refresh a frozen pool.
    for path, data in ((QUERY_PATH,query_data),(POOL_PATH,pool_data),(LOCAL_PATH,local_data),
                       (RECORD_PATH,record_data),(DOC_PATH,doc_data)):
        with path.open("xb") as target:
            target.write(data)
    if QUERY_PATH.read_bytes() != query_data:
        raise ValueError("Serialized final query bytes changed")
    print(json.dumps({"queries":12,"query_sha256":sha(query_data),"pool_rows":len(pool),"per_query_pool_counts":per_query,
                      "fake_acn_absent":True,"count_truth_recorded_without_printing_answers":True,
                      "ask_calls":0,"generation_calls":0,"evaluation_runs":0},indent=2))


if __name__ == "__main__":
    main()
