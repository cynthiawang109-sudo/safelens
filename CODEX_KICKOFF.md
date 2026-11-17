# SafeLens Mini — Codex Kickoff Tasks

Repo: `safelens` (public). Governing documents, in order of authority:
`docs/PROJECT1_MINI_WEEKEND_SPEC.md` (v1.3, frozen) and `docs/DATA_NOTES.md`.
Work in small steps; each step below is one Codex session / one PR-sized unit.
All code, comments, and docs in English.

Environment note (learned on this machine during project #2): this is a Chinese
Windows install — Python stdio defaults to GBK and has broken tool handshakes
before. Every Python entry point must run with UTF-8 stdio
(`PYTHONUTF8=1` / `PYTHONIOENCODING=utf-8` in compose and local env), and all
file opens specify `encoding="utf-8"` explicitly.

## Step 0 — Repo scaffold (no application logic yet)

- `pyproject.toml` (Python 3.12, uv), package `safelens`, dev deps: pytest, ruff
- `.gitignore`: `.env`, `data/`, `__pycache__`, `.venv`
- `.env.example`: `DATABASE_URL`, `OPENAI_API_KEY`, `EMBEDDING_MODEL=BAAI/bge-small-en-v1.5`,
  `EMBED_QUERY_PREFIX=Represent this sentence for searching relevant passages: `,
  `LLM_MODEL=gpt-4o-mini`, `PYTHONUTF8=1`
- `AGENTS.md`: the spec's non-negotiables in one page — report-level ranking only;
  benchmark runs never use the category filter; reindex is offline and explicit;
  raw data never committed; eval queries/qrels are versioned files
- `docker-compose.yml`: single service `db`, image `pgvector/pgvector:pg16`,
  named volume, port 5432, healthcheck `pg_isready`
- `docs/`: copy in the spec (as `PROJECT1_MINI_WEEKEND_SPEC.md`) and `DATA_NOTES.md`
- `README.md` skeleton: what this is, quickstart placeholder, link to spec
- Acceptance: `docker compose up -d` healthy; `uv run pytest` runs (0 tests ok);
  `git status` shows no `data/` or `.env`

## Step 1 — Schema + ingest validation slice (1,000 reports)

- `db/migrations/0001_init.sql`: exactly the spec §5 schema (reports, chunks with
  `UNIQUE(acn, chunk_idx)`, `index_meta` with `status`), plus the GIN index on
  `chunks.tsv`; a tiny migration runner applies `db/migrations/*.sql` in order
- `safelens/config.py` + `safelens/providers.py`: config dataclass and the
  embedding/LLM provider interfaces from spec §5 (`embed_documents` /
  `embed_query` split is mandatory)
- `safelens/ingest.py`: stream the three HF JSONL files from `data/`, normalize
  per DATA_NOTES mapping (allowlist of columns; unknown/missing required columns
  fail loudly), upsert per-ACN in one transaction, skip rule = content hash match
  AND active index config match; log skipped/inserted/updated/failed
- Run on a 1,000-report slice first; verify row counts, spot-check 3 reports
  against the raw JSONL (narrative concatenation incl. Report 2 labels, month
  parsing, anomaly splitting)
- Update `docs/DATA_NOTES.md`: replace sample figures with full-corpus counts
  (run `scripts/inspect_dataset.py` on all three files)
- Acceptance: second ingest run reports all skipped, zero duplicates;
  forced-failure test (kill mid-run) leaves prior data intact

## Step 2+ — follow spec §7 order

Retrieval (lexical → dense → hybrid, spec §5 aggregation contract) → evaluation
(§6) → `/ask` + citation validation → Gradio → scale ingest to 5,000 → README.
Do not start a later step while an earlier acceptance check is red.

## Step 3 — Mini subset (5,000) + Layer-1 evaluation + judging pool

*(Issued by Sunny on 2026-11-15 after independent Step 2 verification: 1,380
chunks, build #2 ready, RRF contract audited in source, sample comparison sane.)*

- **Subset selection** per spec §4 and DATA_NOTES (the four decided categories):
  fixed seed (record it), dedupe by ACN first, documented selection order.
  Write `eval/subset_manifest.json`: selected ACNs, per-label counts, year
  distribution, multi-label overlap. Update DATA_NOTES.md subset figures with
  actuals. The active corpus becomes **the subset only** — the Step 1
  first-1,000 slice is superseded; document the mechanism used to exclude
  non-subset reports from the indexed corpus.
- **Ingest + reindex** the subset. Verify: one `ready` build whose
  `report_count` equals the subset size; every chunk embedded.
- **`eval/queries.jsonl`** per spec §6: 20 Layer-1 queries (5 per category,
  mixing plain-language, paraphrase, and jargon-heavy phrasings) + 8 Layer-2
  queries (2 per category) + the 3 abstention controls (out-of-domain;
  exact day/time the record cannot contain; a fabricated ACN — verify it is
  absent from the subset and record that check in the file or results).
- **`eval/run_eval.py`** per spec §6: benchmark runs are **unfiltered** (never
  pass a query's category as a retrieval filter); Layer-1 metrics
  (Category Precision@10, Hit@10) for lexical / dense / hybrid; full experiment
  record alongside `eval/results.md`.
- **Judging pool export**: union of the top-10 reports of all three retrievers
  for the 8 Layer-2 queries, blinded (no retriever identity) and shuffled, as
  `eval/judging_pool.csv` with columns `query_id, acn, synopsis, grade, note`
  (grade/note left empty — Cynthia fills them; do not pre-judge).
- Acceptance: `eval/results.md` contains the three-retriever Layer-1 table;
  judging pool has ≤ 240 unique (query_id, acn) rows; controls present with
  `expect: insufficient_evidence`; all prior tests still pass, plus new tests
  for subset determinism (same seed → same manifest) and unfiltered eval runs.

## Step 4 — Generation: /ask with validated citations + Gradio UI

*(Issued by Sunny on 2026-11-15 after Step 3 verification. Step 3 headline
finding to keep in mind: the lexical baseline is extremely weak on
natural-language queries — Category Precision@10 0.090 vs dense 0.895 —
because websearch_to_tsquery is conjunctive. That is recorded in
eval/results.md; do NOT retune lexical semantics in this step. A fairer
lexical variant is a flagship M3 bake-off item.)*

- `safelens/generate.py` per spec §5: grounded prompt over the hybrid top-5
  reports (≤ 2 chunks each, ≤ 8 total); passages presented as **reporter
  accounts, not confirmed findings**; the model must answer only from the
  supplied evidence or reply "insufficient evidence". Validate every cited
  ACN against the supplied documents — fabricated citations are dropped and
  the answer flagged. Return structured evidence `{acn, chunk_id, passage}`
  per citation.
- `safelens/app.py` per spec §5: `POST /ask {question, category?}` →
  `{answer, citations[], results[]}`; `GET /report/{acn}` returns exactly the
  indexed source text + provenance; `GET /health`. Response shapes are a
  stable contract for the future Next.js UI.
- Gradio UI (`ui.py` or similar): calls the FastAPI endpoints over HTTP only;
  shows answer, citations with passages, and the report-level result list.
- Smoke-test `/ask` against the 3 abstention controls from eval/queries.jsonl
  plus 2 normal Layer-2 queries; record outcomes (declined? fabricated
  citation? qualified answer?) in a short `docs/STEP4_NOTES.md`. A confident
  invented answer on any control is a failed check — fix the prompt/validation
  before reporting.
- Wire Layer-2 metrics into `eval/run_eval.py`: when `eval/qrels.jsonl`
  exists, also compute Precision@10 and MRR (grade ≥ 1 = relevant) and
  nDCG@10 (graded gains) per retriever, per query and averaged, and append to
  results.md. Do NOT create qrels.jsonl and do not fill any grades — Cynthia
  judges `eval/judging_pool.csv` herself; the metrics must simply work when
  the file appears (converting her filled CSV to qrels is part of this step:
  add a small `eval/import_judgments.py` that validates and converts it).
- Acceptance: `/ask` answers a normal query with at least one validated
  citation whose passage text matches the indexed chunk; all 3 controls
  behave (qualified refusal, no invented ACN/date); `/report/{acn}` output
  matches the DB row; prior tests still pass plus new tests for citation
  validation (fabricated ACN dropped) and the qrels metric math on a toy
  fixture.

## Step 5 — Flagship scale-up: corpus 5,000 → 20,000

*(Issued by Sunny on 2026-11-15 after Mini completion. Decisions recorded by
Cynthia the same day: the name SafeLens is confirmed; the corpus grows to
20k first; the regulations mini-corpus stays in Phase 2; the LLM provider
default — OpenAI generation/filter, local embeddings — stands.)*

- **Selection**: keep ALL 5,000 reports of the Mini subset (every eval asset —
  queries, judging pool, qrels — must stay valid). Add 15,000 reports from the
  remaining corpus, stratified proportionally by year (`Time_Date` year)
  across all anomaly categories, fixed seed recorded in the manifest, deduped
  by ACN against the existing 5,000 and within the addition.
- **Manifest**: write a NEW file `eval/corpus_manifest_20k.json` (seed,
  per-year counts, per-label counts, ACN lists or hashes, snapshot hash).
  Do NOT overwrite `eval/subset_manifest.json` — it stays as the Mini record.
  The eval runner must validate the active corpus against whichever manifest
  is designated current; record the switch explicitly in experiment.json.
- **Ingest + index** through the existing pipeline (idempotent upsert by ACN +
  content hash; only new reports should be processed). Produce a new ready
  build with report_count = 20,000 and zero NULL embeddings.
- **Re-run the full evaluation** (`eval/run_eval.py`) on the 20k corpus:
  Layer-1 (same 28 category queries) and Layer-2 (existing qrels — all pooled
  reports are retained, so judged metrics remain computable). Append a clearly
  labeled "20,000-report corpus" section to `eval/results.md` with both tables
  and the deltas against the 5,000-report numbers.
- **Do NOT change retriever code, queries, prompts, or generation in this
  step.** The point is isolating the corpus-size effect; retrieval changes
  belong to the Step 6 bake-off.
- Acceptance: DB ready build = 20,000 reports, chunks > reports, zero NULL
  embeddings; manifest confirms 5,000/5,000 original ACNs retained;
  results.md contains the 20k Layer-1 and Layer-2 tables with deltas;
  all prior tests still pass, plus a test that the 20k selection is
  deterministic (same seed → same manifest) and a superset of the 5k subset.

## Step 6 — Lexical bake-off (flagship M3, part 1)

*(Issued by Sunny on 2026-11-15 after Step 5 verification. Context: at both 5k
and 20k, the current lexical leg — `websearch_to_tsquery` conjunctive FTS —
scores ~0.09 Layer-1 and ~0.05 judged P@10 because natural-language queries
underfill. Dense is strong (20k Layer-1 0.629 category P@10). Hybrid is
dragged toward dense-minus-noise. This step finds a lexical leg worth fusing.
Spec v1.4 gates apply: development/validation queries only; the frozen final
test set does not exist yet and nothing here touches it; no anomaly label may
be used as a retrieval feature (text-only); unjudged documents are never
assumed irrelevant.)*

Evaluate these lexical variants, each behind the existing retriever interface
and the SAME candidate contract (100 candidate chunks → fold by ACN → 50
candidate reports; report-level outputs only):

1. `lexical-fts-and` — the current implementation (baseline; already measured,
   re-measure in this harness for comparability).
2. `lexical-fts-or` — OR semantics: build a tsquery from the query's content
   terms joined with `|`, rank with `ts_rank_cd` over the existing
   'simple'-config tsvector/GIN index. No schema change.
3. `lexical-bm25-ref` — a true-BM25 reference implementation (e.g. `rank_bm25`)
   run offline over the same chunk texts, eval-only. This sizes the prize of a
   real BM25 leg without touching the production stack. (A `pg_search`
   production integration is OUT of scope here; it is reconsidered only if
   BM25 wins decisively.)

For each variant, and for **hybrid with each variant as its lexical leg**
(dense leg unchanged, report-level RRF k=60 unchanged), report on the
20,000-report corpus:
- Layer-1 (primary selection metric): Category Precision@10 and Hit@10 over
  all 28 category queries, per retriever, plus per-query rows.
- Latency: mean and p95 per query, same protocol as prior steps.
- Layer-2 (secondary, coverage-reported): judged P@10 / MRR / nDCG@10 computed
  ONLY over (query, ACN) pairs present in qrels, with the judged-coverage
  percentage of each top-10 printed alongside. Never zero-fill unjudged pairs;
  label these numbers "partial-coverage development signals", not scores.

Deliverables:
- A bake-off table in a new `docs/STEP6_NOTES.md` and a labeled section in
  `eval/results.md`, with a clear recommendation: which lexical leg the
  flagship should adopt, and whether hybrid-with-winner beats dense alone on
  the primary metric.
- For the winning configuration only, export its unjudged top-10 pairs to
  `eval/judging_pool_step6_additions.csv` (blinded, shuffled, blank grades) so
  Cynthia can judge them later and complete Layer-2 for the winner.
- Do NOT change the production default lexical implementation, the queries,
  the corpus, or any generation code in this step. Adopting the winner is a
  separate change after Cynthia's decision.
- Acceptance: all variants run under the identical candidate contract
  (auditable in code); Layer-1 table complete for 3 lexical variants + 3
  hybrid combinations + dense reference; coverage percentages printed for
  every Layer-2 number; prior tests still pass plus new tests for the OR
  tsquery builder (stopword/empty-query edge cases) and the coverage
  computation.

## Step 6B — Fusion-weight mini bake-off (dense + BM25)

*(Issued by Sunny on 2026-11-16, at Cynthia's decision to test fusion weights
before settling the retrieval default. Context: Step 6 found BM25 the best
lexical leg (Layer-1 Category P@10 0.5714) but equal-weight RRF hybrid-BM25
(0.5786) still lost to dense alone (0.6286). Question for this step: can a
dense-heavy weighting make fusion beat dense alone? Spec v1.4 gates apply:
development queries only, text-only features, unjudged never assumed
irrelevant, no production default change in this step.)*

Method:
- Legs: dense and lexical-bm25-ref exactly as measured in Step 6. Reuse the
  saved Step 6 rankings (`data/eval_rankings_step6.json`) if present so the
  sweep is pure re-ranking; otherwise re-run the two legs once and cache the
  rankings. Candidate contract unchanged (100 chunks → fold by ACN → 50
  reports per leg).
- Fusion families:
  1. **Weighted RRF**: score = w_d/(60 + rank_d) + w_l/(60 + rank_l), k fixed
     at 60, report-level, ACN tie-break.
  2. **Normalized score fusion (CombSUM-style)**: per-query min-max normalize
     each leg's report scores to [0, 1], combine with the same weights.
- **Pre-registered weight grid** (dense:lexical): 1:0 (dense-only reference),
  10:1, 5:1, 3:1, 2:1, 1:1, 1:2, 0:1 (BM25-only reference). No additional
  weights may be tried after seeing results; if a boundary of the grid wins,
  report that fact instead of extending the grid.
- Selection rule (fixed in advance): highest Layer-1 Category P@10 wins;
  tie-break by Hit@10, then by the SMALLER lexical weight.

Reporting (all in `docs/STEP6B_NOTES.md` plus a labeled section in
`eval/results.md` and a versioned `eval/experiment_step6b.json`):
- The FULL grid table for both families: Category P@10, Hit@10 per weight.
  No cherry-picking the winner row alone.
- For the best configuration: per-query win/loss/tie count vs dense-only on
  Category P@10, and the margin. State plainly if the win rests on one or two
  queries flipping.
- Layer-2 partial-coverage signals (same protocol and caveats as Step 6:
  judged pairs only, coverage % printed, never zero-filled, not for
  selection) for the best configuration and for dense, using the qrels file
  as it exists at run time.
- A recommendation: adopt a fusion configuration as the flagship default, or
  keep dense-only — with the numbers behind it. Adoption itself is a separate
  change after Cynthia's decision; this step changes no defaults and no
  production code paths (experiment code only, like Step 6).

Acceptance: both families × full grid reported; weighted-RRF unit tests
(1:1 reduces to the Step 6 hybrid ranking; lexical weight 0 reproduces the
dense ranking exactly); prior tests still pass; protected assets (queries,
qrels, manifests, production retrieval/generation) unchanged by hash.

## Step 7 — Adopt weighted-RRF 10:1 as default + LangGraph agentic layer (flagship M4)

*(Issued by Sunny on 2026-11-16. Cynthia's decision: adopt weighted RRF
10:1 (dense:BM25) as the flagship retrieval default. Step 6B caveat stands:
the margin over dense is fragile on the development set; the Part 3 ablation
re-tests it on judged data. Spec v1.4 gates apply throughout.)*

### Part 1 — Productionize the adopted default

- Implement BM25 as a production lexical leg behind the existing retriever
  interface (same preprocessing and BM25Okapi parameters as the Step 6
  reference). In-memory index over the ready build's chunk texts, built once
  per index build id and invalidated when the ready build changes; measure
  and report index build time and memory.
- Production hybrid = weighted RRF, weights dense 10 : BM25 1, k=60,
  report-level, ACN tie-break. Weights live in configuration. The legacy FTS
  leg stays available as a config option (documented baseline); the default
  hybrid no longer uses it. Dense-only remains selectable.
- Equivalence gate: on the 31 development queries, production hybrid-10:1
  top-10 ACN orders must match the Step 6B best-configuration rankings.
  Rerun `eval/run_eval.py`: Layer-1 hybrid must read 0.6429 (rounding aside).
  For Layer-2, the new hybrid's top-10s contain a few pairs absent from
  qrels — export exactly those to `eval/judging_pool_step7_additions.csv`
  (blinded, blank) and mark the hybrid Layer-2 row pending those judgments.
  Never zero-fill. The dense and lexical rows must be unchanged.

### Part 2 — Agentic layer (LangGraph)

Graph over the Part 1 retriever, preserving every existing generation rule
(citation validation fail-closed, reporter-account framing, per-report and
total chunk caps):
1. **Retrieve** with the production default.
2. **Grade**: an LLM grader scores the retrieved reports for relevance and
   sufficiency against the question (structured output; grades recorded in
   the trace).
3. **Rewrite loop**: if evidence is insufficient and retries remain (max 2),
   rewrite the query (one distinct strategy per retry — e.g. term-focused,
   then synonym/expansion) and re-retrieve. Each attempt is graded.
4. **Generate or abstain**: answer with validated citations, or abstain.
   `/ask` responses carry the v1.4 status field:
   `answered | partial | insufficient_evidence`.
5. **Aggregate routing**: count-style questions ("how many reports…") route
   to an auditable SQL count over report metadata (year and anomaly-category
   filters) that reports its filters and denominator; the LLM never counts.
   If the question's filters cannot be mapped, fall back to the normal path
   and mark the answer `partial`.
- The trace is part of the API response: stages executed, queries tried,
  grades, retries, and per-stage token/latency cost (v1.4: advanced stages
  are conditional, capped, and costed individually).
- The three abstention controls must pass through the full agentic path.
- Gradio calls the same HTTP API; no logic duplication.

### Part 3 — Ablation (v1.4 P2)

Configurations: **Dense-only**, **Hybrid-10:1**, **Hybrid + Rerank**
(cross-encoder reranker, local model, over fused candidates, as a config
flag), **Hybrid + Rewrite** (agentic loop without rerank), **Full Agentic**
(rerank + rewrite + grading). Run over the 8 judged queries + 3 controls and
report per configuration: judged retrieval metrics where coverage allows
(coverage printed; new pairs exported, never zero-filled), abstention
correctness on the 3 controls, mean retries, mean per-question cost
(tokens and latency). Table in `docs/STEP7_NOTES.md` and `eval/results.md`,
with a plain statement of what each added stage buys and costs.

Acceptance: Part 1 equivalence gate passes and run_eval reproduces the
expected Layer-1; Part 2 controls pass end-to-end and traces are complete;
Part 3 table complete for all five configurations; prior tests pass plus new
tests for the weighted-RRF production path (1:1 equals legacy equal-weight
behavior on a fixture; lexical weight 0 equals dense), the BM25 index
build-id invalidation, the rewrite cap, and the aggregate SQL routing.
No final-test queries are created in this step; no Step 8 work.

## Step 7B — Answer-rate calibration (diagnose first, then calibrate)

*(Issued by Sunny on 2026-11-16, at Cynthia's decision. Context: the Step 7
ablation showed all five configurations answering 0 of 8 answerable judged
queries while refusing all 3 controls correctly. Retrieval is not the
bottleneck (judged P@10 0.95). Note that the no-grader configurations
(Dense-only, Hybrid-10:1) also refused 8/8, so the generator's own evidence
bar is a prime suspect. Spec v1.4 gates apply; the hard rules below are not
calibration variables.)*

### Phase 1 — Diagnosis (no behavior changes)

For each of the 8 judged queries and 3 controls, on the production Ask path
and from the Step 7 ablation record, classify where each answerable query
died:
(a) grader marked evidence insufficient although judged-relevant reports
    (grade ≥ 1 in qrels) were in the retrieved set;
(b) grader marked sufficient but the generator still refused;
(c) evidence packaging: the 5-report / 8-passage cap dropped the passages
    that carry the relevant mechanism;
(d) the rewrite loop's final attempt was worse than the first retrieval;
(e) citation validation stripped an otherwise grounded answer.
Deliverable: a per-query diagnosis table in `docs/STEP7B_NOTES.md`, each row
citing the trace evidence for its classification.

### Phase 2 — Calibration (only the levers the diagnosis implicates)

Permitted levers, mechanism-level only (no per-query rules or thresholds
keyed to specific query IDs):
- Generation prompt: make the three-way outcome explicit — answer what the
  evidence supports with qualifications (`answered` / `partial`) instead of
  defaulting to refusal; a partial answer grounded in retrieved reports is a
  success, not a failure.
- Grader sufficiency definition: sufficient = at least one relevant report
  whose passages address the question's mechanism (per the v1.4
  relevance / answerability / groundedness definitions), not complete
  coverage of the topic.
- Evidence packaging: guarantee the generator receives each selected
  report's synopsis plus its highest-ranked passages.
Hard rules that must NOT be weakened: citation validation stays fail-closed;
no claims beyond the supplied passages; reporter-account framing; controls
must still refuse; retrieval defaults unchanged.

### Phase 3 — Re-measure (pre-registered success criteria)

Same 11 requests through (i) the production Ask path, (ii) Dense-only,
(iii) Hybrid-10:1. Report a before/after status table per query per
configuration, citation precision against qrels for answered/partial
responses, and cost deltas. Success = controls still 3/3
`insufficient_evidence` with zero invented citations AND at least 6 of 8
answerable queries reach `answered` or `partial` with validated citations
on the production path AND no answered/partial response cites a grade-0
report as support. If the criteria are not met after the implicated levers,
stop and report the diagnosis and what was tried — do not keep loosening.

Deliverables: `docs/STEP7B_NOTES.md` (diagnosis + changes + before/after
tables), a labeled section in `eval/results.md`, versioned experiment record.
Prior tests must pass, plus new tests pinning any prompt/grader behavior
changed. The 82 ablation additions stay unjudged in this step; no Step 8
work; no final-test queries.

## Step 7C — Freeze the final test set (construction only; no evaluation run)

*(Issued by Sunny on 2026-11-16, at Cynthia's decision. Per spec v1.4 §16
P0-3: the final test is authored AFTER the design freeze — retrieval default
(weighted RRF 10:1), the agentic workflow, and the Step 7B calibration are
all final. This step only CONSTRUCTS and freezes the test. Nobody runs the
system against these queries for scoring in this step, and no parameter,
prompt, or threshold may change because of anything seen here.)*

### The frozen queries

Create `eval/queries_final.jsonl` with exactly these 12 queries (verbatim
wording; fields: id, layer="final", kind, question):

Mechanism queries (kind="mechanism"):
- ft-ri-1: "A flight crew crossed a runway without clearance after accepting a taxi instruction that was meant for another aircraft with a similar call sign. Describe what happened in reports like this."
- ft-ri-2: "In blowing snow, a crew taxied past a runway hold line because the surface markings and signs were obscured. What do reports like this describe?"
- ft-alt-1: "A crew descended below a published crossing restriction because the FMS was programmed with the wrong arrival procedure. Describe what happened in reports like this."
- ft-alt-2: "After a late runway change, a crew flew the wrong departure profile and climbed through their assigned altitude. What do reports like this describe?"
- ft-nmac-1: "Two aircraft on converging courses at the same altitude received no warning from ATC until a pilot spotted the traffic visually at the last moment. Describe what happened in reports like this."
- ft-nmac-2: "A drone passed close to an airliner on final approach and the crew went around. What do reports like this describe?"
- ft-eq-1: "Smoke in the cockpit traced to an overheating galley oven led a crew to declare an emergency and land at the nearest suitable airport. Describe what happened in reports like this."
- ft-eq-2: "After extension, a landing gear indication showed unsafe and the crew made a low pass so the gear could be checked visually before landing. What do reports like this describe?"

Controls (kind="control"):
- ft-ctl-1: "Describe the runway incursion that occurred at Denver International on the morning of October 9, 2017, including the exact time it happened."
- ft-ctl-2: "Summarize the events in ASRS report ACN 777777777777777 involving a cargo aircraft."

Aggregate counts (kind="count"):
- ft-cnt-1: "How many reports in the corpus involve NMAC conflicts in 2019?"
- ft-cnt-2: "How many reports in the corpus are from 2015?"

### Construction tasks

1. Verify ft-ctl-2's ACN does not exist in the corpus; if it ever did,
   stop and report instead of substituting silently. Compute the two count
   answers with the production aggregate SQL path and store them, sealed,
   in the experiment record as ground truth.
2. Build the judging pool for the 8 mechanism queries only: union of the
   top-10 report pairs from dense and from production hybrid-10:1 on the
   20,000-report corpus, blinded, shuffled, blank grades/notes, exported to
   `eval/judging_pool_final.csv`. Report the pool size and per-query counts.
3. Do NOT run the production Ask path (or any generation) on any final
   query in this step. Do NOT grade any pool row. Do NOT touch the
   development queries, qrels, or any production code.
4. Write `docs/FINAL_TEST_FREEZE.md`: freeze date, the SHA-256 of
   `eval/queries_final.jsonl`, pool statistics, and the freeze rules —
   Cynthia judges the pool once; exactly one evaluation run follows
   (Step 7D); any change to retrieval, generation, or grader code after
   this freeze must be disclosed alongside any later re-run.
5. Acceptance: queries file matches the wording above byte-for-byte;
   fake ACN verified absent; count ground truths recorded; pool exported
   with all grades blank; freeze doc written; all prior tests still pass.
