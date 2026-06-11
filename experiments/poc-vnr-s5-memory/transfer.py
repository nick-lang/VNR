"""Weight-memory transfer machinery for VNR Stage 5 (H9).

CompressARC models factor into task-shaped LATENTS (multiposteriors,
target_capacities -- never transferred) and fixed-shape TRANSFORMATION
WEIGHTS (identical structure for every task). This module extracts those
transformation weights to a plain nested structure of CPU tensors, averages
them across donor tasks ("weight soup"), and loads them into a fresh model.

CompressARC source is NOT modified; everything here operates from outside.
"""
from __future__ import annotations

import io

import torch

# Attributes of ARCCompressor that hold transformation weights.
# Deliberately excludes: multiposteriors, target_capacities (task-shaped latents).
TRANSFER_ATTRS = [
    "decode_weights",
    "share_up_weights",
    "share_down_weights",
    "softmax_weights",
    "cummax_weights",
    "shift_weights",
    "direction_share_weights",
    "nonlinear_weights",
    "head_weights",
    "mask_weights",
]


def _to_plain(node):
    """Recursively convert MultiTensor / lists / tensors to nested lists of CPU tensors."""
    if node is None:
        return None
    if isinstance(node, torch.Tensor):
        return node.detach().cpu().clone()
    if isinstance(node, list):
        return [_to_plain(c) for c in node]
    if hasattr(node, "data") and hasattr(node, "multitensor_system"):  # MultiTensor
        return _to_plain(node.data)
    raise TypeError(f"unexpected node type: {type(node)}")


def _copy_into(model_node, plain_node):
    """Recursively copy plain CPU tensors into the live model structure."""
    if model_node is None and plain_node is None:
        return
    if isinstance(model_node, torch.Tensor):
        assert isinstance(plain_node, torch.Tensor), "structure mismatch"
        assert tuple(model_node.shape) == tuple(plain_node.shape), (
            f"shape mismatch: {tuple(model_node.shape)} vs {tuple(plain_node.shape)}"
        )
        with torch.no_grad():
            model_node.data.copy_(plain_node.to(model_node.device))
        return
    if isinstance(model_node, list):
        assert isinstance(plain_node, list) and len(model_node) == len(plain_node)
        for m, p in zip(model_node, plain_node):
            _copy_into(m, p)
        return
    if hasattr(model_node, "data") and hasattr(model_node, "multitensor_system"):
        _copy_into(model_node.data, plain_node)
        return
    raise TypeError(f"unexpected node type: {type(model_node)}")


def _average(nodes: list):
    """Element-wise mean over parallel nested structures."""
    first = nodes[0]
    if first is None:
        return None
    if isinstance(first, torch.Tensor):
        return torch.stack([n.float() for n in nodes]).mean(dim=0)
    if isinstance(first, list):
        return [_average([n[i] for n in nodes]) for i in range(len(first))]
    raise TypeError(f"unexpected node type: {type(first)}")


def extract_weights(model) -> dict:
    """Extract transformation weights (NOT latents) as plain nested CPU tensors."""
    return {attr: _to_plain(getattr(model, attr)) for attr in TRANSFER_ATTRS}


def load_weights(model, blob: dict) -> None:
    """Copy a previously extracted (or averaged) weight structure into a model.

    Latents are untouched; tied (symmetrized) tensors are simply copied twice,
    which preserves the tying.
    """
    for attr in TRANSFER_ATTRS:
        _copy_into(getattr(model, attr), blob[attr])


def average_weights(blobs: list[dict]) -> dict:
    """Weight soup: element-wise mean across donor weight structures."""
    return {attr: _average([b[attr] for b in blobs]) for attr in TRANSFER_ATTRS}


def to_bytes(blob: dict) -> bytes:
    buf = io.BytesIO()
    torch.save(blob, buf)
    return buf.getvalue()


def from_bytes(data: bytes) -> dict:
    return torch.load(io.BytesIO(data), map_location="cpu", weights_only=False)
