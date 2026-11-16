"""Step 6B: fixed-grid reranking over unchanged dense and BM25 report legs."""

import hashlib
import json
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean

import psycopg
from psycopg.rows import dict_row
from run_eval import category_metrics, file_hash, load_queries

from safelens.config import Settings
from safelens.embed import LocalEmbeddingProvider
from safelens.evaluation import load_qrels
from safelens.fusion_experiment import fuse_weighted
from safelens.ingest import require_active_index
from safelens.lexical_bakeoff import BM25Reference, coverage_metrics
from safelens.reindex import LOCK
from safelens.retrieve import RetrievalConfig, fuse, search_dense

DESIGN = Path("eval/step6b_design.json")
CACHE = Path("data/eval_rankings_step6b_candidates.json")
OLD_CACHE = Path("data/eval_rankings_step6.json")
PROTECTED = ["eval/queries.jsonl", "eval/qrels.jsonl", "eval/subset_manifest.json",
             "eval/corpus_manifest_20k.json", "eval/current_corpus.json",
             "src/safelens/retrieve.py", "src/safelens/generate.py", "src/safelens/llm.py",
             "src/safelens/embed.py", "src/safelens/chunk.py", "src/safelens/config.py",
             "src/safelens/lexical_bakeoff.py", "eval/experiment_step6.json",
             "eval/experiment.json", "docs/STEP6_NOTES.md"]


def acns(hits):
    return [h["acn"] for h in hits]


def selection_key(row):
    # Ratios, not arbitrary numeric scale, define relative lexical weight.
    return (-row["category_precision_at_10"], -row["hit_at_10"],
            row["lexical_weight"] / (row["dense_weight"] + row["lexical_weight"]))


def obtain_candidates(conn, settings, queries, provenance):
    old = json.loads(OLD_CACHE.read_text(encoding="utf-8")) if OLD_CACHE.exists() else None
    if CACHE.exists():
        saved = json.loads(CACHE.read_text(encoding="utf-8"))
        if saved["provenance"] != provenance:
            raise ValueError("Candidate cache provenance mismatch; refusing stale reranking")
        return saved["rankings"], ("reused complete Step 6B candidate recapture; "
                                  "original Step 6 cache contains only top ten, so both legs were captured once at full depth"), old
    if old and all(len(old[q["id"]][m]) == 50 for q in queries for m in ("dense", "lexical-bm25-ref")):
        rankings = {q["id"]: {m: old[q["id"]][m] for m in ("dense", "lexical-bm25-ref")} for q in queries}
        reason = "reused full Step 6 candidates"
    else:
        reason = ("Step 6 cache is top-ten-only, insufficient for 50-report candidate contract; "
                  "recaptured both unchanged legs once, verified historical top tens, then cached") if old else "Step 6 cache absent; captured both legs once"
        print(reason, flush=True)
        reference = BM25Reference(conn.execute('SELECT acn,id,text FROM chunks ORDER BY acn COLLATE "C",id').fetchall())
        provider = LocalEmbeddingProvider(settings)
        config = RetrievalConfig()
        rankings = {}
        for query in queries:
            qid = query["id"]
            dense = search_dense(query["query"], 50, conn=conn, settings=settings, provider=provider, config=config)
            lexical = reference.search(query["query"], config)
            rankings[qid] = {"dense": dense, "lexical-bm25-ref": lexical}
            if old:
                for method in ("dense", "lexical-bm25-ref"):
                    actual, previous = rankings[qid][method][:10], old[qid][method][:10]
                    if acns(actual) != acns(previous) or [h["chunk_id"] for h in actual] != [h["chunk_id"] for h in previous]:
                        raise ValueError(f"Historical Step 6 top ten not reproduced: {qid}/{method}")
                if acns(fuse(lexical, dense, config)[:10]) != acns(old[qid]["hybrid-bm25-ref"]):
                    raise ValueError(f"Historical Step 6 equal-weight hybrid not reproduced: {qid}")
            print(f"Captured {qid}: dense={len(dense)}, BM25={len(lexical)}", flush=True)
    CACHE.write_text(json.dumps({"provenance": provenance, "rankings": rankings}), encoding="utf-8")
    return rankings, reason, old


def partial_signals(queries, rankings, qrels):
    rows = [{"query_id": q["id"], **coverage_metrics(rankings[q["id"]], q["id"], qrels)}
            for q in queries if q["layer"] == 2]
    defined = [r for r in rows if r["judged"]]
    average = {m: mean(r[m] for r in defined) if defined else None for m in ("precision_at_10", "mrr", "ndcg_at_10")}
    average.update(coverage_at_10=mean(r["coverage_at_10"] for r in rows), defined_queries=len(defined), queries=len(rows))
    return {"averages": average, "per_query": rows}


def render(record):
    win = record["best"]
    versus = record["comparison_to_dense"]
    lines = ["<!-- fusion-bakeoff-step6b -->", "## Step 6B: fusion-weight mini bake-off (development)", "",
             (f"Corpus: {record['corpus']['reports']:,} reports, {record['corpus']['chunks']:,} embedded chunks; ready build {record['index']['id']}. "
             "All 28 category queries; no category filter, label retrieval features, query edits, or generation calls. These are development results, not final-test estimates."), "",
             "### Fixed protocol", "",
             ("The eight dense:lexical ratios and two families were fixed in `eval/step6b_design.json` before results. "
             "Each leg retains at most 50 reports after fetching 100 chunks and max-score aggregation by ACN. "
             "Weighted RRF uses wd/(60+rank_dense) + wl/(60+rank_lexical), missing components contribute zero; ties break by ACN. "
             "Normalized fusion applies per-query min-max to each complete candidate leg, then wd*d + wl*l; absent reports "
             "and constant-score legs contribute zero. Zero-weight legs are excluded, and pure-leg endpoints preserve the exact source ranking."), "",
             ("Select maximum Category P@10, then Hit@10, then smaller relative lexical weight wl/(wd+wl). "
             "Remaining exact ties are reported as co-winners; fixed family order only picks a display representative. "
             "No extra weights were tried. P@10 uses denominator 10, including underfill. Category agreement is not judged relevance."), "",
             (f"Candidate cache: {record['cache']['source']}. The original Step 6 cache is preserved. "
             "The full-depth recapture matches all original top-ten ACN orders and representative chunk IDs; equal-weight hybrid ACN orders also match Step 6. "
             "All grid trials subsequently use the identical cached lists; no retrieval per weight."), "",
             "### Full grid", "", "| Family | Dense:BM25 | Category P@10 | Hit@10 | Delta P@10 vs dense |",
             "|---|---:|---:|---:|---:|"]
    for row in record["grid"]:
        lines.append(f"| {row['family']} | {row['dense_weight']}:{row['lexical_weight']} | {row['category_precision_at_10']:.4f} | {row['hit_at_10']:.4f} | {row['category_precision_at_10'] - record['dense_reference']['category_precision_at_10']:+.4f} |")
    lines += ["", "### Best configuration and recommendation", "",
              (f"Display representative: **{win['family']} {win['dense_weight']}:{win['lexical_weight']}**. "
              f"Co-winners under the complete selection rule: {', '.join(record['co_winners'])}. "
              f"Category P@10 **{win['category_precision_at_10']:.4f}**, dense **{record['dense_reference']['category_precision_at_10']:.4f}**, "
              f"margin **{versus['mean_delta']:+.4f}** ({versus['net_matching_reports']:+d} matching reports across 280 slots). "
              f"Per-query **{versus['wins']} wins / {versus['losses']} losses / {versus['ties']} ties** versus dense."), "",
              record["recommendation"], "", record["concentration_note"], "",
              "Boundary-grid winner: **" + str(record["boundary_winner"]) + "** (" + record["boundary_kind"] + "). The grid was not extended. "
              "Production defaults and all production code paths remain unchanged; adopting any recommendation needs Cynthia's separate decision. Step 7 has not started.", "",
              "### Per-query comparison versus dense", "",
              "| Query | Dense Category P@10 | Best Category P@10 | Delta | Outcome |", "|---|---:|---:|---:|---|"]
    for row in versus["per_query"]:
        lines.append(f"| {row['query_id']} | {row['dense']:.3f} | {row['best']:.3f} | {row['delta']:+.3f} | {row['outcome']} |")
    lines += ["", "### Layer-2 partial-coverage development signals", "",
              "Uses the runtime `eval/qrels.jsonl` (" + record["qrels_sha256"] + "). "
              "Same Step 6 condensed protocol: remove unknown pairs from the original top ten; precision proxy is relevant/judged, "
              "MRR and DCG use condensed ranks, linear gains 2/1/0, ideal over known qrels at the same judged depth. "
              "No judged hits means undefined, excluded from macro means (query counts printed). Coverage = judged/10 including underfill; "
              "coverage of returned results is separately recorded in JSON. Unknowns never receive grade zero. "
              "These are **partial-coverage development signals**, not full-coverage scores and not used for selection. "
              "Condensation and the historical pooling can favor the original retrievers.", "",
              "| Configuration | Precision proxy (coverage) | Condensed MRR (coverage) | Condensed nDCG (coverage) | Defined queries / 8 |",
              "|---|---:|---:|---:|---:|"]
    def cell(value, coverage):
        return ("N/A" if value is None else f"{value:.4f}") + f" ({coverage:.1%})"
    for name, signal in record["layer2"].items():
        avg = signal["averages"]
        lines.append(f"| {name} | " + " | ".join(cell(avg[m], avg["coverage_at_10"]) for m in ("precision_at_10", "mrr", "ndcg_at_10")) + f" | {avg['defined_queries']} |")
    lines += ["", "| Query | Configuration | Judged / returned | Precision proxy (coverage) | MRR (coverage) | nDCG (coverage) |",
              "|---|---|---:|---:|---:|---:|"]
    for name, signal in record["layer2"].items():
        for row in signal["per_query"]:
            lines.append(f"| {row['query_id']} | {name} | {row['judged']} / {row['returned']} | " + " | ".join(cell(row[m], row["coverage_at_10"]) for m in ("precision_at_10", "mrr", "ndcg_at_10")) + " |")
    lines += ["", "### Reproduction and acceptance", "",
              ("Run `uv run python eval/run_fusion_bakeoff.py` with `PYTHONUTF8=1` and `PYTHONIOENCODING=utf-8`; "
              "set `HF_HUB_OFFLINE=1` for the already cached embedding model. Full configuration, all 448 grid/query rows, "
              "input and protected hashes, cache provenance, historical equivalence checks, and runtime qrels version are "
              "in `eval/experiment_step6b.json`. Detailed evidence stays in ignored `data/eval_rankings_step6b_candidates.json`. "
              "No corpus writes, reindexing, new judgments, production default changes, or additional grid trials."), ""]
    return "\n".join(lines)


def main():
    design = json.loads(DESIGN.read_text(encoding="utf-8"))
    if design["dense_lexical_weights"] != [[1, 0], [10, 1], [5, 1], [3, 1], [2, 1], [1, 1], [1, 2], [0, 1]]:
        raise ValueError("Weight grid must match kickoff exactly")
    protected = {p: file_hash(p) for p in PROTECTED}
    old_cache_hash = file_hash(OLD_CACHE)
    prior_results = Path("eval/results.md").read_text(encoding="utf-8").split("<!-- fusion-bakeoff-step6b -->")[0]
    queries = load_queries(Path("eval/queries.jsonl"))
    settings = Settings.from_env()
    designation = json.loads(Path("eval/current_corpus.json").read_text(encoding="utf-8"))
    manifest = json.loads(Path(designation["manifest"]).read_text(encoding="utf-8"))
    step6 = json.loads(Path("eval/experiment_step6.json").read_text(encoding="utf-8"))
    with psycopg.connect(settings.database_url, autocommit=True) as conn:
        if not conn.execute("SELECT pg_try_advisory_lock_shared(%s)", (LOCK,)).fetchone()[0]:
            raise RuntimeError("Offline build active")
        try:
            require_active_index(conn, settings)
            with conn.cursor(row_factory=dict_row) as cursor:
                reports = {r["acn"]: r for r in cursor.execute('SELECT acn,content_hash,anomaly_codes FROM reports ORDER BY acn COLLATE "C"')}
                index = cursor.execute("SELECT * FROM index_meta WHERE status='ready'").fetchone()
            counts = conn.execute("SELECT count(*),count(embedding),count(DISTINCT acn) FROM chunks").fetchone()
            snapshot = hashlib.sha256("".join(f"{a}:{r['content_hash']}\n" for a, r in reports.items()).encode()).hexdigest()
            if (len(reports) != 20000 or sorted(reports) != manifest["selected_acns"]
                    or snapshot != manifest["snapshot_sha256"] or counts[0] != counts[1]
                    or counts[2] != 20000 or index["report_count"] != 20000):
                raise ValueError("Ready 20k corpus validation failed")
            if snapshot != step6["corpus"]["snapshot_sha256"] or asdict(RetrievalConfig()) != step6["retrieval_config"]:
                raise ValueError("Step 6 corpus or candidate contract changed")
            for p in ("eval/queries.jsonl", "src/safelens/retrieve.py"):
                if file_hash(p) != step6["protected_sha256"][p]:
                    raise ValueError("Step 6 query/retrieval drift")
            provenance = {"snapshot_sha256": snapshot, "query_sha256": protected["eval/queries.jsonl"],
                          "index_config": settings.index_config, "retrieval_config": asdict(RetrievalConfig()),
                          "bm25_source_sha256": file_hash("src/safelens/lexical_bakeoff.py"), "step6_cache_sha256": old_cache_hash}
            candidates, source, old = obtain_candidates(conn, settings, queries, provenance)
        finally:
            conn.execute("SELECT pg_advisory_unlock_shared(%s)", (LOCK,))
    # Retrieval is finished. All sixteen trials below are pure, fixed-candidate reranking.
    rankings, grid, all_rows = {}, [], []
    equivalence = {"dense_endpoints": True, "equal_rrf_matches_step6": True}
    for family in design["families"]:
        for wd, wl in design["dense_lexical_weights"]:
            name = f"{family}:{wd}:{wl}"
            rankings[name] = {}
            for q in queries:
                qid = q["id"]
                legs = candidates[qid]
                for hits in legs.values():
                    if len(hits) > 50 or len(hits) != len(set(acns(hits))) or any(h["acn"] not in reports for h in hits):
                        raise ValueError("Invalid report candidates")
                hits = fuse_weighted(legs["lexical-bm25-ref"], legs["dense"], wd, wl, family)[:10]
                rankings[name][qid] = hits
                if wl == 0 and hits != legs["dense"][:10]:
                    raise ValueError("Dense endpoint mismatch")
                if (family == "weighted_rrf" and wd == wl == 1 and old
                        and acns(hits) != acns(old[qid]["hybrid-bm25-ref"])):
                    raise ValueError("Equal RRF fails Step 6 ranking equivalence")
            wrapped = {qid: {name: hits} for qid, hits in rankings[name].items()}
            rows = category_metrics(queries, wrapped, {a: r["anomaly_codes"] for a, r in reports.items()})
            all_rows.extend(rows)
            grid.append({"name": name, "family": family, "dense_weight": wd, "lexical_weight": wl,
                         "category_precision_at_10": mean(r["category_precision_at_10"] for r in rows),
                         "hit_at_10": mean(r["hit_at_10"] for r in rows)})
    best = min(grid, key=selection_key)
    co_winners = [r["name"] for r in grid if selection_key(r) == selection_key(best)]
    dense = next(r for r in grid if r["family"] == "weighted_rrf" and r["lexical_weight"] == 0)
    comparisons = []
    for q in queries:
        if q["category"] is None:
            continue
        a, b = (next(r["category_matches"] for r in all_rows if r["method"] == name and r["query_id"] == q["id"])
                for name in (dense["name"], best["name"]))
        comparisons.append({"query_id": q["id"], "dense": a / 10, "best": b / 10,
                            "delta": (b - a) / 10, "matching_reports_delta": b - a,
                            "outcome": "win" if b > a else "loss" if b < a else "tie"})
    delta = best["category_precision_at_10"] - dense["category_precision_at_10"]
    wins = sum(r["outcome"] == "win" for r in comparisons)
    losses = sum(r["outcome"] == "loss" for r in comparisons)
    qrels = load_qrels("eval/qrels.jsonl", {q["id"] for q in queries if q["layer"] == 2})
    recommendation = (f"Recommend adopting {best['family']} {best['dense_weight']}:{best['lexical_weight']} as the flagship default under the fixed primary selection rule: "
                      f"Category P@10 improves by {delta:+.4f} on this development set. Adoption remains a separate decision.") if delta > 0 else (
                      "Recommend keeping dense-only: no tested fusion improves the primary metric over dense under the fixed selection rule.")
    largest_gains = sorted((r for r in comparisons if r["matching_reports_delta"] > 0),
                           key=lambda r: (-r["matching_reports_delta"], r["query_id"]))[:2]
    net = sum(r["matching_reports_delta"] for r in comparisons)
    top_two = sum(r["matching_reports_delta"] for r in largest_gains)
    concentration = (
        f"Although {wins}/28 queries improve and {losses}/28 worsen, the net gain is only {net} matching reports. "
        f"The two largest positive flips ({', '.join(r['query_id'] for r in largest_gains)}) contribute {top_two} matches; "
        f"excluding those queries leaves {net - top_two:+d} net matches. "
        + ("The overall win therefore does rest on two query flips in aggregate; it is a fragile development margin, not broad evidence of superiority."
           if net - top_two <= 0 else "The positive margin survives excluding the two largest positive flips, but remains development-only evidence.")
    ) if delta > 0 else "There is no positive primary-metric margin to attribute to one or two query flips."
    if protected != {p: file_hash(p) for p in PROTECTED} or old_cache_hash != file_hash(OLD_CACHE):
        raise RuntimeError("Protected assets changed")
    index["built_at"] = index["built_at"].isoformat()
    record = {"timestamp": datetime.now(UTC).isoformat(), "split": "development", "design": design,
              "design_sha256": file_hash(DESIGN), "protected_sha256_before": protected,
              "protected_sha256_after": {p: file_hash(p) for p in PROTECTED}, "unfiltered": True,
              "corpus": {"reports": len(reports), "chunks": counts[0], "snapshot_sha256": snapshot},
              "index": index, "retrieval_config": asdict(RetrievalConfig()),
              "cache": {"path": str(CACHE), "sha256": file_hash(CACHE), "source": source,
                        "original_step6_sha256": old_cache_hash, "provenance": provenance},
              "equivalence_checks": equivalence, "grid": grid, "per_query": all_rows,
              "best": best, "co_winners": co_winners, "dense_reference": dense,
              "boundary_winner": best["lexical_weight"] == 0 or best["dense_weight"] == 0 or (best["dense_weight"], best["lexical_weight"]) == (10, 1),
              "boundary_kind": "dense-heaviest mixed ratio tested; pure-leg endpoints also evaluated" if (best["dense_weight"], best["lexical_weight"]) == (10, 1) else "pure-leg endpoint" if best["lexical_weight"] == 0 or best["dense_weight"] == 0 else "interior mixed ratio",
              "concentration": {"two_largest_gains": largest_gains, "net_after_excluding_two": net - top_two},
              "comparison_to_dense": {"wins": wins, "losses": losses, "ties": 28 - wins - losses,
                                      "mean_delta": delta, "net_matching_reports": sum(r["matching_reports_delta"] for r in comparisons), "per_query": comparisons},
              "qrels_sha256": protected["eval/qrels.jsonl"], "qrels_rows": len(qrels),
              "layer2": {"best": partial_signals(queries, rankings[best["name"]], qrels),
                         "dense": partial_signals(queries, rankings[dense["name"]], qrels)},
              "recommendation": recommendation, "concentration_note": concentration}
    notes = render(record)
    Path("eval/experiment_step6b.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    Path("docs/STEP6B_NOTES.md").write_text(notes, encoding="utf-8")
    Path("eval/results.md").write_text(prior_results.rstrip() + "\n\n" + notes, encoding="utf-8")
    print(json.dumps({"grid": grid, "best": best, "comparison": record["comparison_to_dense"], "recommendation": recommendation}, indent=2))


if __name__ == "__main__":
    main()
