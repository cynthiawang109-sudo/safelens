"""Evaluation-only lexical alternatives. Production defaults remain unchanged."""

import math
import re

from rank_bm25 import BM25Okapi
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS

from safelens.retrieve import (
    RetrievalConfig,
    _dense,
    _lexical,
    _snapshot,
    _validate,
    aggregate,
    fuse,
)

DEFAULT_CONFIG = RetrievalConfig()


def content_terms(text):
    """Lowercase ASCII alphanumerics, fixed sklearn English stoplist, no stemming."""
    return [t for t in re.findall(r"[a-z0-9]+", text.lower()) if t not in ENGLISH_STOP_WORDS]


def or_tsquery(query):
    # Tokens cannot contain tsquery operators or quotes; SQL still parameterized.
    return " | ".join(f"'{term}'" for term in sorted(set(content_terms(query))))


def lexical_or(conn, query, config):
    expression = or_tsquery(query)
    if not expression:
        return []
    rows = conn.execute(
        "SELECT acn,id,text,ts_rank_cd(tsv,to_tsquery('simple',%s)) AS score "
        "FROM chunks WHERE tsv @@ to_tsquery('simple',%s) "
        'ORDER BY score DESC, acn COLLATE "C", id LIMIT %s',
        (expression, expression, config.candidate_chunks),
    ).fetchall()
    return aggregate(rows, "lexical", config.candidate_reports)


class BM25Reference:
    def __init__(self, rows):
        self.rows = rows  # acn, id, text only: labels cannot enter the index.
        self.model = BM25Okapi([content_terms(row[2]) for row in rows], k1=1.5, b=.75, epsilon=.25)

    def search(self, query, config):
        terms = content_terms(query)
        if not terms:
            return []
        scores = self.model.get_scores(terms)
        # Exclude nonmatching/zero-score chunks rather than pad with arbitrary ACNs.
        ordered = sorted((i for i, score in enumerate(scores) if score > 0),
                         key=lambda i: (-scores[i], self.rows[i][0], self.rows[i][1]))
        rows = [(*self.rows[i], scores[i]) for i in ordered[:config.candidate_chunks]]
        return aggregate(rows, "lexical", config.candidate_reports)


def search_variant(query, k=10, *, conn, settings, provider=None,
                   config=DEFAULT_CONFIG, variant="fts-and", hybrid=False, reference=None):
    """Same interface and candidate contract as production; no category argument."""
    _validate(query, k)
    with _snapshot(conn, settings):
        if variant == "fts-and":
            lexical = _lexical(conn, query, None, config)
        elif variant == "fts-or":
            lexical = lexical_or(conn, query, config)
        elif variant == "bm25-ref":
            lexical = reference.search(query, config)
        else:
            raise ValueError(f"Unknown lexical variant: {variant}")
        if hybrid:
            dense = _dense(conn, query, None, config, provider, settings.embedding_dim)
            return fuse(lexical, dense, config)[:k]
        return lexical[:k]


def coverage_metrics(hits, qid, qrels):
    """Condense judged top-ten only; unknowns removed, never assigned grade zero.

    P is relevant/judged (not conventional fixed-denominator P@10); MRR and
    DCG use condensed ranks. IDCG uses all known qrels for this query at the
    same judged depth. No judged hits -> undefined metrics, not zero.
    """
    grades = [qrels[(qid, h["acn"])] for h in hits[:10] if (qid, h["acn"]) in qrels]
    n = len(grades)
    ideal = sorted((g for (q, _), g in qrels.items() if q == qid), reverse=True)[:n]
    dcg = lambda values: sum(g / math.log2(i + 1) for i, g in enumerate(values, 1))
    return {"returned": len(hits[:10]), "judged": n, "coverage_at_10": n / 10,
            "coverage_of_returned": n / len(hits[:10]) if hits[:10] else None,
            "precision_at_10": sum(g >= 1 for g in grades) / n if n else None,
            "mrr": next((1 / i for i, g in enumerate(grades, 1) if g >= 1), 0.) if n else None,
            "ndcg_at_10": (dcg(grades) / dcg(ideal) if dcg(ideal) else 0.) if n else None}
