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
The original Mini manifest and judging pool are preserved; the original 88 qrel rows are unchanged and 46 human-graded additions have been appended. `current_corpus.json` designates `corpus_manifest_20k.json`; experiment.json records that switch and the archived `experiment_5k.json` baseline.

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

| Retriever | Metric | 5,000 | 20,000 | Delta |
|---|---|---:|---:|---:|
| lexical | precision_at_10 | 0.050 | 0.050 | +0.000 |
| lexical | mrr | 0.042 | 0.031 | -0.010 |
| lexical | ndcg_at_10 | 0.037 | 0.025 | -0.012 |
| dense | precision_at_10 | 0.963 | 0.950 | -0.013 |
| dense | mrr | 1.000 | 1.000 | +0.000 |
| dense | ndcg_at_10 | 0.914 | 0.846 | -0.068 |
| hybrid | precision_at_10 | 0.938 | 0.925 | -0.012 |
| hybrid | mrr | 1.000 | 1.000 | +0.000 |
| hybrid | ndcg_at_10 | 0.889 | 0.809 | -0.080 |

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

### Per-query Layer-2 metrics

| Query | Retriever | Precision@10 | MRR | nDCG@10 |
|---|---|---:|---:|---:|
| ri-l2-1 | lexical | 0.000 | 0.000 | 0.000 |
| ri-l2-1 | dense | 1.000 | 1.000 | 0.849 |
| ri-l2-1 | hybrid | 1.000 | 1.000 | 0.849 |
| ri-l2-2 | lexical | 0.400 | 0.250 | 0.200 |
| ri-l2-2 | dense | 0.900 | 1.000 | 0.855 |
| ri-l2-2 | hybrid | 0.700 | 1.000 | 0.564 |
| alt-l2-1 | lexical | 0.000 | 0.000 | 0.000 |
| alt-l2-1 | dense | 1.000 | 1.000 | 0.933 |
| alt-l2-1 | hybrid | 1.000 | 1.000 | 0.933 |
| alt-l2-2 | lexical | 0.000 | 0.000 | 0.000 |
| alt-l2-2 | dense | 0.900 | 1.000 | 0.826 |
| alt-l2-2 | hybrid | 0.900 | 1.000 | 0.826 |
| nmac-l2-1 | lexical | 0.000 | 0.000 | 0.000 |
| nmac-l2-1 | dense | 0.900 | 1.000 | 0.763 |
| nmac-l2-1 | hybrid | 0.900 | 1.000 | 0.763 |
| nmac-l2-2 | lexical | 0.000 | 0.000 | 0.000 |
| nmac-l2-2 | dense | 0.900 | 1.000 | 0.746 |
| nmac-l2-2 | hybrid | 0.900 | 1.000 | 0.746 |
| equip-l2-1 | lexical | 0.000 | 0.000 | 0.000 |
| equip-l2-1 | dense | 1.000 | 1.000 | 0.938 |
| equip-l2-1 | hybrid | 1.000 | 1.000 | 0.938 |
| equip-l2-2 | lexical | 0.000 | 0.000 | 0.000 |
| equip-l2-2 | dense | 1.000 | 1.000 | 0.855 |
| equip-l2-2 | hybrid | 1.000 | 1.000 | 0.855 |

### Latency and candidate-depth sensitivity

| Retriever | Mean ms | p95 ms | Top-ten changes at 200 candidate chunks |
|---|---:|---:|---:|
| lexical | 10.46 | 31.30 | 0/28 |
| dense | 154.63 | 274.33 | 0/28 |
| hybrid | 146.52 | 203.35 | 0/28 |

Default candidate depths remain 100 chunks / 50 reports, report-level RRF k=60, ties by ACN. All controls were reverified absent; this evaluator makes no generation calls.
Full corpus/query/qrels hashes, per-query measurements, sensitivity records, configuration, software, hardware, and timestamp are in `experiment.json`. This run uses the unchanged production retrievers, not the Step 6 experimental variants.

### Human-judgment completion (2026-11-16)

Cynthia graded all 46 rows in `judging_pool_20k_additions.csv`. The existing importer validated the combined 92-pair top-ten pool against `corpus_manifest_20k.json` and `data/eval_rankings_20k.json`; only the 46 new pairs were appended to `qrels.jsonl`. The original 88 rows are preserved byte-for-byte: 134 total unique query/ACN pairs, zero duplicates. Import provenance is in `eval/judgments_20k_import.json`.

All 92 unique pooled top-ten pairs now have human labels (100% returned-result coverage for all three retrievers). These are full-coverage **development** metrics for eight queries, not Step 6 partial-coverage signals or final-test scores. Precision@10 uses denominator 10 (including underfill); MRR uses the top ten; nDCG uses linear gains 2/1/0 and the pooled ideal.

Deltas use the archived 5k experiment with its original 88 judgments. The current 20k experiment uses 134 judgments, including the 46 new pairs; nDCG ideal gains therefore use the expanded known pool. The 5k baseline was not rescored, and this judgment-pool change should be considered when interpreting nDCG deltas.

| Retriever | P@10 | Delta vs 5k | MRR | Delta vs 5k | nDCG@10 | Delta vs 5k |
|---|---:|---:|---:|---:|---:|---:|
| lexical | 0.0500 | +0.0000 | 0.0312 | -0.0104 | 0.0250 | -0.0118 |
| dense | 0.9500 | -0.0125 | 1.0000 | +0.0000 | 0.8457 | -0.0683 |
| hybrid | 0.9250 | -0.0125 | 1.0000 | +0.0000 | 0.8093 | -0.0800 |

Retrieval, corpus, query, prompt, and generation configurations are unchanged. Step 6 artifacts and its historical qrels version are preserved; this follow-up does not rerun or rescore that bake-off. Step 7 has not started.


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

<!-- fusion-bakeoff-step6b -->
## Step 6B: fusion-weight mini bake-off (development)

Corpus: 20,000 reports, 28,306 embedded chunks; ready build 4. All 28 category queries; no category filter, label retrieval features, query edits, or generation calls. These are development results, not final-test estimates.

### Fixed protocol

The eight dense:lexical ratios and two families were fixed in `eval/step6b_design.json` before results. Each leg retains at most 50 reports after fetching 100 chunks and max-score aggregation by ACN. Weighted RRF uses wd/(60+rank_dense) + wl/(60+rank_lexical), missing components contribute zero; ties break by ACN. Normalized fusion applies per-query min-max to each complete candidate leg, then wd*d + wl*l; absent reports and constant-score legs contribute zero. Zero-weight legs are excluded, and pure-leg endpoints preserve the exact source ranking.

Select maximum Category P@10, then Hit@10, then smaller relative lexical weight wl/(wd+wl). Remaining exact ties are reported as co-winners; fixed family order only picks a display representative. No extra weights were tried. P@10 uses denominator 10, including underfill. Category agreement is not judged relevance.

Candidate cache: reused complete Step 6B candidate recapture; original Step 6 cache contains only top ten, so both legs were captured once at full depth. The original Step 6 cache is preserved. The full-depth recapture matches all original top-ten ACN orders and representative chunk IDs; equal-weight hybrid ACN orders also match Step 6. All grid trials subsequently use the identical cached lists; no retrieval per weight.

### Full grid

| Family | Dense:BM25 | Category P@10 | Hit@10 | Delta P@10 vs dense |
|---|---:|---:|---:|---:|
| weighted_rrf | 1:0 | 0.6286 | 0.9643 | +0.0000 |
| weighted_rrf | 10:1 | 0.6429 | 1.0000 | +0.0143 |
| weighted_rrf | 5:1 | 0.6429 | 1.0000 | +0.0143 |
| weighted_rrf | 3:1 | 0.6107 | 1.0000 | -0.0179 |
| weighted_rrf | 2:1 | 0.6107 | 1.0000 | -0.0179 |
| weighted_rrf | 1:1 | 0.5786 | 1.0000 | -0.0500 |
| weighted_rrf | 1:2 | 0.5964 | 1.0000 | -0.0321 |
| weighted_rrf | 0:1 | 0.5714 | 1.0000 | -0.0571 |
| normalized_scores | 1:0 | 0.6286 | 0.9643 | +0.0000 |
| normalized_scores | 10:1 | 0.6250 | 0.9643 | -0.0036 |
| normalized_scores | 5:1 | 0.6214 | 0.9643 | -0.0071 |
| normalized_scores | 3:1 | 0.6321 | 0.9643 | +0.0036 |
| normalized_scores | 2:1 | 0.6214 | 0.9643 | -0.0071 |
| normalized_scores | 1:1 | 0.6179 | 0.9643 | -0.0107 |
| normalized_scores | 1:2 | 0.5786 | 1.0000 | -0.0500 |
| normalized_scores | 0:1 | 0.5714 | 1.0000 | -0.0571 |

### Best configuration and recommendation

Display representative: **weighted_rrf 10:1**. Co-winners under the complete selection rule: weighted_rrf:10:1. Category P@10 **0.6429**, dense **0.6286**, margin **+0.0143** (+4 matching reports across 280 slots). Per-query **8 wins / 5 losses / 15 ties** versus dense.

Recommend adopting weighted_rrf 10:1 as the flagship default under the fixed primary selection rule: Category P@10 improves by +0.0143 on this development set. Adoption remains a separate decision.

Although 8/28 queries improve and 5/28 worsen, the net gain is only 4 matching reports. The two largest positive flips (equip-l2-2, ri-l1-2) contribute 4 matches; excluding those queries leaves +0 net matches. The overall win therefore does rest on two query flips in aggregate; it is a fragile development margin, not broad evidence of superiority.

Boundary-grid winner: **True** (dense-heaviest mixed ratio tested; pure-leg endpoints also evaluated). The grid was not extended. Production defaults and all production code paths remain unchanged; adopting any recommendation needs Cynthia's separate decision. Step 7 has not started.

### Per-query comparison versus dense

| Query | Dense Category P@10 | Best Category P@10 | Delta | Outcome |
|---|---:|---:|---:|---|
| ri-l1-1 | 0.900 | 0.900 | +0.000 | tie |
| ri-l1-2 | 0.700 | 0.900 | +0.200 | win |
| ri-l1-3 | 0.000 | 0.100 | +0.100 | win |
| ri-l1-4 | 0.200 | 0.200 | +0.000 | tie |
| ri-l1-5 | 1.000 | 0.900 | -0.100 | loss |
| alt-l1-1 | 0.900 | 0.800 | -0.100 | loss |
| alt-l1-2 | 0.200 | 0.300 | +0.100 | win |
| alt-l1-3 | 0.600 | 0.700 | +0.100 | win |
| alt-l1-4 | 0.400 | 0.400 | +0.000 | tie |
| alt-l1-5 | 0.200 | 0.200 | +0.000 | tie |
| nmac-l1-1 | 1.000 | 1.000 | +0.000 | tie |
| nmac-l1-2 | 1.000 | 1.000 | +0.000 | tie |
| nmac-l1-3 | 0.700 | 0.800 | +0.100 | win |
| nmac-l1-4 | 0.400 | 0.400 | +0.000 | tie |
| nmac-l1-5 | 0.800 | 0.800 | +0.000 | tie |
| equip-l1-1 | 0.900 | 0.900 | +0.000 | tie |
| equip-l1-2 | 0.500 | 0.500 | +0.000 | tie |
| equip-l1-3 | 0.700 | 0.800 | +0.100 | win |
| equip-l1-4 | 0.900 | 0.900 | +0.000 | tie |
| equip-l1-5 | 0.700 | 0.700 | +0.000 | tie |
| ri-l2-1 | 0.900 | 0.900 | +0.000 | tie |
| ri-l2-2 | 0.600 | 0.500 | -0.100 | loss |
| alt-l2-1 | 0.400 | 0.300 | -0.100 | loss |
| alt-l2-2 | 0.600 | 0.700 | +0.100 | win |
| nmac-l2-1 | 0.500 | 0.300 | -0.200 | loss |
| nmac-l2-2 | 0.600 | 0.600 | +0.000 | tie |
| equip-l2-1 | 0.800 | 0.800 | +0.000 | tie |
| equip-l2-2 | 0.500 | 0.700 | +0.200 | win |

### Layer-2 partial-coverage development signals

Uses the runtime `eval/qrels.jsonl` (51b93d1b97c873dbf6b6489a436bcde3cd0724b7e30f4acafc0bff0f78029465). Same Step 6 condensed protocol: remove unknown pairs from the original top ten; precision proxy is relevant/judged, MRR and DCG use condensed ranks, linear gains 2/1/0, ideal over known qrels at the same judged depth. No judged hits means undefined, excluded from macro means (query counts printed). Coverage = judged/10 including underfill; coverage of returned results is separately recorded in JSON. Unknowns never receive grade zero. These are **partial-coverage development signals**, not full-coverage scores and not used for selection. Condensation and the historical pooling can favor the original retrievers.

| Configuration | Precision proxy (coverage) | Condensed MRR (coverage) | Condensed nDCG (coverage) | Defined queries / 8 |
|---|---:|---:|---:|---:|
| best | 0.9594 (93.8%) | 1.0000 (93.8%) | 0.8491 (93.8%) | 8 |
| dense | 0.9500 (100.0%) | 1.0000 (100.0%) | 0.8457 (100.0%) | 8 |

| Query | Configuration | Judged / returned | Precision proxy (coverage) | MRR (coverage) | nDCG (coverage) |
|---|---|---:|---:|---:|---:|
| ri-l2-1 | best | 10 / 10 | 1.0000 (100.0%) | 1.0000 (100.0%) | 0.8353 (100.0%) |
| ri-l2-2 | best | 10 / 10 | 0.9000 (100.0%) | 1.0000 (100.0%) | 0.8028 (100.0%) |
| alt-l2-1 | best | 9 / 10 | 1.0000 (90.0%) | 1.0000 (90.0%) | 0.9298 (90.0%) |
| alt-l2-2 | best | 10 / 10 | 1.0000 (100.0%) | 1.0000 (100.0%) | 0.9477 (100.0%) |
| nmac-l2-1 | best | 8 / 10 | 0.8750 (80.0%) | 1.0000 (80.0%) | 0.7378 (80.0%) |
| nmac-l2-2 | best | 10 / 10 | 0.9000 (100.0%) | 1.0000 (100.0%) | 0.7278 (100.0%) |
| equip-l2-1 | best | 9 / 10 | 1.0000 (90.0%) | 1.0000 (90.0%) | 0.9646 (90.0%) |
| equip-l2-2 | best | 9 / 10 | 1.0000 (90.0%) | 1.0000 (90.0%) | 0.8471 (90.0%) |
| ri-l2-1 | dense | 10 / 10 | 1.0000 (100.0%) | 1.0000 (100.0%) | 0.8494 (100.0%) |
| ri-l2-2 | dense | 10 / 10 | 0.9000 (100.0%) | 1.0000 (100.0%) | 0.8550 (100.0%) |
| alt-l2-1 | dense | 10 / 10 | 1.0000 (100.0%) | 1.0000 (100.0%) | 0.9334 (100.0%) |
| alt-l2-2 | dense | 10 / 10 | 0.9000 (100.0%) | 1.0000 (100.0%) | 0.8263 (100.0%) |
| nmac-l2-1 | dense | 10 / 10 | 0.9000 (100.0%) | 1.0000 (100.0%) | 0.7629 (100.0%) |
| nmac-l2-2 | dense | 10 / 10 | 0.9000 (100.0%) | 1.0000 (100.0%) | 0.7457 (100.0%) |
| equip-l2-1 | dense | 10 / 10 | 1.0000 (100.0%) | 1.0000 (100.0%) | 0.9376 (100.0%) |
| equip-l2-2 | dense | 10 / 10 | 1.0000 (100.0%) | 1.0000 (100.0%) | 0.8552 (100.0%) |

### Reproduction and acceptance

Run `uv run python eval/run_fusion_bakeoff.py` with `PYTHONUTF8=1` and `PYTHONIOENCODING=utf-8`; set `HF_HUB_OFFLINE=1` for the already cached embedding model. Full configuration, all 448 grid/query rows, input and protected hashes, cache provenance, historical equivalence checks, and runtime qrels version are in `eval/experiment_step6b.json`. Detailed evidence stays in ignored `data/eval_rankings_step6b_candidates.json`. No corpus writes, reindexing, new judgments, production default changes, or additional grid trials.

Acceptance checks: **46 tests passed** (all 42 prior tests plus four new fusion tests), Ruff and `git diff --check` passed. Weighted-RRF 1:1 matches Step 6 hybrid rankings, and zero lexical weight reproduces dense rankings exactly. Both full grid families are reported; all protected hashes and prior results sections are unchanged.

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

<!-- answer-calibration-step7b -->
## Step 7B — answer-rate calibration (development)

Phase 1 diagnosed the generator's all-conditions requirement and the grader's complete-coverage requirement, not retrieval or citation validation. Fresh unchanged production responses and all five original Step 7 configurations were audited. Selected passages already contained each selected report's synopsis; packaging was not changed. See `docs/STEP7B_NOTES.md` for per-query trace references.

### One implicated calibration batch

Generation now uses explicit structured `answered` / `partial` / `insufficient_evidence` outcomes: report a supported mechanism with qualifications instead of requiring every condition or independently proven causality. Grader sufficiency means at least one relevant account addressing the mechanism, not all reports or all topic details. A partial status is read from the structured outcome rather than the occurrence of 'insufficient evidence' anywhere in a qualified answer. Unavailable precise dates/times, absent named identifiers, and out-of-domain questions still refuse.

Citation validation and evidence packaging functions are unchanged by hash. Reporter-account framing, passage-only claims, caps, query set, qrels, corpus, weights, and retrieval code remain fixed. There are no query-ID rules or qrel-based production filters. Qrels are used only after generation for evaluation; the 82 additions remain unjudged.

### Before/after summary

Production before = fresh unchanged HTTP Ask run; Dense-only and Hybrid-10:1 before = original Step 7 real-provider ablation with matching old generation/grader hashes. After uses the same eleven requests; production is through HTTP. All costs are actual provider tokens and request latency, mean over eleven requests, excluding warmup. Historical baseline latency versus current latency is descriptive, not a controlled provider-speed benchmark.

| Configuration | Supported normal / 8, before → after | Controls / 3, before → after | Citation precision on judged (coverage), after | Grade-0 supports |
|---|---:|---:|---:|---:|
| Production Ask | 1 → 8 | 3 → 3 | 100.0% (81.2%) | 0 |
| Dense-only | 0 → 8 | 3 → 3 | 100.0% (100.0%) | 0 |
| Hybrid-10:1 | 0 → 8 | 3 → 3 | 100.0% (100.0%) | 0 |

Unique cited reports count once per response. Precision = existing qrel grade ≥1 / judged cited reports. Coverage = judged / all cited reports. Unknown pairs are listed separately, never scored as irrelevant or assigned grades. These report-level qrels do not independently prove every generated claim. Precision before and all per-query counts are in the experiment record.

### Cost deltas

| Configuration | Mean input tokens, before → after (delta) | Mean output tokens, before → after (delta) | Mean latency seconds, before → after (delta) | Mean retries, before → after |
|---|---:|---:|---:|---:|
| Production Ask | 8775.5 → 6449.5 (-2326.0) | 659.5 → 479.3 (-180.3) | 14.20 → 9.74 (-4.46) | 1.82 → 0.82 |
| Dense-only | 2551.5 → 2826.5 (+275.0) | 99.8 → 117.4 (+17.5) | 2.40 → 2.60 (+0.20) | 0.00 → 0.00 |
| Hybrid-10:1 | 2618.3 → 2893.3 (+275.0) | 98.4 → 124.1 (+25.7) | 2.43 → 2.79 (+0.36) | 0.00 → 0.00 |

### Per-query status, citation precision and cost

| Configuration | Query | Before → after | Judged-relevant / judged cited; unknown | Input tokens before → after | Output tokens before → after | Latency seconds before → after (delta) |
|---|---|---|---|---:|---:|---:|
| Production Ask | ri-l2-1 | insufficient_evidence → partial | 2/2; 0 unknown | 8136 → 5057 | 485 → 346 | 11.94 → 9.13 (-2.80) |
| Production Ask | ri-l2-2 | insufficient_evidence → partial | 2/2; 0 unknown | 8133 → 5273 | 525 → 330 | 14.10 → 6.30 (-7.80) |
| Production Ask | alt-l2-1 | insufficient_evidence → partial | 1/1; 1 unknown | 9481 → 8452 | 661 → 517 | 14.19 → 11.42 (-2.77) |
| Production Ask | alt-l2-2 | insufficient_evidence → partial | 2/2; 0 unknown | 9703 → 4752 | 743 → 344 | 13.72 → 6.26 (-7.45) |
| Production Ask | nmac-l2-1 | insufficient_evidence → partial | 2/2; 0 unknown | 9719 → 5559 | 755 → 381 | 16.47 → 7.30 (-9.17) |
| Production Ask | nmac-l2-2 | insufficient_evidence → answered | 1/1; 1 unknown | 10980 → 7574 | 726 → 570 | 16.41 → 11.88 (-4.53) |
| Production Ask | equip-l2-1 | partial → answered | 1/1; 1 unknown | 9789 → 7696 | 755 → 541 | 17.65 → 10.89 (-6.76) |
| Production Ask | equip-l2-2 | insufficient_evidence → partial | 2/2; 0 unknown | 9531 → 4464 | 717 → 351 | 13.64 → 7.34 (-6.30) |
| Production Ask | control-domain | insufficient_evidence → insufficient_evidence | N/A (refusal/control) | 8027 → 8405 | 616 → 605 | 12.02 → 11.54 (-0.48) |
| Production Ask | control-time | insufficient_evidence → insufficient_evidence | N/A (refusal/control) | 6026 → 6327 | 640 → 647 | 14.46 → 12.87 (-1.59) |
| Production Ask | control-acn | insufficient_evidence → insufficient_evidence | N/A (refusal/control) | 7005 → 7385 | 632 → 640 | 11.55 → 12.18 (+0.63) |
| Dense-only | ri-l2-1 | insufficient_evidence → partial | 2/2; 0 unknown | 2655 → 2930 | 96 → 121 | 2.98 → 2.69 (-0.29) |
| Dense-only | ri-l2-2 | insufficient_evidence → partial | 2/2; 0 unknown | 2923 → 3198 | 107 → 132 | 2.35 → 2.28 (-0.07) |
| Dense-only | alt-l2-1 | insufficient_evidence → partial | 2/2; 0 unknown | 2493 → 2768 | 102 → 146 | 2.27 → 2.30 (+0.04) |
| Dense-only | alt-l2-2 | insufficient_evidence → answered | 2/2; 0 unknown | 2531 → 2806 | 92 → 168 | 2.27 → 4.94 (+2.67) |
| Dense-only | nmac-l2-1 | insufficient_evidence → partial | 2/2; 0 unknown | 2815 → 3090 | 119 → 143 | 2.42 → 2.81 (+0.39) |
| Dense-only | nmac-l2-2 | insufficient_evidence → partial | 2/2; 0 unknown | 2655 → 2930 | 108 → 137 | 2.52 → 2.42 (-0.09) |
| Dense-only | equip-l2-1 | insufficient_evidence → partial | 2/2; 0 unknown | 2577 → 2852 | 102 → 133 | 2.34 → 3.20 (+0.87) |
| Dense-only | equip-l2-2 | insufficient_evidence → partial | 2/2; 0 unknown | 2477 → 2752 | 122 → 121 | 3.30 → 2.69 (-0.61) |
| Dense-only | control-domain | insufficient_evidence → insufficient_evidence | N/A (refusal/control) | 2720 → 2995 | 61 → 72 | 1.77 → 2.11 (+0.34) |
| Dense-only | control-time | insufficient_evidence → insufficient_evidence | N/A (refusal/control) | 2018 → 2293 | 83 → 56 | 2.02 → 1.40 (-0.61) |
| Dense-only | control-acn | insufficient_evidence → insufficient_evidence | N/A (refusal/control) | 2202 → 2477 | 106 → 62 | 2.22 → 1.73 (-0.49) |
| Hybrid-10:1 | ri-l2-1 | insufficient_evidence → partial | 1/1; 0 unknown | 3046 → 3321 | 92 → 141 | 2.88 → 2.96 (+0.08) |
| Hybrid-10:1 | ri-l2-2 | insufficient_evidence → partial | 2/2; 0 unknown | 2926 → 3201 | 99 → 135 | 2.11 → 4.22 (+2.12) |
| Hybrid-10:1 | alt-l2-1 | insufficient_evidence → partial | 2/2; 0 unknown | 2773 → 3048 | 105 → 150 | 2.93 → 4.14 (+1.20) |
| Hybrid-10:1 | alt-l2-2 | insufficient_evidence → partial | 2/2; 0 unknown | 2531 → 2806 | 114 → 148 | 2.94 → 2.43 (-0.51) |
| Hybrid-10:1 | nmac-l2-1 | insufficient_evidence → partial | 2/2; 0 unknown | 2815 → 3090 | 119 → 141 | 2.59 → 3.62 (+1.02) |
| Hybrid-10:1 | nmac-l2-2 | insufficient_evidence → answered | 2/2; 0 unknown | 2577 → 2852 | 99 → 137 | 2.27 → 2.31 (+0.05) |
| Hybrid-10:1 | equip-l2-1 | insufficient_evidence → partial | 2/2; 0 unknown | 2823 → 3098 | 126 → 133 | 2.44 → 2.78 (+0.33) |
| Hybrid-10:1 | equip-l2-2 | insufficient_evidence → partial | 3/3; 0 unknown | 2477 → 2752 | 110 → 149 | 2.80 → 2.88 (+0.09) |
| Hybrid-10:1 | control-domain | insufficient_evidence → insufficient_evidence | N/A (refusal/control) | 2720 → 2995 | 61 → 78 | 2.15 → 1.69 (-0.45) |
| Hybrid-10:1 | control-time | insufficient_evidence → insufficient_evidence | N/A (refusal/control) | 1970 → 2245 | 102 → 110 | 1.78 → 2.38 (+0.61) |
| Hybrid-10:1 | control-acn | insufficient_evidence → insufficient_evidence | N/A (refusal/control) | 2143 → 2418 | 55 → 43 | 1.86 → 1.26 (-0.60) |

### Pre-registered outcome and stopping rule

**Success criteria met: True.** Production supported answers: 8/8 (required ≥6); every measured configuration controls 3/3 with zero invented citations: True; no answered/partial response cites a known grade-0 support: True.

One calibration batch was tested. No further loosening was attempted.

Full record: `eval/experiment_step7b.json`. Diagnosis: `eval/experiment_step7b_diagnosis.json`. Raw prompts, pre-validation outputs, and passage-bearing responses stay in ignored `data/`. Run `uv run python eval/diagnose_answer_rate.py` on the original pre-calibration source to capture diagnosis; run `uv run python eval/remeasure_answer_rate.py` for the registered calibrated source (matching checkpoints reused). No final-test queries or Step 8 work.

## Final validation

All 57 tests passed, including the 53 prior tests and four calibration tests pinning mechanism-level prompts, explicit partial outcomes, and fail-closed fabricated/uncited answers. Ruff and `git diff --check` passed. All returned citation passages match their indexed DB chunks. Citation validation and evidence selection functions retain their original hashes; retrieval defaults and corpus snapshots, queries, qrels, and all 82 blank ablation additions are unchanged. All per-query diagnosis references resolve. See `docs/STEP7B_VALIDATION.json`.

The production citation precision is 13/13 judged report citations at 13/16 judgment coverage. The other three cited report pairs remain unknown, not incorrect or automatically labeled. These development results meet the specified criteria; they do not constitute independent claim-level faithfulness judgments or final-test accuracy. No further loosening or Step 8 work was performed.
