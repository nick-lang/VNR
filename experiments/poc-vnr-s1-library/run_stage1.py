"""VNR Stage 1 experiment: does a growing library beat per-task search? (H5)

Arm A (no library): search every held-out task from primitives only.
Arm B (growing library): solve a train set from primitives, build an MDL library
of macro-abstractions, then search the SAME held-out tasks with primitives + library.

Primary metric: median states-evaluated-to-solution on held-out tasks both arms
solve. Secondary: held-out solve rate within budget. Decision rule is
pre-registered in ledger/hypotheses.md (H5).
"""
from __future__ import annotations

import argparse
import json
import statistics
import time
from pathlib import Path

import dsl
import library
import search
import tasks


def solve_set(task_list, ops, token_names, budget, max_depth):
    results = []
    for t in task_list:
        r = search.search_task(t.train, ops, token_names, budget=budget, max_depth=max_depth)
        results.append((t, r))
    return results


def summarize(results, macros=None):
    solved = [(t, r) for t, r in results if r.solved]
    rate = len(solved) / len(results) if results else 0.0
    nodes = {t.name: r.nodes for t, r in solved}
    return {"solve_rate": rate, "n_solved": len(solved), "n": len(results), "nodes": nodes}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-train", type=int, default=60)
    ap.add_argument("--n-heldout", type=int, default=60)
    ap.add_argument("--budget", type=int, default=50_000)
    ap.add_argument("--max-depth", type=int, default=7)
    ap.add_argument("--lib-cap", type=int, default=8)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--arc-coverage", type=int, default=50, help="how many ARC dev tasks to probe (0=skip)")
    ap.add_argument("--out", default="experiments/poc-vnr-s1-library/stage1_result.json")
    args = ap.parse_args()

    t0 = time.time()
    all_tasks = tasks.gen_synthetic(args.n_train + args.n_heldout, seed=args.seed)
    train_tasks = all_tasks[: args.n_train]
    heldout = all_tasks[args.n_train :]

    prim_ops = dict(dsl.PRIMITIVES)
    prim_names = list(dsl.PRIMITIVES)

    # Arm A: held-out from primitives only.
    arm_a = solve_set(heldout, prim_ops, prim_names, args.budget, args.max_depth)
    sum_a = summarize(arm_a)

    # Arm B: learn library from solved TRAIN programs, then solve held-out with it.
    train_res = solve_set(train_tasks, prim_ops, prim_names, args.budget, args.max_depth)
    solved_train_programs = [r.program for _, r in train_res if r.solved]
    macros = library.build_library(solved_train_programs, cap=args.lib_cap)
    lib_ops, lib_names = library.make_ops(macros)
    arm_b = solve_set(heldout, lib_ops, lib_names, args.budget, args.max_depth)
    sum_b = summarize(arm_b)

    # Compare on held-out tasks BOTH arms solved.
    both = sorted(set(sum_a["nodes"]) & set(sum_b["nodes"]))
    nodes_a = [sum_a["nodes"][n] for n in both]
    nodes_b = [sum_b["nodes"][n] for n in both]
    med_a = statistics.median(nodes_a) if nodes_a else float("nan")
    med_b = statistics.median(nodes_b) if nodes_b else float("nan")
    ratio = (med_b / med_a) if (nodes_a and med_a) else float("nan")

    # Decision vs pre-registered rule.
    if nodes_a and not (sum_b["solve_rate"] < sum_a["solve_rate"]):
        if ratio <= 0.5:
            decision = "ACCEPT H5 (>=2x search efficiency, solve rate not lower)"
        elif ratio >= 0.9:
            decision = "KILL/PIVOT (<=10% improvement)"
        else:
            decision = "INCONCLUSIVE (10-50% improvement)"
    elif sum_b["solve_rate"] < sum_a["solve_rate"]:
        decision = "KILL/PIVOT (library lowered solve rate)"
    else:
        decision = "INDETERMINATE (no shared-solved tasks)"

    macros_expanded = {name: library.expand(name, macros) for name in macros}

    # ARC dev-split coverage probe (primitives only) -- realism check.
    arc_cov = None
    if args.arc_coverage:
        arc_tasks = tasks.load_arc_dev(limit=args.arc_coverage)
        arc_solved = 0
        for t in arc_tasks:
            r = search.search_task(t.train, prim_ops, prim_names, budget=args.budget, max_depth=args.max_depth)
            if r.solved:
                arc_solved += 1
        arc_cov = {"n": len(arc_tasks), "solved": arc_solved, "rate": arc_solved / max(1, len(arc_tasks))}

    result = {
        "config": vars(args),
        "train_solve_rate": sum(1 for _, r in train_res if r.solved) / max(1, len(train_res)),
        "library_size": len(macros),
        "library": macros_expanded,
        "arm_a_no_library": {"solve_rate": sum_a["solve_rate"], "n_solved": sum_a["n_solved"]},
        "arm_b_with_library": {"solve_rate": sum_b["solve_rate"], "n_solved": sum_b["n_solved"]},
        "shared_solved": len(both),
        "median_nodes_no_library": med_a,
        "median_nodes_with_library": med_b,
        "efficiency_ratio_b_over_a": ratio,
        "speedup_x": (med_a / med_b) if (med_b and med_b == med_b) else float("nan"),
        "decision": decision,
        "seconds": round(time.time() - t0, 1),
        "arc_coverage_primitives": arc_cov,
    }
    print(json.dumps(result, indent=2))
    Path(args.out).write_text(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
