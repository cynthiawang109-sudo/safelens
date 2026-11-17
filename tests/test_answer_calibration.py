from safelens.agent import GRADE_TASK
from safelens.generate import INSTRUCTIONS, AnswerDraft, generate_answer


def fixture():
    hits = [{"acn": "123", "chunk_id": 1, "text": "Synopsis. Crew reported an instrument failure.",
             "ranks": {"lexical": 1, "dense": 1},
             "components": {"dense": {"chunk_id": 1, "text": "Synopsis. Crew reported an instrument failure."}}}]
    reports = {"123": {"report_month": "2020-01", "source_dataset": "fixture", "source_revision": "fixture"}}
    return hits, reports


def test_calibrated_prompts_pin_mechanism_partial_and_hard_refusals():
    assert "AT LEAST ONE relevant report" in GRADE_TASK
    assert "Other irrelevant\nreports do not veto" in GRADE_TASK
    assert "Sufficient requires ALL" not in GRADE_TASK
    assert "A grounded partial answer is a successful response" in INSTRUCTIONS
    assert "Requests for an unavailable exact day/clock time" in INSTRUCTIONS
    assert "Absent named identifiers and out-of-domain requests" in INSTRUCTIONS
    assert "reporter accounts, NOT confirmed findings" in INSTRUCTIONS
    assert "never combine conditions from different reports" in INSTRUCTIONS


def test_explicit_partial_is_not_a_refusal_due_to_missing_detail_phrase():
    class LLM:
        def generate_structured(self, prompt, schema):
            assert schema is AnswerDraft
            return AnswerDraft(status="partial", answer="The crew reported instrument failure [123]. There is insufficient evidence for an exact day."), {}
    hits, reports = fixture()
    response = generate_answer("Instrument failure mechanism", hits, reports, LLM())
    assert response["status"] == "partial" and response["citations"]
    assert not response["validation"]["flagged"]


def test_structured_answer_cannot_bypass_fail_closed_citations():
    class LLM:
        def generate_structured(self, prompt, schema):
            return AnswerDraft(status="answered", answer="An invented finding [999]."), {}
    hits, reports = fixture()
    response = generate_answer("Question", hits, reports, LLM())
    assert response["status"] == "insufficient_evidence"
    assert response["answer"] == "insufficient evidence."
    assert response["validation"]["invalid_acns"] == ["999"]


def test_uncited_partial_cannot_count_as_supported_answer():
    class LLM:
        def generate_structured(self, prompt, schema):
            return AnswerDraft(status="partial", answer="The crew had an instrument failure."), {}
    hits, reports = fixture()
    response = generate_answer("Question", hits, reports, LLM())
    assert response["status"] == "insufficient_evidence"
    assert response["validation"]["missing_citations"]
