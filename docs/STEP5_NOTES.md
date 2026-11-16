# Step 5 — 20,000-report scale-up

**Corpus/index and Layer-1 evaluation completed. Full Layer-2 acceptance is
pending 46 additional human judgments. No Step 6 work was started.**

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

## Layer-2 judgment coverage blocker

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
