"""Shortest-program search for VNR Stage 1.

Breadth-first search over the JOINT state of all train input grids, ordered by
program token count (a minimum-description-length proxy under a uniform token
cost). Each op is applied to every train grid simultaneously; the goal is the
state where every grid equals its train output. States are deduplicated. A
per-task budget caps the number of states evaluated.

The op alphabet is passed in, so library macro-abstractions (each costing one
token but expanding to several primitives) plug in exactly like primitives.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Callable, Optional

import numpy as np

import dsl


@dataclass
class SearchResult:
    solved: bool
    program: list[str]
    nodes: int          # states evaluated (children generated + goal-tested)
    depth: int          # token length of the solution (or -1)
    budget_hit: bool


def _state_key(grids: list[np.ndarray]) -> tuple:
    return tuple(dsl.to_key(g) for g in grids)


def search_task(
    train: list[tuple[np.ndarray, np.ndarray]],
    ops: dict[str, Callable[[np.ndarray], Optional[np.ndarray]]],
    token_names: list[str],
    budget: int = 50_000,
    max_depth: int = 8,
) -> SearchResult:
    inputs = [inp for inp, _ in train]
    outputs = [out for _, out in train]
    out_keys = _state_key(outputs)

    start = [g.copy() for g in inputs]
    if _state_key(start) == out_keys:  # identity already solves it
        return SearchResult(True, [], 0, 0, False)

    visited: set[tuple] = {_state_key(start)}
    queue: deque[tuple[list[str], list[np.ndarray]]] = deque([([], start)])
    nodes = 0

    while queue:
        program, grids = queue.popleft()
        if len(program) >= max_depth:
            continue
        for name in token_names:
            op = ops[name]
            new_grids = []
            valid = True
            for g in grids:
                ng = op(g)
                if ng is None:
                    valid = False
                    break
                new_grids.append(ng)
            if not valid:
                continue

            nodes += 1
            key = _state_key(new_grids)
            new_program = program + [name]
            if key == out_keys:
                return SearchResult(True, new_program, nodes, len(new_program), False)
            if nodes >= budget:
                return SearchResult(False, [], nodes, -1, True)
            if key in visited:
                continue
            visited.add(key)
            queue.append((new_program, new_grids))

    return SearchResult(False, [], nodes, -1, False)


def test_accuracy(program: list[str], test: list[tuple[np.ndarray, np.ndarray]],
                  ops: dict | None = None) -> float:
    """Fraction of test pairs the program reproduces exactly."""
    if not test:
        return float("nan")
    correct = 0
    for inp, out in test:
        pred = dsl.apply_program(program, inp, ops or dsl.PRIMITIVES)
        if dsl.grids_equal(pred, out):
            correct += 1
    return correct / len(test)
