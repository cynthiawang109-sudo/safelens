"""Step 6: fixed-design, text-only lexical bake-off on the ready 20k corpus."""

import hashlib
import importlib.metadata
import json
import math
import platform
import random
from dataclasses import asdict
from datetime import UTC, datetime
from functools import partial
from pathlib import Path
from statistics import mean
from time import perf_counter

import psycopg
from psycopg.rows import dict_row
from run_eval import category_metrics, file_hash, load_queries, write_pool
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS

from safelens.config import Settings
from safelens.embed import LocalEmbeddingProvider
from safelens.evaluation import load_qrels
from safelens.ingest import require_active_index
from safelens.lexical_bakeoff import BM25Reference, coverage_metrics, search_variant
from safelens.reindex import LOCK
from safelens.retrieve import RetrievalConfig, search_dense

PROTECTED = ["src/safelens/retrieve.py", "src/safelens/generate.py", "src/safelens/llm.py",
             "eval/queries.jsonl", "eval/qrels.jsonl", "eval/subset_manifest.json",
             "eval/corpus_manifest_20k.json", "eval/judging_pool.csv"]


def render(record):
    lines = ["<!-- lexical-bakeoff-step6 -->", "# Step 6: lexical bake-off (development)", "",
             ("20,000 reports; 28,306 chunks; ready build 4. Text-only retrieval, no category filter. "
             "All 28 category queries are the primary development selection metric; no final test set was used."), "",
             ("All lexical and dense legs fetch at most 100 chunks, fold by ACN using maximum chunk score, "
             "then retain 50 reports. Hybrid uses report-level RRF k=60, ties by ACN. Underfills are not padded."), "",
             "## Layer-1 and latency", "",
             ("Category agreement is a weak-label measure, not human relevance. Latency: one local run over "
             "all 31 queries in file order, warmed query model, mean and nearest-rank p95; includes query "
             "embedding and retrieval, excludes initialization, BM25 indexing, and generation. Each hybrid "
             "executes its own lexical and dense calls; no cached rankings or embeddings in timed retrieval."), "",
             "| Configuration | Category P@10 | Hit@10 | Mean ms | p95 ms |",
             "|---|---:|---:|---:|---:|"]
    for name, summary in record["summary"].items():
        latency = record["latency_ms"][name]
        lines.append(f"| {name} | {summary['category_precision_at_10']:.4f} | {summary['hit_at_10']:.4f} | {latency['mean']:.2f} | {latency['p95']:.2f} |")
    lines += ["", "## Recommendation", "", record["recommendation"], "",
              ("This selection uses the primary metric only, with mean latency as a prespecified tie-break. "
              "Development margins are descriptive; 28 queries do not establish general superiority. "
              "Production defaults remain unchanged pending Cynthia's decision. No pg_search integration or Step 7 work."), "",
              "## Partial-coverage development signals", "",
              ("These are **partial-coverage development signals**, not comparable full-coverage scores. "
              "For each query, remove unjudged results from the original top ten; P@10 here means relevant/judged "
              "(a judged-only precision proxy, not conventional fixed-denominator P@10). MRR uses condensed ranks; "
              "nDCG uses linear gains and the known-qrels ideal at the same judged depth. Unknowns never get grade 0. "
              "Zero judged hits gives undefined metrics (N/A), excluded from macro averages; contributing query counts "
              "are printed. Coverage is judged/10, including underfill; returned-result coverage is also in JSON. "
              "Condensation is optimistic and the old pooled judgments favor the original methods; do not select on these numbers."), "",
              "| Configuration | Judged-only P@10 (coverage) | Condensed MRR (coverage) | Condensed nDCG@10 (coverage) | Queries defined / 8 |",
              "|---|---:|---:|---:|---:|"]
    def value(v):
        return "N/A" if v is None else f"{v:.4f}"
    for name, row in record["layer2_summary"].items():
        cells = [f"{value(row[m])} ({row['coverage_at_10']:.1%})" for m in ("precision_at_10", "mrr", "ndcg_at_10")]
        lines.append(f"| {name} | " + " | ".join(cells) + f" | {row['defined_queries']} |")
    lines += ["", "## Per-query Layer-1", "", "| Query | Configuration | Returned | Category P@10 | Hit@10 |",
              "|---|---|---:|---:|---:|"]
    for row in record["layer1_per_query"]:
        lines.append(f"| {row['query_id']} | {row['method']} | {row['retrieved']} | {row['category_precision_at_10']:.3f} | {row['hit_at_10']} |")
    lines += ["", "## Per-query partial-coverage development signals", "",
              "| Query | Configuration | Judged / returned | P@10 proxy (coverage) | MRR (coverage) | nDCG@10 (coverage) |",
              "|---|---|---:|---:|---:|---:|"]
    for row in record["layer2_per_query"]:
        cells = [f"{value(row[m])} ({row['coverage_at_10']:.0%})" for m in ("precision_at_10", "mrr", "ndcg_at_10")]
        lines.append(f"| {row['query_id']} | {row['method']} | {row['judged']} / {row['returned']} | " + " | ".join(cells) + " |")
    lines += ["", "## Reproduction and controls", "",
              ("Run `uv run python eval/run_lexical_bakeoff.py` with UTF-8 environment variables set. "
              "The full versioned record is `eval/experiment_step6.json`; detailed evidence rankings stay "
              "in ignored `data/eval_rankings_step6.json`. Original experiment and Step 5 tables are preserved."), "",
              ("FTS-AND calls the unchanged production implementation. OR uses lowercase ASCII alphanumeric content "
              "terms minus sklearn's fixed English stoplist, deduplicated and joined with `|`, PostgreSQL simple "
              "configuration and ts_rank_cd. Stopword-only input returns no matches. No stemming or query expansion."), "",
              ("BM25 reference uses [rank_bm25 BM25Okapi](https://github.com/dorianbrown/rank_bm25) 0.2.2 "
              "(k1=1.5, b=0.75, epsilon=0.25), identical content-term preprocessing for chunk texts and queries, "
              "no labels. Nonpositive scores excluded. These are three complete lexical configurations, not a "
              "controlled scoring-formula-only ablation. BM25 is offline/evaluation-only and needs a fresh "
              "in-memory index each run. Indexing time and software versions are in the experiment record."), "",
              (f"Winner pool: `{record['winner_pool']['path']}`, {record['winner_pool']['rows']} unjudged pairs "
              f"from **{record['winning_configuration']}** only, blinded and shuffled (seed 20261121), blank grades/notes. "
              "No human judgments were created. Original queries, qrels, corpus manifests, production retrieval "
              "and generation hashes were verified unchanged."), ""]
    return "\n".join(lines)


def main():
    protected = {p: file_hash(p) for p in PROTECTED}
    settings = Settings.from_env()
    queries = load_queries(Path("eval/queries.jsonl"))
    qrels = load_qrels("eval/qrels.jsonl", {q["id"] for q in queries if q["layer"] == 2})
    designation = json.loads(Path("eval/current_corpus.json").read_text(encoding="utf-8"))
    manifest = json.loads(Path(designation["manifest"]).read_text(encoding="utf-8"))
    provider = LocalEmbeddingProvider(settings)
    config = RetrievalConfig()
    with psycopg.connect(settings.database_url, autocommit=True) as conn:
        if not conn.execute("SELECT pg_try_advisory_lock_shared(%s)", (LOCK,)).fetchone()[0]:
            raise RuntimeError("Offline build active")
        try:
            require_active_index(conn, settings)
            with conn.cursor(row_factory=dict_row) as cursor:
                reports = {r["acn"]: r for r in cursor.execute('SELECT * FROM reports ORDER BY acn COLLATE "C"')}
                index = cursor.execute("SELECT * FROM index_meta WHERE status='ready'").fetchone()
            snapshot = hashlib.sha256("".join(f"{a}:{r['content_hash']}\n" for a, r in reports.items()).encode("utf-8")).hexdigest()
            counts = conn.execute("SELECT count(*),count(embedding) FROM chunks").fetchone()
            if (len(reports) != 20000 or sorted(reports) != manifest["selected_acns"]
                    or snapshot != manifest["snapshot_sha256"] or counts[0] != counts[1]
                    or index["report_count"] != 20000):
                raise ValueError("Ready 20k corpus validation failed")
            started = perf_counter()
            reference = BM25Reference(conn.execute('SELECT acn,id,text FROM chunks ORDER BY acn COLLATE "C",id').fetchall())
            indexing_ms = (perf_counter() - started) * 1000
            searchers = {}
            for variant in ("fts-and", "fts-or", "bm25-ref"):
                for hybrid in (False, True):
                    name = ("hybrid-" if hybrid else "lexical-") + variant
                    searchers[name] = partial(search_variant, variant=variant, hybrid=hybrid, reference=reference)
            searchers["dense"] = search_dense
            provider.embed_query("aviation safety")
            rankings, timings = {}, {name: [] for name in searchers}
            for q in queries:
                rankings[q["id"]] = {}
                for name, search in searchers.items():
                    started = perf_counter()
                    hits = search(q["query"], 10, conn=conn, settings=settings, provider=provider, config=config)
                    timings[name].append((perf_counter() - started) * 1000)
                    if len(hits) > 10 or len({h["acn"] for h in hits}) != len(hits):
                        raise ValueError("Report ranking contract violated")
                    rankings[q["id"]][name] = hits
            rows = category_metrics(queries, rankings, {a: r["anomaly_codes"] for a, r in reports.items()})
            summary = {name: {m: mean(r[m] for r in rows if r["method"] == name)
                              for m in ("category_precision_at_10", "hit_at_10")} for name in searchers}
            latency = {name: {"mean": mean(v), "p95": sorted(v)[math.ceil(.95 * len(v))-1], "samples": v} for name, v in timings.items()}
            layer2 = [{"query_id": q["id"], "method": name, **coverage_metrics(hits, q["id"], qrels)}
                      for q in queries if q["layer"] == 2 for name, hits in rankings[q["id"]].items()]
            signals = {}
            for name in searchers:
                selected = [r for r in layer2 if r["method"] == name]
                defined = [r for r in selected if r["judged"]]
                signals[name] = {m: mean(r[m] for r in defined) if defined else None for m in ("precision_at_10", "mrr", "ndcg_at_10")}
                signals[name].update(coverage_at_10=mean(r["coverage_at_10"] for r in selected), defined_queries=len(defined))
            winner = min((n for n in searchers if n.startswith("lexical-")), key=lambda n: (-summary[n]["category_precision_at_10"], latency[n]["mean"], n))
            combination = winner.replace("lexical-", "hybrid-", 1)
            delta = summary[combination]["category_precision_at_10"] - summary["dense"]["category_precision_at_10"]
            configuration = winner  # Only the selected lexical configuration's unjudged pairs.
            pool = [{"query_id": q["id"], "acn": h["acn"], "synopsis": reports[h["acn"]]["synopsis"], "grade": "", "note": ""}
                    for q in queries if q["layer"] == 2 for h in rankings[q["id"]][configuration]
                    if (q["id"], h["acn"]) not in qrels]
            random.Random(20261121).shuffle(pool)
            pool_path = Path("eval/judging_pool_step6_additions.csv")
            write_pool(pool_path, pool, preserve_judgments=True)
            if protected != {p: file_hash(p) for p in PROTECTED}:
                raise RuntimeError("Protected assets changed")
            recommendation = (f"Recommend **{winner}** as the lexical leg on the primary metric. "
                              f"Its hybrid **{combination}** changes Category P@10 versus dense by **{delta:+.4f}** "
                              f"({'beats' if delta > 0 else 'does not beat'} dense). "
                              "BM25 improves lexical Category P@10 over OR by "
                              f"{summary[winner]['category_precision_at_10'] - summary['lexical-fts-or']['category_precision_at_10']:+.4f}, "
                              "but the measured fusion does not justify replacing dense alone. "
                              "Defer a pg_search integration until a production lexical/fusion change is justified. "
                              "Adoption is a separate decision; BM25 production integration is not implemented.")
            index["built_at"] = index["built_at"].isoformat()
            record = {"timestamp": datetime.now(UTC).isoformat(), "split": "development", "unfiltered": True,
                      "corpus": {"reports": len(reports), "chunks": counts[0], "snapshot_sha256": snapshot, "manifest": designation["manifest"]},
                      "index": index, "retrieval_config": asdict(config), "protected_sha256": protected,
                      "tokenization": "lowercase ASCII alphanumeric; sklearn English stoplist; no stemming",
                      "stopwords_sha256": hashlib.sha256("\n".join(sorted(ENGLISH_STOP_WORDS)).encode()).hexdigest(),
                      "bm25": {"implementation": "rank-bm25 BM25Okapi", "k1": 1.5, "b": .75, "epsilon": .25, "indexing_ms": indexing_ms},
                      "query_order": [q["id"] for q in queries], "method_order": list(searchers),
                      "summary": summary, "layer1_per_query": rows, "layer2_summary": signals, "layer2_per_query": layer2,
                      "latency_ms": latency, "recommendation": recommendation, "winning_lexical": winner,
                      "winning_configuration": configuration, "winner_pool": {"path": str(pool_path), "rows": len(pool), "shuffle_seed": 20261121},
                      "hardware": platform.platform(), "python": platform.python_version(),
                      "software": {n: importlib.metadata.version(n) for n in ("rank-bm25", "scikit-learn", "psycopg", "sentence-transformers", "torch")}}
            Path("eval/experiment_step6.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
            Path("data/eval_rankings_step6.json").write_text(json.dumps(rankings), encoding="utf-8")
            notes = render(record)
            Path("docs/STEP6_NOTES.md").write_text(notes, encoding="utf-8")
            results = Path("eval/results.md")
            previous = results.read_text(encoding="utf-8").split("<!-- lexical-bakeoff-step6 -->")[0]
            results.write_text(previous.rstrip() + "\n\n" + notes, encoding="utf-8")
            print(json.dumps({"summary": summary, "recommendation": recommendation, "winner_pool": record["winner_pool"]}, indent=2))
        finally:
            conn.execute("SELECT pg_advisory_unlock_shared(%s)", (LOCK,))


if __name__ == "__main__":
    main()
