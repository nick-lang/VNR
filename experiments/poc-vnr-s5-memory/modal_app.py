"""VNR Stage 5 (H9): cross-task weight memory on the CompressARC substrate.

Two-phase experiment over the 11 H8-solved dev tasks (pre-registration:
ledger/hypotheses.md, H9):

  Phase 1 (cold + donors): retrain each task from scratch, 2000 steps,
    recording per-step top-2 solution picks (steps-to-stable-solve) and
    saving final transformation weights. Doubles as the cold arm and the
    H8 determinism check.
  Phase 2 (warm): leave-one-out weight-soup warm-starts for the 11 tasks,
    + 2 same-task-restart sanity jobs (validity gate),
    + 5 exploratory warm-starts on H8-unsolved tasks (full 11-donor soup).

Usage (after phase 1 completes, phase 2 reads its artifacts):
  modal run experiments/poc-vnr-s5-memory/modal_app.py --phase donors
  modal run experiments/poc-vnr-s5-memory/modal_app.py --phase warm
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import modal

if modal.is_local():
    REPO = Path(__file__).resolve().parents[2]
    HERE = Path(__file__).resolve().parent
else:
    REPO = Path("/root")
    HERE = Path("/root")
CARC_LOCAL = REPO / "references" / "CompressARC"
ARTIFACTS = HERE / "s5_artifacts"

GPU = "L40S"
STEPS = 2000

# The 11 H8-solved dev tasks (stage4_result.json, pass@2 == pass@1).
SOLVED = [
    "00576224", "15663ba9", "1d0a4b61", "45737921", "6df30ad6", "8597cfd7",
    "903d1b4a", "ae58858e", "cd3c21df", "d2acf2cb", "ef26cbf6",
]
SANITY = ["00576224", "8597cfd7"]  # same-task restart validity gate
# Exploratory: first 5 H8-unsolved dev-split ids (sorted), fixed in advance.
UNSOLVED_PROBE = ["08573cc6", "0c786b71", "12997ef3", "1990f7a8", "20981f0e"]

app = modal.App("vnr-s5-memory")

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install("torch==2.5.1", "numpy==2.2.2", "tqdm==4.66.6", "matplotlib==3.10.0")
    .add_local_dir(
        str(CARC_LOCAL),
        remote_path="/root/CompressARC",
        ignore=["__pycache__", "results_for_the_blog_post", "*.png"],
    )
    .add_local_file(str(Path(__file__).resolve().parent / "transfer.py"), "/root/transfer.py")
)


def _stable_solve_step(picks_history, solution_hash) -> int | None:
    """Earliest step s where the truth is in the top-2 picks at s and forever after."""
    solved = [solution_hash in picks for picks in picks_history]
    if not solved or not solved[-1]:
        return None
    s = len(solved)
    while s > 0 and solved[s - 1]:
        s -= 1
    return s  # first index of the trailing all-True run


@app.function(gpu=GPU, image=image, timeout=3 * 3600, retries=2)
def run_task(task_id: str, steps: int = STEPS,
             init_blob: bytes | None = None, return_weights: bool = False) -> dict:
    import os
    import sys

    import torch

    torch.set_default_dtype(torch.float32)
    torch.set_default_device("cuda")
    os.chdir("/root/CompressARC")
    sys.path.insert(0, "/root/CompressARC")
    sys.path.insert(0, "/root")
    import arc_compressor
    import preprocessing
    import solution_selection
    import train
    import transfer

    t0 = time.time()
    task = preprocessing.preprocess_tasks("evaluation", [task_id])[0]
    model = arc_compressor.ARCCompressor(task)
    if init_blob is not None:
        transfer.load_weights(model, transfer.from_bytes(init_blob))
    optimizer = torch.optim.Adam(model.weights_list, lr=0.01, betas=(0.5, 0.9))
    logger = solution_selection.Logger(task)
    for step in range(steps):
        train.take_step(task, model, optimizer, step, logger)
        if (step + 1) % 400 == 0:
            print(f"[{task_id}{'/warm' if init_blob else ''}] step {step + 1}/{steps} "
                  f"elapsed={time.time() - t0:.0f}s loss={logger.loss_curve[-1]:.1f}",
                  flush=True)

    top1 = (logger.solution_most_frequent is not None
            and hash(logger.solution_most_frequent) == task.solution_hash)
    top2 = top1 or (logger.solution_second_most_frequent is not None
                    and hash(logger.solution_second_most_frequent) == task.solution_hash)
    result = {
        "task": task_id,
        "warm": init_blob is not None,
        "steps": steps,
        "seconds": round(time.time() - t0, 1),
        "solved_top1": bool(top1),
        "solved_top2": bool(top2),
        "steps_to_stable_solve": _stable_solve_step(
            logger.solution_picks_history, task.solution_hash),
        "final_loss": float(logger.loss_curve[-1]) if logger.loss_curve else None,
    }
    if return_weights:
        result["weights"] = transfer.to_bytes(transfer.extract_weights(model))
    return result


@app.local_entrypoint()
def main(phase: str = "donors", steps: int = STEPS):
    import transfer  # local import; same file shipped to the container

    ARTIFACTS.mkdir(exist_ok=True)

    if phase == "donors":
        results = []
        args = [(tid,) for tid in SOLVED]
        for r in run_task.starmap(args, kwargs={"steps": steps, "return_weights": True}):
            weights = r.pop("weights")
            (ARTIFACTS / f"donor_{r['task']}.pt").write_bytes(weights)
            results.append(r)
            print(f"[cold {len(results)}/{len(SOLVED)}] {json.dumps(r)}", flush=True)
        n2 = sum(r["solved_top2"] for r in results)
        out = {"phase": "donors", "results": {r["task"]: r for r in results},
               "pass_at_2": n2, "reproduces_h8": n2 == len(SOLVED)}
        (HERE / "phase1_result.json").write_text(json.dumps(out, indent=2))
        print(json.dumps({k: v for k, v in out.items() if k != "results"}, indent=2))
        return

    if phase == "warm":
        cold = json.loads((HERE / "phase1_result.json").read_text())["results"]
        donors = {tid: transfer.from_bytes((ARTIFACTS / f"donor_{tid}.pt").read_bytes())
                  for tid in SOLVED}

        jobs: list[tuple[str, str, bytes]] = []  # (kind, task, soup)
        for tid in SOLVED:  # LOO warm
            soup = transfer.average_weights([donors[d] for d in SOLVED if d != tid])
            jobs.append(("loo", tid, transfer.to_bytes(soup)))
        for tid in SANITY:  # same-task restart (own weights)
            jobs.append(("sanity", tid, transfer.to_bytes(donors[tid])))
        full_soup = transfer.to_bytes(transfer.average_weights(list(donors.values())))
        for tid in UNSOLVED_PROBE:
            jobs.append(("probe", tid, full_soup))

        handles = [run_task.spawn(tid, steps=steps, init_blob=soup) for _, tid, soup in jobs]
        results = []
        for (kind, tid, _), h in zip(jobs, handles):
            r = h.get()
            r["kind"] = kind
            results.append(r)
            print(f"[warm {len(results)}/{len(jobs)}] {json.dumps(r)}", flush=True)

        loo = {r["task"]: r for r in results if r["kind"] == "loo"}
        ratios, retained = [], 0
        for tid in SOLVED:
            c = cold[tid]["steps_to_stable_solve"] or steps
            w = loo[tid]["steps_to_stable_solve"] or steps
            if loo[tid]["solved_top2"]:
                retained += 1
            ratios.append((tid, w, c, round(w / max(c, 1), 3)))
        sorted_r = sorted(x[3] for x in ratios)
        median_ratio = sorted_r[len(sorted_r) // 2]

        sanity_ok = all(
            r["solved_top2"] and (r["steps_to_stable_solve"] or steps) <= 200
            for r in results if r["kind"] == "sanity"
        )
        probe_new = sorted(r["task"] for r in results if r["kind"] == "probe" and r["solved_top2"])

        if not sanity_ok:
            decision = "VOID (validity gate failed: same-task restart did not re-solve fast)"
        elif median_ratio <= 0.5 and retained >= 10:
            decision = "ACCEPT H9"
        elif median_ratio >= 1.0 or retained <= 8:
            decision = "KILL"
        else:
            decision = "INCONCLUSIVE"

        out = {
            "phase": "warm",
            "per_task": {r["task"] + ("(sanity)" if r["kind"] == "sanity" else ""): r
                         for r in results},
            "loo_ratios": [{"task": t, "warm_steps": w, "cold_steps": c, "ratio": x}
                           for t, w, c, x in ratios],
            "median_ratio": median_ratio,
            "retained": f"{retained}/{len(SOLVED)}",
            "sanity_ok": sanity_ok,
            "probe_new_solves": probe_new,
            "decision_h9": decision,
        }
        (HERE / "stage5_result.json").write_text(json.dumps(out, indent=2))
        print(json.dumps({k: v for k, v in out.items() if k != "per_task"}, indent=2))
        return

    raise SystemExit(f"unknown phase: {phase}")
