import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location("final_run_support", Path("eval/final_run_support.py"))
support = importlib.util.module_from_spec(spec)
spec.loader.exec_module(support)


def test_single_run_marker_forbids_second_attempt(tmp_path):
    path = tmp_path / "once.json"
    support.reserve_once(path, {"run_id": "original"})
    with pytest.raises(FileExistsError):
        support.reserve_once(path, {"run_id": "retry"})
    assert "original" in path.read_text(encoding="utf-8")


def test_citation_precision_keeps_unknown_pairs_out_of_error_denominator():
    response = {"status": "partial", "citations": [{"acn": "1"}, {"acn": "2"}, {"acn": "3"}, {"acn": "1"}]}
    row = support.citation_precision("fixture", response, {("fixture", "1"): 2, ("fixture", "2"): 0})
    assert row["precision_on_judged"] == .5
    assert row["judged_coverage"] == pytest.approx(2/3)
    assert row["unknown_acns"] == ["3"] and row["grade_zero_acns"] == ["2"]
    average = support.citation_average([row])
    assert average["judged_report_pairs"] == 2 and average["cited_report_pairs"] == 3


def test_unmapped_count_is_reported_as_failure_without_injecting_ground_truth():
    expected = {"count": 7, "denominator": 50, "filters": {"year_start": 2019}}
    response = {"status": "partial", "aggregate": None, "answer": "No count estimated.", "trace": []}
    comparison = support.count_comparison("fixture", response, expected)
    assert comparison["exact_match"] is False and comparison["system_aggregate"] is None
    response["aggregate"] = expected.copy()
    assert support.count_comparison("fixture", response, expected)["exact_match"] is True
