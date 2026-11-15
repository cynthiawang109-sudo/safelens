"""Child process used only by the forced-termination integration test."""

import json
import os
import sys
import time
from dataclasses import replace
from pathlib import Path

import psycopg

from safelens.config import Settings
from safelens.ingest import PreparedChunk, Report, upsert_report


def main():
    dsn, report_path, marker_path = sys.argv[1:]
    report = Report(**json.loads(Path(report_path).read_text(encoding="utf-8")))
    report = replace(report, synopsis="Uncommitted replacement")

    def pause(conn, report):
        Path(marker_path).write_text(str(os.getpid()), encoding="utf-8")
        time.sleep(120)

    with psycopg.connect(dsn, autocommit=True, connect_timeout=10) as conn:
        upsert_report(
            conn, report, Settings.from_env(), after_write=pause,
            prepared_chunks=[PreparedChunk("Uncommitted chunk", [0.2] * 384)],
        )


if __name__ == "__main__":
    main()
