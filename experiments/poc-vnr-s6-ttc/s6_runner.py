"""VNR Stage 6 (H15) — restart diversity + label-free MDL selection.

On the 39 H8-unsolved dev-split tasks, at matched total compute (2000 steps):
  a_T       arm A (control): 1 x 2000 steps, seed 0 (H8 protocol on 5090)
  b_T_s1/2  arm B (treatment): 2 x 1000 steps, seeds 1 and 2; the run with the
            lower mean loss over its final 50 steps is selected (label-free
            MDL proxy); arm B's answer = that run's top-2 picks.
  seedchk_T seed-sensitivity readout (not decision-bearing): the 9
            5090-cold-solvable tasks at seed 1, 1000 steps.

Pre-registered rule (ledger/hypotheses.md H15): ACCEPT if B >= A + 2 and
B >= 2; KILL if B <= A; else inconclusive.

Usage: --status | --worker (run N in parallel) | --clear-claims | --only JOB
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "experiments" / "poc-vnr-s5-memory"))

from local_runner import SOLVED as H8_SOLVED, _env, _stable_solve_step  # noqa: E402

ARTIFACTS = HERE / "s6_artifacts"
CLAIMS = ARTIFACTS / "claims6"

DEV_SPLIT = json.loads((REPO / "data" / "dev_split_arc1.json").read_text())["task_ids"]
UNSOLVED = [t for t in DEV_SPLIT if t not in H8_SOLVED]
# The 9 tasks that solved cold on the 5090 (H14 rebase; = the A40 set).
SOLVED_5090 = [
    "00576224", "1d0a4b61", "45737921", "6df30ad6", "8597cfd7",
    "903d1b4a", "ae58858e", "d2acf2cb", "ef26cbf6",
]

A_STEPS = 2000
B_STEPS = 1000
TAIL = 50  # selection = mean loss over the final TAIL steps


def job_list() -> list[dict]:
    jobs = []
    for tid in UNSOLVED:
        jobs.append({"name": f"a_{tid}", "task": tid, "kind": "a",
                     "steps": A_STEPS, "seed": 0})
        jobs.append({"name": f"b_{tid}_s1", "task": tid, "kind": "b",
                     "steps": B_STEPS, "seed": 1})
        jobs.append({"name": f"b_{tid}_s2", "task": tid, "kind": "b",
                     "steps": B_STEPS, "seed": 2})
    for tid in SOLVED_5090:
        jobs.append({"name": f"seedchk_{tid}", "task": tid, "kind": "seedchk",
                     "steps": B_STEPS, "seed": 1})
    return jobs


def done_jobs() -> dict[str, dict]:
    out = {}
    for f in ARTIFACTS.glob("job6_*.json"):
        r = json.loads(f.read_text())
        out[r["name"]] = r
    return out


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
                  f"elapsed={time.time() - t0:.0f}s loss={logger.loss_curve[-1]:.1f}",
                  flush=True)
    top1 = (logger.solution_most_frequent is not None
            and hash(logger.solution_most_frequent) == task.solution_hash)
    top2 = top1 or (logger.solution_second_most_frequent is not None
                    and hash(logger.solution_second_most_frequent) == task.solution_hash)
    return {
        "name": job["name"], "kind": job["kind"], "task": job["task"],
        "steps": job["steps"], "seed": job["seed"],
        "seconds": round(time.time() - t0, 1),
        "solved_top1": bool(top1), "solved_top2": bool(top2),
        "steps_to_stable_solve": _stable_solve_step(
            logger.solution_picks_history, task.solution_hash),
        "tail_loss": round(float(np.mean(logger.loss_curve[-TAIL:])), 3),
        "final_loss": float(logger.loss_curve[-1]) if logger.loss_curve else None,
    }


def summarize(done: dict[str, dict]) -> dict:
    a = {r["task"]: r for r in done.values() if r["kind"] == "a"}
    b1 = {r["task"]: r for r in done.values()
          if r["kind"] == "b" and r["seed"] == 1}
    b2 = {r["task"]: r for r in done.values()
          if r["kind"] == "b" and r["seed"] == 2}
    seedchk = {r["task"]: r for r in done.values() if r["kind"] == "seedchk"}

    complete = [t for t in UNSOLVED if t in a and t in b1 and t in b2]
    a_solves, b_solves, union_solves = [], [], []
    sel_right, sel_cases = 0, 0
    for t in complete:
        sel = b1[t] if b1[t]["tail_loss"] <= b2[t]["tail_loss"] else b2[t]
        if a[t]["solved_top2"]:
            a_solves.append(t)
        if sel["solved_top2"]:
            b_solves.append(t)
        if b1[t]["solved_top2"] or b2[t]["solved_top2"]:
            union_solves.append(t)
            if b1[t]["solved_top2"] != b2[t]["solved_top2"]:
                sel_cases += 1
                solver = b1[t] if b1[t]["solved_top2"] else b2[t]
                if sel is solver:
                    sel_right += 1

    out: dict = {
        "progress": f"{len(done)}/{len(job_list())} jobs",
        "tasks_complete": f"{len(complete)}/{len(UNSOLVED)}",
        "armA_solves": sorted(a_solves),
        "armB_solves": sorted(b_solves),
        "unionB_oracle_solves": sorted(union_solves),
        "selection_accuracy": f"{sel_right}/{sel_cases}",
        "seedchk_retained": f"{sum(r['solved_top2'] for r in seedchk.values())}"
                            f"/{len(seedchk)}",
        "seedchk_lost": sorted(t for t, r in seedchk.items()
                               if not r["solved_top2"]),
    }
    if len(complete) == len(UNSOLVED):
        na, nb = len(a_solves), len(b_solves)
        if nb >= na + 2 and nb >= 2:
            decision = "ACCEPT H15"
        elif nb <= na:
            decision = "KILL"
        else:
            decision = "INCONCLUSIVE"
        out["decision_h15"] = decision
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
            (ARTIFACTS / f"job6_{job['name']}.json").write_text(
                json.dumps(result, indent=2))
            ran_one = True
            break
        if not ran_one:
            time.sleep(30)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--worker", action="store_true")
    ap.add_argument("--clear-claims", action="store_true")
    ap.add_argument("--only", default="")
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
        print(json.dumps(summarize(done_jobs()), indent=2))
        return

    if args.only:
        job = next((j for j in job_list() if j["name"] == args.only), None)
        if job is None:
            raise SystemExit(f"unknown job: {args.only}")
        if job["name"] in done_jobs():
            print(f"{job['name']} already done", flush=True)
            return
        result = run_job(job)
        (ARTIFACTS / f"job6_{job['name']}.json").write_text(
            json.dumps(result, indent=2))
        print(json.dumps(result), flush=True)
        return

    if args.worker:
        worker_loop()
        done = done_jobs()
        summary = summarize(done)
        (HERE / "stage6_summary.json").write_text(json.dumps(summary, indent=2))
        print(json.dumps(summary, indent=2))
        return

    ap.print_help()


if __name__ == "__main__":
    main()
