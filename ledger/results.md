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
| 2026-06-08 | PoC-A CompressARC baseline | none (baseline) | per-step cost + pipeline validity | pipeline validated on GPU; ~2.1 s/step (~70 min/2000-step task) on RTX 3070 Ti; loss ~910->~82 by step 700; full solve run halted early to conserve time | runnable baseline confirmed; reserve full/bulk solves for cloud or a small task subset | [2026-06-08-stage0-baselines](../experiments/notebook/2026-06-08-stage0-baselines.md) |
| 2026-06-09 | PoC-VNR-S1 library vs search | H5 | median states-to-solution (held-out, shared-solved n=60) | 746 (no lib) -> 228 (lib) = ~3.3x; solve rate 60/60 both arms; >=2x threshold met | ACCEPT H5 (caveat: synthetic reuse; DSL covers ~2% of real ARC-AGI-1) | [2026-06-09-stage1-library](../experiments/notebook/2026-06-09-stage1-library.md) |
| 2026-06-09 | PoC-VNR-S3 object ops + recolor | H7 (coverage form) | ARC-AGI-1 dev-split solve count, object arm vs raw | object 1/50 = raw 1/50 (same task); ARC-2 0/30; budget exhausted, no new solves; library probe gated (5/80 train solves, empty library) | KILL/PIVOT per pre-registered rule: whole-grid composition is the wrong substrate; redesign toward per-object programs/relations | [2026-06-09-stage3-perception](../experiments/notebook/2026-06-09-stage3-perception.md) |
| 2026-06-09 | PoC-VNR-S3b object-mapped substrate | H7-v2 | dev-split union solve count vs raw | union 4/50 train-consistent (3 new; test-correct 3/50, one overfit), raw 1/50; ARC-2 0/30; full run 3.1 s (~1000x cheaper than token BFS) | INCONCLUSIVE (accept needed >=5): substrate direction alive but family-limited; next direction = owner decision (extend families + overfit guard vs Option B) | [2026-06-09-stage3b-objectmap](../experiments/notebook/2026-06-09-stage3b-objectmap.md) |
