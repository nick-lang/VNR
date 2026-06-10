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

## Stage 3 — Object-centric perception + richer DSL (H7) — RUN; KILL-CRITERION FIRED
(Pivot 2026-06-09: DSL coverage (~2% of real ARC-AGI-1) is the binding constraint after Stage 1; a neural proposer over an inexpressive DSL would be premature.)
- [x] Pre-register concrete H7 metrics/thresholds.
- [x] Connected-component perception + param-free object ops (`objects.py`).
- [x] Enriched DSL: geometric + object ops + per-task recolor tokens.
- [x] Raw vs enriched arm on the ARC-AGI-1 dev split (matched 50k budget); ARC-AGI-2 probe (30 tasks).
- [x] H5-on-real-ARC probe: gated — only 5/80 training solves, empty library, no transfer measurable.
- [x] Decide H7: **KILL/PIVOT** — object arm 1/50 = raw arm (same task); ARC-2 0/30. Whole-grid op composition is the wrong substrate. See notebook `2026-06-09-stage3-perception.md`.
- [x] PIVOT direction decided: **Option A** — structural redesign around per-object program application. (Option B = neural per-task substrate remains the pre-registered fallback if H7-v2 kills.)

## Stage 3b — Object-mapped substrate (H7-v2) — RUN; INCONCLUSIVE (one solve short of accept)
- [x] Pre-register H7-v2 (same accept/kill bar as v1); amended pre-run with the MDL smallest-mapping prior (caught by synthetic smoke test).
- [x] `segment.py`: dual segmentation (same-color-4 / multicolor-8) + object features.
- [x] `rules.py`: per-object fate induction + selection-crop; exact re-simulation verifier.
- [x] `run_stage3b.py`: raw BFS vs object-map vs union on the dev split + ARC-2 probe.
- [x] Decide H7-v2: **INCONCLUSIVE** — union 4/50 train-consistent (3 new; needed >=5), test-correct 3/50 (one overfit: `6df30ad6`), ARC-2 0/30, full run 3.1 s. See notebook `2026-06-09-stage3b-objectmap.md`.
- [x] NEXT decided (2026-06-09): **A-continue** as Stage 3c.

## Stage 3c — More families + stability guard (H7-v3)
- [ ] Pre-register H7-v3: new families (colormap, gravity, symmetry-fill) + LOO stability guard; "solved" = train-consistent AND guard-passed; same numeric bar.
- [ ] Extend `rules.py` with the three new families (induction order = simplicity).
- [ ] `run_stage3c.py` with the guard; report guarded + unguarded.
- [ ] Validate: guard rejects 3b's spurious `6df30ad6`; measure guard strictness on the two correct 3b solves.
- [ ] Decide H7-v3 against the pre-registered rule.

## Stage 2 — Neural proposer amortizes search (H6) — now after Stage 3
- [ ] Tiny recurrent proposer trained on success traces over the enriched DSL; compare search cost vs uninformed.

## Stage 4 — Test-time training, MDL-as-loss (H3)
- [ ] Label-free per-task adaptation; quantify lift and added cost.

## Stage 5 — Integrate full refinement loop (H4)
- [ ] Wire perception -> proposer+library -> verifier -> revise + TTT; measure AGI-1 vs AGI-2 gap.

## Stage 6 — Write-up + spec v1
- [ ] Promote validated design to `spec/architecture-v1.md`; draft write-up; open-source PoCs.
