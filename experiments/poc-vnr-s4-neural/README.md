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
Pending.
