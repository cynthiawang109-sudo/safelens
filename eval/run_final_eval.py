"""Step 7D single frozen final run. Refuses any restart/resume after reservation."""

import argparse
import csv
import hashlib
import importlib.metadata
import json
import platform
import subprocess
import uuid
from collections import Counter
from datetime import UTC, date, datetime
from pathlib import Path
from time import perf_counter

import psycopg
from fastapi.testclient import TestClient
from final_run_support import (
    citation_average,
    citation_precision,
    count_comparison,
    file_hash,
    mean_cost,
    render,
    reserve_once,
    save_json,
)

from safelens.app import create_app
from safelens.bm25 import ready_index
from safelens.config import Settings
from safelens.evaluation import import_judgments, judged_metrics, load_qrels
from safelens.ingest import require_active_index
from safelens.reindex import LOCK
from safelens.retrieve import RetrievalConfig, search_dense, search_hybrid

FREEZE = Path("eval/experiment_final_freeze.json")
QUERIES = Path("eval/queries_final.jsonl")
POOL = Path("eval/judging_pool_final.csv")
QRELS = Path("eval/qrels_final.jsonl")
MARKER = Path("eval/final_test_run_once.json")
RECORD = Path("eval/experiment_step7d.json")
RAW = Path("data/final_test_raw.json")
NOTES = Path("docs/STEP7D_NOTES.md")


def preflight(settings):
    frozen = json.loads(FREEZE.read_text(encoding="utf-8"))
    doc = Path("docs/FINAL_TEST_FREEZE.md").read_text(encoding="utf-8")
    if file_hash(FREEZE) not in doc or file_hash(QUERIES) != frozen["queries_sha256"] or frozen["queries_sha256"] not in doc:
        raise ValueError("Frozen query/record SHA-256 differs from freeze document")
    for p, digest in frozen["protected_sha256_before"].items():
        if file_hash(p) != digest:
            raise ValueError(f"Sealed production/development asset mismatch: {p}")
    expected = frozen["production_configuration"]
    actual = {k: getattr(settings,k) for k in expected if k not in ("index", "bm25")}
    actual["index"] = settings.index_config
    actual["bm25"] = {"k1":1.5,"b":.75,"epsilon":.25,
                      "preprocessing":"lowercase ASCII alphanumeric terms minus fixed sklearn English stoplist"}
    if actual != expected:
        raise ValueError("Production runtime configuration differs from freeze")
    for package, version in frozen["software"].items():
        current = platform.python_version() if package == "python" else importlib.metadata.version(package)
        if current != version:
            raise ValueError(f"Frozen runtime software differs: {package}")
    with POOL.open(encoding="utf-8", newline="") as source:
        reader = csv.DictReader(source)
        rows = list(reader)
        if reader.fieldnames != ["query_id", "acn", "synopsis", "grade", "note"]:
            raise ValueError("Pool columns changed")
    identities = [{k:r[k] for k in ("query_id", "acn", "synopsis")}
                  for r in sorted(rows, key=lambda r:(r["query_id"], r["acn"]))]
    identity = hashlib.sha256(json.dumps(identities, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()
    if identity != frozen["pool"]["identity_sha256"] or identity not in doc:
        raise ValueError("Frozen pool identity differs")
    if len(rows) != 89 or len({(r["query_id"],r["acn"]) for r in rows}) != 89:
        raise ValueError("Expected 89 unique human-judged pairs")
    histogram = Counter(r["grade"].strip() for r in rows)
    if histogram != {"2":32,"1":52,"0":5}:
        raise ValueError("Human judgment histogram differs from Step 7D declaration")
    queries = [json.loads(line) for line in QUERIES.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(queries) != 12 or Counter(q["kind"] for q in queries) != {"mechanism":8,"control":2,"count":2}:
        raise ValueError("Invalid frozen query set")
    commit = subprocess.run(["git","log","--diff-filter=A","-1","--format=%H","--",QUERIES.as_posix()],
                            check=True,capture_output=True,encoding="utf-8").stdout.strip()
    if not commit:
        raise ValueError("Frozen queries are not committed")
    for path in (QUERIES, FREEZE):
        blob = subprocess.run(["git","show",f"{commit}:{path.as_posix()}"], check=True, capture_output=True).stdout
        if hashlib.sha256(blob).hexdigest() != file_hash(path):
            raise ValueError("Freeze commit contents differ from frozen artifacts")
    truth = frozen["sealed_ground_truth"]
    truth_data = (json.dumps(truth["answers"],ensure_ascii=False,indent=2)+"\n").encode()
    if hashlib.sha256(truth_data).hexdigest() != truth["payload_sha256"]:
        raise ValueError("Sealed count ground truth hash differs")
    manifest = json.loads(Path(frozen["corpus"]["manifest_path"]).read_text(encoding="utf-8"))
    with psycopg.connect(settings.database_url,autocommit=True,connect_timeout=10) as conn:
        require_active_index(conn,settings)
        pairs = conn.execute('SELECT acn,content_hash FROM reports ORDER BY acn COLLATE "C"').fetchall()
        snapshot = hashlib.sha256("".join(f"{a}:{h}\n" for a,h in pairs).encode()).hexdigest()
        counts = conn.execute("SELECT count(*),count(embedding),count(DISTINCT acn) FROM chunks").fetchone()
        if snapshot != frozen["corpus"]["snapshot_sha256"] or [a for a,_ in pairs] != manifest["selected_acns"]:
            raise ValueError("Frozen corpus snapshot/identities differ")
        if len(pairs) != 20000 or counts != (frozen["corpus"]["chunks"], frozen["corpus"]["chunks"], 20000):
            raise ValueError("Frozen report/chunk/embedding counts differ")
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM index_meta WHERE status='ready'")
            index = dict(zip([c.name for c in cursor.description],cursor.fetchone()))
        index["built_at"] = index["built_at"].isoformat()
        if index != frozen["index"]:
            raise ValueError("Ready index metadata changed since freeze")
    return frozen, queries, rows, {"passed":True,"query_sha256":file_hash(QUERIES),
        "pool_identity_sha256":identity,"graded_pool_sha256":file_hash(POOL),
        "freeze_record_sha256":file_hash(FREEZE),"freeze_commit":commit,
        "production_design_commit":frozen["git_head"],"protected_sha256":frozen["protected_sha256_before"],
        "public_runtime_configuration":actual,"software":frozen["software"],
        "corpus_snapshot_sha256":snapshot,"ready_index_id":index["id"],
        "human_grade_histogram":dict(histogram),"post_freeze_production_changes":[]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--preflight-only",action="store_true")
    action.add_argument("--execute-once",action="store_true")
    parser.add_argument("--run-date",type=date.fromisoformat)
    args = parser.parse_args()
    if any(p.exists() for p in (MARKER,RECORD,RAW,NOTES)):
        raise SystemExit("A final-run artifact already exists. No second invocation or automatic resume is permitted.")
    settings = Settings.from_env()
    frozen,queries,pool,flight = preflight(settings)
    if args.preflight_only:
        print(json.dumps({"preflight_passed":True,"freeze_commit":flight["freeze_commit"],
                          "query_sha256":flight["query_sha256"],"graded_pool_rows":len(pool),
                          "final_run_started":False},indent=2))
        return
    if args.run_date is None:
        parser.error("--execute-once requires --run-date from the client timezone")
    if QRELS.exists():
        raise SystemExit("Final qrels already exist; refusing to overwrite or silently reuse an unexplained import")
    # Only adapt the legacy validator's query-layer schema. Final question bytes stay unchanged.
    adapted = [{"id":q["id"],"layer":2} for q in queries if q["kind"]=="mechanism"]
    adapter_path = Path("data/final_judgment_import_adapter.jsonl")
    adapter_path.write_bytes("".join(json.dumps(q)+"\n" for q in adapted).encode())
    expected_pairs = {(r["query_id"],r["acn"]) for r in pool}
    imported = import_judgments(POOL,QRELS,adapter_path,Path(frozen["corpus"]["manifest_path"]),expected_pairs)
    qrels = load_qrels(QRELS,{q["id"] for q in adapted})
    if imported != 89 or len(qrels) != 89:
        raise ValueError("Final import must contain 89 unique validated judgments")
    record = {"status":"initializing","run_id":str(uuid.uuid4()),"run_count":1,
              "run_date":args.run_date.isoformat(),"run_date_timezone":"America/New_York",
              "preflight":flight,"qrels_import":{"rows":imported,"sha256":file_hash(QRELS),
                   "tool":"safelens.evaluation.import_judgments (unchanged)","path":QRELS.as_posix(),
                   "legacy_layer_adapter":adapter_path.as_posix(),"development_qrels_changed":False},
              "evaluator_source_sha256":file_hash(__file__),
              "reporting_source_sha256":file_hash("eval/final_run_support.py"),
              "transport":"FastAPI TestClient HTTP; frozen production app; real OpenAI provider",
              "operations":[],"raw_checkpoint":RAW.as_posix()}
    raw = {"run_id":record["run_id"],"retrieval":{},"ask":{}}
    started = False
    original_results = Path("eval/results.md").read_bytes()
    try:
        with psycopg.connect(settings.database_url,autocommit=True,connect_timeout=10) as conn:
            if not conn.execute("SELECT pg_try_advisory_lock_shared(%s)",(LOCK,)).fetchone()[0]:
                raise RuntimeError("Offline build active")
            try:
                require_active_index(conn,settings)
                with TestClient(create_app(settings)) as client:
                    warmup = perf_counter()
                    ready_index(conn)
                    client.app.state.embedding.embed_query("aviation safety")
                    record["nonfinal_warmup_ms"] = (perf_counter()-warmup)*1000
                    # Integrity again before the first final-query call, after local initialization.
                    for p,digest in flight["protected_sha256"].items():
                        if file_hash(p)!=digest:
                            raise ValueError("Frozen assets changed before reservation")
                    record["started_at_utc"] = datetime.now(UTC).isoformat()
                    reserve_once(MARKER,{"run_id":record["run_id"],"started_at_utc":record["started_at_utc"],
                                        "policy":"one execution only; failed/partial runs are not resumed",
                                        "query_sha256":flight["query_sha256"],
                                        "evaluator_source_sha256":record["evaluator_source_sha256"]})
                    started = True
                    record["status"] = "running"
                    save_json(RECORD,record)
                    save_json(RAW,raw)
                    config = RetrievalConfig()
                    for query in queries:
                        if query["kind"]!="mechanism":
                            continue
                        qid = query["id"]
                        raw["retrieval"][qid] = {}
                        for method,search in (("dense",search_dense),("hybrid",search_hybrid)):
                            op={"stage":"retrieval","query_id":qid,"method":method,"status":"started"}
                            record["operations"].append(op)
                            save_json(RECORD,record)
                            hits=search(query["question"],10,conn=conn,settings=settings,
                                        provider=client.app.state.embedding,config=config)
                            if len(hits)!=10 or len({h["acn"] for h in hits})!=10:
                                raise ValueError("Retrieval did not return ten unique reports")
                            if any((qid,h["acn"]) not in qrels for h in hits):
                                raise ValueError("Strict final retrieval coverage is incomplete")
                            raw["retrieval"][qid][method]=hits
                            op["status"]="completed"
                            save_json(RAW,raw)
                            save_json(RECORD,record)
                        print(json.dumps({"stage":"retrieval_completed","query_id":qid,"top10_coverage":"complete"}),flush=True)
                    for query in queries:
                        qid=query["id"]
                        op={"stage":"ask","query_id":qid,"status":"started"}
                        record["operations"].append(op)
                        save_json(RECORD,record)
                        before=perf_counter()
                        response=client.post("/ask",json={"question":query["question"]})
                        if response.status_code!=200:
                            raise RuntimeError(f"Frozen Ask returned HTTP {response.status_code}; no retry")
                        result=response.json()
                        result["http_latency_ms"]=(perf_counter()-before)*1000
                        raw["ask"][qid]=result
                        op["status"]="completed"
                        save_json(RAW,raw)
                        save_json(RECORD,record)
                        print(json.dumps({"stage":"ask_completed","query_id":qid,"kind":query["kind"],
                                          "status":result["status"]}),flush=True)
            finally:
                conn.execute("SELECT pg_advisory_unlock_shared(%s)",(LOCK,))
        # No further system calls below: score and publish this one set of observations.
        metrics=judged_metrics(adapted,raw["retrieval"],qrels)
        citation_rows=[{**citation_precision(q["id"],raw["ask"][q["id"]],qrels),"kind":q["kind"]} for q in queries]
        controls=[{"query_id":q["id"],"status":raw["ask"][q["id"]]["status"],
                   "invalid_acns":raw["ask"][q["id"]]["validation"]["invalid_acns"],
                   "passed":raw["ask"][q["id"]]["status"]=="insufficient_evidence"
                   and not raw["ask"][q["id"]]["validation"]["invalid_acns"]}
                  for q in queries if q["kind"]=="control"]
        counts=[count_comparison(q["id"],raw["ask"][q["id"]],frozen["sealed_ground_truth"]["answers"][q["id"]])
                for q in queries if q["kind"]=="count"]
        mechanism_status=Counter(raw["ask"][q["id"]]["status"] for q in queries if q["kind"]=="mechanism")
        observations=[f"- Mechanism responses: {dict(mechanism_status)}. These statuses are observed outputs, not independent claim-level faithfulness judgments.",
                      f"- Controls: {sum(c['passed'] for c in controls)}/2 passed; aggregate counts: {sum(c['exact_match'] for c in counts)}/2 exact matches. Failures were not corrected or retried.",
                      "- Both strict retrieval tables have complete frozen judgment coverage. Citation coverage can be lower because the production workflow can rewrite queries or cite reports outside the original frozen pool; those pairs remain unknown.",
                      "- Eight authored mechanism questions and two controls are a small single frozen sample; no broad superiority or safety conclusions follow."]
        for c in counts:
            if not c["exact_match"]:
                observations.append(f"- {c['query_id']} did not return the sealed aggregate result. System aggregate payload: {c['system_aggregate']}. The unchanged routing behavior is disclosed, not patched.")
        for p,digest in flight["protected_sha256"].items():
            if file_hash(p)!=digest:
                raise ValueError("Frozen assets changed during the final run")
        record.update(status="completed",completed_at_utc=datetime.now(UTC).isoformat(),
            retrieval_metrics=metrics,retrieval_judgment_coverage={"dense":1.0,"hybrid":1.0},
            ask={q["id"]:{"kind":q["kind"],"question":q["question"],
                          **{k:raw["ask"][q["id"]][k] for k in ("status","answer","validation","trace","usage","aggregate","http_latency_ms")},
                          "citation_acns":sorted({c["acn"] for c in raw["ask"][q["id"]]["citations"]})} for q in queries},
            ask_mean_cost=mean_cost(raw["ask"]),controls=controls,counts=counts,citation_per_query=citation_rows,
            citation_summary={"all answered/partial":citation_average(citation_rows),
                              "mechanism answered/partial":citation_average([r for r in citation_rows if r["kind"]=="mechanism"])},
            observations=observations,post_run_protected_hashes={p:file_hash(p) for p in flight["protected_sha256"]},
            frozen_assets_unchanged=True,step8_started=False)
        save_json(RECORD,record)
        notes=render(record)
        NOTES.write_bytes(("# Step 7D — single frozen final evaluation\n\n"+notes).encode("utf-8"))
        if Path("eval/results.md").read_bytes()!=original_results:
            raise ValueError("Historical results changed before publication")
        with Path("eval/results.md").open("ab") as target:
            target.write(("\n\n"+notes).encode("utf-8"))
        print(json.dumps({"run_status":"completed","run_count":1,"retrieval":metrics["averages"],
                          "controls_passed":sum(c["passed"] for c in controls),
                          "counts_exact_match":sum(c["exact_match"] for c in counts),
                          "mean_cost":record["ask_mean_cost"]},indent=2))
    except BaseException as error:  # noqa: BLE001 -- Seal interruption/failure state; never retry this run.
        if started:
            record.update(status="failed_stopped_no_retry",stopped_at_utc=datetime.now(UTC).isoformat(),
                          error={"type":type(error).__name__,"message":"Final run stopped; no retry or resume permitted"})
            save_json(RECORD,record)
            save_json(RAW,raw)
        print(json.dumps({"run_status":"stopped","final_query_calls_started":started,
                          "error_type":type(error).__name__,"no_retry_attempted":True}),flush=True)
        raise SystemExit(1) from None


if __name__=="__main__":
    main()
