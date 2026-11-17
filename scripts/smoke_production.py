"""HTTP deployment smoke using development examples only; no frozen evaluation."""

import argparse
import json
from pathlib import Path

import httpx


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("base_url")
    parser.add_argument("--output", type=Path, default=Path("data/production-smoke.json"))
    args = parser.parse_args()
    checks = []
    with httpx.Client(base_url=args.base_url.rstrip("/"), timeout=240) as client:
        health = client.get("/health")
        health.raise_for_status()
        body = health.json()
        checks.append({"name": "health", "passed": body["status"] == "ready" and body["reports"] == 20000, "reports": body["reports"]})
        for name, question in (("mechanism", "Unreliable airspeed indications left the pilots uncertain about the airplane's actual energy state."),
                               ("count", "How many reports in 2020 about runway incursions?")):
            response = client.post("/ask", json={"question": question})
            response.raise_for_status()
            answer = response.json()
            valid = not answer["validation"]["flagged"] and not answer["validation"]["invalid_acns"]
            if name == "mechanism":
                passed = valid and answer["status"] in ("answered", "partial") and bool(answer["citations"])
            else:
                aggregate = answer["aggregate"] or {}
                passed = valid and answer["status"] == "answered" and aggregate.get("count") == 98 and aggregate.get("denominator") == 20000 and aggregate.get("filters") == {
                    "year_start": 2020, "year_end": 2020, "anomaly_category": "Ground Incursion Runway"}
            checks.append({"name": name, "passed": passed, "status": answer["status"], "aggregate": answer["aggregate"], "usage": answer["usage"]})
    result = {"base_url": args.base_url, "checks": checks, "passed": all(c["passed"] for c in checks)}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
