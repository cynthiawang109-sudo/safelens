"""Fail on any changed frozen production/development/final-test asset."""

import hashlib
import json
from pathlib import Path


def main():
    baseline = json.loads(Path("eval/step9_protected_hashes.json").read_text(encoding="utf-8"))
    changed = [name for name, expected in baseline.items()
               if not Path(name).is_file() or hashlib.sha256(Path(name).read_bytes()).hexdigest() not in expected.values()]
    if changed:
        raise SystemExit(f"Protected files changed: {changed}")
    print(f"Protected hashes unchanged: {len(baseline)} files")


if __name__ == "__main__":
    main()
