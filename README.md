# SafeLens

SafeLens is a planned retrieval and grounded-answer system over NASA ASRS
aviation safety reporter accounts. The Mini milestone will compare PostgreSQL
full-text search, dense retrieval, and hybrid retrieval with report-level
evaluation.

Current status: Step 1 schema and report-only ingestion validated on 1,000
reports. Chunking, embeddings, retrieval, and generation remain future work.

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
stage, so configuration changes cannot be silently skipped. There is no ready
vector index at this stage. The report-only CLI rejects an existing ready index
or chunks; atomic prepared-chunk replacement is tested with synthetic vectors
in isolated schemas. An explicit offline reindex implementation comes later.

The database URL uses `127.0.0.1` to avoid this Windows machine's slow IPv6
localhost connection fallback. The initial vector column is 384-dimensional;
changing model dimension will require an explicit offline schema/index rebuild.

## Project documents

- [Frozen Mini specification](docs/PROJECT1_MINI_WEEKEND_SPEC.md)
- [Data mapping and inspection notes](docs/DATA_NOTES.md)
- [Step-by-step kickoff and acceptance checks](CODEX_KICKOFF.md)
- [Contributor rules](AGENTS.md)
