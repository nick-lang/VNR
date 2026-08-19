# The Utility Problem (explanation-based learning) + case-base maintenance

- **Authors / year:** Minton — 1988 (Learning Search Control Knowledge /
  PRODIGY-EBL); CBR maintenance lineage from the 1990s (Smyth & Keane et al.)
- **Link:** https://doi.org/10.1016/0004-3702(90)90059-9 (Minton, AIJ 1990 version)
- **Pillar:** 5 (algorithms; library curation theory)
- **Date read:** 2026-08-19 (surfaced by the owner's teatime discovery dossier;
  characterization checked against established knowledge — primary sources not
  re-read line-by-line today)

## Problem
Learned macro-operators/control rules can make a problem solver SLOWER: each
stored abstraction adds matching/retrieval cost to every future search, and
that cost can exceed the search it saves. Named the **utility problem**; the
question "when does adding a stored case hurt" was then worked for ~15 years
as **case-base maintenance** in CBR.

## Mechanism
Utility accounting: keep an abstraction only if
(application savings x application frequency) > (match cost x match
frequency). Remedies developed: selective acquisition, empirical utility
validation on a workload, forgetting/deletion policies, case-base
compaction under coverage constraints.

## Relevance
- Limitation(s) addressed: the program's own open question — "what makes a
  growing abstraction library help rather than bloat" (Stage 5d's deferred
  links/pruning; H18's curation).
- **Import, don't reinvent:** our Stage-1 library already logs macro call
  counts (reuse measurement); the utility problem says the DECISION RULE for
  retention should be cost-benefit per abstraction, measured on a workload —
  pre-registerable as H18's curation metric (library size vs solve-rate vs
  per-task search cost curves; prune negative-utility entries).
- **Modern echoes we already cite:** the compute-matched library-learning
  critique (2026) is utility accounting rediscovered; ARC test-time
  transduction is CBR without the maintenance theory. Citing the original
  lineage strengthens the write-up's library discussion and H18's design.
- How it could be wrong / limits: utility accounting assumes measurable,
  stable match costs — in latent-space libraries (H18) "match cost" needs a
  definition (encoder/search steps?) before the accounting transfers.
