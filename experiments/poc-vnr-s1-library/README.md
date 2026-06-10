# PoC-VNR-S1 — Library vs per-task search (H5)

Stage 1 of the VNR plan: the load-bearing test of whether a growing cross-task
library of MDL-selected abstractions beats per-task search. Pre-registration:
[../../ledger/hypotheses.md](../../ledger/hypotheses.md) (H5).

## What it is
- [dsl.py](dsl.py) — 13 param-free grid primitives + interpreter (size-capped at 30x30).
- [tasks.py](tasks.py) — synthetic compositional task generator (ground-truth programs are concatenations of recurring "concept" sub-routines) + ARC-AGI-1 dev-split loader.
- [search.py](search.py) — breadth-first search over the joint state of all train grids, ordered by program token count (MDL proxy), with dedup and a node budget.
- [library.py](library.py) — MDL/BPE-style "sleep" step: greedily compress frequent adjacent token pairs in solved programs into named macro-abstractions (may nest).
- [run_stage1.py](run_stage1.py) — Arm A (no library) vs Arm B (growing library) on identical held-out tasks; reports nodes, solve rate, transfer, decision.

## Run
```bash
.\.venv-carc\Scripts\python.exe experiments/poc-vnr-s1-library/run_stage1.py \
  --n-train 60 --n-heldout 60 --budget 50000 --arc-coverage 50
```
(Any Python with numpy works; `.venv-carc` already has it. No GPU needed.)

## Result (seed 0)
See [stage1_result.json](stage1_result.json). Both arms solve 60/60 held-out; the
library cuts median search nodes 746 -> 228 (~3.3x), so **H5 is ACCEPTED** (>=2x,
solve rate not lower). The library rediscovered the planted concepts.

## Honest caveat
The H5 win is on synthetic tasks that contain reusable structure by construction.
On real ARC-AGI-1 the primitive DSL solves only ~2% (1/50) — it lacks object,
color, and counting ops. That is a DSL-coverage limitation for later stages
(richer ops + object-centric perception), not a refutation of H5: where reuse
exists, the library makes search markedly cheaper.
