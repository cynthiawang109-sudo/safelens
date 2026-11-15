# Step 2 validation

The 1,000-report Step 1 slice is now indexed as **1,380 chunks** with local
`BAAI/bge-small-en-v1.5` embeddings (384 dimensions). See
[STEP2_VALIDATION.json](STEP2_VALIDATION.json) for the pinned model revision,
active build, configuration, token statistics, and report-level sample rankings.

The real-index validation checks token budgets including synopsis and special
tokens, synopsis repetition, chunk metadata, vector dimensions, unique ACNs in
results, and deterministic repeat queries. Nonfinal chunks have at least 400
tokens; short reports/final tails can be smaller. The effective target is 500
tokens, within the model's 512-token input limit. Overlap is 15% of each previous
narrative token window, in addition to the repeated synopsis.

Sample query: **TCAS RA**, no category filter, 100 candidate chunks per
retriever → collapse by best chunk score → 50 candidate reports per retriever
→ hybrid report-level RRF with k=60. Doubling chunk candidates to 200 did not
change any of the three top-five lists for this query. This is a smoke check,
not a relevance benchmark or a corpus-wide candidate-starvation conclusion.

| Rank | PostgreSQL FTS ACN | Dense ACN | Hybrid ACN |
|---|---|---|---|
| 1 | 1122787 | 998938 | 1122787 |
| 2 | 1467950 | 1840188 | 1840188 |
| 3 | 1289481 | 1866809 | 1289481 |
| 4 | 1694805 | 1348828 | 998938 |
| 5 | 1307058 | 1004278 | 1866809 |

Scores, winning chunk IDs, and component ranks are in the validation JSON.
Full passages remain in gitignored `data/step2_sample_results.json`.

Post-index re-ingestion: **1,000 skipped**, zero inserts/updates/failures.
The **19 passing tests** cover source normalization, per-report atomic writes,
process-kill rollback, chunk coverage/overlap, query instruction handling,
chunk-to-report aggregation, report-level RRF, deterministic ties, category
filtering, candidate caps, active-config mismatch rejection, offline serving
locks, dimension-changing index replacement, and failed-build rollback.
Ruff passes.

The initial unbatched build was deliberately terminated before publication.
Its abandoned `building` row was recovered as `failed` by the next explicit
build; no partial chunks were published. Build 2 completed as the single ready
index. Rebuild tests also verify superseding a prior ready index and preserving
the prior chunks/dimension on failure. Source reports were not changed.

Evaluation, generation, UI, and scaling to ~5,000 reports remain unstarted.
