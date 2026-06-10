"""VNR Stage 4 (H8): CompressARC baseline on the 50-task dev split, via Modal.

One GPU job per task (unmodified vendored CompressARC, 2000 steps, pass@2),
fanned out across up to 10 GPUs. Pre-registration: ledger/hypotheses.md (H8).

Usage (after `modal setup`):
  # cost-gate smoke: one task, measure s/step, project full-run cost
  modal run experiments/poc-vnr-s4-neural/modal_app.py --smoke

  # full pre-registered run (only if projection <= $30 out of pocket)
  modal run experiments/poc-vnr-s4-neural/modal_app.py
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import modal

if modal.is_local():
    REPO = Path(__file__).resolve().parents[2]
else:  # inside the container the file lives at /root/modal_app.py
    REPO = Path("/root")
CARC_LOCAL = REPO / "references" / "CompressARC"
DEV_SPLIT = REPO / "data" / "dev_split_arc1.json"
OUT_PATH = Path(__file__).resolve().parent / "stage4_result.json"

GPU = "L40S"
GPU_USD_PER_SEC = 0.000542  # Modal list price, L40S
STEPS = 2000

app = modal.App("vnr-s4-compressarc")

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install("torch==2.5.1", "numpy==2.2.2", "tqdm==4.66.6", "matplotlib==3.10.0")
    .add_local_dir(
        str(CARC_LOCAL),
        remote_path="/root/CompressARC",
        ignore=["__pycache__", "results_for_the_blog_post", "*.png"],
    )
)


@app.function(gpu=GPU, image=image, timeout=3 * 3600, retries=2)
def solve_task(task_id: str, steps: int = STEPS) -> dict:
    """Mirror of experiments/poc-a-baselines/run_compressarc_task.py, cloud-side."""
    import os
    import sys

    import torch

    torch.set_default_dtype(torch.float32)
    torch.set_default_device("cuda")
    os.chdir("/root/CompressARC")
    sys.path.insert(0, "/root/CompressARC")
    import arc_compressor
    import preprocessing
    import solution_selection
    import train

    t0 = time.time()
    task = preprocessing.preprocess_tasks("evaluation", [task_id])[0]
    model = arc_compressor.ARCCompressor(task)
    optimizer = torch.optim.Adam(model.weights_list, lr=0.01, betas=(0.5, 0.9))
    logger = solution_selection.Logger(task)
    for step in range(steps):
        train.take_step(task, model, optimizer, step, logger)
        if (step + 1) % 200 == 0:
            print(f"[{task_id}] step {step + 1}/{steps} "
                  f"elapsed={time.time() - t0:.0f}s loss={logger.loss_curve[-1]:.1f}",
                  flush=True)

    elapsed = time.time() - t0
    top1 = (
        logger.solution_most_frequent is not None
        and hash(logger.solution_most_frequent) == task.solution_hash
    )
    top2 = top1 or (
        logger.solution_second_most_frequent is not None
        and hash(logger.solution_second_most_frequent) == task.solution_hash
    )
    return {
        "task": task_id,
        "steps": steps,
        "seconds": round(elapsed, 1),
        "solved_top1": bool(top1),
        "solved_top2": bool(top2),
        "final_loss": float(logger.loss_curve[-1]) if logger.loss_curve else None,
    }


def _dev_ids() -> list[str]:
    return json.loads(DEV_SPLIT.read_text())["task_ids"]


@app.local_entrypoint()
def main(smoke: bool = False, steps: int = STEPS, banked: str = ""):
    ids = _dev_ids()
    done: dict = {}
    if banked:
        done = json.loads(Path(banked).read_text())
        ids = [i for i in ids if i not in done]
        print(f"resuming: {len(done)} banked, {len(ids)} remaining", flush=True)
    if smoke:
        # Cost gate (pre-registered): one task, project full-run cost.
        r = solve_task.remote(ids[0], steps)
        per_task_usd = r["seconds"] * GPU_USD_PER_SEC
        projection = {
            "smoke": r,
            "sec_per_step": round(r["seconds"] / steps, 3),
            "usd_per_task_list": round(per_task_usd, 3),
            "usd_50_tasks_list": round(per_task_usd * 50, 2),
            "usd_out_of_pocket_after_30_credit": round(max(0.0, per_task_usd * 50 - 30), 2),
        }
        print(json.dumps(projection, indent=2))
        return

    t0 = time.time()
    results = list(done.values())
    for r in solve_task.map(ids, kwargs={"steps": steps}):
        results.append(r)
        print(f"[result {len(results)}/50] {json.dumps(r)}", flush=True)
    by_task = {r["task"]: r for r in results}
    n1 = sum(r["solved_top1"] for r in results)
    n2 = sum(r["solved_top2"] for r in results)
    gpu_secs = sum(r["seconds"] for r in results)
    decision = ("ACCEPT H8" if n2 >= 5 else "KILL" if n2 <= 2 else "INCONCLUSIVE")
    summary = {
        "n_tasks": len(results),
        "steps": steps,
        "gpu": GPU,
        "pass_at_1": n1,
        "pass_at_2": n2,
        "solved_ids_pass2": sorted(t for t, r in by_task.items() if r["solved_top2"]),
        "gpu_hours": round(gpu_secs / 3600, 2),
        "usd_list_estimate": round(gpu_secs * GPU_USD_PER_SEC, 2),
        "wall_clock_min": round((time.time() - t0) / 60, 1),
        "decision_h8": decision,
    }
    OUT_PATH.write_text(json.dumps({"summary": summary, "per_task": by_task}, indent=2))
    print(json.dumps(summary, indent=2))
