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
