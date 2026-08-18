"""Cross-stage coverage analysis for the write-up ($0, CPU-only).

Collects every COLD-protocol run (unmodified CompressARC, random init, fresh
latents) banked across stages into one per-task table over the committed
50-task dev split, then quantifies the write-up's claim 2: coverage is a
stochastic draw, so solve sets must be reported run-marginalized.

Included runs (protocol = hardware @ steps, seed):
  H8    stage4_result.json           L40S @2000 seed0   50 tasks
  H9    job_cold_*.json              A40  @2000 seed0   11 tasks
  H14   job5f_cold5090_*.json        5090 @1000 seed0   11 tasks
  H15   job6_a_*.json                5090 @2000 seed0   39 tasks
  H15   job6_b_*_s{1,2}.json         5090 @1000 seed1/2 39 tasks x2
  H15   job6_seedchk_*.json          5090 @1000 seed1    9 tasks
  E1-B  job_e1b_*.json               5090 @2000/@1000   (auto-included as
                                     they land; fresh draws, some duplicate
                                     S6 configs -> same-config churn readout)

Excluded: all warm-start arms (loo/ret/jret/probe/sanity) -- different
mechanism, not coverage draws.

Outputs: coverage_analysis.json + printed markdown tables.
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
S4 = REPO / "experiments" / "poc-vnr-s4-neural"
S5A = REPO / "experiments" / "poc-vnr-s5-memory" / "s5_artifacts"
S6A = HERE / "s6_artifacts"
E1B = HERE / "e1b_artifacts"

DEV_SPLIT = json.loads(
    (REPO / "data" / "dev_split_arc1.json").read_text())["task_ids"]


def collect_runs() -> list[dict]:
    runs = []

    s4 = json.loads((S4 / "stage4_result.json").read_text())
    solved4 = set(s4["summary"]["solved_ids_pass2"])
    for tid in DEV_SPLIT:
        runs.append({"task": tid, "stage": "H8", "hw": "L40S", "steps": 2000,
                     "seed": 0, "solved": tid in solved4})

    for f in sorted(S5A.glob("job_cold_*.json")):
        r = json.loads(f.read_text())
        runs.append({"task": r["task"], "stage": "H9", "hw": "A40",
                     "steps": r["steps"], "seed": 0,
                     "solved": bool(r["solved_top2"])})

    for f in sorted(S5A.glob("job5f_cold5090_*.json")):
        r = json.loads(f.read_text())
        runs.append({"task": r["task"], "stage": "H14", "hw": "5090",
                     "steps": r["steps"], "seed": 0,
                     "solved": bool(r["solved_top2"])})

    for f in sorted(S6A.glob("job6_*.json")):
        r = json.loads(f.read_text())
        runs.append({"task": r["task"], "stage": "H15", "hw": "5090",
                     "steps": r["steps"], "seed": r["seed"],
                     "solved": bool(r["solved_top2"])})

    if E1B.exists():
        for f in sorted(E1B.glob("job_e1b_*.json")):
            r = json.loads(f.read_text())
            runs.append({"task": r["task"], "stage": "E1B", "hw": "5090",
                         "steps": r["steps"], "seed": r["seed"],
                         "solved": bool(r["solved_top2"]),
                         "name": r["name"]})
    return runs


STAGE_ORDER = ["H8", "H9", "H14", "H15", "E1B"]


def union_timeline(runs):
    solved = set()
    timeline = []
    for st in STAGE_ORDER:
        new = {r["task"] for r in runs
               if r["stage"] == st and r["solved"]} - solved
        solved |= new
        n_runs = sum(1 for r in runs if r["stage"] == st)
        if n_runs:
            timeline.append({"stage": st, "runs": n_runs,
                             "new_tasks": sorted(new),
                             "union": len(solved)})
    return timeline, solved


def matched_flips(runs):
    """Solve-outcome flips between matched run groups (the churn readouts)."""
    def group(stage, hw, steps, seed=None, name_prefix=None):
        out = {}
        for r in runs:
            if r["stage"] != stage or r["hw"] != hw or r["steps"] != steps:
                continue
            if seed is not None and r["seed"] != seed:
                continue
            if name_prefix and not r.get("name", "").startswith(name_prefix):
                continue
            out[r["task"]] = r["solved"]
        return out

    pairs = [
        ("cross-hardware L40S vs A40 @2000 s0",
         group("H8", "L40S", 2000), group("H9", "A40", 2000)),
        ("cross-hardware L40S vs 5090 @2000 s0",
         group("H8", "L40S", 2000), group("H15", "5090", 2000, seed=0)),
        ("cross-seed 5090 @1000 s0 vs s1 (solved tasks)",
         group("H14", "5090", 1000), group("H15", "5090", 1000, seed=1)),
        ("cross-seed 5090 @1000 s1 vs s2 (unsolved tasks)",
         group("H15", "5090", 1000, seed=1), group("H15", "5090", 1000, seed=2)),
        ("SAME-config 5090 @2000 s0: S6 vs E1-B rerun",
         group("H15", "5090", 2000, seed=0), group("E1B", "5090", 2000, seed=0)),
        ("SAME-config 5090 @1000 s1: S6 vs E1-B rerun",
         group("H15", "5090", 1000, seed=1),
         group("E1B", "5090", 1000, seed=1, name_prefix="b_")),
    ]
    out = []
    for label, g1, g2 in pairs:
        common = sorted(set(g1) & set(g2))
        if not common:
            continue
        flips = [t for t in common if g1[t] != g2[t]]
        either = [t for t in common if g1[t] or g2[t]]
        out.append({"label": label, "n_common": len(common),
                    "n_solved_either": len(either), "flips": flips,
                    "flip_rate_among_solved": (
                        round(len(flips) / len(either), 3) if either else None)})
    return out


def per_task_table(runs):
    by_task = defaultdict(list)
    for r in runs:
        by_task[r["task"]].append(r)
    table = []
    for tid in DEV_SPLIT:
        rs = by_task[tid]
        n, k = len(rs), sum(r["solved"] for r in rs)
        table.append({"task": tid, "runs": n, "solved": k,
                      "p_hat": round(k / n, 3) if n else None})
    return table


def main():
    runs = collect_runs()
    timeline, union = union_timeline(runs)
    flips = matched_flips(runs)
    table = per_task_table(runs)

    frac = [t for t in table if t["runs"] >= 3 and 0 < t["solved"] < t["runs"]]
    always = [t for t in table if t["runs"] >= 3 and t["solved"] == t["runs"]]
    never = [t for t in table if t["runs"] >= 3 and t["solved"] == 0]

    print(f"total cold runs: {len(runs)} across {len({r['task'] for r in runs})} tasks\n")
    print("## Union timeline (chronological)")
    for t in timeline:
        newstr = ",".join(t["new_tasks"]) if t["new_tasks"] else "-"
        print(f"  {t['stage']:<4} runs={t['runs']:<4} union={t['union']:>2}/50  new: {newstr}")
    print("\n## Matched-group solve flips")
    for f in flips:
        print(f"  {f['label']}: common={f['n_common']}, "
              f"flips={len(f['flips'])}/{f['n_solved_either']} solved-either "
              f"(rate {f['flip_rate_among_solved']}) {f['flips']}")
    print(f"\n## Per-task solve fraction (tasks with >=3 cold runs)")
    print(f"  always-solved: {len(always)}  fractional: {len(frac)}  never: {len(never)}")
    for t in sorted(frac, key=lambda x: -x["p_hat"]):
        print(f"    {t['task']}: {t['solved']}/{t['runs']} (p^={t['p_hat']})")

    out = {"n_runs": len(runs), "timeline": timeline,
           "union_final": sorted(union), "matched_flips": flips,
           "per_task": table,
           "fractional_tasks": sorted(frac, key=lambda x: -x["p_hat"])}
    (HERE / "coverage_analysis.json").write_text(json.dumps(out, indent=2))
    print("\nsaved coverage_analysis.json")


if __name__ == "__main__":
    main()
