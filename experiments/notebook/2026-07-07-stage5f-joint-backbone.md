# 2026-07-07 — Stage 5f: jointly trained shared backbone (H14)

- **PoC:** PoC-VNR-S5f
- **Hypothesis:** H14 (see `ledger/hypotheses.md`, incl. 2026-07-06 amendments)
- **Hardware:** local RTX 5090 (32 GB), Windows/WDDM, 4 parallel worker processes on one GPU (~1.36x aggregate vs serial; decision metric is steps, so concurrency is comparability-neutral)
- **Seed(s):** 0 (per job, as pre-registered)
- **Exact command:** `python experiments/poc-vnr-s5-memory/s5f_runner.py --worker` (x4), then `--status`, `--deltas`
- **Protocol deviations:** torch 2.11.0+cu128 (pinned 2.5.1 predates Blackwell/sm_120); CompressARC re-cloned at upstream `83a2221` (Jan 2026); cold arm rebased to 5090 per the 2026-07-06 hardware pivot (A40 pods gone).

## Setup

3 folds over the 9 A40-cold-solvable tasks. Per fold: joint-train one set of shared transformation weights across the 6 non-fold tasks (per-task latents separate, round-robin, 1000 cycles); warm-start each held-out task from its fold's backbone (fresh latents, 1000 steps). Cold arm = same 11 tasks re-run cold at 1000 steps on the same GPU. Validity gate: each backbone warm-starts one of its OWN training tasks and must re-solve stably within ~200 steps. Exploratory: all-9 backbone -> 3 H8-unsolved probes. New secondary readout: per-task delta (jret final weights − backbone), pairwise cosines.

## Metric (pre-registered)

Gate first; if valid, ACCEPT if median(jret steps-to-stable-solve / cold) <= 0.5 AND retention >= 8/9; KILL if median >= 1.0 or retention <= 7/9.

## Result

- **Hardware rebase:** 5090 colds solved 9/11 — the same 9 tasks as the A40 (`15663ba9`, `cd3c21df` failed cold on both). Median cold steps-to-stable-solve: 154-356 range, all well under the 1000-step budget (budget-cut decision revalidated on new hardware).
- **Validity gate FAILED 3/3.** jval_0 (`6df30ad6` from backbone_f0), jval_1/jval_2 (`00576224` from f1/f2): none re-solved in 600 steps. Notably jval_1 reached final loss 99.4 — LOWER than the task's cold-run final loss — while still decoding the wrong solution: the backbone pushes the model into a confident wrong basin.
- **Not plumbing.** Transfer round-trip and tensor-aliasing smokes passed on the new stack; H9's same-task-restart gate validated this exact load path in June; `solved_during_joint` shows tasks solving during joint training itself (fold_1: 4/6). The gate isolates the mechanism: shared weights + fresh latents do not reconstruct solutions the joint model demonstrably had.
- **Descriptive numbers (void, so not decision-bearing):** median jret/cold ratio **3.436**; warm slower than cold on **all 9 tasks** (best 1.026, worst 6.25); retention 6/9 (`00576224`, `6df30ad6`, `d2acf2cb` lost); probes 0/3. Worse than H9's soup (1.222) and H10's retrieval (1.396).
- **Delta geometry (the finding):** pairwise cosine of per-task deltas vs the shared backbone ~= 0 (median 0.0067, min −0.014, max 0.062), norms near-identical (114-121). Task adaptations are mutually orthogonal even from a forced shared basin.
- Cost: ~10.4 h wall, $0. Artifacts: `s5_artifacts/job5f_*.json`, `backbone_f*.pt`, `jretw_*.pt`, `delta_geometry.json`, `stage5f_summary.json`.

## Decision

**VOID per the pre-registered validity rule** — no accept/kill is claimed. But the void is diagnostic, and it converges with H9/H10 into a three-negative record for weight-space memory in this substrate:

1. H9: post-hoc averaging transmits AND corrupts (basin misalignment — later literature-confirmed).
2. H10: addressing works, but no single donor's content is reusable.
3. H14: even a jointly-created shared basin does not hold task knowledge in weights alone — CompressARC's "program" lives in the latent/weight co-adaptation, and adaptation directions across tasks are orthogonal (nothing to amortize).

The positive reading: this cleanly redirects the memory thesis to where the lit pass already pointed — decomposed/parameterized concept memory (Stage 5e; ArcMemo's independent result) and the symbolic library route (Stage 1's accept; Pang's real-ARC validation), not whole-network or backbone weight reuse at 76K-param scale.

**H14b fork (owner decision):** the pre-registered escalation trigger ("H14 marginal or kill") did not fire — H14 is void, and the delta orthogonality undercuts H14b's premise (Reptile seeks a shared adaptation direction; measurement says there is none here). Options: (a) run H14b anyway overnight ($0, closes the loop formally), (b) close the weight-space amortization track and return to Stage 6 (TTT-as-MDL) / Stage 2 (proposer redefinition). **Recommendation: (b) close** — consistent with the owner's standing no-premature-memory-optimization direction.
