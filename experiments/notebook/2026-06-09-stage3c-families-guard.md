# 2026-06-09 — Stage 3c: more families + stability guard (H7-v3)

- **PoC:** PoC-VNR-S3b dir (`experiments/poc-vnr-s3b-objectmap/`, `run_stage3c.py`)
- **Hypothesis:** H7-v3 — pre-registered (families + guard + same numeric bar) before running.
- **Hardware:** CPU only, `.venv-carc`. Full run 4.1 s.
- **Command:** `run_stage3c.py --budget 50000 --arc2-probe 30` (deterministic).

## Setup
- Added three families in simplicity order: cellwise color permutation, gravity (4 directions, both segmentations), symmetry-fill (fliplr/flipud/rot180/transpose). Smoke-tested on synthetic cases pre-benchmark (all induce correctly; guard rejects a crafted spurious lookup).
- Stability guard: solve requires no abstention on test inputs AND identical predictions from every leave-one-out re-induction.

## Result
- **Guarded union 1/50 (the raw BFS control's single task). KILL-CRITERION FIRED (<= 2/50).**
- New families: **zero new solves even unguarded** (unguarded stayed at 3 = v2's tasks). ARC-2: 0/30 all arms.
- Guard autopsy: rejected 3/3 — `6df30ad6` correctly (abstain: lookup didn't cover test input), `ae58858e` and `cd3c21df` (both actually correct) via `loo_disagree`: re-induction from n-1 pairs picks different-but-plausible rules whose test predictions differ. The pre-registered known risk materialized in full.

## Reading
1. **Family plateau is real.** Each hand-built family is narrow; the dev split's remaining tasks need composed, relational, generative reasoning — exactly the compositional gap the Living Survey identifies. Adding families one at a time is a losing race against task diversity.
2. **LOO agreement is the wrong verifier for discrete rules.** With 2-4 train pairs, rule identity is underdetermined; equally-consistent rules diverge on test. (CompressARC sidesteps this: a continuous MDL objective integrates over hypotheses instead of committing to one.)
3. Even ignoring the guard (v2 definition), Option A peaked at 4/50 train-consistent / 3/50 test-correct with sharply diminishing returns.

## Decision
- **KILL per the pre-registered rule. Option B — neural per-task substrate (CompressARC-style MDL) — becomes the default next step**, as pre-registered in H7-v2/v3.
- Salvage: segmentation/feature machinery (front-end for later stages), the ~1000x cost observation for induction vs search, and the negative result on LOO-stability verification.
- Cost note for Option B: ~2.1 s/step locally => ~50-70 min/task at 1500-2000 steps on the 3070 Ti; a 50-task dev-split run is ~2+ GPU-days local, a 10-task subset is an overnight job; bulk belongs on cloud.
