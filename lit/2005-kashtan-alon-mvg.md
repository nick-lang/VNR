# Spontaneous Evolution of Modularity and Network Motifs (modularly varying goals)

- **Authors / year:** Kashtan & Alon — PNAS 2005
- **Link:** https://www.pnas.org/doi/10.1073/pnas.0503610102
- **Pillar:** 6 (origins of modularity/generalization), 5
- **Date read:** 2026-08-19 (surfaced by the owner's teatime discovery dossier;
  claim checked against established knowledge of the paper — primary source not
  re-read line-by-line today)

## Problem
Why do evolved/learned systems become modular at all? Under a FIXED goal,
evolution (and by analogy, optimization) does not produce modularity — even
initially-modular solutions decay into non-modular ones that are marginally
fitter.

## Mechanism
**Modularly varying goals (MVG):** switch the target goal over time among
goals that SHARE a common set of subgoals (e.g., alternating logic functions
built from the same subfunctions). Under MVG, modular structure matching the
shared subgoals emerges rapidly and persists; the systems also adapt to each
new goal much faster (the modules are rewired, not relearned) and generalize
to never-seen goals composed of the same subgoals.

## Evidence
Simulated evolution of logic circuits and neural networks: fixed goal ->
non-modular; randomly varying goals -> non-modular; MVG -> modular, with
orders-of-magnitude faster adaptation to goal switches. Lineage continues in
Clune/Mouret/Lipson 2013 (connection costs) and continual-learning work.

## Relevance
- Limitation(s) addressed: L3/L4 — where reusable structure comes from.
- **Retroactive frame for our H14 delta-orthogonality:** 9-11 arbitrary ARC
  dev tasks are (at best) RANDOMLY varying goals — exactly the regime where
  MVG theory predicts NO shared/modular structure forms. Orthogonal per-task
  deltas are the MVG null case observed in the wild. The negative stops being
  a mystery and becomes a curriculum prediction.
- **Forward design for H18 (library growth):** composability becomes a
  property of the CURRICULUM, not just the architecture. Pre-registerable
  arm: train the H17 decoder (or any library learner) on (a) fixed, (b)
  shuffled, (c) modularly-varying task streams (families sharing subgoals —
  re-arc generators make this schedulable); measure abstraction reuse and
  transfer to held-out compositions. Converges with the prospective-
  compression note (humans track non-stationary task structure).
- How it could be wrong / limits: evidence is from small evolved circuits;
  transfer to gradient-trained decoders is a hypothesis, not a result; ARC's
  real eval distribution may not be modularly structured, in which case MVG
  training helps in-family transfer but not the benchmark.
