"""Post-freeze routing checks on new development counts, independently SQL-counted."""

import argparse
import csv
import hashlib
import json
from pathlib import Path

import httpx
import psycopg

from safelens.config import Settings

CASES = [
    ("Count reports in 2018 about NMAC conflicts", 2018, "Conflict NMAC"),
    ("How many reports in 2017 about incursions runway?", 2017, "Ground Incursion Runway"),
    ("Count reports in 2021 about problems critical equipment", 2021, "Aircraft Equipment Problem Critical"),
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8001")
    parser.add_argument("--output", type=Path, default=Path("docs/POST_FREEZE_FIX_CNT1_VALIDATION.json"))
    args = parser.parse_args()
    checks = []
    with psycopg.connect(Settings.from_env().database_url, autocommit=True) as conn, httpx.Client(base_url=args.base_url, timeout=30) as client:
        denominator = conn.execute("SELECT count(*) FROM reports").fetchone()[0]
        assert denominator == 20000
        for question, year, category in CASES:
            # Independently authored SQL: do not use the production mapper or COUNT_SQL as an oracle.
            expected = conn.execute("SELECT count(*) FROM reports WHERE report_year = %s AND %s = ANY(anomaly_codes)",
                                    (year, category)).fetchone()[0]
            response = client.post("/ask", json={"question": question})
            response.raise_for_status()
            body = response.json()
            aggregate = body["aggregate"] or {}
            filters = {"year_start": year, "year_end": year, "anomaly_category": category}
            stages = [event["stage"] for event in body["trace"]]
            passed = (body["status"] == "answered" and aggregate.get("count") == expected
                      and aggregate.get("denominator") == denominator and aggregate.get("filters") == filters
                      and body["usage"]["model_calls"] == 0 and not body["citations"]
                      and stages == ["route", "aggregate_sql"])
            checks.append({"question": question, "year": year, "category": category,
                           "independent_sql_count": expected, "denominator": denominator,
                           "actual": aggregate, "status": body["status"], "model_calls": body["usage"]["model_calls"],
                           "stages": stages, "passed": passed})
    pool = Path("eval/judging_pool_step7_additions.csv")
    with pool.open(encoding="utf-8", newline="") as source:
        rows = list(csv.DictReader(source))
    filled = sum(bool(row["grade"].strip()) for row in rows)
    part_b = {"rows": len(rows), "filled_grades": filled,
              "status": "ready_for_import_validation" if filled == 5 else "waiting_on_judgments",
              "pool_sha256": hashlib.sha256(pool.read_bytes()).hexdigest()}
    assert part_b["rows"] == 5, "Unexpected judging pool size"
    result = {"split": "post-freeze development only", "frozen_question_asked": False,
              "sealed_final_answer_used_as_target": False, "checks": checks, "part_b": part_b,
              "aggregate_source_sha256": hashlib.sha256(Path("src/safelens/aggregate.py").read_bytes()).hexdigest(),
              "passed": all(row["passed"] for row in checks)}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
