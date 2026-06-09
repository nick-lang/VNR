# PoC-A — Reproduce the shoulders (Stage 0)

Establish working, understood baselines and a cost yardstick before building anything new. See [../../docs/vnr-build-test-plan.md](../../docs/vnr-build-test-plan.md) Stage 0 and the checklist [../../docs/vnr-checklist.md](../../docs/vnr-checklist.md).

## Baselines

### CompressARC (runnable here)
Zero-pretraining, per-task MDL/compression solver. ~12-20 min/task on a single ~8 GB GPU.

- Harness: [run_compressarc_task.py](run_compressarc_task.py) — trains one task headlessly and reports pass@2 + wall-clock.
- Data: bundled in `references/CompressARC/dataset/` (ARC-AGI-1, Kaggle-combined format).
- Dev split: `data/dev_split_arc1.json` (50 ARC-AGI-1 eval tasks).

Real baseline needs a CUDA build of torch (the global env is CPU-only). Recommended, in a dedicated venv:

```bash
python -m venv .venv-carc
.\.venv-carc\Scripts\Activate.ps1          # Windows PowerShell
pip install -r references/CompressARC/requirements.txt   # torch 2.5.1, numpy, matplotlib, tqdm
# If that torch is CPU-only, install a CUDA build matching the driver, e.g.:
# pip install torch==2.5.1 --index-url https://download.pytorch.org/whl/cu124
python experiments/poc-a-baselines/run_compressarc_task.py --task <id> --split evaluation --steps 2000
```

Quick functional smoke test (no GPU, few steps — validates the harness, not performance):

```bash
python experiments/poc-a-baselines/run_compressarc_task.py --task <id> --split evaluation --steps 20 --device cpu
```

### TRM (deferred to cloud)
Tiny Recursive Model (~7M params). Per its README, full ARC-AGI-1 training needs ~4 H100s for ~3 days — not feasible on the local 8 GB GPU. Deferred; revisit with cloud compute. The architecture (recursive answer/latent refinement) still informs the VNR proposer design.

## Outputs
Record runs in the notebook entry under `experiments/notebook/` and add rows to `ledger/results.md`.
