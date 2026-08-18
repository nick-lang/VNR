"""E1-B selector evaluation (pre-registered in e1b_runner.py's docstring).

Runs over whatever e1b_artifacts contains (graceful on partial queues, so it
can be re-run as jobs land). Per task, the candidate set = all E1-B runs of
that task. Two kinds of readout:

RUN-PICK selectors (choose ONE run; scored on informative groups, i.e. >=1
candidate solved and not all did -- solve outcomes are E1-B's own, since
runs are fresh draws):
  final_loss      argmin last-step loss (E1-A's surviving scorer, baseline)
  tail_loss       argmin mean loss over final 50 steps (H15's refuted scorer)
  vote_margin     argmax within-run log-score gap top1-vs-top2
  pick_stability  argmax trailing fraction of steps with unchanged top-1 pick

ANSWER-LEVEL selector:
  agreement vote  candidates' top-1 grids vote by hash; answer = the two
                  highest-vote hashes (tie-break: lower mean final_loss of
                  supporting runs); "solved" = solution_hash in the answer.
                  On the never-solved arm, report the WRONG-MODAL rate:
                  fraction of tasks where >=2 runs agree on the same
                  (necessarily wrong) top-1 grid -- agreement's
                  false-positive risk.
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
E1B = HERE / "e1b_artifacts"

SOLVE_TASKS = ["73182012", "981571dc", "be03b35f", "e66aafb8"]
NEVER_ARM_KINDS = {"a", "b"}  # never-arm tasks are those outside SOLVE/CHURN


def trailing_stability(rle: list[list], total_steps: int) -> float:
    """Fraction of trailing steps whose top-1 pick equals the final top-1."""
    if not rle or not total_steps:
        return 0.0
    final_top1 = rle[-1][1]
    steps = 0
    for count, top1, _top2 in reversed(rle):
        if top1 != final_top1:
            break
        steps += count
    return steps / total_steps


def load():
    by_task = defaultdict(list)
    for f in sorted(E1B.glob("job_e1b_*.json")):
        r = json.loads(f.read_text())
        r["stability"] = trailing_stability(
            r.get("picks_history_rle") or [], r["steps"])
        by_task[r["task"]].append(r)
    return by_task


def pick_run(group, key, largest=False):
    vals = [(r.get(key), r) for r in group]
    if any(v is None for v, _ in vals):
        return None
    return max(vals)[1] if largest else min(vals)[1]


def agreement_answer(group):
    """Return (answer_hashes, vote_detail). Top-2 hashes by top-1 votes."""
    votes = Counter(r["top1_hash"] for r in group if r["top1_hash"] is not None)
    if not votes:
        return [], {}
    def mean_loss(h):
        ls = [r["final_loss"] for r in group if r["top1_hash"] == h]
        return sum(ls) / len(ls)
    ranked = sorted(votes, key=lambda h: (-votes[h], mean_loss(h)))
    return ranked[:2], {str(h): votes[h] for h in ranked}


def main():
    by_task = load()
    n_expected = 34
    n_done = sum(len(v) for v in by_task.values())
    print(f"E1-B artifacts: {n_done}/{n_expected} jobs, {len(by_task)} tasks\n")

    selectors = [("final_loss", "final_loss", False),
                 ("tail_loss", "tail_loss", False),
                 ("vote_margin", "vote_margin", True),
                 ("pick_stability", "stability", True)]

    informative, results = [], {name: [] for name, _, _ in selectors}
    agreement_cases, never_cases = [], []

    for task, group in sorted(by_task.items()):
        solved = [r for r in group if r["solved_top2"]]
        kinds = {r["kind"] for r in group}
        # --- run-pick selectors on informative groups ---
        if solved and len(solved) < len(group):
            informative.append(task)
            for name, key, largest in selectors:
                p = pick_run(group, key, largest)
                if p is not None:
                    results[name].append(
                        {"task": task, "picked": p["name"],
                         "picked_solved": bool(p["solved_top2"]),
                         "solvers": [r["name"] for r in solved]})
        # --- agreement vote on every task with >=2 candidates ---
        if len(group) >= 2:
            answers, votes = agreement_answer(group)
            sol_hash = group[0]["solution_hash"]
            agree_solved = sol_hash in answers
            modal_votes = max(votes.values()) if votes else 0
            case = {"task": task, "n_runs": len(group),
                    "n_solved_runs": len(solved), "votes": votes,
                    "agreement_solved_top2": agree_solved}
            agreement_cases.append(case)
            if not solved and kinds & NEVER_ARM_KINDS \
                    and task not in SOLVE_TASKS:
                never_cases.append(
                    {"task": task, "wrong_modal_agreement": modal_votes >= 2,
                     "modal_votes": modal_votes})

    print(f"## Run-pick selectors (informative groups: {len(informative)}: "
          f"{informative})")
    for name, _, _ in selectors:
        cases = results[name]
        hits = sum(c["picked_solved"] for c in cases)
        print(f"  {name:<15} {hits}/{len(cases)}")
        for c in cases:
            mark = "OK " if c["picked_solved"] else "MISS"
            print(f"    [{mark}] {c['task']}: picked {c['picked']} "
                  f"(solvers: {','.join(c['solvers'])})")

    ag_solve_relevant = [c for c in agreement_cases
                         if c["task"] in SOLVE_TASKS]
    ag_hits = sum(c["agreement_solved_top2"] for c in ag_solve_relevant)
    print(f"\n## Agreement vote")
    print(f"  solve-relevant tasks: {ag_hits}/{len(ag_solve_relevant)} "
          f"solved by top-2 modal answer")
    for c in ag_solve_relevant:
        mark = "OK " if c["agreement_solved_top2"] else "MISS"
        print(f"    [{mark}] {c['task']}: {c['n_solved_runs']}/{c['n_runs']} "
              f"runs solved; votes {c['votes']}")
    wrong = sum(c["wrong_modal_agreement"] for c in never_cases)
    print(f"  never-arm wrong-modal agreement: {wrong}/{len(never_cases)} "
          f"tasks with >=2 runs sharing the same wrong top-1")
    for c in never_cases:
        print(f"    {c['task']}: modal_votes={c['modal_votes']} "
              f"wrong_agree={c['wrong_modal_agreement']}")

    out = {"progress": f"{n_done}/{n_expected}",
           "informative_groups": informative,
           "run_pick": results, "agreement": agreement_cases,
           "never_arm": never_cases}
    (HERE / "e1b_eval_result.json").write_text(json.dumps(out, indent=2))
    print("\nsaved e1b_eval_result.json")


if __name__ == "__main__":
    main()
