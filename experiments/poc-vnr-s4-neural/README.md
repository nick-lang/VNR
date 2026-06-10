# PoC-VNR-S4 — Neural per-task MDL substrate baseline (H8, Option B)

Tests whether an UNMODIFIED CompressARC (per-task compression, no pretraining,
no search) clears the bar that killed the hand-built symbolic substrate
(H7-v1..v3): >= 5/50 pass@2 on the same ARC-AGI-1 dev split, kill at <= 2/50.
Pre-registration: `ledger/hypotheses.md` (H8), including a $30 cost gate.

This is the cost/coverage CONTROL for the real VNR question downstream (H9+):
adding cross-task program memory so recurring structure is reused, not
relearned per task.

## How it runs
Cloud fan-out on [Modal](https://modal.com) — one L40S job per task, up to 10
concurrent, vendored `references/CompressARC` shipped into the container image.

```
pip install modal && modal setup            # one-time auth
modal run experiments/poc-vnr-s4-neural/modal_app.py --smoke   # cost gate
modal run experiments/poc-vnr-s4-neural/modal_app.py           # full 50-task run
```

## Result
See [stage4_result.json](stage4_result.json). **ACCEPT H8: 11/50 pass@2 (22%),
all 11 also pass@1** — bar was >= 5/50 and >= 4x the raw-BFS control (1/50).
Matches published CompressARC (~20% on ARC-AGI-1 eval). Superset of every
symbolic-substrate solve (Stages 3b/3c), including `6df30ad6`, which the
symbolic rule overfit and CompressARC solves correctly; raw BFS's `0c786b71`
was not solved (union 12/50).

Cost: 43.3 GPU-hours, ~$84.50 list (~$1.69/task, mean ~52 min/task on L40S).
The run was split by a Modal billing-cap pause at 21/50: banked results are in
`stage4_banked.json` and the remaining 29 were resumed with
`--banked experiments/poc-vnr-s4-neural/stage4_banked.json` (no recompute).

Full narrative: `experiments/notebook/2026-06-10-stage4-compressarc.md`.
Next: H9 — cross-task program memory on this substrate (artifact-saving to be
added to the harness).
