"""Verify live health/source contracts and the UI without calling generation."""

import json
from pathlib import Path

import httpx
import psycopg
from gradio_client import Client
from psycopg.rows import dict_row

from safelens.config import Settings


def main():
    settings = Settings.from_env()
    acn = "1857031"
    with (httpx.Client(base_url="http://127.0.0.1:8000", timeout=20) as api,
          psycopg.connect(settings.database_url, autocommit=True, connect_timeout=10) as conn):
        health = api.get("/health")
        health.raise_for_status()
        assert health.json()["reports"] == 5000 and health.json()["chunks"] == 6998
        response = api.get(f"/report/{acn}")
        response.raise_for_status()
        report = response.json()
        with conn.cursor(row_factory=dict_row) as cursor:
            stored = cursor.execute("SELECT * FROM reports WHERE acn=%s", (acn,)).fetchone()
            chunks = cursor.execute("SELECT id AS chunk_id,chunk_idx,text FROM chunks WHERE acn=%s ORDER BY chunk_idx", (acn,)).fetchall()
        assert all(report[key] == value for key, value in stored.items())
        assert report["text"] == stored["synopsis"] + "\n\n" + stored["narrative"]
        assert report["chunks"] == chunks
        schema = api.get("/openapi.json").json()
        assert "AskResponse" in schema["components"]["schemas"]
        assert "ReportResponse" in schema["components"]["schemas"]
    page = httpx.get("http://127.0.0.1:7860", timeout=20)
    page.raise_for_status()
    # This invokes Gradio's report callback, which in turn reads FastAPI via HTTP.
    ui_report = Client("http://127.0.0.1:7860", verbose=False).predict(acn, api_name="/report")
    assert ui_report == report
    outcome = {"health": health.json(), "report_acn": acn, "all_source_fields_match_db": True,
               "exact_chunk_texts_match_db": True, "openapi_contracts_present": True,
               "gradio_http_status": page.status_code, "gradio_report_callback_matches_api": True,
               "generation_called": False, "qrels_created": Path("eval/qrels.jsonl").exists()}
    Path("data/step4_local_checks.json").write_text(json.dumps(outcome, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(outcome, indent=2))


if __name__ == "__main__":
    main()
