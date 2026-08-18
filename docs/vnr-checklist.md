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
- [x] Compute pivot (owner, 2026-06-10): long local runs not feasible -> **RunPod pod, 6x A40 ($2.65/hr, prepaid credit, no usage-cap freeze risk)**. All 29 jobs completed in 263 min (~$11.60). Local piece 1 sanity gates agreed with pod (cross-hardware validation).
- [x] Results fetched (`s5_artifacts/`, `stage5_result.json`); owner reminded to stop the pod.
- [x] Decide H9: **KILL** (both conditions: median ratio 1.222 >= 1.0; retention 8/11 <= 8) with validity gate PASSED (61/151-step same-task re-solves) — a real negative, not a broken pipeline. Wins on `6df30ad6`/`cd3c21df`/`903d1b4a` prove transferable structure exists; losses prove averaging corrupts. See notebook `2026-06-11-stage5-weightsoup.md`.
- [x] NEXT decided (2026-06-11): **H10 — retrieval-gated weight memory**, Stage 5b below.

## Stage 5b — Addressable memory: retrieval-gated donor selection (H10) — RUN; KILL-CRITERION FIRED
- [x] Pre-register H10: trial-loss probe (100 steps/candidate, seeded identically) selects ONE donor; same numeric bar as H9 (median ratio <= 0.5, retention >= 10/11); probe overhead reported but not decision-bearing; self-retrieval validity gate.
- [x] Build `s5b_runner.py` (sel_/ret_/selfsel_ jobs vs banked H9 cold baselines) + dispatcher `--stage 5b`.
- [x] Local smoke of probe-selection logic.
- [x] Owner: redeployed A40 pod (5x, not 6 — same hardware class, comparison unaffected) with the SAME network volume; all 11 `donor_*.pt` + 11 cold baselines survived, no retrain.
- [x] Run: 24/24 jobs, 175 min wall, ~$6.50; artifacts fetched to `s5_artifacts/` (`job5b_*.json`, `stage5b_summary.json`); owner reminded to stop the pod.
- [x] Decide H10: **KILL** (both conditions: median ratio 1.396 >= 1.0; retention 7/11 <= 8) with validity gate PASSED (both self-retrieval checks ranked own donor #1 with margin). ZERO wins — no task trained faster from its best foreign donor than from scratch; selection collapsed onto "universal donors" (`d2acf2cb` picked 6/11), not task families. Combined with H9: whole-blob weight memory is closed — the soup's wins came from averaging, not from any single donor's content. See notebook `2026-06-11-stage5b-retrieval.md`.
- [x] NEXT decided (2026-06-11): memory track PAUSES with a clean two-kill negative (per owner's standing no-premature-memory-optimization direction); program returns to the remaining architecture slots (Stage 6 TTT / Stage 2 redefinition / Stage 7 loop).

## Stage 5f — Jointly trained shared backbone (H14) — the amortization mechanism H9/H10 left alive
- [x] Protocol decision (2026-06-11, $0, from banked data via `budget_analysis.py`): iteration budget cut 2000 -> 1000 steps (all 9 A40 cold solves stable by step 541, median 222; 9/9 retained at half cost). 2000 stays for benchmark-grade claims.
- [x] Pre-register H14: joint training (shared transformation weights, per-task latents, round-robin) over 3 folds of the 9 A40-solvable tasks; warm-start held-out tasks; same numeric bar rescaled (accept median <= 0.5 + retention >= 8/9; kill >= 1.0 or <= 7/9); permutation-symmetry rationale recorded in advance.
- [x] Build `s5f_runner.py` (fold_/jval_/jret_/jprobe_ jobs; true tensor aliasing for shared weights) + dispatcher `--stage 5f`.
- [x] Local smoke of joint-training mechanics: 2752 transformation tensors shared as identical objects across 2 task models; both losses dropped 8x in 30 round-robin cycles; backbone save/load round-trips.
- [-] Owner go/no-go on ~$6 pod spend; redeploy A40 pod with the same network volume. BLOCKED/STALE (2026-07-06): the A40 pods are no longer available; owner now has a local RTX 5090 (32 GB).
- [x] 5090 environment: `.venv-carc` rebuilt (Python 3.12, **torch 2.11.0+cu128** — protocol deviation from the pinned 2.5.1, which predates Blackwell/sm_120; recorded here and in the notebook). CompressARC re-cloned (commit `83a2221`, Jan 2026 upstream). CUDA verified on the 5090; 100-step GPU smoke OK (~1.0 s/step — ~2x the 3070 Ti, slower than L40S; CompressARC is overhead-bound, not compute-bound).
- [x] Transfer + joint-training mechanics smokes re-run on the new torch: both PASS (10984 tensors round-trip exact; 2752 shared tensors alias correctly; losses drop).
- [x] `s5f_runner.py` extended per the amendments: `cold5090_*` rebase jobs (all 11 H8-solved tasks, 1000 steps), jret weights saved for the delta-geometry readout, `--deltas` mode (pairwise cosine of per-task deltas vs fold backbone), summary decision now anchored to 5090 colds.
- [x] Full H14 queue run locally on the 5090 ($0): 30/30 jobs, ~10.4 h wall (4-way parallel workers, ~1.36x aggregate; WDDM context switching caps the gain). 5090 cold rebase clean: 9/11, same tasks as A40.
- [x] Decide H14: **VOID per pre-registered rule — validity gate failed 3/3** (no backbone re-solved its own training task; plumbing separately verified). Descriptive: median jret/cold 3.436 (warm slower on all 9), retention 6/9, probes 0/3. Delta readout: per-task deltas orthogonal (median cos 0.0067) — nothing to amortize. Third weight-space-memory negative (H9, H10, H14). See notebook `2026-07-07-stage5f-joint-backbone.md`.
- [x] OWNER FORK resolved (2026-07-07): **CLOSE the weight-space amortization track** (owner accepted recommendation). H14b will not run; Stage 5e stays deferred; three independent negatives stand (H9, H10, H14).

## Strategic review (2026-07-06)
- [x] Goal clarified (owner): main goal = frontier-level capability at near-zero usage cost; ARC is the benchmark proxy, not the goal. Recorded in `docs/plan.md` + build-test plan thesis.
- [x] Targeted literature pass done ($0): 7 notes in `lit/` + verdict in `experiments/notebook/2026-07-06-lit-pass-strategic-review.md`. Headlines: H9/H10 kills match known merging negatives (basin misalignment), so they don't indict the memory thesis; library thesis got real-ARC external validation (Pang, ARC Prize runner-up) plus a compute-matching evaluation warning; ArcMemo independently confirms parts-not-blobs memory (Stage 5e direction); ARC Prize Foundation names the EFFICIENCY gap as the open science problem — matching the clarified goal; frontier-level usage cost is rising ~3-18x/yr, so cheap capability won't arrive by default.
- [x] H14 design consequences pre-registered in `ledger/hypotheses.md`: 5090 cold-baseline rebase, H14b (Reptile-style outer step) as the escalation if H14 is marginal/kill, and a delta-geometry secondary readout (task-vector cosine matrix) feeding Stage 5e.

## Stage 2 — Neural proposer amortizes search (H6) — now after Stage 3
- [ ] Tiny recurrent proposer trained on success traces over the enriched DSL; compare search cost vs uninformed. NOTE: designed for the killed symbolic substrate — needs redefinition before it runs.

## Stage 5c — Learned addressing (H11) [CLOSED 2026-06-11: gate failed — H10 killed]
- [-] Gate was "H10 accepts." With blob retrieval dead there is nothing worth addressing at blob granularity. The banked 11x10 probe matrix is kept as data.

## Stage 5d — Memory links + pruning at library scale (H12) [CLOSED 2026-06-11: gate failed — blob memory killed twice (H9, H10)]
- [-] A 400-donor library of monolithic blobs inherits H10's zero-win result at scale. Links/pruning only become meaningful again over decomposed (part-granularity) memories.

## Stage 5e — Concept-level decomposition (H13) [DEFERRED: the only surviving form of weight-space memory]
- [-] H10's kill REDIRECTS here rather than running it now: whole-blob reuse is dead (twice, by independent mechanisms), so any future weight-space memory must store PARTS — (a) layer/module-wise retrieval (testable with transfer.py), (b) latent-space library, (c) symbolic BPE macros (Stage 1's accepted result, still the program's only validated concept-granularity memory). Deferred per owner direction until the integrated loop (Stage 7) shows memory is the binding constraint.

## Stage 6 — Test-time compute: restart diversity + MDL selection (H15; H3 redefined for the neural substrate)
- [x] Pre-register H15 (2026-07-07): on the 39 H8-unsolved dev tasks, arm A = 1x2000 steps seed 0 vs arm B = 2x1000 steps seeds 1/2 with tail-loss (MDL) selection, matched compute; ACCEPT if B >= A+2 and B >= 2; KILL if B <= A. Secondary: selection accuracy, union-of-B oracle, seed-sensitivity check on the 9 solved tasks.
- [x] Build `experiments/poc-vnr-s6-ttc/s6_runner.py` (claims-based parallel workers, banked/resumable; 126 jobs, ~165k steps, ~34h at measured 4-way throughput, $0).
- [x] Run on the 5090: 126/126 jobs, 169.3 GPU-h summed, $0, 2026-07-07 -> 07-20 (survived owner pauses, an IDE-session death, and a reboot via the banked queue).
- [x] Decide H15: **KILL per pre-registered rule** — arm A 3/39 vs arm B 2/39; union-of-B oracle ties A (3), so even perfect selection adds nothing; tail-loss selector refuted (1/2, anti-correlated with solving). Headline finding: coverage is seed-stochastic (arm A solved 3 tasks H8 didn't with the SAME protocol; seed-1 check lost 2/9 banked solves; dev union 11 -> 15/50 by re-rolls). Seed-marginalized solve probability is the metric from now on. See notebook `2026-07-20-stage6-restart-diversity.md`.
- [ ] NEXT (owner input welcome): Stage 2 proposer redefinition is the last unbuilt architecture slot; substrate-external memory (symbolic library / concept memory) is the surviving memory route; a voting/consistency selector over seeds is a deferred H16 candidate.

## Write-up prep (Stage 8 pulled forward; owner decision 2026-08-18)
- [x] Post-H15 literature pass for the write-up ($0): 6 new notes in `lit/` (TTA-at-matched-compute, certified self-consistency, test-time transduction, ARC-AGI-3 report, prospective compression, TRM-TTA note); 2 candidates rejected (DSL-synthesis = pure theory; TTU voting paper inaccessible). Verdicts + write-up consequences in `experiments/notebook/2026-08-18-lit-pass-writeup-prep.md`. Headline: H15 tested the wrong diversity axis (input augmentation, not seed, wins at matched compute); mode-estimation formalism found for seed-marginalized metrics; selection should eliminate on disagreement, not score.
- [x] E1-A — banked-data selector phase (2026-08-18, $0): banked scalars support only LOSS scorers (picks/grids were never banked), and the corpus holds just 8 informative groups. final_loss picked the solver in 6/8 (tail_loss 4/6; final_loss fixed both B-pair tail misses) — weak-n hint that last-step loss beats tail-mean; needs E1-B sample size. `e1_selector_bakeoff.py` + `e1a_result.json`.
- [~] E1-B — capture runs LAUNCHED 2026-08-18 (`e1b_runner.py`: 34 jobs, 44k steps, ~8.6 h at 3-way, $0; scope + selector evaluation pre-registered in the module docstring; 30-step smoke banked all capture fields). Worker-count bench on this rig: 1/2/3/4-way -> 0.81/1.33/1.42/1.44 aggregate steps/s; 3 workers chosen. NONDETERMINISM FOUND during the bench: seven same-seed same-task 120-step runs spread final loss 436-571 — a fixed seed does NOT pin the trajectory on this hardware/torch, so "seed-stochastic" coverage is really RUN-stochastic, banked runs are not regenerable, and E1-B runs double as fresh draws for run-marginalized solve probability (feeds E2).
- [ ] E2 — seed-budget curve: binomial CIs on per-task solve probability + pass@k-over-seeds plot (~15-30 h wall on the 5090, $0). Owner go/no-go after E1.
- [ ] E3 — H16 pre-registration: augmentation-voting (D8 x color perms) at matched compute vs banked arm A; equivariance smoke gate BEFORE the full run (if CompressARC is effectively D8/color-equivariant, augmentation collapses into seed diversity). Owner go/no-go after E1.
- [x] Coverage analysis for the write-up (2026-08-18, $0, CPU): `coverage_analysis.py` over all 198 banked cold runs — union 11 -> 15/50; ever-solved set = 7 always-solved core + 8 fractional-fringe (p^ 0.25-0.75) + 35 never; matched-group flip rates 18-67%; auto-includes E1-B artifacts on re-run. `coverage_analysis.json`.
- [x] E1-B selector evaluation script ready (`e1b_eval.py`, dry-run clean on empty artifacts): final_loss / tail_loss / vote_margin / pick_stability run-pick selectors + cross-run agreement voting with the never-arm wrong-modal (false-positive) readout; re-runnable on partial queues.
- [~] Write-up draft v0 (`writeup/draft-v0.md`, 2026-08-18): full structure + all banked numbers in; `[E1B: ...]` slots await capture results; targets ARC Prize paper track.

## Stage 9 — Amortized interpreter: latent-program search (H17/H18) [PROPOSED 2026-08-18; owner go/no-go pending]
- [ ] OWNER: approve/amend H17 pre-registration (draft bars in `experiments/notebook/2026-08-18-strategic-direction-h17.md`): tiny-LPN (10-30M) on re-arc, Grad-1 train-for-search, frozen-decoder latent-only inference; run-marginalized dev-split coverage at total-cost accounting vs banked CompressARC baselines. Drops zero-pretraining purity (teacher-free procedural pretrain, one-time, ~2-6 days 5090, $0 cloud); rationale recorded in the notebook entry.
- [ ] H18 (gated on H17 accept): grow the latent-program distribution via hindsight replay of self-verified solves vs frozen-distribution control — the LLM-free library-thesis attack on LPN's stated program-diversity ceiling.
- Context: LPN (NeurIPS 2025) = the correctly-run inversion of our H14 negative; see `lit/2025-latent-program-network.md`.

## Stage 7 — Integrate full refinement loop (H4)
- [ ] Wire perception -> proposer+library -> verifier -> revise + TTT; measure AGI-1 vs AGI-2 gap.

## Stage 8 — Write-up + spec v1
- [ ] Promote validated design to `spec/architecture-v1.md`; draft write-up; open-source PoCs.
