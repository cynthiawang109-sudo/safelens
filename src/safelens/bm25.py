"""Production BM25Okapi leg, cached once per database/schema ready build."""

import re
import threading
from time import perf_counter

import psutil
from rank_bm25 import BM25Okapi
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS

_LOCK = threading.Lock()
_CACHE = {}


def content_terms(text):
    return [t for t in re.findall(r"[a-z0-9]+", text.lower()) if t not in ENGLISH_STOP_WORDS]


class BM25Index:
    def __init__(self, rows):
        self.rows = rows
        self.model = BM25Okapi([content_terms(r[2]) for r in rows], k1=1.5, b=.75, epsilon=.25)

    def search(self, query, config, allowed=None):
        from safelens.retrieve import aggregate
        terms = content_terms(query)
        if not terms:
            return []
        scores = self.model.get_scores(terms)
        indices = sorted((i for i, score in enumerate(scores) if score > 0
                          and (allowed is None or self.rows[i][0] in allowed)),
                         key=lambda i: (-scores[i], self.rows[i][0], self.rows[i][1]))
        return aggregate([(*self.rows[i], scores[i]) for i in indices[:config.candidate_chunks]],
                         "lexical", config.candidate_reports)


def ready_index(conn):
    build_id = conn.execute("SELECT id FROM index_meta WHERE status='ready'").fetchone()[0]
    namespace = (conn.info.host, conn.info.port, conn.info.dbname,
                 conn.execute("SELECT current_schema()").fetchone()[0])
    with _LOCK:
        cached = _CACHE.get(namespace)
        if cached is not None and cached[0] == build_id:
            return cached[1], cached[2]
        # Drop the stale build before allocating its replacement. Serving holds a
        # shared offline-build lock, so all rows below belong to this ready build.
        _CACHE.pop(namespace, None)
        process = psutil.Process()
        before = process.memory_info().rss
        started = perf_counter()
        index = BM25Index(conn.execute(
            'SELECT acn,id,text FROM chunks ORDER BY acn COLLATE "C",id').fetchall())
        stats = {"build_id": build_id, "chunks": len(index.rows),
                 "build_ms": (perf_counter() - started) * 1000,
                 "rss_delta_bytes": process.memory_info().rss - before,
                 "process_rss_bytes": process.memory_info().rss,
                 "memory_method": "process RSS after minus before loading chunk texts and building BM25; allocator-dependent"}
        _CACHE[namespace] = (build_id, index, stats)
        return index, stats


def search_bm25(conn, query, category, config):
    index, _ = ready_index(conn)
    allowed = None if category is None else {r[0] for r in conn.execute(
        "SELECT acn FROM reports WHERE %s=ANY(anomaly_codes)", (category,))}
    return index.search(query, config, allowed)
