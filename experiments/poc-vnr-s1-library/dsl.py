"""Minimal param-free grid DSL + interpreter for VNR Stage 1.

A grid is a 2D numpy int array with values 0-9 (0 = background). Every primitive
is a total function grid -> grid (or None if the result would exceed MAX_DIM,
in which case the op is treated as inapplicable). Param-free ops keep the search
alphabet finite so breadth-first / shortest-program search is clean.
"""
from __future__ import annotations

from typing import Callable, Optional

import numpy as np

MAX_DIM = 30  # ARC grids never exceed 30x30

Grid = np.ndarray
Op = Callable[[Grid], Optional[Grid]]


def _cap(g: Grid) -> Optional[Grid]:
    """Reject grids that grew past the ARC size cap."""
    if g.shape[0] > MAX_DIM or g.shape[1] > MAX_DIM or g.size == 0:
        return None
    return g


def rot90(g: Grid) -> Optional[Grid]:
    return _cap(np.rot90(g, 1))


def rot180(g: Grid) -> Optional[Grid]:
    return _cap(np.rot90(g, 2))


def rot270(g: Grid) -> Optional[Grid]:
    return _cap(np.rot90(g, 3))


def flip_h(g: Grid) -> Optional[Grid]:
    return _cap(np.fliplr(g))


def flip_v(g: Grid) -> Optional[Grid]:
    return _cap(np.flipud(g))


def transpose(g: Grid) -> Optional[Grid]:
    return _cap(g.T.copy())


def mirror_h(g: Grid) -> Optional[Grid]:
    """Concatenate the grid with its horizontal mirror (width doubles)."""
    return _cap(np.concatenate([g, np.fliplr(g)], axis=1))


def mirror_v(g: Grid) -> Optional[Grid]:
    return _cap(np.concatenate([g, np.flipud(g)], axis=0))


def tile_h2(g: Grid) -> Optional[Grid]:
    return _cap(np.concatenate([g, g], axis=1))


def tile_v2(g: Grid) -> Optional[Grid]:
    return _cap(np.concatenate([g, g], axis=0))


def tile2x2(g: Grid) -> Optional[Grid]:
    return _cap(np.tile(g, (2, 2)))


def scale2(g: Grid) -> Optional[Grid]:
    """Upscale each cell into a 2x2 block."""
    return _cap(np.kron(g, np.ones((2, 2), dtype=g.dtype)))


def crop_content(g: Grid) -> Optional[Grid]:
    """Crop to the bounding box of non-background (non-zero) cells."""
    nz = np.argwhere(g != 0)
    if nz.size == 0:
        return _cap(g)
    (r0, c0), (r1, c1) = nz.min(0), nz.max(0)
    return _cap(g[r0 : r1 + 1, c0 : c1 + 1].copy())


# Ordered alphabet of primitives (order only affects tie-breaking in search).
PRIMITIVES: dict[str, Op] = {
    "rot90": rot90,
    "rot180": rot180,
    "rot270": rot270,
    "flip_h": flip_h,
    "flip_v": flip_v,
    "transpose": transpose,
    "mirror_h": mirror_h,
    "mirror_v": mirror_v,
    "tile_h2": tile_h2,
    "tile_v2": tile_v2,
    "tile2x2": tile2x2,
    "scale2": scale2,
    "crop_content": crop_content,
}


def apply_program(program: list[str], g: Grid, ops: dict[str, Op] | None = None) -> Optional[Grid]:
    """Apply a sequence of primitive op names to a grid, left to right."""
    ops = ops or PRIMITIVES
    cur: Optional[Grid] = g
    for name in program:
        if cur is None:
            return None
        cur = ops[name](cur)
    return cur


def grids_equal(a: Optional[Grid], b: Optional[Grid]) -> bool:
    return a is not None and b is not None and a.shape == b.shape and bool(np.array_equal(a, b))


def to_key(g: Grid) -> tuple:
    """Hashable canonical key for a grid (shape + bytes)."""
    return (g.shape, g.tobytes())
