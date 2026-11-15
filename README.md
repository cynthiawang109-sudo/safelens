# SafeLens

SafeLens is a planned retrieval and grounded-answer system over NASA ASRS
aviation safety reporter accounts. The Mini milestone will compare PostgreSQL
full-text search, dense retrieval, and hybrid retrieval with report-level
evaluation.

Current status: Step 0 repository scaffold only. Application quickstart and
retrieval results will be added in later milestones.

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
The example database credentials are for local development. The scaffold has
no tests yet; pytest reports zero collected tests (exit code 5).
Keep raw downloads and intermediate data under gitignored `data/`.

## Project documents

- [Frozen Mini specification](docs/PROJECT1_MINI_WEEKEND_SPEC.md)
- [Data mapping and inspection notes](docs/DATA_NOTES.md)
- [Step-by-step kickoff and acceptance checks](CODEX_KICKOFF.md)
- [Contributor rules](AGENTS.md)
