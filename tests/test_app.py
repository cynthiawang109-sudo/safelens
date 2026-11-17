from dataclasses import replace

import httpx
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from test_chunk_embed import FakeProvider
from test_retrieval_index import populate

from safelens.app import create_app
from safelens.llm import GenerationUnavailable
from safelens.reindex import reindex
from safelens.ui import request_api


class FakeLLM:
    def __init__(self, settings):
        pass

    def generate(self, prompt):
        return "The reporter described a runway event [100]."

    def generate_structured(self, prompt, schema):
        import json

        from safelens.generate import AnswerDraft
        if schema is AnswerDraft:
            return AnswerDraft(status="answered", answer=self.generate(prompt)), {"input_tokens": 10, "output_tokens": 5}
        if "queries_tried" in prompt:
            return schema.model_validate({"query": "runway"}), {"input_tokens": 10, "output_tokens": 5}
        data = json.loads(prompt.split("\nReporter accounts are unverified, not confirmed findings.\n")[1])
        acns = sorted({p["acn"] for p in data["passages"]})
        return schema.model_validate({"reports": [{"acn": a, "relevance": 2,
                                                   "supports_requested_fact": True, "reason": "Fixture account"} for a in acns],
                                      "sufficiency": "sufficient", "reason": "Fixture support"}), {"input_tokens": 10, "output_tokens": 5}


def test_ask_report_and_health_match_database(database):
    conn, dsn, settings = database
    settings = replace(settings, database_url=dsn, embedding_dim=3)
    populate(conn, settings)
    reindex(conn, settings, FakeProvider)
    with TestClient(create_app(settings, FakeProvider, FakeLLM)) as client:
        assert client.get("/health").json()["reports"] == 3
        response = client.post("/ask", json={"question": "runway"})
        assert response.status_code == 200
        body = response.json()
        assert body["citations"] and not body["validation"]["flagged"]
        for citation in body["citations"]:
            assert conn.execute("SELECT acn,text FROM chunks WHERE id=%s", (citation["chunk_id"],)).fetchone() == (citation["acn"], citation["passage"])
        report = client.get("/report/100").json()
        assert report["narrative"] == conn.execute("SELECT narrative FROM reports WHERE acn='100'").fetchone()[0]
        assert report["text"] == report["synopsis"] + "\n\n" + report["narrative"]
        assert report["source_dataset"] and report["source_revision"]
        assert client.get("/report/999999999").status_code == 404
        assert client.post("/ask", json={"question": " "}).status_code == 422
        assert client.post("/ask", json={"question": "runway", "category": "typo"}).status_code == 422
        assert client.post("/ask", json={"question": "runway", "category": "Ground Incursion Runway"}).json()["answer"] == "insufficient evidence."


def test_startup_rejects_index_mismatch(database):
    conn, dsn, settings = database
    populate(conn, settings)
    reindex(conn, settings, FakeProvider)
    with (pytest.raises(HTTPException, match="503"),
          TestClient(create_app(replace(settings, database_url=dsn, chunk_tokens=450), FakeProvider, FakeLLM))):
        pass


def test_ui_reads_application_data_over_http():
    requests = []

    def handler(request):
        requests.append((request.method, request.url.path))
        return httpx.Response(200, json={"status": "ready"})

    assert request_api("GET", "/health", base_url="http://test", transport=httpx.MockTransport(handler)) == {"status": "ready"}
    assert requests == [("GET", "/health")]


def test_provider_credit_error_is_actionable_without_exposing_credentials(database):
    conn, dsn, settings = database
    settings = replace(settings, database_url=dsn, embedding_dim=3)
    populate(conn, settings)
    reindex(conn, settings, FakeProvider)

    class UnavailableLLM(FakeLLM):
        def generate(self, prompt):
            raise GenerationUnavailable("LLM provider request failed", "credit_balance_exhausted")

    with TestClient(create_app(settings, FakeProvider, UnavailableLLM)) as client:
        response = client.post("/ask", json={"question": "runway"})
        assert response.status_code == 502
        assert response.json() == {"detail": {"message": "LLM generation unavailable", "code": "credit_balance_exhausted"}}
