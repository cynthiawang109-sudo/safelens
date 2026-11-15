import json
import os
import subprocess
import sys
import time
from dataclasses import asdict, replace
from pathlib import Path

import pytest
from psycopg.types.json import Jsonb

from safelens.ingest import (
    PreparedChunk,
    Report,
    require_active_index,
    upsert_report,
)
from safelens.migrate import migrate


def example():
    return Report("123", "2015-10", 2015, "Synopsis", "— Report 1 —\nAccount",
                  ["Conflict NMAC"], "Cruise", "B737-800")


def snapshot(conn):
    return {
        table: conn.execute(f"SELECT * FROM {table} ORDER BY 1").fetchall()
        for table in ("reports", "chunks", "ingest_state", "index_meta")
    }


def test_idempotency_config_change_and_migrations(database):
    conn, _, settings = database
    report = example()
    assert upsert_report(conn, report, settings) == "inserted"
    before = snapshot(conn)
    assert upsert_report(conn, report, settings) == "skipped"
    assert snapshot(conn) == before
    assert migrate(conn, Path("db/migrations")) == []
    for changed in (
        replace(settings, chunk_tokens=450),
        replace(settings, embedding_model="different-model"),
        replace(settings, embed_query_prefix="different prefix: "),
    ):
        assert upsert_report(conn, report, changed) == "updated"
        assert upsert_report(conn, report, changed) == "skipped"
    with pytest.raises(ValueError, match="matching ready"):
        require_active_index(conn, settings)


def test_atomic_replacement_and_ready_index_guard(database):
    conn, _, settings = database
    report = example()
    chunk = PreparedChunk("Old chunk", [0.1] * settings.embedding_dim)
    upsert_report(conn, report, settings, prepared_chunks=[chunk])
    before = snapshot(conn)

    def fail(conn, report):
        raise RuntimeError("forced failure after report and chunk replacement")

    with pytest.raises(RuntimeError, match="forced failure"):
        upsert_report(conn, replace(report, synopsis="New synopsis"), settings,
                      after_write=fail, prepared_chunks=[PreparedChunk("New chunk", [0.2] * 384)])
    assert snapshot(conn) == before
    assert upsert_report(conn, replace(report, synopsis="New synopsis"), settings,
                         prepared_chunks=[chunk, chunk]) == "updated"
    assert conn.execute("SELECT count(*) FROM chunks").fetchone() == (2,)
    conn.execute(
        "INSERT INTO index_meta (status, embedding_model, embedding_dim, embed_query_prefix, "
        "chunk_config, report_count, built_at) VALUES ('ready', %s, %s, %s, %s, 1, now())",
        (settings.embedding_model, settings.embedding_dim, settings.embed_query_prefix,
         Jsonb(settings.chunk_config)),
    )
    require_active_index(conn, settings)
    with pytest.raises(ValueError, match="configuration mismatch"):
        upsert_report(conn, report, replace(settings, embedding_model="other"))
    with pytest.raises(ValueError, match="cannot update a ready index"):
        upsert_report(conn, report, settings)
    with pytest.raises(ValueError, match="matching ready"):
        require_active_index(conn, replace(settings, chunk_tokens=450))


def test_killed_process_preserves_report_and_chunks(database, tmp_path):
    conn, dsn, settings = database
    report = example()
    upsert_report(conn, report, settings,
                  prepared_chunks=[PreparedChunk("Old chunk", [0.1] * 384)])
    conn.execute(
        "INSERT INTO index_meta (status, embedding_model, embedding_dim, embed_query_prefix, "
        "chunk_config, report_count, built_at) VALUES ('ready', %s, %s, %s, %s, 1, now())",
        (settings.embedding_model, settings.embedding_dim, settings.embed_query_prefix,
         Jsonb(settings.chunk_config)),
    )
    upsert_report(conn, report, settings,
                  prepared_chunks=[PreparedChunk("Old chunk", [0.1] * 384)])
    before = snapshot(conn)
    report_path = tmp_path / "report.json"
    report_path.write_text(json.dumps(asdict(report)), encoding="utf-8")
    marker = tmp_path / "transaction_open"
    env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
    child = subprocess.Popen(
        [sys.executable, "tests/kill_worker.py", dsn, str(report_path), str(marker)],
        env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8",
    )
    try:
        deadline = time.monotonic() + 20
        while not marker.exists() and child.poll() is None and time.monotonic() < deadline:
            time.sleep(0.05)
        assert marker.exists(), child.communicate(timeout=1)
        # MVCC readers still see the complete old state while the transaction is open.
        assert snapshot(conn) == before
        child.kill()
        child.communicate(timeout=10)
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            if not conn.execute(
                "SELECT 1 FROM pg_stat_activity WHERE pid <> pg_backend_pid() "
                "AND state = 'idle in transaction' AND query LIKE 'INSERT INTO chunks%'"
            ).fetchone():
                break
            time.sleep(0.05)
        assert snapshot(conn) == before
        assert upsert_report(conn, report, settings,
                             prepared_chunks=[PreparedChunk("Old chunk", [0.1] * 384)]) == "skipped"
    finally:
        if child.poll() is None:
            child.kill()
            child.communicate(timeout=10)
