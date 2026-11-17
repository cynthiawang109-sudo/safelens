#!/bin/sh
set -eu
exec uv run --no-sync uvicorn safelens.app:app --host 0.0.0.0 --port "${PORT:-10000}"
