# Mini Layer-1 evaluation and judging pool

Benchmark retrieval is **unfiltered**. Category labels measure coarse topical agreement, not query-level relevance.
Missing ranks in an underfilled top ten count as misses (fixed denominator 10). Hit@10 means at least one matching report.

Corpus: **5000 reports**, **6998 chunks**; ready build **3**.
Selection seed: **20261115**. Candidate chunks/reports: **100/50**; report-level max chunk score before RRF, **k=60**; ties by ACN.

## 20 dedicated Layer-1 queries (five per category)

| Retriever | Category Precision@10 | Hit@10 |
|---|---:|---:|
| lexical | 0.090 | 0.300 |
| dense | 0.895 | 1.000 |
| hybrid | 0.885 | 1.000 |

## All 28 category queries (including eight future judged queries)

| Retriever | Category Precision@10 | Hit@10 |
|---|---:|---:|
| lexical | 0.089 | 0.250 |
| dense | 0.904 | 1.000 |
| hybrid | 0.896 | 1.000 |

## Findings

On the 20 primary queries, hybrid Category Precision@10 is 0.885, compared with dense 0.895 and lexical 0.090.
PostgreSQL FTS underfilled the top ten on 19/20 primary queries, including 13 with zero matches under its conjunctive websearch/simple semantics. Queries and defaults were not tuned after seeing results.
These findings describe category agreement only; human relevance judging is still pending.

## Per-query category agreement

Layer 2 rows below are category agreement only; no human relevance scores have been assigned.

| Query | Layer | Retriever | Retrieved | Category Precision@10 | Hit@10 |
|---|---:|---|---:|---:|---:|
| ri-l1-1 | 1 | lexical | 10 | 1.000 | 1 |
| ri-l1-1 | 1 | dense | 10 | 1.000 | 1 |
| ri-l1-1 | 1 | hybrid | 10 | 1.000 | 1 |
| ri-l1-2 | 1 | lexical | 1 | 0.100 | 1 |
| ri-l1-2 | 1 | dense | 10 | 1.000 | 1 |
| ri-l1-2 | 1 | hybrid | 10 | 1.000 | 1 |
| ri-l1-3 | 1 | lexical | 0 | 0.000 | 0 |
| ri-l1-3 | 1 | dense | 10 | 0.500 | 1 |
| ri-l1-3 | 1 | hybrid | 10 | 0.500 | 1 |
| ri-l1-4 | 1 | lexical | 0 | 0.000 | 0 |
| ri-l1-4 | 1 | dense | 10 | 0.900 | 1 |
| ri-l1-4 | 1 | hybrid | 10 | 0.900 | 1 |
| ri-l1-5 | 1 | lexical | 1 | 0.100 | 1 |
| ri-l1-5 | 1 | dense | 10 | 1.000 | 1 |
| ri-l1-5 | 1 | hybrid | 10 | 1.000 | 1 |
| alt-l1-1 | 1 | lexical | 2 | 0.100 | 1 |
| alt-l1-1 | 1 | dense | 10 | 1.000 | 1 |
| alt-l1-1 | 1 | hybrid | 10 | 0.900 | 1 |
| alt-l1-2 | 1 | lexical | 1 | 0.000 | 0 |
| alt-l1-2 | 1 | dense | 10 | 1.000 | 1 |
| alt-l1-2 | 1 | hybrid | 10 | 0.900 | 1 |
| alt-l1-3 | 1 | lexical | 0 | 0.000 | 0 |
| alt-l1-3 | 1 | dense | 10 | 0.700 | 1 |
| alt-l1-3 | 1 | hybrid | 10 | 0.700 | 1 |
| alt-l1-4 | 1 | lexical | 0 | 0.000 | 0 |
| alt-l1-4 | 1 | dense | 10 | 0.800 | 1 |
| alt-l1-4 | 1 | hybrid | 10 | 0.800 | 1 |
| alt-l1-5 | 1 | lexical | 0 | 0.000 | 0 |
| alt-l1-5 | 1 | dense | 10 | 1.000 | 1 |
| alt-l1-5 | 1 | hybrid | 10 | 1.000 | 1 |
| nmac-l1-1 | 1 | lexical | 1 | 0.100 | 1 |
| nmac-l1-1 | 1 | dense | 10 | 0.900 | 1 |
| nmac-l1-1 | 1 | hybrid | 10 | 0.900 | 1 |
| nmac-l1-2 | 1 | lexical | 0 | 0.000 | 0 |
| nmac-l1-2 | 1 | dense | 10 | 1.000 | 1 |
| nmac-l1-2 | 1 | hybrid | 10 | 1.000 | 1 |
| nmac-l1-3 | 1 | lexical | 0 | 0.000 | 0 |
| nmac-l1-3 | 1 | dense | 10 | 0.800 | 1 |
| nmac-l1-3 | 1 | hybrid | 10 | 0.800 | 1 |
| nmac-l1-4 | 1 | lexical | 0 | 0.000 | 0 |
| nmac-l1-4 | 1 | dense | 10 | 0.500 | 1 |
| nmac-l1-4 | 1 | hybrid | 10 | 0.500 | 1 |
| nmac-l1-5 | 1 | lexical | 0 | 0.000 | 0 |
| nmac-l1-5 | 1 | dense | 10 | 0.900 | 1 |
| nmac-l1-5 | 1 | hybrid | 10 | 0.900 | 1 |
| equip-l1-1 | 1 | lexical | 4 | 0.400 | 1 |
| equip-l1-1 | 1 | dense | 10 | 0.900 | 1 |
| equip-l1-1 | 1 | hybrid | 10 | 0.900 | 1 |
| equip-l1-2 | 1 | lexical | 0 | 0.000 | 0 |
| equip-l1-2 | 1 | dense | 10 | 1.000 | 1 |
| equip-l1-2 | 1 | hybrid | 10 | 1.000 | 1 |
| equip-l1-3 | 1 | lexical | 0 | 0.000 | 0 |
| equip-l1-3 | 1 | dense | 10 | 1.000 | 1 |
| equip-l1-3 | 1 | hybrid | 10 | 1.000 | 1 |
| equip-l1-4 | 1 | lexical | 0 | 0.000 | 0 |
| equip-l1-4 | 1 | dense | 10 | 1.000 | 1 |
| equip-l1-4 | 1 | hybrid | 10 | 1.000 | 1 |
| equip-l1-5 | 1 | lexical | 0 | 0.000 | 0 |
| equip-l1-5 | 1 | dense | 10 | 1.000 | 1 |
| equip-l1-5 | 1 | hybrid | 10 | 1.000 | 1 |
| ri-l2-1 | 2 | lexical | 0 | 0.000 | 0 |
| ri-l2-1 | 2 | dense | 10 | 1.000 | 1 |
| ri-l2-1 | 2 | hybrid | 10 | 1.000 | 1 |
| ri-l2-2 | 2 | lexical | 10 | 0.700 | 1 |
| ri-l2-2 | 2 | dense | 10 | 0.900 | 1 |
| ri-l2-2 | 2 | hybrid | 10 | 0.900 | 1 |
| alt-l2-1 | 2 | lexical | 0 | 0.000 | 0 |
| alt-l2-1 | 2 | dense | 10 | 1.000 | 1 |
| alt-l2-1 | 2 | hybrid | 10 | 1.000 | 1 |
| alt-l2-2 | 2 | lexical | 0 | 0.000 | 0 |
| alt-l2-2 | 2 | dense | 10 | 1.000 | 1 |
| alt-l2-2 | 2 | hybrid | 10 | 1.000 | 1 |
| nmac-l2-1 | 2 | lexical | 0 | 0.000 | 0 |
| nmac-l2-1 | 2 | dense | 10 | 0.800 | 1 |
| nmac-l2-1 | 2 | hybrid | 10 | 0.800 | 1 |
| nmac-l2-2 | 2 | lexical | 0 | 0.000 | 0 |
| nmac-l2-2 | 2 | dense | 10 | 0.700 | 1 |
| nmac-l2-2 | 2 | hybrid | 10 | 0.700 | 1 |
| equip-l2-1 | 2 | lexical | 0 | 0.000 | 0 |
| equip-l2-1 | 2 | dense | 10 | 1.000 | 1 |
| equip-l2-1 | 2 | hybrid | 10 | 1.000 | 1 |
| equip-l2-2 | 2 | lexical | 0 | 0.000 | 0 |
| equip-l2-2 | 2 | dense | 10 | 1.000 | 1 |
| equip-l2-2 | 2 | hybrid | 10 | 1.000 | 1 |

## Retrieval latency

Single local run, warmed model; excludes model initialization and generation. Timed across all 31 queries. p95 is nearest-rank.

| Retriever | Mean ms | p95 ms |
|---|---:|---:|
| lexical | 7.71 | 13.44 |
| dense | 66.70 | 133.75 |
| hybrid | 61.33 | 82.09 |

## Candidate-depth check

Defaults remain 100/50. Doubling candidate chunks to 200 is a separately recorded sensitivity check over all 28 category queries.

| Retriever | Queries with changed top-10 ACN order | Change in mean Category Precision@10 |
|---|---:|---:|
| lexical | 0/28 | +0.000 |
| dense | 0/28 | +0.000 |
| hybrid | 0/28 | +0.000 |

## Layer-2 judging

`judging_pool.csv` contains **88** unique (query_id, acn) pairs for eight queries, shuffled with seed 20261116.
The sheet contains no retriever identity or ranks. Filled grades: 88; filled notes: 0. No automated judgments are assigned.
Cynthia: read synopsis first, consult the indexed full narrative if ambiguous, then use grades 2=directly relevant, 1=partially relevant, 0=irrelevant. Record notes as needed.
After human grading, run `uv run python eval/import_judgments.py`, then rerun this evaluator. Unjudged top-ten reports cause an error rather than being assumed irrelevant.

### Judged relevance (macro averages)

Precision@10 and MRR treat grade >=1 as relevant. MRR uses the retrieved top ten. nDCG@10 uses linear gains 2/1/0 and the pooled ideal ranking.
These eight queries are a development set, not an independent held-out test; pooling does not establish complete corpus relevance.

| Retriever | Precision@10 | MRR | nDCG@10 |
|---|---:|---:|---:|
| lexical | 0.050 | 0.042 | 0.037 |
| dense | 0.963 | 1.000 | 0.914 |
| hybrid | 0.938 | 1.000 | 0.889 |

### Per-query judged relevance

| Query | Retriever | Precision@10 | MRR | nDCG@10 |
|---|---|---:|---:|---:|
| ri-l2-1 | lexical | 0.000 | 0.000 | 0.000 |
| ri-l2-1 | dense | 1.000 | 1.000 | 0.859 |
| ri-l2-1 | hybrid | 1.000 | 1.000 | 0.859 |
| ri-l2-2 | lexical | 0.400 | 0.333 | 0.294 |
| ri-l2-2 | dense | 0.900 | 1.000 | 0.917 |
| ri-l2-2 | hybrid | 0.700 | 1.000 | 0.720 |
| alt-l2-1 | lexical | 0.000 | 0.000 | 0.000 |
| alt-l2-1 | dense | 1.000 | 1.000 | 1.000 |
| alt-l2-1 | hybrid | 1.000 | 1.000 | 1.000 |
| alt-l2-2 | lexical | 0.000 | 0.000 | 0.000 |
| alt-l2-2 | dense | 1.000 | 1.000 | 0.951 |
| alt-l2-2 | hybrid | 1.000 | 1.000 | 0.951 |
| nmac-l2-1 | lexical | 0.000 | 0.000 | 0.000 |
| nmac-l2-1 | dense | 1.000 | 1.000 | 0.874 |
| nmac-l2-1 | hybrid | 1.000 | 1.000 | 0.874 |
| nmac-l2-2 | lexical | 0.000 | 0.000 | 0.000 |
| nmac-l2-2 | dense | 1.000 | 1.000 | 0.846 |
| nmac-l2-2 | hybrid | 1.000 | 1.000 | 0.846 |
| equip-l2-1 | lexical | 0.000 | 0.000 | 0.000 |
| equip-l2-1 | dense | 1.000 | 1.000 | 0.910 |
| equip-l2-1 | hybrid | 1.000 | 1.000 | 0.910 |
| equip-l2-2 | lexical | 0.000 | 0.000 | 0.000 |
| equip-l2-2 | dense | 0.800 | 1.000 | 0.955 |
| equip-l2-2 | hybrid | 0.800 | 1.000 | 0.955 |

## Abstention controls

Controls are present with `expect: insufficient_evidence`. Absence was checked against this frozen subset. This retrieval evaluator does not call generation; Step 4 generation smoke outcomes are recorded separately in `docs/STEP4_NOTES.md`.

- `control-domain`: absence verified; `{"matching_report_counts": {"Pelagic Meridian": 0, "MARINE-CONTROL-20261115-X": 0, "ballast pump": 0}}`
- `control-time`: absence verified; `{"acn": "1857031", "report_month": "2021-11", "content_hash": "d37509d66f1bc4eedc11e5bb5dc3a08f006ed5c5754c7a1aa340d47c381e6295", "temporal_marker_found": false, "manual_full_text_inspection": "Entire synopsis and narrative manually inspected: neither contains an event day or clock time; structured date has month precision only. Broad source time-of-day bands cannot establish an exact timestamp."}`
- `control-acn`: absence verified; `{"acn": "999999999999999", "present": false}`

## Limitations and experiment record

Layer-1 category metrics are not judged relevance or proof that any method is better at answering questions. Judged relevance, when available above, is reported separately. Twenty-eight hand-written queries are a development set, not an independent held-out test.
The category-balanced subset includes every available runway-incursion report; category overlap and year skew are recorded in the manifest and DATA_NOTES. Synopsis text is included in indexing and may simplify retrieval.
PostgreSQL FTS uses simple configuration and websearch query semantics; long conjunctive queries may underfill the top ten. This baseline is not BM25. Exact cosine search uses no ANN index.
Candidate-depth changes above must be considered before interpreting hybrid results; the default was not silently tuned.
The complete experiment configuration, corpus/content hashes, query/qrels hashes, per-query metrics and latency samples, software/hardware notes, and timestamp are in `experiment.json`.
No generation or human judging is performed by this evaluator.

<!-- corpus-scaleup-20000 -->
## 20,000-report corpus (development split)

Ready build **4**: **20,000 reports**, **28,306 embedded chunks**. All 5,000 Mini ACNs retained; 15,000 year-stratified additions, seed 20261120.
Only corpus size changed. Retrieval, queries, prompts, generation, chunking, model/revision, and scoring definitions are unchanged. These are development results, not a frozen final test.
The original Mini manifest, judging pool, and qrels are preserved. `current_corpus.json` designates `corpus_manifest_20k.json`; experiment.json records that switch and the archived `experiment_5k.json` baseline.

### Layer-1 category agreement — all 28 category queries

Unfiltered retrieval. Category agreement is coarse topical alignment, not judged relevance. Precision denominator is 10, including underfilled ranks.

| Retriever | Metric | 5,000 | 20,000 | Delta |
|---|---|---:|---:|---:|
| lexical | category_precision_at_10 | 0.089 | 0.089 | +0.000 |
| lexical | hit_at_10 | 0.250 | 0.250 | +0.000 |
| dense | category_precision_at_10 | 0.904 | 0.629 | -0.275 |
| dense | hit_at_10 | 1.000 | 0.964 | -0.036 |
| hybrid | category_precision_at_10 | 0.896 | 0.611 | -0.286 |
| hybrid | hit_at_10 | 1.000 | 0.964 | -0.036 |

### Layer-2 judged relevance — eight development queries

**Not yet computable:** 46 unique top-ten (query_id, ACN) pairs lack judgments. Retaining all Mini reports preserves existing labels but does not judge newly retrieved candidates.
No unjudged report is assumed irrelevant. The 20k scores and deltas remain pending; treating these rows as zero would invalidate the comparison.
`judging_pool_20k_additions.csv` is a blinded, shuffled export of only the missing pairs, with blank grades/notes. The original pool and qrels are untouched.

| Retriever | Metric | 5,000 | 20,000 | Delta |
|---|---|---:|---:|---:|
| lexical | precision_at_10 | 0.050 | pending judgments | N/A |
| lexical | mrr | 0.042 | pending judgments | N/A |
| lexical | ndcg_at_10 | 0.037 | pending judgments | N/A |
| dense | precision_at_10 | 0.963 | pending judgments | N/A |
| dense | mrr | 1.000 | pending judgments | N/A |
| dense | ndcg_at_10 | 0.914 | pending judgments | N/A |
| hybrid | precision_at_10 | 0.938 | pending judgments | N/A |
| hybrid | mrr | 1.000 | pending judgments | N/A |
| hybrid | ndcg_at_10 | 0.889 | pending judgments | N/A |

### Per-query Layer-1 metrics

| Query | Layer | Retriever | Retrieved | Category Precision@10 | Hit@10 |
|---|---:|---|---:|---:|---:|
| ri-l1-1 | 1 | lexical | 10 | 0.800 | 1 |
| ri-l1-1 | 1 | dense | 10 | 0.900 | 1 |
| ri-l1-1 | 1 | hybrid | 10 | 1.000 | 1 |
| ri-l1-2 | 1 | lexical | 3 | 0.100 | 1 |
| ri-l1-2 | 1 | dense | 10 | 0.700 | 1 |
| ri-l1-2 | 1 | hybrid | 10 | 0.700 | 1 |
| ri-l1-3 | 1 | lexical | 0 | 0.000 | 0 |
| ri-l1-3 | 1 | dense | 10 | 0.000 | 0 |
| ri-l1-3 | 1 | hybrid | 10 | 0.000 | 0 |
| ri-l1-4 | 1 | lexical | 0 | 0.000 | 0 |
| ri-l1-4 | 1 | dense | 10 | 0.200 | 1 |
| ri-l1-4 | 1 | hybrid | 10 | 0.200 | 1 |
| ri-l1-5 | 1 | lexical | 1 | 0.100 | 1 |
| ri-l1-5 | 1 | dense | 10 | 1.000 | 1 |
| ri-l1-5 | 1 | hybrid | 10 | 1.000 | 1 |
| alt-l1-1 | 1 | lexical | 5 | 0.100 | 1 |
| alt-l1-1 | 1 | dense | 10 | 0.900 | 1 |
| alt-l1-1 | 1 | hybrid | 10 | 0.600 | 1 |
| alt-l1-2 | 1 | lexical | 1 | 0.000 | 0 |
| alt-l1-2 | 1 | dense | 10 | 0.200 | 1 |
| alt-l1-2 | 1 | hybrid | 10 | 0.200 | 1 |
| alt-l1-3 | 1 | lexical | 0 | 0.000 | 0 |
| alt-l1-3 | 1 | dense | 10 | 0.600 | 1 |
| alt-l1-3 | 1 | hybrid | 10 | 0.600 | 1 |
| alt-l1-4 | 1 | lexical | 0 | 0.000 | 0 |
| alt-l1-4 | 1 | dense | 10 | 0.400 | 1 |
| alt-l1-4 | 1 | hybrid | 10 | 0.400 | 1 |
| alt-l1-5 | 1 | lexical | 0 | 0.000 | 0 |
| alt-l1-5 | 1 | dense | 10 | 0.200 | 1 |
| alt-l1-5 | 1 | hybrid | 10 | 0.200 | 1 |
| nmac-l1-1 | 1 | lexical | 2 | 0.200 | 1 |
| nmac-l1-1 | 1 | dense | 10 | 1.000 | 1 |
| nmac-l1-1 | 1 | hybrid | 10 | 1.000 | 1 |
| nmac-l1-2 | 1 | lexical | 0 | 0.000 | 0 |
| nmac-l1-2 | 1 | dense | 10 | 1.000 | 1 |
| nmac-l1-2 | 1 | hybrid | 10 | 1.000 | 1 |
| nmac-l1-3 | 1 | lexical | 0 | 0.000 | 0 |
| nmac-l1-3 | 1 | dense | 10 | 0.700 | 1 |
| nmac-l1-3 | 1 | hybrid | 10 | 0.700 | 1 |
| nmac-l1-4 | 1 | lexical | 0 | 0.000 | 0 |
| nmac-l1-4 | 1 | dense | 10 | 0.400 | 1 |
| nmac-l1-4 | 1 | hybrid | 10 | 0.400 | 1 |
| nmac-l1-5 | 1 | lexical | 0 | 0.000 | 0 |
| nmac-l1-5 | 1 | dense | 10 | 0.800 | 1 |
| nmac-l1-5 | 1 | hybrid | 10 | 0.800 | 1 |
| equip-l1-1 | 1 | lexical | 10 | 0.900 | 1 |
| equip-l1-1 | 1 | dense | 10 | 0.900 | 1 |
| equip-l1-1 | 1 | hybrid | 10 | 0.800 | 1 |
| equip-l1-2 | 1 | lexical | 0 | 0.000 | 0 |
| equip-l1-2 | 1 | dense | 10 | 0.500 | 1 |
| equip-l1-2 | 1 | hybrid | 10 | 0.500 | 1 |
| equip-l1-3 | 1 | lexical | 0 | 0.000 | 0 |
| equip-l1-3 | 1 | dense | 10 | 0.700 | 1 |
| equip-l1-3 | 1 | hybrid | 10 | 0.700 | 1 |
| equip-l1-4 | 1 | lexical | 0 | 0.000 | 0 |
| equip-l1-4 | 1 | dense | 10 | 0.900 | 1 |
| equip-l1-4 | 1 | hybrid | 10 | 0.900 | 1 |
| equip-l1-5 | 1 | lexical | 0 | 0.000 | 0 |
| equip-l1-5 | 1 | dense | 10 | 0.700 | 1 |
| equip-l1-5 | 1 | hybrid | 10 | 0.700 | 1 |
| ri-l2-1 | 2 | lexical | 0 | 0.000 | 0 |
| ri-l2-1 | 2 | dense | 10 | 0.900 | 1 |
| ri-l2-1 | 2 | hybrid | 10 | 0.900 | 1 |
| ri-l2-2 | 2 | lexical | 10 | 0.300 | 1 |
| ri-l2-2 | 2 | dense | 10 | 0.600 | 1 |
| ri-l2-2 | 2 | hybrid | 10 | 0.400 | 1 |
| alt-l2-1 | 2 | lexical | 0 | 0.000 | 0 |
| alt-l2-1 | 2 | dense | 10 | 0.400 | 1 |
| alt-l2-1 | 2 | hybrid | 10 | 0.400 | 1 |
| alt-l2-2 | 2 | lexical | 0 | 0.000 | 0 |
| alt-l2-2 | 2 | dense | 10 | 0.600 | 1 |
| alt-l2-2 | 2 | hybrid | 10 | 0.600 | 1 |
| nmac-l2-1 | 2 | lexical | 0 | 0.000 | 0 |
| nmac-l2-1 | 2 | dense | 10 | 0.500 | 1 |
| nmac-l2-1 | 2 | hybrid | 10 | 0.500 | 1 |
| nmac-l2-2 | 2 | lexical | 0 | 0.000 | 0 |
| nmac-l2-2 | 2 | dense | 10 | 0.600 | 1 |
| nmac-l2-2 | 2 | hybrid | 10 | 0.600 | 1 |
| equip-l2-1 | 2 | lexical | 0 | 0.000 | 0 |
| equip-l2-1 | 2 | dense | 10 | 0.800 | 1 |
| equip-l2-1 | 2 | hybrid | 10 | 0.800 | 1 |
| equip-l2-2 | 2 | lexical | 0 | 0.000 | 0 |
| equip-l2-2 | 2 | dense | 10 | 0.500 | 1 |
| equip-l2-2 | 2 | hybrid | 10 | 0.500 | 1 |

### Latency and candidate-depth sensitivity

| Retriever | Mean ms | p95 ms | Top-ten changes at 200 candidate chunks |
|---|---:|---:|---:|
| lexical | 8.79 | 22.84 | 0/28 |
| dense | 139.29 | 170.87 | 0/28 |
| hybrid | 136.38 | 155.17 | 0/28 |

Default candidate depths remain 100 chunks / 50 reports, report-level RRF k=60, ties by ACN. All controls were reverified absent; this evaluator makes no generation calls.
Full corpus/query/qrels hashes, per-query measurements, sensitivity records, configuration, software, hardware, and timestamp are in `experiment.json`. No Step 6 retrieval variant was started.

<!-- lexical-bakeoff-step6 -->
# Step 6: lexical bake-off (development)

20,000 reports; 28,306 chunks; ready build 4. Text-only retrieval, no category filter. All 28 category queries are the primary development selection metric; no final test set was used.

All lexical and dense legs fetch at most 100 chunks, fold by ACN using maximum chunk score, then retain 50 reports. Hybrid uses report-level RRF k=60, ties by ACN. Underfills are not padded.

## Layer-1 and latency

Category agreement is a weak-label measure, not human relevance. Latency: one local run over all 31 queries in file order, warmed query model, mean and nearest-rank p95; includes query embedding and retrieval, excludes initialization, BM25 indexing, and generation. Each hybrid executes its own lexical and dense calls; no cached rankings or embeddings in timed retrieval.

| Configuration | Category P@10 | Hit@10 | Mean ms | p95 ms |
|---|---:|---:|---:|---:|
| lexical-fts-and | 0.0893 | 0.2500 | 15.80 | 33.02 |
| hybrid-fts-and | 0.6107 | 0.9643 | 214.44 | 308.97 |
| lexical-fts-or | 0.4321 | 0.9643 | 687.64 | 1577.64 |
| hybrid-fts-or | 0.5821 | 1.0000 | 816.14 | 1687.32 |
| lexical-bm25-ref | 0.5714 | 1.0000 | 146.96 | 267.53 |
| hybrid-bm25-ref | 0.5786 | 1.0000 | 318.72 | 529.90 |
| dense | 0.6286 | 0.9643 | 175.57 | 270.64 |

## Recommendation

Recommend **lexical-bm25-ref** as the lexical leg on the primary metric. Its hybrid **hybrid-bm25-ref** changes Category P@10 versus dense by **-0.0500** (does not beat dense). Adoption is a separate decision; BM25 production integration is not implemented. BM25 improves lexical Category P@10 over OR by +0.1393, but the measured fusion does not justify replacing dense alone. Defer a pg_search integration until a production lexical/fusion change is justified.

This selection uses the primary metric only, with mean latency as a prespecified tie-break. Development margins are descriptive; 28 queries do not establish general superiority. Production defaults remain unchanged pending Cynthia's decision. No pg_search integration or Step 7 work.

## Partial-coverage development signals

These are **partial-coverage development signals**, not comparable full-coverage scores. For each query, remove unjudged results from the original top ten; P@10 here means relevant/judged (a judged-only precision proxy, not conventional fixed-denominator P@10). MRR uses condensed ranks; nDCG uses linear gains and the known-qrels ideal at the same judged depth. Unknowns never get grade 0. Zero judged hits gives undefined metrics (N/A), excluded from macro averages; contributing query counts are printed. Coverage is judged/10, including underfill; returned-result coverage is also in JSON. Condensation is optimistic and the old pooled judgments favor the original methods; do not select on these numbers.

| Configuration | Judged-only P@10 (coverage) | Condensed MRR (coverage) | Condensed nDCG@10 (coverage) | Queries defined / 8 |
|---|---:|---:|---:|---:|
| lexical-fts-and | 0.5000 (5.0%) | 0.3333 (5.0%) | 0.2657 (5.0%) | 1 |
| hybrid-fts-and | 0.9750 (50.0%) | 1.0000 (50.0%) | 0.8461 (50.0%) | 8 |
| lexical-fts-or | 1.0000 (6.2%) | 1.0000 (6.2%) | 0.8333 (6.2%) | 3 |
| hybrid-fts-or | 1.0000 (23.8%) | 1.0000 (23.8%) | 0.8350 (23.8%) | 8 |
| lexical-bm25-ref | 1.0000 (6.2%) | 1.0000 (6.2%) | 0.6250 (6.2%) | 4 |
| hybrid-bm25-ref | 1.0000 (22.5%) | 1.0000 (22.5%) | 0.8435 (22.5%) | 6 |
| dense | 1.0000 (51.2%) | 1.0000 (51.2%) | 0.8710 (51.2%) | 8 |

## Per-query Layer-1

| Query | Configuration | Returned | Category P@10 | Hit@10 |
|---|---|---:|---:|---:|
| ri-l1-1 | lexical-fts-and | 10 | 0.800 | 1 |
| ri-l1-1 | hybrid-fts-and | 10 | 1.000 | 1 |
| ri-l1-1 | lexical-fts-or | 10 | 0.900 | 1 |
| ri-l1-1 | hybrid-fts-or | 10 | 1.000 | 1 |
| ri-l1-1 | lexical-bm25-ref | 10 | 0.900 | 1 |
| ri-l1-1 | hybrid-bm25-ref | 10 | 1.000 | 1 |
| ri-l1-1 | dense | 10 | 0.900 | 1 |
| ri-l1-2 | lexical-fts-and | 3 | 0.100 | 1 |
| ri-l1-2 | hybrid-fts-and | 10 | 0.700 | 1 |
| ri-l1-2 | lexical-fts-or | 10 | 0.400 | 1 |
| ri-l1-2 | hybrid-fts-or | 10 | 0.600 | 1 |
| ri-l1-2 | lexical-bm25-ref | 10 | 0.700 | 1 |
| ri-l1-2 | hybrid-bm25-ref | 10 | 0.900 | 1 |
| ri-l1-2 | dense | 10 | 0.700 | 1 |
| ri-l1-3 | lexical-fts-and | 0 | 0.000 | 0 |
| ri-l1-3 | hybrid-fts-and | 10 | 0.000 | 0 |
| ri-l1-3 | lexical-fts-or | 10 | 0.300 | 1 |
| ri-l1-3 | hybrid-fts-or | 10 | 0.300 | 1 |
| ri-l1-3 | lexical-bm25-ref | 10 | 0.300 | 1 |
| ri-l1-3 | hybrid-bm25-ref | 10 | 0.200 | 1 |
| ri-l1-3 | dense | 10 | 0.000 | 0 |
| ri-l1-4 | lexical-fts-and | 0 | 0.000 | 0 |
| ri-l1-4 | hybrid-fts-and | 10 | 0.200 | 1 |
| ri-l1-4 | lexical-fts-or | 10 | 0.500 | 1 |
| ri-l1-4 | hybrid-fts-or | 10 | 0.400 | 1 |
| ri-l1-4 | lexical-bm25-ref | 10 | 0.700 | 1 |
| ri-l1-4 | hybrid-bm25-ref | 10 | 0.400 | 1 |
| ri-l1-4 | dense | 10 | 0.200 | 1 |
| ri-l1-5 | lexical-fts-and | 1 | 0.100 | 1 |
| ri-l1-5 | hybrid-fts-and | 10 | 1.000 | 1 |
| ri-l1-5 | lexical-fts-or | 10 | 0.900 | 1 |
| ri-l1-5 | hybrid-fts-or | 10 | 1.000 | 1 |
| ri-l1-5 | lexical-bm25-ref | 10 | 0.900 | 1 |
| ri-l1-5 | hybrid-bm25-ref | 10 | 0.900 | 1 |
| ri-l1-5 | dense | 10 | 1.000 | 1 |
| alt-l1-1 | lexical-fts-and | 5 | 0.100 | 1 |
| alt-l1-1 | hybrid-fts-and | 10 | 0.600 | 1 |
| alt-l1-1 | lexical-fts-or | 10 | 0.100 | 1 |
| alt-l1-1 | hybrid-fts-or | 10 | 0.700 | 1 |
| alt-l1-1 | lexical-bm25-ref | 10 | 0.500 | 1 |
| alt-l1-1 | hybrid-bm25-ref | 10 | 0.700 | 1 |
| alt-l1-1 | dense | 10 | 0.900 | 1 |
| alt-l1-2 | lexical-fts-and | 1 | 0.000 | 0 |
| alt-l1-2 | hybrid-fts-and | 10 | 0.200 | 1 |
| alt-l1-2 | lexical-fts-or | 10 | 0.100 | 1 |
| alt-l1-2 | hybrid-fts-or | 10 | 0.300 | 1 |
| alt-l1-2 | lexical-bm25-ref | 10 | 0.300 | 1 |
| alt-l1-2 | hybrid-bm25-ref | 10 | 0.300 | 1 |
| alt-l1-2 | dense | 10 | 0.200 | 1 |
| alt-l1-3 | lexical-fts-and | 0 | 0.000 | 0 |
| alt-l1-3 | hybrid-fts-and | 10 | 0.600 | 1 |
| alt-l1-3 | lexical-fts-or | 10 | 0.100 | 1 |
| alt-l1-3 | hybrid-fts-or | 10 | 0.300 | 1 |
| alt-l1-3 | lexical-bm25-ref | 10 | 0.400 | 1 |
| alt-l1-3 | hybrid-bm25-ref | 10 | 0.400 | 1 |
| alt-l1-3 | dense | 10 | 0.600 | 1 |
| alt-l1-4 | lexical-fts-and | 0 | 0.000 | 0 |
| alt-l1-4 | hybrid-fts-and | 10 | 0.400 | 1 |
| alt-l1-4 | lexical-fts-or | 10 | 0.200 | 1 |
| alt-l1-4 | hybrid-fts-or | 10 | 0.300 | 1 |
| alt-l1-4 | lexical-bm25-ref | 10 | 0.200 | 1 |
| alt-l1-4 | hybrid-bm25-ref | 10 | 0.100 | 1 |
| alt-l1-4 | dense | 10 | 0.400 | 1 |
| alt-l1-5 | lexical-fts-and | 0 | 0.000 | 0 |
| alt-l1-5 | hybrid-fts-and | 10 | 0.200 | 1 |
| alt-l1-5 | lexical-fts-or | 10 | 0.200 | 1 |
| alt-l1-5 | hybrid-fts-or | 10 | 0.300 | 1 |
| alt-l1-5 | lexical-bm25-ref | 10 | 0.200 | 1 |
| alt-l1-5 | hybrid-bm25-ref | 10 | 0.100 | 1 |
| alt-l1-5 | dense | 10 | 0.200 | 1 |
| nmac-l1-1 | lexical-fts-and | 2 | 0.200 | 1 |
| nmac-l1-1 | hybrid-fts-and | 10 | 1.000 | 1 |
| nmac-l1-1 | lexical-fts-or | 10 | 0.300 | 1 |
| nmac-l1-1 | hybrid-fts-or | 10 | 0.700 | 1 |
| nmac-l1-1 | lexical-bm25-ref | 10 | 0.500 | 1 |
| nmac-l1-1 | hybrid-bm25-ref | 10 | 0.600 | 1 |
| nmac-l1-1 | dense | 10 | 1.000 | 1 |
| nmac-l1-2 | lexical-fts-and | 0 | 0.000 | 0 |
| nmac-l1-2 | hybrid-fts-and | 10 | 1.000 | 1 |
| nmac-l1-2 | lexical-fts-or | 10 | 0.900 | 1 |
| nmac-l1-2 | hybrid-fts-or | 10 | 1.000 | 1 |
| nmac-l1-2 | lexical-bm25-ref | 10 | 1.000 | 1 |
| nmac-l1-2 | hybrid-bm25-ref | 10 | 0.900 | 1 |
| nmac-l1-2 | dense | 10 | 1.000 | 1 |
| nmac-l1-3 | lexical-fts-and | 0 | 0.000 | 0 |
| nmac-l1-3 | hybrid-fts-and | 10 | 0.700 | 1 |
| nmac-l1-3 | lexical-fts-or | 10 | 0.000 | 0 |
| nmac-l1-3 | hybrid-fts-or | 10 | 0.400 | 1 |
| nmac-l1-3 | lexical-bm25-ref | 10 | 0.900 | 1 |
| nmac-l1-3 | hybrid-bm25-ref | 10 | 0.800 | 1 |
| nmac-l1-3 | dense | 10 | 0.700 | 1 |
| nmac-l1-4 | lexical-fts-and | 0 | 0.000 | 0 |
| nmac-l1-4 | hybrid-fts-and | 10 | 0.400 | 1 |
| nmac-l1-4 | lexical-fts-or | 10 | 0.400 | 1 |
| nmac-l1-4 | hybrid-fts-or | 10 | 0.300 | 1 |
| nmac-l1-4 | lexical-bm25-ref | 10 | 0.800 | 1 |
| nmac-l1-4 | hybrid-bm25-ref | 10 | 0.500 | 1 |
| nmac-l1-4 | dense | 10 | 0.400 | 1 |
| nmac-l1-5 | lexical-fts-and | 0 | 0.000 | 0 |
| nmac-l1-5 | hybrid-fts-and | 10 | 0.800 | 1 |
| nmac-l1-5 | lexical-fts-or | 10 | 0.400 | 1 |
| nmac-l1-5 | hybrid-fts-or | 10 | 0.500 | 1 |
| nmac-l1-5 | lexical-bm25-ref | 10 | 0.900 | 1 |
| nmac-l1-5 | hybrid-bm25-ref | 10 | 0.700 | 1 |
| nmac-l1-5 | dense | 10 | 0.800 | 1 |
| equip-l1-1 | lexical-fts-and | 10 | 0.900 | 1 |
| equip-l1-1 | hybrid-fts-and | 10 | 0.800 | 1 |
| equip-l1-1 | lexical-fts-or | 10 | 0.700 | 1 |
| equip-l1-1 | hybrid-fts-or | 10 | 0.900 | 1 |
| equip-l1-1 | lexical-bm25-ref | 10 | 0.900 | 1 |
| equip-l1-1 | hybrid-bm25-ref | 10 | 0.900 | 1 |
| equip-l1-1 | dense | 10 | 0.900 | 1 |
| equip-l1-2 | lexical-fts-and | 0 | 0.000 | 0 |
| equip-l1-2 | hybrid-fts-and | 10 | 0.500 | 1 |
| equip-l1-2 | lexical-fts-or | 10 | 0.300 | 1 |
| equip-l1-2 | hybrid-fts-or | 10 | 0.500 | 1 |
| equip-l1-2 | lexical-bm25-ref | 10 | 0.500 | 1 |
| equip-l1-2 | hybrid-bm25-ref | 10 | 0.600 | 1 |
| equip-l1-2 | dense | 10 | 0.500 | 1 |
| equip-l1-3 | lexical-fts-and | 0 | 0.000 | 0 |
| equip-l1-3 | hybrid-fts-and | 10 | 0.700 | 1 |
| equip-l1-3 | lexical-fts-or | 10 | 0.800 | 1 |
| equip-l1-3 | hybrid-fts-or | 10 | 0.700 | 1 |
| equip-l1-3 | lexical-bm25-ref | 10 | 0.800 | 1 |
| equip-l1-3 | hybrid-bm25-ref | 10 | 0.700 | 1 |
| equip-l1-3 | dense | 10 | 0.700 | 1 |
| equip-l1-4 | lexical-fts-and | 0 | 0.000 | 0 |
| equip-l1-4 | hybrid-fts-and | 10 | 0.900 | 1 |
| equip-l1-4 | lexical-fts-or | 10 | 0.300 | 1 |
| equip-l1-4 | hybrid-fts-or | 10 | 0.500 | 1 |
| equip-l1-4 | lexical-bm25-ref | 10 | 0.300 | 1 |
| equip-l1-4 | hybrid-bm25-ref | 10 | 0.600 | 1 |
| equip-l1-4 | dense | 10 | 0.900 | 1 |
| equip-l1-5 | lexical-fts-and | 0 | 0.000 | 0 |
| equip-l1-5 | hybrid-fts-and | 10 | 0.700 | 1 |
| equip-l1-5 | lexical-fts-or | 10 | 0.500 | 1 |
| equip-l1-5 | hybrid-fts-or | 10 | 0.800 | 1 |
| equip-l1-5 | lexical-bm25-ref | 10 | 0.500 | 1 |
| equip-l1-5 | hybrid-bm25-ref | 10 | 0.700 | 1 |
| equip-l1-5 | dense | 10 | 0.700 | 1 |
| ri-l2-1 | lexical-fts-and | 0 | 0.000 | 0 |
| ri-l2-1 | hybrid-fts-and | 10 | 0.900 | 1 |
| ri-l2-1 | lexical-fts-or | 10 | 0.700 | 1 |
| ri-l2-1 | hybrid-fts-or | 10 | 0.700 | 1 |
| ri-l2-1 | lexical-bm25-ref | 10 | 0.800 | 1 |
| ri-l2-1 | hybrid-bm25-ref | 10 | 0.700 | 1 |
| ri-l2-1 | dense | 10 | 0.900 | 1 |
| ri-l2-2 | lexical-fts-and | 10 | 0.300 | 1 |
| ri-l2-2 | hybrid-fts-and | 10 | 0.400 | 1 |
| ri-l2-2 | lexical-fts-or | 10 | 0.400 | 1 |
| ri-l2-2 | hybrid-fts-or | 10 | 0.500 | 1 |
| ri-l2-2 | lexical-bm25-ref | 10 | 0.200 | 1 |
| ri-l2-2 | hybrid-bm25-ref | 10 | 0.400 | 1 |
| ri-l2-2 | dense | 10 | 0.600 | 1 |
| alt-l2-1 | lexical-fts-and | 0 | 0.000 | 0 |
| alt-l2-1 | hybrid-fts-and | 10 | 0.400 | 1 |
| alt-l2-1 | lexical-fts-or | 10 | 0.100 | 1 |
| alt-l2-1 | hybrid-fts-or | 10 | 0.400 | 1 |
| alt-l2-1 | lexical-bm25-ref | 10 | 0.300 | 1 |
| alt-l2-1 | hybrid-bm25-ref | 10 | 0.400 | 1 |
| alt-l2-1 | dense | 10 | 0.400 | 1 |
| alt-l2-2 | lexical-fts-and | 0 | 0.000 | 0 |
| alt-l2-2 | hybrid-fts-and | 10 | 0.600 | 1 |
| alt-l2-2 | lexical-fts-or | 10 | 0.500 | 1 |
| alt-l2-2 | hybrid-fts-or | 10 | 0.400 | 1 |
| alt-l2-2 | lexical-bm25-ref | 10 | 0.200 | 1 |
| alt-l2-2 | hybrid-bm25-ref | 10 | 0.400 | 1 |
| alt-l2-2 | dense | 10 | 0.600 | 1 |
| nmac-l2-1 | lexical-fts-and | 0 | 0.000 | 0 |
| nmac-l2-1 | hybrid-fts-and | 10 | 0.500 | 1 |
| nmac-l2-1 | lexical-fts-or | 10 | 0.500 | 1 |
| nmac-l2-1 | hybrid-fts-or | 10 | 0.400 | 1 |
| nmac-l2-1 | lexical-bm25-ref | 10 | 0.600 | 1 |
| nmac-l2-1 | hybrid-bm25-ref | 10 | 0.400 | 1 |
| nmac-l2-1 | dense | 10 | 0.500 | 1 |
| nmac-l2-2 | lexical-fts-and | 0 | 0.000 | 0 |
| nmac-l2-2 | hybrid-fts-and | 10 | 0.600 | 1 |
| nmac-l2-2 | lexical-fts-or | 10 | 0.800 | 1 |
| nmac-l2-2 | hybrid-fts-or | 10 | 0.900 | 1 |
| nmac-l2-2 | lexical-bm25-ref | 10 | 0.700 | 1 |
| nmac-l2-2 | hybrid-bm25-ref | 10 | 0.800 | 1 |
| nmac-l2-2 | dense | 10 | 0.600 | 1 |
| equip-l2-1 | lexical-fts-and | 0 | 0.000 | 0 |
| equip-l2-1 | hybrid-fts-and | 10 | 0.800 | 1 |
| equip-l2-1 | lexical-fts-or | 10 | 0.400 | 1 |
| equip-l2-1 | hybrid-fts-or | 10 | 0.900 | 1 |
| equip-l2-1 | lexical-bm25-ref | 10 | 0.800 | 1 |
| equip-l2-1 | hybrid-bm25-ref | 10 | 0.700 | 1 |
| equip-l2-1 | dense | 10 | 0.800 | 1 |
| equip-l2-2 | lexical-fts-and | 0 | 0.000 | 0 |
| equip-l2-2 | hybrid-fts-and | 10 | 0.500 | 1 |
| equip-l2-2 | lexical-fts-or | 10 | 0.400 | 1 |
| equip-l2-2 | hybrid-fts-or | 10 | 0.600 | 1 |
| equip-l2-2 | lexical-bm25-ref | 10 | 0.200 | 1 |
| equip-l2-2 | hybrid-bm25-ref | 10 | 0.400 | 1 |
| equip-l2-2 | dense | 10 | 0.500 | 1 |

## Per-query partial-coverage development signals

| Query | Configuration | Judged / returned | P@10 proxy (coverage) | MRR (coverage) | nDCG@10 (coverage) |
|---|---|---:|---:|---:|---:|
| ri-l2-1 | lexical-fts-and | 0 / 0 | N/A (0%) | N/A (0%) | N/A (0%) |
| ri-l2-1 | hybrid-fts-and | 9 / 10 | 1.0000 (90%) | 1.0000 (90%) | 0.8523 (90%) |
| ri-l2-1 | lexical-fts-or | 1 / 10 | 1.0000 (10%) | 1.0000 (10%) | 0.5000 (10%) |
| ri-l2-1 | hybrid-fts-or | 4 / 10 | 1.0000 (40%) | 1.0000 (40%) | 0.6803 (40%) |
| ri-l2-1 | lexical-bm25-ref | 1 / 10 | 1.0000 (10%) | 1.0000 (10%) | 0.5000 (10%) |
| ri-l2-1 | hybrid-bm25-ref | 5 / 10 | 1.0000 (50%) | 1.0000 (50%) | 0.6653 (50%) |
| ri-l2-1 | dense | 9 / 10 | 1.0000 (90%) | 1.0000 (90%) | 0.8523 (90%) |
| ri-l2-2 | lexical-fts-and | 4 / 10 | 0.5000 (40%) | 0.3333 (40%) | 0.2657 (40%) |
| ri-l2-2 | hybrid-fts-and | 5 / 10 | 0.8000 (50%) | 1.0000 (50%) | 0.7469 (50%) |
| ri-l2-2 | lexical-fts-or | 0 / 10 | N/A (0%) | N/A (0%) | N/A (0%) |
| ri-l2-2 | hybrid-fts-or | 2 / 10 | 1.0000 (20%) | 1.0000 (20%) | 1.0000 (20%) |
| ri-l2-2 | lexical-bm25-ref | 1 / 10 | 1.0000 (10%) | 1.0000 (10%) | 0.5000 (10%) |
| ri-l2-2 | hybrid-bm25-ref | 4 / 10 | 1.0000 (40%) | 1.0000 (40%) | 1.0000 (40%) |
| ri-l2-2 | dense | 6 / 10 | 1.0000 (60%) | 1.0000 (60%) | 0.9461 (60%) |
| alt-l2-1 | lexical-fts-and | 0 / 0 | N/A (0%) | N/A (0%) | N/A (0%) |
| alt-l2-1 | hybrid-fts-and | 3 / 10 | 1.0000 (30%) | 1.0000 (30%) | 1.0000 (30%) |
| alt-l2-1 | lexical-fts-or | 0 / 10 | N/A (0%) | N/A (0%) | N/A (0%) |
| alt-l2-1 | hybrid-fts-or | 2 / 10 | 1.0000 (20%) | 1.0000 (20%) | 1.0000 (20%) |
| alt-l2-1 | lexical-bm25-ref | 0 / 10 | N/A (0%) | N/A (0%) | N/A (0%) |
| alt-l2-1 | hybrid-bm25-ref | 1 / 10 | 1.0000 (10%) | 1.0000 (10%) | 1.0000 (10%) |
| alt-l2-1 | dense | 3 / 10 | 1.0000 (30%) | 1.0000 (30%) | 1.0000 (30%) |
| alt-l2-2 | lexical-fts-and | 0 / 0 | N/A (0%) | N/A (0%) | N/A (0%) |
| alt-l2-2 | hybrid-fts-and | 6 / 10 | 1.0000 (60%) | 1.0000 (60%) | 0.7893 (60%) |
| alt-l2-2 | lexical-fts-or | 2 / 10 | 1.0000 (20%) | 1.0000 (20%) | 1.0000 (20%) |
| alt-l2-2 | hybrid-fts-or | 3 / 10 | 1.0000 (30%) | 1.0000 (30%) | 1.0000 (30%) |
| alt-l2-2 | lexical-bm25-ref | 2 / 10 | 1.0000 (20%) | 1.0000 (20%) | 1.0000 (20%) |
| alt-l2-2 | hybrid-bm25-ref | 4 / 10 | 1.0000 (40%) | 1.0000 (40%) | 0.9159 (40%) |
| alt-l2-2 | dense | 6 / 10 | 1.0000 (60%) | 1.0000 (60%) | 0.7893 (60%) |
| nmac-l2-1 | lexical-fts-and | 0 / 0 | N/A (0%) | N/A (0%) | N/A (0%) |
| nmac-l2-1 | hybrid-fts-and | 6 / 10 | 1.0000 (60%) | 1.0000 (60%) | 0.7677 (60%) |
| nmac-l2-1 | lexical-fts-or | 0 / 10 | N/A (0%) | N/A (0%) | N/A (0%) |
| nmac-l2-1 | hybrid-fts-or | 1 / 10 | 1.0000 (10%) | 1.0000 (10%) | 0.5000 (10%) |
| nmac-l2-1 | lexical-bm25-ref | 0 / 10 | N/A (0%) | N/A (0%) | N/A (0%) |
| nmac-l2-1 | hybrid-bm25-ref | 2 / 10 | 1.0000 (20%) | 1.0000 (20%) | 0.6199 (20%) |
| nmac-l2-1 | dense | 6 / 10 | 1.0000 (60%) | 1.0000 (60%) | 0.7677 (60%) |
| nmac-l2-2 | lexical-fts-and | 0 / 0 | N/A (0%) | N/A (0%) | N/A (0%) |
| nmac-l2-2 | hybrid-fts-and | 7 / 10 | 1.0000 (70%) | 1.0000 (70%) | 0.7724 (70%) |
| nmac-l2-2 | lexical-fts-or | 0 / 10 | N/A (0%) | N/A (0%) | N/A (0%) |
| nmac-l2-2 | hybrid-fts-or | 3 / 10 | 1.0000 (30%) | 1.0000 (30%) | 0.5000 (30%) |
| nmac-l2-2 | lexical-bm25-ref | 0 / 10 | N/A (0%) | N/A (0%) | N/A (0%) |
| nmac-l2-2 | hybrid-bm25-ref | 0 / 10 | N/A (0%) | N/A (0%) | N/A (0%) |
| nmac-l2-2 | dense | 7 / 10 | 1.0000 (70%) | 1.0000 (70%) | 0.7724 (70%) |
| equip-l2-1 | lexical-fts-and | 0 / 0 | N/A (0%) | N/A (0%) | N/A (0%) |
| equip-l2-1 | hybrid-fts-and | 3 / 10 | 1.0000 (30%) | 1.0000 (30%) | 0.8403 (30%) |
| equip-l2-1 | lexical-fts-or | 0 / 10 | N/A (0%) | N/A (0%) | N/A (0%) |
| equip-l2-1 | hybrid-fts-or | 2 / 10 | 1.0000 (20%) | 1.0000 (20%) | 1.0000 (20%) |
| equip-l2-1 | lexical-bm25-ref | 1 / 10 | 1.0000 (10%) | 1.0000 (10%) | 0.5000 (10%) |
| equip-l2-1 | hybrid-bm25-ref | 2 / 10 | 1.0000 (20%) | 1.0000 (20%) | 0.8597 (20%) |
| equip-l2-1 | dense | 3 / 10 | 1.0000 (30%) | 1.0000 (30%) | 0.8403 (30%) |
| equip-l2-2 | lexical-fts-and | 0 / 0 | N/A (0%) | N/A (0%) | N/A (0%) |
| equip-l2-2 | hybrid-fts-and | 1 / 10 | 1.0000 (10%) | 1.0000 (10%) | 1.0000 (10%) |
| equip-l2-2 | lexical-fts-or | 2 / 10 | 1.0000 (20%) | 1.0000 (20%) | 1.0000 (20%) |
| equip-l2-2 | hybrid-fts-or | 2 / 10 | 1.0000 (20%) | 1.0000 (20%) | 1.0000 (20%) |
| equip-l2-2 | lexical-bm25-ref | 0 / 10 | N/A (0%) | N/A (0%) | N/A (0%) |
| equip-l2-2 | hybrid-bm25-ref | 0 / 10 | N/A (0%) | N/A (0%) | N/A (0%) |
| equip-l2-2 | dense | 1 / 10 | 1.0000 (10%) | 1.0000 (10%) | 1.0000 (10%) |

## Reproduction and controls

Run `uv run python eval/run_lexical_bakeoff.py` with UTF-8 environment variables set. The full versioned record is `eval/experiment_step6.json`; detailed evidence rankings stay in ignored `data/eval_rankings_step6.json`. Original experiment and Step 5 tables are preserved.

FTS-AND calls the unchanged production implementation. OR uses lowercase ASCII alphanumeric content terms minus sklearn's fixed English stoplist, deduplicated and joined with `|`, PostgreSQL simple configuration and ts_rank_cd. Stopword-only input returns no matches. No stemming or query expansion.

BM25 reference uses [rank_bm25 BM25Okapi](https://github.com/dorianbrown/rank_bm25) 0.2.2 (k1=1.5, b=0.75, epsilon=0.25), identical content-term preprocessing for chunk texts and queries, no labels. Nonpositive scores excluded. These are three complete lexical configurations, not a controlled scoring-formula-only ablation. BM25 is offline/evaluation-only and needs a fresh in-memory index each run. Indexing time and software versions are in the experiment record.

Winner pool: `eval\judging_pool_step6_additions.csv`, 75 unjudged pairs from **lexical-bm25-ref** only, blinded and shuffled (seed 20261121), blank grades/notes. No human judgments were created. Original queries, qrels, corpus manifests, production retrieval and generation hashes were verified unchanged.

## Acceptance checks

- All seven configurations executed on the verified ready 20k corpus; 196 per-query Layer-1 rows and 56 per-query Layer-2 rows.
- Coverage printed beside every Layer-2 signal; unknown pairs removed rather than assigned irrelevant grades.
- `uv run pytest -q`: 42 passed (all 38 prior tests plus four bake-off tests).
- `uv run ruff check .` and `git diff --check`: passed.
- Protected production/query/qrels/corpus assets unchanged by SHA-256; no tracked `data/` or `.env`.
- Production defaults unchanged. Step 7 not started.
