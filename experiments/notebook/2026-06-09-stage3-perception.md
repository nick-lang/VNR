# 2026-06-09 — Stage 3: object ops + richer DSL on real ARC (H7)

- **PoC:** PoC-VNR-S3 (`experiments/poc-vnr-s3-perception/`)
- **Hypothesis:** H7 (coverage form) — pre-registered in `ledger/hypotheses.md` before the run.
- **Hardware:** CPU only, `.venv-carc`. Full run ~18 min (1068.6 s).
- **Command:** `run_stage3.py --budget 50000 --arc2-probe 30 --h5-train-tasks 80` (deterministic, no seed).

## Setup
- Raw arm: Stage-1 geometric DSL (13 primitives). Object arm: + 6 connected-component object ops (keep/delete/crop largest/smallest) + per-task recolor tokens from the task palette. Same BFS solver, 50k-state budget, depth 7.
- Benchmarks: 50-task ARC-AGI-1 dev split (primary); 30-task ARC-AGI-2 probe; H5-on-real-ARC probe (library from 80 ARC-1 training-split tasks).

## Result
- **Dev split: raw 1/50, object 1/50 — the SAME single task (`0c786b71`, test acc 1.0). Object ops + recolor moved coverage by exactly zero.**
- ARC-AGI-2 probe: 0/30.
- Search behavior: the object arm exhausted the full 50k budget on nearly every task, while the raw arm exhausted its small reachable state space early. The bigger alphabet made search strictly more expensive without unlocking any solutions.
- H5-on-real-ARC probe: gated by coverage. Only 5/80 training tasks solved; solved programs were too short/sparse for BPE to extract even one macro (empty library), so no transfer measurement was possible.

## Decision
- **KILL-CRITERION FIRED (object arm <= 2/50). Recorded per the pre-registered rule.**
- Interpretation: the failure is structural, not a budget or tuning issue. Real ARC tasks are not short compositions of whole-grid transforms; they need per-object program application (map/filter a sub-program over objects), spatial relations, masks, drawing/filling, and size-dependent constructions. Adding more whole-grid tokens only inflates branching.
- Secondary insight: H5-on-real-ARC cannot even be tested until coverage rises — a library needs a corpus of solves to compress. Coverage gates everything downstream.

## Next (pivot, to be decided)
- Option A: structural DSL redesign — object-mapped programs (`for each object: <sub-program>`), object filters as arguments, relations; retest H7 in that form.
- Option B: stop expanding the hand-DSL; use a neural per-task model (CompressARC-style MDL) as the hypothesis substrate and reserve the library/search machinery for where reuse provably exists.
- Either way: synthetic-H5 (Stage 1) stands; real-ARC H5 remains untested pending coverage.
