"""VNR Stage 5b (H10) — addressable memory: retrieval-gated donor selection.

Job kinds (LOO over the 11 H8-solved tasks; cold baselines = banked H9
phase-1 results, same A40 hardware):

  sel_T     probe each of the 10 other donors: load donor weights + fresh
            latents, train 100 steps (identical RNG seed per candidate),
            score = mean loss over the last 20 probe steps; bank ranking.
  ret_T     warm-start from the selected donor, 2000 steps, H9 metrics.
  selfsel_T self-retrieval validity gate (2 tasks): probe the FULL 11-donor
            pool; PASS iff the task's own donor ranks #1.

Usage mirrors local_runner.py:  --status | --only JOB | --max-jobs N
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from local_runner import (  # noqa: E402
    ARTIFACTS, SANITY, SOLVED, STEPS, _env, _stable_solve_step,
)

PROBE_STEPS = 100
SCORE_LAST = 20


def job_list() -> list[dict]:
    jobs = []
    for tid in SOLVED:
        jobs.append({"name": f"sel_{tid}", "kind": "select", "task": tid})
    for tid in SANITY:
        jobs.append({"name": f"selfsel_{tid}", "kind": "selfselect", "task": tid})
    for tid in SOLVED:
        jobs.append({"name": f"ret_{tid}", "kind": "ret", "task": tid,
                     "needs": [f"sel_{tid}"]})
    return jobs


def done_jobs() -> dict[str, dict]:
    out = {}
    for f in ARTIFACTS.glob("job5b_*.json"):
        r = json.loads(f.read_text())
        out[r["name"]] = r
    return out


def _probe(task_id: str, donor_ids: list[str]) -> list[dict]:
    """Score candidate donors by short-trial loss; lower is better."""
    e = _env()
    torch, transfer = e["torch"], e["transfer"]
    import numpy as np

    scores = []
    for did in donor_ids:
        blob = transfer.from_bytes((ARTIFACTS / f"donor_{did}.pt").read_bytes())
        torch.manual_seed(0)
        np.random.seed(0)
        task = e["preprocessing"].preprocess_tasks("evaluation", [task_id])[0]
        model = e["arc_compressor"].ARCCompressor(task)
        transfer.load_weights(model, blob)
        opt = torch.optim.Adam(model.weights_list, lr=0.01, betas=(0.5, 0.9))
        logger = e["solution_selection"].Logger(task)
        for step in range(PROBE_STEPS):
            e["train"].take_step(task, model, opt, step, logger)
        score = float(sum(logger.loss_curve[-SCORE_LAST:]) / SCORE_LAST)
        scores.append({"donor": did, "score": round(score, 2)})
        print(f"    probe {task_id} <- {did}: {score:.1f}", flush=True)
    return sorted(scores, key=lambda s: s["score"])


def run_job(job: dict) -> dict:
    e = _env()
    torch, transfer = e["torch"], e["transfer"]
    import numpy as np

    t0 = time.time()
    tid = job["task"]

    if job["kind"] == "select":
        ranking = _probe(tid, [d for d in SOLVED if d != tid])
        return {"name": job["name"], "kind": job["kind"], "task": tid,
                "selected": ranking[0]["donor"], "ranking": ranking,
                "seconds": round(time.time() - t0, 1)}

    if job["kind"] == "selfselect":
        ranking = _probe(tid, list(SOLVED))
        return {"name": job["name"], "kind": job["kind"], "task": tid,
                "self_first": ranking[0]["donor"] == tid, "ranking": ranking,
                "seconds": round(time.time() - t0, 1)}

    # ret: warm-start from the selected donor, full budget
    sel = json.loads((ARTIFACTS / f"job5b_sel_{tid}.json").read_text())["selected"]
    blob = transfer.from_bytes((ARTIFACTS / f"donor_{sel}.pt").read_bytes())
    torch.manual_seed(0)
    np.random.seed(0)
    task = e["preprocessing"].preprocess_tasks("evaluation", [tid])[0]
    model = e["arc_compressor"].ARCCompressor(task)
    transfer.load_weights(model, blob)
    opt = torch.optim.Adam(model.weights_list, lr=0.01, betas=(0.5, 0.9))
    logger = e["solution_selection"].Logger(task)
    for step in range(STEPS):
        e["train"].take_step(task, model, opt, step, logger)
        if (step + 1) % 400 == 0:
            print(f"  [{job['name']}<-{sel}] step {step + 1}/{STEPS} "
                  f"elapsed={time.time() - t0:.0f}s loss={logger.loss_curve[-1]:.1f}",
                  flush=True)
    top1 = (logger.solution_most_frequent is not None
            and hash(logger.solution_most_frequent) == task.solution_hash)
    top2 = top1 or (logger.solution_second_most_frequent is not None
                    and hash(logger.solution_second_most_frequent) == task.solution_hash)
    return {"name": job["name"], "kind": job["kind"], "task": tid, "donor": sel,
            "steps": STEPS, "seconds": round(time.time() - t0, 1),
            "solved_top1": bool(top1), "solved_top2": bool(top2),
            "steps_to_stable_solve": _stable_solve_step(
                logger.solution_picks_history, task.solution_hash),
            "final_loss": float(logger.loss_curve[-1]) if logger.loss_curve else None}


def summarize(done: dict[str, dict]) -> dict:
    cold = {}
    for f in ARTIFACTS.glob("job_cold_*.json"):
        r = json.loads(f.read_text())
        cold[r["task"]] = r
    ret = {r["task"]: r for r in done.values() if r["kind"] == "ret"}
    selfsel = [r for r in done.values() if r["kind"] == "selfselect"]
    sel = {r["task"]: r for r in done.values() if r["kind"] == "select"}

    out: dict = {
        "progress": f"{len(done)}/{len(job_list())} jobs",
        "selections": {t: r["selected"] for t, r in sorted(sel.items())},
        "self_retrieval": [{"task": r["task"], "own_first": r["self_first"],
                            "top": r["ranking"][0]["donor"]} for r in selfsel],
    }
    if ret and cold:
        ratios, retained = [], 0
        for tid, r in sorted(ret.items()):
            if tid not in cold:
                continue
            c = cold[tid]["steps_to_stable_solve"] or STEPS
            w = r["steps_to_stable_solve"] or STEPS
            if r["solved_top2"]:
                retained += 1
            ratios.append({"task": tid, "donor": r["donor"], "ret": w, "cold": c,
                           "ratio": round(w / max(c, 1), 3),
                           "full_cost_ratio": round((w + PROBE_STEPS * 10) / max(c, 1), 3)})
        out["ratios"] = ratios
        if len(ratios) == len(SOLVED):
            rs = sorted(r["ratio"] for r in ratios)
            median = rs[len(rs) // 2]
            gate_ok = all(r["self_first"] for r in selfsel) and len(selfsel) == len(SANITY)
            full_rs = sorted(r["full_cost_ratio"] for r in ratios)
            if not gate_ok:
                decision = "VOID (self-retrieval gate failed)"
            elif median <= 0.5 and retained >= 10:
                decision = "ACCEPT H10"
            elif median >= 1.0 or retained <= 8:
                decision = "KILL"
            else:
                decision = "INCONCLUSIVE"
            out.update(median_ratio=median,
                       median_full_cost_ratio=full_rs[len(full_rs) // 2],
                       retained=f"{retained}/{len(SOLVED)}",
                       self_retrieval_ok=gate_ok, decision_h10=decision)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-jobs", type=int, default=0)
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--only", default="")
    args = ap.parse_args()

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
        (ARTIFACTS / f"job5b_{job['name']}.json").write_text(json.dumps(result, indent=2))
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
        (ARTIFACTS / f"job5b_{job['name']}.json").write_text(json.dumps(result, indent=2))
        done[job["name"]] = result
        ran += 1
        if args.max_jobs and ran >= args.max_jobs:
            break

    summary = summarize(done)
    (HERE / "stage5b_summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
