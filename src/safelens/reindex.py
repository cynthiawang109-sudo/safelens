"""Explicit offline index build; atomic chunk replacement after validation."""

import logging
import math

from psycopg import sql
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from safelens.chunk import chunk_report

LOCK = 742802
LOG = logging.getLogger(__name__)


def reindex(conn, settings, provider_factory, before_swap=None, replacement_reports=None):
    """Use an autocommit connection. Session lock excludes serving and ingestion.

    A killed builder retains only a building metadata row; old chunks stay valid.
    The next explicit build marks abandoned building rows failed under the lock.
    """
    if not conn.autocommit:
        raise ValueError("Reindex requires an autocommit connection")
    if not conn.execute("SELECT pg_try_advisory_lock(%s)", (LOCK,)).fetchone()[0]:
        raise RuntimeError("Another ingest/reindex operation is active")
    build_id = None
    try:
        with conn.cursor(row_factory=dict_row) as cursor:
            original = cursor.execute("SELECT * FROM reports ORDER BY acn COLLATE \"C\"").fetchall()
        reports = original if replacement_reports is None else sorted(replacement_reports, key=lambda r: r["acn"])
        if len({report["acn"] for report in reports}) != len(reports):
            raise ValueError("Replacement corpus contains duplicate ACNs")
        with conn.transaction():
            conn.execute("UPDATE index_meta SET status='failed' WHERE status='building'")
            count = len(reports)
            if not count:
                raise ValueError("Cannot build an empty corpus")
            build_id = conn.execute(
                "INSERT INTO index_meta (status, embedding_model, embedding_dim, "
                "embed_query_prefix, chunk_config, report_count, built_at) "
                "VALUES ('building', %s, %s, %s, %s, %s, now()) RETURNING id",
                (settings.embedding_model, settings.embedding_dim, settings.embed_query_prefix,
                 Jsonb(settings.chunk_config), count),
            ).fetchone()[0]
        provider = provider_factory(settings)
        conn.execute("CREATE TEMP TABLE staged_chunks (acn text, chunk_idx int, text text, embedding text)")
        pending = []
        for report in reports:
            passages = chunk_report(report["synopsis"] or "", report["narrative"], provider, settings)
            pending.extend((report["acn"], index, text) for index, text in enumerate(passages))
        # Pack similarly sized inputs together to avoid padding short chunks to 500 tokens.
        pending.sort(key=lambda row: provider.count_tokens(row[2]), reverse=True)
        expected = len(pending)
        for start in range(0, expected, settings.embedding_batch_size):
            batch = pending[start:start + settings.embedding_batch_size]
            vectors = provider.embed_documents([row[2] for row in batch])
            if len(vectors) != len(batch) or any(
                len(vector) != settings.embedding_dim
                or not all(math.isfinite(v) for v in vector)
                or not any(vector) for vector in vectors
            ):
                raise ValueError("Embedding count/dimension/values do not match chunks")
            with conn.transaction(), conn.cursor() as cursor:
                cursor.executemany(
                    "INSERT INTO staged_chunks VALUES (%s, %s, %s, %s)",
                    [(*row, str(vector)) for row, vector in zip(batch, vectors)],
                )
            LOG.info("Build %s: embedded %s/%s chunks", build_id, min(start + len(batch), expected), expected)
        actual = conn.execute("SELECT count(*), count(DISTINCT acn) FROM staged_chunks").fetchone()
        if actual != (expected, count):
            raise ValueError("Staged chunk/report count validation failed")
        with conn.transaction():
            # Defensive locks also protect against SQL writers outside the advisory protocol.
            conn.execute("LOCK TABLE reports IN SHARE MODE")
            with conn.cursor(row_factory=dict_row) as cursor:
                current = cursor.execute("SELECT * FROM reports ORDER BY acn COLLATE \"C\"").fetchall()
            if current != original:
                raise ValueError("Corpus changed while embedding; rebuild required")
            conn.execute("DELETE FROM chunks")
            if replacement_reports is not None:
                # Old reports and ingestion state are removed only inside the atomic swap.
                conn.execute("DELETE FROM reports")
                columns = list(reports[0])
                with conn.cursor() as cursor:
                    cursor.executemany(
                        sql.SQL("INSERT INTO reports ({}) VALUES ({})").format(
                            sql.SQL(", ").join(map(sql.Identifier, columns)),
                            sql.SQL(", ").join(sql.Placeholder() for _ in columns),
                        ),
                        [[report[c] for c in columns] for report in reports],
                    )
            conn.execute(sql.SQL("ALTER TABLE chunks ALTER COLUMN embedding TYPE vector({})").format(
                sql.Literal(settings.embedding_dim)
            ))
            conn.execute(
                "INSERT INTO chunks (acn, chunk_idx, text, embedding, anomaly_codes, "
                "flight_phase, aircraft_category, report_month, report_year) "
                "SELECT s.acn, s.chunk_idx, s.text, s.embedding::vector, r.anomaly_codes, "
                "r.flight_phase, r.aircraft_category, r.report_month, r.report_year "
                "FROM staged_chunks s JOIN reports r USING (acn) ORDER BY s.acn COLLATE \"C\", s.chunk_idx"
            )
            validated = conn.execute(
                "SELECT count(*), count(DISTINCT acn), count(embedding) FROM chunks"
            ).fetchone()
            if validated != (expected, count, expected):
                raise ValueError("Installed index count validation failed")
            if before_swap:
                before_swap(conn)
            conn.execute("UPDATE index_meta SET status='superseded' WHERE status='ready'")
            conn.execute("UPDATE index_meta SET status='ready', built_at=now() WHERE id=%s", (build_id,))
            state = {"stage": "indexed", "index_config": settings.index_config,
                     "active_index": settings.index_config}
            conn.execute(
                "INSERT INTO ingest_state SELECT acn, %s FROM reports "
                "ON CONFLICT (acn) DO UPDATE SET config=EXCLUDED.config", (Jsonb(state),)
            )
        return {"build_id": build_id, "status": "ready", "reports": count, "chunks": expected}
    except BaseException:
        if build_id is not None:
            conn.execute("UPDATE index_meta SET status='failed' WHERE id=%s AND status='building'", (build_id,))
        raise
    finally:
        conn.execute("DROP TABLE IF EXISTS pg_temp.staged_chunks")
        conn.execute("SELECT pg_advisory_unlock(%s)", (LOCK,))
