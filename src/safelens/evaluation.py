"""Strict qrels ingestion and report-level judged relevance metrics."""

import csv
import json
import math
from pathlib import Path
from statistics import mean


def load_qrels(path, allowed_query_ids):
    qrels = {}
    with Path(path).open(encoding="utf-8") as source:
        for number, line in enumerate(source, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            if set(row) - {"query_id", "acn", "grade", "note"} or not {"query_id", "acn", "grade"} <= row.keys():
                raise ValueError(f"Invalid qrel fields on line {number}")
            if row["query_id"] not in allowed_query_ids or not isinstance(row["acn"], str) or not row["acn"].isdigit():
                raise ValueError(f"Invalid qrel query/ACN on line {number}")
            if type(row["grade"]) is not int or row["grade"] not in (0, 1, 2):
                raise ValueError(f"Qrel grade must be integer 0, 1, or 2 on line {number}")
            key = (row["query_id"], row["acn"])
            if key in qrels:
                raise ValueError(f"Duplicate qrel: {key}")
            qrels[key] = row["grade"]
    if not qrels:
        raise ValueError("Qrels file is empty")
    return qrels


def judged_metrics(queries, rankings, qrels):
    judged = [q for q in queries if q["layer"] == 2]
    rows = []
    for query in judged:
        qid = query["id"]
        pooled = [grade for (query_id, _), grade in qrels.items() if query_id == qid]
        if not pooled:
            raise ValueError(f"No judgments for query {qid}")
        ideal = sum(grade / math.log2(rank + 1) for rank, grade in
                    enumerate(sorted(pooled, reverse=True)[:10], 1))
        for method, hits in rankings[qid].items():
            missing = [h["acn"] for h in hits[:10] if (qid, h["acn"]) not in qrels]
            if missing:
                raise ValueError(f"Unjudged top-ten reports for {qid}/{method}: {missing}; extend the pool before comparison")
            grades = [qrels[(qid, h["acn"])] for h in hits[:10]]
            dcg = sum(grade / math.log2(rank + 1) for rank, grade in enumerate(grades, 1))
            rows.append({"query_id": qid, "method": method,
                         "precision_at_10": sum(grade >= 1 for grade in grades) / 10,
                         "mrr": next((1 / rank for rank, grade in enumerate(grades, 1) if grade >= 1), 0.0),
                         "ndcg_at_10": dcg / ideal if ideal else 0.0})
    methods = list(next(iter(rankings.values())))
    averages = {method: {metric: mean(r[metric] for r in rows if r["method"] == method)
                        for metric in ("precision_at_10", "mrr", "ndcg_at_10")} for method in methods}
    return {"status": "ready", "queries": len(judged), "per_query": rows, "averages": averages,
            "definitions": "P@10 denominator=10; relevant=grade>=1; MRR over retrieved top ten; nDCG linear gains 2/1/0, pooled ideal; unjudged top-ten fails"}


def import_judgments(csv_path, output, queries_path, manifest_path, expected_pairs=None):
    """Validate a fully human-filled CSV and create qrels without overwriting."""
    with Path(queries_path).open(encoding="utf-8") as source:
        query_ids = {q["id"] for line in source if line.strip() and (q := json.loads(line))["layer"] == 2}
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    allowed_acns = set(manifest["selected_acns"])
    rows, seen = [], set()
    with Path(csv_path).open(encoding="utf-8", newline="") as source:
        reader = csv.DictReader(source)
        if reader.fieldnames != ["query_id", "acn", "synopsis", "grade", "note"]:
            raise ValueError("Judging CSV must have query_id, acn, synopsis, grade, note columns")
        for row in reader:
            key = (row["query_id"], row["acn"])
            if key in seen or key[0] not in query_ids or key[1] not in allowed_acns:
                raise ValueError(f"Duplicate or unknown query/report: {key}")
            if row["grade"] is None or row["grade"].strip() not in ("0", "1", "2"):
                raise ValueError(f"Every pool row needs a human grade 0, 1, or 2: {key}")
            seen.add(key)
            record = {"query_id": key[0], "acn": key[1], "grade": int(row["grade"].strip())}
            if row["note"]:
                record["note"] = row["note"]
            rows.append(record)
    if {qid for qid, _ in seen} != query_ids or not rows:
        raise ValueError("Judgments must cover every Layer-2 query")
    if expected_pairs is not None and seen != expected_pairs:
        raise ValueError("Judgments must cover the entire current judging pool, with no added or missing pairs")
    # Validation finishes before creating any output; blank or invalid input leaves no qrels.
    with Path(output).open("x", encoding="utf-8") as target:
        for row in sorted(rows, key=lambda r: (r["query_id"], r["acn"])):
            target.write(json.dumps(row, ensure_ascii=False) + "\n")
    return len(rows)
