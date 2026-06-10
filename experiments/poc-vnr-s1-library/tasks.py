"""Tasks for VNR Stage 1.

Two sources:
1. Synthetic compositional benchmark: ground-truth programs are concatenations
   of recurring "concept" sub-routines, so reuse genuinely exists and a learned
   library should transfer. Tasks are guaranteed solvable by the DSL.
2. ARC-AGI-1 dev split loader: a coverage reality-check (most won't be solvable
   by this tiny DSL; that's expected and reported).
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

import dsl

REPO = Path(__file__).resolve().parents[2]
DEV_SPLIT = REPO / "data" / "dev_split_arc1.json"
ARC1_EVAL = REPO / "data" / "arc-agi-1" / "data" / "evaluation"

# Recurring concept sub-routines (sequences of primitives). Shared structure
# across tasks is exactly what a library is supposed to capture.
CONCEPTS: dict[str, list[str]] = {
    "quadmir": ["mirror_h", "mirror_v"],
    "rotmir": ["rot90", "mirror_h"],
    "scaleflip": ["scale2", "flip_v"],
    "transtile": ["transpose", "tile_h2"],
    "rot2": ["rot90", "rot90"],
    "scalemir": ["scale2", "mirror_h"],
}


@dataclass
class Task:
    name: str
    train: list[tuple[np.ndarray, np.ndarray]]
    test: list[tuple[np.ndarray, np.ndarray]]
    gt_program: list[str] | None = None
    meta: dict = field(default_factory=dict)


def _random_grid(rng: np.random.Generator, max_side: int = 3) -> np.ndarray:
    h = int(rng.integers(2, max_side + 1))
    w = int(rng.integers(2, max_side + 1))
    n_colors = int(rng.integers(2, 4))  # palette size incl. background
    g = rng.integers(0, n_colors, size=(h, w))
    if np.count_nonzero(g) == 0:  # avoid all-background
        g[0, 0] = 1
    return g.astype(int)


def _make_pair(rng, program, max_side):
    inp = _random_grid(rng, max_side)
    out = dsl.apply_program(program, inp)
    if out is None:
        return None
    if np.array_equal(inp, out):  # skip trivial identity pairs
        return None
    return inp, out


def gen_synthetic(
    n_tasks: int,
    seed: int,
    n_concepts_range: tuple[int, int] = (2, 3),
    n_train: int = 3,
    n_test: int = 2,
    max_side: int = 3,
) -> list[Task]:
    rng = np.random.default_rng(seed)
    concept_names = list(CONCEPTS)
    tasks: list[Task] = []
    attempts = 0
    while len(tasks) < n_tasks and attempts < n_tasks * 200:
        attempts += 1
        k = int(rng.integers(n_concepts_range[0], n_concepts_range[1] + 1))
        chosen = [concept_names[int(rng.integers(0, len(concept_names)))] for _ in range(k)]
        program: list[str] = []
        for c in chosen:
            program.extend(CONCEPTS[c])
        pairs = []
        ok = True
        for _ in range(n_train + n_test):
            p = _make_pair(rng, program, max_side)
            if p is None:
                ok = False
                break
            pairs.append(p)
        if not ok:
            continue
        tasks.append(
            Task(
                name=f"syn_{len(tasks):03d}",
                train=pairs[:n_train],
                test=pairs[n_train:],
                gt_program=program,
                meta={"concepts": chosen, "len": len(program)},
            )
        )
    if len(tasks) < n_tasks:
        raise RuntimeError(f"only generated {len(tasks)}/{n_tasks} tasks; loosen constraints")
    return tasks


def load_arc_dev(limit: int | None = None) -> list[Task]:
    ids = json.loads(DEV_SPLIT.read_text())["task_ids"]
    if limit:
        ids = ids[:limit]
    tasks: list[Task] = []
    for tid in ids:
        f = ARC1_EVAL / f"{tid}.json"
        if not f.exists():
            continue
        obj = json.loads(f.read_text())
        train = [(np.array(p["input"]), np.array(p["output"])) for p in obj["train"]]
        test = [
            (np.array(p["input"]), np.array(p["output"]))
            for p in obj["test"]
            if "output" in p
        ]
        tasks.append(Task(name=tid, train=train, test=test))
    return tasks
