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
