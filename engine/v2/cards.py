"""Card loading, archetype listing, and school depth calculation for BLOCK Simulator v2."""

from __future__ import annotations

from typing import Any

from ..capabilities import admitted_slots
from ..ontology import ROOT, Knowledge
from .data import load_model_v2


def load_card_v2(k: Knowledge, value: Any) -> dict[str, Any]:
    """Resolve a predefined archetype ID, file path, or card dict, preferring explicit block-2 cards in cards/v2/."""
    if isinstance(value, str):
        v2_path = k.root / "cards" / "v2" / f"{value}.json"
        if v2_path.exists():
            return k.card(v2_path)
    return k.card(value)


def list_archetypes_v2(knowledge: Knowledge | None = None) -> list[dict[str, Any]]:
    """Return a structured catalog of all predefined block-2 fighter archetypes in cards/v2/*.json."""
    k = knowledge or Knowledge()
    archetypes: list[dict[str, Any]] = []
    v2_dir = k.root / "cards" / "v2"
    paths = sorted(v2_dir.glob("*.json")) if v2_dir.exists() else sorted((k.root / "cards").glob("*.json"))
    for path in paths:
        c = k.card(path)
        archetypes.append(
            {
                "fighter_id": c["fighter_id"],
                "name": c["name"],
                "version": c.get("version", "block-2"),
                "combat_identity": c["combat_identity"],
                "slot_count": c["slot_count"],
                "slot_label": c["slot_label"],
                "tempo": c["tempo"],
                "orientation": c["orientation"],
                "adaptation": c["adaptation"],
                "preferred_ranges": c["preferred_ranges"],
                "dimensions": c["dimensions"],
                "signature_moves": c.get("signature_moves", []),
                "slots": [
                    {
                        "id": s["id"],
                        "capabilities": s["capabilities"],
                        "home_range": s.get("home_range"),
                        "goal": s.get("goal"),
                        "sequence": s.get("sequence", []),
                    }
                    for s in c["synchronized_capabilities"]
                ],
                "fighting_description": c["fighting_description"],
            }
        )
    return archetypes


def compute_school_depth_multiplier(card: dict[str, Any], k: Knowledge | None = None) -> float:
    """Compute depth multiplier based on BOTH total trained schools and slot count so cramming
    more schools into fewer slots never grants an unfair depth bonus.
    """
    root = k.root if k is not None else ROOT
    model_cfg = load_model_v2(root)
    slot_depth_mult = {int(key): float(val) for key, val in model_cfg.get("slot_depth_multipliers", {}).items()}
    slots = admitted_slots(card, k) if k is not None else card.get("synchronized_capabilities", [])
    num_slots = max(1, len(slots))
    unique_schools = {
        c
        for s in card.get("synchronized_capabilities", [])
        for c in s.get("capabilities", [])
        if c not in ("basic_movement",)
    }
    total_schools = len(unique_schools)
    effective_breadth = min(4, max(num_slots, max(1, (total_schools + 1) // 2)))
    return slot_depth_mult.get(effective_breadth, 1.0)
