"""VNR Stage 5f (H14) — jointly trained shared backbone.

Unlike H9 (average post-hoc) and H10 (transplant post-hoc), the backbone here
is created BY joint training: one set of transformation-weight tensors is
literally shared (aliased) across one CompressARC model per training task,
with per-task latents kept separate; training round-robins one step per task,
so every shared-weight update serves all tasks at once (single shared basin).

Job kinds (3 folds of 3 over the 9 A40-cold-solvable tasks; cold arm = banked
H9 A40 baselines, no recompute):

  cold5090_T  hardware rebase (2026-07-06): re-run each of the 11 H8-solved
              tasks cold at 1000 steps on the local RTX 5090 (A40 pods gone;
              cross-hardware caveat forbids comparing 5090 warms to A40
              colds). These become the cold arm for the ratio.
  fold_N    joint-train a backbone on the 6 tasks NOT in fold N
            (1000 cycles x 6 tasks = 6000 shared-weight updates); save
            backbone_fN.pt.
  fold_all  exploratory backbone on all 9 tasks -> backbone_all.pt.
  jval_N    validity gate: warm-start the first task of fold N's TRAINING set
            from backbone_fN; must re-solve stably within ~200 steps.
  jret_T    the hypothesis test: warm-start held-out task T from its fold's
            backbone, 1000 steps (the new iteration budget). Final
            transformation weights are saved (jretw_T.pt) for the
            delta-geometry readout (2026-07-06 lit-pass amendment).
  jprobe_T  exploratory: warm-start 3 H8-unsolved tasks from backbone_all.

Usage mirrors local_runner.py:  --status | --only JOB | --max-jobs N
Extra:      --deltas  (delta-geometry readout over saved jretw_*.pt)
            --worker  (claim-based loop; run N of these in parallel on one
                       GPU — the 5090 is <30% utilized by a single job, and
                       the decision metric is STEPS, not wall-clock, so
                       concurrency cannot affect comparability)
            --clear-claims  (drop stale claims after a crash)
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

from local_runner import (  # noqa: E402
    ARTIFACTS, SOLVED, UNSOLVED_PROBE, _env, _stable_solve_step,
)

# The 9 tasks whose A40 cold runs solved (fold composition fixed at
# pre-registration; unchanged by the 2026-07-06 hardware rebase).
SOLVED_A40 = [
    "00576224", "1d0a4b61", "45737921", "6df30ad6", "8597cfd7",
    "903d1b4a", "ae58858e", "d2acf2cb", "ef26cbf6",
]
FOLDS = [SOLVED_A40[0:3], SOLVED_A40[3:6], SOLVED_A40[6:9]]
PROBE_TASKS = UNSOLVED_PROBE[:3]
# Hardware rebase: cold arm re-run on the 5090 for ALL 11 H8-solved tasks
# (the 2 A40-cold-failures included, as a free cross-hardware datapoint).
COLD_TASKS = list(SOLVED)

JOINT_CYCLES = 1000
RET_STEPS = 1000   # iteration budget (pre-registered cut from 2000)
VAL_STEPS = 600    # gate asks for stable re-solve <= 200; 600 is generous

LATENT_ATTRS = ["multiposteriors", "target_capacities"]


def fold_of(task_id: str) -> int:
    return next(i for i, f in enumerate(FOLDS) if task_id in f)


def job_list() -> list[dict]:
    jobs = []
    for tid in COLD_TASKS:
        jobs.append({"name": f"cold5090_{tid}", "kind": "cold5090", "task": tid})
    for i in range(3):
        train_tasks = [t for t in SOLVED_A40 if t not in FOLDS[i]]
        jobs.append({"name": f"fold_{i}", "kind": "fold", "tasks": train_tasks})
    jobs.append({"name": "fold_all", "kind": "fold", "tasks": list(SOLVED_A40)})
    for i in range(3):
        train_tasks = [t for t in SOLVED_A40 if t not in FOLDS[i]]
        jobs.append({"name": f"jval_{i}", "kind": "jval", "task": train_tasks[0],
                     "backbone": f"backbone_f{i}.pt", "needs": [f"fold_{i}"]})
    for tid in SOLVED_A40:
        i = fold_of(tid)
        jobs.append({"name": f"jret_{tid}", "kind": "jret", "task": tid,
                     "backbone": f"backbone_f{i}.pt", "needs": [f"fold_{i}"]})
    for tid in PROBE_TASKS:
        jobs.append({"name": f"jprobe_{tid}", "kind": "jprobe", "task": tid,
                     "backbone": "backbone_all.pt", "needs": ["fold_all"]})
    return jobs


def done_jobs() -> dict[str, dict]:
    out = {}
    for f in ARTIFACTS.glob("job5f_*.json"):
        r = json.loads(f.read_text())
        out[r["name"]] = r
    return out


def _leaves(node, out: dict) -> None:
    """Collect leaf tensors (dedup by id — tied tensors appear repeatedly)."""
    import torch
    if node is None:
        return
    if isinstance(node, torch.Tensor):
        out[id(node)] = node
        return
    if isinstance(node, list):
        for c in node:
            _leaves(c, out)
        return
    if hasattr(node, "data") and hasattr(node, "multitensor_system"):
        _leaves(node.data, out)
        return
    raise TypeError(f"unexpected node type: {type(node)}")


def _alias(dst, src) -> None:
    """Replace dst's leaf tensors with src's tensor OBJECTS, in place.

    Position-wise parallel walk, so weight tying (the same object appearing at
    several positions) is preserved automatically.
    """
    import torch
    if hasattr(dst, "data") and hasattr(dst, "multitensor_system"):
        _alias(dst.data, src.data if hasattr(src, "data") else src)
        return
    assert isinstance(dst, list) and isinstance(src, list) and len(dst) == len(src)
    for i, (d, s) in enumerate(zip(dst, src)):
        if d is None:
            assert s is None
            continue
        if isinstance(d, torch.Tensor):
            assert tuple(d.shape) == tuple(s.shape), (
                f"shape mismatch: {tuple(d.shape)} vs {tuple(s.shape)}")
            dst[i] = s
        else:
            _alias(d, s if not hasattr(s, "data") else s.data)


def _share_weights(base, other, transfer) -> None:
    """Make `other` use `base`'s transformation-weight tensors."""
    for attr in transfer.TRANSFER_ATTRS:
        _alias(getattr(other, attr), getattr(base, attr))


def _joint_train(task_ids: list[str], out_name: str) -> dict:
    """Round-robin joint training with shared transformation weights."""
    e = _env()
    torch, transfer = e["torch"], e["transfer"]
    import numpy as np

    t0 = time.time()
    torch.manual_seed(0)
    np.random.seed(0)
    tasks = e["preprocessing"].preprocess_tasks("evaluation", task_ids)
    models = [e["arc_compressor"].ARCCompressor(t) for t in tasks]
    for m in models[1:]:
        _share_weights(models[0], m, transfer)

    params: dict = {}
    for attr in transfer.TRANSFER_ATTRS:
        _leaves(getattr(models[0], attr), params)
    for m in models:
        for attr in LATENT_ATTRS:
            _leaves(getattr(m, attr), params)
    opt = torch.optim.Adam(list(params.values()), lr=0.01, betas=(0.5, 0.9))
    loggers = [e["solution_selection"].Logger(t) for t in tasks]

    for cycle in range(JOINT_CYCLES):
        for task, model, logger in zip(tasks, models, loggers):
            e["train"].take_step(task, model, opt, cycle, logger)
        if (cycle + 1) % 100 == 0:
            losses = " ".join(f"{lg.loss_curve[-1]:.0f}" for lg in loggers)
            print(f"  [{out_name}] cycle {cycle + 1}/{JOINT_CYCLES} "
                  f"elapsed={time.time() - t0:.0f}s losses=[{losses}]", flush=True)

    (ARTIFACTS / out_name).write_bytes(
        transfer.to_bytes(transfer.extract_weights(models[0])))
    return {
        "tasks": task_ids, "cycles": JOINT_CYCLES,
        "seconds": round(time.time() - t0, 1),
        "first_losses": {tid: round(float(lg.loss_curve[0]), 1)
                         for tid, lg in zip(task_ids, loggers)},
        "final_losses": {tid: round(float(lg.loss_curve[-1]), 1)
                         for tid, lg in zip(task_ids, loggers)},
        "solved_during_joint": {tid: bool(
            lg.solution_most_frequent is not None
            and hash(lg.solution_most_frequent) == t.solution_hash
            or lg.solution_second_most_frequent is not None
            and hash(lg.solution_second_most_frequent) == t.solution_hash)
            for tid, lg, t in zip(task_ids, loggers, tasks)},
    }


def _warm_run(task_id: str, backbone: str | None, steps: int,
              save_weights: str | None = None) -> dict:
    """Train one task for `steps`; warm-start from `backbone` if given (else cold)."""
    e = _env()
    torch, transfer = e["torch"], e["transfer"]
    import numpy as np

    t0 = time.time()
    blob = (transfer.from_bytes((ARTIFACTS / backbone).read_bytes())
            if backbone else None)
    torch.manual_seed(0)
    np.random.seed(0)
    task = e["preprocessing"].preprocess_tasks("evaluation", [task_id])[0]
    model = e["arc_compressor"].ARCCompressor(task)
    if blob is not None:
        transfer.load_weights(model, blob)
    opt = torch.optim.Adam(model.weights_list, lr=0.01, betas=(0.5, 0.9))
    logger = e["solution_selection"].Logger(task)
    src = backbone or "cold"
    for step in range(steps):
        e["train"].take_step(task, model, opt, step, logger)
        if (step + 1) % 200 == 0:
            print(f"  [{task_id}<-{src}] step {step + 1}/{steps} "
                  f"elapsed={time.time() - t0:.0f}s loss={logger.loss_curve[-1]:.1f}",
                  flush=True)
    if save_weights:
        (ARTIFACTS / save_weights).write_bytes(
            transfer.to_bytes(transfer.extract_weights(model)))
    top1 = (logger.solution_most_frequent is not None
            and hash(logger.solution_most_frequent) == task.solution_hash)
    top2 = top1 or (logger.solution_second_most_frequent is not None
                    and hash(logger.solution_second_most_frequent) == task.solution_hash)
    return {"task": task_id, "backbone": backbone, "steps": steps,
            "seconds": round(time.time() - t0, 1),
            "solved_top1": bool(top1), "solved_top2": bool(top2),
            "steps_to_stable_solve": _stable_solve_step(
                logger.solution_picks_history, task.solution_hash),
            "final_loss": float(logger.loss_curve[-1]) if logger.loss_curve else None}


def run_job(job: dict) -> dict:
    if job["kind"] == "fold":
        out_name = ("backbone_all.pt" if job["name"] == "fold_all"
                    else f"backbone_f{job['name'].split('_')[1]}.pt")
        result = _joint_train(job["tasks"], out_name)
    elif job["kind"] == "cold5090":
        result = _warm_run(job["task"], None, RET_STEPS)
    else:
        steps = VAL_STEPS if job["kind"] == "jval" else RET_STEPS
        save = f"jretw_{job['task']}.pt" if job["kind"] == "jret" else None
        result = _warm_run(job["task"], job["backbone"], steps, save_weights=save)
    result.update(name=job["name"], kind=job["kind"])
    return result


def summarize(done: dict[str, dict]) -> dict:
    # Cold arm = the 5090 rebased colds (hardware pivot 2026-07-06); the old
    # A40 job_cold_*.json files are no longer decision-bearing.
    cold = {r["task"]: r for r in done.values() if r["kind"] == "cold5090"}
    jret = {r["task"]: r for r in done.values() if r["kind"] == "jret"}
    jval = sorted((r for r in done.values() if r["kind"] == "jval"),
                  key=lambda r: r["name"])
    jprobe = [r for r in done.values() if r["kind"] == "jprobe"]

    out: dict = {
        "progress": f"{len(done)}/{len(job_list())} jobs",
        "cold5090_solved": f"{sum(r['solved_top2'] for r in cold.values())}/{len(cold)}",
        "cold5090_unsolved_tasks": sorted(
            t for t, r in cold.items() if not r["solved_top2"]),
        "validity": [{"fold": r["name"], "task": r["task"],
                      "steps_to_stable_solve": r["steps_to_stable_solve"]}
                     for r in jval],
        "probe_new_solves": sorted(r["task"] for r in jprobe if r["solved_top2"]),
    }
    if jret and cold:
        ratios, retained = [], 0
        for tid, r in sorted(jret.items()):
            if tid not in cold:
                continue
            c = cold[tid]["steps_to_stable_solve"] or RET_STEPS
            w = r["steps_to_stable_solve"] or RET_STEPS
            if r["solved_top2"]:
                retained += 1
            ratios.append({"task": tid, "jret": w, "cold": c,
                           "ratio": round(w / max(c, 1), 3)})
        out["ratios"] = ratios
        if len(ratios) == len(SOLVED_A40):
            rs = sorted(r["ratio"] for r in ratios)
            median = rs[len(rs) // 2]
            gate_ok = (len(jval) == 3 and all(
                r["solved_top2"] and (r["steps_to_stable_solve"] or 9999) <= 200
                for r in jval))
            if not gate_ok:
                decision = "VOID (validity gate failed)"
            elif median <= 0.5 and retained >= 8:
                decision = "ACCEPT H14"
            elif median >= 1.0 or retained <= 7:
                decision = "KILL"
            else:
                decision = "INCONCLUSIVE"
            out.update(median_ratio=median, retained=f"{retained}/{len(SOLVED_A40)}",
                       validity_ok=gate_ok, decision_h14=decision)
    return out


def _flatten_blob(blob) -> "object":
    """Flatten a transfer blob (nested lists of tensors) into one 1-D tensor."""
    import torch

    flat = []

    def walk(node):
        if node is None:
            return
        if isinstance(node, torch.Tensor):
            flat.append(node.float().flatten())
            return
        if isinstance(node, list):
            for c in node:
                walk(c)
            return
        raise TypeError(f"unexpected node: {type(node)}")

    for attr in sorted(blob.keys()):
        walk(blob[attr])
    return torch.cat(flat)


def delta_geometry() -> dict:
    """Secondary readout (2026-07-06 amendment, not decision-bearing):
    per-task deltas vs each fold's backbone; pairwise cosine matrix.
    Task-vector geometry predicts deltas from a shared base are composable."""
    import torch
    sys.path.insert(0, str(HERE))
    import transfer

    deltas, norms = {}, {}
    for tid in SOLVED_A40:
        w = ARTIFACTS / f"jretw_{tid}.pt"
        bb = ARTIFACTS / f"backbone_f{fold_of(tid)}.pt"
        if not (w.exists() and bb.exists()):
            continue
        d = (_flatten_blob(transfer.from_bytes(w.read_bytes()))
             - _flatten_blob(transfer.from_bytes(bb.read_bytes())))
        deltas[tid] = d
        norms[tid] = round(float(d.norm()), 2)
    tids = sorted(deltas)
    cos = {}
    for i, a in enumerate(tids):
        for b in tids[i + 1:]:
            c = torch.nn.functional.cosine_similarity(
                deltas[a], deltas[b], dim=0)
            cos[f"{a}~{b}"] = round(float(c), 4)
    vals = sorted(cos.values())
    out = {"tasks": tids, "delta_norms": norms, "pairwise_cosine": cos}
    if vals:
        out["cosine_median"] = vals[len(vals) // 2]
        out["cosine_min"] = vals[0]
        out["cosine_max"] = vals[-1]
    return out


CLAIMS = ARTIFACTS / "claims5f"


def _try_claim(name: str) -> bool:
    """Atomically claim a job; False if another worker holds it."""
    CLAIMS.mkdir(exist_ok=True)
    try:
        with open(CLAIMS / f"{name}.claim", "x", encoding="utf-8") as f:
            f.write(f"pid={os.getpid()} at={time.time():.0f}\n")
        return True
    except FileExistsError:
        return False


def worker_loop() -> None:
    """Pull runnable unclaimed jobs until the queue is exhausted."""
    while True:
        done = done_jobs()
        remaining = [j for j in job_list() if j["name"] not in done]
        if not remaining:
            print("worker: queue empty, exiting", flush=True)
            return
        ran_one = False
        for job in remaining:
            if any(n not in done for n in job.get("needs", [])):
                continue
            if not _try_claim(job["name"]):
                continue
            print(f"=== {job['name']} ===", flush=True)
            result = run_job(job)
            (ARTIFACTS / f"job5f_{job['name']}.json").write_text(
                json.dumps(result, indent=2))
            ran_one = True
            break
        if not ran_one:
            # Jobs remain but all are claimed or dep-blocked; wait for folds.
            time.sleep(30)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-jobs", type=int, default=0)
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--only", default="")
    ap.add_argument("--deltas", action="store_true")
    ap.add_argument("--worker", action="store_true")
    ap.add_argument("--clear-claims", action="store_true")
    args = ap.parse_args()

    if args.clear_claims:
        done = done_jobs()
        n = 0
        for c in CLAIMS.glob("*.claim"):
            if c.stem not in done:
                c.unlink()
                n += 1
        print(f"cleared {n} stale claims")
        return

    if args.worker:
        ARTIFACTS.mkdir(exist_ok=True)
        worker_loop()
        done = done_jobs()
        if len(done) == len(job_list()):
            summary = summarize(done)
            (HERE / "stage5f_summary.json").write_text(json.dumps(summary, indent=2))
            print(json.dumps(summary, indent=2))
        return

    if args.deltas:
        result = delta_geometry()
        (ARTIFACTS / "delta_geometry.json").write_text(json.dumps(result, indent=2))
        print(json.dumps(result, indent=2))
        return

    ARTIFACTS.mkdir(exist_ok=True)
    done = done_jobs()

    if args.status:
        print(json.dumps(summarize(done), indent=2))
        return

    if args.only:
        job = next((j for j in job_list() if j["name"] == args.only), None)
        if job is None:
            raise SystemExit(f"unknown job: {args.only}")
        if job["name"] in done:
            print(f"{job['name']} already done", flush=True)
            return
        missing = [n for n in job.get("needs", []) if n not in done]
        if missing:
            raise SystemExit(f"{job['name']} blocked on {missing}")
        result = run_job(job)
        (ARTIFACTS / f"job5f_{job['name']}.json").write_text(json.dumps(result, indent=2))
        print(json.dumps(result), flush=True)
        return

    ran = 0
    for job in job_list():
        if job["name"] in done:
            continue
        if any(n not in done for n in job.get("needs", [])):
            continue
        print(f"=== {job['name']} ===", flush=True)
        result = run_job(job)
        (ARTIFACTS / f"job5f_{job['name']}.json").write_text(json.dumps(result, indent=2))
        done[job["name"]] = result
        ran += 1
        if args.max_jobs and ran >= args.max_jobs:
            break

    summary = summarize(done)
    (HERE / "stage5f_summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
