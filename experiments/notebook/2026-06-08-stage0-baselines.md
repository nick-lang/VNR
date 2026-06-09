# 2026-06-08 — Stage 0 baselines (PoC-A)

- **PoC:** PoC-A (reproduce the shoulders)
- **Hypothesis:** none (baseline establishment + cost yardstick)
- **Hardware:** RTX 3070 Ti, 8 GB VRAM; global Python 3.11.9 with torch `2.11.0+cpu`.

## Setup
Goal: establish runnable baselines and a cost yardstick before building VNR.
- Verified reference repo URLs are canonical (TRM, CompressARC, NVARC) by reading their bundled READMEs.
- Built a committed 50-task ARC-AGI-1 dev split (`data/dev_split_arc1.json`, `data/build_dev_split.py`): sorted eval IDs, every 8th, first 50.
- Wrote a headless harness `run_compressarc_task.py` (pass@2 vs ground-truth solution hash + wall-clock).
- CompressARC bundles ARC-AGI-1 data in `references/CompressARC/dataset/`, so no data conversion needed.

## Result
- **TRM:** confirmed full ARC-AGI-1 training needs ~4 H100s for ~3 days (repo README). Not feasible on the 8 GB GPU -> deferred to cloud. Architecture insight (recursive answer/latent refinement) retained for the VNR proposer.
- **CompressARC CPU smoke test (10 steps, task 00576224):** FAILED to run on the global env. The global torch is `2.11.0+cpu`; CompressARC's `preprocessing.py` calls `torch.get_default_device()`, which raises `AssertionError: Torch not compiled with CUDA enabled` on this CPU-only 2.11 build. CompressARC pins `torch==2.5.1`.
  - Takeaway: the harness + data path are wired correctly (it reached preprocessing); the blocker is the torch build/version. A dedicated venv with the pinned CUDA torch is required — which we want anyway to actually use the GPU.

## Decision
- Proceed to set up `.venv-carc` with CompressARC's pinned requirements + a CUDA build of torch (cu124) to use the 3070 Ti, then re-run the smoke test and a real per-task baseline (target ~2000 steps, expected ~12-20 min/task).
- Recorded the Stage 0 pivot (TRM deferred; CompressARC = runnable baseline) in the plan and checklist.

## Next
- Create venv + install CUDA torch; smoke test (few steps) on GPU; then full baseline over a handful of dev-split tasks; log pass@2 + cost to `ledger/results.md`.
