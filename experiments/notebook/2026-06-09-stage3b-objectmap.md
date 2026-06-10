# 2026-06-09 — Stage 3b: object-mapped substrate (H7-v2)

- **PoC:** PoC-VNR-S3b (`experiments/poc-vnr-s3b-objectmap/`)
- **Hypothesis:** H7-v2 — pre-registered in `ledger/hypotheses.md` (incl. a pre-run amendment: MDL = smallest consistent mapping, caught by the synthetic smoke test before touching the benchmark).
- **Hardware:** CPU only, `.venv-carc`. Full run **3.1 s** (vs ~18 min for Stage 3a's token search).
- **Command:** `run_stage3b.py --budget 50000 --arc2-probe 30` (deterministic).

## Setup
- Substrate redesign per the Option A pivot: programs are per-object rules, not whole-grid token chains.
  - Family 1 (same-shape fates): object -> keep/delete/recolor-to-c, fate = f(one feature); among consistent features pick the smallest mapping (MDL); verify by exact re-simulation.
  - Family 2 (selection-crop): output = crop of the object picked by a unique-selection predicate.
  - Dual segmentation: same-color-4 and multicolor-8.
- Arms: raw BFS (control, unchanged), object-map alone, union (system under test). Same dev split + ARC-2 probe as v1.

## Result
- **Union 4/50 train-consistent (raw 1 + 3 new). Accept needed >= 5: INCONCLUSIVE (one short). Kill (<= 2) not hit.**
- Test correctness of new solves: `ae58858e` 1.0, `cd3c21df` 1.0, `6df30ad6` 0.0 (spurious size->color lookup; memorized train). **Union test-correct 3/50.**
- ARC-AGI-2: 0/30 (all arms).
- Cost: rule induction solves the whole benchmark ~1000x faster than token BFS.

## Reading
- The structural change did what token-stacking couldn't: +3 new solves from just TWO rule families, instantly. The substrate direction is alive but under-powered — coverage now looks family-limited (movement, drawing, symmetry-completion, per-object geometric transforms, relational fates are all unimplemented).
- The `6df30ad6` overfit shows the weak spot: with few train pairs, parameter-heavy lookups can be train-consistent yet wrong. Needs a stronger prior (penalize mapping size vs train support) or held-out-within-train validation.
- ARC-2 remains untouched: its tasks need composition beyond single rules, consistent with the survey's compositional-collapse finding.

## Decision / next
- Per the pre-registered rule: INCONCLUSIVE — no auto-prescribed direction. Options:
  - **A-continue:** add 2-3 more rule families + an overfit guard, re-run the same bar (cheap: seconds per iteration now).
  - **B:** switch to the neural per-task substrate (CompressARC-style MDL).
  - Bank and pause.
- Direction left to the program owner; trajectory evidence favors one more A iteration.
