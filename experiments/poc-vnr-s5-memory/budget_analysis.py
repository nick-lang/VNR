"""Mine banked Stage 5/5b artifacts: what step budget would have retained every solve?"""
import glob
import json

rows = [json.load(open(f)) for f in sorted(glob.glob("experiments/poc-vnr-s5-memory/s5_artifacts/job_cold_*.json"))]
solved = [r for r in rows if r["solved_top2"]]
steps = sorted(r["steps_to_stable_solve"] for r in solved)

for r in rows:
    status = f"stable@{r['steps_to_stable_solve']}" if r["solved_top2"] else "FAILED"
    print(f"{r['task']}  {status:>12}  {r['seconds']/60:5.0f} min")

print(f"\nsolved {len(solved)}/{len(rows)}  median stable step {steps[len(steps)//2]}  max {steps[-1]}")
for budget in (600, 800, 1000, 2000):
    kept = sum(s <= budget for s in steps)
    print(f"budget {budget:>4}: retains {kept}/{len(solved)} solves, cost {budget/2000:.0%} of current")
