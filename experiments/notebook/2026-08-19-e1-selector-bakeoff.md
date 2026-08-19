# 2026-08-19 — E1 selector bake-off (banked phase + capture runs)

- **PoC:** `experiments/poc-vnr-s6-ttc/` (`e1_selector_bakeoff.py`, `e1b_runner.py`, `e1b_eval.py`)
- **Hypothesis:** none numbered (write-up prep; scope + metrics pre-registered in `e1b_runner.py`'s docstring before launch)
- **Hardware:** local RTX 5090, 3-way workers (worker-count sweep run first: 1/2/3/4-way -> 0.81/1.33/1.42/1.44 aggregate steps/s; 3 chosen)

## Setup

E1-A (banked, $0): retrospective evaluation of every selector the banked S6 scalars
support. E1-B (34 capture jobs, 44k steps, ~13 h wall across owner pauses and one
session death; claims-based queue survived all of it): re-run a pre-registered
scope — 4 solve-relevant trios, 2 seed-churn pairs, 6 never-solved trios (first-6
rule, no cherry-picking) — banking full pick histories, top-2 grids, vote margins,
and loss curves. 30 of the 34 configs duplicate banked S6 configs exactly
(task/seed/steps/hardware/torch), giving a same-config reproducibility readout.

## Results

1. **Loss-level scoring is refuted, full stop.** E1-A's weak-n hint (final_loss
   6/8 vs tail_loss 4/6) REVERSED on fresh draws: final_loss 0/3, tail_loss 0/3
   on E1-B's informative groups. Combined with H10 (probe-loss) and H15
   (tail-loss anti-correlation), no loss-derived scalar has ever picked a solver
   above chance in this substrate.
2. **Trajectory-derived signals beat loss signals:** within-run vote margin 2/3,
   trailing pick stability 2/3 (both miss the same case, `6df30ad6`, where the
   losing run was more confident). Small n, consistent direction.
3. **Agreement voting works where solvers exist, and its failure mode is now
   measured:** on the only solve-relevant task with any solving run this draw
   (`73182012`, 2/3 runs agreeing on the truth) the modal answer was correct; on
   the never-solved precision arm, 2/6 tasks had >=2 runs agreeing on the same
   WRONG answer (`08573cc6` 2 votes, `2697da3f` 3/3 votes!). Agreement carries a
   real false-positive rate; any deployment must budget for confidently-wrong
   consensus.
4. **Same-config solve flips at scale (the run-stochasticity capstone):** 5 of
   the 7 duplicated configs that solved in S6 failed to re-solve (`a_981571dc`,
   `a_be03b35f`, `a_e66aafb8`, `b_be03b35f_s2`, `b_e66aafb8_s1`); only the two
   `73182012` b-runs reproduced their solves. Identical protocol, hardware, and
   seed — the flip is pure execution nondeterminism compounding into different
   basins. Meanwhile the churn arm solved `c_00576224_s0` and `c_6df30ad6_s1`
   fresh. Updated 232-run coverage table: fringe p^ now 0.14-0.67
   (`981571dc` 1/7; `be03b35f`/`e66aafb8` 2/7; `73182012` 4/7; `00576224`/
   `6df30ad6` 4/6).
5. The draw was UNLUCKY on the solve-relevant arm (3 of 4 tasks produced zero
   solving runs), which capped informative-group counts at 3 — itself a coverage
   datum consistent with the fringe p^ estimates.

## Decision

- Loss scorers: closed (three independent refutations: H10, H15, E1).
- Live selector design for H16: agreement/consistency + trajectory confidence
  (vote margin, pick stability), never loss levels; the never-arm false-positive
  rate must be a pre-registered metric.
- Write-up: all `[E1B: ...]` slots filled from these numbers; the same-config
  flip readout upgrades claim 2 from "seed-stochastic" to "run-stochastic" with
  direct evidence.
