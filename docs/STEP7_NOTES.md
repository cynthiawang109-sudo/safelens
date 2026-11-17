# Step 7 — production fusion and bounded agent

<!-- production-step7-part1 -->
## Step 7 Part 1 — adopted production hybrid

Production lexical = BM25Okapi; hybrid = dense:BM25 10:1, report-level RRF k=60. The lexical evaluation row remains the explicitly retained **legacy FTS baseline**; dense is unchanged. All 28 category queries, development split, unfiltered; candidate contract 100 chunks → 50 reports.

| Retriever | Category P@10 | Hit@10 | Judged P@10 | MRR | nDCG@10 |
|---|---:|---:|---:|---:|---:|
| lexical (legacy FTS) | 0.0893 | 0.2500 | 0.0500 | 0.0312 | 0.0250 |
| dense | 0.6286 | 0.9643 | 0.9500 | 1.0000 | 0.8457 |
| hybrid | 0.6429 | 1.0000 | pending judgments | pending judgments | pending judgments |

Equivalence gate: **31/31** production hybrid top-ten ACN orders match Step 6B 10:1. BM25 cold build: **8033.10 ms**, process RSS delta **380.99 MiB** (process RSS after minus before loading chunk texts and building BM25; allocator-dependent). Cache reuse is once per database/schema ready build ID; switching the ready build invalidates it.

Hybrid Layer-2 has **5** missing query/ACN pairs, exported blinded and blank to `eval/judging_pool_step7_additions.csv`. Unknowns are never assigned grade zero. Dense and legacy lexical metrics retain their existing complete judgments. Full record: `eval/experiment_step7_part1.json`.

## Step 7 Part 2 — bounded LangGraph Ask workflow

`route → retrieve → optional rerank → grade → conditional rewrite/retrieve → generate or abstain`. The two retry strategies are term-focused, then synonym/expansion; at most two retrieval retries and six provider LLM requests, with SDK retries disabled. Duplicate rewrites terminate the loop. Relevance and sufficiency grades are structured and checked against exactly the supplied ACNs. Grading uses the same five-report/eight-passage evidence cap as generation. All source text is framed as unverified reporter accounts; generation and citation validation rules are retained.

API additions: `status`, `trace`, `usage`, and optional `aggregate`; existing answer/citation/result fields remain. Traces carry queries tried, structured grades, retry strategies, provider tokens and per-stage latency. Local embedding and cross-encoder stages are bounded by the same three-attempt limit; provider `model_calls` counts LLM requests rather than local predictions. Gradio displays status/traces through the HTTP API, with no duplicate workflow logic.

Count questions with recognized year/category filters execute parameterized metadata SQL and show the filter parameters and full indexed-corpus denominator. Unmapped filters fall back to evidence retrieval with `partial` status, explicitly declining to estimate a count. Counts are voluntary ASRS reports, not incident rates.

Real OpenAI HTTP smoke checks (FastAPI TestClient against the indexed PostgreSQL corpus):

| Check | Passed | Status | Validated evidence citations | Provider calls | Retries |
|---|---|---|---:|---:|---:|
| control-domain | True | insufficient_evidence | 0 | 5 | 2 |
| control-time | True | insufficient_evidence | 0 | 5 | 2 |
| control-acn | True | insufficient_evidence | 0 | 5 | 2 |
| alt-l2-1 | True | insufficient_evidence | 1 | 6 | 2 |
| equip-l2-1 | True | partial | 2 | 6 | 2 |
| count-mapped | True | answered | 0 | 0 | 0 |
| count-unmapped | True | partial | 2 | 6 | 2 |

All three controls traversed the full grade/rewrite path and correctly refused with no invented ACN/date. A normal hydraulic query returned a supported partial answer with exact indexed passages; the altitude-premise query gave a qualified refusal, which is permitted rather than forcing unsupported claims. The mapped count was 98 runway-incursion reports in 2020 out of 20,000, with zero model calls. The Toronto count was unmapped, returned partial, and estimated no count. See `docs/STEP7_PART2_SMOKE.json`; full response passages remain under ignored `data/`.

<!-- agent-ablation-step7 -->
## Step 7 Part 3 — development ablation

Eight existing judged questions plus the three existing controls; real OpenAI generation in every configuration, same reporter-account prompt and citation validation, no category filter. Results name the runtime qrels hash `51b93d1b97c873dbf6b6489a436bcde3cd0724b7e30f4acafc0bff0f78029465`. No final-test questions were created.

### Judged retrieval (complete-query subsets only)

Metrics use final-attempt top-ten unique reports before generation filtering. A query contributes strict P@10/MRR/nDCG only when every returned top-ten pair has a human judgment; fixed P@10 denominator 10, linear nDCG gains. Different complete-query subsets are not fair head-to-head scores. Percentages are overall top-ten coverage across all eight queries; contributing strict-score subsets themselves are fully judged. Full eight-query rows remain pending where any pair is unjudged.

| Configuration | Complete queries / 8 | Strict P@10 (coverage) | MRR (coverage) | nDCG@10 (coverage) | Full eight-query status |
|---|---:|---:|---:|---:|---|
| Dense-only | 8 | 0.9500 (100.0%) | 1.0000 (100.0%) | 0.8457 (100.0%) | ready |
| Hybrid-10:1 | 4 | 0.9500 (93.8%) | 1.0000 (93.8%) | 0.8284 (93.8%) | pending judgments |
| Hybrid + Rerank | 0 | N/A (48.8%) | N/A (48.8%) | N/A (48.8%) | pending judgments |
| Hybrid + Rewrite | 0 | N/A (68.8%) | N/A (68.8%) | N/A (68.8%) | pending judgments |
| Full Agentic | 0 | N/A (45.0%) | N/A (45.0%) | N/A (45.0%) | pending judgments |

### Partial-coverage development signals

These are **partial-coverage development signals**, not full judged scores or grounds for choosing a default. Same Step 6 protocol: remove unknown top-ten pairs, precision=relevant/judged, condensed-rank MRR/DCG, known-qrels ideal at the same judged depth; undefined when no judged hits, excluded from means. Coverage is judged/10 including underfill. Never zero-fill unknown pairs. Original pooling and condensation bias comparisons.

| Configuration | Precision proxy (coverage) | MRR (coverage) | nDCG proxy (coverage) | Defined queries / 8 |
|---|---:|---:|---:|---:|
| Dense-only | 0.9500 (100.0%) | 1.0000 (100.0%) | 0.8457 (100.0%) | 8 |
| Hybrid-10:1 | 0.9594 (93.8%) | 1.0000 (93.8%) | 0.8491 (93.8%) | 8 |
| Hybrid + Rerank | 0.9750 (48.8%) | 1.0000 (48.8%) | 0.7731 (48.8%) | 8 |
| Hybrid + Rewrite | 0.9844 (68.8%) | 1.0000 (68.8%) | 0.8421 (68.8%) | 8 |
| Full Agentic | 1.0000 (45.0%) | 1.0000 (45.0%) | 0.7813 (45.0%) | 8 |

### Abstention and per-question cost

Means cover all eleven requests. Actual provider input/output tokens and total wall latency are reported; no dollar estimate is inferred. Initialization and warmup excluded. Model calls are capped at six, rewrites at two. Grading/rewrite and generation tokens are counted separately in each trace. Rerank is local CPU over at most 50 fused reports, one representative chunk each, pair truncation at 512 tokens. Cold model/index warmup measurements are in the record.

| Configuration | Controls correct / 3 | Mean retries | Mean calls | Mean input tokens | Mean output tokens | Mean latency s |
|---|---:|---:|---:|---:|---:|---:|
| Dense-only | 3 | 0.00 | 1.00 | 2551.5 | 99.8 | 2.40 |
| Hybrid-10:1 | 3 | 0.00 | 1.00 | 2618.3 | 98.4 | 2.43 |
| Hybrid + Rerank | 3 | 0.00 | 1.00 | 2801.5 | 104.1 | 7.84 |
| Hybrid + Rewrite | 3 | 1.55 | 4.82 | 7993.5 | 604.8 | 12.05 |
| Full Agentic | 3 | 1.64 | 4.82 | 8084.8 | 623.6 | 25.55 |

### Normal-query answer statuses (eight queries)

These are observed statuses, not human answerability or faithfulness judgments. Frequent refusals can be over-abstention; passing three controls does not establish useful answers on normal questions.

| Configuration | Answered | Partial | Insufficient evidence |
|---|---:|---:|---:|
| Dense-only | 0 | 0 | 8 |
| Hybrid-10:1 | 0 | 0 | 8 |
| Hybrid + Rerank | 0 | 0 | 8 |
| Hybrid + Rewrite | 0 | 1 | 7 |
| Full Agentic | 0 | 0 | 8 |

### Per-stage mean cost per question

| Configuration | Stage | Latency ms | Input tokens | Output tokens | Model calls |
|---|---|---:|---:|---:|---:|
| Dense-only | route | 0.04 | 0.0 | 0.0 | 0.00 |
| Dense-only | retrieve | 185.72 | 0.0 | 0.0 | 0.00 |
| Dense-only | generate | 2212.46 | 2551.5 | 99.8 | 1.00 |
| Dense-only | finalize | 0.01 | 0.0 | 0.0 | 0.00 |
| Hybrid-10:1 | route | 0.02 | 0.0 | 0.0 | 0.00 |
| Hybrid-10:1 | retrieve | 329.37 | 0.0 | 0.0 | 0.00 |
| Hybrid-10:1 | generate | 2097.25 | 2618.3 | 98.4 | 1.00 |
| Hybrid-10:1 | finalize | 0.01 | 0.0 | 0.0 | 0.00 |
| Hybrid + Rerank | route | 0.02 | 0.0 | 0.0 | 0.00 |
| Hybrid + Rerank | retrieve | 342.06 | 0.0 | 0.0 | 0.00 |
| Hybrid + Rerank | rerank | 5035.53 | 0.0 | 0.0 | 0.00 |
| Hybrid + Rerank | generate | 2455.26 | 2801.5 | 104.1 | 1.00 |
| Hybrid + Rerank | finalize | 0.01 | 0.0 | 0.0 | 0.00 |
| Hybrid + Rewrite | route | 0.02 | 0.0 | 0.0 | 0.00 |
| Hybrid + Rewrite | retrieve | 916.41 | 0.0 | 0.0 | 0.00 |
| Hybrid + Rewrite | grade | 8214.54 | 6362.7 | 493.9 | 2.55 |
| Hybrid + Rewrite | rewrite | 1378.83 | 313.7 | 30.5 | 1.55 |
| Hybrid + Rewrite | generate | 1527.14 | 1317.0 | 80.4 | 0.73 |
| Hybrid + Rewrite | finalize | 0.01 | 0.0 | 0.0 | 0.00 |
| Full Agentic | route | 0.02 | 0.0 | 0.0 | 0.00 |
| Full Agentic | retrieve | 931.29 | 0.0 | 0.0 | 0.00 |
| Full Agentic | rerank | 12594.36 | 0.0 | 0.0 | 0.00 |
| Full Agentic | grade | 9328.22 | 6760.5 | 526.3 | 2.64 |
| Full Agentic | rewrite | 1480.50 | 336.5 | 33.4 | 1.64 |
| Full Agentic | generate | 1197.39 | 987.8 | 64.0 | 0.55 |
| Full Agentic | finalize | 0.01 | 0.0 | 0.0 | 0.00 |

### What the stages buy and cost

- BM25 fusion: controls 3/3 → 3/3; mean latency delta +0.03s, input-token delta +66.8, output-token delta -1.5. Judged coverage 100.0% → 93.8%; missing judgments prevent a fair full eight-query relevance win claim.
- Local reranking: controls 3/3 → 3/3; mean latency delta +5.41s, input-token delta +183.3, output-token delta +5.7. Judged coverage 93.8% → 48.8%; missing judgments prevent a fair full eight-query relevance win claim.
- Conditional grading and rewrite: controls 3/3 → 3/3; mean latency delta +9.62s, input-token delta +5375.2, output-token delta +506.5. Judged coverage 93.8% → 68.8%; missing judgments prevent a fair full eight-query relevance win claim.
- Reranking on top of grading/rewrite: controls 3/3 → 3/3; mean latency delta +13.50s, input-token delta +91.4, output-token delta +18.8. Judged coverage 68.8% → 45.0%; missing judgments prevent a fair full eight-query relevance win claim.
- Keep the adopted 10:1 retrieval settings. Reranking remains disabled by default; its added latency is not earned by complete human-judged evidence here. The bounded grading/rewrite path is available for Ask evidence sufficiency, with its measured cost visible; no additional rewrite or rerank tuning was performed.
- Conditional grading/rewrite produced one partial normal-query response versus eight refusals for Hybrid-10:1; Full Agentic refused all eight. These are observed statuses, not independently judged answer correctness. Keep the requested bounded Ask workflow available, expose its cost, and do not enable reranking by default on this evidence.

All **82** new final top-ten query/ACN pairs are exported as `eval/judging_pool_step7_ablation_additions.csv`, blinded, shuffled, with blank grades/notes. They are not automatic judgments and do not alter qrels. Full response passages remain in ignored data; per-question outcomes, grades, trace costs, configuration and source hashes are in `eval/experiment_step7_ablation.json`.

Reproduce: `uv run python eval/run_agent_ablation.py` with UTF-8 variables set. Matching-source checkpoints reuse the original real-provider responses; changed code/configuration gets a separate cache fingerprint. This ablation cannot establish general superiority on eight repeatedly inspected development queries. Step 8 has not started.

## Step 7 acceptance

53 tests passed, including all prior tests and production weighting, BM25 build-ID invalidation, rewrite/call caps, and aggregate SQL tests. Ruff and `git diff --check` pass. All 55 ablation responses obey their budgets; every returned citation passage was independently matched to its DB chunk. The corpus, queries, qrels, manifests, generation prompt, citation validator, and historical result sections are unchanged. See `docs/STEP7_VALIDATION.json`.

The 82-pair ablation sheet includes 5 pairs also present in the five-pair Part 1 sheet; each query/ACN pair only needs one human grade. No grades were invented. Step 8 was not started.
