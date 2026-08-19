"""H20 — MVG rescue attempt (pre-registered in ledger/hypotheses.md).

Removes H19's three named confounds at once: binding capacity (top-K=4 score
contest each epoch), horizon-matched retention (EMA decay 0.8/epoch of use
counts instead of binary 2-epoch forgetting), and a HARD transfer set
(3-concept compositions, mostly unsolvable raw at budget) so the primary
metric is solve rate, not node noise. Streams and arms as in H19: M = ring
order, R = exact permutation of the same tasks, F = fixed pair; 5 seeds.

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
sys.path.insert(0, str(HERE))

import dsl  # noqa: E402
import library as lib  # noqa: E402
import search  # noqa: E402
from tasks import CONCEPTS, Task, _make_pair  # noqa: E402
from h19_runner import RING, HELDOUT_PAIRS, gen_pair_task  # noqa: E402

N_EPOCHS, TASKS_PER_EPOCH = 12, 10
N_TRANSFER = 30
BUDGET, MAX_DEPTH = 50_000, 10
MAX_DEPTH_TRANSFER = 3  # pre-run amendment: depth-capped transfer (assay probes)
LIB_CAP = 4            # binding top-level capacity
PROPOSE_CAP, MIN_COUNT = 4, 2
EMA_DECAY = 0.8        # retention horizon ~ matched to the 6-epoch ring cycle
FIXED_PAIR = RING[0]


def gen_hard_task(pair, rng, name, k_concepts=3):
    """A transfer task whose program is k concept draws from pair (6+ prims)."""
    for _ in range(500):
        chosen = [pair[int(rng.integers(0, 2))] for _ in range(k_concepts)]
        program = [p for c in chosen for p in CONCEPTS[c]]
        pairs = []
        ok = True
        for _ in range(5):
            p = _make_pair(rng, program, 2)  # small inputs: 3 concepts can grow grids fast
            if p is None:
                ok = False
                break
            pairs.append(p)
        if ok:
            return Task(name=name, train=pairs[:3], test=pairs[3:],
                        gt_program=program, meta={"concepts": chosen})
    return None  # caller retries with a different held-out pair


def build_streams(seed):
    rng = np.random.default_rng(seed)
    m_stream = []
    for e in range(N_EPOCHS):
        pair = RING[e % len(RING)]
        for t in range(TASKS_PER_EPOCH):
            m_stream.append(gen_pair_task(pair, rng, f"M_e{e:02d}_t{t}"))
    r_stream = [m_stream[i] for i in rng.permutation(len(m_stream))]
    f_stream = [gen_pair_task(FIXED_PAIR, rng, f"F_{i:03d}")
                for i in range(N_EPOCHS * TASKS_PER_EPOCH)]
    transfer = []
    i = 0
    while len(transfer) < N_TRANSFER:
        pair = HELDOUT_PAIRS[i % len(HELDOUT_PAIRS)]
        t = gen_hard_task(pair, rng, f"X_{len(transfer):03d}")
        i += 1
        if t is not None:
            transfer.append(t)
        if i > N_TRANSFER * 40:
            raise RuntimeError("could not build hard transfer set")
    return m_stream, r_stream, f_stream, transfer


class ContestLibrary:
    """Top-K macro store: incumbents (EMA-scored by use) vs fresh proposals."""

    def __init__(self):
        self.macros: dict[str, tuple[str, str]] = {}   # includes helpers
        self.top: dict[str, float] = {}                # top-level name -> score
        self.n_created = 0
        self.log: list[dict] = []

    def ops(self):
        return lib.make_ops(self.macros)

    def _store_flat(self, flat):
        name = f"m{self.n_created}"
        self.n_created += 1
        self.macros[name] = self._encode(flat, name)
        return name

    def _encode(self, flat, name):
        if len(flat) == 2:
            return (flat[0], flat[1])
        helper = f"{name}_h{len(flat)}"
        self.macros[helper] = self._encode(flat[:-1], helper)
        return (helper, flat[-1])

    def _gc_helpers(self):
        keep = set()
        def mark(tok):
            if tok in self.macros:
                keep.add(tok)
                a, b = self.macros[tok]
                mark(a); mark(b)
        for t in self.top:
            mark(t)
        for name in list(self.macros):
            if name not in keep:
                del self.macros[name]

    def epoch_update(self, epoch, solved_programs, used_counts):
        # decay incumbents, credit this epoch's uses
        for name in self.top:
            self.top[name] = EMA_DECAY * self.top[name] + used_counts.get(name, 0)
        # proposals from this epoch's solved programs, expanded to primitives
        corpus = [lib.expand_program(p, self.macros) for p in solved_programs if p]
        proposals = lib.build_library(corpus, cap=PROPOSE_CAP, min_count=MIN_COUNT)
        existing = {tuple(lib.expand(m, self.macros)) for m in self.top}
        counts = {}
        for pname in proposals:
            flat = tuple(lib.expand(pname, proposals))
            if flat in existing:
                continue
            # score proposal by its frequency in this epoch's corpus
            freq = sum(1 for seq in corpus
                       for i in range(len(seq) - len(flat) + 1)
                       if tuple(seq[i:i + len(flat)]) == flat)
            counts[flat] = freq
        # contest: incumbents + proposals -> top K by score
        cands = [(score, ("inc", name)) for name, score in self.top.items()]
        cands += [(freq, ("new", flat)) for flat, freq in counts.items()]
        cands.sort(key=lambda x: -x[0])
        new_top: dict[str, float] = {}
        added, dropped = [], []
        for score, (kind, ref) in cands[:LIB_CAP]:
            if kind == "inc":
                new_top[ref] = score
            else:
                name = self._store_flat(list(ref))
                new_top[name] = score
                added.append({"name": name, "expansion": list(ref), "score": score})
        dropped = [n for n in self.top if n not in new_top]
        self.top = new_top
        self._gc_helpers()
        self.log.append({"epoch": epoch, "added": added, "dropped": dropped,
                         "top": {n: round(s, 2) for n, s in self.top.items()}})

    def search_ops(self):
        """Primitives + only the current top-level macros (helpers hidden)."""
        ops, _ = lib.make_ops(self.macros)
        token_names = list(dsl.PRIMITIVES) + list(self.top)
        return ops, token_names


def run_arm(stream, transfer, arm_name):
    plib = ContestLibrary()
    online = []
    for e in range(N_EPOCHS):
        chunk = stream[e * TASKS_PER_EPOCH:(e + 1) * TASKS_PER_EPOCH]
        ops, tokens = plib.search_ops()
        solved_programs, used = [], {}
        for pos, task in enumerate(chunk):
            res = search.search_task(task.train, ops, tokens,
                                     budget=BUDGET, max_depth=MAX_DEPTH)
            online.append({"epoch": e, "pos": pos, "task": task.name,
                           "solved": res.solved, "nodes": res.nodes})
            if res.solved:
                solved_programs.append(res.program)
                for tok in res.program:
                    if tok in plib.top:
                        used[tok] = used.get(tok, 0) + 1
        plib.epoch_update(e, solved_programs, used)
    ops, tokens = plib.search_ops()
    xfer = []
    for task in transfer:
        res = search.search_task(task.train, ops, tokens,
                                 budget=BUDGET, max_depth=MAX_DEPTH_TRANSFER)
        xfer.append({"task": task.name, "solved": res.solved,
                     "nodes": res.nodes if res.solved else BUDGET,
                     "test_acc": search.test_accuracy(res.program, task.test, ops)
                     if res.solved else 0.0})
    concept_seqs = {tuple(v) for v in CONCEPTS.values()}
    aligned = [m for m in plib.top
               if tuple(lib.expand(m, plib.macros)) in concept_seqs]
    return {"arm": arm_name, "online": online, "transfer": xfer,
            "library_log": plib.log,
            "final_macros": {m: list(lib.expand(m, plib.macros))
                             for m in plib.top},
            "alignment": f"{len(aligned)}/{len(plib.top)}"}


def run_seed(seed):
    m_s, r_s, f_s, transfer = build_streams(seed)
    out = {"seed": seed}
    for name, stream in [("M", m_s), ("R", r_s), ("F", f_s)]:
        t0 = time.time()
        out[name] = run_arm(stream, transfer, name)
        out[name]["seconds"] = round(time.time() - t0, 1)
    raw = []
    for task in transfer:
        res = search.search_task(task.train, dict(dsl.PRIMITIVES),
                                 list(dsl.PRIMITIVES), budget=BUDGET,
                                 max_depth=MAX_DEPTH_TRANSFER)
        raw.append({"task": task.name, "solved": res.solved})
    out["RAW"] = {"transfer": raw}
    return out


def summarize(seed_results):
    def rate(arm, r):
        ts = r[arm]["transfer"]
        return sum(t["solved"] for t in ts) / len(ts)
    rows = []
    for r in seed_results:
        rows.append({"seed": r["seed"],
                     "solve_rate": {a: round(rate(a, r), 3)
                                    for a in ("M", "R", "F")},
                     "raw_rate": round(sum(t["solved"] for t in r["RAW"]["transfer"])
                                       / len(r["RAW"]["transfer"]), 3),
                     "alignment": {a: r[a]["alignment"] for a in ("M", "R", "F")}})
    m_solve = sum(t["solved"] for r in seed_results for t in r["M"]["transfer"])
    r_solve = sum(t["solved"] for r in seed_results for t in r["R"]["transfer"])
    n = sum(len(r["M"]["transfer"]) for r in seed_results)
    raw_solve = sum(t["solved"] for r in seed_results for t in r["RAW"]["transfer"])
    m_wins = sum(1 for row in rows
                 if row["solve_rate"]["M"] >= row["solve_rate"]["R"])
    pooled_m, pooled_r, pooled_raw = m_solve / n, r_solve / n, raw_solve / n
    summary = {"per_seed": rows,
               "pooled_solve_rate": {"M": round(pooled_m, 3), "R": round(pooled_r, 3),
                                     "RAW": round(pooled_raw, 3)},
               "pooled_solves": f"M {m_solve} vs R {r_solve} of {n}",
               "seeds_M_geq_R": f"{m_wins}/{len(rows)}"}
    # design-validity gate: raw baseline must be materially below library arms
    if pooled_raw >= min(pooled_m, pooled_r):
        summary["decision_h20"] = "VOID (hard-transfer premise failed: raw >= library arms)"
        return summary
    if pooled_m >= pooled_r + 0.10 and m_wins >= 4:
        summary["decision_h20"] = "ACCEPT"
    elif pooled_m <= pooled_r:
        summary["decision_h20"] = "KILL (second kill -> MVG closed for the symbolic substrate per pre-registration)"
    else:
        summary["decision_h20"] = "INCONCLUSIVE"
    return summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--seeds", type=int, default=5)
    args = ap.parse_args()

    if args.smoke:
        global N_EPOCHS, TASKS_PER_EPOCH, N_TRANSFER
        N_EPOCHS, TASKS_PER_EPOCH, N_TRANSFER = 3, 4, 6
        r = run_seed(999)
        small = {a: {"alignment": r[a]["alignment"],
                     "final_macros": r[a]["final_macros"],
                     "transfer_solved": sum(t["solved"] for t in r[a]["transfer"]),
                     "seconds": r[a]["seconds"]}
                 for a in ("M", "R", "F")}
        small["RAW_solved"] = sum(t["solved"] for t in r["RAW"]["transfer"])
        print(json.dumps(small, indent=2))
        return
    if args.run:
        results = []
        for s in range(args.seeds):
            t0 = time.time()
            results.append(run_seed(s))
            print(f"seed {s} done in {time.time() - t0:.0f}s", flush=True)
        summary = summarize(results)
        (HERE / "h20_result.json").write_text(json.dumps(
            {"summary": summary, "seeds": results}, indent=2))
        print(json.dumps(summary, indent=2))
        return
    ap.print_help()


if __name__ == "__main__":
    main()
