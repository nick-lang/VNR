# ARC Prize 2025: Technical Report (+ Living Survey cost analysis)

- **Authors / year:** ARC Prize Foundation — 2026 (arXiv 2601.10904); Living Survey (arXiv 2603.13372)
- **Link:** https://arxiv.org/html/2601.10904
- **Pillar:** 4 (ARC corpus)
- **Date read:** 2026-07-06 (updates the June skim with the cost-frontier numbers)

## Problem
State of the field: what won, what's bottlenecked, where the open scientific gap is.

## Mechanism
Survey. Defining 2025 theme: **the refinement loop** (per-task iterative program/model improvement against a feedback signal), in three substrates: evolutionary program synthesis (Berman, Pang), application-layer loops on commercial LLMs, and weight-space loops (TTT; zero-pretraining models like TRM/CompressARC).

## Evidence
- ARC-AGI-2 top: NVARC 24.03% at $0.20/task (Kaggle, compute-capped). ARC-AGI-1: GPT-5.2 Pro 90.5% at $11.64/task; Gemini 3 Flash 84.7% at $0.17/task; Pang 77.1% at ~$4/task.
- Cost scaling law (Living Survey): accuracy ~ 0.15 x log(cost) — each 10x compute buys ~15 points; scaling to human level is economically prohibitive. The o3 -> GPT-5.2 "390x efficiency gain" was mostly reduced parallelism, not algorithmic progress.
- **Foundation's own assessment: the accuracy gap is now bottlenecked by engineering; the *efficiency* gap is bottlenecked by fundamental science and new ideas.**
- Frontier reasoning remains knowledge-coverage-bound (new contamination modes); ARC-AGI-3 (early 2026) moves to interactive tasks: exploration, planning, memory, goal acquisition. Frontier systems score <1%, humans 100%.

## Cost / compute
N/A.

## Relevance
- Limitation(s) addressed: L3, L4, L5.
- **Directly ratifies the clarified program goal (2026-07-06):** the open scientific problem is capability-per-dollar, not raw accuracy — which is exactly the owner's north star. VNR's cost-first metrics are aimed at the acknowledged science bottleneck, not the engineering one.
- Frontier cost trend paper (arXiv 2511.23455): per-token prices fall, but frontier-*level* usage cost rises ~3-18x/year because marginal gains need more inference. "Cheap frontier capability" will not arrive by default from price deflation.
- ARC-AGI-3's explicit memory/exploration requirements land on VNR's thesis (persistent memory + cheap adaptation); worth tracking as the eventual benchmark where a memory architecture pays off visibly.
- How it could be wrong / limits: Kaggle cost numbers are compute-capped, not free-market; contamination analysis makes frontier comparisons noisy.
