"""E1-B — pick/grid CAPTURE runs for the selector bake-off (write-up prep).

E1-A showed the banked S6 corpus supports only loss-scorer selectors and holds
just 8 informative cases; agreement voting, pick stability, and vote margin
need per-run picks/grids, which s6_runner discarded. This runner re-runs a
scoped job subset with full capture. Benchmark (2026-08-18, this rig): worker
sweep 1/2/3/4 -> 0.81/1.33/1.42/1.44 aggregate steps/s; 3 workers chosen.

NONDETERMINISM (found during the bench, recorded before any E1-B result):
seven same-seed (42) same-task 120-step runs produced final losses 436-571 --
fixed seed does NOT pin the trajectory on this hardware/torch. Consequences:
(a) these runs are FRESH SAMPLES, not regenerations of banked runs; the
per-job `banked_final_loss` field is a reproducibility READOUT, not a gate;
(b) every capture run doubles as a new draw for run-marginalized solve
probability (feeds E2).

Pre-registered scope (no cherry-picking):
  solve-relevant unsolved tasks (any S6 run solved): 73182012, 981571dc,
    be03b35f, e66aafb8 -> full trio (2000@s0, 1000@s1, 1000@s2)
  seed-churn solved tasks (solved s0, lost s1 in S6/S5f): 00576224,
    6df30ad6 -> pair (1000@s0, 1000@s1)
  never-solved precision sample: the FIRST SIX tasks in committed dev-split
    order among the 35 never-solved-in-any-run tasks -> full trio.
    (False-positive check: does cross-run agreement vote for the same WRONG
    answer? Agreement precision is meaningless without this arm.)
  34 jobs, ~44k steps, ~8.6 h at 3-way throughput, $0.

Pre-registered selector evaluation (run AFTER capture completes, over the
union of capture runs per task; descriptive, not decision-bearing -- this is
write-up material, not a numbered hypothesis):
  agreement vote:  candidates' top-1 grids vote; answer = modal grid(s);
                   report solve recall on solve-relevant tasks AND wrong-modal
                   rate on the never-solved arm.
  pick stability:  fraction of trailing steps with unchanged top-1 pick
                   (from picks_history); select the most stable run.
  vote margin:     log-score gap top1-vs-top2 within a run (from
                   solution_hashes_count); select the largest margin.
  final_loss:      E1-A's surviving scorer, as the baseline to beat.

Usage: --status | --worker | --clear-claims | --smoke
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from s6_runner import (  # noqa: E402
    DEV_SPLIT, UNSOLVED, _env, _stable_solve_step,
)

ARTIFACTS = HERE / "e1b_artifacts"
CLAIMS = ARTIFACTS / "claims_e1b"
S6_ARTIFACTS = HERE / "s6_artifacts"

SOLVE_TASKS = ["73182012", "981571dc", "be03b35f", "e66aafb8"]
CHURN_TASKS = ["00576224", "6df30ad6"]
NEVER_TASKS = [t for t in UNSOLVED if t not in SOLVE_TASKS][:6]

A_STEPS, B_STEPS, TAIL = 2000, 1000, 50


def job_list() -> list[dict]:
    jobs = []
    for tid in SOLVE_TASKS + NEVER_TASKS:
        jobs.append({"name": f"a_{tid}", "task": tid, "kind": "a",
                     "steps": A_STEPS, "seed": 0})
        jobs.append({"name": f"b_{tid}_s1", "task": tid, "kind": "b",
                     "steps": B_STEPS, "seed": 1})
        jobs.append({"name": f"b_{tid}_s2", "task": tid, "kind": "b",
                     "steps": B_STEPS, "seed": 2})
    for tid in CHURN_TASKS:
        jobs.append({"name": f"c_{tid}_s0", "task": tid, "kind": "churn",
                     "steps": B_STEPS, "seed": 0})
        jobs.append({"name": f"c_{tid}_s1", "task": tid, "kind": "churn",
                     "steps": B_STEPS, "seed": 1})
    return jobs


def _rle(picks: list[list]) -> list[list]:
    """[[top1, top2], ...] -> [[count, top1, top2], ...] run-length encoded."""
    out: list[list] = []
    for p in picks:
        pair = [p[0], p[1]]
        if out and out[-1][1:] == pair:
            out[-1][0] += 1
        else:
            out.append([1] + pair)
    return out


def _banked_counterpart(name: str):
    if name.startswith("c_"):  # churn jobs have no same-name S6 counterpart
        return None
    f = S6_ARTIFACTS / f"job6_{name}.json"
    if f.exists():
        return json.loads(f.read_text())
    return None


def run_job(job: dict) -> dict:
    e = _env()
    torch = e["torch"]
    import numpy as np

    t0 = time.time()
    torch.manual_seed(job["seed"])
    np.random.seed(job["seed"])
    task = e["preprocessing"].preprocess_tasks("evaluation", [job["task"]])[0]
    model = e["arc_compressor"].ARCCompressor(task)
    opt = torch.optim.Adam(model.weights_list, lr=0.01, betas=(0.5, 0.9))
    logger = e["solution_selection"].Logger(task)
    for step in range(job["steps"]):
        e["train"].take_step(task, model, opt, step, logger)
        if (step + 1) % 500 == 0:
            print(f"  [{job['name']}] step {step + 1}/{job['steps']} "
                  f"elapsed={time.time() - t0:.0f}s "
                  f"loss={logger.loss_curve[-1]:.1f}", flush=True)

    top1_sol = logger.solution_most_frequent
    top2_sol = logger.solution_second_most_frequent
    top1 = top1_sol is not None and hash(top1_sol) == task.solution_hash
    top2 = top1 or (top2_sol is not None
                    and hash(top2_sol) == task.solution_hash)
    counts = logger.solution_hashes_count
    h1 = hash(top1_sol) if top1_sol is not None else None
    h2 = hash(top2_sol) if top2_sol is not None else None
    margin = (counts[h1] - counts[h2]
              if h1 in counts and h2 in counts and h1 != h2 else None)
    banked = _banked_counterpart(job["name"])

    return {
        "name": job["name"], "kind": job["kind"], "task": job["task"],
        "steps": job["steps"], "seed": job["seed"],
        "seconds": round(time.time() - t0, 1),
        "solved_top1": bool(top1), "solved_top2": bool(top2),
        "steps_to_stable_solve": _stable_solve_step(
            logger.solution_picks_history, task.solution_hash),
        "tail_loss": round(float(np.mean(logger.loss_curve[-TAIL:])), 3),
        "final_loss": float(logger.loss_curve[-1]),
        # --- capture payload (the point of E1-B) ---
        "solution_hash": task.solution_hash,
        "top1_hash": h1, "top2_hash": h2, "vote_margin": margin,
        "top1_grid": top1_sol, "top2_grid": top2_sol,
        "hash_scores_top8": dict(sorted(
            ((str(k), float(v)) for k, v in counts.items()),
            key=lambda kv: -kv[1])[:8]),
        "picks_history_rle": _rle(logger.solution_picks_history),
        "loss_curve": [round(float(x), 2) for x in logger.loss_curve],
        # --- reproducibility readout vs the banked same-config S6 run ---
        "banked_final_loss": banked["final_loss"] if banked else None,
        "banked_solved_top2": banked["solved_top2"] if banked else None,
    }


def done_jobs() -> dict[str, dict]:
    out = {}
    for f in ARTIFACTS.glob("job_e1b_*.json"):
        r = json.loads(f.read_text())
        out[r["name"]] = r
    return out


def _try_claim(name: str) -> bool:
    CLAIMS.mkdir(parents=True, exist_ok=True)
    try:
        with open(CLAIMS / f"{name}.claim", "x", encoding="utf-8") as f:
            f.write(f"pid={os.getpid()} at={time.time():.0f}\n")
        return True
    except FileExistsError:
        return False


def worker_loop() -> None:
    while True:
        done = done_jobs()
        remaining = [j for j in job_list() if j["name"] not in done]
        if not remaining:
            print("worker: queue empty, exiting", flush=True)
            return
        ran_one = False
        for job in remaining:
            if not _try_claim(job["name"]):
                continue
            print(f"=== {job['name']} ===", flush=True)
            result = run_job(job)
            (ARTIFACTS / f"job_e1b_{job['name']}.json").write_text(
                json.dumps(result, indent=2))
            ran_one = True
            break
        if not ran_one:
            time.sleep(30)


def status() -> dict:
    done = done_jobs()
    total = job_list()
    repro = []
    for r in done.values():
        if r.get("banked_final_loss") is not None:
            repro.append({
                "name": r["name"],
                "final_loss": round(r["final_loss"], 1),
                "banked": round(r["banked_final_loss"], 1),
                "solve_agrees": r["solved_top2"] == r["banked_solved_top2"],
            })
    return {
        "progress": f"{len(done)}/{len(total)} jobs",
        "solved_top2": sorted(r["name"] for r in done.values()
                              if r["solved_top2"]),
        "reproducibility_readout": sorted(repro, key=lambda r: r["name"]),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--worker", action="store_true")
    ap.add_argument("--clear-claims", action="store_true")
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()

    ARTIFACTS.mkdir(exist_ok=True)

    if args.clear_claims:
        done = done_jobs()
        n = 0
        for c in CLAIMS.glob("*.claim"):
            if c.stem not in done:
                c.unlink()
                n += 1
        print(f"cleared {n} stale claims")
        return
    if args.status:
        print(json.dumps(status(), indent=2))
        return
    if args.smoke:
        job = {"name": "smoke", "task": CHURN_TASKS[0], "kind": "smoke",
               "steps": 30, "seed": 0}
        r = run_job(job)
        r_small = {k: v for k, v in r.items()
                   if k not in ("picks_history_rle", "loss_curve",
                                "top1_grid", "top2_grid")}
        r_small["picks_rle_len"] = len(r["picks_history_rle"])
        r_small["loss_curve_len"] = len(r["loss_curve"])
        r_small["grids_present"] = (r["top1_grid"] is not None,
                                    r["top2_grid"] is not None)
        (HERE / "e1b_smoke.json").write_text(json.dumps(r, indent=2))
        print(json.dumps(r_small, indent=2, default=str))
        return
    if args.worker:
        worker_loop()
        print(json.dumps(status(), indent=2))
        return
    ap.print_help()


if __name__ == "__main__":
    main()
