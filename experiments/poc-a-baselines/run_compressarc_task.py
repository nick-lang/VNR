"""Headless CompressARC baseline harness.

Trains a CompressARC model on ONE ARC-AGI task for a given number of steps and
reports whether the task was solved (pass@2: top-1 or top-2 most-frequent
solution matches the ground-truth solution hash), plus wall-clock cost.

Wraps the vendored reference repo at references/CompressARC (git-ignored).
CompressARC bundles its own ARC-AGI-1 data under references/CompressARC/dataset/.

Usage (real baseline needs a CUDA build of torch; see Stage 0 notes):
  python experiments/poc-a-baselines/run_compressarc_task.py --task 00576224 --split evaluation --steps 2000
  # quick functional smoke test on CPU:
  python experiments/poc-a-baselines/run_compressarc_task.py --task 00576224 --split evaluation --steps 20 --device cpu
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CARC = REPO / "references" / "CompressARC"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True, help="ARC task id, e.g. 00576224")
    ap.add_argument("--split", default="evaluation", choices=["training", "evaluation", "test"])
    ap.add_argument("--steps", type=int, default=2000)
    ap.add_argument("--device", default="auto", help="auto | cpu | cuda")
    ap.add_argument("--out", default=None, help="optional path to write the JSON result")
    ap.add_argument("--progress-every", type=int, default=100, help="print a heartbeat every N steps (0 to disable)")
    args = ap.parse_args()

    if not CARC.exists():
        raise SystemExit(f"{CARC} missing; clone it (see references/README.md).")

    import torch

    device = (
        ("cuda" if torch.cuda.is_available() else "cpu")
        if args.device == "auto"
        else args.device
    )
    torch.set_default_dtype(torch.float32)
    torch.set_default_device(device)

    # CompressARC uses relative paths (dataset/...) and bare module imports.
    os.chdir(CARC)
    sys.path.insert(0, str(CARC))
    import preprocessing  # noqa: E402
    import arc_compressor  # noqa: E402
    import solution_selection  # noqa: E402
    import train  # noqa: E402

    t0 = time.time()
    task = preprocessing.preprocess_tasks(args.split, [args.task])[0]
    model = arc_compressor.ARCCompressor(task)
    optimizer = torch.optim.Adam(model.weights_list, lr=0.01, betas=(0.5, 0.9))
    logger = solution_selection.Logger(task)

    for step in range(args.steps):
        train.take_step(task, model, optimizer, step, logger)
        if args.progress_every and (step + 1) % args.progress_every == 0:
            loss = logger.loss_curve[-1] if logger.loss_curve else float("nan")
            print(
                f"[progress] step {step + 1}/{args.steps} "
                f"elapsed={time.time() - t0:.1f}s loss={loss:.1f}",
                flush=True,
            )

    elapsed = time.time() - t0
    top1 = (
        logger.solution_most_frequent is not None
        and hash(logger.solution_most_frequent) == task.solution_hash
    )
    top2 = top1 or (
        logger.solution_second_most_frequent is not None
        and hash(logger.solution_second_most_frequent) == task.solution_hash
    )

    result = {
        "task": args.task,
        "split": args.split,
        "steps": args.steps,
        "device": device,
        "seconds": round(elapsed, 1),
        "solved_top1": bool(top1),
        "solved_top2": bool(top2),
        "final_loss": logger.loss_curve[-1] if logger.loss_curve else None,
    }
    print(json.dumps(result))
    if args.out:
        Path(args.out).write_text(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
