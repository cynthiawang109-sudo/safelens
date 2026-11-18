"""Explicit, narrowly authorized protected-manifest reissue for the cnt-1 fix."""

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

ACTIVE = Path("eval/step9_protected_hashes.json")
ARCHIVE = Path("eval/protected_hash_history/step9_before_cnt1.json")
AUDIT = Path("eval/protected_hash_history/cnt1_reissue.json")
AUTHORIZED = "src/safelens/aggregate.py"
JUDGMENT_PATHS = {"eval/judging_pool_step7_additions.csv", "eval/qrels.jsonl",
                  "eval/experiment_step7_part1.json", "eval/results.md"}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--disclosure", type=Path, required=True)
    parser.add_argument("--judgment-completion", type=Path)
    args = parser.parse_args()
    if not args.disclosure.is_file():
        parser.error("Write the disclosure before reissuing the manifest")
    original = ACTIVE.read_bytes()
    baseline = json.loads(original.decode("utf-8"))
    allowed = {AUTHORIZED}
    frozen_results_sha256 = None
    if args.judgment_completion:
        completion = json.loads(args.judgment_completion.read_text(encoding="utf-8"))
        if not (completion["imported_rows"] == 5 and completion["qrels_rows_after"] == 139
                and completion["prior_rows_byte_unchanged"] and completion["dense_metrics_unchanged"]):
            parser.error("Judgment completion audit does not authorize this reissue")
        work = Path("data/post_freeze_step7_import")
        prior_qrels = (work / "prior_qrels.jsonl").read_bytes()
        current_qrels = Path("eval/qrels.jsonl").read_bytes()
        if sha(prior_qrels) not in baseline["eval/qrels.jsonl"].values() or not current_qrels.startswith(prior_qrels):
            parser.error("Prior qrel bytes were not preserved")
        if len(current_qrels.splitlines()) != 139 or sha(current_qrels) != completion["qrels_sha256"]:
            parser.error("Merged qrels differ from the validated import")
        if sha(Path("eval/judging_pool_step7_additions.csv").read_bytes()) != completion["pool_sha256"]:
            parser.error("Human pool changed after validation")
        prior_results = (work / "prior_results.md").read_bytes()
        current_results = Path("eval/results.md").read_bytes()
        if sha(prior_results) not in baseline["eval/results.md"].values():
            parser.error("Results backup is not the sealed original")
        start, end = b"<!-- production-step7-part1 -->", b"<!-- agent-ablation-step7 -->"
        if prior_results.split(start, 1)[0] != current_results.split(start, 1)[0] or prior_results.split(end, 1)[1] != current_results.split(end, 1)[1]:
            parser.error("A historical results section outside development Part 1 changed")
        marker = b"<!-- frozen-final-test-step7d -->"
        frozen_results_sha256 = sha(prior_results.split(marker, 1)[1])
        if sha(current_results.split(marker, 1)[1]) != frozen_results_sha256:
            parser.error("Frozen final results changed; reissue forbidden")
        old_record = json.loads((work / "prior_experiment.json").read_text(encoding="utf-8"))
        new_record = json.loads(Path("eval/experiment_step7_part1.json").read_text(encoding="utf-8"))
        for method in ("dense", "lexical"):
            if old_record["judged_relevance"]["averages"][method] != new_record["judged_relevance"]["averages"][method]:
                parser.error("Retained metrics changed")
        allowed |= JUDGMENT_PATHS
    changed = [name for name, hashes in baseline.items()
               if not Path(name).is_file() or sha(Path(name).read_bytes()) not in hashes.values()]
    if set(changed) != allowed:
        parser.error(f"Reissue permits exactly {sorted(allowed)}; actual changed files: {changed}")
    if ARCHIVE.exists() or AUDIT.exists():
        parser.error("This reissue already has an archive/audit; never overwrite history")
    before = {name: baseline[name] for name in sorted(allowed)}
    for name in sorted(allowed):
        raw = Path(name).read_bytes()
        canonical = raw.replace(b"\r\n", b"\n")
        baseline[name] = {"repository_sha256": sha(canonical), "original_checkout_sha256": sha(raw),
                          "windows_checkout_sha256": sha(canonical.replace(b"\n", b"\r\n"))}
    # Every other entry, including all frozen/development data, remains sealed.
    updated = (json.dumps(baseline, indent=2) + "\n").encode("utf-8")
    audit = {"reason": "Disclosed post-freeze aggregate category token-set mapping fix",
             "disclosure": args.disclosure.as_posix(), "authorized_changed_paths": sorted(allowed),
             "production_changed_paths": [AUTHORIZED],
             "judgment_completion": args.judgment_completion.as_posix() if args.judgment_completion else None,
             "base_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
             "prior_manifest_sha256": sha(original), "new_manifest_sha256": sha(updated),
             "before": before, "after": {name: baseline[name] for name in sorted(allowed)},
             "unchanged_entries": len(baseline) - len(allowed), "frozen_assets_reissued": False,
             "frozen_results_section_sha256": frozen_results_sha256}
    ARCHIVE.parent.mkdir(parents=True, exist_ok=True)
    with ARCHIVE.open("xb") as target:
        target.write(original)
    with AUDIT.open("x", encoding="utf-8", newline="\n") as target:
        target.write(json.dumps(audit, indent=2) + "\n")
    ACTIVE.write_bytes(updated)
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
