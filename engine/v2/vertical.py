"""Vertical mode normalization and gating helpers (§7.13, D14) for BLOCK Simulator v2."""

from __future__ import annotations

from typing import Any

from .data import load_model_v2


def normalize_vertical_mode(vertical_mode: str, model_cfg: dict[str, Any] | None = None) -> str:
    """Normalize input vertical_mode aliases (e.g. 'wall_assisted' -> 'aerial', D14)."""
    cfg = model_cfg if model_cfg is not None else load_model_v2()
    aliases = cfg.get("vertical", {}).get("aliases", {})
    return str(aliases.get(vertical_mode, vertical_mode))


def is_technique_vertically_allowed(
    tech_entry: dict[str, Any],
    card: dict[str, Any],
    vertical_mode: str = "grounded",
    model_cfg: dict[str, Any] | None = None,
) -> bool:
    """Return True if tech_entry is usable under the fight's vertical_mode and card's airborne_training (§7.13)."""
    cfg = model_cfg if model_cfg is not None else load_model_v2()
    v_cfg = cfg.get("vertical", {})
    norm_mode = normalize_vertical_mode(vertical_mode, cfg)
    modes_map = v_cfg.get(
        "modes",
        {
            "grounded": ["grounded"],
            "athletic": ["grounded", "athletic"],
            "aerial": ["grounded", "athletic", "aerial"],
        },
    )
    allowed_by_fight = set(modes_map.get(norm_mode, ["grounded"]))
    v_min = str(tech_entry.get("vertical_min") or "grounded")
    if v_min not in allowed_by_fight:
        return False

    air_tr = card.get("airborne_training") or {}
    allowed_by_card = set(air_tr.get("allowed_vertical_modes") or ["grounded"]) | {"grounded"}
    if v_min not in allowed_by_card:
        return False

    if bool(tech_entry.get("requires_airborne_training", False)):
        trained_air_techs = set(air_tr.get("techniques") or [])
        if str(tech_entry.get("id", "")) not in trained_air_techs:
            return False

    return True

