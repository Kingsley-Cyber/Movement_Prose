"""Technique availability calculation for BLOCK Simulator v2."""

from __future__ import annotations

from typing import Any

from ..capabilities import available, training
from ..ontology import Knowledge
from .data import load_model_v2


def available_v2(k: Knowledge, card: dict[str, Any], ruleset: str = "mma") -> set[str]:
    """Return the fighter's legal v2 technique set."""
    avail = set(available(k, card, ruleset))
    caps = training(card)
    model_cfg = load_model_v2(k.root)
    leg_avail = model_cfg.get("legacy", {}).get("legacy_availability", {})
    karate_opt = leg_avail.get("karate_option")
    karate_grants = leg_avail.get("karate_grants", [])
    if ruleset == "mma" and "karate" in caps and card["dimensions"].get("kicking") == karate_opt:
        avail.update(karate_grants)
    return avail
