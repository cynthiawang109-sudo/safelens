import importlib.util
import json
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location("ci_gate", Path("eval/run_ci_gate.py"))
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


def test_judged_precision_excludes_unknown_pairs_and_reports_coverage():
    hits = [{"acn": str(n)} for n in range(10)]
    result = gate.judged_precision("dev", hits, {("dev", "0"): 2, ("dev", "1"): 0})
    assert result["precision_on_judged"] == .5
    assert result["coverage_at_10"] == .2
    assert len(result["missing_acns"]) == 8


def test_no_judgments_is_undefined_not_perfect_or_zero_filled():
    result = gate.judged_precision("dev", [{"acn": "1"}], {})
    assert result["precision_on_judged"] is None
    assert result["coverage_at_10"] == 0


def test_ci_refuses_spent_final_set_paths_before_reading_them():
    config = json.loads(Path("eval/gates.json").read_text(encoding="utf-8"))
    config["queries"] = "eval/queries_final.jsonl"
    with pytest.raises(ValueError, match="fixed development"):
        gate.load_development(config)
