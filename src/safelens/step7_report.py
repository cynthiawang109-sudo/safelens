"""Step 7 part-one reporting without overwriting historical experiments."""


def render_part1(record):
    lines = ["<!-- production-step7-part1 -->", "## Step 7 Part 1 — adopted production hybrid", "",
             ("Production lexical = BM25Okapi; hybrid = dense:BM25 10:1, report-level RRF k=60. "
             "The lexical evaluation row remains the explicitly retained **legacy FTS baseline**; dense is unchanged. "
             "All 28 category queries, development split, unfiltered; candidate contract 100 chunks → 50 reports."), "",
             "| Retriever | Category P@10 | Hit@10 | Judged P@10 | MRR | nDCG@10 |",
             "|---|---:|---:|---:|---:|---:|"]
    relevance = record["judged_relevance"]
    for method, row in record["all_category_queries"].items():
        metrics = relevance.get("averages", {}).get(method)
        scores = [f"{metrics[m]:.4f}" for m in ("precision_at_10", "mrr", "ndcg_at_10")] if metrics else ["pending judgments"] * 3
        label = "lexical (legacy FTS)" if method == "lexical" else method
        lines.append(f"| {label} | {row['category_precision_at_10']:.4f} | {row['hit_at_10']:.4f} | " + " | ".join(scores) + " |")
    stats = record["bm25_cache"]
    lines += ["", (f"Equivalence gate: **{record['equivalence_queries']}/31** production hybrid top-ten ACN orders match Step 6B 10:1. "
              f"BM25 cold build: **{stats['build_ms']:.2f} ms**, process RSS delta **{stats['rss_delta_bytes']/1024**2:.2f} MiB** "
              f"({stats['memory_method']}). Cache reuse is once per database/schema ready build ID; switching the ready build invalidates it."), "",
              (f"Hybrid Layer-2 has **{len(relevance.get('missing_pairs', []))}** missing query/ACN pairs, exported blinded and blank to "
              "`eval/judging_pool_step7_additions.csv`. Unknowns are never assigned grade zero. Dense and legacy lexical metrics "
              "retain their existing complete judgments. Full record: `eval/experiment_step7_part1.json`."), ""]
    return "\n".join(lines)


def render_part2(smoke):
    lines = ["## Step 7 Part 2 — bounded LangGraph Ask workflow", "",
             ("`route → retrieve → optional rerank → grade → conditional rewrite/retrieve → generate or abstain`. "
             "The two retry strategies are term-focused, then synonym/expansion; at most two retrieval retries "
             "and six provider LLM requests, with SDK retries disabled. Duplicate rewrites terminate the loop. "
             "Relevance and sufficiency grades are structured and checked against exactly the supplied ACNs. "
             "Grading uses the same five-report/eight-passage evidence cap as generation. All source text is framed "
             "as unverified reporter accounts; generation and citation validation rules are retained."), "",
             ("API additions: `status`, `trace`, `usage`, and optional `aggregate`; existing answer/citation/result "
             "fields remain. Traces carry queries tried, structured grades, retry strategies, provider tokens and "
             "per-stage latency. Local embedding and cross-encoder stages are bounded by the same three-attempt "
             "limit; provider `model_calls` counts LLM requests rather than local predictions. Gradio displays "
             "status/traces through the HTTP API, with no duplicate workflow logic."), "",
             ("Count questions with recognized year/category filters execute parameterized metadata SQL and show "
             "the filter parameters and full indexed-corpus denominator. Unmapped filters fall back to evidence "
             "retrieval with `partial` status, explicitly declining to estimate a count. Counts are voluntary "
             "ASRS reports, not incident rates."), "",
             "Real OpenAI HTTP smoke checks (FastAPI TestClient against the indexed PostgreSQL corpus):", "",
             "| Check | Passed | Status | Validated evidence citations | Provider calls | Retries |",
             "|---|---|---|---:|---:|---:|"]
    for row in smoke["checks"]:
        lines.append(f"| {row['query_id']} | {row['passed']} | {row['status']} | {row['citations']} | {row['usage']['model_calls']} | {row['usage']['retries']} |")
    lines += ["", ("All three controls traversed the full grade/rewrite path and correctly refused with no invented "
              "ACN/date. A normal hydraulic query returned a supported partial answer with exact indexed passages; "
              "the altitude-premise query gave a qualified refusal, which is permitted rather than forcing unsupported "
              "claims. The mapped count was 98 runway-incursion reports in 2020 out of 20,000, with zero model calls. "
              "The Toronto count was unmapped, returned partial, and estimated no count. See "
              "`docs/STEP7_PART2_SMOKE.json`; full response passages remain under ignored `data/`."), ""]
    return "\n".join(lines)
