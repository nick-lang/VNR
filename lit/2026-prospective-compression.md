# Prospective Compression in Human Abstraction Learning

- **Authors / year:** 2026 (arXiv 2605.09985; under review NeurIPS 2026)
- **Link:** https://arxiv.org/abs/2605.09985
- **Pillar:** 6 (cognitive science), 5 (MDL)
- **Date read:** 2026-08-18

## Problem
How do humans acquire reusable abstractions ONLINE when the task distribution drifts — the regime where retrospective library learning (compress what already worked) should lag?

## Mechanism
"Pattern Builder" visual program-synthesis paradigm: participants build geometric patterns from primitives + persistent custom helpers across trials; two latent non-stationary curricula dissociate PROSPECTIVE compression (choose abstractions that will compress FUTURE tasks) from retrospective strategies. Six computational models compared against behavior.

## Evidence
Human abstraction choices track the latent drift of the task generator — consistent with prospective compression; retrospective-compression algorithms (DreamCoder-style) and LLM inductive biases both fail to capture the behavior. (Abstract-level; quantitative details pending — preprint under review.)

## Cost / compute
Behavioral + small models; not a systems paper.

## Relevance
- Limitation(s) addressed: L3/L4 framing — what a library is FOR.
- **Cog-sci anchor for the library thesis, with a twist that critiques our own Stage 1.** H5's BPE compression is purely retrospective (compress solved programs); humans apparently select abstractions by anticipated reuse. For the write-up this is a framing citation (humans do MDL-library learning, so the mechanism is not ad hoc); for any future Stage 5e design it suggests scoring candidate abstractions by expected future compression, not frequency in past solutions.
- Idea worth stealing: curricula with latent drift as a test harness for whether a library HELPS or just memorizes — a cheap synthetic follow-up to Stage 1 if the library route reopens.
- How it could be wrong / limits: under review, numbers not yet extractable; human behavioral evidence, not a working algorithm; drift regime may not map to ARC's static task distribution.
