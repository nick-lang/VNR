# ARC-AGI-3: A New Challenge for Frontier Agentic Intelligence (Technical Report)

- **Authors / year:** ARC Prize Foundation — 2026 (arXiv 2603.24621)
- **Link:** https://arxiv.org/html/2603.24621v1
- **Pillar:** 4 (ARC corpus), 6 (measure of intelligence)
- **Date read:** 2026-08-18 (upgrades the tracking mention in `2026-arc-prize-2025-report.md` to a full note)

## Problem
ARC-1/2 measure static few-shot inference; ARC-AGI-3 measures agentic intelligence — exploration, world-modeling, goal acquisition, planning — with no instructions given at all.

## Mechanism
Interactive turn-based grid environments (64x64, 16 colors; 5-6+ levels each); agent sees frames, acts (5 directions, cell-select, undo), must DISCOVER the win condition. Scoring = RHAE (Relative Human Action Efficiency): per-level min(1, h/a)^2 vs the second-best human's action count — a capability-per-ACTION metric; internal reasoning is free, only state-altering actions count. Splits: 25 public / 55 semi-private / 55 fully private (inverts ARC-2's public:private ratio); hard cost cap at 5x human actions.

## Evidence
Humans: 100% of environments solvable (486 participants; median successful attempt 8.1 min). Frontier systems (March 2026, no harness): Gemini 3.1 Pro 0.37%, GPT 5.4 0.26%, Opus 4.6 0.25%, Grok-4.20 0.00% — all <1%.

## Cost / compute
Full frontier eval estimated tens of thousands of dollars — the benchmark itself prices efficiency in.

## Relevance
- Limitation(s) addressed: L1 (memory), L4, L5 — the first benchmark where they are load-bearing rather than instrumental.
- **The efficiency metric IS the program's objective function.** RHAE squares the inefficiency penalty and normalizes to human action budgets: capability-per-action, formalized by the field's own benchmark. A memory+exploration architecture pays off VISIBLY here in a way ARC-1/2 never rewarded (frontier <1% vs human 100% is a 100x open gap, vs the crowded ARC-1 leaderboard).
- Idea worth stealing: action-efficiency as the headline metric for any future VNR agentic stage; the 5x-human hard cap as a cost-gate discipline we already practice.
- How it could be wrong / limits: interactive environments obsolete our entire CompressARC-substrate tooling (per-task MDL on static grids does not transfer directly); public set is deliberately easy; scores <1% may partly reflect missing harness scaffolding, not missing capability.
