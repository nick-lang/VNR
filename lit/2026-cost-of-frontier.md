# The Price of Progress: Price-Performance and the Future of AI (+ distillation economics)

- **Authors / year:** 2025-26 (arXiv 2511.23455); small-reasoning-model survey (Frontiers of CS 2025); practitioner distillation economics (2026)
- **Link:** https://arxiv.org/html/2511.23455v2
- **Pillar:** 1/5 (economics of capability)
- **Date read:** 2026-07-06

## Problem
Is "frontier capability at near-zero cost" arriving by default from market price declines?

## Mechanism
Longitudinal analysis of benchmark performance vs inference price; separates price-deflation effects from algorithmic progress.

## Evidence
- Per-token prices fall fast (~80% headline drop 2024-26; up to ~31x/year at the quality frontier), BUT **the cost of running frontier-*level* models rose ~3-18x/year** because marginal capability gains require disproportionately more inference (longer reasoning traces, more samples). Roughly half of measured GPQA "progress" is just higher inference spend.
- Distillation: DeepSeek-R1-style CoT distillation gets a 32B student competitive with models 3-4x larger; well-distilled students are up to ~130x faster / ~25x cheaper — but the capability is a *snapshot*, domain-brittle, and needs 100K-1M reasoning traces from a teacher that must already exist.
- Small reasoning models (SRM survey): distilled small models are the standard efficient alternative; all inherit the teacher-dependence.

## Cost / compute
N/A (analysis).

## Relevance
- Limitation(s) addressed: L5 (now the program's primary limitation per the 2026-07-06 goal clarification).
- **The goal will not be reached by waiting:** frontier-level *usage* cost is rising, not falling. And the standard cheap path (distillation) presupposes a frontier teacher — it compresses existing capability, it cannot create cheap capability. That is precisely the niche VNR targets: capability from architecture (memory + adaptation + compression objectives) rather than from scale or from copying scale.
- Sharpens the honest framing: "as powerful as frontier models at near-zero cost" across ALL domains is not supported by any known mechanism; the defensible target is frontier-*matching capability per domain* at orders-of-magnitude lower cost (PTRM's 2x-accuracy-at-0.0001x-cost result is the existence proof), plus a memory/adaptation architecture that widens the domain over time.
- How it could be wrong / limits: cost trends extrapolate a young market; a single algorithmic break (e.g., cheap TTT at scale) could invert the trend.
