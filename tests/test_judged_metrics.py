import csv
import json
import math

import pytest

from safelens.evaluation import import_judgments, judged_metrics, load_qrels


def test_toy_metric_math_and_unjudged_fails():
    queries = [{"id": "q", "layer": 2}]
    hits = [{"acn": str(i)} for i in range(1, 4)]
    rankings = {"q": {name: hits for name in ("lexical", "dense", "hybrid")}}
    qrels = {("q", "1"): 0, ("q", "2"): 1, ("q", "3"): 2}
    result = judged_metrics(queries, rankings, qrels)
    expected_ndcg = (1 / math.log2(3) + 2 / math.log2(4)) / (2 + 1 / math.log2(3))
    for values in result["averages"].values():
        assert values["precision_at_10"] == pytest.approx(.2)
        assert values["mrr"] == pytest.approx(.5)
        assert values["ndcg_at_10"] == pytest.approx(expected_ndcg)
    with pytest.raises(ValueError, match="Unjudged"):
        judged_metrics(queries, rankings, {("q", "2"): 1, ("q", "3"): 2})
    zeros = judged_metrics(queries, rankings, {key: 0 for key in qrels})
    assert zeros["averages"]["dense"] == {"precision_at_10": 0, "mrr": 0, "ndcg_at_10": 0}


def test_import_validates_without_creating_qrels_for_blank_grades(tmp_path):
    query_path, manifest, csv_path, output = [tmp_path / name for name in ("queries", "manifest", "pool.csv", "qrels.jsonl")]
    query_path.write_text('{"id":"q","layer":2}\n', encoding="utf-8")
    manifest.write_text('{"selected_acns":["123"]}', encoding="utf-8")

    def write_grade(grade):
        with csv_path.open("w", encoding="utf-8", newline="") as target:
            writer = csv.DictWriter(target, fieldnames=["query_id", "acn", "synopsis", "grade", "note"])
            writer.writeheader()
            writer.writerow({"query_id": "q", "acn": "123", "synopsis": "Synthetic", "grade": grade, "note": ""})

    write_grade("")
    with pytest.raises(ValueError, match="human grade"):
        import_judgments(csv_path, output, query_path, manifest)
    assert not output.exists()
    write_grade("2")
    with pytest.raises(ValueError, match="entire current judging pool"):
        import_judgments(csv_path, output, query_path, manifest, {("q", "123"), ("q", "456")})
    assert not output.exists()
    assert import_judgments(csv_path, output, query_path, manifest, {("q", "123")}) == 1
    assert load_qrels(output, {"q"}) == {("q", "123"): 2}
    with pytest.raises(FileExistsError):
        import_judgments(csv_path, output, query_path, manifest)
    output.write_text(json.dumps({"query_id": "q", "acn": "123", "grade": True}) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="integer"):
        load_qrels(output, {"q"})
