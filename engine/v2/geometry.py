"""Arena presets and 2-D geometry helpers for BLOCK Simulator v2."""

from __future__ import annotations

from typing import Any

from .data import ARENA_PRESETS, load_model_v2


def get_arena_preset(arena: str) -> dict[str, Any]:
    model_cfg = load_model_v2()
    presets = model_cfg.get("arena_presets", ARENA_PRESETS)
    return presets.get(arena, presets.get("cage", {}))
