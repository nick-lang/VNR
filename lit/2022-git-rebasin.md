# Git Re-Basin: Merging Models modulo Permutation Symmetries

- **Authors / year:** Ainsworth, Hayase, Srinivasa — 2022 (ICLR 2023)
- **Link:** https://arxiv.org/abs/2209.04836
- **Pillar:** 2 (memory in weight space)
- **Date read:** 2026-07-06

## Problem
Independently trained networks cannot be naively averaged: they sit in different loss basins, so weight interpolation crosses high-loss barriers.

## Mechanism
Neural loss landscapes contain (nearly) a single basin *after accounting for permutation symmetries of hidden units*. Three algorithms (activation matching, weight matching, straight-through estimation) permute one model's units to align it with a reference model; after alignment, linear interpolation between independently trained models can have zero barrier ("linear mode connectivity").

## Evidence
First demonstration of zero-barrier LMC between independently trained ResNets on CIFAR-10. Alignment quality improves with model width and training time. Known follow-up caveat: REPAIR (Jordan et al. 2023) shows that even after permutation alignment, residual activation-statistics mismatches create apparent barriers, needing post-alignment renormalization. The single-basin theory also has explicit counterexamples.

## Cost / compute
Alignment is cheap (matching problems solvable with Hungarian algorithm); trivially reproducible at CompressARC scale (76K params).

## Relevance
- Limitation(s) addressed: L1 (weight-space memory).
- **Retro-explains H9/H10:** our weight-soup (H9) and single-donor transplant (H10) kills are exactly what this literature predicts for *unaligned* independently trained models. Our H14 rationale (joint training forces one shared basin) is the standard escape route this line of work implies.
- Idea worth stealing: a cheap retro-experiment — permutation-align the 11 banked donors before souping. Caveat: CompressARC's weight-tying/equivariance structure constrains which permutations are valid; alignment may be partially degenerate there.
- How it could be wrong / limits: alignment works best for wide networks; CompressARC is tiny and heavily tied, so residual barriers may persist even aligned.
