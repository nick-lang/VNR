# PoC-VNR-S3 — Object ops + richer DSL on real ARC (H7)

Stage 3 of the VNR plan (run before Stage 2 per the 2026-06-09 ordering pivot).
Tests whether object-centric ops + per-task recolor tokens lift real-ARC
coverage over the Stage-1 geometric DSL at a matched search budget.
Pre-registration and outcome: [../../ledger/hypotheses.md](../../ledger/hypotheses.md) (H7).

## What it is
- [objects.py](objects.py) — same-color 4-connected component extraction (pure numpy) + 6 param-free object ops (keep/delete/crop largest/smallest; ties = inapplicable).
- [run_stage3.py](run_stage3.py) — raw arm (Stage-1 13 primitives) vs object arm (+ object ops + palette recolor tokens) on the 50-task ARC-AGI-1 dev split; 30-task ARC-AGI-2 probe; H5-on-real-ARC library probe (reuses Stage-1 `search.py`/`library.py`).

## Run
```bash
.\.venv-carc\Scripts\python.exe experiments/poc-vnr-s3-perception/run_stage3.py \
  --budget 50000 --arc2-probe 30 --h5-train-tasks 80
```
CPU-only; full run ~18 min.

## Result
See [stage3_result.json](stage3_result.json). **KILL-CRITERION FIRED:** object arm
1/50 = raw arm 1/50 (identical task), ARC-2 0/30, budget exhausted everywhere;
library probe coverage-gated (5/80 training solves -> empty library). Whole-grid
op composition is the wrong hypothesis substrate for real ARC; see the notebook
entry for the pivot options (per-object programs vs neural substrate).
