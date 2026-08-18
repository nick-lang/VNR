# 2026-08-18 — Strategic direction: amortize the interpreter, not the weights (proposed Stage 9)

- **PoC:** none yet (reading + synthesis, $0; E1-B capture runs in flight on the 5090)
- **Hypothesis:** proposes H17/H18 for owner pre-registration; no decision rule is active until the owner sets numbers
- **Hardware:** local RTX 5090 (reference)

## The question (owner, 2026-08-18)

Given all findings and the new literature: is there a genuinely new direction toward
cheaper frontier-class capability and/or solving ARC?

## Synthesis: the program's negatives point somewhere specific

1. H9/H10/H14 closed weight-space memory: weights alone don't encode solutions
   (knowledge = latent/weight co-adaptation), and per-task weight deltas are
   orthogonal even from a shared basin — there is no shared weight-space direction
   to amortize.
2. H15 + the 198-run coverage study: per-task training is run-stochastic; coverage
   is a draw; loss-scorers can't pick winners. The substrate's real ceiling (union
   15+/50) is above its deliverable pass@2 (11/50) for want of a selector.
3. Read together: the amortizable object is NOT the weights and NOT the training
   trajectory — it is the INTERPRETER. Fix a decoder that maps (input, latent
   program) -> output; make the latent the only per-task object; adapt by searching
   latent space, not by training weights.

**The literature already contains the existence proof we lacked:** the Latent
Program Network (Macfarlane & Bonnet, NeurIPS 2025; `lit/2025-latent-program-network.md`).
Frozen decoder + test-time gradient search in latent space, trained WITH search in
the loop (their Grad-1 lesson: 99.5% vs 67.5%). On real ARC eval (OOD): 15.5% —
CompressARC-class accuracy — at collapsed marginal cost (latent search instead of
2000 weight-training steps per task). Trained only on re-arc (procedural, LLM-free).
H14 is not contradicted: it never had an encoder, never searched latents-only, and
never trained the backbone to support that search. LPN is the correctly-run
inversion of H14.

**The open niche (nobody has run it, LLM-free):** LPN's stated limitation is the
narrow program distribution (re-arc's 400 fixed programs). That is precisely the
library thesis' opening: grow the latent-program distribution over time by
hindsight replay of self-verified solves (train-pair-consistent solutions distilled
back into the training stream). VNR's "fixed interpreter + growing abstraction
library" maps 1:1 onto "frozen decoder + expanding latent-program corpus." Our
selection stack (H16 augmentation-voting; E1-B selectors) and run-marginalized
evaluation apply directly on top and are themselves contributions there
(LPN's numbers are single-run; ours would be honest).

## Proposed three-horizon plan (owner decision required)

- **Horizon 1 (in flight, unchanged):** finish E1-B -> selector verdicts; H16
  augmentation-voting behind its equivariance gate; ship the write-up. This is the
  deliverable regardless of any pivot.
- **Horizon 2 — H17 (Stage 9a, proposed):** tiny-LPN reproduction on the 5090.
  re-arc generation (CPU, LLM-free) + a 10-30M-param encoder/decoder with Grad-1
  training. Validity gate: reproduce the train-for-search dynamics at small scale
  (search-scaling curve; Grad-1 >> Grad-0). Decision metric (numbers = owner's
  call; drafted): run-marginalized pass@2 on our committed 50-task dev split at
  matched TOTAL cost accounting (pretrain amortized + marginal), vs the banked
  CompressARC baselines. Draft bars: ACCEPT if coverage >= CompressARC's
  run-marginalized 11-15/50 at <= 1/10 marginal per-task cost; KILL if < 6/50 at
  every search budget. One-time pretrain estimate: 2-6 days 5090, $0 cloud.
  NOTE: this drops the zero-pretraining purity constraint. The goal (2026-07-06)
  is capability-per-dollar, not purity: procedural pretraining is teacher-free
  (no frontier model anywhere in the loop) and its one-time cost amortizes to
  ~zero marginal. The honest accounting stays in the metric (total-cost curve).
- **Horizon 3 — H18 (Stage 9b, gated on H17 accept):** grow the program
  distribution — hindsight replay of self-verified eval solves into training,
  vs a frozen-distribution control at matched compute; metric = OOD coverage
  growth. This attacks LPN's stated ceiling with the program's library thesis
  and would be the write-up's sequel.

## What was done today ($0)

- LPN read in full; note filed (`lit/2025-latent-program-network.md`); index
  updated (+ 4 tracked-unread links: ARC-TGI, ARC-GEN, slots/loops world models,
  T5-ARC).
- This entry records the proposal BEFORE any Stage-9 code exists; pre-registration
  numbers await owner approval per house discipline.

## Decision

OWNER FORK (open): (a) approve Stage 9a/H17 pre-registration as drafted (or set
different bars), to start after E1-B drains; (b) fold H17 behind the write-up
(ship first, then build); (c) decline the pivot and continue substrate-external
memory (Stage 5e symbolic) instead. Recommendation: (b) — ship the write-up, then
H17; the write-up's conclusions are unaffected by H17's outcome and the capture
runs + H16 feed both.
