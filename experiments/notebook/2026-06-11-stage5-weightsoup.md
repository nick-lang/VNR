# 2026-06-11 — Stage 5: cross-task weight memory via LOO soup (H9)

- **PoC:** `experiments/poc-vnr-s5-memory/`
- **Hypothesis:** H9 — pre-registered before running (LOO weight-soup warm-start; accept = median warm/cold steps-to-stable-solve <= 0.5x with >= 10/11 retention; kill = >= 1.0x or <= 8/11).
- **Hardware:** RunPod community pod, 6x A40 ($2.65/hr), all 29 jobs in one queue (`runpod_queue.py`), 263 min wall, **~$11.60 actual**. Both arms same hardware.
- **Compute history (honest):** Modal unusable (owner billing); local 3070 Ti started piece 1 (~1.2 s/step) but owner ruled long local runs out; pivoted to RunPod. Local piece 1's sanity gates agreed with the pod's (cross-hardware validation sample).

## Result: KILL-CRITERION FIRED (both conditions)
- **Validity gate passed:** same-task warm restarts re-solved in 61 / 151 steps (bar ~200) — transfer mechanics verified, so the kill is a real negative result, not a broken pipeline.
- **Median ratio 1.222** (no speedup; kill bar >= 1.0). **Retention 8/11** (kill bar <= 8). **Probes 0/5.**
- Per-task ratios (warm steps / cold steps, censored at 2000):

| task | cold | warm | ratio |
| --- | --- | --- | --- |
| 00576224 | 222 | 2000 (lost) | 9.01 |
| 15663ba9 | 2000 (failed) | 2000 (failed) | 1.00 |
| 1d0a4b61 | 158 | 193 | 1.22 |
| 45737921 | 62 | 159 | 2.57 |
| 6df30ad6 | 541 | 168 | **0.31** |
| 8597cfd7 | 138 | 164 | 1.19 |
| 903d1b4a | 480 | 274 | **0.57** |
| ae58858e | 229 | 399 | 1.74 |
| cd3c21df | 2000 (failed) | 749 (solved!) | **0.37** |
| d2acf2cb | 517 | 2000 (lost) | 3.87 |
| ef26cbf6 | 186 | 229 | 1.23 |

## Reading
1. **The soup both transmits and corrupts.** Three large wins — including `cd3c21df`, which cold FAILED on this hardware and the soup unlocked — prove transferable cross-task structure exists in the transformation weights. Two outright losses prove naive averaging destroys task-idiosyncratic structure other tasks depend on. Net: zero median benefit.
2. **Structure clusters by family.** The soup's biggest wins (`6df30ad6`, `cd3c21df`) are precisely the tasks the Stage 3b symbolic object-substrate could express. Whatever those tasks share, several donors carry it.
3. **Cross-hardware nondeterminism is real:** A40 reproduced 9/11 of the L40S solves (`15663ba9`, `cd3c21df` failed cold). All future comparisons must keep arms on one hardware type (this run did).
4. Per the pre-registered guardrail: this kills the weight-SOUP mechanism, not the memory thesis. The win/loss heterogeneity is the strongest argument yet for **addressable** memory — select the right donor(s) per task instead of smearing all of them together. That is the von Neumann thesis in miniature, and the natural H10.

## Decision
- **KILL H9** per the pre-registered rule. Recorded in `ledger/hypotheses.md`, `ledger/results.md`, checklist, plan.
- Candidate H10 (to be pre-registered before any run): retrieval-gated weight memory — pick the nearest donor (task-feature similarity or quick trial-loss probe) instead of the average; same LOO design, same bar, reuse of this stage's banked donors cuts the cost roughly in half.
