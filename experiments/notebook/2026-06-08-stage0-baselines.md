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

## GPU run (update)
- Built `.venv-carc` with `torch==2.5.1+cu124`; CUDA available on the RTX 3070 Ti. Harness runs correctly on GPU (30-step test printed valid JSON).
- **Cost finding:** task `00576224` runs at **~2.1 s/step** (100 steps = 214 s) -> a 2000-step solve is **~70 min** on this GPU, not ~15 min. The README's 12-20 min figure was on a faster RTX 4070 and likely smaller-grid tasks. Loss fell ~910 (step 100) -> ~82 (step 700), so it is learning.
- Implication for Stage 0/later stages: per-task CompressARC cost on the 3070 Ti is high (tens of minutes to ~1h). Use short step counts for pipeline checks; reserve full runs for a small handful of tasks, or move bulk runs to cloud alongside TRM.
- Harness hardened with `--progress-every` heartbeats so long runs are observable and any kill is diagnosable.

## Next
- Let the single full task finish; record pass@2 + wall-clock to `ledger/results.md`.
- Decide step budget vs task count for any further baseline tasks given the ~2.1 s/step cost.
