# Test-Time Augmentation for LLMs: When Input Diversity Beats Output Diversity at Matched Compute

- **Authors / year:** 2026 (arXiv 2608.09351)
- **Link:** https://arxiv.org/html/2608.09351
- **Pillar:** 4/5 (test-time compute; economics)
- **Date read:** 2026-08-18

## Problem
At fixed inference compute, does input-side diversity (augmented/rephrased inputs) or output-side diversity (self-consistency sampling) convert compute into accuracy more efficiently?

## Mechanism
Test-time augmentation (TTA): generate k input variants (semantic rephrasings, lexical perturbations, or mild visual transforms), answer each independently, aggregate by majority vote. Systematic matched-compute comparison against self-consistency across 6 benchmarks.

## Evidence
Semantic TTA +1.8pp avg (p<0.01) vs self-consistency +0.92pp over CoT baseline; beats self-consistency on 5/6 benchmarks; ~1.8x more accuracy per dollar; Pareto-dominates on the cost-accuracy frontier. Gains shrink with model scale (Haiku +2.75pp -> Opus +0.25pp). Combining text+image augmentation DEGRADES (65.08% vs 68.09% text-only) — diversity axes don't stack for free.

## Cost / compute
LLM-substrate experiments (Claude 4.5 Haiku primary); the augmentation principle itself is substrate-agnostic and free to test in ours.

## Relevance
- Limitation(s) addressed: L5 (compute allocation), and it reframes the H15 kill.
- **H15 tested the wrong diversity axis.** Our arm B varied the SEED (output-side/init diversity); this paper says the winning axis is the INPUT. In our substrate the natural input augmentations are exact and lossless: D8 grid transforms + color permutations of a task, each solved independently, top-picks reverse-mapped and voted. That is the AIRV recipe (already in `lit/`, 2506.14276) arriving independently in the LLM literature with a matched-compute win. Direct design template for H16.
- Idea worth stealing: report accuracy-per-dollar Pareto curves, not just accuracy — matches our capability-per-dollar framing exactly.
- How it could be wrong / limits: LLM-only evidence; gains are small (1-2pp) and shrink with capability; majority voting can amplify confidently-wrong answers (their caveat = our seed-churn caveat); answer-equivalence must be well-defined (it is, for ARC grids).
