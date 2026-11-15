"""Inspect the HF ASRS dataset (JSONL splits) and print schema statistics.

Usage:
    python inspect_dataset.py <file1.jsonl> [file2.jsonl ...]

Prints row counts, ACN uniqueness, date range/format, anomaly label
distribution (multi-label, semicolon-joined), narrative/synopsis coverage
and lengths, and per-column non-empty rates. Read-only; safe to re-run
on the full corpus to finalize docs/DATA_NOTES.md.
"""
import collections
import json
import re
import sys


def main(paths: list[str]) -> None:
    rows = 0
    key_nonempty: collections.Counter = collections.Counter()
    acns: set = set()
    acn_dup = 0
    anomaly_counter: collections.Counter = collections.Counter()
    multi_label = 0
    dates: list[str] = []
    narr: dict[str, list[int]] = collections.defaultdict(lambda: [0, 0])
    syn_lens: list[int] = []
    doc_lens: list[int] = []

    for path in paths:
        with open(path, encoding="utf-8") as f:
            for line in f:
                r = json.loads(line)
                rows += 1
                for k, v in r.items():
                    if v not in ("", None, [], " "):
                        key_nonempty[k] += 1
                acn = r.get("acn_num_ACN")
                if acn in acns:
                    acn_dup += 1
                acns.add(acn)
                if r.get("Time_Date"):
                    dates.append(r["Time_Date"])
                parts = [p.strip() for p in str(r.get("Events_Anomaly", "")).split(";") if p.strip()]
                if len(parts) > 1:
                    multi_label += 1
                for p in parts:
                    anomaly_counter[p] += 1
                for k in ("Report 1_Narrative", "Report 2_Narrative"):
                    v = r.get(k) or ""
                    if v:
                        narr[k][0] += 1
                        narr[k][1] += len(v)
                syn = r.get("Report 1.2_Synopsis") or ""
                syn_lens.append(len(syn))
                doc_lens.append(
                    len(syn)
                    + len(r.get("Report 1_Narrative") or "")
                    + len(r.get("Report 2_Narrative") or "")
                )

    dates.sort()
    doc_lens.sort()
    print(f"rows: {rows}")
    print(f"columns: {len(key_nonempty)}")
    print(f"ACN unique: {len(acns)}  duplicates: {acn_dup}")
    print(f"Time_Date range: {dates[0]}..{dates[-1]}  distinct months: {len(set(dates))}")
    print(f"multi-label rows: {multi_label}  distinct anomaly labels: {len(anomaly_counter)}")
    print("top anomaly labels:")
    for name, c in anomaly_counter.most_common(25):
        print(f"  {c:6d}  {name}")
    for k, (n, chars) in sorted(narr.items()):
        print(f"{k}: nonempty={n} avg_chars={chars / max(n, 1):.0f}")
    print(f"synopsis chars: avg={sum(syn_lens) / max(len(syn_lens), 1):.0f} max={max(syn_lens, default=0)}")
    if doc_lens:
        print(f"document chars: avg={sum(doc_lens) / len(doc_lens):.0f} p90={doc_lens[int(len(doc_lens) * 0.9)]}")
    print("columns by coverage:")
    for k, c in key_nonempty.most_common():
        print(f"  {c:6d}/{rows}  {k}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("usage: python inspect_dataset.py <file.jsonl> [...]")
    main(sys.argv[1:])
