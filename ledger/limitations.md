# Limitations ledger

The precise, evidence-backed statement of what is broken in the current paradigm. This is the Phase 1 deliverable; Phase 0 seeds the skeleton and the grounding evidence already gathered. Each item: claim -> evidence -> candidate cause -> which hypothesis (in `hypotheses.md`) attacks it.

> Status: SEED (skeleton + initial evidence). To be completed in Phase 1 with full per-paper citations from `lit/`.

## L1 — Bounded context => no persistent episodic memory
- **Claim:** Memory is conflated with the context window; there is no separate, persistent, addressable store.
- **Evidence (to expand):** SSM/long-context characterization shows recall degrades with distance; Sessa explicitly targets "exponential forgetting" of distant evidence.
- **Candidate cause:** computation and memory are fused in the same activations/weights (no von Neumann separation).
- **Attacked by:** H1.

## L2 — Next-token likelihood != correctness / reasoning
- **Claim:** Optimizing token likelihood does not optimize for correct, compressed, or verifiable reasoning.
- **Evidence (to expand):** JEPA/EBM motivation (predict in latent space); CompressARC reaches non-trivial ARC scores via MDL with zero pretraining.
- **Candidate cause:** the training objective rewards plausible continuations, not minimal correct programs.
- **Attacked by:** H2.

## L3 — Compositional / OOD collapse
- **Claim:** All paradigms drop ~2-3x from ARC-AGI-1 to ARC-AGI-2; humans stay near-perfect.
- **Evidence:** Living Survey of 82 approaches (program synthesis, neurosymbolic, neural) reports consistent 2-3x degradation; ARC-AGI-2 top open score ~24%, ARC-AGI-3 ~13%.
- **Candidate cause:** lack of true compositional generalization / reusable abstraction.
- **Attacked by:** H4.

## L4 — Sample inefficiency (reasoning is "knowledge-bound")
- **Claim:** Strong ARC scores currently require enormous synthetic data.
- **Evidence:** ARC Prize 2025 winners needed hundreds of thousands of synthetic examples to reach ~24% on ARC-AGI-2.
- **Candidate cause:** generalization is achieved by coverage, not by efficient skill acquisition.
- **Attacked by:** H3 (test-time learning), H2 (objective).

## L5 — Cost / test-time-compute economics
- **Claim:** Frontier-model accuracy is expensive; cost, not just accuracy, is the gating factor for access.
- **Evidence:** cost fell ~390x in a year but high-accuracy frontier runs remain costly; Kaggle-constrained 660M-8B models reach competitive results at ~$0.20/task.
- **Candidate cause:** reliance on scale and brute-force test-time compute rather than efficient architecture.
- **Attacked by:** all hypotheses (cost is a first-class metric in `results.md`).
