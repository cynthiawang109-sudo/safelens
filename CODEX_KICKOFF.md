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
