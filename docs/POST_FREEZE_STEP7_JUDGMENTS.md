# Five Step 7 judgments — post-freeze development addendum

The five-row `eval/judging_pool_step7_additions.csv` became fully graded during
this task. Its original query/ACN/synopsis tuples were verified unchanged;
grades **1 / 2 / 1 / 1 / 2** are human-provided, not inferred by the agent.

The existing `safelens.evaluation.import_judgments` validator imported exactly
these five pairs. Its query scope was derived from their four development
query IDs in ignored `data/`, with the exact recorded five-pair whitelist and
the full 20k manifest. No validation rule was weakened. The full merged file
was then validated against all eight development Layer-2 query IDs.

`eval/qrels.jsonl`: **134 → 139 rows**, zero duplicates. The complete original
134-line byte prefix is preserved, including grades, notes and line endings.
The newly filled pool matches both the recorded missing-pair set and the
current production hybrid top ten. All eight production top-ten ACN orders
were independently retrieved and verified identical to the Step 7 rankings;
no retrieval setting or production retrieval code changed.

Completed production hybrid row, unfiltered, 20,000 reports, dense:BM25 10:1:

| P@10 | MRR | nDCG@10 | Top-ten judgment coverage |
| ---: | ---: | ---: | ---: |
| **0.9625** | **1.0000** | **0.8528626272** | **100%** (80/80 pairs) |

Metrics use the existing strict `judged_metrics` implementation: grade ≥ 1
is relevant, denominator 10, linear gains 2/1/0 and a pooled ideal. No unjudged
pair is zero-filled. `eval/experiment_step7_part1.json` records the completed
hybrid averages and per-query rows, the new qrels hash and import provenance;
only the Step 7 Part 1 development section of `eval/results.md` was updated.

**Dense rows remain unchanged**, as instructed: P@10 0.9500, MRR 1.0000,
nDCG@10 0.8456998926. Dense and legacy lexical retain their original 134-qrel
judgment version. The new hybrid row uses all 139 qrels; the extra grade-2
judgment changes the pooled nDCG ideal for `nmac-l2-1`. Consequently the retained
dense/lexical nDCG values and the new hybrid nDCG are **not a fresh common-pool
head-to-head comparison**. This judgment-version distinction is disclosed in
the experiment record and development table, without silently rescoring dense.

`POST_FREEZE_STEP7_JUDGMENTS.json` records the import and exact unrounded row.
The frozen final queries, qrels, freeze document, experiment, run-once record
and Step 7D results section remain byte-identical. The frozen set was never
run or rescored. The [routing disclosure](POST_FREEZE_FIX_CNT1.md) describes
the separately authorized production mapping patch and hash reissue.
