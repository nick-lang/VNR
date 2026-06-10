# VNR Checklist

Living checklist for the VNR build-and-test program ([vnr-build-test-plan.md](vnr-build-test-plan.md)). Update this when working on VNR; record pivots here and in the plan via commits (see `.cursor/rules/`).

Legend: `[ ]` todo, `[~]` in progress, `[x]` done, `[-]` deferred/blocked (note why).

## Stage 0 — Reproduce the shoulders

- [x] Verify reference repo URLs are canonical
  - TRM = `SamsungSAILMontreal/TinyRecursiveModels` (matches paper arXiv:2510.04871).
  - CompressARC = `iliao2345/CompressARC` (Isaac Liao & Albert Gu).
  - NVARC = `1ytic/NVARC` (Sorokin & Puget, ARC Prize 2025 winner).
- [x] Record hardware reality
  - GPU: RTX 3070 Ti, 8 GB VRAM. Global torch is CPU-only (`2.11.0+cpu`).
- [x] Define committed ARC-AGI-1 dev split (50 tasks): `data/dev_split_arc1.json` + builder `data/build_dev_split.py`.
- [x] Scaffold `experiments/poc-a-baselines/` + notebook entry + results placeholders.
- [x] CompressARC headless harness: `experiments/poc-a-baselines/run_compressarc_task.py`.
- [~] CompressARC baseline run
  - [-] CPU smoke test on global torch: BLOCKED. Global torch is `2.11.0+cpu`; CompressARC's `get_default_device()` raises "Torch not compiled with CUDA" and the repo pins `torch==2.5.1`. Harness + data path reached preprocessing OK; need the venv.
  - [x] Create `.venv-carc` + install CompressARC requirements with a CUDA build of torch (cu124); CUDA verified on the 3070 Ti.
  - [x] GPU functional check: 30-step run prints valid JSON.
  - [x] Real single-task baseline started on GPU (`00576224`, 2000 steps). Cost characterized: ~2.1 s/step -> ~70 min/task on this GPU (README's 12-20 min was a faster 4070). Loss ~910 -> ~82 by step 700; learning confirmed. Full solve run halted early (cost) once the pipeline + cost were validated.
  - [x] Logged per-step cost to `ledger/results.md`. Decision: per-task cost is high on the 3070 Ti; reserve full/bulk solves for cloud or a small task subset; use short step counts for pipeline checks.
- [-] TRM baseline: DEFERRED. Full ARC-AGI-1 training needs ~4 H100s for ~3 days; not feasible on an 8 GB GPU. Do a code-read + cost note now; run on cloud later.
- [x] Stage 0 gate: CompressARC runs correctly end-to-end on GPU and trains as expected (loss decreasing). Per-task cost characterized. Stage 0 complete; ready for Stage 1.

## Stage 1 — Library vs per-task MDL search (H5, riskiest) — COMPLETE, H5 ACCEPTED
- [x] Define minimal grid DSL + interpreter (`dsl.py`, 13 param-free ops).
- [x] Define MDL score (program token count; library macros = 1 token; BPE/MDL compression in `library.py`).
- [x] Implement search to shortest consistent program (`search.py`, BFS over joint grid-state, dedup, budget).
- [x] Arm A (no library) vs Arm B (growing library) on identical held-out tasks (`run_stage1.py`).
- [x] Decide H5: ACCEPTED — median states-to-solution 746 -> 228 (~3.3x), solve rate unchanged (60/60). See `ledger/results.md` + notebook `2026-06-09-stage1-library.md`.
- [ ] Caveat to address later: DSL covers only ~2% of real ARC-AGI-1 (geometric ops only); richer ops + object-centric perception needed (Stage 3) to retest H5 on non-synthetic reuse.

## Stage 2 — Neural proposer amortizes search (H6)
- [ ] Tiny recurrent proposer trained on Stage-1 success traces; compare search cost vs uninformed.

## Stage 3 — Object-centric perception (H7)
- [ ] Object/relation extractor front-end; ablate vs raw-grid on AGI-2 subset.

## Stage 4 — Test-time training, MDL-as-loss (H3)
- [ ] Label-free per-task adaptation; quantify lift and added cost.

## Stage 5 — Integrate full refinement loop (H4)
- [ ] Wire perception -> proposer+library -> verifier -> revise + TTT; measure AGI-1 vs AGI-2 gap.

## Stage 6 — Write-up + spec v1
- [ ] Promote validated design to `spec/architecture-v1.md`; draft write-up; open-source PoCs.
