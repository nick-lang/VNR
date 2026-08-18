# Program Synthesis via Test-Time Transduction

- **Authors / year:** 2025 (arXiv 2509.17393; NeurIPS 2025)
- **Link:** https://arxiv.org/abs/2509.17393
- **Pillar:** 4 (ARC corpus / program synthesis)
- **Date read:** 2026-08-18

## Problem
Synthesis from few examples is brittle on edge-case test inputs; test inputs are normally used only for post-hoc evaluation, wasting their information.

## Mechanism
Reframes synthesis as ACTIVE LEARNING over a finite hypothesis class defined by candidate programs' OUTPUTS: strategically pick test inputs where candidates disagree, query an oracle (LLM) for the output there, eliminate inconsistent hypotheses; greedy maximin minimizes queries.

## Evidence
Improved accuracy and efficiency on Playgol, MBPP+, 1D-ARC, and MiniGrid world-modeling (abstract-level; per-benchmark numbers not extracted).

## Cost / compute
Rides on LLM queries; the elimination loop itself is cheap. Reproducible in miniature.

## Relevance
- Limitation(s) addressed: L3/L5 — candidate selection without labels.
- **Selection = hypothesis elimination on disagreement, not scoring.** Our refuted selectors (H10 probe-loss, H15 tail-loss) both tried to SCORE candidates; this line eliminates candidates where their predictions DISAGREE. Substrate translation for H16: seeds/augmentations are the hypothesis class, the test grid (and held-out train pairs) are the disagreement domain, agreement clusters replace oracle queries (we have no oracle — voting is the degenerate but label-free form).
- Idea worth stealing: the finite-hypothesis-class framing makes our "126 banked runs" a reusable eval set for ANY selector, retrospectively, at $0.
- How it could be wrong / limits: needs an oracle for elimination (we don't have one — weakens the transfer); LLM-substrate; 1D-ARC only, not real ARC.
