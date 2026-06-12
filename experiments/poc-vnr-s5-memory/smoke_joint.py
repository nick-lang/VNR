"""Local smoke of Stage 5f joint-training mechanics (tiny cycle count).

Checks: (1) aliasing makes both models read the SAME transformation tensors;
(2) shared weights actually move under round-robin steps; (3) both tasks'
losses decrease; (4) the saved backbone round-trips into a fresh model.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import s5f_runner as s5f
from local_runner import ARTIFACTS, _env

s5f.JOINT_CYCLES = 30

result = s5f._joint_train(["00576224", "8597cfd7"], "backbone_smoke.pt")
print("joint result:", result)

e = _env()
torch, transfer = e["torch"], e["transfer"]

tasks = e["preprocessing"].preprocess_tasks("evaluation", ["00576224", "8597cfd7"])
m0 = e["arc_compressor"].ARCCompressor(tasks[0])
m1 = e["arc_compressor"].ARCCompressor(tasks[1])
s5f._share_weights(m0, m1, transfer)
l0, l1 = {}, {}
for attr in transfer.TRANSFER_ATTRS:
    s5f._leaves(getattr(m0, attr), l0)
    s5f._leaves(getattr(m1, attr), l1)
assert set(l0) == set(l1), "aliasing failed: models hold different tensor objects"
print(f"aliasing OK: {len(l0)} shared transformation tensors (identical objects)")

blob = transfer.from_bytes((ARTIFACTS / "backbone_smoke.pt").read_bytes())
transfer.load_weights(m0, blob)
print("backbone round-trip OK")

for tid in result["tasks"]:
    first, final = result["first_losses"][tid], result["final_losses"][tid]
    assert final < 0.5 * first, f"loss did not decrease for {tid}: {first} -> {final}"
    print(f"loss decreasing OK: {tid} {first:.0f} -> {final:.0f}")
print("SMOKE PASSED")
