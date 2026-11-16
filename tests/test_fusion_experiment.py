from copy import deepcopy

import pytest

from safelens.fusion_experiment import fuse_weighted
from safelens.retrieve import RetrievalConfig, aggregate, fuse


def legs():
    lexical = aggregate([("1", 1, "a", 8), ("2", 2, "b", 4), ("4", 4, "d", 2)], "lexical", 50)
    dense = aggregate([("2", 2, "b", .9), ("3", 3, "c", .7), ("1", 1, "a", .5)], "dense", 50)
    return lexical, dense


def test_equal_weight_rrf_reproduces_step6_hybrid():
    lexical, dense = legs()
    before = deepcopy((lexical, dense))
    actual = fuse_weighted(lexical, dense, 1, 1)
    expected = fuse(lexical, dense, RetrievalConfig())
    assert [{k: v for k, v in h.items() if k != "contributions"} for h in actual] == expected
    assert (lexical, dense) == before
    assert actual[0]["score"] == pytest.approx(1 / 61 + 1 / 62)


@pytest.mark.parametrize("family", ["weighted_rrf", "normalized_scores"])
def test_zero_lexical_weight_reproduces_dense_exactly(family):
    lexical, dense = legs()
    assert fuse_weighted(lexical, dense, 1, 0, family) == dense
    assert fuse_weighted(lexical, dense, 0, 1, family) == lexical
    assert fuse_weighted(lexical, [], 1, 0, family) == []


def test_normalized_scores_use_whole_leg_and_zero_for_missing_constant():
    lexical, dense = legs()
    result = fuse_weighted(lexical, dense, 2, 1, "normalized_scores")
    by_acn = {h["acn"]: h for h in result}
    assert by_acn["2"]["score"] == pytest.approx(2 + 2 / 6)
    assert by_acn["3"]["score"] == pytest.approx(1)
    constant = aggregate([("9", 9, "x", 2), ("8", 8, "y", 2)], "lexical", 50)
    tied = fuse_weighted(constant, [], 1, 1, "normalized_scores")
    assert [h["acn"] for h in tied] == ["8", "9"]
    assert [h["score"] for h in tied] == [0, 0]
    with pytest.raises(ValueError):
        fuse_weighted(lexical, dense, 0, 0)
