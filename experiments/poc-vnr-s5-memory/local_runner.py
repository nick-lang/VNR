"""VNR Stage 5 (H9) — resumable LOCAL queue runner (3070 Ti, no cloud).

Runs the pre-registered H9 job list one task at a time, banking every result
to disk immediately; safe to stop (Ctrl+C / reboot) and re-run any time --
completed jobs are never recomputed.

Queue order is chosen for fast confidence:
  1. cold_00576224, cold_8597cfd7        -- do local colds reproduce H8?
  2. sanity_* (same-task warm, 600 steps) -- pre-registered validity gate
  3. remaining 9 colds (donor pool)
  4. 11 LOO warm runs (the hypothesis test)
  5. 5 exploratory probes on H8-unsolved tasks

Usage:
  python experiments/poc-vnr-s5-memory/local_runner.py --status
  python experiments/poc-vnr-s5-memory/local_runner.py --max-jobs 2
  python experiments/poc-vnr-s5-memory/local_runner.py            # run everything left
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
CARC = REPO / "references" / "CompressARC"
ARTIFACTS = HERE / "s5_artifacts"

sys.path.insert(0, str(HERE))

STEPS = 2000
SANITY_STEPS = 600  # gate asks for re-solve within ~200 steps; 600 is generous

SOLVED = [
    "00576224", "15663ba9", "1d0a4b61", "45737921", "6df30ad6", "8597cfd7",
    "903d1b4a", "ae58858e", "cd3c21df", "d2acf2cb", "ef26cbf6",
]
SANITY = ["00576224", "8597cfd7"]
UNSOLVED_PROBE = ["08573cc6", "0c786b71", "12997ef3", "1990f7a8", "20981f0e"]


def job_list() -> list[dict]:
    jobs = []
    early = SANITY + [t for t in SOLVED if t not in SANITY]
    for tid in early[:2]:
        jobs.append({"name": f"cold_{tid}", "kind": "cold", "task": tid, "steps": STEPS})
    for tid in SANITY:
        jobs.append({"name": f"sanity_{tid}", "kind": "sanity", "task": tid,
                     "steps": SANITY_STEPS, "needs": [f"cold_{tid}"]})
    for tid in early[2:]:
        jobs.append({"name": f"cold_{tid}", "kind": "cold", "task": tid, "steps": STEPS})
    all_colds = [f"cold_{t}" for t in SOLVED]
    for tid in SOLVED:
        jobs.append({"name": f"loo_{tid}", "kind": "loo", "task": tid, "steps": STEPS,
                     "needs": [c for c in all_colds if c != f"cold_{tid}"]})
    for tid in UNSOLVED_PROBE:
        jobs.append({"name": f"probe_{tid}", "kind": "probe", "task": tid, "steps": STEPS,
                     "needs": all_colds})
    return jobs


def done_jobs() -> dict[str, dict]:
    out = {}
    for f in ARTIFACTS.glob("job_*.json"):
        r = json.loads(f.read_text())
        out[r["name"]] = r
    return out


def _stable_solve_step(picks_history, solution_hash):
    solved = [solution_hash in picks for picks in picks_history]
    if not solved or not solved[-1]:
        return None
    s = len(solved)
    while s > 0 and solved[s - 1]:
        s -= 1
    return s


_ENV = {}


def _env():
    """Import CompressARC modules once (chdir + path setup)."""
    if _ENV:
        return _ENV
    import torch

    torch.set_default_dtype(torch.float32)
    torch.set_default_device("cuda")
    os.chdir(CARC)
    sys.path.insert(0, str(CARC))
    import arc_compressor
    import preprocessing
    import solution_selection
    import train
    import transfer

    _ENV.update(torch=torch, arc_compressor=arc_compressor, preprocessing=preprocessing,
                solution_selection=solution_selection, train=train, transfer=transfer)
    return _ENV


def run_job(job: dict) -> dict:
    e = _env()
    transfer = e["transfer"]
    torch = e["torch"]

    init_blob = None
    if job["kind"] == "sanity":
        init_blob = transfer.from_bytes((ARTIFACTS / f"donor_{job['task']}.pt").read_bytes())
    elif job["kind"] == "loo":
        donors = [transfer.from_bytes((ARTIFACTS / f"donor_{t}.pt").read_bytes())
                  for t in SOLVED if t != job["task"]]
        init_blob = transfer.average_weights(donors)
    elif job["kind"] == "probe":
        donors = [transfer.from_bytes((ARTIFACTS / f"donor_{t}.pt").read_bytes())
                  for t in SOLVED]
        init_blob = transfer.average_weights(donors)

    t0 = time.time()
    task = e["preprocessing"].preprocess_tasks("evaluation", [job["task"]])[0]
    model = e["arc_compressor"].ARCCompressor(task)
    if init_blob is not None:
        transfer.load_weights(model, init_blob)
    optimizer = torch.optim.Adam(model.weights_list, lr=0.01, betas=(0.5, 0.9))
    logger = e["solution_selection"].Logger(task)
    for step in range(job["steps"]):
        e["train"].take_step(task, model, optimizer, step, logger)
        if (step + 1) % 200 == 0:
            print(f"  [{job['name']}] step {step + 1}/{job['steps']} "
                  f"elapsed={time.time() - t0:.0f}s loss={logger.loss_curve[-1]:.1f}",
                  flush=True)

    top1 = (logger.solution_most_frequent is not None
            and hash(logger.solution_most_frequent) == task.solution_hash)
    top2 = top1 or (logger.solution_second_most_frequent is not None
                    and hash(logger.solution_second_most_frequent) == task.solution_hash)
    result = {
        "name": job["name"], "kind": job["kind"], "task": job["task"],
        "steps": job["steps"], "seconds": round(time.time() - t0, 1),
        "solved_top1": bool(top1), "solved_top2": bool(top2),
        "steps_to_stable_solve": _stable_solve_step(
            logger.solution_picks_history, task.solution_hash),
        "final_loss": float(logger.loss_curve[-1]) if logger.loss_curve else None,
    }
    if job["kind"] == "cold":
        (ARTIFACTS / f"donor_{job['task']}.pt").write_bytes(
            transfer.to_bytes(transfer.extract_weights(model)))
    return result


def summarize(done: dict[str, dict]) -> dict:
    cold = {r["task"]: r for r in done.values() if r["kind"] == "cold"}
    loo = {r["task"]: r for r in done.values() if r["kind"] == "loo"}
    sanity = [r for r in done.values() if r["kind"] == "sanity"]
    probe = [r for r in done.values() if r["kind"] == "probe"]

    out: dict = {
        "progress": f"{len(done)}/{len(job_list())} jobs",
        "cold_solved": f"{sum(r['solved_top2'] for r in cold.values())}/{len(cold)}",
        "sanity": [{"task": r["task"], "solved": r["solved_top2"],
                    "steps_to_stable_solve": r["steps_to_stable_solve"]} for r in sanity],
        "probe_new_solves": sorted(r["task"] for r in probe if r["solved_top2"]),
    }
    if loo:
        ratios = []
        retained = 0
        for tid, w in loo.items():
            if tid not in cold:
                continue
            c_steps = cold[tid]["steps_to_stable_solve"] or STEPS
            w_steps = w["steps_to_stable_solve"] or STEPS
            if w["solved_top2"]:
                retained += 1
            ratios.append({"task": tid, "warm": w_steps, "cold": c_steps,
                           "ratio": round(w_steps / max(c_steps, 1), 3)})
        out["loo_ratios"] = sorted(ratios, key=lambda r: r["task"])
        if len(ratios) == len(SOLVED):
            rs = sorted(r["ratio"] for r in ratios)
            median = rs[len(rs) // 2]
            sanity_ok = all(r["solved_top2"] and (r["steps_to_stable_solve"] or 9999) <= 200
                            for r in sanity) and len(sanity) == len(SANITY)
            if not sanity_ok:
                decision = "VOID (validity gate failed)"
            elif median <= 0.5 and retained >= 10:
                decision = "ACCEPT H9"
            elif median >= 1.0 or retained <= 8:
                decision = "KILL"
            else:
                decision = "INCONCLUSIVE"
            out.update(median_ratio=median, retained=f"{retained}/{len(SOLVED)}",
                       sanity_ok=sanity_ok, decision_h9=decision)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-jobs", type=int, default=0, help="0 = run all remaining")
    ap.add_argument("--status", action="store_true")
    args = ap.parse_args()

    ARTIFACTS.mkdir(exist_ok=True)
    done = done_jobs()

    if args.status:
        print(json.dumps(summarize(done), indent=2))
        return

    ran = 0
    for job in job_list():
        if job["name"] in done:
            continue
        missing = [n for n in job.get("needs", []) if n not in done]
        if missing:
            print(f"skip {job['name']} (waiting on {missing[0]}...)", flush=True)
            continue
        print(f"=== {job['name']} ({job['steps']} steps) ===", flush=True)
        result = run_job(job)
        (ARTIFACTS / f"job_{job['name']}.json").write_text(json.dumps(result, indent=2))
        done[job["name"]] = result
        print(json.dumps(result), flush=True)
        ran += 1
        if args.max_jobs and ran >= args.max_jobs:
            break

    summary = summarize(done)
    (HERE / "stage5_local_summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
