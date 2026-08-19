"""H16 — augmentation-voting selection (pre-registered in ledger/hypotheses.md).

K=4 exact task transforms (identity; rot90/flip_h/transpose each + a seeded
color permutation of colors 1-9), solved independently by unmodified
CompressARC (1000 steps, seed 0), answers REVERSE-MAPPED to the original frame
and voted. Jobs are claim-based and banked; the 8 gate jobs (tasks 1d0a4b61,
73182012) are identical to their full-run counterparts and are reused.

Usage: --selftest | --status | --worker [--gate-only] | --clear-claims
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

from s6_runner import DEV_SPLIT, _env, _stable_solve_step  # noqa: E402

ARTIFACTS = HERE / "h16_artifacts"
CLAIMS = ARTIFACTS / "claims_h16"

STEPS, SEED, TAIL = 1000, 0, 50
AUG_NAMES = ["identity", "rot90", "flip_h", "transpose"]
GATE_TASKS = ["1d0a4b61", "73182012"]


# ---------------------------------------------------------------- transforms
def _perm_for(task_id: str, aug: int):
    """Deterministic permutation of colors 1-9 (0 fixed) per (task, aug)."""
    import numpy as np
    if aug == 0:
        return list(range(10))
    rng = np.random.default_rng([int(task_id, 16) % (2**31), aug])
    p = list(range(1, 10))
    rng.shuffle(p)
    return [0] + p


def _d8(grid, aug: int, inverse: bool = False):
    import numpy as np
    g = np.array(grid)
    if aug == 1:                       # rot90 (ccw); inverse = rot -1
        g = np.rot90(g, -1 if inverse else 1)
    elif aug == 2:                     # flip_h; self-inverse
        g = np.fliplr(g)
    elif aug == 3:                     # transpose; self-inverse
        g = g.T
    return g


def transform_grid(grid, task_id: str, aug: int, inverse: bool = False):
    perm = _perm_for(task_id, aug)
    table = perm if not inverse else [perm.index(i) for i in range(10)]
    g = _d8(grid, aug, inverse)
    return [[table[int(v)] for v in row] for row in g]


def transform_problem(problem, solution, task_id, aug):
    tp = {"train": [{"input": transform_grid(p["input"], task_id, aug),
                     "output": transform_grid(p["output"], task_id, aug)}
                    for p in problem["train"]],
          "test": [{"input": transform_grid(p["input"], task_id, aug)}
                   for p in problem["test"]]}
    ts = [transform_grid(g, task_id, aug) for g in solution]
    return tp, ts


def ghash(grids) -> int:
    """Canonical hash of a list of grids (order = test examples)."""
    return hash(tuple(tuple(tuple(int(v) for v in row) for row in g)
                      for g in grids))


def _sol_to_grids(sol):
    """Logger solution object (nested tuples over test examples) -> list of
    grids as lists. Handles None."""
    if sol is None:
        return None
    return [[list(row) for row in ex] for ex in sol]


# ------------------------------------------------------------------- selftest
def selftest():
    raw = _load_raw()
    checked = 0
    for tid in DEV_SPLIT[:10]:
        problem, solution = raw[tid]
        for aug in range(4):
            tp, ts = transform_problem(problem, solution, tid, aug)
            back = [transform_grid(g, tid, aug, inverse=True) for g in ts]
            assert back == [
                [[int(v) for v in row] for row in g] for g in solution
            ], f"round-trip failed: {tid} aug{aug}"
            back_in = [transform_grid(p["input"], tid, aug, inverse=True)
                       for p in tp["train"]]
            assert back_in == [
                [[int(v) for v in row] for row in p["input"]]
                for p in problem["train"]
            ], f"train-input round-trip failed: {tid} aug{aug}"
            if aug == 0:
                assert ts == [[[int(v) for v in row] for row in g]
                              for g in solution], f"identity not identity: {tid}"
            checked += 1
    print(f"selftest OK: {checked} (task, aug) round-trips exact")


def _load_raw():
    """task_id -> (problem, solution) from the CompressARC dataset files."""
    e = _env()  # chdirs to the CompressARC repo
    with open("dataset/arc-agi_evaluation_challenges.json") as f:
        problems = json.load(f)
    with open("dataset/arc-agi_evaluation_solutions.json") as f:
        solutions = json.load(f)
    return {tid: (problems[tid], solutions[tid]) for tid in DEV_SPLIT}


# ---------------------------------------------------------------------- jobs
def job_list(gate_only=False):
    tasks = GATE_TASKS if gate_only else GATE_TASKS + [
        t for t in DEV_SPLIT if t not in GATE_TASKS]
    return [{"name": f"g{aug}_{tid}", "task": tid, "aug": aug}
            for tid in tasks for aug in range(4)]


def run_job(job):
    e = _env()
    torch = e["torch"]
    import numpy as np

    t0 = time.time()
    tid, aug = job["task"], job["aug"]
    raw = _load_raw()
    problem, solution = raw[tid]
    tp, ts = transform_problem(problem, solution, tid, aug)

    torch.manual_seed(SEED)
    np.random.seed(SEED)
    task = e["preprocessing"].Task(f"{tid}_g{aug}", tp, ts)
    model = e["arc_compressor"].ARCCompressor(task)
    opt = torch.optim.Adam(model.weights_list, lr=0.01, betas=(0.5, 0.9))
    logger = e["solution_selection"].Logger(task)
    for step in range(STEPS):
        e["train"].take_step(task, model, opt, step, logger)
        if (step + 1) % 500 == 0:
            print(f"  [{job['name']}] step {step + 1}/{STEPS} "
                  f"loss={logger.loss_curve[-1]:.1f}", flush=True)

    top1 = _sol_to_grids(logger.solution_most_frequent)
    top2 = _sol_to_grids(logger.solution_second_most_frequent)
    counts = logger.solution_hashes_count
    h1 = hash(logger.solution_most_frequent) if top1 else None
    h2 = hash(logger.solution_second_most_frequent) if top2 else None
    margin = (counts[h1] - counts[h2]
              if h1 in counts and h2 in counts and h1 != h2 else None)
    picks = logger.solution_picks_history
    stab = 0
    if picks:
        final = picks[-1][0]
        for p in reversed(picks):
            if p[0] != final:
                break
            stab += 1
    inv1 = [transform_grid(g, tid, aug, inverse=True) for g in top1] if top1 else None
    inv2 = [transform_grid(g, tid, aug, inverse=True) for g in top2] if top2 else None
    gt = [[list(map(int, row)) for row in g] for g in solution]

    return {
        "name": job["name"], "task": tid, "aug": aug,
        "aug_name": AUG_NAMES[aug], "steps": STEPS, "seed": SEED,
        "seconds": round(time.time() - t0, 1),
        "solved_in_frame_top1": bool(
            top1 and hash(logger.solution_most_frequent) == task.solution_hash),
        "solved_in_frame_top2": bool(
            (top1 and hash(logger.solution_most_frequent) == task.solution_hash)
            or (top2 and hash(logger.solution_second_most_frequent)
                == task.solution_hash)),
        "vote_margin": margin, "pick_stability": stab / max(len(picks), 1),
        "tail_loss": round(float(np.mean(logger.loss_curve[-TAIL:])), 3),
        "final_loss": float(logger.loss_curve[-1]),
        "top1_grids_origframe": inv1, "top2_grids_origframe": inv2,
        "top1_hash_origframe": ghash(inv1) if inv1 else None,
        "top2_hash_origframe": ghash(inv2) if inv2 else None,
        "gt_hash_origframe": ghash(gt),
        "solved_origframe_top1": bool(inv1 and ghash(inv1) == ghash(gt)),
    }


def done_jobs():
    out = {}
    for f in ARTIFACTS.glob("job_h16_*.json"):
        r = json.loads(f.read_text())
        out[r["name"]] = r
    return out


def _try_claim(name):
    CLAIMS.mkdir(parents=True, exist_ok=True)
    try:
        with open(CLAIMS / f"{name}.claim", "x") as f:
            f.write(f"pid={os.getpid()} at={time.time():.0f}\n")
        return True
    except FileExistsError:
        return False


def worker_loop(gate_only=False):
    while True:
        done = done_jobs()
        remaining = [j for j in job_list(gate_only) if j["name"] not in done]
        if not remaining:
            print("worker: queue empty, exiting", flush=True)
            return
        ran = False
        for job in remaining:
            if not _try_claim(job["name"]):
                continue
            print(f"=== {job['name']} ===", flush=True)
            r = run_job(job)
            (ARTIFACTS / f"job_h16_{job['name']}.json").write_text(
                json.dumps(r, indent=2))
            ran = True
            break
        if not ran:
            time.sleep(30)


def gate_status():
    done = done_jobs()
    gate = [r for r in done.values() if r["task"] in GATE_TASKS]
    out = {"gate_jobs": f"{len(gate)}/8"}
    if len(gate) < 8:
        return out
    core = [r for r in gate if r["task"] == GATE_TASKS[0]]
    b = any(r["solved_in_frame_top2"] for r in core if r["aug"] != 0)
    div = False
    for tid in GATE_TASKS:
        hs = {r["top1_hash_origframe"] for r in gate if r["task"] == tid
              if r["top1_hash_origframe"] is not None}
        if len(hs) >= 2:
            div = True
    out["b_validity_nonidentity_core_solve"] = b
    out["c_diversity_distinct_answers"] = div
    out["gate"] = "PASS" if (b and div) else "FAIL -> H16 VOID (do not run full)"
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--gate-status", action="store_true")
    ap.add_argument("--worker", action="store_true")
    ap.add_argument("--gate-only", action="store_true")
    ap.add_argument("--clear-claims", action="store_true")
    args = ap.parse_args()

    ARTIFACTS.mkdir(exist_ok=True)
    if args.selftest:
        selftest()
        return
    if args.clear_claims:
        done = done_jobs()
        n = 0
        for c in CLAIMS.glob("*.claim"):
            if c.stem not in done:
                c.unlink()
                n += 1
        print(f"cleared {n} stale claims")
        return
    if args.gate_status:
        print(json.dumps(gate_status(), indent=2))
        return
    if args.status:
        done = done_jobs()
        print(json.dumps({
            "progress": f"{len(done)}/{len(job_list())}",
            "solved_in_frame": sorted(r["name"] for r in done.values()
                                      if r["solved_in_frame_top2"]),
        }, indent=2))
        return
    if args.worker:
        worker_loop(gate_only=args.gate_only)
        return
    ap.print_help()


if __name__ == "__main__":
    main()
