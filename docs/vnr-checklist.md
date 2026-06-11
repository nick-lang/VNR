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

## Stage 3c — More families + stability guard (H7-v3) — RUN; KILL-CRITERION FIRED
- [x] Pre-register H7-v3: new families (colormap, gravity, symmetry-fill) + LOO stability guard; "solved" = train-consistent AND guard-passed; same numeric bar.
- [x] Extend `rules.py` with the three new families (induction order = simplicity).
- [x] `run_stage3c.py` with the guard; report guarded + unguarded.
- [x] Validate: guard rejected `6df30ad6` correctly (abstain) but ALSO rejected both correct 3b solves (`loo_disagree`) — the pre-registered known risk materialized fully.
- [x] Decide H7-v3: **KILL** — guarded union 1/50; new families added zero solves even unguarded; ARC-2 0/30. See notebook `2026-06-09-stage3c-families-guard.md`.
- [x] NEXT decided (2026-06-09): **Option B as Stage 4**, on cloud (Modal) with a <= $30 out-of-pocket budget approved by owner; local fallback if the smoke-test cost projection exceeds it.

## Stage 4 — Neural per-task MDL substrate baseline (H8, Option B) — RUN; ACCEPTED
- [x] Pre-register H8: unmodified CompressARC, 2000 steps/task, pass@2, same 50-task dev split, same numeric bar (accept >= 5/50; kill <= 2/50); cost gate $30.
- [x] Build Modal fan-out harness (`experiments/poc-vnr-s4-neural/`): one GPU job per task, results collected locally.
- [x] Owner: create Modal account; authorize this machine (`modal setup`).
- [x] Cloud smoke: 1 task, 0.825 s/step on L40S, projected $44.71 list (under budget after credits) — gate passed.
- [x] Full 50-task fan-out (split by a billing-cap pause at 21/50; owner approved cost, plan upgraded, 29 resumed via `--banked`, no recompute). Actual: 43.3 GPU-h, ~$84.50 list (~2x projection — fan-out tasks ran slower than the smoke task).
- [x] Decide H8: **ACCEPT** — 11/50 pass@2 (all pass@1), superset of all symbolic solves incl. 3b's overfit task `6df30ad6`; raw BFS's `0c786b71` not solved (union 12/50). See notebook `2026-06-10-stage4-compressarc.md`.
- [x] NEXT decided (2026-06-10): H9 designed and pre-registered as Stage 5 below.

## Stage 5 — Cross-task weight memory (H9) — first non-reproduction stage
- [x] Pre-register H9: LOO weight-soup warm-start over the 11 H8-solved tasks; accept = median steps-to-stable-solve <= 0.5x cold AND retention >= 10/11; kill = no speedup or retention <= 8/11.
- [x] Build `experiments/poc-vnr-s5-memory/`: transfer machinery (extract/average/load transformation weights; latents always fresh) + two-phase Modal harness; CompressARC stays unmodified.
- [x] Local smoke: transfer mechanics verified (10984 tensors, exact round-trip, latents untouched, soup = mean, training runs after warm load).
- [x] Owner decision (2026-06-10): Modal not usable — **run locally on the 3070 Ti in resumable pieces** (`local_runner.py`: every job banked on completion; early-signal ordering = 2 colds -> 2 same-task validity gates -> rest). Upside: both arms on identical hardware.
- [~] Compute pivot (owner, 2026-06-10): long local runs not feasible -> **RunPod pod, 6x A40 ($2.65/hr, prepaid credit, no usage-cap freeze risk)**. `runpod_queue.py` dispatching all 29 jobs, one per GPU, results banked on the pod's persistent volume; ~1.1 s/step measured (~37 min/2000-step job), ~5 waves ~= 3.5-4 h, ~$10. Local piece 1 (2 colds + 2 sanity gates) left running as a cross-hardware validation sample.
- [ ] Fetch s5_artifacts + summary from pod; STOP POD; decide H9 against the pre-registered rule; record everywhere.
- [ ] Decide H9 against the pre-registered rule; record everywhere.

## Stage 2 — Neural proposer amortizes search (H6) — now after Stage 3
- [ ] Tiny recurrent proposer trained on success traces over the enriched DSL; compare search cost vs uninformed.

## Stage 6 — Test-time training, MDL-as-loss (H3) — renumbered (Stage 5 = H9 memory)
- [ ] Label-free per-task adaptation; quantify lift and added cost.

## Stage 7 — Integrate full refinement loop (H4)
- [ ] Wire perception -> proposer+library -> verifier -> revise + TTT; measure AGI-1 vs AGI-2 gap.

## Stage 8 — Write-up + spec v1
- [ ] Promote validated design to `spec/architecture-v1.md`; draft write-up; open-source PoCs.
