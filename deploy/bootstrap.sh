#!/bin/sh
set -eu
# Explicit operator command, never part of ordinary startup.
uv run --no-sync python -m safelens.migrate
uv run --no-sync python scripts/download_dataset.py
uv run --no-sync python -m safelens.cli reindex --corpus-manifest eval/corpus_manifest_20k.json
