"""Read-only corpus verification plus a repeat-run acceptance check for Step 1."""

import collections
import hashlib
import json
from dataclasses import asdict
from pathlib import Path

import psycopg
from psycopg.rows import dict_row

from safelens.config import Settings
from safelens.ingest import SOURCE_COLUMNS, ingest, normalize


def main():
    paths = [Path(f"data/asrs-aviation-reports-{split}.jsonl")
             for split in ("train", "validation", "test")]
    slice_raw = []
    years = collections.Counter()
    labels = collections.Counter()
    selected_overlap = collections.Counter()
    selected = {
        "Ground Incursion Runway", "Deviation - Altitude Excursion From Assigned Altitude",
        "Conflict NMAC", "Aircraft Equipment Problem Critical",
    }
    total = 0
    for path in paths:
        with path.open(encoding="utf-8") as source:
            for line in source:
                raw = json.loads(line)
                assert set(raw) == SOURCE_COLUMNS
                report = normalize(raw)
                assert report is not None
                total += 1
                if len(slice_raw) < 1000:
                    slice_raw.append(raw)
                    years[report.report_year] += 1
                    labels.update(report.anomaly_codes)
                    selected_overlap[len(set(report.anomaly_codes) & selected)] += 1
    settings = Settings.from_env()
    with psycopg.connect(settings.database_url, autocommit=True, connect_timeout=10) as conn:
        before = conn.execute(
            "SELECT count(*), count(DISTINCT acn) FROM reports"
        ).fetchone()
        assert before == (1000, 1000), before
        chunks_before = conn.execute("SELECT count(*) FROM chunks").fetchone()[0]
        states_before = conn.execute("SELECT count(*) FROM ingest_state").fetchone()[0]
        hashes_before = conn.execute(
            "SELECT acn, content_hash FROM reports ORDER BY acn"
        ).fetchall()
        rerun = ingest(conn, paths, settings, limit=1000)
        assert rerun == {"skipped": 1000, "inserted": 0, "updated": 0,
                         "failed": 0, "dropped": 0, "duplicates": 0}
        assert conn.execute("SELECT acn, content_hash FROM reports ORDER BY acn").fetchall() == hashes_before
        assert conn.execute("SELECT count(*) FROM chunks").fetchone()[0] == chunks_before == 0
        assert conn.execute("SELECT count(*) FROM index_meta").fetchone()[0] == 0
        assert states_before == 1000
        spot_checks = []
        for index in (0, 499, 999):
            raw = slice_raw[index]
            report = normalize(raw)
            with conn.cursor(row_factory=dict_row) as cursor:
                stored = cursor.execute(
                    "SELECT * FROM reports WHERE acn=%s", (report.acn,)
                ).fetchone()
            assert stored == {**asdict(report), "content_hash": report.content_hash}
            # Independently reconstruct source text and fields, rather than only using normalize().
            expected_narrative = "\n\n".join(
                f"— Report {n} —\n{raw[f'Report {n}_Narrative'].strip()}"
                for n in (1, 2) if raw[f"Report {n}_Narrative"].strip()
            )
            assert stored["narrative"] == expected_narrative
            assert stored["report_month"] == raw["Time_Date"][:4] + "-" + raw["Time_Date"][4:]
            assert stored["anomaly_codes"] == [
                p.strip() for p in raw["Events_Anomaly"].split(";") if p.strip()
            ]
            spot_checks.append({"acn": report.acn, "slice_index": index,
                                "has_report_2": bool(raw["Report 2_Narrative"].strip()),
                                "report_month": report.report_month, "verified": True})
    result = {
        "full_rows_schema_and_normalization_validated": total,
        "file_sha256": {},
        "reports": before[0], "unique_acns": before[1], "chunks": chunks_before,
        "ready_indexes": 0, "rerun": rerun, "spot_checks": spot_checks,
        "slice_selection": "First 1000 unique nonempty-narrative ACNs in train, validation, test file order; no sampling",
        "slice_years": dict(sorted(years.items())),
        "slice_selected_labels": {key: labels[key] for key in sorted(selected)},
        "slice_selected_label_overlap": dict(sorted(selected_overlap.items())),
    }
    for path in paths:
        with path.open("rb") as source:
            result["file_sha256"][str(path)] = hashlib.file_digest(source, "sha256").hexdigest()
    Path("docs/STEP1_VALIDATION.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
