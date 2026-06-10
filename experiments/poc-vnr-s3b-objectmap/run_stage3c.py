"""VNR Stage 3c experiment: more rule families + stability guard (H7-v3).

"Solved" (v3) = train-consistent rule that (a) predicts on every test input
(no abstention) and (b) survives leave-one-out re-induction with identical
predictions on all test inputs. Unguarded counts reported for transparency.

Arms: raw BFS (control, unguarded) | object-map (guarded) | union (guarded).
Decision rule pre-registered in ledger/hypotheses.md (H7-v3).
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
from run_stage3b import load_arc_dir, test_acc_rule, ARC2_EVAL  # noqa: E402


def guarded_induce(train, test_inputs):
    """Returns (rule_or_None, status) where status explains guard outcomes."""
    full = rules.induce(train)
    if full is None:
        return None, "no_rule"
    preds = [rules.apply_rule(full, ti) for ti in test_inputs]
    if any(p is None for p in preds):
        return None, "abstain"
    for k in range(len(train)):
        sub = train[:k] + train[k + 1 :]
        if not sub:
            continue
        r_k = rules.induce(sub)
        if r_k is None:
            return None, "loo_no_rule"
        for ti, p in zip(test_inputs, preds):
            pk = rules.apply_rule(r_k, ti)
            if pk is None or pk.shape != p.shape or not np.array_equal(pk, p):
                return None, "loo_disagree"
    return full, "pass"


def run_tasks(task_list, budget: int, max_depth: int, label: str):
    prim_ops, prim_names = dict(dsl.PRIMITIVES), list(dsl.PRIMITIVES)
    per_task = {}
    for i, t in enumerate(task_list):
        test_inputs = [inp for inp, _ in t.test]
        unguarded = rules.induce(t.train)
        rule, guard_status = guarded_induce(t.train, test_inputs)
        raw = search.search_task(t.train, prim_ops, prim_names, budget=budget, max_depth=max_depth)
        entry = {
            "unguarded_solved": unguarded is not None,
            "unguarded_family": unguarded["family"] if unguarded else None,
            "guard_status": guard_status,
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
              f"guarded={entry['objectmap_solved']} ({guard_status}) raw={raw.solved}", flush=True)
    return per_task


def summarize(per_task: dict) -> dict:
    def arm(flag, acc_key):
        solved = {k: v for k, v in per_task.items() if v[flag]}
        accs = [v[acc_key] for v in solved.values()
                if v.get(acc_key) is not None and v[acc_key] == v[acc_key]]
        return {
            "n_solved": len(solved),
            "solve_rate": len(solved) / max(1, len(per_task)),
            "solved_ids": sorted(solved),
            "mean_test_acc_on_solved": (sum(accs) / len(accs)) if accs else None,
        }
    return {
        "raw": arm("raw_solved", "raw_test_acc"),
        "objectmap_guarded": arm("objectmap_solved", "objectmap_test_acc"),
        "objectmap_unguarded_n": sum(1 for v in per_task.values() if v["unguarded_solved"]),
        "union": arm("union_solved", "union_test_acc"),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--budget", type=int, default=50_000)
    ap.add_argument("--max-depth", type=int, default=7)
    ap.add_argument("--arc2-probe", type=int, default=30)
    ap.add_argument("--out", default=str(HERE / "stage3c_result.json"))
    args = ap.parse_args()

    t0 = time.time()
    dev = s1_tasks.load_arc_dev()
    dev_res = run_tasks(dev, args.budget, args.max_depth, "dev")
    dev_sum = summarize(dev_res)

    n_union, n_raw = dev_sum["union"]["n_solved"], dev_sum["raw"]["n_solved"]
    if n_union >= 5 and n_union >= 4 * max(1, n_raw):
        decision = "ACCEPT H7-v3"
    elif n_union <= 2:
        decision = "KILL"
    else:
        decision = "INCONCLUSIVE"

    arc2_sum = None
    if args.arc2_probe and ARC2_EVAL.exists():
        a2 = load_arc_dir(ARC2_EVAL, args.arc2_probe)
        arc2_sum = summarize(run_tasks(a2, args.budget, args.max_depth, "arc2"))

    result = {
        "config": vars(args),
        "dev": dev_sum,
        "decision_h7v3": decision,
        "arc2": arc2_sum,
        "per_task_dev": dev_res,
        "seconds": round(time.time() - t0, 1),
    }
    Path(args.out).write_text(json.dumps(result, indent=2))
    print(json.dumps({k: result[k] for k in ("dev", "decision_h7v3", "arc2", "seconds")}, indent=2))


if __name__ == "__main__":
    main()
