"""Validate the real Step 2 index and show one query through all retrievers."""

import json
import platform
from dataclasses import asdict, replace
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

import psycopg
from psycopg.rows import dict_row

from safelens.config import Settings
from safelens.embed import LocalEmbeddingProvider
from safelens.ingest import require_active_index
from safelens.retrieve import (
    RetrievalConfig,
    search_dense,
    search_hybrid,
    search_lexical,
)


def main():
    settings = Settings.from_env()
    provider = LocalEmbeddingProvider(settings)
    query = "TCAS RA"
    config = RetrievalConfig()
    with psycopg.connect(settings.database_url, autocommit=True, connect_timeout=10) as conn:
        require_active_index(conn, settings)
        counts = conn.execute("SELECT count(*), count(DISTINCT acn) FROM chunks").fetchone()
        assert counts[1] == conn.execute("SELECT count(*) FROM reports").fetchone()[0] == 1000
        assert not conn.execute(
            "SELECT 1 FROM chunks GROUP BY acn, chunk_idx HAVING count(*) > 1"
        ).fetchone()
        assert not conn.execute(
            "SELECT 1 FROM chunks c JOIN reports r USING(acn) WHERE "
            "c.anomaly_codes IS DISTINCT FROM r.anomaly_codes OR "
            "c.flight_phase IS DISTINCT FROM r.flight_phase OR "
            "c.aircraft_category IS DISTINCT FROM r.aircraft_category OR "
            "c.report_month IS DISTINCT FROM r.report_month OR "
            "c.report_year IS DISTINCT FROM r.report_year"
        ).fetchone()
        rows = conn.execute(
            "SELECT c.text, r.synopsis, vector_dims(c.embedding), "
            "c.chunk_idx = max(c.chunk_idx) OVER (PARTITION BY c.acn) AS final_chunk "
            "FROM chunks c JOIN reports r USING(acn)"
        ).fetchall()
        lengths = []
        for text, synopsis, dimension, final_chunk in rows:
            assert text.startswith(synopsis + "\n\n" if synopsis else "")
            assert dimension == provider.dimension
            length = provider.count_tokens(text)
            assert length <= min(settings.chunk_tokens, provider.max_tokens)
            assert final_chunk or length >= 400
            lengths.append(length)
        samples, timings, deep_samples = {}, {}, {}
        for name, function in (("lexical", search_lexical), ("dense", search_dense), ("hybrid", search_hybrid)):
            extra = {} if name == "lexical" else {"provider": provider}
            start = perf_counter()
            hits = function(query, 5, conn=conn, settings=settings, config=config, **extra)
            timings[name] = round((perf_counter() - start) * 1000, 2)
            assert len(hits) == len({hit["acn"] for hit in hits}) == 5
            repeat = function(query, 5, conn=conn, settings=settings, config=config, **extra)
            assert hits == repeat
            samples[name] = hits
            deep_samples[name] = function(
                query, 5, conn=conn, settings=settings,
                config=replace(config, candidate_chunks=200), **extra,
            )
        with conn.cursor(row_factory=dict_row) as cursor:
            build = cursor.execute("SELECT * FROM index_meta WHERE status='ready'").fetchone()
        build["built_at"] = build["built_at"].isoformat()
        # Source passages remain in ignored data/. Version only aggregate evidence and ranks.
        Path("data/step2_sample_results.json").write_text(
            json.dumps({"query": query, "results": samples}, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        summary = {
            "timestamp": datetime.now(UTC).isoformat(),
            "hardware": platform.processor(), "platform": platform.platform(),
            "active_build": build, "reports": counts[1], "chunks": counts[0],
            "token_counts": {"min": min(lengths), "max": max(lengths),
                             "mean": round(sum(lengths) / len(lengths), 2),
                             "below_400": sum(length < 400 for length in lengths)},
            "query": query, "category_filter": None, "retrieval_config": asdict(config),
            "latency_ms_single_run_excludes_model_load_not_p95": timings,
            "samples": {name: [{key: hit[key] for key in ("acn", "chunk_id", "score", "ranks")}
                               for hit in hits] for name, hits in samples.items()},
            "candidate_chunks_200_top5": {name: [hit["acn"] for hit in hits]
                                          for name, hits in deep_samples.items()},
            "candidate_depth_changes_top5": {name: [h["acn"] for h in samples[name]] !=
                                            [h["acn"] for h in deep_samples[name]] for name in samples},
            "checks": {"token_budget_and_synopsis": "passed", "nonfinal_chunks_at_least_400": "passed",
                       "chunk_metadata": "passed",
                       "unique_report_results": "passed", "repeat_queries_identical": "passed"},
        }
        Path("docs/STEP2_VALIDATION.json").write_text(
            json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
