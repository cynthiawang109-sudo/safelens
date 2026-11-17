"""Exact lexical/dense retrieval; aggregate chunks before report-level RRF."""

import math
from contextlib import contextmanager
from dataclasses import dataclass

from safelens.ingest import require_active_index
from safelens.reindex import LOCK


@dataclass(frozen=True)
class RetrievalConfig:
    candidate_chunks: int = 100
    candidate_reports: int = 50
    rrf_k: int = 60
    aggregation: str = "max_chunk_score_then_report_rrf; ties=acn; chunk_ties=id"

    def __post_init__(self):
        if min(self.candidate_chunks, self.candidate_reports, self.rrf_k) <= 0:
            raise ValueError("Candidate depths and RRF k must be positive")


@contextmanager
def _snapshot(conn, settings):
    if not conn.autocommit:
        raise ValueError("Retrieval requires an autocommit connection")
    if not conn.execute("SELECT pg_try_advisory_lock_shared(%s)", (LOCK,)).fetchone()[0]:
        raise RuntimeError("Offline reindex/ingest is active; retrieval unavailable")
    try:
        # Establish the snapshot only after obtaining the lock (DDL swaps may rewrite chunks).
        with conn.transaction():
            conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ")
            require_active_index(conn, settings)
            yield
    finally:
        conn.execute("SELECT pg_advisory_unlock_shared(%s)", (LOCK,))


def aggregate(rows, name, depth):
    """Keep best chunk per ACN, then rank reports; independent of input order."""
    best = {}
    for acn, chunk_id, text, score in rows:
        hit = {"acn": acn, "chunk_id": chunk_id, "text": text, "score": float(score)}
        old = best.get(acn)
        if old is None or (-hit["score"], chunk_id) < (-old["score"], old["chunk_id"]):
            best[acn] = hit
    reports = sorted(best.values(), key=lambda hit: (-hit["score"], hit["acn"]))[:depth]
    for rank, hit in enumerate(reports, 1):
        hit["ranks"] = {"lexical": None, "dense": None, name: rank}
        hit["components"] = {name: {key: hit[key] for key in ("chunk_id", "text", "score")}}
    return reports


def fuse(lexical, dense, config, dense_weight=1.0, lexical_weight=1.0):
    if (not all(math.isfinite(w) and w >= 0 for w in (dense_weight, lexical_weight))
            or dense_weight + lexical_weight <= 0):
        raise ValueError("RRF weights must be finite, nonnegative, and not both zero")
    if lexical_weight == 0:
        return dense
    if dense_weight == 0:
        return lexical
    by_acn = {}
    for name, reports in (("lexical", lexical), ("dense", dense)):
        for rank, hit in enumerate(reports, 1):
            record = by_acn.setdefault(hit["acn"], {
                "acn": hit["acn"], "ranks": {"lexical": None, "dense": None}, "components": {},
            })
            record["ranks"][name] = rank
            record["components"][name] = hit["components"][name]
    for hit in by_acn.values():
        weights = {"lexical": lexical_weight, "dense": dense_weight}
        hit["score"] = math.fsum(weights[name] / (config.rrf_k + rank)
                                 for name, rank in hit["ranks"].items() if rank is not None)
        # Representative evidence: better component rank; lexical wins equal rank.
        winner = min(hit["components"], key=lambda name: (hit["ranks"][name], name != "lexical"))
        hit["chunk_id"] = hit["components"][winner]["chunk_id"]
        hit["text"] = hit["components"][winner]["text"]
    return sorted(by_acn.values(), key=lambda hit: (-hit["score"], hit["acn"]))


def _lexical(conn, q, category, config):
    rows = conn.execute(
        "SELECT acn, id, text, ts_rank_cd(tsv, websearch_to_tsquery('simple', %s)) AS score "
        "FROM chunks WHERE tsv @@ websearch_to_tsquery('simple', %s) "
        "AND (%s::text IS NULL OR %s = ANY(anomaly_codes)) "
        "ORDER BY score DESC, acn COLLATE \"C\", id LIMIT %s",
        (q, q, category, category, config.candidate_chunks),
    ).fetchall()
    return aggregate(rows, "lexical", config.candidate_reports)


def _dense(conn, q, category, config, provider, dimension):
    vector = provider.embed_query(q)
    if (len(vector) != dimension or not all(math.isfinite(v) for v in vector)
            or not any(vector)):
        raise ValueError("Query embedding has invalid dimension/values")
    rows = conn.execute(
        "SELECT acn, id, text, 1 - (embedding <=> %s::vector) AS score "
        "FROM chunks WHERE embedding IS NOT NULL "
        "AND (%s::text IS NULL OR %s = ANY(anomaly_codes)) "
        "ORDER BY score DESC, acn COLLATE \"C\", id LIMIT %s",
        (str(vector), category, category, config.candidate_chunks),
    ).fetchall()
    return aggregate(rows, "dense", config.candidate_reports)


def _validate(q, k):
    if not isinstance(q, str) or not q.strip() or k <= 0:
        raise ValueError("Query must be nonempty and k positive")


def _production_lexical(conn, q, category, config, backend):
    if backend == "fts":
        return _lexical(conn, q, category, config)
    if backend != "bm25":
        raise ValueError("Unknown lexical backend")
    from safelens.bm25 import search_bm25
    return search_bm25(conn, q, category, config)


def search_lexical(q, k=10, *, conn, settings, category=None, config=RetrievalConfig(), backend=None):
    _validate(q, k)
    with _snapshot(conn, settings):
        return _production_lexical(conn, q, category, config, backend or settings.lexical_backend)[:k]


def search_dense(q, k=10, *, conn, settings, provider, category=None, config=RetrievalConfig()):
    _validate(q, k)
    with _snapshot(conn, settings):
        return _dense(conn, q, category, config, provider, settings.embedding_dim)[:k]


def search_hybrid(q, k=10, *, conn, settings, provider, category=None, config=RetrievalConfig()):
    _validate(q, k)
    with _snapshot(conn, settings):
        if settings.retrieval_mode == "dense" or settings.rrf_lexical_weight == 0:
            return _dense(conn, q, category, config, provider, settings.embedding_dim)[:k]
        lexical = _production_lexical(conn, q, category, config, settings.lexical_backend)
        if settings.rrf_dense_weight == 0:
            return lexical[:k]
        dense = _dense(conn, q, category, config, provider, settings.embedding_dim)
        return fuse(lexical, dense, config, settings.rrf_dense_weight, settings.rrf_lexical_weight)[:k]
