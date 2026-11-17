# SafeLens

[![PR gate](https://github.com/cynthiawang109-sudo/safelens/actions/workflows/pr.yml/badge.svg)](https://github.com/cynthiawang109-sudo/safelens/actions/workflows/pr.yml)
[![Development evaluation](https://github.com/cynthiawang109-sudo/safelens/actions/workflows/eval.yml/badge.svg)](https://github.com/cynthiawang109-sudo/safelens/actions/workflows/eval.yml)

CI gates and cloud deployment configuration are ready. See
[deployment instructions and required operator decisions](docs/DEPLOYMENT.md)
and [Step 9 evidence](docs/STEP9_NOTES.md). No live cloud deployment has been
performed. The frozen final evaluation is never run by CI.
The hosted retrieval/SQL gates pass; hosted Ask awaits the `OPENAI_API_KEY`
repository secret. The full local development smoke passes.

SafeLens retrieves NASA ASRS aviation reporter accounts and generates grounded
answers with validated citations. Production retrieval uses local BGE embeddings
and BM25 with report-level weighted RRF (dense:BM25 10:1, k=60). A bounded
LangGraph workflow grades evidence, conditionally rewrites the query, and answers
or abstains; metadata count questions use auditable SQL.

## Run the full stack

With the existing indexed database and `data/models` cache from the offline
ingest/reindex steps, start PostgreSQL, the unchanged FastAPI service and the
Next.js frontend together:

```powershell
# Set OPENAI_API_KEY in your shell, or in the gitignored .env (see .env.example).
docker compose up -d --build
```

Open http://localhost:3000 for Ask, source reports and the evaluation lab.
The API is at http://localhost:8000. Stop any standalone servers using these
ports before starting Compose. A fresh database still requires the documented
offline migration/ingest/reindex steps; containers never silently rebuild the
frozen index. Gradio remains the internal prototype and is unchanged.

For frontend development against a running API:

```powershell
cd web
npm ci
# Optional: copy .env.example to .env.local and adjust the API base URL.
npm run dev
```

`NEXT_PUBLIC_API_BASE_URL` defaults to `http://localhost:8000`; Compose uses
`http://api:8000`. Next.js forwards the existing HTTP endpoints through a
same-origin frontend route because the frozen API has no browser CORS policy.
No API key belongs in frontend environment variables. `npm run build` regenerates
the sanitized evaluation snapshot from committed records; `npm start` serves
the production build. See [Step 8 validation](docs/STEP8_NOTES.md) for smoke
commands, recorded statuses and screenshots.

Current corpus: **20,000 reports**, retaining every Mini report. Step 5 indexing,
Layer-1 evaluation, and full-coverage Layer-2 evaluation pass after importing
46 additional human judgments (134 total qrels). See [Step 5 notes](docs/STEP5_NOTES.md).
The production fusion matches the Step 6B winner on all 31 development queries;
all-28 Category P@10 is 0.6429. Its five unjudged top-ten pairs remain pending
human grades. See [Step 7 notes](docs/STEP7_NOTES.md) for the full adoption gate,
real-provider agent smoke checks, and five-configuration ablation. Step 8 adds
the Next.js Ask, source-report and evaluation views, with the frozen final-test
results displayed from committed records. Earlier experiments remain historical
development records. See [Step 8 notes](docs/STEP8_NOTES.md).

Step 7B calibrated mechanism-level grading and explicit generation outcomes:
the production Ask path now returns supported `answered`/`partial` responses
for 8/8 existing normal development queries, versus 1/8 before, while all three
controls still refuse. No known grade-0 reports are cited as support. Citation
precision on judged citations is 100% at 81.25% production judgment coverage;
three cited pairs remain unjudged. Retrieval, fail-closed citation validation,
and evidence packaging are unchanged. See [Step 7B notes](docs/STEP7B_NOTES.md)
for diagnosis, all three before/after configurations, and measured cost deltas.

## Production retrieval and Ask configuration

The BM25Okapi index uses the Step 6 preprocessing and parameters (lowercase
ASCII alphanumeric content terms, fixed sklearn English stoplist; k1=1.5,
b=0.75, epsilon=0.25). It loads ready-build chunk text once per database/schema
and invalidates on a new ready build ID. The initial cold build measured 5.90 s
with about 381 MiB process RSS growth; allocator-dependent memory figures and
the initial and repeated measurements are in `eval/experiment_step7_part1.json`. The vector index
and corpus are unchanged; no re-embedding is needed for fusion-weight changes.

| Setting | Default | Alternatives |
|---|---|---|
| `LEXICAL_BACKEND` | `bm25` | `fts` retains conjunctive PostgreSQL FTS |
| `RETRIEVAL_MODE` | `hybrid` | `dense` selects dense-only |
| `RRF_DENSE_WEIGHT` / `RRF_LEXICAL_WEIGHT` | `10` / `1` | `1` / `1` reproduces equal-weight fusion |
| `AGENT_ENABLED` | `true` | `false` bypasses grading/rewrite while retaining citation validation and count routing |
| `AGENT_MAX_RETRIES` / `AGENT_MAX_CALLS` | `2` / `6` | Lower caps allowed; calls count provider LLM requests, with SDK retries disabled |
| `RERANK_ENABLED` | `false` | `true` enables the pinned local cross-encoder over up to 50 fused reports |

For the historical hybrid baseline, set `LEXICAL_BACKEND=fts` and both weights
to 1. The evaluator keeps its standalone lexical row explicitly labeled as
the legacy FTS baseline so that old lexical/dense scores remain comparable.
Production standalone lexical search uses BM25 by default.

`POST /ask` retains `answer`, `citations`, `results`, and citation validation,
and adds `status` (`answered`, `partial`, `insufficient_evidence`), `trace`,
`usage`, and optional `aggregate`. Trace events include query attempts,
structured relevance/sufficiency grades, retry strategy, actual provider
tokens, and stage latency. Rewrites occur only after an insufficient/partial
grade, use distinct term-focused and synonym strategies, and stop after two
retries. Three retrieval attempts also bound local embedding/rerank stages;
these local stages report latency rather than LLM tokens.

Evidence remains at most five reports, two passages per report, eight passages
total. Citations fail closed against the actual supplied passages. The graph
does not turn LLM relevance grades into human qrels or claims of confirmed
findings. Gradio uses this same HTTP contract and displays status and traces.

Count routing supports the four published anomaly-category labels/aliases and
single-year, since/after, before/until, and inclusive year-range filters.
Unrecognized filters use the normal evidence path with `partial` status and
no estimated count. Mapped answers show the parameterized SQL, filters, count,
and full indexed-corpus denominator. ASRS report counts are not incident rates.

Reproduce each Step 7 part with UTF-8 variables set:

```powershell
uv run python eval/run_eval.py
uv run python scripts/smoke_step7.py
uv run python eval/run_agent_ablation.py
uv run pytest -q
```

The ablation is a development experiment, not a final test. New unjudged pairs
are exported blind with blank grades; strict relevance scores remain pending
where coverage is incomplete. The local reranker is
`cross-encoder/ms-marco-MiniLM-L6-v2` at revision
`233902d25c440f23af6f7d6e94d2946bac0bee0a`, downloaded into ignored model caches.

## Scaffold quickstart

Prerequisites: Docker Compose and uv. The project uses Python 3.12.
In PowerShell:

```powershell
Copy-Item .env.example .env
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
uv sync
docker compose up -d
docker compose ps
uv run pytest
```

The database listens on localhost:5432 and persists in a named Docker volume.
The example database credentials are for local development. PostgreSQL must be
running for integration tests; each test uses and cleans up its own schema.
Keep raw downloads and intermediate data under gitignored `data/`.

## Step 1 validation

Historical first-1,000 validation on a fresh database, before subset replacement:

After setting the UTF-8 variables above:

```powershell
uv run python scripts/download_dataset.py
uv run python -m safelens.migrate
$splits = @(
  "data/asrs-aviation-reports-train.jsonl",
  "data/asrs-aviation-reports-validation.jsonl",
  "data/asrs-aviation-reports-test.jsonl"
)
uv run python scripts/inspect_dataset.py @splits
uv run python -m safelens.ingest @splits --limit 1000
uv run python -m safelens.ingest @splits --limit 1000
uv run python scripts/validate_ingest.py
uv run pytest
uv run ruff check src scripts tests
```

The download is pinned to the revision and SHA-256s in the data notes. On an
empty database, the first import inserts 1,000 and the second skips all 1,000.
`validate_ingest.py` verifies all source rows, the existing 1,000-report slice,
three source spot checks, and the repeat-run counts; it writes aggregate
evidence to `docs/STEP1_VALIDATION.json`. It expects exactly the validation slice.

Reports are committed per ACN. Hashing includes normalized content and pinned
provenance. `ingest_state` additionally records the configuration and report-only
stage, so configuration changes cannot be silently skipped. After indexing,
unchanged reports still skip when the active configuration matches; the
report-only CLI rejects changes that would invalidate existing chunks.
`validate_ingest.py` records Step 1 evidence and expects the report-only state;
run it before the first index build. Tests also cover atomic chunk replacement.

The database URL uses `127.0.0.1` to avoid this Windows machine's slow IPv6
localhost connection fallback. The initial vector column is 384-dimensional;
changing model dimension will require an explicit offline schema/index rebuild.

## Step 2 indexing and retrieval

Historical first-1,000 smoke check; `validate_retrieval.py` expects that slice.
Use the Step 3 evaluator/acceptance checker for the active 5,000-report corpus.

```powershell
uv run python -m safelens.cli reindex --model BAAI/bge-small-en-v1.5
uv run python -m safelens.cli search "TCAS RA" --method all -k 5
uv run python scripts/validate_retrieval.py
```

The model and tokenizer are pinned by `EMBEDDING_REVISION` and cached in ignored
`data/models/`. Embeddings run locally on CPU; documents receive no instruction,
queries receive exactly `EMBED_QUERY_PREFIX`, and vectors are normalized.
`EMBEDDING_THREADS` and `EMBEDDING_BATCH_SIZE` control CPU batching.

Chunking preserves source spelling and paragraph boundaries where possible,
targets 500 tokens including the repeated synopsis and model special tokens,
and overlaps 15% of narrative-window tokens. Short reports/final tails can be
below 400. The effective ceiling is the lower of the 400–600 configured target
and the model's input limit (512 for BGE). Oversized synopses/queries fail rather
than being silently truncated. The exact policy is stored in `chunk_config`.

Reindex holds an exclusive advisory lock throughout the offline build.
Retrieval refuses requests during that period, and ingestion is serialized.
New chunks are staged; only a validated full build atomically replaces chunks
and changes `building` to `ready`, superseding the previous build. Failure
preserves the old index and records `failed`. A killed process leaves `building`;
the next explicit reindex marks that abandoned build failed before retrying.
The dimension change, if needed, is part of the same atomic swap. To change
model, supply its `--revision` and matching `--dimension`, then update env to
match before serving. Every retrieval checks the active model, dimension,
revision, query prefix, and chunk configuration.

Lexical retrieval uses PostgreSQL FTS (`simple`, `websearch_to_tsquery`,
`ts_rank_cd`); dense uses exact cosine similarity without an ANN index. Each
fetches 100 chunk hits, collapses to the best chunk per ACN, and keeps 50 reports.
Hybrid applies RRF with k=60 to those report rankings. Score ties break by ACN;
equal-score chunks of one report break by chunk ID. Results retain each
component's rank and winning chunk/text. Hybrid's representative passage comes
from its better-ranked component, with lexical winning equal component ranks.

Category filtering is optional and defaults off. Benchmark labels must never be
passed as filters. `validate_retrieval.py` runs unfiltered and records smoke
results and a 100-versus-200 candidate-chunk check in
`docs/STEP2_VALIDATION.json`; full source passages stay in
`data/step2_sample_results.json`. These samples are not benchmark relevance
scores or p95 measurements. Evaluation remains the next step.

## Step 3 subset, category agreement, and judging pool

```powershell
uv run python -m safelens.subset
uv run python -m safelens.cli reindex --subset-manifest eval/subset_manifest.json
uv run python eval/run_eval.py
uv run python scripts/validate_step3.py
uv run pytest
uv run ruff check src scripts tests eval
```

The default selection seed is 20261115. The manifest versions 5,000 selected
ACNs, counts, overlaps, years, source revision, and the normalized content hash.
The subset reindex stages reports/chunks and atomically replaces the previous
corpus; non-subset reports are removed from both source and chunk tables.
CPU embedding can take substantial time on this machine. Failure preserves
the prior corpus/index, and retrieval is offline during the build.

The query file has 20 dedicated Layer-1 queries, eight separate Layer-2 pool
queries, and three verified absence controls. Retrieval never receives their
category labels as filters. `eval/results.md` reports category agreement for
the primary 20 and all 28 category queries; `eval/experiment.json` records the
full reproducibility metadata and per-query metrics. Category Precision@10 is
weak-label topical agreement, not judged relevance.

`eval/judging_pool.csv` contains the shuffled, deduplicated top-ten union for
the eight Layer-2 queries, with no retriever identities and blank grade/note
fields. See [the judging handoff](eval/JUDGING.md). The evaluator protects a CSV
with filled human work from overwriting. No grading, qrels, generation/API/UI,
or generation-based abstention scoring is performed in Step 3.

## Step 4 generation API and Gradio

Set `OPENAI_API_KEY` for an account with available API credit. Model defaults
to `gpt-4o-mini` at temperature 0; `LLM_MODEL`, `LLM_TEMPERATURE`,
`LLM_MAX_OUTPUT_TOKENS`, and `LLM_TIMEOUT` are
configurable. Keep the UTF-8 environment variables from quickstart set in both
terminals. Start the API and UI in separate terminals:

```powershell
uv run uvicorn safelens.app:app --host 127.0.0.1 --port 8000
```

```powershell
uv run python -m safelens.ui
```

Open [Gradio](http://127.0.0.1:7860) or [API documentation](http://127.0.0.1:8000/docs).
The UI reads FastAPI over HTTP only; `SAFELENS_API_URL` selects its API URL.
`GET /health` checks the ready index, not external provider quota.

- `POST /ask` accepts `{question, category?}` and returns `{answer, citations,
  results, validation, index_id}`. Citations contain `{acn, chunk_id, passage}`.
- `GET /report/{acn}` returns the indexed normalized report, exact chunk texts,
  content hash, source dataset/revision, and active build ID.
- OpenAPI defines stable request/response schemas. A model/config mismatch or
  offline build makes serving unavailable; the API never serves mixed builds.

Context is the best chunk of each hybrid top-five report, plus a distinct
component chunk only when that report is top-five in the component. There are
at most two chunks per report and eight total. Prompts distinguish reporter
accounts from confirmed findings, prohibit unsupported claims and invented
date precision, and request qualified refusal when support is missing.

Every cited ACN must belong to supplied passages. Fabricated citations are
dropped, the answer is flagged, and unsafe/uncited output is replaced with
`insufficient evidence.` Valid citation membership does not prove claim support.
Lexical semantics and retrieval defaults remain unchanged.

Run `uv run python scripts/smoke_step4.py` for the three controls and two normal
queries; it verifies citation passages and source reports against PostgreSQL.
`uv run python scripts/check_step4_local.py` verifies health, source contracts,
and the Gradio report callback without calling generation. Retrieved text and
full smoke output stay under ignored `data/`; outcomes are documented in notes.

### Human judging and relevance metrics

Do not create labels automatically. After Cynthia fills every row in
`eval/judging_pool.csv`:

```powershell
uv run python eval/import_judgments.py
uv run python eval/run_eval.py
```

The importer checks query IDs, subset ACNs, complete pool coverage, unique pairs,
and grades 0/1/2, then creates `eval/qrels.jsonl` without overwriting an existing
file. Blank or invalid grades create no output. The evaluator preserves matching
human-filled CSVs. It scores only when qrels exist and refuses comparisons with
unjudged top-ten reports.

Precision@10 and MRR use grade >=1 as relevant. MRR is measured over the returned
top ten. nDCG@10 uses linear gains 2/1/0 and the ideal ranking of the judged pool.
Both per-query and macro-average scores are appended separately from Layer-1
category agreement. No qrels or human grades are supplied by this implementation.

## Step 5 flagship scale-up

Step 5 keeps every Mini report and adds 15,000 reports sampled proportionally
by year from the remaining pinned source, with seed 20261120. No retrieval,
query, prompt, or generation behavior changes. The original Mini manifest,
human-filled pool, and qrels remain frozen; 5k experiment/results are archived.

```powershell
uv run python -m safelens.corpus
uv run python -m safelens.cli reindex --corpus-manifest eval/corpus_manifest_20k.json --incremental
uv run python eval/run_eval.py --manifest eval/corpus_manifest_20k.json
uv run python scripts/validate_step5.py
```

Incremental growth reuses unchanged report chunks and embeddings when content
hash and active configuration match. Only new/changed reports are embedded;
the ready-build switch is atomic and growth never infers deletions. A repeat
with unchanged inputs initializes no embedding model and creates no new build.
The CPU embedding pass is offline and can take substantial time at this scale.

After publication, `eval/current_corpus.json` designates the active manifest for
default evaluation. The new experiment records this switch, the development
split, and deltas against the archived 5k numbers. The 20k results section is
appended to `eval/results.md`; the Mini section is retained.

Retaining judged reports does not guarantee judgment coverage of every newly
retrieved top-ten pair. The evaluator never treats missing qrels as grade zero.
If coverage is incomplete, full 20k Layer-2 scores/deltas remain pending and a
separate blinded `eval/judging_pool_20k_additions.csv` requests only the missing
pairs. The original human judging sheet and qrels are never overwritten.
Step 6 retrieval bake-offs are outside this step.

## Project documents

- [Frozen Mini specification](docs/PROJECT1_MINI_WEEKEND_SPEC.md)
- [Data mapping and inspection notes](docs/DATA_NOTES.md)
- [Step-by-step kickoff and acceptance checks](CODEX_KICKOFF.md)
- [Contributor rules](AGENTS.md)
