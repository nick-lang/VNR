# 2026-06-11 — Stage 5b: addressable (retrieval-gated) weight memory (H10)

- **PoC:** `experiments/poc-vnr-s5-memory/` (`s5b_runner.py`, dispatched by `runpod_queue.py --stage 5b`)
- **Hypothesis:** H10 — pre-registered before running: a trial-loss probe (100 steps from each candidate donor's weights, identical RNG seed per candidate, score = mean loss over last 20 steps) selects ONE donor whose weights warm-start the task to a stable solve materially faster than cold init. Accept = median ret/cold steps-to-stable-solve <= 0.5 with >= 10/11 retention; kill = >= 1.0 or <= 8/11. Probe overhead reported, not decision-bearing.
- **Hardware:** RunPod community pod, **5x A40** (owner could deploy 5, not the planned 6 — same hardware class as H9's cold arm, so reusing H9's cold baselines stays clean). Network volume survived the redeploy: all 11 `donor_*.pt` and all 11 banked cold results reused, zero recompute. 24 jobs (11 sel + 11 ret + 2 selfsel), 175 min wall, **~$6.50**.

## Result: KILL-CRITERION FIRED (both conditions)

- **Validity gate PASSED:** both self-retrieval checks ranked the task's own donor #1 of the full 11-pool, with clear margin (`00576224`: 1210 vs 1336 runner-up; `8597cfd7`: 1338 vs 1616). The probe signal is real; the kill is about memory content, not a broken lookup.
- **Median ratio 1.396** (kill bar >= 1.0). **Retention 7/11** (kill bar <= 8). Both worse than the soup (1.222, 8/11). Median full-cost ratio incl. the 1000-step probe: 5.8x (reported per pre-registration).
- Per-task (ret steps / cold steps, censored at 2000; cold = H9's banked A40 baselines):

| task | selected donor | cold | ret (warm) | ratio |
| --- | --- | --- | --- | --- |
| 00576224 | 45737921 | 222 | 310 | 1.40 |
| 15663ba9 | d2acf2cb | 2000 (failed) | 2000 (failed) | 1.00 |
| 1d0a4b61 | d2acf2cb | 158 | 167 | 1.06 |
| 45737921 | cd3c21df | 62 | 1599 | **25.79** |
| 6df30ad6 | d2acf2cb | 541 | 2000 (lost) | 3.70 |
| 8597cfd7 | cd3c21df | 138 | 153 | 1.11 |
| 903d1b4a | d2acf2cb | 480 | 662 | 1.38 |
| ae58858e | d2acf2cb | 229 | 326 | 1.42 |
| cd3c21df | 45737921 | 2000 (failed) | 2000 (failed) | 1.00 |
| d2acf2cb | 45737921 | 517 | 2000 (lost) | 3.87 |
| ef26cbf6 | d2acf2cb | 186 | 298 | 1.60 |

(`15663ba9`/`cd3c21df` failed in BOTH arms — the known A40 cross-hardware caveat from H9; censored, not evidence either way.)

## Reading

1. **Zero wins.** Not one task trained faster from its best-fitting foreign donor than from random init. The soup at least had three large wins; best-single-donor has none, plus one catastrophic 25.8x slowdown and two outright losses. Selection was the natural fix for the soup's corruption — it fixed nothing.
2. **Retrieval collapsed onto "universal donors," not families.** `d2acf2cb` was selected by 6/11 tasks, `45737921` by 3, `cd3c21df` by 2. The pre-registered family-clustering probe failed: `6df30ad6` did NOT pick its Stage-3b family pair `cd3c21df`. Among foreign donors the trial-loss probe finds "generically adaptable weights," because there is no task-similarity signal to find.
3. **The combined H9+H10 inference (the branch-closer):** the soup's wins must have come from the AVERAGING itself — structure distributed across donors acting as a regularizer — not from any individual donor's content. A whole trained model is the wrong unit of memory: donor weights at blob granularity are task-specialized monoliths, and no addressing scheme over monoliths can rescue that.
4. **The von Neumann analogy sharpened, not weakened.** We built an addressable memory and the addressing worked (self-retrieval passed). What is stored in the cells is not reusable *program*; it is baked-in *data*. The memory-content question — what unit of structure IS reusable across tasks — is now the live one, and it points at parts, not wholes: modules/layers, latents, or the symbolic macros Stage 1 already validated.

## Decision

- **KILL H10** per the pre-registered rule. Recorded in `ledger/hypotheses.md`, `ledger/results.md`, checklist, plan.
- **Gate consequences:** Stage 5c (H11, learned addressing — gated on H10 accept) CLOSED; Stage 5d (H12, blob library at scale) CLOSED; Stage 5e (concept-level decomposition) survives as the only possible form of weight-space memory but is DEFERRED per the owner's standing no-premature-memory-optimization direction.
- **Program returns to the remaining architecture slots:** Stage 6 (TTT-as-MDL), Stage 2 (proposer, needs redefinition for the neural substrate), Stage 7 (integrated loop).
- Artifacts banked locally: `s5_artifacts/job5b_*.json` (24), `s5_artifacts/stage5b_summary.json` (includes the full 11x10 probe-score matrix in the `sel_*` files for any future encoder work).
