"""H16 evaluation — reverse-mapped agreement voting (rule pre-registered in
ledger/hypotheses.md). Re-runnable on partial artifacts; the decision line
only prints when all 200 jobs are banked.

Voting rule (fixed in advance): per task, candidate pool = the 4 frames'
reverse-mapped top-1 grids, ranked by (vote count, then summed within-run
vote margin); answer 1 = first; answer 2 = second distinct top-1 if any,
else the modal reverse-mapped top-2 (same tie-break). pass@2 = ground truth
in {answer 1, answer 2}.
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ARTIFACTS = HERE / "h16_artifacts"
DEV_SPLIT = json.loads(
    (HERE.parents[1] / "data" / "dev_split_arc1.json").read_text())["task_ids"]

cov = json.loads((HERE / "coverage_analysis.json").read_text())
NEVER = {t["task"] for t in cov["per_task"]
         if t["runs"] >= 3 and t["solved"] == 0}
EVER = set(DEV_SPLIT) - NEVER


def load():
    by_task = defaultdict(list)
    for f in sorted(ARTIFACTS.glob("job_h16_*.json")):
        r = json.loads(f.read_text())
        by_task[r["task"]].append(r)
    return by_task


def rank_hashes(runs, key):
    """hash -> (votes, summed margin) over non-None hashes of `key`."""
    tally = defaultdict(lambda: [0, 0.0])
    for r in runs:
        h = r[key]
        if h is None:
            continue
        tally[h][0] += 1
        tally[h][1] += r["vote_margin"] or 0.0
    return sorted(tally.items(), key=lambda kv: (-kv[1][0], -kv[1][1]))


def vote(runs):
    """Return (answer_hashes, detail) per the pre-registered rule."""
    top1 = rank_hashes(runs, "top1_hash_origframe")
    answers = [h for h, _ in top1[:2]]
    used_fallback = False
    if len(answers) < 2:
        top2 = rank_hashes(runs, "top2_hash_origframe")
        for h, _ in top2:
            if h not in answers:
                answers.append(h)
                used_fallback = True
                break
    detail = {"top1_votes": {str(h): v[0] for h, v in top1},
              "used_top2_fallback": used_fallback}
    return answers[:2], detail


def main():
    by_task = load()
    n_done = sum(len(v) for v in by_task.values())
    complete = [t for t in DEV_SPLIT if len(by_task.get(t, [])) == 4]
    print(f"artifacts: {n_done}/200 jobs; complete tasks: {len(complete)}/50\n")

    voted_solved, frame_solved = [], defaultdict(list)
    union_oracle, wrong_consensus = [], []
    rows = []
    for t in complete:
        runs = sorted(by_task[t], key=lambda r: r["aug"])
        gt = runs[0]["gt_hash_origframe"]
        answers, detail = vote(runs)
        ok = gt in answers
        if ok:
            voted_solved.append(t)
        for r in runs:
            if r["solved_origframe_top1"]:
                frame_solved[r["aug_name"]].append(t)
        if any(r["solved_origframe_top1"] or r["top2_hash_origframe"] == gt
               for r in runs):
            union_oracle.append(t)
        if t in NEVER:
            wrongs = [h for h, v in detail["top1_votes"].items()
                      if int(h) != gt and v >= 2]
            if wrongs:
                wrong_consensus.append({"task": t,
                                        "votes": detail["top1_votes"]})
        rows.append({"task": t, "voted_pass2": ok,
                     "never_arm": t in NEVER, **detail})

    print(f"## Voted pass@2: {len(voted_solved)}/{len(complete)}"
          f"{' (PARTIAL)' if len(complete) < 50 else ''}")
    print(f"   solved: {sorted(voted_solved)}")
    print(f"## Union-of-frames oracle (any frame top-2 correct): "
          f"{len(union_oracle)}/{len(complete)}")
    print(f"## Per-frame top-1 solves (orig frame): "
          f"{ {k: len(v) for k, v in sorted(frame_solved.items())} }")
    nev_done = [t for t in complete if t in NEVER]
    print(f"## Wrong-consensus on never-solved arm: "
          f"{len(wrong_consensus)}/{len(nev_done)} "
          f"(E1-B same-input baseline: 2/6)")
    for w in wrong_consensus:
        print(f"   {w['task']}: {w['votes']}")

    out = {"progress": f"{n_done}/200", "complete_tasks": len(complete),
           "voted_pass2": sorted(voted_solved),
           "union_oracle": sorted(union_oracle),
           "per_frame_solves": {k: sorted(v) for k, v in frame_solved.items()},
           "wrong_consensus_never_arm":
               f"{len(wrong_consensus)}/{len(nev_done)}",
           "wrong_consensus_cases": wrong_consensus, "rows": rows}

    if len(complete) == 50:
        n = len(voted_solved)
        decision = ("ACCEPT" if n >= 13 else
                    "KILL" if n <= 11 else "INCONCLUSIVE")
        out["decision_h16"] = decision
        print(f"\n## DECISION H16: {decision} (voted pass@2 = {n}/50; "
              f"accept >= 13, kill <= 11)")

    (HERE / "h16_eval_result.json").write_text(json.dumps(out, indent=2))
    print("\nsaved h16_eval_result.json")


if __name__ == "__main__":
    main()
