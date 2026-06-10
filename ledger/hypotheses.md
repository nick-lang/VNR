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
