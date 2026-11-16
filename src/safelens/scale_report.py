"""Corpus-size comparison reporting; incomplete judgments are never grade zero."""


def missing_judgments(queries, rankings, qrels):
    return sorted({(q["id"], hit["acn"]) for q in queries if q["layer"] == 2
                   for hits in rankings[q["id"]].values() for hit in hits[:10]
                   if (q["id"], hit["acn"]) not in qrels})


def comparison(record, baseline):
    result = {"baseline_reports": baseline["corpus"]["reports"],
              "baseline_snapshot_sha256": baseline["corpus"]["snapshot_sha256"],
              "split": "development", "layer1": {}, "layer2": {}}
    for method, values in record["all_category_queries"].items():
        result["layer1"][method] = {}
        for metric in ("category_precision_at_10", "hit_at_10"):
            old = baseline["all_category_queries"][method][metric]
            result["layer1"][method][metric] = {"5000": old, "20000": values[metric], "delta": values[metric] - old}
    for method, values in baseline["judged_relevance"]["averages"].items():
        result["layer2"][method] = {}
        for metric, old in values.items():
            new = record["judged_relevance"].get("averages", {}).get(method, {}).get(metric)
            result["layer2"][method][metric] = {"5000": old, "20000": new,
                                               "delta": new - old if new is not None else None}
    return result


def render_scaleup(record):
    compared = record["comparison_to_5k"]
    lines = ["<!-- corpus-scaleup-20000 -->", "## 20,000-report corpus (development split)", "",
             f"Ready build **{record['index']['id']}**: **20,000 reports**, **{record['corpus']['chunks']:,} embedded chunks**. All 5,000 Mini ACNs retained; 15,000 year-stratified additions, seed {record['corpus']['selection_seed']}.",
             "Only corpus size changed. Retrieval, queries, prompts, generation, chunking, model/revision, and scoring definitions are unchanged. These are development results, not a frozen final test.",
             "The original Mini manifest, judging pool, and qrels are preserved. `current_corpus.json` designates `corpus_manifest_20k.json`; experiment.json records that switch and the archived `experiment_5k.json` baseline.",
             "", "### Layer-1 category agreement — all 28 category queries", "",
             "Unfiltered retrieval. Category agreement is coarse topical alignment, not judged relevance. Precision denominator is 10, including underfilled ranks.", "",
             "| Retriever | Metric | 5,000 | 20,000 | Delta |", "|---|---|---:|---:|---:|"]
    for method, metrics in compared["layer1"].items():
        for metric, values in metrics.items():
            lines.append(f"| {method} | {metric} | {values['5000']:.3f} | {values['20000']:.3f} | {values['delta']:+.3f} |")
    relevance = record["judged_relevance"]
    lines.extend(["", "### Layer-2 judged relevance — eight development queries", ""])
    if relevance["status"] != "ready":
        lines.extend([f"**Not yet computable:** {len(relevance.get('missing_pairs', []))} unique top-ten (query_id, ACN) pairs lack judgments. Retaining all Mini reports preserves existing labels but does not judge newly retrieved candidates.",
                      "No unjudged report is assumed irrelevant. The 20k scores and deltas remain pending; treating these rows as zero would invalidate the comparison.",
                      "`judging_pool_20k_additions.csv` is a blinded, shuffled export of only the missing pairs, with blank grades/notes. The original pool and qrels are untouched.", ""])
    lines.extend(["| Retriever | Metric | 5,000 | 20,000 | Delta |", "|---|---|---:|---:|---:|"])
    for method, metrics in compared["layer2"].items():
        for metric, values in metrics.items():
            new = f"{values['20000']:.3f}" if values["20000"] is not None else "pending judgments"
            delta = f"{values['delta']:+.3f}" if values["delta"] is not None else "N/A"
            lines.append(f"| {method} | {metric} | {values['5000']:.3f} | {new} | {delta} |")
    lines.extend(["", "### Per-query Layer-1 metrics", "",
                  "| Query | Layer | Retriever | Retrieved | Category Precision@10 | Hit@10 |", "|---|---:|---|---:|---:|---:|"])
    for row in record["per_query"]:
        lines.append(f"| {row['query_id']} | {row['layer']} | {row['method']} | {row['retrieved']} | {row['category_precision_at_10']:.3f} | {row['hit_at_10']} |")
    if relevance["status"] == "ready":
        lines.extend(["", "### Per-query Layer-2 metrics", "",
                      "| Query | Retriever | Precision@10 | MRR | nDCG@10 |", "|---|---|---:|---:|---:|"])
        for row in relevance["per_query"]:
            lines.append(f"| {row['query_id']} | {row['method']} | {row['precision_at_10']:.3f} | {row['mrr']:.3f} | {row['ndcg_at_10']:.3f} |")
    lines.extend(["", "### Latency and candidate-depth sensitivity", "",
                  "| Retriever | Mean ms | p95 ms | Top-ten changes at 200 candidate chunks |", "|---|---:|---:|---:|"])
    for method, timing in record["latency_ms"].items():
        changes = record["candidate_depth_sensitivity"][method]["changed_top10_queries"]
        lines.append(f"| {method} | {timing['mean']:.2f} | {timing['p95']:.2f} | {changes}/28 |")
    lines.extend(["", "Default candidate depths remain 100 chunks / 50 reports, report-level RRF k=60, ties by ACN. All controls were reverified absent; this evaluator makes no generation calls.",
                  "Full corpus/query/qrels hashes, per-query measurements, sensitivity records, configuration, software, hardware, and timestamp are in `experiment.json`. No Step 6 retrieval variant was started.", ""])
    return "\n".join(lines)
