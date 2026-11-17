"""Five-config Step 7 development ablation with real generation and safe checkpoints."""

import hashlib
import importlib.metadata
import json
import random
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean
from time import perf_counter

from run_eval import file_hash, load_queries, write_pool

from safelens.agent import AgentEngine, AgentOptions
from safelens.app import indexed_connection
from safelens.bm25 import ready_index
from safelens.config import Settings
from safelens.embed import LocalEmbeddingProvider
from safelens.evaluation import judged_metrics, load_qrels
from safelens.lexical_bakeoff import coverage_metrics
from safelens.llm import OpenAILLMProvider
from safelens.rerank import LocalReranker

DESIGN = Path("eval/step7_ablation_design.json")
SOURCES = ["src/safelens/agent.py", "src/safelens/aggregate.py", "src/safelens/retrieve.py",
           "src/safelens/bm25.py", "src/safelens/rerank.py", "src/safelens/llm.py",
           "src/safelens/generate.py", "src/safelens/config.py"]
FROZEN = ["eval/queries.jsonl", "eval/qrels.jsonl", "eval/subset_manifest.json", "eval/corpus_manifest_20k.json"]


def summarize(queries, responses, qrels):
    judged = [q for q in queries if q["layer"] == 2]
    rows = [{"query_id": q["id"], **coverage_metrics(responses[q["id"]]["results"], q["id"], qrels)} for q in judged]
    defined = [r for r in rows if r["judged"]]
    signals = {m: mean(r[m] for r in defined) if defined else None for m in ("precision_at_10", "mrr", "ndcg_at_10")}
    signals.update(coverage_at_10=mean(r["coverage_at_10"] for r in rows), defined_queries=len(defined))
    complete = [q for q in judged if all((q["id"], h["acn"]) in qrels for h in responses[q["id"]]["results"][:10])]
    full = None
    if complete:
        rankings = {q["id"]: {"configuration": responses[q["id"]]["results"][:10]} for q in complete}
        full = judged_metrics(complete, rankings, qrels)
    controls = [{"query_id": q["id"], "passed": responses[q["id"]]["status"] == "insufficient_evidence"
                 and not responses[q["id"]]["validation"]["invalid_acns"],
                 "answer": responses[q["id"]]["answer"], "status": responses[q["id"]]["status"]}
                for q in queries if q["layer"] == "control"]
    per_stage = defaultdict(lambda: {"latency_ms": 0., "input_tokens": 0, "output_tokens": 0, "model_calls": 0})
    for response in responses.values():
        for event in response["trace"]:
            for metric in per_stage[event["stage"]]:
                per_stage[event["stage"]][metric] += event[metric] or 0
    return {"full_eight_query_status": "ready" if len(complete) == len(judged) else "pending judgments",
            "normal_answer_statuses": {status: sum(responses[q["id"]]["status"] == status for q in judged)
                                       for status in ("answered", "partial", "insufficient_evidence")},
            "fully_judged_queries": len(complete), "fully_judged_subset_metrics": full,
            "partial_signals": signals, "coverage_per_query": rows, "controls": controls,
            "controls_passed": sum(c["passed"] for c in controls),
            "mean_retries": mean(r["usage"]["retries"] for r in responses.values()),
            "mean_model_calls": mean(r["usage"]["model_calls"] for r in responses.values()),
            "mean_input_tokens": mean(r["usage"]["input_tokens"] for r in responses.values()),
            "mean_output_tokens": mean(r["usage"]["output_tokens"] for r in responses.values()),
            "mean_latency_ms": mean(r["usage"]["latency_ms"] for r in responses.values()),
            "per_stage_mean_per_question": {s: {k: v / len(responses) for k, v in data.items()} for s, data in per_stage.items()}}


def render(record):
    lines = ["<!-- agent-ablation-step7 -->", "## Step 7 Part 3 — development ablation", "",
             ("Eight existing judged questions plus the three existing controls; real OpenAI generation in every configuration, "
             "same reporter-account prompt and citation validation, no category filter. Results name the runtime qrels hash "
             f"`{record['protected_hashes']['eval/qrels.jsonl']}`. No final-test questions were created."), "",
             "### Judged retrieval (complete-query subsets only)", "",
             ("Metrics use final-attempt top-ten unique reports before generation filtering. A query contributes strict P@10/MRR/nDCG "
             "only when every returned top-ten pair has a human judgment; fixed P@10 denominator 10, linear nDCG gains. "
             "Different complete-query subsets are not fair head-to-head scores. Percentages are overall top-ten coverage across all eight queries; "
             "contributing strict-score subsets themselves are fully judged. Full eight-query rows remain pending where any pair is unjudged."), "",
             "| Configuration | Complete queries / 8 | Strict P@10 (coverage) | MRR (coverage) | nDCG@10 (coverage) | Full eight-query status |",
             "|---|---:|---:|---:|---:|---|"]
    def cell(value, coverage):
        return ("N/A" if value is None else f"{value:.4f}") + f" ({coverage:.1%})"
    for name, row in record["summaries"].items():
        scores = row["fully_judged_subset_metrics"]
        avg = scores["averages"]["configuration"] if scores else {}
        coverage = row["partial_signals"]["coverage_at_10"]
        lines.append(f"| {name} | {row['fully_judged_queries']} | " + " | ".join(cell(avg.get(m), coverage) for m in ("precision_at_10", "mrr", "ndcg_at_10")) + f" | {row['full_eight_query_status']} |")
    lines += ["", "### Partial-coverage development signals", "",
              ("These are **partial-coverage development signals**, not full judged scores or grounds for choosing a default. "
              "Same Step 6 protocol: remove unknown top-ten pairs, precision=relevant/judged, condensed-rank MRR/DCG, "
              "known-qrels ideal at the same judged depth; undefined when no judged hits, excluded from means. "
              "Coverage is judged/10 including underfill. Never zero-fill unknown pairs. Original pooling and condensation bias comparisons."), "",
              "| Configuration | Precision proxy (coverage) | MRR (coverage) | nDCG proxy (coverage) | Defined queries / 8 |",
              "|---|---:|---:|---:|---:|"]
    for name, row in record["summaries"].items():
        avg = row["partial_signals"]
        lines.append(f"| {name} | " + " | ".join(cell(avg[m], avg["coverage_at_10"]) for m in ("precision_at_10", "mrr", "ndcg_at_10")) + f" | {avg['defined_queries']} |")
    lines += ["", "### Abstention and per-question cost", "",
              ("Means cover all eleven requests. Actual provider input/output tokens and total wall latency are reported; "
              "no dollar estimate is inferred. Initialization and warmup excluded. Model calls are capped at six, rewrites at two. "
              "Grading/rewrite and generation tokens are counted separately in each trace. Rerank is local CPU over at most 50 fused reports, "
              "one representative chunk each, pair truncation at 512 tokens. Cold model/index warmup measurements are in the record."), "",
              "| Configuration | Controls correct / 3 | Mean retries | Mean calls | Mean input tokens | Mean output tokens | Mean latency s |",
              "|---|---:|---:|---:|---:|---:|---:|"]
    for name, row in record["summaries"].items():
        lines.append(f"| {name} | {row['controls_passed']} | {row['mean_retries']:.2f} | {row['mean_model_calls']:.2f} | {row['mean_input_tokens']:.1f} | {row['mean_output_tokens']:.1f} | {row['mean_latency_ms']/1000:.2f} |")
    lines += ["", "### Normal-query answer statuses (eight queries)", "",
              ("These are observed statuses, not human answerability or faithfulness judgments. Frequent refusals can be over-abstention; "
              "passing three controls does not establish useful answers on normal questions."), "",
              "| Configuration | Answered | Partial | Insufficient evidence |", "|---|---:|---:|---:|"]
    for name, row in record["summaries"].items():
        status = row["normal_answer_statuses"]
        lines.append(f"| {name} | {status['answered']} | {status['partial']} | {status['insufficient_evidence']} |")
    lines += ["", "### Per-stage mean cost per question", "",
              "| Configuration | Stage | Latency ms | Input tokens | Output tokens | Model calls |",
              "|---|---|---:|---:|---:|---:|"]
    for name, row in record["summaries"].items():
        for stage, data in row["per_stage_mean_per_question"].items():
            lines.append(f"| {name} | {stage} | {data['latency_ms']:.2f} | {data['input_tokens']:.1f} | {data['output_tokens']:.1f} | {data['model_calls']:.2f} |")
    lines += ["", "### What the stages buy and cost", "", *record["findings"], "",
              (f"All **{record['missing_pairs_count']}** new final top-ten query/ACN pairs are exported as "
              "`eval/judging_pool_step7_ablation_additions.csv`, blinded, shuffled, with blank grades/notes. "
              "They are not automatic judgments and do not alter qrels. Full response passages remain in ignored data; "
              "per-question outcomes, grades, trace costs, configuration and source hashes are in `eval/experiment_step7_ablation.json`."), "",
              ("Reproduce: `uv run python eval/run_agent_ablation.py` with UTF-8 variables set. Matching-source checkpoints reuse "
              "the original real-provider responses; changed code/configuration gets a separate cache fingerprint. "
              "This ablation cannot establish general superiority on eight repeatedly inspected development queries. Step 8 has not started."), ""]
    return "\n".join(lines)


def main():
    settings = Settings.from_env()
    design = json.loads(DESIGN.read_text(encoding="utf-8"))
    queries = [q for q in load_queries(Path("eval/queries.jsonl")) if q["layer"] in (2, "control")]
    protected = {p: file_hash(p) for p in FROZEN}
    sources = {p: file_hash(p) for p in SOURCES}
    qrels = load_qrels("eval/qrels.jsonl", {q["id"] for q in queries if q["layer"] == 2})
    fingerprint_data = {"sources": sources, "inputs": protected, "design": design,
                        "llm_model": settings.llm_model, "rerank_model": settings.rerank_model,
                        "rerank_revision": settings.rerank_revision, "temperature": settings.llm_temperature}
    fingerprint = hashlib.sha256(json.dumps(fingerprint_data, sort_keys=True).encode()).hexdigest()
    checkpoint = Path(f"data/step7_ablation_{fingerprint[:16]}.json")
    responses = json.loads(checkpoint.read_text(encoding="utf-8")) if checkpoint.exists() else {}
    embedding = LocalEmbeddingProvider(settings)
    llm = OpenAILLMProvider(settings)
    reranker = LocalReranker(settings)
    with indexed_connection(settings) as conn:
        ready = conn.execute("SELECT id,report_count FROM index_meta WHERE status='ready'").fetchone()
        if ready[1] != 20000:
            raise ValueError("Ablation requires the ready 20k corpus")
        warmup = perf_counter()
        _, bm25_stats = ready_index(conn)
        embedding.embed_query("aviation safety")
        reranker.rerank("aviation safety", [{"acn": "warmup", "text": "A pilot reported an approach warning.", "score": 0}])
        warmup_ms = (perf_counter() - warmup) * 1000
        for config in design["configurations"]:
            name = config["name"]
            options = AgentOptions(**{k: v for k, v in config.items() if k != "name"})
            responses.setdefault(name, {})
            for query in queries:
                qid = query["id"]
                if qid not in responses[name]:
                    response = AgentEngine(conn, settings, embedding, llm, options=options, reranker=reranker).run(query["query"])
                    responses[name][qid] = response
                    checkpoint.write_text(json.dumps(responses, indent=2), encoding="utf-8")
                response = responses[name][qid]
                print(json.dumps({"configuration": name, "query_id": qid, "status": response["status"],
                                  "retries": response["usage"]["retries"], "latency_ms": response["usage"]["latency_ms"]}), flush=True)
        missing = sorted({(q["id"], h["acn"]) for q in queries if q["layer"] == 2
                          for results in responses.values() for h in results[q["id"]]["results"][:10]
                          if (q["id"], h["acn"]) not in qrels})
        synopses = dict(conn.execute("SELECT acn,synopsis FROM reports WHERE acn=ANY(%s)", (sorted({a for _, a in missing}),)).fetchall())
    pool = [{"query_id": qid, "acn": acn, "synopsis": synopses[acn], "grade": "", "note": ""} for qid, acn in missing]
    random.Random(20261117).shuffle(pool)
    write_pool(Path("eval/judging_pool_step7_ablation_additions.csv"), pool, preserve_judgments=True)
    summaries = {name: summarize(queries, result, qrels) for name, result in responses.items()}
    findings = []
    comparisons = [("Hybrid-10:1", "Dense-only", "BM25 fusion"), ("Hybrid + Rerank", "Hybrid-10:1", "Local reranking"),
                   ("Hybrid + Rewrite", "Hybrid-10:1", "Conditional grading and rewrite"), ("Full Agentic", "Hybrid + Rewrite", "Reranking on top of grading/rewrite")]
    for new, old, label in comparisons:
        a, b = summaries[new], summaries[old]
        findings.append(f"- {label}: controls {b['controls_passed']}/3 → {a['controls_passed']}/3; "
                        f"mean latency delta {(a['mean_latency_ms']-b['mean_latency_ms'])/1000:+.2f}s, "
                        f"input-token delta {a['mean_input_tokens']-b['mean_input_tokens']:+.1f}, output-token delta {a['mean_output_tokens']-b['mean_output_tokens']:+.1f}. "
                        f"Judged coverage {b['partial_signals']['coverage_at_10']:.1%} → {a['partial_signals']['coverage_at_10']:.1%}; "
                        "missing judgments prevent a fair full eight-query relevance win claim.")
    findings.append("- Keep the adopted 10:1 retrieval settings. Reranking remains disabled by default; its added latency is not earned by complete human-judged evidence here. The bounded grading/rewrite path is available for Ask evidence sufficiency, with its measured cost visible; no additional rewrite or rerank tuning was performed.")
    if protected != {p: file_hash(p) for p in FROZEN}:
        raise RuntimeError("Frozen evaluation assets changed")
    record = {"timestamp": datetime.now(UTC).isoformat(), "split": "development", "design": design,
              "design_sha256": file_hash(DESIGN), "protected_hashes": protected, "source_hashes": sources,
              "fingerprint": fingerprint, "local_checkpoint": str(checkpoint), "ready_build": ready[0],
              "bm25_cache": bm25_stats, "warmup_ms": warmup_ms,
              "models": {"embedding": settings.embedding_model, "embedding_revision": settings.embedding_revision,
                         "llm": settings.llm_model, "reranker": settings.rerank_model, "reranker_revision": settings.rerank_revision},
              "software": {n: importlib.metadata.version(n) for n in ("langgraph", "openai", "sentence-transformers", "rank-bm25")},
              "summaries": summaries, "findings": findings, "missing_pairs_count": len(missing), "missing_pairs": missing,
              "per_question": {name: {qid: {"status": r["status"], "answer": r["answer"], "usage": r["usage"],
                                          "trace": r["trace"], "top10_acns": [h["acn"] for h in r["results"]],
                                          "citation_acns": sorted({c["acn"] for c in r["citations"]}),
                                          "validation": r["validation"]} for qid, r in result.items()}
                               for name, result in responses.items()}}
    Path("eval/experiment_step7_ablation.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    notes = render(record)
    part1 = json.loads(Path("eval/experiment_step7_part1.json").read_text(encoding="utf-8"))
    from safelens.step7_report import render_part1, render_part2
    smoke = json.loads(Path("docs/STEP7_PART2_SMOKE.json").read_text(encoding="utf-8"))
    Path("docs/STEP7_NOTES.md").write_text("# Step 7 — production fusion and bounded agent\n\n" + render_part1(part1) + "\n" + render_part2(smoke) + "\n" + notes, encoding="utf-8")
    results = Path("eval/results.md")
    previous = results.read_text(encoding="utf-8").split("<!-- agent-ablation-step7 -->")[0]
    results.write_text(previous.rstrip() + "\n\n" + notes, encoding="utf-8")
    print(json.dumps({"summaries": {name: {k: row[k] for k in ("controls_passed", "mean_retries", "mean_input_tokens", "mean_output_tokens", "mean_latency_ms", "partial_signals")} for name, row in summaries.items()},
                      "new_pairs": len(missing)}, indent=2))


if __name__ == "__main__":
    main()
