"""Object-centric perception for VNR Stage 3.

Connected-component extraction (same-color, 4-connectivity — the common ARC
convention) plus param-free object-level ops that plug into the Stage-1 search
as ordinary grid -> grid primitives. Pure numpy, no scipy dependency.
"""
from __future__ import annotations

from collections import deque
from typing import Optional

import numpy as np

Grid = np.ndarray


def components(g: Grid) -> list[dict]:
    """Same-color 4-connected components of non-background (non-zero) cells.

    Returns a list of {color, cells, size, bbox} dicts in deterministic order
    (sorted by first cell encountered in row-major scan).
    """
    seen = np.zeros(g.shape, dtype=bool)
    comps: list[dict] = []
    rows, cols = g.shape
    for r in range(rows):
        for c in range(cols):
            if g[r, c] == 0 or seen[r, c]:
                continue
            color = int(g[r, c])
            cells = []
            q = deque([(r, c)])
            seen[r, c] = True
            while q:
                cr, cc = q.popleft()
                cells.append((cr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = cr + dr, cc + dc
                    if 0 <= nr < rows and 0 <= nc < cols and not seen[nr, nc] and g[nr, nc] == color:
                        seen[nr, nc] = True
                        q.append((nr, nc))
            rs = [p[0] for p in cells]
            cs = [p[1] for p in cells]
            comps.append({
                "color": color,
                "cells": cells,
                "size": len(cells),
                "bbox": (min(rs), min(cs), max(rs), max(cs)),
            })
    return comps


def _extremal(comps: list[dict], largest: bool) -> Optional[dict]:
    """Unique largest/smallest component; None on tie (op inapplicable)."""
    if not comps:
        return None
    sizes = sorted((c["size"] for c in comps), reverse=largest)
    if len(sizes) > 1 and sizes[0] == sizes[1]:
        return None  # ambiguous under param-free semantics
    target = sizes[0]
    for c in comps:
        if c["size"] == target:
            return c
    return None


def keep_largest(g: Grid) -> Optional[Grid]:
    comp = _extremal(components(g), largest=True)
    if comp is None:
        return None
    out = np.zeros_like(g)
    for r, c in comp["cells"]:
        out[r, c] = g[r, c]
    return out


def keep_smallest(g: Grid) -> Optional[Grid]:
    comp = _extremal(components(g), largest=False)
    if comp is None:
        return None
    out = np.zeros_like(g)
    for r, c in comp["cells"]:
        out[r, c] = g[r, c]
    return out


def delete_largest(g: Grid) -> Optional[Grid]:
    comp = _extremal(components(g), largest=True)
    if comp is None:
        return None
    out = g.copy()
    for r, c in comp["cells"]:
        out[r, c] = 0
    return out


def delete_smallest(g: Grid) -> Optional[Grid]:
    comp = _extremal(components(g), largest=False)
    if comp is None:
        return None
    out = g.copy()
    for r, c in comp["cells"]:
        out[r, c] = 0
    return out


def crop_largest(g: Grid) -> Optional[Grid]:
    comp = _extremal(components(g), largest=True)
    if comp is None:
        return None
    r0, c0, r1, c1 = comp["bbox"]
    return g[r0 : r1 + 1, c0 : c1 + 1].copy()


def crop_smallest(g: Grid) -> Optional[Grid]:
    comp = _extremal(components(g), largest=False)
    if comp is None:
        return None
    r0, c0, r1, c1 = comp["bbox"]
    return g[r0 : r1 + 1, c0 : c1 + 1].copy()


OBJECT_OPS = {
    "keep_largest": keep_largest,
    "keep_smallest": keep_smallest,
    "delete_largest": delete_largest,
    "delete_smallest": delete_smallest,
    "crop_largest": crop_largest,
    "crop_smallest": crop_smallest,
}
