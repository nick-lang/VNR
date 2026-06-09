# Experiments (`experiments/`)

Tiny, laptop-runnable proof-of-concept experiments (Phase 4+). Each PoC gets its own subdirectory (`poc-a-trm/`, `poc-b-memory/`, ...) plus a dated lab-notebook entry in `notebook/`.

## Discipline
1. Pre-register the hypothesis + metric in `../ledger/hypotheses.md`.
2. Create a notebook entry from `notebook/TEMPLATE.md` (named `YYYY-MM-DD-shortname.md`).
3. Keep code small, seeded, and reproducible. Log exact command, seed, and hardware.
4. On completion, add a row to `../ledger/results.md` and update the relevant `spec/` section.

## Sizing constraint
Everything must run on a laptop, a single consumer GPU, or free cloud credits. If an idea needs more, shrink the task until it fits — the program optimizes for cheap, fast falsification.

## Planned PoCs
- `poc-a-trm` — reproduce a tiny baseline (TRM ~7M and/or CompressARC) on ARC-AGI-1.
- `poc-b-memory` — external addressable memory vs longer context (H1).
- `poc-c-objective` — next-token vs MDL/latent-prediction objective (H2).
- `poc-d-ttt` — per-task test-time learning lift (H3).
- `poc-e-refine` — propose/verify refinement loop (H4).
