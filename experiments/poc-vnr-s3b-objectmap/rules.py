"""Per-object rule induction for VNR Stage 3b (the object-mapped substrate).

Two rule families, both verified by exact re-simulation on every train pair:

1. Same-shape per-object fates: each input object -> keep | delete | recolor-to-c,
   where the fate is a function of ONE object feature. Feature keys are tried in
   a fixed simplicity order (an MDL prior); the induced lookup must be
   consistent across all train objects and reproduce every train output.

2. Selection-crop: the output equals one input object's crop. A fixed-order
   predicate list must select exactly one object per train pair, with a
   consistent crop variant.

A rule is a small dict (the "program"); apply() executes it on a new input.
"""
from __future__ import annotations

from typing import Callable, Optional

import numpy as np

import segment as seg

Grid = np.ndarray

MODES = ("color4", "multi8")

# Fate = ("keep",) | ("delete",) | ("color", c)
KEY_FNS: list[tuple[str, Callable[[seg.Obj], object]]] = [
    ("const", lambda o: 0),
    ("color", lambda o: o.color),
    ("is_largest", lambda o: o.is_largest),
    ("is_smallest", lambda o: o.is_smallest),
    ("touches_border", lambda o: o.touches_border),
    ("size", lambda o: o.size),
    ("size_rank", lambda o: o.size_rank),
    ("shape_key", lambda o: o.shape_key),
    ("shape_count", lambda o: o.shape_count),
    ("color_count", lambda o: o.color_count),
]
KEY_LOOKUP = dict(KEY_FNS)

SELECTORS: list[tuple[str, Callable[[list[seg.Obj]], Optional[seg.Obj]]]] = [
    ("is_largest", lambda objs: _unique(objs, lambda o: o.is_largest)),
    ("is_smallest", lambda objs: _unique(objs, lambda o: o.is_smallest)),
    ("unique_color", lambda objs: _unique(objs, lambda o: o.color_count == 1)),
    ("unique_shape", lambda objs: _unique(objs, lambda o: o.shape_count == 1)),
    ("only_touching_border", lambda objs: _unique(objs, lambda o: o.touches_border)),
    ("only_not_touching_border", lambda objs: _unique(objs, lambda o: not o.touches_border)),
]
SELECTOR_LOOKUP = dict(SELECTORS)


def _unique(objs: list[seg.Obj], pred) -> Optional[seg.Obj]:
    hits = [o for o in objs if pred(o)]
    return hits[0] if len(hits) == 1 else None


def _object_fate(o: seg.Obj, out: Grid):
    """Fate of an input object judged by the output cells it occupies; None = complex."""
    vals = {int(out[r, c]) for r, c in o.cells}
    if vals == {0}:
        return ("delete",)
    if all(int(out[r, c]) == v for (r, c), v in o.colors.items()):
        return ("keep",)
    if len(vals) == 1:
        return ("color", vals.pop())
    return None


def _fates_for_pair(inp: Grid, out: Grid, mode: str):
    """(objects, fates) for one same-shape pair, or None if family inapplicable."""
    objs = seg.segment(inp, mode)
    if not objs:
        return None
    covered = {p for o in objs for p in o.cells}
    nz = {(int(r), int(c)) for r, c in np.argwhere(out != 0)}
    if not nz <= covered:
        return None  # output creates cells outside input objects: generative
    fates = []
    for o in objs:
        f = _object_fate(o, out)
        if f is None:
            return None
        fates.append(f)
    return objs, fates


def _apply_fates(inp: Grid, mode: str, key_name: str, mapping: dict) -> Optional[Grid]:
    key_fn = KEY_LOOKUP[key_name]
    out = np.zeros_like(inp)
    for o in seg.segment(inp, mode):
        k = key_fn(o)
        if k not in mapping:
            return None  # unseen key value: rule cannot predict
        fate = mapping[k]
        if fate == ("delete",):
            continue
        for (r, c), v in o.colors.items():
            out[r, c] = v if fate == ("keep",) else fate[1]
    return out


def induce_same_shape(train, mode: str) -> Optional[dict]:
    if not all(inp.shape == out.shape for inp, out in train):
        return None
    per_pair = []
    for inp, out in train:
        fo = _fates_for_pair(inp, out, mode)
        if fo is None:
            return None
        per_pair.append(fo)

    # Collect every consistent key, then choose the smallest mapping (MDL:
    # fewest entries = shortest description). Ties break by KEY_FNS order.
    candidates: list[tuple[int, int, str, dict]] = []
    for order, (key_name, key_fn) in enumerate(KEY_FNS):
        mapping: dict = {}
        ok = True
        for objs, fates in per_pair:
            for o, f in zip(objs, fates):
                k = key_fn(o)
                if mapping.setdefault(k, f) != f:
                    ok = False
                    break
            if not ok:
                break
        if ok:
            candidates.append((len(mapping), order, key_name, mapping))

    for _, _, key_name, mapping in sorted(candidates, key=lambda t: (t[0], t[1])):
        if all(_grid_eq(_apply_fates(inp, mode, key_name, mapping), out) for inp, out in train):
            return {"family": "same_shape_fates", "mode": mode, "key": key_name,
                    "mapping": {repr(k): list(v) for k, v in mapping.items()},
                    "_mapping": mapping}
    return None


def induce_select_crop(train, mode: str) -> Optional[dict]:
    for sel_name, sel in SELECTORS:
        for variant in ("cells", "bbox"):
            ok = True
            for inp, out in train:
                objs = seg.segment(inp, mode)
                chosen = sel(objs) if objs else None
                if chosen is None or not _grid_eq(seg.render_crop(chosen, variant, inp), out):
                    ok = False
                    break
            if ok:
                return {"family": "select_crop", "mode": mode,
                        "selector": sel_name, "variant": variant}
    return None


def _grid_eq(a: Optional[Grid], b: Grid) -> bool:
    return a is not None and a.shape == b.shape and bool(np.array_equal(a, b))


def induce(train) -> Optional[dict]:
    """Try all (family, mode) combinations in fixed order; return first verified rule."""
    for mode in MODES:
        r = induce_same_shape(train, mode)
        if r:
            return r
    for mode in MODES:
        r = induce_select_crop(train, mode)
        if r:
            return r
    return None


def apply_rule(rule: dict, inp: Grid) -> Optional[Grid]:
    if rule["family"] == "same_shape_fates":
        return _apply_fates(inp, rule["mode"], rule["key"], rule["_mapping"])
    objs = seg.segment(inp, rule["mode"])
    chosen = SELECTOR_LOOKUP[rule["selector"]](objs) if objs else None
    if chosen is None:
        return None
    return seg.render_crop(chosen, rule["variant"], inp)
