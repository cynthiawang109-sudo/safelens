"""Flagship corpus growth: retain Mini and sample additions proportionally by year."""

import argparse
import hashlib
import json
import random
from collections import Counter, defaultdict
from dataclasses import asdict
from pathlib import Path

from safelens.ingest import SOURCE_DATASET, SOURCE_REVISION
from safelens.subset import DEFAULT_PATHS, read_corpus, select_subset

DEFAULT_SEED = 20261120


def select_expanded_corpus(reports, mini_manifest, seed=DEFAULT_SEED, size=20000):
    unique = {}
    for report in reports:
        unique.setdefault(report.acn, report)
    retained = set(mini_manifest["selected_acns"])
    if not retained <= unique.keys() or size < len(retained) or size > len(unique):
        raise ValueError("Expanded corpus must retain the Mini and fit the available source")
    available = defaultdict(list)
    for acn, report in unique.items():
        if acn not in retained:
            available[report.report_year].append(acn)
    count = size - len(retained)
    total = sum(map(len, available.values()))
    quotas = {year: count * len(acns) // total for year, acns in available.items()} if total else {}
    residual = count - sum(quotas.values())
    order = sorted(available, key=lambda year: (-(count * len(available[year]) % total), year))
    for year in order[:residual]:
        quotas[year] += 1
    rng = random.Random(seed)
    added = set()
    for year in sorted(available):
        added.update(rng.sample(sorted(available[year]), quotas[year]))
    selected = retained | added
    chosen = [unique[acn] for acn in sorted(selected)]
    labels = Counter(label for report in chosen for label in set(report.anomaly_codes))
    years = Counter(report.report_year for report in chosen)
    fingerprint = "".join(f"{r.acn}:{r.content_hash}\n" for r in chosen)
    return {
        "manifest_type": "flagship_year_stratified_v1", "size": size, "seed": seed,
        "source_dataset": SOURCE_DATASET, "source_revision": SOURCE_REVISION,
        "deduplicated_source_reports": len(unique),
        "base_snapshot_sha256": mini_manifest["snapshot_sha256"],
        "base_size": len(retained), "retained_base_reports": len(retained & selected),
        "added_reports": len(added),
        "selection_policy": "dedupe first occurrence in train/validation/test; keep all Mini ACNs; Hamilton largest-remainder year quotas over remaining corpus; remainder ties by year; sorted years and ACNs; Python 3.12 random.Random(seed).sample; no anomaly filter",
        "remaining_year_population": {str(y): len(available[y]) for y in sorted(available)},
        "addition_year_counts": {str(y): quotas[y] for y in sorted(quotas)},
        "year_distribution": {str(y): years[y] for y in sorted(years)},
        "per_label_counts": dict(sorted(labels.items())),
        "selected_acns": sorted(selected), "added_acns": sorted(added),
        "snapshot_sha256": hashlib.sha256(fingerprint.encode("utf-8")).hexdigest(),
    }


def load_expanded_reports(path, base_path=Path("eval/subset_manifest.json"), paths=DEFAULT_PATHS):
    manifest = json.loads(Path(path).read_text(encoding="utf-8"))
    mini = json.loads(Path(base_path).read_text(encoding="utf-8"))
    corpus = read_corpus(paths)
    if mini != select_subset(corpus.values(), mini["seed"], mini["size"]):
        raise ValueError("Mini manifest does not reproduce from source")
    expected = select_expanded_corpus(corpus.values(), mini, manifest["seed"], manifest["size"])
    if manifest != expected:
        raise ValueError("Expanded manifest does not reproduce from source")
    return [{**asdict(corpus[acn]), "content_hash": corpus[acn].content_hash}
            for acn in manifest["selected_acns"]]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, default=Path("eval/subset_manifest.json"))
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--size", type=int, default=20000)
    parser.add_argument("--output", type=Path, default=Path("eval/corpus_manifest_20k.json"))
    args = parser.parse_args()
    mini = json.loads(args.base.read_text(encoding="utf-8"))
    manifest = select_expanded_corpus(read_corpus(DEFAULT_PATHS).values(), mini, args.seed, args.size)
    args.output.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in manifest.items() if k not in ("selected_acns", "added_acns", "per_label_counts")}, indent=2))


if __name__ == "__main__":
    main()
