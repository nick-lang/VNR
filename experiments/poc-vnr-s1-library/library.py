"""Growing library of macro-abstractions for VNR Stage 1 (the 'sleep' step).

Given a corpus of solved programs (token sequences), greedily compress the most
frequent adjacent token pair into a new named macro, byte-pair-encoding style.
Each merge reduces total corpus description length, so this is an MDL-driven
abstraction step. Macros may nest (a macro can contain earlier macros), forming
a small hierarchy. The resulting library plugs into search as extra one-token
ops whose effect is their expanded primitive sequence.
"""
from __future__ import annotations

from collections import Counter
from typing import Callable, Optional

import numpy as np

import dsl


def _adjacent_pairs(corpus: list[list[str]]) -> Counter:
    counts: Counter = Counter()
    for seq in corpus:
        for i in range(len(seq) - 1):
            counts[(seq[i], seq[i + 1])] += 1
    return counts


def _replace_pair(seq: list[str], a: str, b: str, name: str) -> list[str]:
    out: list[str] = []
    i = 0
    while i < len(seq):
        if i < len(seq) - 1 and seq[i] == a and seq[i + 1] == b:
            out.append(name)
            i += 2
        else:
            out.append(seq[i])
            i += 1
    return out


def build_library(
    solved_programs: list[list[str]],
    cap: int = 8,
    min_count: int = 2,
) -> dict[str, tuple[str, str]]:
    """Return macros: name -> (left_token, right_token). Tokens may be macros."""
    corpus = [list(p) for p in solved_programs if p]
    macros: dict[str, tuple[str, str]] = {}
    while len(macros) < cap:
        counts = _adjacent_pairs(corpus)
        if not counts:
            break
        (a, b), f = counts.most_common(1)[0]
        if f < min_count:
            break
        name = f"m{len(macros)}"
        macros[name] = (a, b)
        corpus = [_replace_pair(seq, a, b, name) for seq in corpus]
    return macros


def expand(token: str, macros: dict[str, tuple[str, str]]) -> list[str]:
    """Expand a (possibly macro) token to its primitive sequence."""
    if token not in macros:
        return [token]
    a, b = macros[token]
    return expand(a, macros) + expand(b, macros)


def expand_program(program: list[str], macros: dict[str, tuple[str, str]]) -> list[str]:
    out: list[str] = []
    for tok in program:
        out.extend(expand(tok, macros))
    return out


def make_ops(macros: dict[str, tuple[str, str]]):
    """Build (ops, token_names) = primitives + macro ops (macros applied last)."""
    ops: dict[str, Callable[[np.ndarray], Optional[np.ndarray]]] = dict(dsl.PRIMITIVES)

    def _make(prims: list[str]):
        def fn(g):
            return dsl.apply_program(prims, g, dsl.PRIMITIVES)
        return fn

    for name in macros:
        ops[name] = _make(expand(name, macros))
    token_names = list(dsl.PRIMITIVES) + list(macros)
    return ops, token_names
