"""Step 6B experiment only: weighted report-level fusion, no serving imports."""

import math
from copy import deepcopy


def fuse_weighted(lexical, dense, dense_weight, lexical_weight, family="weighted_rrf"):
    """Fuse fixed, unique-ACN report candidates without changing either leg."""
    if (not all(math.isfinite(w) and w >= 0 for w in (dense_weight, lexical_weight))
            or dense_weight + lexical_weight == 0):
        raise ValueError("Weights must be finite, nonnegative, and not both zero")
    if family not in ("weighted_rrf", "normalized_scores"):
        raise ValueError("Unknown fusion family")
    for leg in (lexical, dense):
        if len(leg) != len({hit["acn"] for hit in leg}):
            raise ValueError("Fusion requires unique report ACNs per leg")
    if lexical_weight == 0:
        return deepcopy(dense)
    if dense_weight == 0:
        return deepcopy(lexical)
    records = {}
    for name, hits, weight in (("lexical", lexical, lexical_weight), ("dense", dense, dense_weight)):
        low = min((h["score"] for h in hits), default=0)
        high = max((h["score"] for h in hits), default=0)
        for rank, hit in enumerate(hits, 1):
            row = records.setdefault(hit["acn"], {
                "acn": hit["acn"], "ranks": {"lexical": None, "dense": None},
                "components": {}, "contributions": {},
            })
            row["ranks"][name] = rank
            row["components"][name] = deepcopy(hit["components"][name])
            normalized = (hit["score"] - low) / (high - low) if high > low else 0.
            row["contributions"][name] = (
                weight / (60 + rank) if family == "weighted_rrf" else weight * normalized)
    for row in records.values():
        row["score"] = math.fsum(row["contributions"].values())
        # Match Step 6 representative evidence policy, regardless of fusion weight.
        winner = min(row["components"], key=lambda n: (row["ranks"][n], n != "lexical"))
        row["chunk_id"] = row["components"][winner]["chunk_id"]
        row["text"] = row["components"][winner]["text"]
    return sorted(records.values(), key=lambda h: (-h["score"], h["acn"]))
