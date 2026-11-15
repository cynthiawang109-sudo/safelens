from safelens.generate import build_prompt, select_evidence, validate_citations


def test_fabricated_acn_dropped_and_answer_flagged():
    evidence = [{"acn": "123", "chunk_id": 9, "passage": "An account."}]
    result = validate_citations("Reported a warning [123] and a made-up finding [999].", evidence)
    assert result["validation"]["flagged"] is True
    assert result["validation"]["invalid_acns"] == ["999"]
    assert result["answer"] == "insufficient evidence."
    assert result["citations"] == evidence
    assert all(item["acn"] != "999" for item in result["citations"])


def test_valid_citations_exact_passages_and_uncited_claim_rejected():
    evidence = [{"acn": "123", "chunk_id": 9, "passage": "An account."},
                {"acn": "123", "chunk_id": 10, "passage": "Another account."}]
    result = validate_citations("The reporter described a warning [123].", evidence)
    assert result["citations"] == evidence
    assert not result["validation"]["flagged"]
    assert validate_citations("A warning definitely happened.", evidence)["validation"]["missing_citations"]
    assert not validate_citations("insufficient evidence: the exact day is unavailable.", evidence)["validation"]["flagged"]
    refusal = validate_citations("An uncited, specific causal conclusion. But insufficient evidence overall.", evidence)
    assert refusal["answer"] == "insufficient evidence."


def test_context_contract_and_grounding_prompt():
    hits = [{"acn": str(i), "chunk_id": i * 10, "text": f"Best passage {i}",
             "ranks": {"lexical": i + 1, "dense": i + 1},
             "components": {"lexical": {"chunk_id": i * 10, "text": "best"},
                            "dense": {"chunk_id": i * 10 + 1, "text": "second"}}}
            for i in range(6)]
    evidence = select_evidence(hits)
    assert len(evidence) == 8
    assert {item["acn"] for item in evidence} == {"0", "1", "2", "3", "4"}
    assert all(sum(e["acn"] == str(i) for e in evidence) <= 2 for i in range(5))
    prompt = build_prompt("Question", evidence, {
        str(i): {"report_month": "2015-10", "source_dataset": "dataset", "source_revision": "revision"}
        for i in range(5)
    })
    assert "reporter accounts, NOT confirmed findings" in prompt
    assert "2015-10" in prompt and "insufficient evidence" in prompt
