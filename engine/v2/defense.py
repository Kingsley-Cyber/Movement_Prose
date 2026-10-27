"""Data-driven kick defense and native defense selection for BLOCK Simulator v2."""

from __future__ import annotations

import random
from typing import Any

from .data import get_attack_profile, load_model_v2, load_option_behaviors


def _matches_kick_when(
    when: dict[str, Any],
    kick_tid: str,
    def_opt: str,
    kick_opt: str,
    wall_near: bool,
) -> bool:
    if "kick_in" in when and kick_tid not in when["kick_in"]:
        return False
    if "defense" in when and def_opt != when["defense"]:
        return False
    if "defense_in" in when and def_opt not in when["defense_in"]:
        return False
    if "wall_near" in when and wall_near != bool(when["wall_near"]):
        return False
    if "any_of" in when:
        matched_any = False
        for clause in when["any_of"]:
            if ("kicking" in clause and kick_opt == clause["kicking"]) or (
                "defense" in clause and def_opt == clause["defense"]
            ):
                matched_any = True
                break
        if not matched_any:
            return False
    return True


def select_kick_defense(
    defender_card: dict[str, Any],
    kick_tid: str,
    range_band: str,
    lane_readiness: float = 3.5,
    attacker_card: dict[str, Any] | None = None,
    rng: random.Random | None = None,
    opt_behaviors: dict[str, dict[str, Any]] | None = None,
    wall_proximity: str = "far",
) -> tuple[str, str]:
    """Return (defense_action, outcome_effect) native to defender's defense & kicking dimensions."""
    beh = opt_behaviors if opt_behaviors is not None else load_option_behaviors()
    model_cfg = load_model_v2()
    kd_cfg = model_cfg.get("kick_defense", {})
    catch_lo, catch_hi = kd_cfg.get("catch_clamp", [0.10, 0.65])
    catch_rdy_factor = float(kd_cfg.get("catch_readiness_factor", 0.05))
    rules = model_cfg.get("legacy", {}).get("kick_defense_rules", {}).get("rules", [])

    def_opt = str(defender_card["dimensions"].get("defense") or "")
    kick_opt = str(defender_card["dimensions"].get("kicking") or "")
    wall_near = wall_proximity == "near"

    for rule in rules:
        when = rule.get("when", {})
        if not _matches_kick_when(when, kick_tid, def_opt, kick_opt, wall_near):
            continue
        if "roll" in rule:
            if rng is None:
                no_rng = rule.get("no_rng", {})
                if kick_tid in no_rng.get("kick_in", []):
                    return str(no_rng["action"]), str(no_rng["outcome"])
                continue
            base_catch_map = rule["roll"].get("base_catch", {})
            base_catch = float(base_catch_map.get(kick_tid, 0.18))
            def_catch_bonus = (
                float(get_attack_profile(kick_opt, beh).get("kick_catch_bonus", 0.0))
                + float(get_attack_profile(def_opt, beh).get("kick_catch_bonus", 0.0))
            )
            att_kick_opt = str((attacker_card or {}).get("dimensions", {}).get("kicking") or "")
            retract_mod = float(get_attack_profile(att_kick_opt, beh).get("kick_retraction_delta", 0.0))
            catch_prob = max(
                float(catch_lo),
                min(
                    float(catch_hi),
                    base_catch + def_catch_bonus + retract_mod + catch_rdy_factor * (lane_readiness - 3.0),
                ),
            )
            if rng.random() < catch_prob:
                return str(rule["action"]), str(rule["outcome"])
            continue
        return str(rule["action"]), str(rule["outcome"])

    return "", "blocked"


def _eval_native_step_list(
    steps: list[dict[str, Any]],
    incoming_tid: str,
    avail_def: set[str],
    wall_near: bool,
    hands_opt: str,
) -> tuple[str, str] | None:
    for step in steps:
        when = step.get("when", {})
        if "incoming_in" in when and incoming_tid not in when["incoming_in"]:
            continue
        if "wall_near" in when and wall_near != bool(when["wall_near"]):
            continue
        if "hands" in when and hands_opt != when["hands"]:
            continue
        action = str(step["action"])
        if step.get("needs_trained", False) and action not in avail_def:
            continue
        return action, str(step["outcome"])
    return None


def select_native_defense(
    defender_card: dict[str, Any],
    incoming_tid: str,
    range_band: str,
    avail_def: set[str],
    wall_proximity: str = "far",
) -> tuple[str, str]:
    """Select the defender's native posture-driven defensive action and outcome."""
    model_cfg = load_model_v2()
    nd_cfg = model_cfg.get("legacy", {}).get("native_defense_rules", {})
    default_def = str(nd_cfg.get("default_defense", ""))
    default_hands = str(nd_cfg.get("default_hands", ""))

    def_opt = str(defender_card["dimensions"].get("defense") or default_def)
    hands_opt = str(defender_card["dimensions"].get("hands") or default_hands)
    wall_near = wall_proximity == "near"

    grapple_entry_ids = set(nd_cfg.get("grapple_entry_ids", []))
    if incoming_tid in grapple_entry_ids:
        ge_table = nd_cfg.get("grapple_entry", {})
        opt_entry = ge_table.get(def_opt)
        if opt_entry:
            res = _eval_native_step_list(
                opt_entry.get("steps", []), incoming_tid, avail_def, wall_near, hands_opt
            )
            if res is not None:
                return res
            if not opt_entry.get("fallthrough", True):
                return "", "blocked"
        generic_steps = ge_table.get("generic", {}).get("steps", [])
        res = _eval_native_step_list(generic_steps, incoming_tid, avail_def, wall_near, hands_opt)
        if res is not None:
            return res

    strike_table = nd_cfg.get("strike", {})
    steps = strike_table.get(def_opt, strike_table.get(default_def, []))
    res = _eval_native_step_list(steps, incoming_tid, avail_def, wall_near, hands_opt)
    if res is not None:
        return res
    return "", "blocked"
