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

## H10 — Addressable (retrieval-gated) weight memory amortizes where the soup failed (Stage 5b)

### H10 pre-registration (2026-06-11, before running)
- **Hypothesis:** for a new task, a cheap content-based lookup over the donor library — train K=100 steps from each candidate donor's weights (fresh latents) and score by mean loss over the last 20 probe steps — selects a SINGLE donor whose weights warm-start the task to a stable solve in materially fewer training steps than cold init, without the soup's interference losses. (MDL reading: "which stored program best compresses this task?")
- **Design (LOO over the same 11 tasks, same A40 hardware so H9's phase-1 cold baselines are reused unchanged — no recompute of the cold arm):**
  - `sel_T`: probe the 10 other donors (100 steps each, identical RNG seed before every candidate so probes differ ONLY by donor weights); bank scores + selected donor.
  - `ret_T`: warm-start from the selected donor, 2000 steps, same metrics as H9.
- **Primary decision rule (pre-committed, identical numeric bar to H9):** ACCEPT if median ratio (ret_T training steps-to-stable-solve / cold steps-to-stable-solve) <= 0.5 AND retention >= 10/11. KILL if median >= 1.0 OR retention <= 8/11. Else inconclusive.
- **Honest-accounting caveat (recorded in advance):** the probe itself costs 10 x 100 = 1000 steps per task; the full-cost ratio ((probe + train) / cold) is reported alongside but is NOT decision-bearing. H10 tests whether ADDRESSING works — whether the right donor exists and is findable by content. Making the lookup cheap (an index instead of trial training) is a separate, later engineering stage and only worth building if addressing works at all.
- **Validity gate (not decision-bearing):** self-retrieval check on 2 tasks — probing the FULL 11-donor pool (own donor included) must rank the task's own donor #1. If lookup can't even find the task's own program, the probe signal is too weak and the run is void.
- **Secondary readouts:** per-task comparison vs H9's soup arm (does selection fix the 2 interference losses? keep the 3 soup wins?); the full 11x10 probe-score matrix (does retrieval cluster by task family, e.g. the 6df30ad6/cd3c21df pair?).
- **Cost gate:** ~11 GPU-h on 6x A40 ~= ~2 h wall ~= **~$5-6** (+~$5 donor retrain if the network volume was lost with the pod). Owner go/no-go on pod redeploy before spend.

### H10 outcome (2026-06-11): KILL-CRITERION FIRED (both conditions) — and it closes the whole-blob memory branch
- **Run:** RunPod 5x A40 (owner could deploy 5, not 6; same hardware class as H9 colds, so the comparison holds), all 24 jobs, 175 min wall, ~$6.50. Network volume survived the redeploy: all 11 donors + 11 banked cold baselines reused, no recompute.
- **Validity gate PASSED:** both self-retrieval checks ranked the task's own donor #1 of 11 with clear margin (`00576224`: 1210 vs 1336 runner-up; `8597cfd7`: 1338 vs 1616). The probe signal is real — the lookup CAN find a task's own program. The kill is about memory CONTENT, not a broken probe.
- **Decision inputs:** median ret/cold steps-to-stable-solve ratio = **1.396** (kill: >= 1.0); retention **7/11** (kill: <= 8/11). Both fired — worse than the soup on both numbers (H9: 1.222, 8/11). Median full-cost ratio incl. probe: 5.8x (reported per pre-registration, not decision-bearing).
- **The sharpest finding: zero wins.** Not one of the 11 tasks trained faster from its best-fitting foreign donor than from random init — every solved task's ratio > 1.0 (1.06-1.60), one catastrophic 25.8x slowdown (`45737921`: cold 62 -> warm 1599), and two tasks cold solves easily never solved warm (`6df30ad6` 541 -> never, `d2acf2cb` 517 -> never). (`15663ba9`/`cd3c21df` failed in BOTH arms — the known A40 cross-hardware caveat, censored 1.0, not evidence either way.)
- **Retrieval collapsed onto "universal donors," not task families:** `d2acf2cb` was selected by 6/11 tasks, `45737921` by 3, `cd3c21df` by 2. The pre-registered family-clustering probe failed: `6df30ad6` did NOT select its Stage-3b family pair `cd3c21df`. The trial-loss probe measures "generically adaptable weights," not task similarity — among foreign donors there is no task-similarity signal worth finding.
- **Combined H9+H10 reading (the branch-closing inference):** H9's soup produced real wins (0.31x/0.57x, one cold-failed task unlocked); H10's best-single-donor produced none and MORE interference. So the soup's transferable signal was a property of AVERAGING (regularization / structure distributed across donors), not of any one donor's content. Selection was the natural fix for the soup's corruption; it fixed nothing. Conclusion: a whole trained model is the wrong unit of memory — donor weights at blob granularity are task-specialized monoliths, and no addressing scheme over monoliths can rescue that. The von Neumann analogy sharpens: we built an addressable memory and the addressing worked; what's stored in the cells is not reusable program, it's baked-in data.
- **Memory-ladder consequences (gates evaluated):** H11 (learned addressing) — gate was "H10 accepts": CLOSED, nothing worth addressing at blob level. H12 (links/pruning at 400-donor blob scale) — CLOSED for the same reason. H13/Stage 5e's gate as written ("blob-level addressing must work") fails on the retrieval half — but its MOTIVATION is exactly what survived: memory must hold PARTS (sub-task-granularity structure: modules, latents, or symbolic macros), because whole-blob reuse is now killed twice by two independent mechanisms. Decomposition is no longer a refinement of the ladder; it is the only remaining form a weight-space memory could take.
- **Per the owner's standing direction** (don't over-optimize memory before the rest of the architecture validates): the memory track PAUSES here with a clean negative result, and the program returns to the remaining architecture slots (TTT-as-MDL, proposer redefinition, integrated loop). The Stage 1 symbolic library result remains the only accepted concept-granularity memory in the program.

## H14 — Jointly trained shared backbone amortizes per-task training (Stage 5f)

### Protocol decision feeding into H14 (2026-06-11, from banked data, $0)
- **Iteration budget cut to 1000 steps.** Mining the banked Stage-5 cold runs (`budget_analysis.py`): all 9 A40-solvable tasks reached stable solve by step 541 (median 222); a 1000-step budget retains 9/9 with ~2x headroom at HALF the per-task cost. Adopted for all experimental runs going forward; 2000 steps remains the protocol for benchmark-grade pass@2 claims (H8 comparability).

### H14 pre-registration (2026-06-11, before running)
- **Why this can work where H9/H10 died (recorded in advance):** independently trained networks land in different loss basins (permutation symmetry — many weight orderings compute the same function), so element-wise averaging (H9) or transplanting whole donors (H10) starts new training from no-man's land between basins. JOINT training — one set of shared transformation weights serving many tasks simultaneously, per-task latents kept separate — forces a single basin shaped by all training tasks at once. The shared structure is created during training, not assembled post hoc. This is the "shared meta-trained backbone" escape route pre-named in H9's interpretation guardrail, and it is amortization infrastructure, NOT a reopening of the memory ladder (links/index/pruning stay paused per owner direction).
- **Hypothesis:** warm-starting a held-out task's transformation weights from a backbone jointly trained on 6 other tasks reaches a stable solve in materially fewer training steps than cold init.
- **Design (3-fold rotation over the 9 A40-cold-solvable tasks; cold arm = H9's banked A40 baselines, no recompute):**
  - `fold_F` (3 folds of 3 tasks): joint-train a backbone on the 6 tasks NOT in fold F — one CompressARC model per task aliasing the SAME transformation-weight tensors, per-task latents/optimizer state, round-robin one step per task, 1000 cycles (= 6000 shared-weight updates); save backbone.
  - `jret_T`: warm-start each held-out task T from its fold's backbone (fresh latents), train 1000 steps (the new iteration budget), same steps-to-stable-solve metric. Censoring at 1000 is conservative AGAINST acceptance (all colds stabilized <= 541).
- **Primary decision rule (pre-committed, same numeric bar rescaled to 9 tasks):** ACCEPT if median ratio (jret steps-to-stable-solve / cold steps-to-stable-solve) <= 0.5 AND retention >= 8/9. KILL if median >= 1.0 OR retention <= 7/9. Else inconclusive.
- **Validity gate (not decision-bearing):** each backbone, warm-starting one of its OWN training tasks, must re-solve within ~200 steps (H9's same-task bar). If joint training can't even re-solve tasks it trained on, the mechanism is broken and the run is void.
- **Exploratory (not decision-bearing):** train one backbone on all 9 tasks; warm-start 3 H8-unsolved tasks from it; any new solve reported as a coverage signal.
- **Payoff if accepted:** all later stages' per-task runs start from the backbone, compounding with the 1000-step budget — projected >= 4x cheaper iteration loop for Stages 6/2/7.
- **Cost gate:** 3 joint trainings (~2h each, serial per GPU) + 1 exploratory backbone + 9 jret + 3 validity + 3 probe runs at 1000 steps (~20 min each) ~= ~11 GPU-h ~= ~2.5h wall on 5x A40 ~= **~$6**. Owner go/no-go on pod redeploy before spend.

### H14 amendments from the 2026-07-06 literature pass + hardware pivot (pre-run, decision rule unchanged)
- **Hardware rebase:** A40 pods are gone; reference hardware is now the owner's local RTX 5090 (32 GB). The 9 cold baselines must be RE-RUN on the 5090 before any warm arm (pre-registered cross-hardware caveat: per-task trajectories are hardware-sensitive). Cost gate becomes $0 (local).
- **Expectation calibration (recorded in advance):** fair meta-learning comparisons (Miranda et al. 2023; see `lit/2023-pretrain-vs-meta.md`) show plain multi-task initialization helps least when task diversity is high — and ARC is maximally diverse. H14's round-robin joint training is multi-task, not bi-level meta-learning. Therefore, **pre-registered escalation:** if H14 lands marginal or kill, run **H14b — Reptile-style outer update** (inner steps per task, outer interpolation toward inner result) on the same harness before abandoning the shared-backbone route. H14b inherits H14's numeric bar; only the update rule changes.
- **New secondary readout (not decision-bearing):** after joint training, save each task's fine-tuned delta vs the backbone and report pairwise cosine similarities of the deltas. The merging literature (task-vector line; see `lit/2025-llm-merging-study.md`) predicts that deltas from a shared base are the composable unit of weight-space memory; this readout measures whether that geometry exists in our substrate, feeding the deferred Stage 5e design.

### H14 outcome (2026-07-07): VOID per the pre-registered rule — and the void is itself the finding
- **Run:** local RTX 5090, 4-way parallel workers, 30/30 jobs, ~10.4 h wall, $0. Protocol deviations recorded: torch 2.11.0+cu128 (pinned 2.5.1 predates Blackwell); CompressARC re-cloned at upstream `83a2221`.
- **Hardware rebase clean:** 5090 colds solved 9/11 — the SAME 9 tasks as the A40 colds (`15663ba9`, `cd3c21df` failed on both), so cross-hardware solvability is stable at 1000 steps.
- **Validity gate FAILED 3/3 — formally VOID:** each backbone, warm-starting one of its OWN training tasks (fresh latents), failed to re-solve within 600 steps (bar ~200; all three `steps_to_stable_solve = null`). This is NOT plumbing: the transfer round-trip and aliasing smokes passed, H9's same-task-restart gate previously validated the load path, and `solved_during_joint` shows tasks solving DURING joint training (fold_1: 4/6). The failure isolates the mechanism itself: **the shared transformation weights, without their co-adapted per-task latents, do not encode the solutions** — knowledge in this substrate lives in the latent/weight co-adaptation.
- **Descriptive numbers (reported per protocol; not decision-bearing under a void):** median jret/cold ratio 3.436 — warm-starting from the backbone was SLOWER than random init on all 9 tasks; retention 6/9; exploratory probes 0/3. Joint-basin warm-starting actively harms, worse than the soup (1.222) and retrieval (1.396).
- **Delta-geometry readout (the informative surprise):** per-task adaptation deltas from the same fold backbone have pairwise cosine ~= 0 (median 0.0067, min -0.014, max 0.062) with near-identical norms (~114-121). Even from a forced shared basin, task adaptations are mutually orthogonal — there is no shared direction across these 9 tasks for any warm-start/averaging scheme to exploit. (Merging-literature note: orthogonal task vectors are the GOOD case for interference-free multi-task merging, but they are the NULL case for cross-task transfer/amortization.)
- **H14b gate evaluation:** the pre-registered escalation trigger was "H14 marginal or kill." H14 is VOID, so H14b does NOT auto-fire. The delta orthogonality also undercuts H14b's premise (a Reptile outer step searches for a shared adaptation direction; the readout says there is none among these tasks at this scale).
- **Combined weight-space memory record (H9, H10, H14): three independent negatives** — post-hoc averaging corrupts, addressed retrieval finds nothing reusable, and joint training stores knowledge somewhere weights alone cannot carry. The remaining weight-space option (Stage 5e decomposition) and the substrate-external options (symbolic library — Stage 1's accept, Pang's external validation; concept memory — ArcMemo) are where the memory thesis still lives.
- **Owner decision requested:** run H14b anyway (~1 night, $0, pre-registration formality) vs close the weight-space amortization track and return to Stage 6 (TTT-as-MDL) / Stage 2 (proposer). Recommendation recorded: close — three mechanism-level negatives plus orthogonal deltas make H14b's prior very low, and the owner's standing direction is not to over-invest in memory before the rest of the architecture validates.
- **Owner decision (2026-07-07): CLOSE the weight-space amortization track.** H14b will not run (trigger never fired; premise undercut by delta orthogonality). Stage 5e stays deferred as the only surviving weight-space form. Program returns to Stage 6, redefined below as H15.

## H15 — Restart diversity + label-free MDL selection lifts coverage at matched compute (Stage 6, TTT-as-MDL redefined for the neural substrate)

### H15 pre-registration (2026-07-07, before running)
- **Why this redefinition:** H3's original form (adapt a pretrained core per task) presupposed a trained proposer; in the CompressARC substrate ALL training is already test-time, so the live H3 question becomes how to SPEND test-time compute. Mechanistic prior from the lit pass (`lit/2026-trm-followups.md`): deterministic refinement converges into one attractor per seed and stalls (PTRM's finding on TRM; CompressARC is likewise deterministic per seed, and our own cross-hardware record — A40 vs L40S solving different task subsets — shows basin selection is seed/numerics-sensitive). The label-free escape is restart diversity with MDL selection: the description length IS the objective, so "which run compressed better" needs no labels.
- **Hypothesis:** on tasks unsolved by the single-seed protocol, two independent 1000-step runs from different seeds with MDL selection solve more tasks than one 2000-step run, at identical total compute.
- **Design (all on the 5090, torch 2.11+cu128, same protocol as H14's runs):**
  - Benchmark: the **39 H8-unsolved tasks** of the committed 50-task dev split (coverage is the question; the 11 solved tasks are the control set elsewhere).
  - **Arm A (control):** 1 run x 2000 steps, seed 0 — the H8 protocol, rebased to this hardware.
  - **Arm B (treatment):** 2 runs x 1000 steps, seeds 1 and 2. Selection: the run with the lower mean training loss over its final 50 steps (label-free MDL proxy; mirrors H10's probe scoring). Arm B's answer = the selected run's top-2 picks (pass@2).
  - **Seed-sensitivity readout (not decision-bearing):** the 9 5090-cold-solvable tasks re-run at seed 1, 1000 steps — measures how fragile the existing solves are to seed choice (protocol-stability data).
- **Primary metric:** tasks solved (pass@2) per arm, out of 39.
- **Decision rule (pre-committed):** ACCEPT H15 if arm B solves >= arm A + 2 tasks AND arm B >= 2. KILL if arm B <= arm A. INCONCLUSIVE otherwise (e.g., B = A + 1).
- **Secondary readouts:** (a) selection accuracy — among tasks where exactly one B run solves, how often the MDL selector picks the solver (validates label-free selection independent of the coverage outcome); (b) union-of-B-runs oracle coverage — the ceiling a better selector could reach; (c) per-task s/step (cost accounting).
- **Cost gate:** ~165k training steps ~= ~34 h wall at the measured 4-way throughput (~1.36 steps/s aggregate), $0, resumable at job granularity (owner can pause/resume freely; pausing only delays the verdict).
- **Interpretation guardrails (recorded in advance):** an ACCEPT means test-time compute is better spent on basin diversity than on longer convergence — a capability-per-dollar result that composes with any future substrate improvement, and it makes a K>2 scaling study the natural follow-up. A KILL with high union-oracle coverage indicts the SELECTOR (MDL tail-loss is not basin quality), not diversity itself — that redirects to better label-free selection, not away from restarts. A KILL with near-zero union coverage says unsolved dev tasks are beyond this substrate at this budget regardless of seed — a substrate-coverage wall, pointing back to perception/DSL work (Stage 2/3 lineage), not compute allocation.

### H15 outcome (2026-07-20): KILL per the pre-registered rule — restarts don't beat convergence, and the seed-stochasticity finding matters more than the verdict
- **Run:** local RTX 5090, 4-way parallel workers, 126/126 jobs, 169.3 GPU-h summed job time (~42 h wall-equivalent at 4-way), $0. Spread over 2026-07-07 -> 07-20 across owner pauses, one IDE-session death, and one machine reboot; banked/resumable queue handled all three with only in-flight jobs redone.
- **Primary result:** arm A (1x2000, seed 0) solved **3/39** (`981571dc`, `be03b35f`, `e66aafb8`); arm B (2x1000, seeds 1-2, tail-loss selection) solved **2/39** (`73182012`, `e66aafb8`). B <= A -> **KILL**.
- **Guardrail application:** union-of-B oracle = 3 (`73182012`, `be03b35f`, `e66aafb8`) — equal to A, so even a PERFECT selector only ties longer convergence. Both pre-registered failure readings apply at once: (a) the selector is bad — accuracy 1/2, and in 3 of 4 solve cases the solving run had the HIGHER tail loss (e.g. `be03b35f`: solver s2 tail 127.9 vs non-solver s1 87.1; `73182012`: unsolved arm A had the lowest tail loss of its trio). Tail training loss ANTI-correlates with solving here, echoing H10's finding that loss-based scoring carries no task-relevant signal. (b) Diversity at halved length adds nothing over convergence at matched compute — no compute-allocation free lunch.
- **The informative surprise — coverage is a stochastic draw, not a set:** arm A IS the H8 protocol (2000 steps, seed 0), yet it solved 3 tasks that identical-protocol H8-on-L40S did not; across all 5 runs/task this experiment solved **4 previously-unsolved dev tasks** (union 11 -> 15/50 with pure re-rolls); meanwhile the seed-1 check LOST 2 of the 9 banked solves (`00576224`, `6df30ad6` — the latter a task BOTH H9 soup and the symbolic substrate once solved). Per-seed churn is roughly +-20-30% of the solve set in both directions. Single-seed pass@2 numbers (including our own H8 "11/50") therefore overstate protocol stability; the honest substrate metric going forward is seed-marginalized solve probability, and any coverage claim must state its seed budget.
- **Capability-per-dollar reading:** re-rolls DO buy real coverage (pass@k over seeds grows ~11 -> 15), but ARC's pass@2 submission budget makes that unusable without a working label-free selector — and the MDL tail-loss selector is now refuted in this substrate. Better selection (train-pair consistency checks, ensembling/voting across seeds' top picks) is the surviving lever, but it is a new design, not a tweak of H15.
- **Stage 6 closes.** Remaining live slots: Stage 2 (proposer redefinition) and the substrate-external memory routes (symbolic library, concept memory). The seed-stochasticity fact feeds both: any proposer evaluation must marginalize over seeds, and voting-across-seeds is a candidate selection mechanism for a future H16.

## H19 — Modularly varying goals grow a more transferable abstraction library (Stage 9 pilot, symbolic substrate)

### H19 pre-registration (2026-08-19, before the full run; smoke only so far)

- **Numbering note:** H16 (voting selector) remains a deferred candidate; H17/H18 (amortized interpreter / library growth) are proposed in `experiments/notebook/2026-08-18-strategic-direction-h17.md` and await owner bars. H19 is the CPU-only pilot of the MVG design input from the 2026-08-19 teatime dossier (`lit/2005-kashtan-alon-mvg.md`), runnable without the H17 build.
- **Hypothesis:** a task stream whose goals vary MODULARLY (epoch-level concept pairs that switch while sharing subgoals) grows an abstraction library that transfers better to never-seen concept combinations than THE SAME TASKS presented in random order, at identical compute. (Kashtan & Alon 2005 transferred to library learning; falsifiable because arm R is an exact permutation control of arm M.)
- **Design (`experiments/poc-vnr-s9-mvg/h19_runner.py`):** 6 Stage-1 concepts; epoch goals = concept pairs on a shared-subgoal ring; 12 epochs x 10 tasks. Arm M = ring order (each epoch pair shares a concept with the next); arm R = same 120 tasks shuffled; arm F = fixed pair (K&A control). Library mechanics unify both dossier imports: persistent cap-12 store, per-epoch BPE proposals (<=4, min_count 2) from that epoch's solved programs, pruning of macros unused for 2 consecutive epochs (Minton-style utility forgetting). Transfer = 30 tasks from the 6 distance-2 pairs (combinations never used as an epoch goal), solved with each arm's FINAL library at the same 50k budget; unsolved censored at budget. 5 stream seeds; raw-primitives baseline reported.
- **Primary decision rule (pre-committed):** per-seed ratio = median transfer nodes-to-solution (M) / (R). ACCEPT if ratio <= 0.75 in >= 4/5 seeds AND pooled M transfer solves >= R. KILL if pooled median ratio >= 1.0. INCONCLUSIVE otherwise.
- **Secondary readouts (not decision-bearing):** macro-concept alignment rate per arm; library-log dynamics (what gets proposed/pruned under each stream); per-epoch online adaptation curves; per-macro utility accounting (uses; feeds H18 curation design); F-arm comparisons.
- **Known threats (recorded in advance):** (1) BPE pair counts are order-invariant, so any curriculum effect must flow through window locality + capacity/retention pressure — a clean null is informative about the MECHANISM (MVG needs selection pressure to bite), not a harness bug; (2) BFS returns shortest programs, which may be behaviorally-equivalent alternates of the generative concepts, so alignment is scored against concept sequences but treated as secondary; (3) synthetic-only, same caveat as H5 — an accept licenses an MVG arm in H18's neural pre-registration, not a real-ARC claim.
- **Cost gate:** CPU-only, ~minutes per seed; $0; launched after the E1-B GPU queue drains (CompressARC jobs are CPU-overhead-sensitive).

### H19 outcome (2026-08-19): KILL per the pre-registered rule — and the mechanism inverts the naive reading
- **Run:** 5 seeds x 3 arms x (120 stream + 30 transfer tasks), CPU-only, ~3 min total, $0. All arms solved 150/150 transfer tasks (task space does not bind on solve rate; discrimination is nodes-to-solution, as designed).
- **Decision inputs:** M/R median-transfer-nodes ratio >= 1.14 in ALL 5 seeds (1.14, 9.06, 2.04, 2.09, 1.14; pooled 1.25; accept needed <= 0.75 in >= 4/5). KILL.
- **The shuffled arm won, and the pre-registered threat fired in an unexpected direction:** it was not BPE order-invariance that neutralized the curriculum — it was the RETENTION POLICY that punished it. Under modular switching, the 2-epoch utility-forgetting prunes macros whose concepts return 5 epochs later; under random order every useful macro gets occasional use and survives. The two dossier imports (MVG curriculum, Minton forgetting) interact destructively when the forgetting horizon is shorter than the goal-return period — which is itself a Minton-literature lesson (utility must be measured on the WORKLOAD, and a modular workload has long return periods).
- **Sanity check preserved:** libraries beat raw primitives ~2.6x on transfer nodes (median 113 vs 294), consistent with H5's 3.3x.
- **Consequences:** (a) H19 as registered is closed; (b) any H18 MVG arm must pre-register retention horizon >= goal-return period (or utility-weighted rather than binary forgetting) — the pilot's kill is evidence about POLICY-CURRICULUM COUPLING, not yet about MVG in an order-sensitive (SGD) learner, where plasticity dynamics differ from corpus statistics; (c) the K&A import survives as theory but has lost its cheap-validation support; its prior for H18 is now mixed and the write-up makes no MVG claim.
