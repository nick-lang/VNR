# Annotated bibliography — index

Master list of reading notes, grouped by pillar. Add an entry (link to the note file) when a paper is logged. Seeded from the Phase 0 grounding search; notes to be written in Phase 1.

## 1. Limits of transformers / next-token objective
- [2026 — The Price of Progress + distillation economics](2026-cost-of-frontier.md) — frontier-level usage cost RISES ~3-18x/yr; distillation compresses capability but cannot create it. (Also pillar 5; primary support for the 2026-07-06 goal clarification.)

## 2. Memory & long context
- Mamba-3: Improved Sequence Modeling using State Space Principles — https://arxiv.org/html/2603.15569v1
- Sessa: Selective State Space Attention (power-law memory) — https://arxiv.org/pdf/2604.18580
- Characterizing SSM & hybrid LM performance with long context — https://arxiv.org/html/2507.12442v3
- [2022 — Git Re-Basin](2022-git-rebasin.md) — permutation symmetry / loss basins; retro-explains the H9/H10 kills.
- [2025 — Systematic study of LLM model merging](2025-llm-merging-study.md) — only Task Arithmetic (shared-base task vectors) works; merging independently trained models fails. Backs H14's joint-basin rationale.
- [2025 — ArcMemo](2025-arcmemo.md) — concept-level (decomposed, parameterized) memory beats instance-level memory on ARC; independent convergence with our H13/Stage-5e direction.

## 3. World models / latent prediction
- I-JEPA (LeCun's joint-embedding predictive architecture) — https://ai.meta.com/blog/yann-lecun-ai-model-i-jepa/

## 4. ARC corpus
- [2026 — ARC Prize 2025 Technical Report + Living Survey cost analysis](2026-arc-prize-2025-report.md) — accuracy gap = engineering; EFFICIENCY gap = open science; accuracy ~ 0.15 log(cost).
- [2026 — ARC-AGI-3 Technical Report](2026-arc-agi-3-report.md) — interactive agentic benchmark; RHAE = capability-per-action metric; frontier <1%, humans 100%. The benchmark where the memory thesis becomes load-bearing.
- [2025 — Pang, Efficient Evolutionary Program Synthesis](2025-pang-library-arc.md) — DreamCoder-style growing library on real ARC: 77.1% ARC-1 at ~$4/task; strongest external validation of the library thesis (LLM-dependent).
- [2026 — TRM follow-ups (TRM-Planner, PTRM, mechanistics)](2026-trm-followups.md) — noise + learned selection escapes refinement attractors; frontier-beating accuracy at ~1e-4x cost within a domain.
- [2025 — TRM test-time adaptation (competition note)](2025-trm-tta-competition.md) — 7M TRM + full-FT TTA: 6.67% semi-private ARC-2; the pretrained-prior counterpart to our substrate; public->private drop is an overfitting caution.
- [2026 — Test-Time Augmentation at matched compute](2026-tta-matched-compute.md) — input diversity beats output diversity at equal compute (~1.8x accuracy/$); H15 tested the wrong diversity axis; direct H16 design template. (Also pillar 5.)
- [2025 — Program Synthesis via Test-Time Transduction](2025-test-time-transduction.md) — selection as hypothesis ELIMINATION on disagreement, not scoring; framing for the H16 selector after two score-based selectors died.
- [2025 — Latent Program Network (Searching Latent Program Spaces)](2025-latent-program-network.md) — frozen decoder + test-time GRADIENT SEARCH IN LATENT SPACE; train-for-search lesson; OOD 15.5% on ARC eval at collapsed marginal cost; its stated limitation (program diversity) is the library thesis' opening. The literature-backed inversion of our H14 negative.
- Tracked, unread: ILP-for-ARC / ILPAR (arXiv 2405.06399, verified real); Combining Induction and Transduction for Abstract Reasoning (arXiv 2411.02272 — different approaches solve DIFFERENT subsets, ensembling approaches human level; independent echo of our portfolio/churn finding); Gold/Angluin grammatical-inference bounds as DSL-learnability theory (teatime dossier direction 3, long-horizon); ARC-TGI task generators (arXiv 2603.05099); ARC-GEN mimetic generator (arXiv 2511.00162); Slots/Transitions/Loops composable world models (arXiv 2606.12316); T5-ARC transductive TTT (OpenReview TtGONY7UKy).
- ARC Prize 2025: Technical Report — https://arxiv.org/html/2601.10904
- The ARC of Progress: Living Survey of 82 approaches — https://arxiv.org/html/2603.13372v1
- Compositional Neuro-Symbolic Reasoning (ARC-AGI-2) — https://arxiv.org/pdf/2604.02434
- Don't throw the baby out with the bathwater: deep learning for ARC (TTFT + AIRV) — https://arxiv.org/html/2506.14276v2
- ARC-AGI 2025 research review (lewish.io) — https://lewish.io/posts/arc-agi-2025-research-review
- NVARC solution (synthetic data + TTT + ensemble) — https://github.com/1ytic/NVARC
- SOAR, TRM, CompressARC, "From Parrots to Von Neumanns" — see https://arcprize.org/competitions/2025

## 5. Algorithms & information theory (Knuth)
- TAOCP Vol 4 (combinatorial searching) — for program/DSL search
- Kolmogorov complexity / MDL — link to CompressARC's objective
- [2026 — Library-learning critique (compute-matched evaluation)](2026-library-learning-critique.md) — ICL library-learning gains vanish at equal compute; reuse must be measured. Raises the bar for all future library claims; symbolic compression (Stitch/our Stage 1) exempted.
- [1988 — The utility problem + case-base maintenance](1988-minton-utility-problem.md) — learned abstractions can SLOW a solver; 15 years of retention/forgetting policy theory; the decision rule for H18's library curation. (Teatime dossier import.)
- [2025 — Certified Self-Consistency](2025-certified-self-consistency.md) — majority voting as mode estimation with finite-sample certificates + adaptive stopping (MMC); the formalism behind "seed-marginalized solve probability" and vote-margin confidence for H16.

## 6. Cognitive science of fluid intelligence
- Chollet, "On the Measure of Intelligence" (skill-acquisition efficiency) — _(todo)_
- [2023 — Pre-training vs meta-learning (task diversity)](2023-pretrain-vs-meta.md) — plain multi-task init wins at low task diversity, meta-learning at high; calibrates H14 expectations and pre-registers the Reptile escalation.
- [2005 — Kashtan & Alon, modularly varying goals](2005-kashtan-alon-mvg.md) — modularity/reuse emerges iff goals vary modularly (shared subgoals); random variation -> none. Retroactive frame for H14's orthogonal deltas; curriculum arm for H18. (Teatime dossier import.)
- [2026 — Prospective Compression in Human Abstraction Learning](2026-prospective-compression.md) — humans pick abstractions for FUTURE compression, not past; cog-sci anchor for the library thesis; critique of purely retrospective Stage-1 BPE.
