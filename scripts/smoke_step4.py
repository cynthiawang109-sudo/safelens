"""Exercise the live HTTP API on three controls and two normal queries."""

import json
import os
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

import httpx
import psycopg
from psycopg.rows import dict_row

from safelens.config import Settings


def main():
    with Path("eval/queries.jsonl").open(encoding="utf-8") as source:
        queries = [json.loads(line) for line in source if line.strip()]
    selected = [q for q in queries if q["layer"] == "control"] + [
        next(q for q in queries if q["id"] == qid) for qid in ("alt-l2-1", "nmac-l2-1")
    ]
    settings = Settings.from_env()
    outcomes = []
    base_url = os.getenv("SAFELENS_API_URL", "http://127.0.0.1:8000")
    with (httpx.Client(base_url=base_url, timeout=100) as client,
          psycopg.connect(settings.database_url, autocommit=True, connect_timeout=10) as conn):
        health = client.get("/health")
        health.raise_for_status()
        assert health.json()["reports"] == 5000
        for query in selected:
            started = perf_counter()
            response = client.post("/ask", json={"question": query["query"]})
            response.raise_for_status()
            result = response.json()
            elapsed = (perf_counter() - started) * 1000
            for citation in result["citations"]:
                assert conn.execute("SELECT acn, text FROM chunks WHERE id=%s", (citation["chunk_id"],)).fetchone() == (citation["acn"], citation["passage"])
            assert len(result["results"]) <= 5 and len({h["acn"] for h in result["results"]}) == len(result["results"])
            assert all(c["acn"] in {h["acn"] for h in result["results"]} for c in result["citations"])
            outcomes.append({"query_id": query["id"], "query": query["query"], "answer": result["answer"],
                             "citations": result["citations"], "validation": result["validation"],
                             "index_id": result["index_id"], "latency_ms": round(elapsed, 2),
                             "declined_literal": "insufficient evidence" in result["answer"].casefold(),
                             "passages_match_db": True})
            print(json.dumps({"query_id": query["id"], "answer": result["answer"],
                              "citation_acns": [c["acn"] for c in result["citations"]],
                              "validation": result["validation"], "latency_ms": round(elapsed, 2)}, ensure_ascii=False), flush=True)
            # Keep diagnostics even if a later request/check fails. An honest
            # refusal on a normal query must not prevent testing the remaining query.
            Path("data/step4_smoke_partial.json").write_text(
                json.dumps(outcomes, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
            )
        normal = [r for r in outcomes if r["query_id"] in ("alt-l2-1", "nmac-l2-1")]
        cited_normal = [r for r in normal if r["citations"] and not r["validation"]["flagged"]]
        assert cited_normal, "Acceptance requires at least one normal answer with validated citations"
        acn = cited_normal[0]["citations"][0]["acn"]
        report_response = client.get(f"/report/{acn}")
        report_response.raise_for_status()
        report = report_response.json()
        with conn.cursor(row_factory=dict_row) as cursor:
            stored = cursor.execute("SELECT * FROM reports WHERE acn=%s", (acn,)).fetchone()
            chunks = cursor.execute("SELECT id AS chunk_id,chunk_idx,text FROM chunks WHERE acn=%s ORDER BY chunk_idx", (acn,)).fetchall()
        assert all(report[key] == value for key, value in stored.items())
        assert report["text"] == stored["synopsis"] + "\n\n" + stored["narrative"]
        assert report["chunks"] == chunks
    artifact = {"timestamp": datetime.now(UTC).isoformat(), "llm_model": settings.llm_model,
                "llm_temperature": settings.llm_temperature,
                "health": health.json(), "outcomes": outcomes,
                "report_endpoint_check": {"acn": acn, "all_source_fields_match_db": True, "chunks_match_db": True},
                "latency_scope": "5 live /ask requests including retrieval, generation, and citation validation; not a p95 study"}
    Path("data/step4_smoke.json").write_text(json.dumps(artifact, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
