# nextGen — Post-LLM Reasoning Architecture Research

A theory-first, low-compute research program to rearchitect reasoning systems "from the ground up": separating computation from addressable memory, moving beyond pure next-token prediction, and targeting the real open problem the 2026 literature has converged on — the consistent ~2-3x compositional-generalization collapse from ARC-AGI-1 to ARC-AGI-2 that every paradigm exhibits, plus the fact that reasoning is still "knowledge-bound" and expensive.

The full staged program lives in [docs/plan.md](docs/plan.md). The concrete build-and-test plan for the synthesized architecture (codename VNR — a fixed interpreter + growing abstraction library) lives in [docs/vnr-build-test-plan.md](docs/vnr-build-test-plan.md).

## Guiding theses (intuitions mapped to live research)

- Context limits memory -> separate computation from addressable memory (von Neumann analogy). SSMs (Mamba-3), power-law memory (Sessa), external/episodic memory.
- "Just next-word prediction" -> predict in latent space and optimize for correctness/compression. JEPA / energy-based models; MDL (CompressARC); program synthesis ("Parrots to Von Neumanns").
- ARC is unsolved -> the gap is compositional, sample-efficient, fluid reasoning, not scale. The strongest ideas live in tiny zero/low-pretraining models (TRM ~7M params, CompressARC).
- Cost is the threat -> treat skill-acquisition efficiency (Chollet) and $/task as first-class targets.

## Repository layout

| Directory | Purpose |
| --- | --- |
| `docs/` | The approved research plan and high-level documents. |
| `lit/` | Annotated bibliography and per-paper notes (one file per paper). |
| `ledger/` | Living research ledgers: `limitations.md`, `hypotheses.md`, `results.md`. |
| `spec/` | Architecture spec / manifesto drafts (`architecture-v0.md`). |
| `experiments/` | Tiny, laptop-runnable proof-of-concept experiments + lab-notebook entries. |
| `data/` | ARC-AGI task data (fetched via `data/fetch_arc.py`; not committed). |
| `references/` | Vendored reference code (TRM, CompressARC, NVARC; cloned, not committed). |

## Working discipline

This is a lab notebook, not a product. Every experiment gets a dated entry in `experiments/notebook/` using [experiments/notebook/TEMPLATE.md](experiments/notebook/TEMPLATE.md): hypothesis -> setup -> metric -> result -> decision. Hypotheses are pre-registered in `ledger/hypotheses.md` before experiments run; outcomes land in `ledger/results.md`.

## Status

Phase 0 (workspace scaffolding) complete. Next: Phase 1 — literature map + limitations ledger.

## Environment

- Python 3.11+
- See `requirements.txt` for the (intentionally minimal) starting dependencies.
