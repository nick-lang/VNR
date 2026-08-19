"""H19 — Modularly-varying goals as the library-growth curriculum (Stage 9 pilot).

Tests the Kashtan & Alon (PNAS 2005) transfer claim in the program's validated
symbolic library substrate (Stage 1 harness): does a MODULARLY varying task
stream grow a more reusable abstraction library than the same tasks in random
order, under identical compute?

Design (pre-registered in ledger/hypotheses.md before the full run):
  Concepts: the 6 Stage-1 concept subroutines. Epoch goals are concept PAIRS.
  Arm M (MVG):    12 epochs x 10 tasks; epoch pairs cycle a ring where each
                  pair shares one concept with the next: (c0,c1),(c1,c2),...,
                  (c5,c0), twice. Goals switch; subgoals are shared.
  Arm R (random): THE SAME 120 tasks, order shuffled. Identical task multiset,
                  identical marginals — the arms differ ONLY in temporal
                  structure.
  Arm F (fixed):  120 tasks from the single pair (c0,c1) (K&A's fixed-goal
                  control; marginals necessarily differ).
  Library (unified Treasure 1+2 mechanics): persistent across epochs, cap 12.
  After each epoch: BPE proposals (<=4 new, min_count 2) from THAT epoch's
  solved programs (expanded to primitives); prune macros with zero uses in
  solutions for 2 consecutive epochs (utility-style forgetting; no pruning
  before epoch 3). Search always uses primitives + current library.
  Transfer: 30 held-out tasks from the 6 "distance-2" ring pairs — concept
  combinations NEVER used as an epoch goal — solved with each arm's FINAL
  library, same budget. Raw-primitives baseline reported for reference.
  Known threat (recorded in advance): BPE counts are order-invariant, so any
  curriculum effect must flow through window locality + capacity/retention
  pressure; a clean null here is evidence about the MECHANISM (MVG needs
  selection pressure to bite), not sloppiness.

Usage: --smoke | --run [--seeds N]
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
import library as lib  # noqa: E402
import search  # noqa: E402
from tasks import CONCEPTS, Task, _make_pair  # noqa: E402

CONCEPT_NAMES = list(CONCEPTS)  # 6, in file order
RING = [(CONCEPT_NAMES[i], CONCEPT_NAMES[(i + 1) % 6]) for i in range(6)]
HELDOUT_PAIRS = [(CONCEPT_NAMES[i], CONCEPT_NAMES[(i + 2) % 6]) for i in range(6)]

N_EPOCHS, TASKS_PER_EPOCH = 12, 10
N_TRANSFER = 30
BUDGET, MAX_DEPTH = 50_000, 8
LIB_CAP, PROPOSE_CAP, MIN_COUNT = 12, 4, 2
PRUNE_AFTER = 2  # epochs of zero use before a macro is dropped
FIXED_PAIR = RING[0]


def gen_pair_task(pair, rng, name):
    """A task whose program is 2 concept draws (with replacement) from pair."""
    for _ in range(200):
        chosen = [pair[int(rng.integers(0, 2))] for _ in range(2)]
        program = [p for c in chosen for p in CONCEPTS[c]]
        pairs = []
        ok = True
        for _ in range(5):  # 3 train + 2 test
            p = _make_pair(rng, program, 3)
            if p is None:
                ok = False
                break
            pairs.append(p)
        if ok:
            return Task(name=name, train=pairs[:3], test=pairs[3:],
                        gt_program=program, meta={"concepts": chosen})
    raise RuntimeError(f"could not generate task for pair {pair}")


def build_streams(seed, n_epochs, tasks_per_epoch):
    """Return (arm_M_stream, arm_R_stream, arm_F_stream); M and R share tasks."""
    rng = np.random.default_rng(seed)
    m_stream = []
    for e in range(n_epochs):
        pair = RING[e % len(RING)]
        for t in range(tasks_per_epoch):
            m_stream.append(gen_pair_task(pair, rng, f"M_e{e:02d}_t{t}"))
    r_stream = [m_stream[i] for i in rng.permutation(len(m_stream))]
    f_stream = [gen_pair_task(FIXED_PAIR, rng, f"F_{i:03d}")
                for i in range(n_epochs * tasks_per_epoch)]
    transfer = []
    for i in range(N_TRANSFER):
        pair = HELDOUT_PAIRS[i % len(HELDOUT_PAIRS)]
        transfer.append(gen_pair_task(pair, rng, f"X_{i:03d}"))
    return m_stream, r_stream, f_stream, transfer


class PersistentLibrary:
    """Cap-limited macro store with per-epoch BPE proposals + use-based pruning."""

    def __init__(self):
        self.macros: dict[str, tuple[str, str]] = {}
        self.zero_use_epochs: dict[str, int] = {}
        self.n_created = 0
        self.log: list[dict] = []

    def ops(self):
        return lib.make_ops(self.macros)

    def epoch_update(self, epoch, solved_programs, used_counts):
        # 1. prune (after a grace period) macros unused for PRUNE_AFTER epochs
        pruned = []
        for name in list(self.macros):
            if used_counts.get(name, 0) == 0:
                self.zero_use_epochs[name] = self.zero_use_epochs.get(name, 0) + 1
            else:
                self.zero_use_epochs[name] = 0
            if epoch >= 2 and self.zero_use_epochs[name] >= PRUNE_AFTER:
                # drop only if no surviving macro references it
                referenced = any(name in pair for m, pair in self.macros.items()
                                 if m != name)
                if not referenced:
                    del self.macros[name]
                    del self.zero_use_epochs[name]
                    pruned.append(name)
        # 2. propose from this epoch's solved programs (expanded to primitives)
        corpus = [lib.expand_program(p, self.macros) for p in solved_programs if p]
        proposals = lib.build_library(corpus, cap=PROPOSE_CAP, min_count=MIN_COUNT)
        added = []
        existing = {tuple(lib.expand(m, self.macros)) for m in self.macros}
        for _, pair in proposals.items():
            if len(self.macros) >= LIB_CAP:
                break
            # re-express proposal pair in terms of primitives, then store as a
            # macro over primitives (flat) to keep expansion well-defined
            flat = tuple(lib.expand(pair[0], proposals) + lib.expand(pair[1], proposals))
            if flat in existing:
                continue
            name = f"m{self.n_created}"
            self.n_created += 1
            # store as chain: flat sequence encoded left-assoc via helper macros
            self.macros[name] = self._encode_flat(flat, name)
            self.zero_use_epochs[name] = 0
            existing.add(flat)
            added.append({"name": name, "expansion": list(flat)})
        self.log.append({"epoch": epoch, "added": added, "pruned": pruned,
                         "size": len(self.macros)})

    def _encode_flat(self, flat, name):
        """Encode a flat primitive sequence as nested binary macros."""
        if len(flat) == 2:
            return (flat[0], flat[1])
        helper = f"{name}_h{len(flat)}"
        self.macros[helper] = self._encode_flat(flat[:-1], helper)
        self.zero_use_epochs[helper] = 0
        return (helper, flat[-1])


def run_arm(stream, transfer, arm_name, n_epochs, tasks_per_epoch):
    plib = PersistentLibrary()
    online = []
    for e in range(n_epochs):
        chunk = stream[e * tasks_per_epoch:(e + 1) * tasks_per_epoch]
        ops, tokens = plib.ops()
        solved_programs, used = [], {}
        for task in chunk:
            res = search.search_task(task.train, ops, tokens,
                                     budget=BUDGET, max_depth=MAX_DEPTH)
            acc = search.test_accuracy(res.program, task.test, ops) if res.solved else 0.0
            online.append({"epoch": e, "task": task.name, "solved": res.solved,
                           "nodes": res.nodes, "depth": res.depth,
                           "test_acc": acc})
            if res.solved:
                solved_programs.append(res.program)
                for tok in res.program:
                    if tok in plib.macros:
                        used[tok] = used.get(tok, 0) + 1
        plib.epoch_update(e, solved_programs, used)
    # transfer with the FINAL library
    ops, tokens = plib.ops()
    xfer = []
    for task in transfer:
        res = search.search_task(task.train, ops, tokens,
                                 budget=BUDGET, max_depth=MAX_DEPTH)
        xfer.append({"task": task.name, "solved": res.solved,
                     "nodes": res.nodes if res.solved else BUDGET,
                     "test_acc": search.test_accuracy(res.program, task.test, ops)
                     if res.solved else 0.0})
    # macro-concept alignment of the final library (helpers excluded)
    concept_seqs = {tuple(v) for v in CONCEPTS.values()}
    top = [m for m in plib.macros if "_h" not in m]
    aligned = [m for m in top
               if tuple(lib.expand(m, plib.macros)) in concept_seqs]
    return {"arm": arm_name, "online": online, "transfer": xfer,
            "library_log": plib.log,
            "final_macros": {m: list(lib.expand(m, plib.macros)) for m in top},
            "alignment": f"{len(aligned)}/{len(top)}"}


def run_seed(seed, n_epochs=N_EPOCHS, tasks_per_epoch=TASKS_PER_EPOCH):
    m_s, r_s, f_s, transfer = build_streams(seed, n_epochs, tasks_per_epoch)
    out = {"seed": seed}
    for name, stream in [("M", m_s), ("R", r_s), ("F", f_s)]:
        t0 = time.time()
        out[name] = run_arm(stream, transfer, name, n_epochs, tasks_per_epoch)
        out[name]["seconds"] = round(time.time() - t0, 1)
    # raw-primitives transfer baseline (no library)
    raw = []
    for task in transfer:
        res = search.search_task(task.train, dict(dsl.PRIMITIVES),
                                 list(dsl.PRIMITIVES), budget=BUDGET,
                                 max_depth=MAX_DEPTH)
        raw.append({"task": task.name, "solved": res.solved,
                    "nodes": res.nodes if res.solved else BUDGET})
    out["RAW"] = {"transfer": raw}
    return out


def summarize(seed_results):
    def med_nodes(arm, r):
        return statistics.median(t["nodes"] for t in r[arm]["transfer"])
    def solve_rate(arm, r):
        ts = r[arm]["transfer"]
        return sum(t["solved"] for t in ts) / len(ts)
    rows = []
    for r in seed_results:
        rows.append({
            "seed": r["seed"],
            "med_transfer_nodes": {a: med_nodes(a, r) for a in ("M", "R", "F")},
            "raw_med_nodes": statistics.median(t["nodes"] for t in r["RAW"]["transfer"]),
            "solve_rate": {a: solve_rate(a, r) for a in ("M", "R", "F")},
            "M_over_R": round(med_nodes("M", r) / max(med_nodes("R", r), 1), 3),
            "alignment": {a: r[a]["alignment"] for a in ("M", "R", "F")},
        })
    ratios = [row["M_over_R"] for row in rows]
    n_low = sum(1 for x in ratios if x <= 0.75)
    pooled_m = statistics.median(x for r in seed_results for x in
                                 (t["nodes"] for t in r["M"]["transfer"]))
    pooled_r = statistics.median(x for r in seed_results for x in
                                 (t["nodes"] for t in r["R"]["transfer"]))
    m_solve = sum(t["solved"] for r in seed_results for t in r["M"]["transfer"])
    r_solve = sum(t["solved"] for r in seed_results for t in r["R"]["transfer"])
    summary = {"per_seed": rows, "ratio_seeds_leq_0.75": f"{n_low}/{len(rows)}",
               "pooled_median_M_over_R": round(pooled_m / max(pooled_r, 1), 3),
               "pooled_solves_M_vs_R": f"{m_solve} vs {r_solve}"}
    if n_low >= 4 and len(rows) >= 5 and m_solve >= r_solve:
        summary["decision_h19"] = "ACCEPT"
    elif summary["pooled_median_M_over_R"] >= 1.0:
        summary["decision_h19"] = "KILL"
    else:
        summary["decision_h19"] = "INCONCLUSIVE"
    return summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--seeds", type=int, default=5)
    args = ap.parse_args()

    if args.smoke:
        r = run_seed(999, n_epochs=3, tasks_per_epoch=4)
        small = {a: {"seconds": r[a]["seconds"], "alignment": r[a]["alignment"],
                     "final_macros": r[a]["final_macros"],
                     "online_solved": sum(t["solved"] for t in r[a]["online"]),
                     "transfer_solved": sum(t["solved"] for t in r[a]["transfer"])}
                 for a in ("M", "R", "F")}
        print(json.dumps(small, indent=2))
        (HERE / "h19_smoke.json").write_text(json.dumps(r, indent=2))
        return
    if args.run:
        results = []
        for s in range(args.seeds):
            t0 = time.time()
            results.append(run_seed(s))
            print(f"seed {s} done in {time.time() - t0:.0f}s", flush=True)
        summary = summarize(results)
        (HERE / "h19_result.json").write_text(json.dumps(
            {"summary": summary, "seeds": results}, indent=2))
        print(json.dumps(summary, indent=2))
        return
    ap.print_help()


if __name__ == "__main__":
    main()
