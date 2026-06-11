# Hypothesis register (pre-registration)

Hypotheses are registered here BEFORE the corresponding experiment runs, with a pre-committed metric and decision rule. Outcomes are recorded in `results.md`. This guards against post-hoc rationalization.

> Status: SEED. H1-H4 below are drafted from the plan; they will be sharpened with exact metrics/thresholds in Phase 2.

## H1 — Memory vs context
- **Statement:** An explicit read/write addressable memory outperforms a longer context window for multi-fact algorithmic recall, at equal parameter count.
- **Targets limitation:** L1.
- **Benchmark:** synthetic recall/extrapolation tasks (associative recall, copy, lookup) with controllable length.
- **Metric / decision rule (to finalize in Phase 2):** accuracy at out-of-distribution sequence lengths; accept if memory model >= context model by a pre-set margin at fixed params.
- **PoC:** PoC-B.

## H2 — Objective
- **Statement:** A compression/MDL or latent-prediction objective generalizes better than next-token on controlled compositional tasks.
- **Targets limitation:** L2, L4.
- **Metric / decision rule:** generalization gap (train vs OOD) under matched backbone/compute.
- **PoC:** PoC-C.

## H3 — Test-time learning
- **Statement:** Per-task adaptation (test-time fine-tuning / latent-state refinement) is the dominant lever for fluid generalization.
- **Targets limitation:** L4, L3.
- **Reference effect to replicate:** TTFT lifting ARC pass rate ~17.5% -> ~45% in a controlled setup.
- **PoC:** PoC-D.

## H4 — Compositionality via propose/verify
- **Statement:** A propose/verify refinement loop narrows the ARC-AGI-1 -> ARC-AGI-2 generalization gap vs a single-pass model.
- **Targets limitation:** L3.
- **Metric / decision rule:** AGI-1 vs AGI-2-subset gap, single-pass vs refinement loop, matched compute.
- **PoC:** PoC-E.

---

## Architecture hypotheses (VNR build-and-test plan)

These three are introduced by the synthesized "fixed core + growing library" architecture. See [docs/vnr-build-test-plan.md](../docs/vnr-build-test-plan.md). They reinterpret L1 for the ARC setting: "addressable memory" = a growing library of reusable abstractions, not long-context recall.

## H5 — Growing library beats per-task search (the core, riskiest thesis)
- **Statement:** A growing cross-task library of MDL-selected abstractions on top of a fixed interpreter improves search/sample efficiency and transfer versus per-task MDL search with no library.
- **Targets limitation:** L1 (reinterpreted), L3, L4.
- **Metric / decision rule:** tasks solved per unit search budget, and forward-transfer (solve rate on held-out tasks after library growth) — library variant must beat no-library by a pre-set margin at equal compute.
- **Kill-criterion:** if the library gives no search/sample-efficiency gain, the von Neumann framing weakens -> pivot away from library-centric design.
- **Stage / PoC:** Stage 1.

### H5 pre-registration (2026-06-09, before running)
- **Setup:** a fixed param-free grid DSL + interpreter. Search = breadth-first over the joint state of all train input grids, ordered by program token count (shortest-program / MDL proxy); dedup by state; per-task budget cap on states evaluated. A task is "solved" iff a program maps every train input to its output (then test accuracy is reported separately).
- **Arms (identical tasks, identical budget):**
  - **A (no library):** every task searched from primitives only.
  - **B (growing library):** build a library of MDL-selected macro-abstractions from solved TRAIN-set programs (sleep/compression step), then search the HELD-OUT set with primitives + library.
- **Datasets:** (1) a synthetic compositional benchmark where ground-truth programs are concatenations of recurring "concept" sub-routines (controlled reuse, guaranteed solvable); (2) the ARC-AGI-1 dev split as a coverage reality-check.
- **Primary metric:** median states-evaluated-to-solution on the held-out set (over tasks both arms solve).
- **Secondary metric:** held-out solve rate within the per-task budget.
- **Decision rule (pre-committed):**
  - **Accept H5** if Arm B's median states-to-solution on the shared-solved held-out tasks is <= 50% of Arm A's (i.e., >= 2x search efficiency) AND Arm B's solve rate is not lower than Arm A's.
  - **Kill / pivot** if Arm B reduces median states-to-solution by <= 10% OR lowers solve rate. (DSL-search remains a component, but library-centric design is demoted.)
  - **Inconclusive** (10-50% improvement): keep the library but flag that the effect is weak; investigate abstraction quality before relying on it.
- **Fixed knobs:** per-task budget = 50,000 states; max grid dim = 30; library cap = 8 abstractions; seed = 0.

## H6 — Neural proposer amortizes search
- **Statement:** A tiny recurrent proposer distilled from successful search traces (wake-sleep / SOAR-style) reduces search cost at fixed solve rate versus uninformed search.
- **Targets limitation:** L4, L5.
- **Metric / decision rule:** search nodes/FLOPs to first solution at matched solve rate, neural-guided vs uninformed.
- **Stage / PoC:** Stage 2.

## H7 — Object-centric perception lifts compositional generalization
- **Statement:** An object/relation-structured input representation narrows the AGI-1 -> AGI-2 gap versus a raw-grid representation, at matched solver.
- **Targets limitation:** L3.
- **Metric / decision rule:** AGI-2-subset solve rate, object-centric vs raw-grid front-end, matched solver/compute.
- **Stage / PoC:** Stage 3.

### H7 pre-registration (2026-06-09, before running) — coverage form
- **Setup:** same BFS solver and budget as Stage 1 (50,000 states, max depth 7, deterministic). Two arms on identical tasks:
  - **Raw arm:** Stage-1 geometric DSL (13 primitives).
  - **Object arm:** geometric primitives + connected-component object ops (keep/delete/crop largest/smallest) + per-task recolor tokens instantiated from the task palette.
- **Primary benchmark:** the committed 50-task ARC-AGI-1 dev split. "Solved" = program consistent with all train pairs (test-pair exact accuracy reported separately, as in Stage 1).
- **Secondary probes:** (a) 30-task ARC-AGI-2 evaluation subset (first 30 sorted IDs) for the AGI-1 vs AGI-2 gap; (b) H5-on-real-ARC: build a BPE/MDL library from ARC-1 *training-split* solves and report delta solved + delta nodes on the dev split.
- **Decision rule (pre-committed):**
  - **Accept H7 (coverage form)** if the object arm solves >= 5/50 dev tasks (10%) AND >= 4x the raw arm's solve count.
  - **Kill / pivot** if the object arm solves <= 2/50 — object ops + recolor at this grain don't move coverage; rethink perception (relations, masks, per-object programs) before proceeding.
  - **Inconclusive** otherwise: report and decide direction in the notebook.
- **Fixed knobs:** budget 50,000 states; max depth 7; library cap 8; min macro count 2; no seed needed (deterministic search).

### H7 outcome (2026-06-09): KILL-CRITERION FIRED
- Object arm solved 1/50 dev tasks — identical to the raw arm (same task, `0c786b71`). ARC-AGI-2 probe: 0/30. The enriched alphabet exhausted the 50k budget on nearly every task (vs early frontier exhaustion for raw): extra whole-grid tokens made search strictly more expensive without unlocking solutions.
- H5-on-real-ARC probe was gated by coverage: only 5/80 training tasks solved, programs too short/sparse for BPE to extract a single macro (empty library).
- **Decision per pre-registered rule: KILL/PIVOT.** Whole-grid op composition (even with object-selection and recolor ops) is the wrong hypothesis substrate for real ARC. The pivot direction (pre-registered): per-object program application (map/filter over objects), relations, masks — a structural DSL redesign, not more whole-grid tokens.
- **Pivot direction decided 2026-06-09: Option A (structural redesign), tested as H7-v2 below.**

### H7-v2 pre-registration (2026-06-09, before running) — object-mapped substrate
- **Statement:** a per-object hypothesis substrate (induce a rule mapping each object to a fate, or select-and-crop an object by an induced predicate) lifts real-ARC coverage where whole-grid token composition could not.
- **Setup:** two segmentations (same-color 4-connected; multicolor 8-connected). Two rule families, both verified by exact re-simulation on all train pairs:
  1. **Same-shape per-object fates:** each input object maps to keep / delete / recolor-to-c; the fate is a function of ONE object feature (constant, color, is_largest, is_smallest, touches_border, size, size_rank, shape_key, shape_count, color_count). *Amended pre-run (2026-06-09, caught by synthetic smoke test before touching the benchmark): among consistent keys, pick the one with the SMALLEST mapping (fewest entries = shortest description, the proper MDL choice), ties broken by the fixed order — a fixed order alone preferred spuriously specific lookups that fail on unseen values.* Inapplicable if output has cells outside input objects (generative tasks).
  2. **Selection-crop:** output equals one input object's crop (object-cells or bbox variant); the selector is a fixed-order list of predicates (is_largest, is_smallest, unique_color, unique_shape, only-touching-border, only-not-touching-border) that must select exactly one object per pair.
- **Arms:** raw BFS (Stage-1 13 primitives, 50k budget, depth 7) — the unchanged control; object-map solver alone; **union (object-map, else raw BFS) = the system under test.**
- **Benchmarks:** same as H7-v1 — 50-task ARC-AGI-1 dev split primary, 30-task ARC-AGI-2 probe secondary. "Solved" = train-consistent; test-pair exact accuracy reported separately.
- **Decision rule (pre-committed, same bar v1 failed):**
  - **Accept H7-v2** if the union solves >= 5/50 AND >= 4x the raw arm's count.
  - **Kill** if the union solves <= 2/50 — the hand-built program substrate road is then judged closed at this effort level; Option B (neural per-task substrate) becomes the default next step.
  - **Inconclusive** otherwise.

### H7-v2 outcome (2026-06-09): INCONCLUSIVE — one solve short of accept
- Union: **4/50 train-consistent** (raw 1 + 3 new from the object-map substrate); accept needed >= 5. Kill threshold (<= 2) not hit. ARC-AGI-2 probe: 0/30.
- Test-pair correctness of the new solves: `ae58858e` 1.0 (size-threshold recolor), `cd3c21df` 1.0 (select-crop by unique color), `6df30ad6` 0.0 — a spuriously specific size->color lookup that memorized train pairs (train-consistent but wrong). Union test-correct: 3/50.
- Cost: the whole dev split + ARC-2 probe ran in ~3 s (vs ~18 min for the v1 token search): rule induction is ~1000x cheaper than BFS over tokens.
- Reading: the structural substrate change moved coverage where token-stacking moved nothing (0 new -> 3 new), with only TWO rule families implemented (per-object fates, selection-crop). The overfit case shows the verifier needs either more train support or a stronger simplicity prior for parameter-heavy lookups. Direction decision recorded in the notebook/checklist.
- **Direction decided 2026-06-09: A-continue, tested as H7-v3 below.**

### H7-v3 pre-registration (2026-06-09, before running) — more families + stability guard
- **Changes vs v2:**
  1. **New rule families** (induction order = simplicity order: colormap, same-shape fates, gravity, symmetry-fill, selection-crop):
     - *Cellwise color permutation:* same-shape; a consistent color->color lookup over all cells of all train pairs (non-identity).
     - *Gravity/move:* all objects slide maximally in one of 4 directions (settling order = furthest along the direction first); both segmentations.
     - *Symmetry-fill:* zeros filled from a grid symmetry (fliplr / flipud / rot180 / transpose-if-square) that reproduces every train output and fills at least one cell.
  2. **Stability guard (the overfit fix):** a rule counts as a solve ONLY if (a) it predicts (no abstention) on every test input, and (b) for every leave-one-out subset of the train pairs, the re-induced rule exists and produces IDENTICAL predictions on all test inputs. (Test inputs are visible at solve time; outputs are not.)
- **"Solved" (v3) = train-consistent AND guard-passed** — strictly harder than v2's definition. Unguarded counts reported alongside for transparency.
- **Arms:** raw BFS control (unchanged, no guard); object-map (guarded); union (guarded object-map, else raw).
- **Decision rule (pre-committed, same numeric bar):** accept if guarded union >= 5/50 AND >= 4x raw; kill if <= 2/50; else inconclusive.
- **Validation expectation (recorded in advance):** the guard should reject 3b's spurious `6df30ad6` rule; whether it keeps the two correct 3b solves is an open measurement of guard strictness (LOO from few pairs may pick a different-but-agreeing or disagreeing rule).
- **Known risk:** for 2-pair tasks the LOO induction sees a single pair and may legitimately disagree, costing correct solves; this is measurable (unguarded vs guarded gap) and accepted for v3.

### H7-v3 outcome (2026-06-09): KILL-CRITERION FIRED
- **Guarded union 1/50 (raw only) — kill threshold (<= 2) hit.** ARC-AGI-2: 0/30 in every arm. Full run 4.1 s.
- Finding 1 — **new families added zero solves:** colormap, gravity, and symmetry-fill solved no dev task even unguarded (unguarded count stayed at v2's 3). Hand-building families plateaus immediately on this split; the remaining tasks need composition/relations, not more single-rule families.
- Finding 2 — **the stability guard rejected 3/3 unguarded solves:** `6df30ad6` correctly (abstain — its lookup did not cover the test input), but both genuinely correct v2 solves via `loo_disagree` (LOO re-induction picks different-but-plausible rules whose test predictions differ). The pre-registered known risk materialized fully: discrete rule identity is too brittle for LOO agreement under 2-4 train pairs.
- Combined honest verdict: even under v2's friendlier definition, two Option-A iterations max out at 4/50 train-consistent / 3/50 test-correct, with the marginal family contributing nothing. **Per the pre-registered rule: the hand-built program substrate road is closed at this effort level; Option B (neural per-task substrate, CompressARC-style MDL) is the default next step.**
- Salvage worth keeping: the object segmentation/features machinery (reusable as a front-end), the result that rule induction is ~1000x cheaper than token search, and the negative result on LOO-stability as a verifier for discrete rules.

## H8 — Neural per-task MDL substrate clears the bar the symbolic substrate failed (Stage 4 / Option B)

### H8 pre-registration (2026-06-09, before running)
- **Hypothesis:** an unmodified CompressARC model (per-task compression, no pretraining, no search), trained 2000 steps per task, solves >= 5/50 of the SAME dev split (pass@2, CompressARC's published selection protocol: top-1 or top-2 most-frequent decoded solution matches ground truth) — i.e. it clears the exact numeric bar that killed the hand-built symbolic substrate (H7-v1..v3).
- **Why this bar:** comparability. Same 50 tasks, same accept threshold (>= 5/50 and >= 4x the raw-BFS control's 1/50), same kill threshold (<= 2/50). Published CompressARC numbers (~20% on ARC-AGI-1 eval) predict ~10/50, so an accept is expected — the run's value is (a) confirming the substrate choice on our split with our protocol, and (b) characterizing per-task cost as the baseline for the REAL question (H9+, cross-task memory/amortization, where VNR departs from reproduction).
- **Protocol:** vendored CompressARC (commit as cloned, unmodified), 2000 steps/task, Adam lr=0.01 betas=(0.5,0.9), seeds as-shipped; one GPU-job per task fanned out on Modal (L40S default); harness = same logic as Stage 0's `run_compressarc_task.py`.
- **Pre-registered cost gate:** smoke ONE task in the cloud first to measure s/step; if projected full-run out-of-pocket cost (after Modal's free credits) exceeds $30, do NOT launch the fan-out — fall back to a local run (owner-approved). Record actual $ spent in the results ledger.
- **Decision rule (pre-committed):** accept H8 if pass@2 solves >= 5/50; kill if <= 2/50; else inconclusive. Pass@1 reported alongside for transparency.

### H8 outcome (2026-06-10): ACCEPTED
- **11/50 pass@2 (22%), and all 11 are pass@1** — more than double the accept bar (>= 5/50), 11x the raw-BFS control (1/50). Matches published CompressARC (~20% on ARC-AGI-1 eval) on our split: clean reproduction, no protocol surprises.
- **Strict superset of every symbolic-substrate solve:** all 3 of Stage 3b's object-map solves (`ae58858e`, `cd3c21df`, and `6df30ad6` — the task the symbolic rule OVERFIT, here solved correctly) plus 8 more. The raw-BFS solve `0c786b71` was NOT solved (union 12/50): small but real complementarity between search and compression.
- **Cost baseline for H9+:** mean ~52 min/task on L40S (range 25-128 min), 43.3 GPU-hours of completed-task compute (~$84.50 list, ~$1.69/task). **Actual billed (owner dashboard, 2026-06-10): $116.31 usage − $30 credits = $86.31 out of pocket.** The ~$32 above the completed-task estimate = smoke test + CPU/memory + partial progress on in-flight tasks lost at the billing-cap freeze (banked results needed no recompute, but mid-training tasks restarted in the resume).
- **Protocol deviations (recorded):** (1) the $30 cost-gate projection ($44.71 list) was exceeded in practice (~$84.50 list) because fan-out per-task times ran ~2x the smoke task's; owner explicitly approved finishing regardless of cost mid-run. (2) The run was split across two app invocations due to the cap pause; same code, same protocol, disjoint task sets, so comparability is unaffected.
- Reading: the substrate slot in the VNR architecture is filled — per-task MDL compression expresses real ARC structure that hand-built rules could not. The defining limitation is now AMNESIA: 50 tasks = 50 disposable models, ~$1.69 and ~52 min each, zero accumulated knowledge. H9 (cross-task program memory / amortization) is the first stage where VNR departs from reproduction.

## H9 — Cross-task weight memory amortizes per-task compression (Stage 5)

### H9 pre-registration (2026-06-10, before running)
- **Architecture fact the design rests on:** CompressARC factors into task-shaped LATENTS (`multiposteriors`, `target_capacities` — sized by each task's grids; never transferable) and fixed-shape TRANSFORMATION WEIGHTS (decode, share-up/down, softmax, cummax, shift, direction-share, nonlinear, head, mask — identical structure for every task because validity of dims combinations is task-independent). The transformation weights are the only place cross-task "program memory" can live in this substrate without redesigning it.
- **Hypothesis:** transformation weights learned while solving tasks contain task-general structure, so initializing a NEW task's transformation weights from the element-wise average of donor tasks' trained weights (latents always fresh) reaches a stable correct solution in materially fewer steps than random init.
- **Design (leave-one-out over the 11 H8-solved tasks):**
  - *Phase 1 (cold + donors):* retrain each of the 11 solved tasks from scratch, 2000 steps, seeds/protocol exactly as H8, now recording the per-step top-2 solution-pick history (the existing Logger already tracks it) and saving final transformation weights. Phase 1 IS the cold arm AND the donor pool; its pass@2 must reproduce H8 (determinism check).
  - *Phase 2 (warm, LOO):* for each task T of the 11, build the average-weight "soup" from the OTHER 10 donors, warm-start T's transformation weights from it (fresh latents), train 2000 steps, record the same curves.
- **Primary metric:** steps-to-stable-solve = earliest step s such that the ground-truth solution is among the logger's top-2 picks at s and at every later step; unsolved = censored at 2000. Compare warm vs cold per task; headline = median ratio.
- **Decision rule (pre-committed):** ACCEPT H9 if median steps-to-stable-solve (warm) <= 0.5x (cold) — the same >= 2x amortization bar H5 used — AND warm retains >= 10/11 solves. KILL if warm median shows no speedup (>= 1.0x cold) OR retention <= 8/11 (interference). Else inconclusive.
- **Validity gate (not decision-bearing):** same-task warm restart (task warm-started from its OWN phase-1 weights) on 2 tasks must re-solve within ~200 steps; if it fails, the transfer mechanics are broken and the run is void, not evidence.
- **Exploratory (not decision-bearing):** warm-start 5 H8-UNSOLVED tasks from the full 11-donor soup at 2000 steps; any new solves reported as a coverage bonus signal.
- **Cost gate:** projected ~32 cloud jobs x ~52 min ~= 28 GPU-h ~= $55 list on L40S; owner go/no-go BEFORE launch (local 3070 Ti fallback ~58 h unattended). CompressARC source stays unmodified; all transfer logic lives in the VNR harness.
- **Interpretation guardrails (recorded in advance):** an accept means amortization exists even via the crudest memory (weight soup) — it sets a floor, not a ceiling, and motivates richer addressable memory designs. A kill means per-task weights are task-specialized at this scale and memory must live elsewhere (e.g., shared meta-trained backbone, latent-space library) — it does NOT kill the memory thesis itself, only this mechanism.

### H9 outcome (2026-06-11): KILL-CRITERION FIRED (both conditions)
- **Run:** RunPod 6x A40 pod, all 29 jobs, 263 min wall, ~$11.60. Compute pivot from Modal (owner: billing unusable) and from local (owner: not feasible long-term) recorded in checklist; both arms ran on identical hardware, so the comparison is clean.
- **Validity gate PASSED:** same-task warm restarts re-solved in 61 and 151 steps (bar: ~200). The transfer machinery works; the result is meaningful, not an artifact.
- **Decision inputs:** median warm/cold steps-to-stable-solve ratio = **1.222** (kill threshold: >= 1.0 — no speedup) and retention **8/11** (kill threshold: <= 8 — interference). Probes: **0/5** new solves from the full soup.
- **The heterogeneity is the real finding.** Warm LOST two tasks cold solves easily (`00576224`: 222 -> never; `d2acf2cb`: 517 -> never) but produced large wins on others: `6df30ad6` 0.31x (541 -> 168), `903d1b4a` 0.57x (480 -> 274), and `cd3c21df` — which COLD FAILED on this hardware — solved warm at step 749. Transferable cross-task structure EXISTS; averaging everything into one soup both transmits it and corrupts task-idiosyncratic weights.
- Notable: the soup's biggest wins (`6df30ad6`, `cd3c21df`) are exactly the tasks the symbolic object-substrate could express in Stage 3b — shared structure appears to cluster by task family.
- **Cross-hardware note:** A40 colds reproduced only 9/11 of the L40S (H8) solves (`15663ba9`, `cd3c21df` failed cold) — per-task trajectories are hardware-sensitive; recorded as a protocol caveat for all future cross-run comparisons.
- **Per the pre-registered guardrail:** this kills the WEIGHT-SOUP mechanism, not the memory thesis. The win/loss split argues for ADDRESSABLE memory — retrieve the right donor for the task rather than average all donors — which is the natural H10 (and is, notably, the von Neumann point: a memory you address, not a memory you smear).
