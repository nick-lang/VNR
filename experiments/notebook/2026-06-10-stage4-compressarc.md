# 2026-06-10 — Stage 4: CompressARC baseline on the dev split, via Modal (H8)

- **PoC:** `experiments/poc-vnr-s4-neural/` (`modal_app.py`)
- **Hypothesis:** H8 — pre-registered before running (unmodified CompressARC, 2000 steps/task, pass@2, same 50-task dev split and numeric bar as H7).
- **Hardware:** Modal cloud, one L40S per task, up to 10 concurrent. First cloud run of the program.
- **Command:** `modal run experiments/poc-vnr-s4-neural/modal_app.py` (+ `--smoke` cost gate first; `--banked` resume after the billing-cap pause).

## Setup
- Vendored `references/CompressARC` shipped unmodified into the container image; harness mirrors Stage 0's `run_compressarc_task.py` (2000 steps, Adam lr=0.01 betas=(0.5,0.9), pass@2 = top-1/top-2 most-frequent decoded solution vs ground-truth hash).
- Pre-registered cost gate: smoke task `00576224` measured 0.825 s/step => $44.71 list projected for 50 tasks => under the owner's $30 out-of-pocket budget after credits; full fan-out approved.

## Run history (honest record)
1. Full fan-out launched; per-task times ran ~2x the smoke task's (mean ~52 min vs ~27 min) — bigger grids + more examples per task than the smoke task, so the cost projection was optimistic.
2. At 21/50 results, Modal's workspace usage cap ($42.50) froze the app. Owner approved finishing regardless of cost, upgraded the plan; 21 banked results were preserved (`stage4_banked.json`) and the remaining 29 relaunched with `--banked` (no recompute).
3. Resume completed cleanly: 29/29.

## Result
- **11/50 pass@2 (22%) — ACCEPT H8** (bar: >= 5/50 and >= 4x raw control's 1/50; kill <= 2/50). All 11 solves are also pass@1.
- Solved: `00576224 15663ba9 1d0a4b61 45737921 6df30ad6 8597cfd7 903d1b4a ae58858e cd3c21df d2acf2cb ef26cbf6`.
- Matches published CompressARC (~20% on ARC-AGI-1 eval): clean reproduction on our split.
- **Superset of every symbolic solve:** includes all 3 Stage 3b object-map solves — notably `6df30ad6`, which the symbolic rule overfit and CompressARC solves correctly. Raw BFS's `0c786b71` was NOT solved; union across substrates = 12/50.
- **Cost:** 43.3 GPU-hours, ~$84.50 list (~$1.69/task, mean 3118 s, range 1492-7710 s); wall clock ~2.1 h for the 29-task resume at 10-way concurrency. Out-of-pocket lower after plan credits.

## Reading
1. The neural per-task MDL substrate expresses real ARC structure that two iterations of hand-built rules could not (11/50 vs 3/50 test-correct max). The substrate slot in the VNR architecture is filled.
2. The continuous-objective point from Stage 3c held up: where discrete rule identity was brittle (overfit, LOO-unstable), compression integrates over hypotheses — `6df30ad6` is the direct head-to-head case.
3. The defining limitation is now amnesia, by construction: every task trains and discards its own model. ~52 min and ~$1.69 of compute per task, none of it reused. That is the number H9+ (cross-task program memory / amortization) must beat — VNR's actual thesis, and where we stop reproducing published work.

## Decision
- **ACCEPT H8** per the pre-registered rule. Recorded in `ledger/hypotheses.md` and `ledger/results.md`.
- Next: design H9 (cross-task memory on the neural substrate) with its own pre-registration; artifact-saving (per-task weights/latents) to be added to the harness for that work.
