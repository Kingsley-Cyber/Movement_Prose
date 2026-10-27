"""Slot gameplan construction and technique selection helpers for BLOCK Simulator v2."""

from __future__ import annotations

from typing import Any

from ..capabilities import admitted_slots
from ..ontology import Knowledge
from .availability import available_v2
from .cards import compute_school_depth_multiplier
from .data import load_model_v2


def _matches_slot_fallback(
    when: dict[str, Any],
    caps: set[str],
    slot_moves: list[str],
    kicking_opt: str,
    target_opt: str,
    mentality_opt: str | None,
) -> bool:
    if "caps_has" in when and when["caps_has"] not in caps:
        return False
    if "caps_has_any" in when and not any(c in caps for c in when["caps_has_any"]):
        return False
    if "slot_moves_has" in when and when["slot_moves_has"] not in slot_moves:
        return False
    if "kicking" in when and kicking_opt != when["kicking"]:
        return False
    if "target" in when and target_opt != when["target"]:
        return False
    if "mentality" in when and mentality_opt != when["mentality"]:
        return False
    return True


def build_slot_plans(
    k: Knowledge,
    card: dict[str, Any],
    ruleset: str = "mma",
) -> list[dict[str, Any]]:
    """Build executable SlotPlan objects from card.synchronized_capabilities."""
    model_cfg = load_model_v2(k.root)
    sp_cfg = model_cfg.get("legacy", {}).get("slot_plans", {})
    default_opts = sp_cfg.get("default_options", {})
    karate_opt_id = sp_cfg.get("karate_option")
    excluded_tid = sp_cfg.get("excluded_technique")
    karate_mma_append = sp_cfg.get("karate_mma_append", [])
    empty_seq_fallback = sp_cfg.get("empty_sequence_fallback", [])
    fallback_orders = sp_cfg.get("fallback_orders", [])
    home_range_default = sp_cfg.get("home_range_default", {})

    all_avail = available_v2(k, card, ruleset)
    plans: list[dict[str, Any]] = []
    slots = admitted_slots(card, k)
    depth_mult = compute_school_depth_multiplier(card, k)
    kicking_opt = str(card["dimensions"].get("kicking") or default_opts.get("kicking", ""))
    target_opt = str(card["dimensions"].get("target") or default_opts.get("target", ""))
    mentality_opt = card["dimensions"].get("mentality")

    for idx, slot in enumerate(slots):
        caps = set(slot.get("capabilities", []))
        explicit_seq = [m for m in slot.get("sequence", []) if m in all_avail]
        if explicit_seq and not ("karate" in caps and kicking_opt == karate_opt_id and len(explicit_seq) <= 3):
            clean_seq = explicit_seq
        else:
            t_lookup = {**getattr(k, "techniques_v2", {}), **k.techniques}
            slot_moves = [
                tid
                for tid in card["active_techniques"]
                if tid in all_avail
                and tid != excluded_tid
                and tid in t_lookup
                and t_lookup[tid]["kind"] in ("punch", "kick", "knee", "takedown", "grip", "control", "submission")
                and (set(t_lookup[tid]["required_capabilities"]) & caps)
            ]
            if "karate" in caps and kicking_opt == karate_opt_id and ruleset == "mma":
                for km in karate_mma_append:
                    if km in all_avail and km not in slot_moves:
                        slot_moves.append(km)
            if not slot_moves:
                slot_moves = [
                    tid
                    for tid in card["active_techniques"]
                    if tid in all_avail and tid in t_lookup and t_lookup[tid]["kind"] in ("punch", "kick", "takedown", "grip")
                ]

            ordered_seq: list[str] = []
            for rule in fallback_orders:
                if _matches_slot_fallback(
                    rule.get("when", {}), caps, slot_moves, kicking_opt, target_opt, mentality_opt
                ):
                    order_spec = rule.get("order")
                    if order_spec == "slot_moves":
                        ordered_seq.extend(slot_moves)
                    else:
                        pool_mode = rule.get("pool", "slot_moves")
                        if pool_mode == "slot_moves_or_available":
                            ordered_seq.extend([m for m in order_spec if m in slot_moves or m in all_avail])
                        else:
                            ordered_seq.extend([m for m in order_spec if m in slot_moves])
                    break

            seen_m: set[str] = set()
            clean_seq = []
            for m in ordered_seq + slot_moves:
                if m in all_avail and m not in seen_m:
                    seen_m.add(m)
                    clean_seq.append(m)

        home_range = slot.get("home_range")
        if not home_range:
            home_range = str(home_range_default.get("else", "punch"))
            if any(c in caps for c in home_range_default.get("clinch", [])):
                home_range = "clinch"
            elif any(c in caps for c in home_range_default.get("kick", [])):
                home_range = "kick"

        abandon_rule = slot.get("abandon_rule", {})
        max_stalls = int(abandon_rule.get("max_consecutive_stalls", 999 if len(slots) == 1 else 2))
        next_slot_id = (slot.get("links") or [slots[(idx + 1) % len(slots)]["id"]])[0]

        plans.append(
            {
                "slot_id": slot["id"],
                "slot_index": idx,
                "capabilities": sorted(caps),
                "sequence": clean_seq or list(empty_seq_fallback),
                "home_range": home_range,
                "goal": slot.get("goal", "head_damage"),
                "depth_multiplier": depth_mult,
                "trigger": slot.get("trigger", "fight_start" if idx == 0 else "slot_stalled_or_countered"),
                "abandon_threshold": max_stalls,
                "next_slot_id": next_slot_id,
            }
        )

    pref_first = (card.get("preferred_ranges") or ["punch"])[0]
    plans.sort(key=lambda p: (0 if p["home_range"] == pref_first else 1, p["slot_index"]))
    for i, p in enumerate(plans):
        p["trigger"] = "fight_start" if i == 0 else "slot_stalled_or_countered"
        p["next_slot_id"] = plans[(i + 1) % len(plans)]["slot_id"]
    return plans
