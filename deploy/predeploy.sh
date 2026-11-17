#!/bin/sh
set -eu
# Initial bootstrap is opt-in; reset the flag before subsequent deploys.
if [ "${SAFELENS_BOOTSTRAP:-0}" = "1" ]; then
  sh deploy/bootstrap.sh
else
  uv run --no-sync python -c 'import psycopg; from safelens.config import Settings; from safelens.ingest import require_active_index; s=Settings.from_env(); c=psycopg.connect(s.database_url); require_active_index(c,s); c.close()'
fi
