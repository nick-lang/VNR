# Searching Latent Program Spaces (Latent Program Network, LPN)

- **Authors / year:** Macfarlane & Bonnet — NeurIPS 2025 (arXiv 2411.08706v3)
- **Link:** https://arxiv.org/abs/2411.08706
- **Pillar:** 3/4 (latent prediction; ARC corpus)
- **Date read:** 2026-08-18 (full read, pp. 1-11)

## Problem
Program induction without a hand-built DSL (unscalable) and without test-time
full fine-tuning (expensive, overfits): where should test-time adaptation live?

## Mechanism
Encoder (I/O pair -> posterior over a 256-dim latent "program"), decoder
(input + latent -> output, pixelwise), and TEST-TIME GRADIENT SEARCH IN LATENT
SPACE with the decoder FROZEN: z' = argmax sum log p(y_i|x_i,z), initialized
from the encoder (system 1), refined by gradient ascent (system 2). Decisive
design lesson: training must ANTICIPATE the search — training with 1 step of
latent optimization in the loop (Grad 1) vs none (Grad 0) is the difference
between 99.5% and 67.5% on the pattern task. Formally semi-amortised
variational inference; the ELBO framing makes it MDL-native.

## Evidence
Pattern task (1M params): test-time latent search scales smoothly with
inference compute; TTT overfits, ICL flat; OOD: LPN Grad-1 recovers 88% where
TTT/ICL get ~0. ARC-AGI (178M params, trained ONLY on re-arc — procedurally
generated, no LLM, ARC train outputs never seen): in-distribution 68.75-80%
vs TTT 45.75-58.75% across 2e11-2e13 FLOPs; OOD (real eval set) 7.75 -> 15.5%
as search FLOPs scale 2e11 -> 2e15 (doubles with search on), TTT 5.85 -> 16%.
LPN and TTT solve DIFFERENT eval subsets (their B.9). Beats CodeIt (220M) and
text-davinci (175B) baselines on both splits.

## Cost / compute
178M params, 100k steps, 2 days on a TPU v4-32 (one-time); per-task inference
is latent-only gradient search — MARGINAL cost per task collapses vs
per-task weight training. Their 1M-param pattern-task models train in hours;
a 10-30M ARC variant is plausibly consumer-GPU-trainable.

## Relevance
- Limitation(s) addressed: L4/L5 (amortization), L3 (OOD adaptation).
- **This is the inversion of our H14 negative, run correctly.** H14 found the
  shared weights alone don't encode solutions (knowledge = latent/weight
  co-adaptation) and per-task weight deltas are orthogonal. LPN's answer:
  make latents the ONLY per-task object, freeze the decoder, and train the
  decoder explicitly so latent-only search works (Grad-1-in-training). H14
  never had an encoder, never did latent-only search, and never trained for
  it — the negatives are compatible, and LPN is the pre-registered escape
  route we didn't know existed. Decoder = fixed interpreter; latent =
  program: this IS the VNR architecture sketch in neural form.
- **Their stated limitation is our thesis' opening:** "limited diversity of
  programs on which LPN is trained" — re-arc's 400 fixed programs. A growing
  abstraction library / hindsight replay of self-verified solves back into
  the training distribution is exactly the library-thesis attack on that
  ceiling, and nobody has run it LLM-free.
- Ideas worth stealing: train-for-search (Grad-1); encoder-init-then-search
  beats prior sampling by a wide margin; stop-gradient through the latent
  update (cheaper AND better); different-substrates-solve-different-subsets
  (portfolio/selection angle, matches our churn finding).
- How it could be wrong / limits: OOD ceiling ~15.5% is CompressARC-class,
  not a step change; 178M/TPU pretrain is not $0 (though one-time and
  teacher-free); compositional generalization at test time is "not robust"
  (their B.10); latent search inherits our run-stochasticity questions —
  their numbers are single-run.
