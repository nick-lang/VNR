# 2026-06-09 — Stage 1: library vs per-task search (H5)

- **PoC:** PoC-VNR-S1 (`experiments/poc-vnr-s1-library/`)
- **Hypothesis:** H5 (growing library beats per-task search) — pre-registered in `ledger/hypotheses.md`.
- **Hardware:** CPU only (pure-Python + numpy); ran in `.venv-carc`. ~7 s wall-clock.
- **Seed:** 0. **Command:** `run_stage1.py --n-train 60 --n-heldout 60 --budget 50000 --arc-coverage 50`.

## Setup
- 13 param-free grid primitives; BFS over the joint state of all train grids, ordered by token count (MDL proxy), dedup, 50k-state budget.
- Synthetic compositional benchmark: ground-truth programs = concatenations of recurring "concept" sub-routines (controlled reuse, guaranteed solvable).
- Arm A: held-out solved from primitives only. Arm B: build an MDL/BPE macro library from solved TRAIN programs, then solve the SAME held-out with primitives + library.
- ARC-AGI-1 dev split (50 tasks) probed with primitives only as a realism check.

## Result
- Train solve rate 1.0; library size 8 (rediscovered planted concepts, e.g. `m0 = [mirror_h, mirror_v]`, plus nested macros).
- Held-out solve rate: Arm A 60/60, Arm B 60/60 (library did not change solvability within budget).
- **Median states-to-solution (shared-solved, n=60): 746 (no library) -> 228 (library) = ratio 0.306 (~3.3x speedup).**
- ARC coverage (primitives): **1/50 (2%)** solved.

## Decision
- **ACCEPT H5** per the pre-registered rule (>=2x search efficiency, solve rate not lower). Recorded in `ledger/results.md`.
- The von Neumann "fixed interpreter + growing library" thesis survives its riskiest cheap test: where reuse exists, the library makes search markedly cheaper.

## Caveats / threats to validity
- The win is on synthetic tasks with reuse by construction. Real-world reuse may be less regular.
- The 13-op geometric DSL covers only ~2% of real ARC-AGI-1 (no object/color/counting ops). H5 is about *search efficiency given reuse*, not DSL coverage — but coverage is the next bottleneck.
- Speedup magnitude depends on the task-length distribution (a smaller subset showed ~14x). The pre-registered 60/60 run (3.3x) is the decision basis.

## Next
- Stage 2 (H6): a neural proposer to amortize search; and/or enrich the DSL + object-centric perception (Stage 3) to raise real-ARC coverage so H5 can be retested on non-synthetic reuse.
