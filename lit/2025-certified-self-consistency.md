# Certified Self-Consistency: Statistical Guarantees and Test-Time Training for Reliable Reasoning

- **Authors / year:** 2025 (arXiv 2510.17472)
- **Link:** https://arxiv.org/abs/2510.17472
- **Pillar:** 5 (algorithms & information theory), 4
- **Date read:** 2026-08-18

## Problem
Self-consistency (majority voting over samples) improves reliability but with no statistical guarantees: how many samples certify that the empirical majority is the true mode of the answer distribution?

## Mechanism
Frames majority voting as MODE ESTIMATION of the terminal answer distribution; finite-sample concentration bounds give confidence >= 1-eps that the aggregated answer is the true mode. Martingale Majority Certificate (MMC): adaptive sequential stopping rule (leader / runner-up / others) that stops sampling as soon as the majority is certified. Also proves KL-regularized test-time training performs exponential tilting of the answer distribution toward its mode (raises SNR), with label-free SNR/entropy objectives.

## Evidence
Expected stopping time N ~ 2(p_lead+p_run)/(margin)^2 * log(1/eps). On MATH-500 (Qwen-Math-1.5B/7B, N up to 100): fewer samples needed after test-time training at equal majority-vote accuracy; SNR tracks problem difficulty without supervision.

## Cost / compute
Analysis + small open models; the certificates are substrate-agnostic arithmetic over vote counts.

## Relevance
- Limitation(s) addressed: L5; formal grounding for our H15 headline finding.
- **This is the missing formalism for "seed-marginalized solve probability."** Our claim that coverage is a stochastic draw (union 11->15/50, +-20-30% churn) is exactly "per-task answer distributions have modes with finite margins; single-seed pass@2 is a 1-sample mode estimate." Citing this upgrades the write-up's methodology claim from observation to statistics.
- Idea worth stealing: (1) MMC as the per-task stopping rule for any seed/augmentation-voting selector (spend seeds only until the vote certifies — capability-per-dollar native); (2) vote-margin as a labeled-free confidence signal to replace the refuted tail-loss selector.
- How it could be wrong / limits: guarantees certify the MODE, not correctness — if the substrate's modal answer is wrong, certification is confidently wrong (our `6df30ad6` overfit case is the shape of this risk); LLM math setting, small models.
