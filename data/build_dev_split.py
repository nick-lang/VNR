"""Build a committed, deterministic 50-task ARC-AGI-1 dev split.

Selects every Nth task ID (sorted) from the ARC-AGI-1 evaluation set so the
split is spread across the corpus and fully reproducible (no RNG). Writes the
task IDs to data/dev_split_arc1.json (committed; the task JSONs themselves are
fetched via fetch_arc.py and git-ignored).

Run from the repo root after fetch_arc.py:  python data/build_dev_split.py
"""
from __future__ import annotations

import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent
EVAL_DIR = DATA_DIR / "arc-agi-1" / "data" / "evaluation"
OUT = DATA_DIR / "dev_split_arc1.json"
N = 50


def main() -> None:
    if not EVAL_DIR.exists():
        raise SystemExit(f"{EVAL_DIR} missing; run `python data/fetch_arc.py` first.")
    ids = sorted(p.stem for p in EVAL_DIR.glob("*.json"))
    if not ids:
        raise SystemExit(f"No task JSONs found in {EVAL_DIR}.")
    stride = max(1, len(ids) // N)
    selected = ids[::stride][:N]
    OUT.write_text(json.dumps(
        {
            "source": "ARC-AGI-1 evaluation",
            "selection": f"sorted ids, every {stride}th, first {N}",
            "n": len(selected),
            "total_available": len(ids),
            "task_ids": selected,
        },
        indent=2,
    ))
    print(f"Wrote {len(selected)} task IDs to {OUT} (from {len(ids)} eval tasks, stride {stride}).")


if __name__ == "__main__":
    main()
