# Results ledger

One row per completed experiment. Links to the full lab-notebook entry in `experiments/notebook/`. Decision is made against the pre-registered rule in `hypotheses.md`.

> Status: empty (no experiments run yet). First entries arrive in Phase 4.

## Metrics tracked (defined in Phase 2)
- **Accuracy** on the task/benchmark.
- **Generalization gap:** ARC-AGI-1 vs ARC-AGI-2 (or train vs OOD on synthetic tasks).
- **Sample efficiency:** accuracy vs number of training examples.
- **Cost proxy:** FLOPs and/or $/task and wall-clock on the reference hardware.

## Log

| Date | Experiment | Hypothesis | Headline metric | Result vs rule | Decision | Notebook entry |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-06-08 | PoC-A TRM baseline | none (baseline) | ARC-AGI-1 pass rate | deferred (needs ~4 H100s/3 days) | defer to cloud | [2026-06-08-stage0-baselines](../experiments/notebook/2026-06-08-stage0-baselines.md) |
| 2026-06-08 | PoC-A CompressARC baseline | none (baseline) | ARC-AGI-1 dev-split pass@2 | pending GPU venv (CPU torch incompatible) | set up venv, run | [2026-06-08-stage0-baselines](../experiments/notebook/2026-06-08-stage0-baselines.md) |
