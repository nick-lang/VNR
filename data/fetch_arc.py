"""Fetch ARC-AGI task corpora into data/ (shallow git clones).

Stdlib only. Idempotent: skips a target that already exists.
Run from the repo root:  python data/fetch_arc.py
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent

# (target_subdir, git_url). Update URLs here if upstream moves.
SOURCES = [
    ("arc-agi-1", "https://github.com/fchollet/ARC-AGI"),
    ("arc-agi-2", "https://github.com/arcprize/ARC-AGI-2"),
]


def clone(target: str, url: str) -> Path:
    dest = DATA_DIR / target
    if dest.exists():
        print(f"[skip] {dest} already exists")
        return dest
    if shutil.which("git") is None:
        sys.exit("git not found on PATH; install git or download the tasks manually.")
    print(f"[clone] {url} -> {dest}")
    subprocess.run(
        ["git", "clone", "--depth", "1", url, str(dest)],
        check=True,
    )
    return dest


def count_tasks(root: Path) -> int:
    """Count ARC-schema task JSONs anywhere under root."""
    n = 0
    for p in root.rglob("*.json"):
        try:
            obj = json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError, OSError):
            continue
        if isinstance(obj, dict) and "train" in obj and "test" in obj:
            n += 1
    return n


def main() -> None:
    for target, url in SOURCES:
        dest = clone(target, url)
        print(f"[count] {target}: {count_tasks(dest)} ARC-schema task files")
    print("Done.")


if __name__ == "__main__":
    main()
