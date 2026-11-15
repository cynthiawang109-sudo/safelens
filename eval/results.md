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
| lexical | 11.69 | 19.35 |
| dense | 105.43 | 222.26 |
| hybrid | 104.49 | 195.96 |

## Candidate-depth check

Defaults remain 100/50. Doubling candidate chunks to 200 is a separately recorded sensitivity check over all 28 category queries.

| Retriever | Queries with changed top-10 ACN order | Change in mean Category Precision@10 |
|---|---:|---:|
| lexical | 0/28 | +0.000 |
| dense | 0/28 | +0.000 |
| hybrid | 0/28 | +0.000 |

## Layer-2 judging is pending

`judging_pool.csv` contains **88** unique (query_id, acn) pairs for eight queries, shuffled with seed 20261116.
The sheet contains no retriever identity or ranks. Grade and note are blank; no documents have been pre-judged.
Cynthia: read synopsis first, consult the indexed full narrative if ambiguous, then use grades 2=directly relevant, 1=partially relevant, 0=irrelevant. Record notes as needed.
Only the judging CSV should be used during blinded judging. A future step will version completed qrels and compute relevance metrics; unjudged reports are not assumed irrelevant.

## Abstention controls

Controls are present with `expect: insufficient_evidence`. Absence was checked against this frozen subset; generation outcomes are **not run in Step 3**.

- `control-domain`: absence verified; `{"matching_report_counts": {"Pelagic Meridian": 0, "MARINE-CONTROL-20261115-X": 0, "ballast pump": 0}}`
- `control-time`: absence verified; `{"acn": "1857031", "report_month": "2021-11", "content_hash": "d37509d66f1bc4eedc11e5bb5dc3a08f006ed5c5754c7a1aa340d47c381e6295", "temporal_marker_found": false, "manual_full_text_inspection": "Entire synopsis and narrative manually inspected: neither contains an event day or clock time; structured date has month precision only. Broad source time-of-day bands cannot establish an exact timestamp."}`
- `control-acn`: absence verified; `{"acn": "999999999999999", "present": false}`

## Limitations and experiment record

These are weak-label category metrics, not judged Precision@10, MRR, nDCG, or proof that any method is better at answering questions. Twenty-eight hand-written queries are a development set, not an independent held-out test.
The category-balanced subset includes every available runway-incursion report; category overlap and year skew are recorded in the manifest and DATA_NOTES. Synopsis text is included in indexing and may simplify retrieval.
PostgreSQL FTS uses simple configuration and websearch query semantics; long conjunctive queries may underfill the top ten. This baseline is not BM25. Exact cosine search uses no ANN index.
Candidate-depth changes above must be considered before interpreting hybrid results; the default was not silently tuned.
The complete experiment configuration, corpus/content hashes, query/qrels hashes, per-query metrics and latency samples, software/hardware notes, and timestamp are in `experiment.json`.
Generation/API/UI and human judging are outside this completed Step 3.
