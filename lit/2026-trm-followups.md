# TRM follow-ups: TRM-Planner, Probabilistic TRM, attractor-landscape mechanistics

- **Authors / year:** TRM-Planner (ACL Findings 2026); PTRM (Sghaier, Parviz, Jolicoeur-Martineau, arXiv 2605.19943); mechanistic analysis (OpenReview kKps9W1K7n)
- **Link:** https://aclanthology.org/2026.findings-acl.1350/ ; https://arxiv.org/html/2605.19943
- **Pillar:** 4 / 1 (tiny recursive reasoning)
- **Date read:** 2026-07-06

## Problem
TRM (7M params, 45% ARC-AGI-1) is the strongest tiny-model line; what has moved since?

## Mechanism
- **TRM-Planner:** teacher-cache distillation — unroll a frozen TRM offline, cache good refinement targets, train a student with a distillation loss. ARC-1 pass@2 43.1 -> 48.1, ARC-2 6.7 -> 9.2, at unchanged inference cost.
- **PTRM:** test-time scaling by injecting Gaussian noise into the latent each recursion step, running K parallel rollouts, selecting by the existing Q-head. Sudoku-Extreme 87.4 -> 98.75; Pencil Puzzle Bench 62.6 -> 91.2 (~2x frontier LLM accuracy at <0.0001x cost). No retraining.
- **Mechanistics:** TRM recursion = adaptive search over an attractor landscape; failed runs stall in high-loss attractors; noise + restarts escape them.

## Evidence
See numbers above; all three converge on "deterministic refinement gets stuck; cheap stochastic exploration + a learned verifier/selector fixes it."

## Cost / compute
7M params; single consumer GPU. Fully reproducible locally on the 5090 — TRM's original "4 H100s for 3 days" barrier applies to full training, but PTRM-style inference interventions need only checkpoints.

## Relevance
- Limitation(s) addressed: L4, L5.
- The propose/verify slot of VNR gets a concrete, validated micro-mechanism: noise-perturbed parallel rollouts + learned selection head. Notably parallel to our own Stage-4 substrate: CompressARC also converges deterministically; a PTRM-style noise/restart wrapper is a cheap coverage lever worth a gated probe.
- The "frontier accuracy at ~1/10000 cost on a narrow domain" result is the strongest existing proof-of-concept for the program's clarified goal — tiny specialized recursive models CAN beat frontier cost-performance by orders of magnitude *within a domain*.
- How it could be wrong / limits: domain-specific; TRM still needs expensive supervised training on each task family; none of this addresses cross-task memory.
