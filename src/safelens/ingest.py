"""Stream and validate pinned ASRS JSONL; commit each normalized ACN atomically.

The CLI imports reports only. Unchanged indexed reports may skip; changed
indexed content requires prepared chunks or the explicit offline reindex path.
"""

import argparse
import hashlib
import json
import logging
import math
import re
from dataclasses import asdict, dataclass
from pathlib import Path

import psycopg
from psycopg.types.json import Jsonb

from safelens.config import Settings

SOURCE_DATASET = "elihoole/asrs-aviation-reports"
SOURCE_REVISION = "f1e681e92cddae20d01fc498d685f1cf6a052d34"
SOURCE_COLUMNS = frozenset(json.loads(
    Path(__file__).with_name("source_columns.json").read_text(encoding="utf-8")
))
REQUIRED_COLUMNS = frozenset({
    "acn_num_ACN", "Time_Date", "Events_Anomaly", "Aircraft 1.9_Flight Phase",
    "Aircraft 1.2_Make Model Name", "Report 1.2_Synopsis",
    "Report 1_Narrative", "Report 2_Narrative",
})
LOG = logging.getLogger(__name__)


@dataclass(frozen=True)
class Report:
    acn: str
    report_month: str
    report_year: int
    synopsis: str
    narrative: str
    anomaly_codes: list[str]
    flight_phase: str
    aircraft_category: str
    source_dataset: str = SOURCE_DATASET
    source_revision: str = SOURCE_REVISION

    @property
    def content_hash(self):
        # Fixed dataclass field order, compact UTF-8 JSON, no ASCII escaping.
        canonical = json.dumps(asdict(self), ensure_ascii=False, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class PreparedChunk:
    """Already prepared outside the transaction; the write seam never runs models."""

    text: str
    embedding: list[float]


def normalize(raw: dict) -> Report | None:
    unknown = set(raw) - SOURCE_COLUMNS
    missing = REQUIRED_COLUMNS - set(raw)
    if unknown or missing:
        raise ValueError(f"Source schema mismatch: unknown={sorted(unknown)}, missing={sorted(missing)}")
    for name, value in raw.items():
        if value is not None and not isinstance(value, str):
            raise ValueError(f"Expected string or null: {name}")
    acn = (raw["acn_num_ACN"] or "").strip()
    if not re.fullmatch(r"[0-9]+", acn):
        raise ValueError("ACN must be a nonempty numeric string")
    date = (raw["Time_Date"] or "").strip()
    if not re.fullmatch(r"[0-9]{4}(0[1-9]|1[0-2])", date) or int(date[:4]) == 0:
        raise ValueError(f"Invalid YYYYMM for ACN {acn}: {date!r}")
    narratives = []
    for number in (1, 2):
        text = (raw[f"Report {number}_Narrative"] or "").strip()
        if text:
            narratives.append(f"— Report {number} —\n{text}")
    if not narratives:
        return None
    return Report(
        acn=acn, report_month=f"{date[:4]}-{date[4:]}", report_year=int(date[:4]),
        synopsis=raw["Report 1.2_Synopsis"] or "", narrative="\n\n".join(narratives),
        anomaly_codes=[p.strip() for p in (raw["Events_Anomaly"] or "").split(";") if p.strip()],
        flight_phase=raw["Aircraft 1.9_Flight Phase"] or "",
        aircraft_category=raw["Aircraft 1.2_Make Model Name"] or "",
    )


def stream_reports(paths):
    for path in paths:
        with Path(path).open(encoding="utf-8") as source:
            for line_number, line in enumerate(source, 1):
                try:
                    raw = json.loads(line)
                    if not isinstance(raw, dict):
                        raise TypeError("Expected a JSON object")
                    yield normalize(raw)
                except (ValueError, TypeError) as exc:
                    raise ValueError(f"{path}:{line_number}: {exc}") from exc


def active_index_config(conn):
    rows = conn.execute(
        "SELECT embedding_model, embedding_dim, embed_query_prefix, chunk_config "
        "FROM index_meta WHERE status = 'ready'"
    ).fetchall()
    if len(rows) > 1:
        raise ValueError("More than one ready index")
    if not rows:
        return None
    return dict(zip(
        ("embedding_model", "embedding_dim", "embed_query_prefix", "chunk_config"), rows[0]
    ))


def require_active_index(conn, settings):
    if active_index_config(conn) != settings.index_config:
        raise ValueError("No matching ready index; run an explicit offline reindex")


def upsert_report(conn, report: Report, settings: Settings, after_write=None, prepared_chunks=None):
    """Atomic report/chunk replacement; after_write synchronizes failure tests."""
    if prepared_chunks is not None:
        prepared_chunks = list(prepared_chunks)
        if not prepared_chunks or any(
            len(chunk.embedding) != settings.embedding_dim
            or not all(math.isfinite(value) for value in chunk.embedding)
            for chunk in prepared_chunks
        ):
            raise ValueError("Prepared chunks must have finite vectors of the configured dimension")
    with conn.transaction():
        # Serialize import writers and index-state inspection for this transaction.
        conn.execute("SELECT pg_advisory_xact_lock(742802)")
        active = active_index_config(conn)
        if active is not None and active != settings.index_config:
            raise ValueError("Active index configuration mismatch; offline reindex required")
        state = {
            "stage": "indexed" if prepared_chunks is not None or active is not None else "reports_only",
            "index_config": settings.index_config, "active_index": active,
        }
        old = conn.execute(
            "SELECT r.content_hash, s.config FROM reports r LEFT JOIN ingest_state s USING (acn) "
            "WHERE r.acn = %s FOR UPDATE OF r", (report.acn,)
        ).fetchone()
        if old and old == (report.content_hash, state):
            return "skipped"
        if active is not None and prepared_chunks is None:
            raise ValueError("Report-only ingestion cannot update a ready index; offline reindex required")
        if prepared_chunks is None and conn.execute(
            "SELECT 1 FROM chunks WHERE acn = %s LIMIT 1", (report.acn,)
        ).fetchone():
            raise ValueError("Existing chunks require atomic offline index replacement")
        record = asdict(report)
        record["content_hash"] = report.content_hash
        columns = list(record)
        conn.execute(
            f"INSERT INTO reports ({', '.join(columns)}) "
            f"VALUES ({', '.join(['%s'] * len(columns))}) ON CONFLICT (acn) DO UPDATE SET "
            + ", ".join(f"{c} = EXCLUDED.{c}" for c in columns if c != "acn"),
            list(record.values()),
        )
        conn.execute(
            "INSERT INTO ingest_state VALUES (%s, %s) "
            "ON CONFLICT (acn) DO UPDATE SET config = EXCLUDED.config",
            (report.acn, Jsonb(state)),
        )
        if prepared_chunks is not None:
            conn.execute("DELETE FROM chunks WHERE acn = %s", (report.acn,))
            for index, chunk in enumerate(prepared_chunks):
                conn.execute(
                    "INSERT INTO chunks (acn, chunk_idx, text, embedding, anomaly_codes, "
                    "flight_phase, aircraft_category, report_month, report_year) "
                    "VALUES (%s, %s, %s, %s::vector, %s, %s, %s, %s, %s)",
                    (report.acn, index, chunk.text, str(chunk.embedding), report.anomaly_codes,
                     report.flight_phase, report.aircraft_category, report.report_month, report.report_year),
                )
            if active is not None:
                conn.execute(
                    "UPDATE index_meta SET report_count = (SELECT count(*) FROM reports) "
                    "WHERE status = 'ready'"
                )
        if after_write:
            after_write(conn, report)
        return "updated" if old else "inserted"


def ingest(conn, paths, settings, limit=1000):
    if limit <= 0:
        raise ValueError("Limit must be positive")
    counts = dict.fromkeys(("skipped", "inserted", "updated", "failed", "dropped", "duplicates"), 0)
    seen = set()
    try:
        for report in stream_reports(paths):
            if report is None:
                counts["dropped"] += 1
                continue
            if report.acn in seen:
                counts["duplicates"] += 1
                continue
            seen.add(report.acn)
            counts[upsert_report(conn, report, settings)] += 1
            if len(seen) == limit:
                break
    except Exception:
        counts["failed"] += 1
        LOG.exception("Ingestion failed; committed earlier ACNs remain valid. counts=%s", counts)
        raise
    LOG.info("Ingestion complete: %s", counts)
    return counts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", type=Path, nargs="+")
    parser.add_argument("--limit", type=int, default=1000)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    settings = Settings.from_env()
    with psycopg.connect(settings.database_url, autocommit=True, connect_timeout=10) as conn:
        print(json.dumps(ingest(conn, args.paths, settings, args.limit)))


if __name__ == "__main__":
    main()
