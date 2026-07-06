# ArcMemo: Abstract Reasoning Composition with Lifelong LLM Memory

- **Authors / year:** Ho et al. — 2025 (arXiv 2509.04439; ARC Prize 2025 paper runner-up)
- **Link:** https://arxiv.org/abs/2509.04439
- **Pillar:** 2/4 (memory; ARC corpus)
- **Date read:** 2026-07-06

## Problem
Reasoning traces are discarded when the context resets; instance-level memories (stored Q/A pairs, trace summaries) transfer poorly to superficially different problems.

## Mechanism
**Concept-level memory in natural language:** distill solution traces into abstract, modular, *parameterized* concepts (their "program synthesis" format: typed, higher-order-function-like entries), stored in a flat library. At inference: select relevant concepts (reasoning-based selection, not embedding similarity) and insert into the prompt. Memory updates continually at test time.

## Evidence
On ARC-AGI-1 with a frontier LLM: 55.17 -> 59.33 (+7.5% relative) over a strong no-memory baseline; the *abstract* concept format is the only memory design that beats baseline at all inference-compute scales; dynamic test-time memory updates beat frozen memory. Instance-level memory designs underperform.

## Cost / compute
Rides on frontier-LLM inference; the memory machinery itself is cheap (text).

## Relevance
- Limitation(s) addressed: L1, L3.
- **Independent convergence on our two-kill inference:** whole-solution memories (their "instance-level" = our weight blobs) transfer poorly; decomposed, parameterized concepts transfer. This is the H13/Stage-5e direction validated in the LLM substrate — and it strengthens the case that VNR's memory should store *parts* with typed composition interfaces, whatever the substrate.
- Idea worth stealing: (1) parameterization + typed interfaces as the storage format for abstractions (maps directly onto DSL macros with typed holes); (2) reasoning-based selection over embedding lookup — matches our H10 finding that cheap similarity signals fail; (3) write-time abstraction from pseudocode of the solution, not the raw trace.
- How it could be wrong / limits: depends on a frontier LLM to do the abstraction and the composition; +7.5% relative is modest; no evidence it works without giant priors.
