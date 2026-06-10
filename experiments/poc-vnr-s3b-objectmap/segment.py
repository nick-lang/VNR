"""Segmentation + object features for VNR Stage 3b.

Two segmentation modes (the solver tries both):
  color4 — same-color, 4-connected components (classic ARC objects)
  multi8 — any-nonzero, 8-connected components (multi-color shapes)

Each object carries the features used by rule induction. Pure numpy.
"""
from __future__ import annotations

from collections import Counter, deque
from dataclasses import dataclass, field

import numpy as np

Grid = np.ndarray

NEIGH4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
NEIGH8 = NEIGH4 + ((1, 1), (1, -1), (-1, 1), (-1, -1))


@dataclass
class Obj:
    cells: list[tuple[int, int]]
    colors: dict[tuple[int, int], int]
    color: int                      # dominant color
    size: int = 0
    bbox: tuple[int, int, int, int] = (0, 0, 0, 0)
    shape_key: tuple = ()
    # grid-context features (filled by segment()):
    size_rank: int = 0              # dense rank by size, desc (1 = biggest)
    is_largest: bool = False        # unique max size
    is_smallest: bool = False       # unique min size
    touches_border: bool = False
    shape_count: int = 0            # objects in grid sharing shape_key
    color_count: int = 0            # objects in grid sharing dominant color
    meta: dict = field(default_factory=dict)


def _flood(g: Grid, mode: str) -> list[Obj]:
    rows, cols = g.shape
    seen = np.zeros(g.shape, dtype=bool)
    neigh = NEIGH4 if mode == "color4" else NEIGH8
    objs: list[Obj] = []
    for r in range(rows):
        for c in range(cols):
            if g[r, c] == 0 or seen[r, c]:
                continue
            color0 = int(g[r, c])
            q = deque([(r, c)])
            seen[r, c] = True
            cells = []
            while q:
                cr, cc = q.popleft()
                cells.append((cr, cc))
                for dr, dc in neigh:
                    nr, nc = cr + dr, cc + dc
                    if not (0 <= nr < rows and 0 <= nc < cols) or seen[nr, nc] or g[nr, nc] == 0:
                        continue
                    if mode == "color4" and int(g[nr, nc]) != color0:
                        continue
                    seen[nr, nc] = True
                    q.append((nr, nc))
            colors = {(cr, cc): int(g[cr, cc]) for cr, cc in cells}
            dominant = Counter(colors.values()).most_common(1)[0][0]
            objs.append(Obj(cells=cells, colors=colors, color=dominant))
    return objs


def segment(g: Grid, mode: str) -> list[Obj]:
    objs = _flood(g, mode)
    rows, cols = g.shape
    for o in objs:
        o.size = len(o.cells)
        rs = [p[0] for p in o.cells]
        cs = [p[1] for p in o.cells]
        o.bbox = (min(rs), min(cs), max(rs), max(cs))
        r0, c0 = o.bbox[0], o.bbox[1]
        o.shape_key = tuple(sorted((r - r0, c - c0) for r, c in o.cells))
        o.touches_border = any(r in (0, rows - 1) or c in (0, cols - 1) for r, c in o.cells)

    sizes = sorted({o.size for o in objs}, reverse=True)
    size_counts = Counter(o.size for o in objs)
    shape_counts = Counter(o.shape_key for o in objs)
    color_counts = Counter(o.color for o in objs)
    for o in objs:
        o.size_rank = sizes.index(o.size) + 1
        o.is_largest = o.size == sizes[0] and size_counts[o.size] == 1
        o.is_smallest = o.size == sizes[-1] and size_counts[o.size] == 1
        o.shape_count = shape_counts[o.shape_key]
        o.color_count = color_counts[o.color]
    return objs


def render_crop(o: Obj, variant: str, g: Grid) -> Grid:
    """Crop of an object: 'cells' = object cells on 0 background; 'bbox' = raw grid slice."""
    r0, c0, r1, c1 = o.bbox
    if variant == "bbox":
        return g[r0 : r1 + 1, c0 : c1 + 1].copy()
    out = np.zeros((r1 - r0 + 1, c1 - c0 + 1), dtype=g.dtype)
    for (r, c), v in o.colors.items():
        out[r - r0, c - c0] = v
    return out
