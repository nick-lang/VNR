# PoC-VNR-S5 — Cross-task weight memory (H9): LOO weight soup

First non-reproduction stage. Tests whether CompressARC transformation
weights (shape-identical across tasks; latents are task-shaped and never
transferred) carry reusable cross-task structure: warm-start each of the 11
H8-solved tasks from the element-wise average of the other 10 donors' trained
weights and compare steps-to-stable-solve against cold runs on the same
hardware. Pre-registration: `ledger/hypotheses.md` (H9).

## Layout
- `transfer.py` — extract / average / load transformation weights (CompressARC unmodified)
- `local_runner.py` — resumable single-GPU queue (29 banked jobs, `--status`, `--only`)
- `runpod_queue.py` — multi-GPU dispatcher over the same job list (see `RUNPOD.md`)
- `modal_app.py` — earlier Modal variant (unused after the compute pivot)
- `smoke_transfer.py` — machinery validation (run before any GPU spend)

## Result — KILL H9 (pre-registered rule; both conditions fired)
See [stage5_result.json](stage5_result.json) and the notebook entry
`experiments/notebook/2026-06-11-stage5-weightsoup.md`.

- Validity gate PASSED: same-task warm restarts re-solved in 61 / 151 steps.
- Median warm/cold ratio **1.222** (accept needed <= 0.5); retention **8/11**
  (accept needed >= 10/11); probes on unsolved tasks 0/5.
- The informative part: the soup UNLOCKED `cd3c21df` (cold-failed -> solved at
  step 749) and sped up `6df30ad6` (0.31x) and `903d1b4a` (0.57x), while
  destroying two tasks cold solves easily. Transferable structure exists;
  averaging corrupts it. Next mechanism candidate: retrieval-gated donor
  selection (addressable memory) — H10, owner decision pending.

Run: RunPod 6x A40, 29 jobs, 263 min wall, ~$11.60.
