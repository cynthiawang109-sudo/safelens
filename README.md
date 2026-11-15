# SafeLens

SafeLens is a planned retrieval and grounded-answer system over NASA ASRS
aviation safety reporter accounts. The Mini milestone will compare PostgreSQL
full-text search, dense retrieval, and hybrid retrieval with report-level
evaluation.

Current milestone: Step 3 — a deterministic 5,000-report subset, unfiltered
Layer-1 evaluation, and a blinded judging pool. Human relevance judgments and
generation remain future work; this is not yet a complete RAG application.

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

## Project documents

- [Frozen Mini specification](docs/PROJECT1_MINI_WEEKEND_SPEC.md)
- [Data mapping and inspection notes](docs/DATA_NOTES.md)
- [Step-by-step kickoff and acceptance checks](CODEX_KICKOFF.md)
- [Contributor rules](AGENTS.md)
