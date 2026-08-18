# 2026-08-18 — Literature pass for the write-up (post-H15)

- **PoC:** none (reading, $0)
- **Hypothesis:** informs the Stage 8 write-up framing and the design of a future H16 (label-free selection)
- **Hardware:** n/a

## Setup

Owner asked (a) whether new literature since the 2026-07-06 pass changes the program's standing, and (b) how to make the write-up as strong as possible, including any cheap strengthening experiments. Web pass on: test-time-compute allocation, label-free selection/voting, ARC field updates, library-learning cog-sci. Six notes filed in `lit/` (see `index.md`); two candidates rejected.

## Findings

1. **H15 tested the wrong diversity axis — input augmentation, not seed, is the axis that wins at matched compute.** TTA-at-matched-compute (arXiv 2608.09351): semantic input augmentation + voting beats self-consistency (output/seed diversity) on 5/6 benchmarks at ~1.8x accuracy per dollar. Our arm B varied init seeds; the literature's winning axis is augmented INPUTS voted back through inverse transforms. In our substrate the augmentations are exact (D8 x color permutations), and AIRV (2506.14276, already in `lit/`) is the same recipe from the ARC side. H16's design should be augmentation-voting, not seed-voting.
2. **The seed-stochasticity finding now has a formalism.** Certified Self-Consistency (arXiv 2510.17472): majority voting = mode estimation of an answer distribution, with finite-sample certificates and an adaptive stopping rule (MMC). "Coverage is a stochastic draw; report seed-marginalized solve probability" is exactly a mode-estimation claim; citing this turns our H15 headline from an observation into statistics. Vote-margin also replaces tail-loss (refuted, H10+H15) as the candidate label-free confidence signal.
3. **Selection should eliminate on disagreement, not score.** Test-Time Transduction (arXiv 2509.17393, NeurIPS 2025): candidates form a finite hypothesis class over their OUTPUTS; strategically chosen inputs where candidates disagree eliminate hypotheses. Both of our dead selectors (H10 probe-loss, H15 tail-loss) were scorers. Voting/agreement over augmentations is the degenerate label-free form of elimination.
4. **ARC-AGI-3 formalizes capability-per-action (RHAE) and is where the memory thesis becomes load-bearing.** Frontier <1% vs humans 100%; scoring is min(1,h/a)^2 — an efficiency metric, not accuracy. Static-grid tooling does not transfer, so this is a season-2 decision, not a bolt-on.
5. **Cog-sci anchor with a self-critique:** Prospective Compression (arXiv 2605.09985): humans select abstractions by anticipated FUTURE compression; retrospective compressors (DreamCoder-style, like our Stage-1 BPE) fail to capture the behavior. Framing citation for the library thesis + a design note for any Stage 5e reopening.
6. **TRM-substrate datapoint:** TRM TTA competition note (arXiv 2511.02886): 7M TRM, full-FT TTA, 6.67% semi-private ARC-2 (10% public — the drop is an overfitting caution for all public-set claims, including ours).

**Rejected candidates:** arXiv 2508.16063 (Synthesizing DSLs for Few-Shot Learning) — purely theoretical decidability results via tree automata, no algorithm, no empirics; does not help the H7 coverage wall. ICLR 2026 TTU workshop "Majority Voting for Code Generation" — inaccessible (OpenReview bot-block); the voting-theory ground is covered by Certified Self-Consistency.

## Decision

- The write-up's three claims all got stronger: (1) weight-space negatives stand unchallenged (nothing new contradicts them); (2) seed-stochasticity gains a citable formalism (mode estimation); (3) the selector question gains a literature-backed next design (augmentation-voting / elimination) that turns the paper's ending from "we killed things" into "and here is the pre-registered live hypothesis."
- Strengthening experiments (owner go/no-go, all local/$0): E1 selector bake-off on BANKED runs (retrospective, no new GPU time); E2 seed-budget curve (pass@k over seeds with CIs on a task subset); E3 pre-registered H16 = augmentation-voting (D8 x color) at matched compute vs convergence. E1 before any new compute.
- Write-up target: ARC Prize paper track / workshop; negative-results + methodology framing.
