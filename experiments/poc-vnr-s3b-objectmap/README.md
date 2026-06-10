# PoC-VNR-S3b — Object-mapped substrate (H7-v2)

The Option A pivot after H7-v1 killed: programs are per-object rules (induced
object -> fate mappings, or select-and-crop by predicate) instead of whole-grid
token chains. Pre-registration + outcome: [../../ledger/hypotheses.md](../../ledger/hypotheses.md).

## What it is
- [segment.py](segment.py) — dual segmentation (same-color 4-conn / multicolor 8-conn) + object features (size, ranks, shape key, border contact, counts).
- [rules.py](rules.py) — two verified rule families:
  - same-shape fates: object -> keep/delete/recolor-to-c with fate = f(one feature); among consistent features, the smallest mapping wins (MDL prior);
  - selection-crop: output = crop of the uniquely selected object.
- [run_stage3b.py](run_stage3b.py) — raw BFS (control) vs object-map vs union on the 50-task dev split + 30-task ARC-2 probe.

## Run
```bash
.\.venv-carc\Scripts\python.exe experiments/poc-vnr-s3b-objectmap/run_stage3b.py --budget 50000 --arc2-probe 30
```
CPU-only; ~3 s total.

## Result (v2, two families)
See [stage3b_result.json](stage3b_result.json). Union 4/50 train-consistent
(raw 1 + 3 new; test-correct 3/50 — `6df30ad6` overfit its train pairs).
**INCONCLUSIVE** per the pre-registered bar (accept needed >= 5). ARC-2: 0/30.
Rule induction is ~1000x cheaper than token BFS (3 s vs ~18 min).

## Stage 3c (v3): more families + stability guard
[run_stage3c.py](run_stage3c.py) adds colormap / gravity / symmetry-fill
families to `rules.py` plus a leave-one-out stability guard. Result
([stage3c_result.json](stage3c_result.json)): **KILL-CRITERION FIRED** —
new families added zero solves even unguarded; the guard rejected the overfit
correctly but also both correct v2 solves (`loo_disagree`). Guarded union 1/50.
Per the pre-registered rule, the hand-built substrate is closed at this effort
level; Option B (neural per-task MDL substrate) is the default next step.
Note: `rules.py` now contains the v3 families, so re-running `run_stage3b.py`
reflects the extended induction order; exact v2 behavior is at commit `d3710c6`.
