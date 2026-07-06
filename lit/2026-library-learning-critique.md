# Is This LLM Library Learning? Evaluation Must Account For Compute and Behaviour (+ LEGO-Prover case study)

- **Authors / year:** Berlot-Attwell et al. — EACL 2026 (companion case study arXiv 2504.03048)
- **Link:** https://aclanthology.org/2026.eacl-long.163/ ; https://arxiv.org/html/2504.03048
- **Pillar:** 4/5 (library learning, MDL)
- **Date read:** 2026-07-06

## Problem
Are the reported gains of in-context-learning library-learning systems (LEGO-Prover, TroVE, DynaSaur) real, or artifacts of unequal compute?

## Mechanism
Re-evaluate published library-learning systems against baselines given an *equal computational budget*, plus behavioral analysis of whether learned artifacts are actually reused (direct or soft reuse).

## Evidence
All three studied systems fail to consistently beat simple prompting once compute is matched; LEGO-Prover shows **no evidence of direct lemma reuse and evidence against soft reuse**. Apparent gains were hidden test-time scaling. Their constructive suggestion: symbolic refactoring systems that demonstrably work (Stitch/LILO-style compression) over LLM in-context "libraries."

## Cost / compute
N/A (methodology paper).

## Relevance
- Limitation(s) addressed: L1/L4 — the library thesis itself.
- **Direct warning for VNR:** our H5 accept (library gives ~3.3x search efficiency) survives this critique *in design* — both arms had identical budgets and reuse was mechanical (BPE macros in the search alphabet), not vibes. But the H5 result is synthetic-only; the critique raises the bar for any future claim of library gain on real ARC: must be compute-matched AND show measured reuse (macro call counts), which our harness already logs.
- Idea worth stealing: "reuse must be measured, not assumed" as a pre-registered metric for every future library-stage decision rule.
- How it could be wrong / limits: the critique targets *in-context LLM* library learning; compression-based symbolic library learning (DreamCoder/Stitch — and our Stage 1) is explicitly exempted as "known to work."
