"""Stance relation and laterality subsystem (§7.4) for BLOCK Simulator v2."""

from __future__ import annotations

import math
import random
from typing import Any

from .data import (
    TECH_SWITCH_KICK,
    TECH_SWITCH_STEP,
    load_model_v2,
    load_option_behaviors,
)
from .defense import contest_roll


def compute_lead_foot_matchup(orientation_a: str, orientation_b: str) -> str:
    return "closed_stance" if orientation_a == orientation_b else "open_stance"


def get_anatomical_sides(orientation: str) -> tuple[str, str]:
    """Return (lead_side, rear_side) in ('left', 'right') for the current orientation."""
    if orientation == "southpaw":
        return "right", "left"
    return "left", "right"


def resolve_actor_laterality(
    card: dict[str, Any],
    current_orientation: str,
) -> dict[str, Any]:
    """Resolve dominant_hand, dominant_leg, opposite_stance_experience, and natural flag (§7.4.1)."""
    card_orient = str(card.get("orientation") or "orthodox")
    base_orient = "orthodox" if card_orient == "switching" else card_orient
    default_dom = "left" if base_orient == "southpaw" else "right"

    lat_block = card.get("laterality") or {}
    dom_hand = str(lat_block.get("dominant_hand") or default_dom)
    dom_leg = str(lat_block.get("dominant_leg") or dom_hand)
    opp_exp = str(lat_block.get("opposite_stance_experience") or "normal")

    _, rear_side = get_anatomical_sides(current_orientation)
    is_natural = dom_hand == rear_side and dom_leg == rear_side

    return {
        "dominant_hand": dom_hand,
        "dominant_leg": dom_leg,
        "opposite_stance_experience": opp_exp,
        "natural": is_natural,
    }


def is_switch_step_trained(card: dict[str, Any]) -> bool:
    """Return True if the fighter is trained in the switch_step capability."""
    for slot in card.get("synchronized_capabilities", []):
        if TECH_SWITCH_STEP in slot.get("capabilities", []):
            return True
    if TECH_SWITCH_STEP in card.get("baseline_capabilities", []):
        return True
    return False


def compute_dominance_deltas(
    card: dict[str, Any],
    actor_state: dict[str, Any] | None,
    tech_v2_entry: dict[str, Any],
    model_cfg: dict[str, Any] | None = None,
) -> tuple[float, float]:
    """Return (power_delta, accuracy_delta) from §7.4.1–7.4.2 dominance rules and §7.4.8 limb damage penalties."""
    m_cfg = model_cfg if model_cfg is not None else load_model_v2()
    lat_cfg = m_cfg.get("laterality", {})
    limb_cfg = lat_cfg.get("limb_effects", {})

    orientation = str(
        (actor_state or {}).get("orientation")
        or ("orthodox" if card.get("orientation") == "switching" else card.get("orientation", "orthodox"))
    )
    lat_info = (actor_state or {}).get("laterality") or resolve_actor_laterality(card, orientation)
    dom_hand = str(lat_info.get("dominant_hand", "right"))
    dom_leg = str(lat_info.get("dominant_leg", dom_hand))

    lead_side, rear_side = get_anatomical_sides(orientation)
    tid = str(tech_v2_entry.get("id") or "")
    kind = str(tech_v2_entry.get("kind") or "")
    side = str(tech_v2_entry.get("side") or "none")
    if tid == TECH_SWITCH_KICK:
        side = "lead"

    switch_scale = float(lat_cfg.get("switch_trained_rear_penalty_scale", 0.5)) if is_switch_step_trained(card) else 1.0
    power_delta = 0.0
    acc_delta = 0.0

    if kind in ("punch", "elbow") and side in ("lead", "rear"):
        if dom_hand == "ambidextrous":
            hd = lat_cfg.get("hand_deltas", {}).get("ambidextrous", {})
            power_delta = float(hd.get(f"{side}_power", 0.0))
            acc_delta = float(hd.get(f"{side}_accuracy", 0.0))
        elif dom_hand == lead_side:
            hd = lat_cfg.get("hand_deltas", {}).get("cross_dominant", {})
            power_delta = float(hd.get(f"{side}_power", 0.0))
            acc_delta = float(hd.get(f"{side}_accuracy", 0.0))
            if side == "rear":
                power_delta *= switch_scale
                acc_delta *= switch_scale

    elif kind in ("kick", "knee") and side in ("lead", "rear"):
        if dom_leg == "both":
            ld = lat_cfg.get("leg_deltas", {}).get("both", {})
            power_delta = float(ld.get(f"{side}_power", 0.0))
            acc_delta = float(ld.get(f"{side}_accuracy", 0.0))
        elif dom_leg == lead_side:
            ld = lat_cfg.get("leg_deltas", {}).get("cross_dominant", {})
            power_delta = float(ld.get(f"{side}_power", 0.0))
            acc_delta = float(ld.get(f"{side}_accuracy", 0.0))
            if side == "rear":
                power_delta *= switch_scale
                acc_delta *= switch_scale

    # Limb damage penalties (§7.4.8): arm damage reduces punch power on that arm
    dmg_side = (actor_state or {}).get("damage_by_side")
    if dmg_side:
        limb_anat = resolve_limb_anatomical_side(orientation, tech_v2_entry)
        if kind in ("punch", "elbow") and limb_anat in ("left", "right"):
            arm_dmg = float(dmg_side.get(f"arm_{limb_anat}", 0.0))
            arm_pen_pt = float(limb_cfg.get("arm_damage_power_penalty_per_point", 0.03))
            arm_pen_cap = float(limb_cfg.get("arm_damage_power_penalty_cap", 0.15))
            power_delta -= min(arm_pen_cap, arm_dmg * arm_pen_pt)

    return round(power_delta, 4), round(acc_delta, 4)


def resolve_limb_anatomical_side(
    orientation: str,
    tech_v2_entry: dict[str, Any],
) -> str:
    """Return 'left', 'right', 'both', or 'none' for the attacking limb's anatomical side (§7.4.3)."""
    tid = str(tech_v2_entry.get("id") or "")
    side = str(tech_v2_entry.get("side") or "none")
    if tid == TECH_SWITCH_KICK:
        side = "lead"
    lead_side, rear_side = get_anatomical_sides(orientation)
    if side == "lead":
        return lead_side
    if side in ("rear", "either"):
        return rear_side
    if side == "both":
        return "both"
    return "none"


def resolve_target_anatomical_side(
    attacker_orientation: str,
    defender_orientation: str,
    tech_v2_entry: dict[str, Any],
) -> tuple[str, str]:
    """Return (limb_side, target_side) for an exchange (§7.4.7)."""
    limb_side = resolve_limb_anatomical_side(attacker_orientation, tech_v2_entry)
    rule = str(tech_v2_entry.get("target_side_rule") or "none")
    def_lead, def_rear = get_anatomical_sides(defender_orientation)

    if rule == "opposite_of_limb":
        if limb_side == "left":
            return limb_side, "right"
        if limb_side == "right":
            return limb_side, "left"
        return limb_side, def_lead
    if rule == "defender_lead":
        return limb_side, def_lead
    if rule == "defender_rear":
        return limb_side, def_rear
    if rule == "grip_side":
        return limb_side, (limb_side if limb_side in ("left", "right") else def_lead)
    if rule == "center":
        return limb_side, "center"
    return limb_side, "none"


def compute_line_accuracy_modifier(
    stance_relation: str,
    tech_v2_entry: dict[str, Any],
    lead_foot_outside_winner_id: str | None,
    attacker_id: str,
    model_cfg: dict[str, Any] | None = None,
) -> float:
    """Return line_accuracy_modifiers[relation][line] + lead_foot_outside winner bonus (§7.4.4–7.4.5)."""
    m_cfg = model_cfg if model_cfg is not None else load_model_v2()
    lat_cfg = m_cfg.get("laterality", {})
    line_mods = lat_cfg.get("line_accuracy_modifiers", {}).get(stance_relation, {})
    line = str(tech_v2_entry.get("line") or "none")
    mod = float(line_mods.get(line, 0.0))

    if lead_foot_outside_winner_id and lead_foot_outside_winner_id == attacker_id:
        lfo_cfg = lat_cfg.get("lead_foot_outside", {})
        rear_power_lines = set(lfo_cfg.get("rear_power_lines", []))
        if line in rear_power_lines:
            mod += float(lfo_cfg.get("winner_rear_power_line_accuracy_bonus", 0.06))
    return round(mod, 4)


def resolve_lead_foot_outside_contest(
    canonical_ids: list[str],
    cards: dict[str, dict[str, Any]],
    actors: dict[str, dict[str, Any]],
    stance_relation: str,
    range_band: str,
    rng: random.Random,
    opt_behaviors: dict[str, dict[str, Any]] | None = None,
    model_cfg: dict[str, Any] | None = None,
) -> str | None:
    """Resolve the open-stance lead-foot-outside contest in canonical order (§7.4.5).

    Sets `attention.outside_angle_conceded` on both actors and returns the winner's fighter_id (or None).
    """
    m_cfg = model_cfg if model_cfg is not None else load_model_v2()
    beh = opt_behaviors if opt_behaviors is not None else load_option_behaviors()
    lfo_cfg = m_cfg.get("laterality", {}).get("lead_foot_outside", {})

    for fid in canonical_ids:
        actors[fid]["attention"]["outside_angle_conceded"] = False

    if stance_relation != lfo_cfg.get("applies_in", "open_stance"):
        return None
    if range_band not in lfo_cfg.get("ranges", ["kick", "punch"]):
        return None

    def _lfo_sum(card: dict[str, Any]) -> float:
        dims = card.get("dimensions", {})
        total = 0.0
        for d in ("mentality", "stance", "defense", "hands", "tie", "kicking", "target"):
            oid = dims.get(d)
            if oid and oid in beh:
                ometa = beh[oid]
                val = ometa.get("lead_foot_outside_delta", ometa.get("attack_profile", {}).get("lead_foot_outside_delta", 0.0))
                total += float(val or 0.0)
        return total

    id0, id1 = canonical_ids[0], canonical_ids[1]
    slope = float(lfo_cfg.get("contest_slope", 1.0))
    sum0 = _lfo_sum(cards[id0])
    sum1 = _lfo_sum(cards[id1])
    diff = sum0 - sum1
    p0 = 1.0 / (1.0 + math.exp(-slope * diff))
    won0, _, _ = contest_roll(p0, band_name="lead_foot_outside", rng=rng, model_cfg=m_cfg)
    winner_id = id0 if won0 else id1
    loser_id = id1 if won0 else id0
    winner_sum = sum0 if won0 else sum1
    loser_sum = sum1 if won0 else sum0
    if lfo_cfg.get("loser_sets_outside_angle_conceded", True) and (winner_sum - loser_sum) >= 0.15:
        actors[loser_id]["attention"]["outside_angle_conceded"] = True
    return winner_id


def compute_familiarity_multipliers(
    defender_card: dict[str, Any],
    defender_orientation: str,
    attacker_orientation: str,
    model_cfg: dict[str, Any] | None = None,
) -> tuple[float, float]:
    """Return (read_gain_mult, novelty_penalty_mult) for facing the attacker's stance (§7.4.6)."""
    if defender_orientation == attacker_orientation:
        return 1.0, 1.0

    m_cfg = model_cfg if model_cfg is not None else load_model_v2()
    fam_cfg = m_cfg.get("laterality", {}).get("familiarity", {})
    exp_def = fam_cfg.get("exposure_default", {})
    overrides = fam_cfg.get("card_override", {})

    lat_block = defender_card.get("laterality") or {}
    exp_label = str(lat_block.get("opposite_stance_experience") or "normal")
    override_val = overrides.get(exp_label)
    if override_val is not None:
        exposure = float(override_val)
    elif defender_orientation == "orthodox" and attacker_orientation == "southpaw":
        exposure = float(exp_def.get("orthodox_facing_southpaw", 0.25))
    else:
        exposure = float(exp_def.get("southpaw_facing_orthodox", 0.85))

    rg_zero = float(fam_cfg.get("read_gain_at_zero_exposure", 0.8))
    np_zero = float(fam_cfg.get("novelty_penalty_multiplier_at_zero_exposure", 1.5))
    rg_mult = rg_zero + (1.0 - rg_zero) * exposure
    np_mult = np_zero + (1.0 - np_zero) * exposure
    return rg_mult, np_mult


def apply_side_damage_and_cuts(
    defender_state: dict[str, Any],
    target_region: str,
    target_side: str,
    final_damage: float,
    outcome: str,
    tech_v2_entry: dict[str, Any],
    rng: random.Random | None = None,
    model_cfg: dict[str, Any] | None = None,
    damage_share: float = 1.0,
    equipment: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Update defender's damage_by_side, cuts, and compute body-side stamina multiplier (§7.4.7–7.4.8)."""
    m_cfg = model_cfg if model_cfg is not None else load_model_v2()
    lat_cfg = m_cfg.get("laterality", {})
    body_sides_cfg = lat_cfg.get("body_sides", {})
    cuts_cfg = lat_cfg.get("cuts", {})

    dmg_side = defender_state.setdefault(
        "damage_by_side",
        {
            "head_left": 0.0,
            "head_right": 0.0,
            "body_left": 0.0,
            "body_right": 0.0,
            "leg_left": 0.0,
            "leg_right": 0.0,
            "arm_left": 0.0,
            "arm_right": 0.0,
        },
    )
    cuts = defender_state.setdefault("cuts", {"left": 0, "right": 0})
    eff_dmg = float(final_damage) * float(damage_share)

    side_bucket = target_side if target_side in ("left", "right") else "center"
    kind = str(tech_v2_entry.get("kind") or "")
    joint = str(tech_v2_entry.get("joint_target") or "none")

    if eff_dmg > 0.0:
        if outcome == "blocked" and kind in ("punch", "kick", "elbow", "knee") and target_region in ("head", "body"):
            # Blocked strikes also wear the guarding arm(s)
            if side_bucket in ("left", "right"):
                arm_key = f"arm_{side_bucket}"
                dmg_side[arm_key] = round(float(dmg_side.get(arm_key, 0.0)) + 0.35 * eff_dmg, 3)
            else:
                dmg_side["arm_left"] = round(float(dmg_side.get("arm_left", 0.0)) + 0.175 * eff_dmg, 3)
                dmg_side["arm_right"] = round(float(dmg_side.get("arm_right", 0.0)) + 0.175 * eff_dmg, 3)

        if kind == "submission" and joint in ("elbow", "shoulder", "wrist"):
            arm_s = side_bucket if side_bucket in ("left", "right") else "right"
            arm_key = f"arm_{arm_s}"
            dmg_side[arm_key] = round(float(dmg_side.get(arm_key, 0.0)) + eff_dmg, 3)

        if target_region in ("head", "body", "leg"):
            if side_bucket in ("left", "right"):
                key = f"{target_region}_{side_bucket}"
                dmg_side[key] = round(float(dmg_side.get(key, 0.0)) + eff_dmg, 3)
            else:
                k_l = f"{target_region}_left"
                k_r = f"{target_region}_right"
                dmg_side[k_l] = round(float(dmg_side.get(k_l, 0.0)) + 0.5 * eff_dmg, 3)
                dmg_side[k_r] = round(float(dmg_side.get(k_r, 0.0)) + 0.5 * eff_dmg, 3)

    # Body side stamina multiplier (liver on liver_side -> 1.25, spleen -> 1.05)
    liver_side = str(body_sides_cfg.get("liver_side", "right"))
    liver_mult = float(body_sides_cfg.get("liver_stamina_multiplier", 1.25))
    spleen_mult = float(body_sides_cfg.get("spleen_stamina_multiplier", 1.05))
    body_stamina_mult = 1.0
    if target_region == "body":
        if side_bucket == liver_side:
            body_stamina_mult = liver_mult
        elif side_bucket in ("left", "right"):
            body_stamina_mult = spleen_mult
        else:
            body_stamina_mult = 0.5 * (liver_mult + spleen_mult)

    # Cut chance on head impacts (§7.4.8 & ruleset equipment cut_chance_bonus)
    cut_added = False
    base_cut = float(tech_v2_entry.get("cut_chance") or 0.0)
    eq = equipment or {}
    cut_bonus = float(eq.get("cut_chance_bonus", 0.0))
    gloves = bool(eq.get("gloves", True))
    if base_cut > 0.0:
        cut_chance = min(1.0, base_cut + cut_bonus)
    elif not gloves and kind == "punch" and outcome in ("clean", "flush", "counter_hit"):
        cut_chance = min(1.0, cut_bonus)
    else:
        cut_chance = 0.0
    max_cut = int(cuts_cfg.get("max_cut_level", 3))
    if (
        rng is not None
        and cut_chance > 0.0
        and target_region == "head"
        and outcome in ("clean", "flush", "counter_hit", "partial")
    ):
        won_cut, _, _ = contest_roll(cut_chance, band_name="cut", rng=rng, model_cfg=m_cfg)
        if won_cut:
            cut_side = side_bucket if side_bucket in ("left", "right") else (
                "left" if int(cuts.get("left", 0)) <= int(cuts.get("right", 0)) else "right"
            )
            if int(cuts.get(cut_side, 0)) < max_cut:
                cuts[cut_side] = int(cuts.get(cut_side, 0)) + 1
                cut_added = True

    return {
        "body_stamina_mult": body_stamina_mult,
        "cut_added": cut_added,
    }
