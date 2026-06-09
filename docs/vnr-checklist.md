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
  - [ ] Create `.venv-carc` + install CompressARC requirements with a CUDA build of torch (cu124).
  - [ ] GPU smoke test (few steps), then real baseline (~2000 steps) over a handful of dev-split tasks; record pass@2 + cost.
- [-] TRM baseline: DEFERRED. Full ARC-AGI-1 training needs ~4 H100s for ~3 days; not feasible on an 8 GB GPU. Do a code-read + cost note now; run on cloud later.
- [ ] Stage 0 gate: CompressARC roughly matches reported per-task behavior on the dev split.

## Stage 1 — Library vs per-task MDL search (H5, riskiest)
- [ ] Define minimal grid DSL + interpreter.
- [ ] Define MDL score (program description length; library calls at compressed cost).
- [ ] Implement enumerative/guided search to shortest consistent program.
- [ ] Arm A (no library) vs Arm B (growing library); measure solves/budget + transfer.
- [ ] Decide H5 against pre-registered rule (kill-criterion: no library gain -> pivot).

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
