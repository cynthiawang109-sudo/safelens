"""Real-provider HTTP /ask smoke checks for the bounded Step 7 graph."""

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

from fastapi.testclient import TestClient

from safelens.app import create_app
from safelens.config import Settings


def main():
    queries = [json.loads(line) for line in Path("eval/queries.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    checks = [q for q in queries if q["layer"] == "control"]
    checks += [q for q in queries if q["id"] in ("equip-l2-1", "alt-l2-1")]
    checks += [{"id": "count-mapped", "query": "How many reports in 2020 about runway incursions?", "layer": "aggregate"},
               {"id": "count-unmapped", "query": "How many reports from Toronto in 2020?", "layer": "aggregate"}]
    reuse = "--reuse-responses" in sys.argv
    summaries = []
    responses = json.loads(Path("data/step7_smoke_responses.json").read_text(encoding="utf-8")) if reuse else {}
    with TestClient(create_app(Settings.from_env())) as client:
        for query in checks:
            if query["id"] not in responses:
                response = client.post("/ask", json={"question": query["query"]})
                if response.status_code != 200:
                    print(json.dumps({"query_id": query["id"], "http_status": response.status_code, "error": response.json()}), flush=True)
                    response.raise_for_status()
                responses[query["id"]] = response.json()
            body = responses[query["id"]]
            responses[query["id"]] = body
            valid = not body["validation"]["invalid_acns"]
            for citation in body["citations"]:
                source = client.get(f"/report/{citation['acn']}").json()
                assert any(c["chunk_id"] == citation["chunk_id"] and c["text"] == citation["passage"] for c in source["chunks"])
            stages = [e["stage"] for e in body["trace"]]
            passed = valid
            if query["layer"] == "control":
                passed = passed and body["status"] == "insufficient_evidence" and "grade" in stages and "retrieve" in stages
            elif query["id"] == "count-mapped":
                passed = passed and body["aggregate"] is not None and body["usage"]["model_calls"] == 0
            elif query["id"] == "count-unmapped":
                passed = passed and body["status"] == "partial" and body["aggregate"] is None
            else:
                # A normal development premise may be unsupported. A grounded
                # partial answer or qualified refusal must not be forced positive.
                passed = passed and (bool(body["citations"]) or body["status"] == "insufficient_evidence")
            summary = {"query_id": query["id"], "passed": passed, "status": body["status"],
                       "answer": body["answer"], "citations": len(body["citations"]), "usage": body["usage"],
                       "stages": stages, "invalid_acns": body["validation"]["invalid_acns"]}
            summaries.append(summary)
            Path("data/step7_smoke_responses.json").write_text(json.dumps(responses, indent=2), encoding="utf-8")
            Path("docs/STEP7_PART2_SMOKE.json").write_text(json.dumps({"timestamp": datetime.now(UTC).isoformat(),
                "transport": "FastAPI TestClient HTTP; real OpenAI and indexed PostgreSQL corpus",
                "reused_original_real_provider_responses": reuse,
                "normal_policy": "validated supported citation or qualified refusal; no forced answer to unsupported premise",
                "checks": summaries}, indent=2), encoding="utf-8")
            print(json.dumps(summary), flush=True)
    if not all(r["passed"] for r in summaries):
        raise SystemExit("Agentic smoke acceptance failed; see recorded checks")


if __name__ == "__main__":
    main()
