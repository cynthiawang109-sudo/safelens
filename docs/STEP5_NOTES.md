# Step 5 — 20,000-report scale-up

**Completed: corpus/index, Layer-1, and full-coverage Layer-2 evaluation.
The human-judgment blocker was resolved on 2026-11-16; completion details and
real scores follow below. The original Step 5 evidence is retained as history.**

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


## Corpus and index acceptance

- New manifest: `eval/corpus_manifest_20k.json`, seed **20261120**. All
  **5,000/5,000 Mini ACNs** retained; **15,000 additions** sampled from the
  remaining **42,723** reports, proportionally by year using largest-remainder
  quotas and seeded sampling. No anomaly-category filter is applied.
- **Ready build 4: 20,000 reports, 28,306 chunks, zero NULL embeddings.**
  Only 15,000 reports were processed/embedded. All **6,998 Mini chunks** retained
  their IDs, exact text hashes, and embedding hashes.
- Idempotent repeat: **20,000 skipped, zero processed, zero embedded**, same
  ready build. The check forbids embedding-provider initialization.
- Original Mini manifest, queries, human-filled judging CSV, and qrels are
  byte-for-byte unchanged. Retriever, prompt, and generation code hashes are
  unchanged. Source JSONL checksums still match the pinned HF revision.
- `eval/current_corpus.json` designates the 20k manifest. The switch and hashes
  are explicit in `eval/experiment.json`. Mini measurements are archived in
  `eval/experiment_5k.json` and `eval/results_5k.md`; a labeled 20k section is
  appended to `eval/results.md`.
- **38 tests pass**, including deterministic superset/year-quota selection,
  unchanged-vector reuse, idempotency, and rollback of failed incremental
  publication. Ruff and `git diff --check` pass.

See `docs/STEP5_VALIDATION.json` for the machine-readable checks and DATA_NOTES
for year/label distributions. The final corpus contains 75 observed exact
labels; rare source labels are eligible but not guaranteed to be sampled.

## Layer-1 development results (all 28 category queries)

Retrieval is unfiltered, with unchanged 100-chunk / 50-report candidate depths,
report-level RRF k=60, exact vector search, and deterministic ACN ties.

| Retriever | Category P@10: 5k → 20k | Delta | Hit@10: 5k → 20k |
|---|---:|---:|---:|
| lexical | 0.0893 → 0.0893 | +0.0000 | 0.2500 → 0.2500 |
| dense | 0.9036 → 0.6286 | -0.2750 | 1.0000 → 0.9643 |
| hybrid | 0.8964 → 0.6107 | -0.2857 | 1.0000 → 0.9643 |

These are category-agreement development numbers, not query-level relevance,
answerability, groundedness, or frozen final-test scores. The enlarged corpus
adds many reports outside the Mini's four category pools. A category-agreement
drop alone cannot establish a drop in judged relevance. No retrieval settings
or queries were tuned in response to these results.

Observed local retrieval p95 (31 requests, including controls; excludes model
initialization and generation): lexical **22.84 ms**, dense **170.87 ms**,
hybrid **155.17 ms**. Full samples/configuration are in the experiment record.

## Initial Layer-2 judgment coverage blocker (historical; resolved 2026-11-16)

The paragraphs below describe the initial run before Cynthia supplied the 46 missing grades; they are superseded by the completion section above.

All original qrels remain valid and every judged report remains in the corpus.
However, the new top-ten union contains **92 query/report pairs**, of which
**46 are absent from the existing qrels**. All 46 are newly added report ACNs,
not lost Mini reports. Retaining judged reports does not automatically judge
new retrieval results. The Mini spec §6 says: “Unjudged documents are not
assumed irrelevant.” Computing complete point scores or deltas by assigning
those rows zero would violate that contract.

`eval/results.md` contains the requested 20k Layer-2 comparison table, but its
20k scores and deltas are explicitly **pending judgments / N/A**, not fabricated
numbers. The 5k human-judged baseline remains reported. `experiment.json`
records `judged_relevance.status = needs_judgments` and the exact missing pairs.

| Query | Missing query/report pairs |
|---|---:|
| alt-l2-1 | 7 |
| alt-l2-2 | 4 |
| equip-l2-1 | 7 |
| equip-l2-2 | 9 |
| nmac-l2-1 | 4 |
| nmac-l2-2 | 3 |
| ri-l2-1 | 1 |
| ri-l2-2 | 11 |
| Total | 46 |

Only missing pairs are exported in `eval/judging_pool_20k_additions.csv`,
blinded and shuffled with blank grade/note fields. The complete new 92-pair
union is separately exported as `eval/judging_pool_20k.csv`. No new judgments
have been assigned, and the original Mini CSV/qrels have not been overwritten.
Human labels for the 46 additions are required to finish the full Layer-2 gate.

All three existing abstention controls were reverified against the selected and
indexed 20k corpus. Step 5 made no generation calls or generation/prompt changes.
The v1.4 §16 decisions were read; retrieval bake-offs and other later query-path
changes remain deferred to their assigned steps.
