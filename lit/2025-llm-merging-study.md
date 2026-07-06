# A Systematic Study of Model Merging Techniques in Large Language Models

- **Authors / year:** 2025 (arXiv 2511.21437)
- **Link:** https://arxiv.org/html/2511.21437
- **Pillar:** 2 (memory in weight space)
- **Date read:** 2026-07-06

## Problem
Do model-merging gains reported for small classifiers transfer to LLMs? (I.e., can weight-space combination serve as cheap knowledge reuse at scale?)

## Mechanism
Large-scale evaluation of six merging methods (Task Arithmetic, TIES, Model Stock, TSV-Merge, Iso-C, Subspace Boosting) across 4 open LLMs x 12 fine-tuned checkpoints x 16 benchmarks.

## Evidence
Only **Task Arithmetic** (the oldest, simplest method — add task vectors relative to a shared base) reliably produces constructive interference, and the gain is modest (<1% average). Interference-aware (TIES) and subspace methods often *degrade* performance, sometimes catastrophically. Critical detail: Task Arithmetic works because all checkpoints share a **common base initialization** — task vectors live in the same basin.

## Cost / compute
Merging itself is free; the finding is about when it works at all.

## Relevance
- Limitation(s) addressed: L1.
- **Sharpens the H9/H10 postmortem:** the one merging method that works at scale requires a shared base model. Our donors were independently trained from random init — precisely the setting where all merging fails. This upgrades H14's rationale from plausible to literature-backed: create the shared base *first* (joint training), then per-task deltas become combinable/reusable objects (task vectors).
- Idea worth stealing: if H14's backbone works, per-task adaptation deltas relative to the backbone are the natural "program" unit for a weight-space library — the task-vector formulation, not whole models.
- How it could be wrong / limits: LLM-scale findings may not transfer down to 76K-param models; gains even in the working regime are small.
