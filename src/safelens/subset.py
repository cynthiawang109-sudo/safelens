"""Deterministic, deduplicated Mini subset selection from pinned source files."""

import argparse
import hashlib
import json
import random
from collections import Counter
from dataclasses import asdict
from pathlib import Path

from safelens.ingest import SOURCE_DATASET, SOURCE_REVISION, stream_reports

CATEGORIES = (
    "Ground Incursion Runway",
    "Deviation - Altitude Excursion From Assigned Altitude",
    "Conflict NMAC",
    "Aircraft Equipment Problem Critical",
)
DEFAULT_PATHS = tuple(Path(f"data/asrs-aviation-reports-{split}.jsonl")
                      for split in ("train", "validation", "test"))
DEFAULT_SEED = 20261115


def read_corpus(paths):
    reports = {}
    for report in stream_reports(paths):
        if report is not None:
            reports.setdefault(report.acn, report)
    return reports


def select_subset(reports, seed=DEFAULT_SEED, size=5000):
    """Deduplicate first; rarity-first quotas, then fill from the category union.

    Canonically sort ACNs before sampling with a private seeded RNG. For each
    category in the fixed order, select up to size//4 as-yet-unselected reports.
    When the rare runway pool is exhausted, its deficit is filled from the
    remaining union after all four passes. Multi-label reports count once.
    """
    if size <= 0:
        raise ValueError("Subset size must be positive")
    unique = {}
    for report in reports:
        unique.setdefault(report.acn, report)
    rng = random.Random(seed)
    selected = set()
    passes = []
    for category in CATEGORIES:
        pool = sorted(acn for acn, report in unique.items()
                      if acn not in selected and category in report.anomaly_codes)
        chosen = rng.sample(pool, min(size // len(CATEGORIES), len(pool)))
        selected.update(chosen)
        passes.append({"category": category, "available_before_pass": len(pool), "new_reports": len(chosen)})
    remaining = sorted(acn for acn, report in unique.items()
                       if acn not in selected and set(report.anomaly_codes).intersection(CATEGORIES))
    deficit = size - len(selected)
    if len(remaining) < deficit:
        raise ValueError("Not enough reports in the selected-category union")
    selected.update(rng.sample(remaining, deficit))
    chosen = [unique[acn] for acn in sorted(selected)]
    labels = Counter(label for report in chosen for label in set(report.anomaly_codes))
    years = Counter(report.report_year for report in chosen)
    overlaps = Counter(len(set(report.anomaly_codes).intersection(CATEGORIES)) for report in chosen)
    snapshot = "".join(f"{report.acn}:{report.content_hash}\n" for report in chosen)
    return {
        "source_dataset": SOURCE_DATASET, "source_revision": SOURCE_REVISION,
        "seed": seed, "size": size, "deduplicated_source_reports": len(unique),
        "selection_policy": "dedupe first occurrence; sorted ACN; seeded random.sample; four ordered size//4 quotas; fill deficit from remaining union",
        "dedupe_file_order": ["train", "validation", "test"],
        "category_order": list(CATEGORIES), "selection_passes": passes, "union_fill": deficit,
        "selected_acns": sorted(selected), "per_label_counts": {c: labels[c] for c in CATEGORIES},
        "all_label_counts": dict(sorted(labels.items())),
        "year_distribution": {str(k): v for k, v in sorted(years.items())},
        "selected_category_overlap": {str(k): v for k, v in sorted(overlaps.items())},
        "snapshot_sha256": hashlib.sha256(snapshot.encode("utf-8")).hexdigest(),
    }


def load_manifest_reports(path, paths=DEFAULT_PATHS):
    manifest = json.loads(Path(path).read_text(encoding="utf-8"))
    corpus = read_corpus(paths)
    expected = select_subset(corpus.values(), manifest["seed"], manifest["size"])
    if manifest != expected:
        raise ValueError("Manifest does not reproduce from the pinned source and selection policy")
    return [{**asdict(corpus[acn]), "content_hash": corpus[acn].content_hash}
            for acn in manifest["selected_acns"]]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--size", type=int, default=5000)
    parser.add_argument("--output", type=Path, default=Path("eval/subset_manifest.json"))
    args = parser.parse_args()
    manifest = select_subset(read_corpus(DEFAULT_PATHS).values(), args.seed, args.size)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in manifest.items() if k not in ("selected_acns", "all_label_counts")}, indent=2))


if __name__ == "__main__":
    main()
