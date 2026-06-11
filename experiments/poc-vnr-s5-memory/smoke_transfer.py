"""Local smoke test for the H9 transfer machinery (no cloud, tiny step counts).

Checks, on two real ARC tasks with different grid shapes:
  1. extract -> load round-trip is exact (same task);
  2. cross-task load works (shapes are task-independent) and changes the
     recipient's transformation weights;
  3. latents are NOT touched by a cross-task load;
  4. averaging two donors gives the element-wise mean;
  5. a few training steps run after a warm load (optimizer compatibility).

Usage:  python experiments/poc-vnr-s5-memory/smoke_transfer.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CARC = REPO / "references" / "CompressARC"
sys.path.insert(0, str(Path(__file__).resolve().parent))

import torch

torch.set_default_dtype(torch.float32)
torch.set_default_device("cuda" if torch.cuda.is_available() else "cpu")
os.chdir(CARC)
sys.path.insert(0, str(CARC))
import arc_compressor  # noqa: E402
import preprocessing  # noqa: E402
import solution_selection  # noqa: E402
import train  # noqa: E402
import transfer  # noqa: E402


def flat_tensors(blob):
    out = []

    def walk(n):
        if isinstance(n, torch.Tensor):
            out.append(n)
        elif isinstance(n, list):
            for c in n:
                walk(c)

    for attr in transfer.TRANSFER_ATTRS:
        walk(blob[attr])
    return out


def main() -> None:
    task_a, task_b = preprocessing.preprocess_tasks("evaluation", ["00576224", "8597cfd7"])
    model_a = arc_compressor.ARCCompressor(task_a)
    model_b = arc_compressor.ARCCompressor(task_b)

    blob_a = transfer.extract_weights(model_a)
    blob_b = transfer.extract_weights(model_b)
    fa, fb = flat_tensors(blob_a), flat_tensors(blob_b)
    assert len(fa) == len(fb), "transformation weight structure differs across tasks"
    assert all(x.shape == y.shape for x, y in zip(fa, fb)), "shape mismatch across tasks"
    print(f"[1] structure identical across tasks: {len(fa)} tensors")

    # round-trip exactness
    rt = transfer.from_bytes(transfer.to_bytes(blob_a))
    transfer.load_weights(model_a, rt)
    assert all(torch.equal(x, y) for x, y in zip(flat_tensors(transfer.extract_weights(model_a)), fa))
    print("[2] extract -> bytes -> load round-trip exact")

    # cross-task load changes b's weights, leaves latents alone
    lat_before = [m.detach().clone() for m, _ in _posterior_means(model_b)]
    transfer.load_weights(model_b, blob_a)
    fb2 = flat_tensors(transfer.extract_weights(model_b))
    assert all(torch.equal(x, y) for x, y in zip(fb2, fa)), "cross-task load incomplete"
    lat_after = [m.detach().clone() for m, _ in _posterior_means(model_b)]
    assert all(torch.equal(x, y) for x, y in zip(lat_before, lat_after)), "latents were modified!"
    print("[3] cross-task load exact; latents untouched")

    # averaging
    soup = transfer.average_weights([blob_a, blob_b])
    fs = flat_tensors(soup)
    ok = all(torch.allclose(s, (x.float() + y.float()) / 2, atol=1e-6)
             for s, x, y in zip(fs, fa, fb))
    assert ok, "average is not the element-wise mean"
    print("[4] weight soup = element-wise mean")

    # a few optimizer steps after warm load
    model_c = arc_compressor.ARCCompressor(task_b)
    transfer.load_weights(model_c, soup)
    opt = torch.optim.Adam(model_c.weights_list, lr=0.01, betas=(0.5, 0.9))
    logger = solution_selection.Logger(task_b)
    for step in range(5):
        train.take_step(task_b, model_c, opt, step, logger)
    print(f"[5] 5 training steps after warm load OK (loss={logger.loss_curve[-1]:.1f})")
    print("SMOKE PASS")


def _posterior_means(model):
    pairs = []

    def walk(n):
        if isinstance(n, list):
            if len(n) == 2 and isinstance(n[0], torch.Tensor):
                pairs.append((n[0], n[1]))
            else:
                for c in n:
                    walk(c)

    walk(model.multiposteriors.data)
    return pairs


if __name__ == "__main__":
    main()
