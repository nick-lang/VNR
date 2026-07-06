# Efficient Evolutionary Program Synthesis (Pang, ARC Prize 2025 runner-up)

- **Authors / year:** Eric Pang — 2025
- **Link:** https://ctpang.substack.com/p/arc-agi-2-sota-efficient-evolutionary
- **Pillar:** 4 (ARC corpus)
- **Date read:** 2026-07-06

## Problem
LLM-evolutionary ARC solvers (Berman-style) are accurate but expensive; can cross-task knowledge accumulation cut the cost?

## Mechanism
DreamCoder-inspired wake-sleep on top of an LLM: solve tasks by generating Python programs (wake), then abstract solved programs into a persistent shared library that is fed into later prompts (sleep). Trained on the 1,000-task ARC-AGI-2 public training set, seeding a 538-program library.

## Evidence
77.1% ARC-AGI-1 / 26.0% ARC-AGI-2 at ~$2.56-3.97/task — beating frontier models on the cost-accuracy Pareto frontier; LLM calls per task cut from ~36 to 10 via library reuse. Still shows the universal 2.5-3x ARC-1 -> ARC-2 degradation.

## Cost / compute
~$4/task with a frontier LLM (Grok-4) as proposer. Not reproducible without LLM API spend, but the library mechanism is.

## Relevance
- Limitation(s) addressed: L1, L4, L5.
- **This is the strongest external validation of the VNR library thesis on real ARC:** a growing cross-task library measurably cut cost per task (the amortization H5 showed synthetically) at near-SoTA accuracy. Key difference from our stages: the proposer is a frontier LLM, so the library rides on massive priors — exactly the dependency VNR wants to remove.
- Caveat from the library-learning critique (2026-library-learning-critique.md): Pang's LLM-call reduction (36 -> 10) is a *measured compute saving*, which is the kind of evidence the critique demands — but reuse behavior wasn't independently audited.
- Idea worth stealing: library entries as plain Python functions with docstrings, selected into context by the proposer; the wake-sleep loop structure over a real task corpus.
- How it could be wrong / limits: gains may come from the LLM's knowledge, with the library acting mostly as prompt-cache; ARC-2 degradation persists, so the library doesn't fix compositional collapse.
