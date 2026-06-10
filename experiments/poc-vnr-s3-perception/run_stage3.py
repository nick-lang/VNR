"""VNR Stage 3 experiment: object-centric perception + richer DSL (H7).

Arms (identical tasks, matched solver/budget):
  raw    = Stage-1 geometric DSL (13 primitives)
  object = geometric + object ops (connected components) + per-task recolor tokens

Primary: solve rate on the committed 50-task ARC-AGI-1 dev split.
Secondary: 30-task ARC-AGI-2 probe (the gap), and an H5-on-real-ARC probe
(library built from ARC-1 training-split solves, transferred to the dev split).
Decision rule pre-registered in ledger/hypotheses.md (H7).
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
S1 = HERE.parent / "poc-vnr-s1-library"
sys.path.insert(0, str(S1))

import dsl  # noqa: E402
import library  # noqa: E402
import search  # noqa: E402
import tasks as s1_tasks  # noqa: E402
from objects import OBJECT_OPS  # noqa: E402

REPO = HERE.parents[1]
ARC1_TRAIN = REPO / "data" / "arc-agi-1" / "data" / "training"
ARC2_EVAL = REPO / "data" / "arc-agi-2" / "data" / "evaluation"


def load_arc_dir(d: Path, limit: int) -> list[s1_tasks.Task]:
    out = []
    for f in sorted(d.glob("*.json"))[:limit]:
        obj = json.loads(f.read_text())
        train = [(np.array(p["input"]), np.array(p["output"])) for p in obj["train"]]
        test = [(np.array(p["input"]), np.array(p["output"])) for p in obj["test"] if "output" in p]
        out.append(s1_tasks.Task(name=f.stem, train=train, test=test))
    return out


def make_recolor(a: int, b: int):
    def fn(g):
        if not (g == a).any():
            return None  # inapplicable: prune identity branches
        out = g.copy()
        out[g == a] = b
        return out
    return fn


def build_object_ops(task: s1_tasks.Task, macros: dict | None = None):
    """Per-task token set: geometric + object ops + palette recolor (+ macros)."""
    ops = dict(dsl.PRIMITIVES)
    ops.update(OBJECT_OPS)
    palette = sorted({int(v) for inp, out in task.train for v in np.concatenate([inp.ravel(), out.ravel()])})
    for a in palette:
        for b in palette:
            if a != b:
                ops[f"recolor_{a}_{b}"] = make_recolor(a, b)
    token_names = list(ops)
    if macros:
        lib_ops, _ = library.make_ops(macros)
        # macro bodies may reference recolor tokens; expand against this task's ops
        for name in macros:
            prims = library.expand(name, macros)
            if all(p in ops for p in prims):
                def _mk(seq):
                    def fn(g):
                        return dsl.apply_program(seq, g, ops)
                    return fn
                ops[name] = _mk(prims)
                token_names.append(name)
        del lib_ops
    return ops, token_names


def run_arm(task_list, arm: str, budget: int, max_depth: int, macros: dict | None = None, label: str = ""):
    results = {}
    for i, t in enumerate(task_list):
        if arm == "raw":
            ops, names = dict(dsl.PRIMITIVES), list(dsl.PRIMITIVES)
        else:
            ops, names = build_object_ops(t, macros)
        r = search.search_task(t.train, ops, names, budget=budget, max_depth=max_depth)
        test_acc = search.test_accuracy(r.program, t.test, ops) if r.solved else None
        results[t.name] = {
            "solved": r.solved,
            "nodes": r.nodes,
            "program": r.program,
            "test_acc": test_acc,
        }
        print(f"[{label or arm}] {i + 1}/{len(task_list)} {t.name} "
              f"solved={r.solved} nodes={r.nodes}", flush=True)
    return results


def summarize(res: dict) -> dict:
    solved = {k: v for k, v in res.items() if v["solved"]}
    test_accs = [v["test_acc"] for v in solved.values() if v["test_acc"] is not None]
    return {
        "n": len(res),
        "n_solved": len(solved),
        "solve_rate": len(solved) / max(1, len(res)),
        "solved_ids": sorted(solved),
        "mean_test_acc_on_solved": (sum(test_accs) / len(test_accs)) if test_accs else None,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--budget", type=int, default=50_000)
    ap.add_argument("--max-depth", type=int, default=7)
    ap.add_argument("--arc2-probe", type=int, default=30)
    ap.add_argument("--h5-train-tasks", type=int, default=80)
    ap.add_argument("--lib-cap", type=int, default=8)
    ap.add_argument("--out", default=str(HERE / "stage3_result.json"))
    args = ap.parse_args()

    t0 = time.time()
    dev = s1_tasks.load_arc_dev()

    # Primary: raw vs object arms on the dev split.
    raw_res = run_arm(dev, "raw", args.budget, args.max_depth, label="dev/raw")
    obj_res = run_arm(dev, "object", args.budget, args.max_depth, label="dev/object")
    raw_sum, obj_sum = summarize(raw_res), summarize(obj_res)

    # H7 decision (pre-registered).
    n_obj, n_raw = obj_sum["n_solved"], raw_sum["n_solved"]
    if n_obj >= 5 and n_obj >= 4 * max(1, n_raw):
        decision = "ACCEPT H7 (coverage form)"
    elif n_obj <= 2:
        decision = "KILL/PIVOT (object ops + recolor do not move coverage)"
    else:
        decision = "INCONCLUSIVE"

    # Secondary probe: ARC-AGI-2 gap.
    arc2 = None
    if args.arc2_probe and ARC2_EVAL.exists():
        a2 = load_arc_dir(ARC2_EVAL, args.arc2_probe)
        a2_res = run_arm(a2, "object", args.budget, args.max_depth, label="arc2/object")
        arc2 = summarize(a2_res)

    # Secondary probe: H5 on real ARC (library from training-split solves).
    h5_probe = None
    if args.h5_train_tasks:
        tr = load_arc_dir(ARC1_TRAIN, args.h5_train_tasks)
        tr_res = run_arm(tr, "object", args.budget, args.max_depth, label="train/object")
        solved_programs = [v["program"] for v in tr_res.values() if v["solved"]]
        macros = library.build_library(solved_programs, cap=args.lib_cap)
        lib_res = run_arm(dev, "object", args.budget, args.max_depth, macros=macros, label="dev/object+lib")
        lib_sum = summarize(lib_res)
        both = sorted(set(obj_sum["solved_ids"]) & set(lib_sum["solved_ids"]))
        med_obj = statistics.median([obj_res[k]["nodes"] for k in both]) if both else None
        med_lib = statistics.median([lib_res[k]["nodes"] for k in both]) if both else None
        h5_probe = {
            "train_solved": sum(1 for v in tr_res.values() if v["solved"]),
            "train_n": len(tr),
            "library": {m: library.expand(m, macros) for m in macros},
            "dev_with_library": lib_sum,
            "shared_solved": len(both),
            "median_nodes_object": med_obj,
            "median_nodes_object_plus_lib": med_lib,
        }

    result = {
        "config": vars(args),
        "dev_raw": raw_sum,
        "dev_object": obj_sum,
        "decision_h7": decision,
        "arc2_object": arc2,
        "h5_real_arc_probe": h5_probe,
        "seconds": round(time.time() - t0, 1),
    }
    Path(args.out).write_text(json.dumps(result, indent=2))
    print(json.dumps({k: v for k, v in result.items() if k != "config"}, indent=2))


if __name__ == "__main__":
    main()
