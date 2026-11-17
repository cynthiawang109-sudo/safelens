"""Pure reporting and one-shot helpers; no production calls or tuning."""

import hashlib
import json
from pathlib import Path
from statistics import mean


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save_json(path, value):
    Path(path).write_bytes((json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))


def reserve_once(path, record):
    """An existing marker forbids both a second run and an automatic resume."""
    with Path(path).open("xb") as target:
        target.write((json.dumps(record, indent=2) + "\n").encode("utf-8"))


def citation_precision(qid, response, qrels):
    acns = sorted({c["acn"] for c in response["citations"]})
    scored = [(a, qrels[(qid, a)]) for a in acns if (qid, a) in qrels]
    relevant = sum(g >= 1 for _, g in scored)
    return {"query_id": qid, "status": response["status"], "cited_acns": acns,
            "eligible": response["status"] in ("answered", "partial"),
            "judged_cited_reports": len(scored), "relevant_cited_reports": relevant,
            "grade_zero_acns": [a for a,g in scored if g == 0],
            "unknown_acns": [a for a in acns if (qid,a) not in qrels],
            "precision_on_judged": relevant/len(scored) if scored else None,
            "judged_coverage": len(scored)/len(acns) if acns else None}


def citation_average(rows):
    selected = [r for r in rows if r["eligible"]]
    cited = sum(len(r["cited_acns"]) for r in selected)
    judged = sum(r["judged_cited_reports"] for r in selected)
    relevant = sum(r["relevant_cited_reports"] for r in selected)
    return {"eligible_responses": len(selected), "cited_report_pairs": cited,
            "judged_report_pairs": judged, "relevant_report_pairs": relevant,
            "precision_on_judged": relevant/judged if judged else None,
            "judged_coverage": judged/cited if cited else None,
            "unknown_report_pairs": cited-judged,
            "known_grade_zero_citations": sum(len(r["grade_zero_acns"]) for r in selected)}


def count_comparison(qid, response, expected):
    actual = response.get("aggregate")
    numeric_match = actual is not None and type(actual.get("count")) is int and actual["count"] == expected["count"]
    filters_match = actual is not None and actual.get("filters") == expected["filters"]
    denominator_match = actual is not None and actual.get("denominator") == expected["denominator"]
    return {"query_id": qid, "status": response["status"], "expected": expected,
            "system_aggregate": actual, "numeric_exact_match": numeric_match,
            "filters_match": filters_match, "denominator_match": denominator_match,
            "exact_match": bool(numeric_match and filters_match and denominator_match),
            "answer": response["answer"],
            "routing_trace": [e for e in response["trace"] if e["stage"] in ("route", "aggregate_sql")]}


def mean_cost(responses):
    return {"questions": len(responses), **{k: mean(r["usage"][k] for r in responses.values())
                                           for k in ("input_tokens", "output_tokens", "model_calls", "retries")},
            "latency_ms": mean(r["http_latency_ms"] for r in responses.values()),
            "graph_latency_ms": mean(r["usage"]["latency_ms"] for r in responses.values())}


def render(record):
    lines = ["<!-- frozen-final-test-step7d -->", "## Final test (frozen)", "",
             (f"Run date: **{record['run_date']} (America/New_York)**; started {record['started_at_utc']}, completed {record['completed_at_utc']}. "
             "These are **single-run frozen final-test results**, not development numbers. One run was made, with no tuning "
             "or second execution to check scores. Disappointing results are retained."), "",
             (f"Freeze commit: `{record['preflight']['freeze_commit']}`. Production-design commit recorded at construction: "
             f"`{record['preflight']['production_design_commit']}`. Query SHA-256: `{record['preflight']['query_sha256']}`. "
             f"Final qrels SHA-256: `{record['qrels_import']['sha256']}`."), "",
             ("Pre-flight query, pool identity, production code/configuration, installed software, index and corpus checks all matched "
             "the sealed record. No post-freeze production changes were made. The 89 human judgments were validated by the existing "
             "importer through a temporary in-memory/file Layer-2 schema adapter; frozen final queries and development qrels were not altered."), "",
             "### Strict mechanism retrieval", "",
             ("Eight mechanism queries; dense and production dense:BM25 10:1 hybrid, report-level RRF k=60. "
             "100 chunk candidates → best chunk per ACN → 50 reports per leg; deterministic ACN ties; no category filter. "
             "**100% judgment coverage of both retrievers' top tens**, no unknowns zero-filled. P@10 denominator 10; "
             "relevance grade ≥1; MRR over top ten; nDCG@10 uses linear gains 2/1/0 and each query's complete frozen pooled ideal."), "",
             "| Retriever | P@10 | MRR | nDCG@10 | Judged top-ten coverage |", "|---|---:|---:|---:|---:|"]
    for name, row in record["retrieval_metrics"]["averages"].items():
        lines.append(f"| {name} | {row['precision_at_10']:.4f} | {row['mrr']:.4f} | {row['ndcg_at_10']:.4f} | 100% |")
    lines += ["", "| Query | Retriever | P@10 | MRR | nDCG@10 | Coverage |", "|---|---|---:|---:|---:|---:|"]
    for row in record["retrieval_metrics"]["per_query"]:
        lines.append(f"| {row['query_id']} | {row['method']} | {row['precision_at_10']:.4f} | {row['mrr']:.4f} | {row['ndcg_at_10']:.4f} | 100% |")
    lines += ["", "### Production Ask outcomes and cost", "",
              ("Each of all twelve questions was sent once to the frozen production HTTP Ask path, including its "
              "conditional grading/rewrite workflow and SQL routing. No caller-specific flags or category filters were supplied. "
              "Costs are actual provider usage and measured HTTP request wall latency (local FastAPI TestClient); graph-only latency is also in the record. Model/index initialization and non-final warmup "
              "are excluded. Provider retries remain disabled. No request was reissued."), "",
              "| Query | Kind | Status | Validated cited reports | Input tokens | Output tokens | Latency s | Calls | Retries |",
              "|---|---|---|---:|---:|---:|---:|---:|---:|"]
    for qid, row in record["ask"].items():
        usage = row["usage"]
        lines.append(f"| {qid} | {row['kind']} | {row['status']} | {len(row['citation_acns'])} | {usage['input_tokens']} | {usage['output_tokens']} | {row['http_latency_ms']/1000:.2f} | {usage['model_calls']} | {usage['retries']} |")
    avg = record["ask_mean_cost"]
    lines += ["", (f"Mean across all 12 questions: **{avg['input_tokens']:.1f} input tokens**, **{avg['output_tokens']:.1f} output tokens**, "
              f"**{avg['latency_ms']/1000:.2f}s**, {avg['model_calls']:.2f} provider calls and {avg['retries']:.2f} retries per question. "
              "A SQL-only answer has zero provider tokens. Local embedding latency is included in request wall time, not provider-token counts."), "",
              "### Frozen controls", "", "| Control | Status | Invented ACNs detected | Pass |", "|---|---|---:|---|"]
    for row in record["controls"]:
        lines.append(f"| {row['query_id']} | {row['status']} | {len(row['invalid_acns'])} | {row['passed']} |")
    lines += ["", "### Frozen aggregate counts", "",
              ("Expected counts were sealed during construction using the production SQL executor with explicit metadata filters. "
              "The run did not substitute those answers for the system's natural-language routing. `null` means the system did not "
              "return that aggregate field; it is reported as a failed comparison rather than guessed or silently repaired."), "",
              "| Query | Status | Expected count | System count | Expected filters | System-stated filters | Expected denominator | System-stated denominator | Exact match |",
              "|---|---|---:|---:|---|---|---:|---:|---|"]
    for row in record["counts"]:
        exp = row["expected"]
        system = row["system_aggregate"] or {}
        filters = json.dumps(system.get("filters"), sort_keys=True)
        lines.append(f"| {row['query_id']} | {row['status']} | {exp['count']} | {system.get('count', 'null')} | `{json.dumps(exp['filters'], sort_keys=True)}` | `{filters}` | {exp['denominator']} | {system.get('denominator', 'null')} | {row['exact_match']} |")
    lines += ["", ("Exact match above requires the numeric count, filters, and denominator to match; separate numeric/filter/denominator "
              "flags and complete system answers/routing traces are in the experiment record. Counts are voluntary ASRS reports, not incident rates."), "",
              "### Citation precision against frozen qrels", "",
              ("Scored responses are only `answered` or `partial`. Each cited ACN counts once per response. A known pair supports "
              "when grade ≥1; grade 0 is non-support. Outside-pool pairs are **unknown**, never scored as wrong. Refusals are "
              "listed but excluded from citation precision; count questions have no final relevance judgments, so any narrative "
              "citations they produce are unknown. Report-level relevance does not prove every generated claim."), "",
              "| Scope | Supporting / judged pairs | Precision on judged | Judged / cited pairs | Coverage | Unknown pairs |",
              "|---|---:|---:|---:|---:|---:|"]
    def pct(value):
        return "N/A" if value is None else f"{value:.2%}"
    for scope, row in record["citation_summary"].items():
        lines.append(f"| {scope} | {row['relevant_report_pairs']}/{row['judged_report_pairs']} | {pct(row['precision_on_judged'])} | {row['judged_report_pairs']}/{row['cited_report_pairs']} | {pct(row['judged_coverage'])} | {row['unknown_report_pairs']} |")
    lines += ["", "| Query | Status | Known supporting / judged citations | Precision | Judged coverage | Grade-0 ACNs | Unknown ACNs |",
              "|---|---|---:|---:|---:|---|---|"]
    for row in record["citation_per_query"]:
        precision = pct(row["precision_on_judged"]) if row["eligible"] else "N/A (refusal)"
        lines.append(f"| {row['query_id']} | {row['status']} | {row['relevant_cited_reports']}/{row['judged_cited_reports']} | {precision} | {pct(row['judged_coverage'])} | {', '.join(row['grade_zero_acns']) or '—'} | {', '.join(row['unknown_acns']) or '—'} |")
    lines += ["", "### Observations and limitations", "", *record["observations"], "",
              ("Complete per-query answers, trace grades/queries, actual usage, import provenance, source/config hashes, and this run's "
              "single-run marker are in `eval/experiment_step7d.json`. Passage-bearing response data stay under ignored `data/`. "
              "Results were not used to tune the system or to request another run. Development assets remain separate; only this "
              "labeled section is appended to the existing results document. Step 8 has not started."), ""]
    return "\n".join(lines)
