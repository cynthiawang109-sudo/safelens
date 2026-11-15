"""Convert Cynthia's fully graded judging CSV to versioned qrels; never grade."""

import argparse
import json
from pathlib import Path

from safelens.evaluation import import_judgments


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("eval/judging_pool.csv"))
    parser.add_argument("--output", type=Path, default=Path("eval/qrels.jsonl"))
    parser.add_argument("--queries", type=Path, default=Path("eval/queries.jsonl"))
    parser.add_argument("--manifest", type=Path, default=Path("eval/subset_manifest.json"))
    parser.add_argument("--rankings", type=Path, default=Path("data/eval_rankings.json"))
    args = parser.parse_args()
    try:
        with args.queries.open(encoding="utf-8") as source:
            judged_ids = {q["id"] for line in source if line.strip() and (q := json.loads(line))["layer"] == 2}
        rankings = json.loads(args.rankings.read_text(encoding="utf-8"))
        pairs = {(qid, h["acn"]) for qid in judged_ids for hits in rankings[qid].values() for h in hits[:10]}
        count = import_judgments(args.input, args.output, args.queries, args.manifest, pairs)
    except (ValueError, FileExistsError) as error:
        parser.exit(1, str(error) + "\n")
    print(f"Imported {count} human judgments to {args.output}")


if __name__ == "__main__":
    main()
