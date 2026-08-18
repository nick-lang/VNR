"""E1-A — retrospective selector bake-off on BANKED data ($0, CPU-only).

The S6 banking discarded pick histories and grids (only scalars survive), so
this phase evaluates every LOSS-SCORER selector the banked data supports:

  tail_loss   mean loss over final 50 steps (H15's refuted selector; b jobs only)
  final_loss  last-step loss (all jobs)

Candidate groups (a selector must pick ONE run per group, label-free):
  B-pair  b_T_s1 vs b_T_s2         (matched 1000-step budget; 39 tasks)
  trio    a_T vs b_T_s1 vs b_T_s2  (unequal budgets, reported but caveated)
  S-pair  cold5090_T (seed 0) vs seedchk_T (seed 1)  (9 solved tasks;
          final_loss only -- cold5090 artifacts lack tail_loss)

A group is INFORMATIVE when >=1 candidate solved_top2 and not all did.
Output: per-group table + per-scorer selection accuracy + what banked data
CANNOT evaluate (agreement voting, pick stability, vote margin -> E1-B).
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
S6 = HERE / "s6_artifacts"
S5 = HERE.parents[0] / "poc-vnr-s5-memory" / "s5_artifacts"

def load(pattern, base):
    return {f.stem: json.loads(f.read_text()) for f in base.glob(pattern)}

s6 = load("job6_*.json", S6)
cold = {r["task"]: r for r in load("job5f_cold5090_*.json", S5).values()}

a  = {r["task"]: r for r in s6.values() if r["kind"] == "a"}
b1 = {r["task"]: r for r in s6.values() if r["kind"] == "b" and r["seed"] == 1}
b2 = {r["task"]: r for r in s6.values() if r["kind"] == "b" and r["seed"] == 2}
sc = {r["task"]: r for r in s6.values() if r["kind"] == "seedchk"}

def pick(group, key):
    """argmin of key over candidates; None if any candidate lacks the key."""
    if any(r.get(key) is None for r in group):
        return None
    return min(group, key=lambda r: r[key])

def informative(group):
    s = [bool(r["solved_top2"]) for r in group]
    return any(s) and not all(s)

def evaluate(groups, scorers, label):
    print(f"\n=== {label} ({len(groups)} groups) ===")
    info = [g for g in groups if informative(g)]
    none_solved = sum(1 for g in groups if not any(r["solved_top2"] for r in g))
    all_solved = sum(1 for g in groups if all(r["solved_top2"] for r in g))
    print(f"informative: {len(info)}  |  none-solved: {none_solved}  |  all-solved: {all_solved}")
    out = {}
    for key in scorers:
        hits, cases = 0, []
        for g in info:
            p = pick(g, key)
            if p is None:
                continue
            solver = next(r for r in g if r["solved_top2"])
            ok = bool(p["solved_top2"])
            hits += ok
            cases.append({
                "task": g[0]["task"], "picked": p["name"], "picked_solved": ok,
                "solver": solver["name"],
                key: {r["name"]: r.get(key) for r in g},
            })
        n = len(cases)
        acc = f"{hits}/{n}" if n else "n/a"
        print(f"  scorer={key:<11} accuracy on informative groups: {acc}")
        for c in cases:
            vals = ", ".join(f"{k.split('_', 1)[-1]}={v}" for k, v in c[key].items())
            mark = "OK " if c["picked_solved"] else "MISS"
            print(f"    [{mark}] {c['task']}: picked {c['picked']} "
                  f"(solver {c['solver']})  {vals}")
        out[key] = {"accuracy": acc, "cases": cases}
    return out

results = {}

# 1. B-pairs (H15's own selector setting, matched budget).
bpairs = [[b1[t], b2[t]] for t in b1 if t in b2]
results["b_pair"] = evaluate(bpairs, ["tail_loss", "final_loss"], "B-pair (b_s1 vs b_s2, matched 1000 steps)")

# 2. Trios (unequal budgets -- loss at step 2000 vs 1000 is not strictly
#    comparable; reported as descriptive only).
trios = [[a[t], b1[t], b2[t]] for t in a if t in b1 and t in b2]
results["trio"] = evaluate(trios, ["tail_loss", "final_loss"], "Trio (a vs b_s1 vs b_s2; UNEQUAL budgets, descriptive)")

# 3. S-pairs on the 9 solved tasks (seed 0 cold5090 vs seed 1 seedchk,
#    matched 1000 steps; final_loss only).
spairs = [[cold[t], sc[t]] for t in sc if t in cold]
results["s_pair"] = evaluate(spairs, ["final_loss"], "S-pair (cold5090 seed0 vs seedchk seed1, matched 1000 steps)")

# 4. Loss-vs-solving association across ALL matched-budget runs (descriptive):
#    within each matched pair, does the solving run have the lower loss?
print("\n=== Within-pair loss direction (matched-budget pairs, informative only) ===")
for name, pairs, key in [("b_pair/tail", bpairs, "tail_loss"),
                         ("b_pair/final", bpairs, "final_loss"),
                         ("s_pair/final", spairs, "final_loss")]:
    lower_solves, n = 0, 0
    for g in pairs:
        if not informative(g) or any(r.get(key) is None for r in g):
            continue
        solver = next(r for r in g if r["solved_top2"])
        n += 1
        lower_solves += (solver == pick(g, key))
    if n:
        print(f"  {name}: solver had LOWER {key} in {lower_solves}/{n} pairs")

# 5. Throughput accounting for E1-B sizing.
import statistics
for kind, runs in [("a(2000)", a.values()), ("b(1000)", list(b1.values()) + list(b2.values())),
                   ("seedchk(1000)", sc.values())]:
    spd = [r["seconds"] / r["steps"] for r in runs]
    print(f"\n{kind}: n={len(spd)} median {statistics.median(spd):.2f} s/step "
          f"(min {min(spd):.2f}, max {max(spd):.2f}) [4-way-parallel wall seconds]")

(HERE / "e1a_result.json").write_text(json.dumps(results, indent=2))
print("\nbanked-data limits: agreement voting, pick stability, and vote margin "
      "are NOT evaluable (picks/grids were not banked) -> E1-B capture runs.")
print("saved e1a_result.json")
