"""VNR Stage 3b experiment: object-mapped substrate vs whole-grid search (H7-v2).

Arms on identical tasks:
  raw       = Stage-1 geometric BFS (unchanged control)
  objectmap = per-object rule induction (rules.py), verified by re-simulation
  union     = objectmap, else raw BFS  <- the system under test

Primary: 50-task ARC-AGI-1 dev split. Secondary: 30-task ARC-AGI-2 probe.
Decision rule pre-registered in ledger/hypotheses.md (H7-v2).
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
S1 = HERE.parent / "poc-vnr-s1-library"
sys.path.insert(0, str(S1))
sys.path.insert(0, str(HERE))

import dsl  # noqa: E402
import search  # noqa: E402
import tasks as s1_tasks  # noqa: E402
import rules  # noqa: E402

REPO = HERE.parents[1]
ARC2_EVAL = REPO / "data" / "arc-agi-2" / "data" / "evaluation"


def load_arc_dir(d: Path, limit: int) -> list[s1_tasks.Task]:
    out = []
    for f in sorted(d.glob("*.json"))[:limit]:
        obj = json.loads(f.read_text())
        train = [(np.array(p["input"]), np.array(p["output"])) for p in obj["train"]]
        test = [(np.array(p["input"]), np.array(p["output"])) for p in obj["test"] if "output" in p]
        out.append(s1_tasks.Task(name=f.stem, train=train, test=test))
    return out


def test_acc_rule(rule: dict, test) -> float:
    if not test:
        return float("nan")
    ok = 0
    for inp, out in test:
        pred = rules.apply_rule(rule, inp)
        if pred is not None and pred.shape == out.shape and np.array_equal(pred, out):
            ok += 1
    return ok / len(test)


def run_tasks(task_list, budget: int, max_depth: int, label: str):
    prim_ops, prim_names = dict(dsl.PRIMITIVES), list(dsl.PRIMITIVES)
    per_task = {}
    for i, t in enumerate(task_list):
        rule = rules.induce(t.train)
        raw = search.search_task(t.train, prim_ops, prim_names, budget=budget, max_depth=max_depth)
        entry = {
            "objectmap_solved": rule is not None,
            "rule": ({k: v for k, v in rule.items() if k != "_mapping"} if rule else None),
            "objectmap_test_acc": test_acc_rule(rule, t.test) if rule else None,
            "raw_solved": raw.solved,
            "raw_test_acc": search.test_accuracy(raw.program, t.test) if raw.solved else None,
        }
        entry["union_solved"] = entry["objectmap_solved"] or entry["raw_solved"]
        entry["union_test_acc"] = (
            entry["objectmap_test_acc"] if entry["objectmap_solved"] else entry["raw_test_acc"]
        )
        per_task[t.name] = entry
        print(f"[{label}] {i + 1}/{len(task_list)} {t.name} "
              f"objmap={entry['objectmap_solved']} raw={raw.solved}", flush=True)
    return per_task


def summarize(per_task: dict) -> dict:
    def arm(prefix):
        solved = {k: v for k, v in per_task.items() if v[f"{prefix}_solved"]}
        accs = [v[f"{prefix}_test_acc"] for v in solved.values()
                if v[f"{prefix}_test_acc"] is not None and v[f"{prefix}_test_acc"] == v[f"{prefix}_test_acc"]]
        return {
            "n_solved": len(solved),
            "solve_rate": len(solved) / max(1, len(per_task)),
            "solved_ids": sorted(solved),
            "mean_test_acc_on_solved": (sum(accs) / len(accs)) if accs else None,
        }
    return {"raw": arm("raw"), "objectmap": arm("objectmap"), "union": arm("union")}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--budget", type=int, default=50_000)
    ap.add_argument("--max-depth", type=int, default=7)
    ap.add_argument("--arc2-probe", type=int, default=30)
    ap.add_argument("--out", default=str(HERE / "stage3b_result.json"))
    args = ap.parse_args()

    t0 = time.time()
    dev = s1_tasks.load_arc_dev()
    dev_res = run_tasks(dev, args.budget, args.max_depth, "dev")
    dev_sum = summarize(dev_res)

    n_union, n_raw = dev_sum["union"]["n_solved"], dev_sum["raw"]["n_solved"]
    if n_union >= 5 and n_union >= 4 * max(1, n_raw):
        decision = "ACCEPT H7-v2"
    elif n_union <= 2:
        decision = "KILL (hand-built program substrate road judged closed at this effort level)"
    else:
        decision = "INCONCLUSIVE"

    arc2_sum = None
    if args.arc2_probe and ARC2_EVAL.exists():
        a2 = load_arc_dir(ARC2_EVAL, args.arc2_probe)
        arc2_sum = summarize(run_tasks(a2, args.budget, args.max_depth, "arc2"))

    result = {
        "config": vars(args),
        "dev": dev_sum,
        "decision_h7v2": decision,
        "arc2": arc2_sum,
        "per_task_dev": dev_res,
        "seconds": round(time.time() - t0, 1),
    }
    Path(args.out).write_text(json.dumps(result, indent=2))
    print(json.dumps({k: result[k] for k in ("dev", "decision_h7v2", "arc2", "seconds")}, indent=2))


if __name__ == "__main__":
    main()
