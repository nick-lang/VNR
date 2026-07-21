# 2026-07-20 — Stage 6: restart diversity + label-free MDL selection (H15)

**Hypothesis (pre-registered 2026-07-07, `ledger/hypotheses.md`):** on the 39 H8-unsolved dev tasks, two 1000-step CompressARC runs from different seeds with label-free MDL selection beat one 2000-step run at matched compute.

**Verdict: KILL per the pre-registered rule.** Arm A (1x2000, seed 0) solved 3/39; arm B (2x1000, seeds 1-2, tail-loss selection) solved 2/39.

## Setup
- Local RTX 5090, torch 2.11+cu128, `experiments/poc-vnr-s6-ttc/s6_runner.py`, 4-way claims-based workers.
- 126 jobs: 39 x (a: 2000 steps seed 0; b_s1/b_s2: 1000 steps seeds 1/2) + 9 seed-sensitivity checks on the banked-solved tasks.
- 169.3 GPU-h summed job time, $0. Run spanned 07-07 -> 07-20 across owner pauses, one IDE-session death, and one machine reboot — the banked/resumable queue lost only in-flight jobs each time.

## Numbers
| Readout | Result |
| --- | --- |
| Arm A solves | 3/39: `981571dc`, `be03b35f`, `e66aafb8` |
| Arm B solves (selected) | 2/39: `73182012`, `e66aafb8` |
| Union-of-B oracle | 3/39: `73182012`, `be03b35f`, `e66aafb8` |
| Selector accuracy | 1/2 |
| Seed-1 check on 9 banked solves | 7/9 retained; lost `00576224`, `6df30ad6` |
| New-to-substrate solves across all runs | 4: `73182012`, `981571dc`, `be03b35f`, `e66aafb8` (dev union 11 -> 15/50) |

## Findings
1. **No compute-allocation free lunch.** Union-of-B equals arm A exactly: even a perfect selector would only TIE longer convergence at matched compute. Some tasks need the diversity (`73182012`: both short seeds solved by step ~150, the 2000-step run never did), others need the convergence (`981571dc`: solved at step 742, beyond the short runs' budget). The two effects cancel at this K and budget.
2. **MDL tail loss is refuted as a run selector.** Accuracy 1/2, and in 3 of 4 solve cases the solving run had the HIGHER mean tail loss (e.g. `be03b35f`: solver 127.9 vs non-solver 87.1; on `73182012` the one run that did NOT solve had the lowest loss of the trio). Lower description length of the joint code does not indicate a solving basin — consistent with H10, where loss-based donor scoring was similarly uninformative. Absolute loss scale is task-dominated and, within a task, basin quality is not loss-ordered at these budgets.
3. **The headline finding is seed stochasticity, not the arm comparison.** Arm A replicates the H8 protocol exactly (2000 steps, seed 0) on new hardware and solved 3 tasks H8-on-L40S did not; the seed-1 re-check lost 2 of 9 banked solves. The substrate's solve set churns +-20-30% per re-roll. Consequences: (a) H8's "11/50" is one draw from a distribution — seed-marginalized solve probability is the honest metric from here on; (b) any cross-arm or cross-stage comparison must hold seeds fixed or marginalize; (c) re-rolls genuinely grow pass@k coverage (11 -> 15/50 here) but ARC's pass@2 budget makes that unusable without a working label-free selector, which we do not have.

## Decisions
- **KILL H15** per the pre-registered rule; Stage 6 (test-time compute allocation) closes.
- Voting/train-pair-consistency selection across seeds is a candidate future H16 (new design, not an H15 tweak) — deferred, not pre-registered.
- Live slots now: Stage 2 (proposer redefinition) and the substrate-external memory routes (symbolic library, concept memory). Both inherit the seed-marginalization requirement.
