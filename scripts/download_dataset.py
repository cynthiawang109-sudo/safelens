"""Download the three pinned source files into ignored data/, checking SHA-256."""

import hashlib
import shutil
import urllib.request
from pathlib import Path

from safelens.ingest import SOURCE_DATASET, SOURCE_REVISION

FILES = {
    "train": "1b9300b926774d2ba025552db0bbd3894891c69ddb1f43f85fc4f5241221f101",
    "validation": "6734d8823eba239b1b296e7bfa606407659903bfb4e614ed7f4864aea65cce1c",
    "test": "56272a11b62c1b17137b638b99b7f05c105a9eaf3443165e7de5b844fd8a735a",
}


def digest(path):
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def main():
    Path("data").mkdir(exist_ok=True)
    for split, expected in FILES.items():
        path = Path("data") / f"asrs-aviation-reports-{split}.jsonl"
        if path.exists():
            if digest(path) != expected:
                raise ValueError(f"Existing file checksum mismatch: {path}; move it aside and retry")
            print(f"Verified {path}")
            continue
        url = f"https://huggingface.co/datasets/{SOURCE_DATASET}/resolve/{SOURCE_REVISION}/{path.name}"
        partial = path.with_suffix(".jsonl.part")
        with urllib.request.urlopen(url, timeout=60) as response, partial.open("wb") as target:
            shutil.copyfileobj(response, target)
        if digest(partial) != expected:
            raise ValueError(f"Downloaded file checksum mismatch: {partial}")
        partial.replace(path)
        print(f"Downloaded and verified {path}")


if __name__ == "__main__":
    main()
