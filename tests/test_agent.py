import json
from dataclasses import replace

import pytest
from test_chunk_embed import FakeProvider
from test_retrieval_index import populate

from safelens.agent import AgentEngine, EvidenceGrade
from safelens.aggregate import execute_count, map_count_filters
from safelens.reindex import reindex


class InsufficientLLM:
    def __init__(self):
        self.rewrites = 0

    def generate_structured(self, prompt, schema):
        if schema is EvidenceGrade:
            data = json.loads(prompt.split("\nReporter accounts are unverified, not confirmed findings.\n")[1])
            value = {"reports": [{"acn": a, "relevance": 0, "supports_requested_fact": False, "reason": "Unsupported"}
                                 for a in sorted({p["acn"] for p in data["passages"]})],
                     "sufficiency": "insufficient", "reason": "Unsupported request"}
        else:
            self.rewrites += 1
            value = {"query": f"runway rewrite {self.rewrites}"}
        return schema.model_validate(value), {"input_tokens": 10, "output_tokens": 5}

    def generate(self, prompt):
        raise AssertionError("Insufficient evidence must abstain without generation")


def test_agent_rewrite_cap_and_complete_trace(database):
    conn, _, settings = database
    settings = replace(settings, embedding_dim=3)
    populate(conn, settings)
    reindex(conn, settings, FakeProvider)
    llm = InsufficientLLM()
    result = AgentEngine(conn, settings, FakeProvider(settings), llm).run("runway")
    assert result["status"] == "insufficient_evidence"
    assert result["usage"]["retries"] == 2 and result["usage"]["model_calls"] == 5
    assert llm.rewrites == 2
    stages = [e["stage"] for e in result["trace"]]
    assert stages.count("retrieve") == stages.count("grade") == 3
    assert stages.count("rewrite") == 2
    assert result["usage"]["input_tokens"] == 50
    assert all(e["latency_ms"] >= 0 for e in result["trace"])
    strategies = [e["detail"]["strategy"] for e in result["trace"] if e["stage"] == "rewrite"]
    assert strategies[0] != strategies[1]


def test_aggregate_sql_and_unknown_filter_fallback(database):
    conn, _, settings = database
    settings = replace(settings, embedding_dim=3)
    populate(conn, settings)
    reindex(conn, settings, FakeProvider)
    filters = map_count_filters("How many reports in 2015?")
    counted = execute_count(conn, filters)
    assert counted["count"] == counted["denominator"] == 3
    assert "%s" in counted["sql"] and counted["parameters"][:2] == [2015, 2015]
    assert map_count_filters("How many reports from Toronto in 2015?") is None
    assert map_count_filters("How many reports between 2020 and 2015?") is None
    result = AgentEngine(conn, settings, FakeProvider(settings), InsufficientLLM()).run("How many reports in 2015?")
    assert result["status"] == "answered" and result["aggregate"]["count"] == 3
    assert result["usage"]["model_calls"] == 0
    fallback = AgentEngine(conn, settings, FakeProvider(settings), InsufficientLLM()).run("How many reports from Toronto in 2015?")
    assert fallback["status"] == "partial" and fallback["aggregate"] is None
    assert "no count was estimated" in fallback["answer"]


@pytest.mark.parametrize("cap", [1, 3, 6])
def test_partial_evidence_respects_total_model_call_cap(database, cap):
    conn, _, settings = database
    settings = replace(settings, embedding_dim=3, agent_max_calls=cap)
    populate(conn, settings)
    reindex(conn, settings, FakeProvider)

    class Partial(InsufficientLLM):
        def generate_structured(self, prompt, schema):
            from safelens.generate import AnswerDraft
            if schema is AnswerDraft:
                return AnswerDraft(status="partial", answer=self.generate(prompt)), {"input_tokens": 10, "output_tokens": 5}
            value, usage = super().generate_structured(prompt, schema)
            if schema is EvidenceGrade:
                value.sufficiency = "partial"
                for report in value.reports:
                    report.relevance = 1
                    report.supports_requested_fact = True
            return value, usage

        def generate(self, prompt):
            return "The reporter described a runway event [100]."

    result = AgentEngine(conn, settings, FakeProvider(settings), Partial()).run("runway")
    assert result["usage"]["model_calls"] <= cap
    assert result["usage"]["retries"] <= 2
    if cap == 6:
        assert result["usage"]["model_calls"] == 6 and result["status"] == "partial"
