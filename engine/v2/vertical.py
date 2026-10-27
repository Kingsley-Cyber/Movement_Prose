"""Vertical mode normalization and gating helpers for BLOCK Simulator v2."""

from __future__ import annotations

from .data import load_model_v2


def normalize_vertical_mode(vertical_mode: str) -> str:
    """Normalize input vertical_mode aliases (e.g. 'wall_assisted' -> 'aerial', D14)."""
    model_cfg = load_model_v2()
    aliases = model_cfg.get("vertical", {}).get("aliases", {})
    return str(aliases.get(vertical_mode, vertical_mode))
