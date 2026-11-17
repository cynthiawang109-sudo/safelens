# Final test freeze — Step 7C

Freeze date: **2026-11-16 (America/New_York)**. UTC construction timestamp: 2026-11-17T01:58:47.306421+00:00.

This is **construction only**. Evaluation runs: **0**. Final-query Ask/generation calls: **0**. No final pool row has been graded. No prompt, threshold, production code, or retrieval setting was changed.

## Frozen artifacts

- `eval/queries_final.jsonl`: SHA-256 `2160adf50cb818fce182c8c431e1005587acecd63261005241bef3a90a4ec2de`.
- Original blank `eval/judging_pool_final.csv`: SHA-256 `6bce74c3b2944df18c0361fb39fcef35827720aa5c743166d56d6ceb70a6ab7f`.
- Pool identity (sorted query/ACN/synopsis tuples, excluding grade/note): SHA-256 `d0ddb3dcb8d26c938064856f477cf2b864d343f7335f4d9e5c5f9c661080321c`.
- `eval/experiment_final_freeze.json`: SHA-256 `a61e9a107b28f2d97548a9e007dc2f87ee19b1e9156ae3353b32ffbdd5583e53`.

The JSONL contains exactly the twelve supplied queries, with fields `id`, `layer=final`, `kind`, and `question`, in kickoff order. Question text is copied verbatim from CODEX_KICKOFF.md and checked byte-for-byte. Encoding is UTF-8 without BOM, LF newlines, final newline. There are eight mechanism queries, two controls, and two counts.

## Corpus and construction checks

Active corpus: **20,000 reports**, **28,306 embedded chunks**, ready build **4**. Snapshot SHA-256 `c47c73dae040d26dba7221e50c6cbeb457859632f6ef385e7fdf338b03db850b`. The active identity set and snapshot match `eval/corpus_manifest_20k.json`.

The exact fabricated ACN for `ft-ctl-2` was checked against the indexed report table and selected ACN manifest and is absent. Construction would stop if it existed; no substitution is permitted. The other control was not submitted to retrieval or Ask during construction.

Both count answers were computed directly by the production `safelens.aggregate.execute_count` SQL executor, with explicit metadata filters bound from the fixed questions. This is ground-truth construction, not a test of natural-language routing. The record stores the SQL, parameters, filters, count, and corpus denominator under `sealed_ground_truth`, with a canonical payload hash. These frozen answers are not printed here and were not submitted to Ask. The seal is an integrity freeze, not encryption; do not use the answers to tune the system.

## Blinded mechanism judging pool

Only the eight mechanism questions were sent to dense retrieval and the frozen production hybrid (dense:BM25 10:1, report-level RRF k=60). Each leg uses 100 candidate chunks, max-score folding by ACN, then 50 candidate reports; pooling uses the returned top ten. No category filter, generation, grader, rewrite, reranker, evaluation metric, or relevance label was used. Both retrievers returned ten distinct reports per query.

The union contains **89 unique (query_id, ACN) pairs**, shuffled with seed **20261118**. CSV columns are exactly `query_id,acn,synopsis,grade,note`; all grade/note fields are blank. It hides retriever identity, ranks, and scores. The separate construction provenance remains in ignored `data/`; Cynthia should not consult retrieval provenance while judging.

| Mechanism query | Unique report pairs |
|---|---:|
| ft-ri-1 | 10 |
| ft-ri-2 | 11 |
| ft-alt-1 | 12 |
| ft-alt-2 | 11 |
| ft-nmac-1 | 10 |
| ft-nmac-2 | 12 |
| ft-eq-1 | 11 |
| ft-eq-2 | 12 |
| Total | 89 |

## Freeze rules and handoff

1. Cynthia judges the mechanism pool **once**, blind to proposing retrievers: 2=directly relevant, 1=partially relevant, 0=irrelevant. Read synopsis first and consult the indexed full narrative when needed. Reporter accounts are unverified; judge relevance to the exact question. Edit only grade/note; retain the frozen query/ACN identities and synopsis text. The initial blank-sheet hash changes when grades are filled; the pool identity hash must remain stable. Never copy development qrels onto different final questions.
2. No system may be run for scoring, generation, answer inspection, or tuning against these final questions during Step 7C. The sixteen retrieval calls above are solely for the expressly authorized pool construction, and the two SQL calls solely for sealed count truth. No result metrics or final answers were generated.
3. After human judgments are complete, **exactly one final evaluation run follows in Step 7D**. Do not run it now, repeatedly inspect scores, expand the pool opportunistically, or tune prompts/parameters against this set. Keep all development artifacts separate.
4. The experiment record seals all production Python/migration/dependency hashes and the public runtime configuration, including retrieval, generation, grader, model revisions, budgets, and calibrated prompts. Any retrieval/generation/grader code or configuration change after this freeze must be disclosed alongside any later re-run, with both source/config versions and the reason. Never silently overwrite or replace this test.
5. The construction command refuses to overwrite any final artifact. Verify the query hash and pool identities before importing judgments or running Step 7D. No final qrels are created until Cynthia supplies human grades.

Production source, development queries/qrels, corpus manifests, and historical results were checked unchanged by hash. The experiment records the construction-only checks. Prior tests run separately on their synthetic/development fixtures; they do not run this final test. Step 7D and Step 8 have not started.

## Acceptance verification

- `uv run pytest -q`: **57 passed**. These are prior synthetic/development tests; no final-test evaluation was run.
- `uv run ruff check .` and `git diff --check`: passed.
- Exact twelve-query wording/canonical bytes, query and record hashes, the exact 89-pair dense/hybrid union, pool identities, all blank grades/notes, the fake-ACN absence check, and both sealed SQL ground-truth hashes were independently verified.
- Production files and development queries/qrels/results remain unchanged by their recorded SHA-256 hashes.
- `.gitattributes` disables Git text/EOL conversion for the three sealed JSONL/CSV/JSON data files so Windows checkout settings cannot alter their frozen bytes.

Construction helper: `eval/freeze_final_set.py --freeze-date 2026-11-16` (invoke through `uv run python` with UTF-8 environment variables). It refuses to overwrite these existing artifacts; do not reconstruct or refresh the pool. This helper contains no Ask, generator, grading, or evaluation invocation.
