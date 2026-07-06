# Is Pre-Training Truly Better than Meta-Learning? (+ related transfer/meta comparisons)

- **Authors / year:** Miranda et al. — 2023/24 (arXiv 2306.13841); with Gijsbers et al. ML journal 2023 (MAML/Reptile vs finetuning)
- **Link:** https://arxiv.org/html/2306.13841v2
- **Pillar:** 6 (few-shot adaptation) / 2
- **Date read:** 2026-07-06

## Problem
When does meta-learning (MAML/Reptile-style shared initialization) beat plain multi-task pre-training + fine-tuning?

## Mechanism
Fair comparison (same architecture, same optimizer, trained to convergence, 196 models, 21 benchmarks) stratified by a *task-diversity coefficient* (Task2Vec-based).

## Evidence
**Low task diversity: pre-training >= meta-learning (they become empirically equivalent). High task diversity: meta-learning wins.** Related work shows MAML/Reptile specialize for fast adaptation in low-data regimes *near the training distribution* and can generalize worse out-of-distribution than finetuning from diverse features.

## Cost / compute
Concept-level takeaway; no reproduction needed.

## Relevance
- Limitation(s) addressed: L4.
- **Calibrates H14 expectations:** H14's joint round-robin training is multi-task pre-training (not true meta-learning — no inner/outer loop). ARC tasks are *maximally* diverse by design, which is the regime where plain multi-task init helps least and bi-level meta-learning helps most. Two consequences recorded before the run: (a) a marginal/kill H14 result would NOT close the shared-backbone route — the pre-registered escalation is a Reptile-style outer step, cheap to add to `s5f_runner.py`; (b) with only 6 training tasks per fold, diversity is high but *coverage* is tiny, so warm-start gains may be family-local (echoing H9's family-clustered wins).
- Idea worth stealing: the task-diversity framing as a diagnostic — our banked 11x10 probe matrix is effectively a task-similarity matrix and showed ~no family signal, predicting weak plain-multitask transfer.
- How it could be wrong / limits: vision-centric benchmarks; a 76K-param compression model at n=6 tasks is far outside the studied regime.
