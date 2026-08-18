# Test-time Adaptation of Tiny Recursive Models (ARC Prize 2025 competition note)

- **Authors / year:** 2025 (arXiv 2511.02886)
- **Link:** https://arxiv.org/abs/2511.02886
- **Pillar:** 4 (ARC corpus)
- **Date read:** 2026-08-18

## Problem
Squeeze ARC-AGI-2 performance from a 7M-param TRM under Kaggle compute caps.

## Mechanism
Pre-train TRM on 1,280 public tasks (700k+ steps, 48h on 4xH100), then test-time adaptation by FULL fine-tuning (not LoRA/embedding-only) on the hidden competition tasks, 12,500 gradient steps within the cap.

## Evidence
~10% public ARC-AGI-2 eval after pre-training; 6.67% semi-private after TTA. Full fine-tuning chosen over parameter-efficient variants.

## Cost / compute
7M params; pre-train 48h/4xH100 (out of solo-budget range but ~100x below frontier); TTA phase itself is cheap.

## Relevance
- Limitation(s) addressed: L4/L5 datapoint.
- **Nearest neighbor to our program on the OTHER zero/low-pretraining substrate** — and a useful contrast: TRM's TTA needs a pre-trained prior to adapt (their H3 form), while CompressARC's "training IS test-time" needs none. Their 6.67% semi-private at Kaggle cost vs NVARC's 24% quantifies how far tiny-model purity currently trails synthetic-data scale.
- Idea worth stealing: the full-fine-tuning-beats-PEFT finding at 7M scale (relevant if a trained proposer ever lands in Stage 2 — don't assume LoRA).
- How it could be wrong / limits: competition note, minimal analysis/ablation; the public->semi-private drop (10% -> 6.67%) is itself an overfitting signal worth remembering when we quote public-set numbers.
