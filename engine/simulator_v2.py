"""BLOCK Fight Simulator v2: Card-Driven Simulation, First-Class Kicking, Grappling Position Map,
Slot Gameplans, Real Fight Clock, 2D Arena Presets, and Card-Derived Damage Calculator.

Implements docs/BLOCK_SIMULATOR_V2_DESIGN_SPEC.md while preserving 100% backward compatibility
with existing v1 engine modules and all 107 v1 tests.
"""

from __future__ import annotations

import copy
import math
import random
from typing import Dict, List, Optional, Tuple

from .capabilities import admitted_slots, available, resolved_dimensions
from .ontology import Knowledge
from .probability import predict


# ---------------------------------------------------------------------------
# 1. Move Base Damage, Damage Types & 24fps Frame Costs
# ---------------------------------------------------------------------------

MOVE_BASE_STATS: Dict[str, Dict[str, object]] = {
    # Movement & Feints
    "step": {"base": 0.0, "type": "movement", "setup_f": 3, "exec_f": 6, "hold_f": 0, "rec_f": 4},
    "retreat": {"base": 0.0, "type": "movement", "setup_f": 2, "exec_f": 6, "hold_f": 0, "rec_f": 4},
    "pivot": {"base": 0.0, "type": "movement", "setup_f": 3, "exec_f": 7, "hold_f": 0, "rec_f": 4},
    "switch_step": {"base": 0.0, "type": "movement", "setup_f": 3, "exec_f": 8, "hold_f": 0, "rec_f": 5},
    "feint": {"base": 0.0, "type": "feint", "setup_f": 2, "exec_f": 5, "hold_f": 0, "rec_f": 3},
    # Punches
    "jab": {"base": 1.0, "type": "buildup", "setup_f": 3, "exec_f": 5, "hold_f": 2, "rec_f": 5, "line": "head_straight"},
    "cross": {"base": 2.0, "type": "impact", "setup_f": 5, "exec_f": 7, "hold_f": 3, "rec_f": 8, "line": "head_straight"},
    "hook": {"base": 2.5, "type": "impact", "setup_f": 5, "exec_f": 8, "hold_f": 3, "rec_f": 9, "line": "head_hook"},
    "body_hook": {"base": 2.3, "type": "stamina_drain", "setup_f": 5, "exec_f": 8, "hold_f": 3, "rec_f": 8, "line": "body"},
    "uppercut": {"base": 2.7, "type": "impact", "setup_f": 6, "exec_f": 8, "hold_f": 3, "rec_f": 10, "line": "head_uppercut"},
    "haymaker": {"base": 3.2, "type": "impact", "setup_f": 9, "exec_f": 11, "hold_f": 4, "rec_f": 16, "line": "head_hook"},
    # Kicks & Knees (First-Class Kicking Subsystem)
    "teep": {"base": 1.4, "type": "stamina_drain", "setup_f": 4, "exec_f": 7, "hold_f": 2, "rec_f": 7, "line": "body"},
    "low_kick": {"base": 2.2, "type": "buildup", "setup_f": 5, "exec_f": 8, "hold_f": 3, "rec_f": 10, "line": "leg"},
    "body_kick": {"base": 2.6, "type": "stamina_drain", "setup_f": 6, "exec_f": 9, "hold_f": 3, "rec_f": 12, "line": "body"},
    "side_kick": {"base": 2.3, "type": "impact", "setup_f": 5, "exec_f": 8, "hold_f": 3, "rec_f": 10, "line": "body"},
    "head_kick": {"base": 3.5, "type": "impact", "setup_f": 7, "exec_f": 10, "hold_f": 4, "rec_f": 15, "line": "head_hook"},
    "switch_kick": {"base": 2.8, "type": "stamina_drain", "setup_f": 6, "exec_f": 9, "hold_f": 3, "rec_f": 11, "line": "body"},
    "spinning_back_kick": {"base": 3.3, "type": "impact", "setup_f": 8, "exec_f": 10, "hold_f": 4, "rec_f": 16, "line": "body", "vertical": "athletic"},
    "axe_kick": {"base": 3.1, "type": "impact", "setup_f": 8, "exec_f": 11, "hold_f": 3, "rec_f": 14, "line": "head_straight", "vertical": "athletic"},
    "knee_body": {"base": 2.8, "type": "stamina_drain", "setup_f": 4, "exec_f": 7, "hold_f": 3, "rec_f": 8, "line": "body"},
    "jumping_knee": {"base": 3.6, "type": "impact", "setup_f": 7, "exec_f": 10, "hold_f": 4, "rec_f": 16, "line": "head_uppercut", "vertical": "athletic"},
    # Clinch, Takedowns, Control & Submissions
    "pummel": {"base": 0.4, "type": "stamina_drain", "setup_f": 4, "exec_f": 8, "hold_f": 2, "rec_f": 6, "line": "clinch"},
    "collar_tie": {"base": 0.5, "type": "stamina_drain", "setup_f": 4, "exec_f": 7, "hold_f": 2, "rec_f": 6, "line": "clinch"},
    "body_lock": {"base": 0.6, "type": "stamina_drain", "setup_f": 5, "exec_f": 8, "hold_f": 2, "rec_f": 7, "line": "clinch"},
    "cage_plum": {"base": 0.8, "type": "stamina_drain", "setup_f": 5, "exec_f": 8, "hold_f": 3, "rec_f": 7, "line": "clinch"},
    "shield_frame": {"base": 0.5, "type": "buildup", "setup_f": 3, "exec_f": 6, "hold_f": 2, "rec_f": 5, "line": "head_straight"},
    "double_leg": {"base": 2.4, "type": "impact", "setup_f": 6, "exec_f": 12, "hold_f": 4, "rec_f": 14, "line": "entry"},
    "single_leg": {"base": 2.1, "type": "buildup", "setup_f": 5, "exec_f": 11, "hold_f": 4, "rec_f": 12, "line": "entry"},
    "outside_trip": {"base": 2.5, "type": "impact", "setup_f": 5, "exec_f": 10, "hold_f": 4, "rec_f": 12, "line": "clinch"},
    "sanda_sweep": {"base": 2.6, "type": "impact", "setup_f": 4, "exec_f": 9, "hold_f": 4, "rec_f": 11, "line": "single_support"},
    "guard_pull": {"base": 0.8, "type": "stamina_drain", "setup_f": 4, "exec_f": 10, "hold_f": 2, "rec_f": 8, "line": "clinch"},
    "ride": {"base": 1.6, "type": "stamina_drain", "setup_f": 4, "exec_f": 14, "hold_f": 4, "rec_f": 8, "line": "ground"},
    "armbar": {"base": 3.8, "type": "submission", "setup_f": 8, "exec_f": 16, "hold_f": 6, "rec_f": 12, "line": "ground"},
    "escape": {"base": 0.0, "type": "movement", "setup_f": 5, "exec_f": 12, "hold_f": 0, "rec_f": 8, "line": "ground"},
}


# ---------------------------------------------------------------------------
# 2. Arena Geometry Presets & Verticality Modes
# ---------------------------------------------------------------------------

ARENA_PRESETS: Dict[str, Dict[str, object]] = {
    "ring": {
        "id": "ring",
        "half_width_m": 3.0,
        "wall_near_m": 0.6,
        "has_walls": True,
        "has_corners": True,
        "corner_trap_bonus": 1.15,
        "lateral_freedom": 1.0,
    },
    "cage": {
        "id": "cage",
        "half_width_m": 3.5,
        "wall_near_m": 0.65,
        "has_walls": True,
        "has_corners": False,
        "wall_pin_bonus": 1.20,
        "lateral_freedom": 1.1,
    },
    "open_floor": {
        "id": "open_floor",
        "half_width_m": 50.0,
        "wall_near_m": 0.0,
        "has_walls": False,
        "has_corners": False,
        "lateral_freedom": 1.35,
    },
    "narrow_alley": {
        "id": "narrow_alley",
        "half_width_m": 1.6,
        "wall_near_m": 0.5,
        "has_walls": True,
        "has_corners": True,
        "restricts_wide_kicks": True,
        "lateral_freedom": 0.55,
    },
    "rooftop_edge": {
        "id": "rooftop_edge",
        "half_width_m": 2.8,
        "wall_near_m": 0.6,
        "has_walls": False,
        "has_drop_hazard": True,
        "lateral_freedom": 0.85,
    },
    "dojo": {
        "id": "dojo",
        "half_width_m": 4.0,
        "wall_near_m": 0.6,
        "has_walls": True,
        "hard_floor_throw_bonus": 1.20,
        "lateral_freedom": 1.15,
    },
}


# ---------------------------------------------------------------------------
# 3. First-Class Kicking Subsystem (Unrolled Anatomy & School Mechanics)
# ---------------------------------------------------------------------------

KICK_IDS = {
    "low_kick",
    "body_kick",
    "head_kick",
    "teep",
    "side_kick",
    "switch_kick",
    "spinning_back_kick",
    "axe_kick",
    "jumping_knee",
    "knee_body",
}


def unroll_kick_anatomy(tid: str, card: Dict[str, object], orientation: str) -> Optional[Dict[str, object]]:
    """Generate the full 6-part unrolled biomechanical kick descriptor for any kick/knee move."""
    if tid not in KICK_IDS:
        return None
    school = (card["dimensions"].get("kicking") or "kicking.none").split(".")[-1]
    lead_side = "left" if orientation == "orthodox" else "right"
    rear_side = "right" if orientation == "orthodox" else "left"

    if tid == "teep":
        return {
            "kick_family": school,
            "kicking_leg": f"lead_{lead_side}",
            "chamber": "high_tight_knee_fold",
            "support_foot": f"rear_{rear_side}_flat_planted_15deg",
            "path": "linear_thrust_centerline",
            "target_region": "body_sternum_or_hip",
            "striking_surface": "ball_of_foot",
            "ending": "snap_back_to_lead_stance",
            "single_leg_exposure_window": "low",
        }
    if tid == "side_kick":
        return {
            "kick_family": school,
            "kicking_leg": f"lead_{lead_side}",
            "chamber": "lateral_bladed_hip_fold",
            "support_foot": f"rear_{rear_side}_heel_turned_135deg",
            "path": "linear_side_thrust",
            "target_region": "body_floating_ribs",
            "striking_surface": "blade_or_heel_of_foot",
            "ending": "snap_back_to_bladed_stance",
            "single_leg_exposure_window": "low",
        }
    if tid == "low_kick":
        is_thai = school == "muay_thai"
        return {
            "kick_family": school,
            "kicking_leg": f"rear_{rear_side}",
            "chamber": "hip_whip_minimal_chamber" if is_thai else "compact_diagonal_step_chamber",
            "support_foot": f"lead_{lead_side}_ball_pivot_90deg",
            "path": "downward_diagonal_round_arc",
            "target_region": "lead_thigh_sciatic_line",
            "striking_surface": "lower_shin_bone" if is_thai else "lower_shin_and_instep",
            "ending": "carry_through_hip_turn" if is_thai else "fast_retract_to_dutch_guard",
            "single_leg_exposure_window": "high_on_miss_or_check" if is_thai else "moderate",
        }
    if tid in ("body_kick", "switch_kick"):
        leg_used = f"switched_{lead_side}_power_leg" if tid == "switch_kick" else f"rear_{rear_side}"
        return {
            "kick_family": school,
            "kicking_leg": leg_used,
            "chamber": "switch_hop_hip_load" if tid == "switch_kick" else "open_hip_torque_arc",
            "support_foot": "planted_support_ball_pivot_110deg",
            "path": "horizontal_round_arc_to_ribs",
            "target_region": "body_liver_or_floating_ribs",
            "striking_surface": "lower_shin_bone",
            "ending": "step_down_into_stance" if tid == "switch_kick" else "full_hip_turn_recovery",
            "single_leg_exposure_window": "high_catchable_window",
        }
    if tid == "head_kick":
        return {
            "kick_family": school,
            "kicking_leg": f"rear_{rear_side}",
            "chamber": "high_diagonal_knee_lift",
            "support_foot": f"lead_{lead_side}_high_ball_pivot_135deg",
            "path": "high_round_arc_to_temple_neck",
            "target_region": "head_temple_jaw",
            "striking_surface": "lower_shin_or_instep",
            "ending": "carry_through_spin_or_wide_retract",
            "single_leg_exposure_window": "high_on_whiff",
        }
    if tid == "spinning_back_kick":
        return {
            "kick_family": school,
            "kicking_leg": f"rear_{rear_side}",
            "chamber": "dorsal_180_spin_tight_tuck",
            "support_foot": f"lead_{lead_side}_180deg_heel_pivot",
            "path": "linear_back_thrust_out_of_spin",
            "target_region": "body_solar_plexus",
            "striking_surface": "heel_of_foot",
            "ending": "step_down_stance_completion",
            "single_leg_exposure_window": "high_if_stepped_around",
        }
    if tid == "axe_kick":
        return {
            "kick_family": school,
            "kicking_leg": f"rear_{rear_side}",
            "chamber": "high_vertical_arc_above_head",
            "support_foot": f"lead_{lead_side}_planted_pivot",
            "path": "vertical_hammer_drop",
            "target_region": "head_collarbone_crown",
            "striking_surface": "back_of_heel",
            "ending": "drop_down_to_lead_stance",
            "single_leg_exposure_window": "moderate",
        }
    # knee_body / jumping_knee
    return {
        "kick_family": school,
        "kicking_leg": f"rear_{rear_side}",
        "chamber": "airborne_double_knee_tuck" if tid == "jumping_knee" else "clinch_hip_thrust_spear",
        "support_foot": "airborne_none" if tid == "jumping_knee" else f"lead_{lead_side}_ball_rise",
        "path": "rising_vertical_spear" if tid == "jumping_knee" else "diagonal_upward_spear",
        "target_region": "head_chin" if tid == "jumping_knee" else "body_solar_plexus_ribs",
        "striking_surface": "pointed_kneecap",
        "ending": "two_foot_landing_recovery" if tid == "jumping_knee" else "re-establish_clinch_base",
        "single_leg_exposure_window": "high_landing_recovery" if tid == "jumping_knee" else "low",
    }


def select_kick_defense(defender_card: Dict[str, object], kick_tid: str, range_band: str) -> Tuple[str, str]:
    """Return (defense_action, outcome_effect) tailored to defender's defense & kicking dimensions."""
    def_opt = defender_card["dimensions"].get("defense") or ""
    kick_opt = defender_card["dimensions"].get("kicking") or ""

    # Sanda or parry_catch against body_kick / low_kick -> kick_catch!
    if kick_tid in ("body_kick", "low_kick", "switch_kick") and (
        kick_opt == "kicking.sanda" or def_opt == "defense.parry_catch"
    ):
        return "kick_catch", "caught"

    # check_frame against low_kick / body_kick -> shin check (reflects recoil leg damage!)
    if kick_tid in ("low_kick", "body_kick", "switch_kick") and def_opt == "defense.check_frame":
        return "check", "checked"

    # outfight against round kicks -> step back out of range
    if def_opt == "defense.outfight" and kick_tid in ("low_kick", "body_kick", "head_kick", "spinning_back_kick"):
        return "evade_step_back", "evaded"

    # slip_roll against high kicks -> lean back
    if def_opt in ("defense.slip_roll", "defense.shoulder_roll") and kick_tid in ("head_kick", "axe_kick"):
        return "lean_back", "evaded"

    # smother / sprawl_pummel against teep or body_kick -> jam step inside chamber
    if def_opt in ("defense.smother", "defense.sprawl_pummel") and kick_tid in ("teep", "body_kick"):
        return "jam_step", "jammed"

    return "shell_block", "blocked"


# ---------------------------------------------------------------------------
# 4. Card-Derived Damage Formula (No Physical Size/Speed Stats)
# ---------------------------------------------------------------------------

MENTALITY_POWER_MULT: Dict[str, float] = {
    "mentality.slugger": 1.32,
    "mentality.pressure": 1.15,
    "mentality.boxer_puncher": 1.10,
    "mentality.switch_hitter": 1.08,
    "mentality.technician": 1.04,
    "mentality.counter": 0.96,  # Jumps to 1.45x on a counter_hit!
    "mentality.swarmer": 0.88,
    "mentality.outboxer": 0.90,
    "mentality.spoiler": 0.88,
    "mentality.defensive": 0.86,
    "mentality.slickster": 0.92,
    "mentality.showman": 1.05,
}

STANCE_POWER_MULT: Dict[str, float] = {
    "stance.planted": 1.22,
    "stance.crouch": 1.15,
    "stance.balanced": 1.00,
    "stance.upright": 1.00,
    "stance.switch": 1.08,
    "stance.bladed": 0.92,
    "stance.shuffle": 0.90,
}

SLOT_DEPTH_MULT: Dict[int, float] = {
    1: 1.15,  # Brawler: only Plan A, sharpest single-plan power
    2: 1.05,  # Two-piece: Plan A + Plan B
    3: 1.00,  # Triad: balanced 3-plan versatility
    4: 0.95,  # Anomaly: 4-plan adaptability
}

LANDING_QUALITY_MULT: Dict[str, float] = {
    "evaded": 0.0,
    "miss": 0.0,
    "caught": 0.10,
    "checked": 0.10,
    "jammed": 0.20,
    "blocked": 0.18,
    "partial": 0.50,
    "clean": 1.00,
    "counter_hit": 1.40,
    "flush": 1.65,
}


def compute_card_derived_damage(
    k: Knowledge,
    attacker_card: Dict[str, object],
    defender_card: Dict[str, object],
    tid: str,
    landing_quality: str,
    attacker_state: Dict[str, object],
    defender_state: Dict[str, object],
    in_active_slot: bool = True,
) -> Dict[str, object]:
    """Compute qualitative Card-Derived Damage = Base * M_attacker * M_landing * M_defender."""
    stats = MOVE_BASE_STATS.get(tid, {"base": 1.0, "type": "impact", "line": "head_straight"})
    base = float(stats["base"])
    if base <= 0.0:
        return {
            "technique_id": tid,
            "base_damage": 0.0,
            "attacker_multiplier": 1.0,
            "landing_multiplier": 0.0,
            "defender_multiplier": 1.0,
            "final_damage": 0.0,
            "recoil_leg_damage_to_attacker": 0.0,
            "damage_type": stats["type"],
            "landing_quality": landing_quality,
        }

    tech = k.techniques.get(tid, {})
    target_region = tech.get("target_region", "head")
    if target_region not in ("head", "body", "leg"):
        target_region = "body"

    # 1. Attacker Build Multiplier
    mentality = attacker_card["dimensions"].get("mentality") or "mentality.boxer_puncher"
    stance = attacker_card["dimensions"].get("stance") or "stance.balanced"
    target_opt = attacker_card["dimensions"].get("target") or "target.mixer"
    kicking_opt = attacker_card["dimensions"].get("kicking") or "kicking.none"

    m_mentality = MENTALITY_POWER_MULT.get(mentality, 1.0)
    if mentality == "mentality.counter" and landing_quality == "counter_hit":
        m_mentality = 1.45

    m_stance = STANCE_POWER_MULT.get(stance, 1.0)
    if stance == "stance.crouch" and tid in ("hook", "body_hook", "uppercut"):
        m_stance *= 1.08
    if stance == "stance.switch" and "switch_step" in attacker_state.get("setups", []):
        m_stance *= 1.10

    m_kicking = 1.0
    if tid in KICK_IDS:
        if kicking_opt == "kicking.muay_thai" and tid in ("low_kick", "body_kick", "head_kick", "knee_body", "jumping_knee"):
            m_kicking = 1.25
        elif kicking_opt == "kicking.dutch" and tid == "low_kick":
            m_kicking = 1.20
        elif kicking_opt == "kicking.karate" and tid in ("side_kick", "spinning_back_kick", "axe_kick", "teep"):
            m_kicking = 1.18

    m_target_spec = 1.0
    if (
        (target_opt == "target.head_hunter" and target_region == "head")
        or (target_opt in ("target.body_puncher", "target.liver_ribs") and target_region == "body")
        or (target_opt == "target.leg_chopper" and target_region == "leg")
        or (target_opt == "target.knee_clincher" and tid in ("knee_body", "jumping_knee", "collar_tie"))
    ):
        m_target_spec = 1.15

    slot_depth = SLOT_DEPTH_MULT.get(int(attacker_card.get("slot_count", 2)), 1.0)
    m_slot = slot_depth if in_active_slot else 0.80

    # Attacker fatigue & battered kicking leg penalty
    att_fatigue = float(attacker_state.get("fatigue", 0.0))
    att_leg_dmg = float(attacker_state.get("damage", {}).get("leg", 0.0))
    m_fatigue = max(0.72, 1.0 - 0.015 * att_fatigue)
    m_leg_wear = max(0.65, 1.0 - 0.04 * att_leg_dmg) if tid in KICK_IDS else max(0.82, 1.0 - 0.02 * att_leg_dmg)

    m_attacker = m_mentality * m_stance * m_kicking * m_target_spec * m_slot * m_fatigue * m_leg_wear

    # 2. Landing Quality Multiplier
    m_landing = LANDING_QUALITY_MULT.get(landing_quality, 1.0)
    if defender_state.get("wall_proximity") == "near" and m_landing > 0:
        m_landing *= 1.15

    # 3. Defender Build Mitigation
    def_hands_id = defender_card["dimensions"].get("hands")
    def_opt_id = defender_card["dimensions"].get("defense")
    hands_ratings = (
        k.options[def_hands_id]["mma_adaptation"]["ratings"]
        if def_hands_id and def_hands_id in k.options
        else {"head_coverage": 3, "body_coverage": 3, "takedown_readiness": 3}
    )
    if target_region == "head":
        cov = hands_ratings.get("head_coverage", 3)
    elif target_region == "body":
        cov = hands_ratings.get("body_coverage", 3)
    else:
        cov = hands_ratings.get("takedown_readiness", 3)

    m_guard = 1.16 - 0.07 * cov  # rating 5 -> 0.81x, rating 1 -> 1.09x
    if def_opt_id == "defense.block_absorb" and target_region == "head":
        m_guard *= 0.88

    # Compounding wear on already damaged region
    existing_reg_dmg = float(defender_state.get("damage", {}).get(target_region, 0.0))
    m_wear = 1.0 + 0.06 * existing_reg_dmg

    m_defender = max(0.55, m_guard * m_wear)

    final_damage = round(base * m_attacker * m_landing * m_defender, 3)

    # Checked low/body kicks reflect shin recoil damage back onto the kicker's leg!
    recoil_leg_damage = 0.0
    if landing_quality == "checked" and tid in ("low_kick", "body_kick", "switch_kick"):
        recoil_leg_damage = round(base * 0.65 * m_attacker, 3)

    return {
        "technique_id": tid,
        "target_region": target_region,
        "base_damage": base,
        "attacker_multiplier": round(m_attacker, 3),
        "landing_multiplier": round(m_landing, 3),
        "defender_multiplier": round(m_defender, 3),
        "final_damage": final_damage,
        "recoil_leg_damage_to_attacker": recoil_leg_damage,
        "damage_type": stats["type"],
        "landing_quality": landing_quality,
    }


# ---------------------------------------------------------------------------
# 5. Slots as Tactical Gameplans (Depth-vs-Breadth + Triggers + Abandon Rules)
# ---------------------------------------------------------------------------

def build_slot_plans(k: Knowledge, card: Dict[str, object], ruleset: str = "mma") -> List[Dict[str, object]]:
    """Build executable SlotPlan objects from card.synchronized_capabilities."""
    all_avail = set(available(k, card, ruleset))
    plans: List[Dict[str, object]] = []
    slots = admitted_slots(card, k)
    depth_mult = SLOT_DEPTH_MULT.get(len(slots), 1.0)
    kicking_opt = card["dimensions"].get("kicking") or "kicking.none"
    target_opt = card["dimensions"].get("target") or "target.mixer"

    for idx, slot in enumerate(slots):
        caps = set(slot.get("capabilities", []))
        # Determine moves unlocked by this slot's capabilities (plus basic movement/feints)
        slot_moves = [
            tid
            for tid in card["active_techniques"]
            if tid in all_avail
            and k.techniques[tid]["kind"] in ("punch", "kick", "knee", "takedown", "grip", "control", "submission")
            and (set(k.techniques[tid]["required_capabilities"]) & caps)
        ]
        if not slot_moves:
            slot_moves = [
                tid
                for tid in card["active_techniques"]
                if tid in all_avail and k.techniques[tid]["kind"] in ("punch", "kick", "takedown", "grip")
            ]

        # Order sequence according to school & target identity rather than alphabetical sorting
        ordered_seq: List[str] = []
        if "sanda" in caps and "sanda_sweep" in slot_moves:
            ordered_seq.extend([m for m in ("side_kick", "low_kick", "sanda_sweep", "body_kick") if m in slot_moves])
        elif "judo" in caps or "wrestling" in caps:
            ordered_seq.extend([m for m in ("body_lock", "outside_trip", "double_leg", "single_leg", "ride") if m in slot_moves])
        elif "bjj" in caps:
            ordered_seq.extend([m for m in ("collar_tie", "guard_pull", "armbar") if m in slot_moves])
        elif "clinch" in caps:
            ordered_seq.extend([m for m in ("collar_tie", "knee_body", "body_lock", "pummel") if m in slot_moves])
        elif "kickboxing" in caps:
            if kicking_opt == "kicking.dutch":
                ordered_seq.extend([m for m in ("jab", "cross", "body_hook", "low_kick", "body_kick") if m in slot_moves or m in all_avail])
            elif kicking_opt == "kicking.muay_thai":
                ordered_seq.extend([m for m in ("teep", "body_kick", "low_kick", "knee_body") if m in slot_moves or m in all_avail])
            else:
                ordered_seq.extend([m for m in ("teep", "low_kick", "body_kick") if m in slot_moves])
        elif "karate" in caps:
            ordered_seq.extend([m for m in ("side_kick", "jab", "cross") if m in slot_moves or m in all_avail])
        elif "boxing" in caps:
            if target_opt == "target.body_puncher":
                ordered_seq.extend([m for m in ("jab", "body_hook", "cross", "uppercut", "hook") if m in slot_moves])
            elif card["dimensions"].get("mentality") == "mentality.counter":
                ordered_seq.extend([m for m in ("jab", "cross", "uppercut", "hook", "body_hook") if m in slot_moves])
            else:
                ordered_seq.extend([m for m in ("jab", "cross", "hook", "body_hook", "uppercut") if m in slot_moves])
        else:
            ordered_seq.extend(slot_moves)

        # Deduplicate while preserving order
        seen_m = set()
        clean_seq = []
        for m in ordered_seq + slot_moves:
            if m in all_avail and m not in seen_m:
                seen_m.append(m) if False else None
                seen_m.add(m)
                clean_seq.append(m)

        home_range = "punch"
        if any(c in caps for c in ("bjj", "wrestling", "judo", "clinch")):
            home_range = "clinch"
        elif any(c in caps for c in ("kickboxing", "karate", "sanda")):
            home_range = "kick"

        next_slot_id = slots[(idx + 1) % len(slots)]["id"]
        plans.append(
            {
                "slot_id": slot["id"],
                "slot_index": idx,
                "capabilities": sorted(caps),
                "sequence": clean_seq or ["jab"],
                "home_range": home_range,
                "depth_multiplier": depth_mult,
                "trigger": "fight_start" if idx == 0 else "slot_stalled_or_countered",
                "abandon_threshold": 999 if len(slots) == 1 else 2,
                "next_slot_id": next_slot_id,
            }
        )
    # Order plans so the slot matching preferred_ranges[0] is the opening Plan A
    pref_first = (card.get("preferred_ranges") or ["punch"])[0]
    plans.sort(key=lambda p: (0 if p["home_range"] == pref_first else 1, p["slot_index"]))
    for i, p in enumerate(plans):
        p["trigger"] = "fight_start" if i == 0 else "slot_stalled_or_countered"
        p["next_slot_id"] = plans[(i + 1) % len(plans)]["slot_id"]
    return plans


# ---------------------------------------------------------------------------
# 6. Grappling Position & Grip Map State Helper
# ---------------------------------------------------------------------------

def update_grappling_position(
    actor_state: Dict[str, object],
    defender_state: Dict[str, object],
    tid: str,
    outcome: str,
    actor_card: Dict[str, object],
) -> str:
    """Update explicit grappling position, sub-grips, and 3-stage submission progress."""
    if outcome not in ("clean", "flush", "counter_hit", "partial"):
        if outcome == "jammed":
            actor_state["grappling_position"] = "clinch_over_under"
            defender_state["grappling_position"] = "clinch_over_under"
        return str(actor_state.get("grappling_position", "standing_neutral"))

    tie_opt = actor_card["dimensions"].get("tie")
    if tid == "collar_tie":
        pos = "thai_plum" if tie_opt == "tie.thai_plum" else "collar_tie"
        actor_state["grappling_position"] = pos
        defender_state["grappling_position"] = "clinch_controlled"
        actor_state["sub_grips"]["head_position"] = "inside_control"
        actor_state["grip"], defender_state["grip"] = "collar", "controlled"
    elif tid == "body_lock":
        actor_state["grappling_position"] = "front_body_lock"
        defender_state["grappling_position"] = "clinch_controlled"
        actor_state["sub_grips"]["underhooks"] = 2
        actor_state["grip"], defender_state["grip"] = "body_lock", "controlled"
    elif tid == "pummel":
        actor_state["grappling_position"] = "double_underhooks"
        defender_state["grappling_position"] = "over_under_defending"
        actor_state["sub_grips"]["underhooks"] = min(2, actor_state["sub_grips"].get("underhooks", 0) + 1)
    elif tid in ("double_leg", "single_leg", "outside_trip", "sanda_sweep"):
        actor_state["posture"] = defender_state["posture"] = "ground"
        actor_state["grappling_position"] = "side_control" if tid in ("outside_trip", "sanda_sweep") else "half_guard_top"
        defender_state["grappling_position"] = "bottom_pinned"
        actor_state["grip"], defender_state["grip"] = "top", "bottom"
        actor_state["control_marks"] += 1
    elif tid == "guard_pull":
        actor_state["posture"] = defender_state["posture"] = "ground"
        actor_state["grappling_position"] = "closed_guard_bottom"
        defender_state["grappling_position"] = "in_closed_guard_top"
        actor_state["grip"], defender_state["grip"] = "bottom", "top"
        actor_state["control_marks"] += 1
    elif tid == "ride":
        actor_state["grappling_position"] = "mount_or_back_ride"
        defender_state["grappling_position"] = "flattened_bottom"
        actor_state["control_marks"] += 1
    elif tid == "armbar":
        # 3-stage submission progression: isolate_limb (1) -> lock_hold (2) -> finish (3)
        stage = int(actor_state.get("submission_stage", 0)) + 1
        actor_state["submission_stage"] = stage
        actor_state["sub_grips"]["wrist_control"] = True
        actor_state["grappling_position"] = f"armbar_stage_{stage}"
        actor_state["control_marks"] += 1
    elif tid == "escape":
        actor_state["posture"] = defender_state["posture"] = "standing"
        actor_state["grappling_position"] = defender_state["grappling_position"] = "standing_neutral"
        actor_state["grip"] = defender_state["grip"] = None
        actor_state["submission_stage"] = defender_state["submission_stage"] = 0

    return str(actor_state["grappling_position"])


# ---------------------------------------------------------------------------
# 7. Level 2: Exchange-by-Exchange Simulator (`simulate_fight_v2`)
# ---------------------------------------------------------------------------

def simulate_fight_v2(
    a,
    b,
    ruleset: str = "mma",
    duration_s: float = 60.0,
    seed: int = 42,
    arena: str = "cage",
    vertical_mode: str = "grounded",
    knowledge: Optional[Knowledge] = None,
) -> Dict[str, object]:
    """Run a clock-driven, card-authentic v2 fight simulation between fighter A and fighter B."""
    k = knowledge or Knowledge()
    card_a, card_b = k.card(a), k.card(b)
    cards = {card_a["fighter_id"]: card_a, card_b["fighter_id"]: card_b}
    ids = [card_a["fighter_id"], card_b["fighter_id"]]
    rng = random.Random(seed)

    arena_cfg = ARENA_PRESETS.get(arena, ARENA_PRESETS["cage"])
    half_w = float(arena_cfg["half_width_m"])

    slot_plans = {
        fid: build_slot_plans(k, cards[fid], ruleset)
        for fid in ids
    }

    actors: Dict[str, Dict[str, object]] = {}
    for fid, x0 in zip(ids, [-0.8, 0.8]):
        c = cards[fid]
        actors[fid] = {
            "fighter_id": fid,
            "name": c["name"],
            "position": [x0, 0.0],
            "orientation": "orthodox" if c["orientation"] == "switching" else c["orientation"],
            "stance": c["dimensions"]["stance"],
            "guard": c["dimensions"]["hands"],
            "posture": "standing",
            "grappling_position": "standing_neutral",
            "grip": None,
            "sub_grips": {"underhooks": 0, "wrist_control": False, "head_position": "neutral"},
            "submission_stage": 0,
            "wall_proximity": "far",
            "damage": {"head": 0.0, "body": 0.0, "leg": 0.0},
            "fatigue": 0.0,
            "contact_marks": 0,
            "control_marks": 0,
            "active_slot_idx": 0,
            "slot_Cursor": 0,
            "slot_stalls": 0,
            "slot_switches": 0,
            "kick_checks_suffered": 0,
            "recent_moves": [],
            "setups": [],
        }

    clock_frames = 0
    max_frames = int(duration_s * 24)
    range_band = "kick" if ruleset == "mma" else "punch"
    exchanges: List[Dict[str, object]] = []
    finish_reason: Optional[str] = None
    winner_id: Optional[str] = None
    last_attacker_id: Optional[str] = None
    last_recovery_drag: float = 0.0

    while clock_frames < max_frames:
        # 1. Decide who initiates this exchange from Tempo, Mentality, Recovery Cooldown & Fatigue
        scores_init = {}
        for fid in ids:
            c = cards[fid]
            st = actors[fid]
            mentality = c["dimensions"].get("mentality")
            base_tempo = float(c.get("tempo", 3))
            # Counter-fighters wait for the opponent to commit first unless opponent is recovering
            counter_wait = -0.8 if (mentality == "mentality.counter" and last_attacker_id in (None, fid)) else (
                0.6 if mentality in ("mentality.swarmer", "mentality.pressure") else 0.0
            )
            recovery_cooldown = -last_recovery_drag if fid == last_attacker_id else 0.0
            fatigue_drag = -0.08 * float(st["fatigue"])
            leg_drag = -0.10 * float(st["damage"]["leg"])
            scores_init[fid] = base_tempo + counter_wait + recovery_cooldown + fatigue_drag + leg_drag + rng.uniform(-0.85, 0.85)

        attacker_id = max(ids, key=lambda i: scores_init[i])
        defender_id = next(i for i in ids if i != attacker_id)
        att_card, def_card = cards[attacker_id], cards[defender_id]
        att_state, def_state = actors[attacker_id], actors[defender_id]

        # 2. Check active slot plan & select candidate technique
        plans = slot_plans[attacker_id]
        active_plan = plans[int(att_state["active_slot_idx"]) % len(plans)]
        seq: List[str] = list(active_plan["sequence"])

        # Adapt range toward active slot's home_range
        if att_state["posture"] == "ground":
            range_band = "ground"
        elif att_state["grip"] in ("collar", "body_lock"):
            range_band = "clinch"
        else:
            range_band = str(active_plan["home_range"])
            if ruleset == "boxing" and range_band in ("kick", "clinch", "ground"):
                range_band = "punch"

        # If attacker has suffered >= 2 checked/caught kicks, de-prioritize kicks
        filtered_seq = [
            m for m in seq
            if not (att_state["kick_checks_suffered"] >= 2 and m in ("low_kick", "body_kick"))
        ] or seq

        # Pick move from slot sequence while avoiding repeating the exact last move 3x
        cursor = int(att_state["slot_Cursor"])
        tid = filtered_seq[cursor % len(filtered_seq)]
        att_state["slot_Cursor"] = cursor + 1

        # Ground overrides
        if range_band == "ground":
            avail_t = set(available(k, att_card, ruleset))
            if att_state["grip"] == "top" and "ride" in avail_t:
                tid = "ride"
            elif att_state["grip"] == "bottom" and "armbar" in avail_t:
                tid = "armbar"
            elif "escape" in avail_t:
                tid = "escape"

        # Calculate Read-Memory Penalty if attacker repeats the same move consecutively
        recent = att_state["recent_moves"]
        consecutive_repeats = 0
        for prev_m in reversed(recent):
            if prev_m == tid:
                consecutive_repeats += 1
            else:
                break
        recent.append(tid)
        if len(recent) > 6:
            recent.pop(0)

        # 3. Resolve Exchange Outcome (Attacker vs. Defender Defense/Hands/Mentality + Read Penalty)
        kick_detail = unroll_kick_anatomy(tid, att_card, str(att_state["orientation"]))
        defense_used = None
        counter_triggered = False

        # Base accuracy from mentality & setup
        att_mentality = att_card["dimensions"].get("mentality")
        acc = 0.62
        if att_mentality == "mentality.slugger":
            acc -= 0.10
        elif att_mentality in ("mentality.technician", "mentality.boxer_puncher", "mentality.outboxer"):
            acc += 0.08
        acc -= 0.22 * consecutive_repeats  # Heavy penalty for spamming the same move!

        def_mentality = def_card["dimensions"].get("mentality")
        def_option = def_card["dimensions"].get("defense")

        roll = rng.random()
        kick_def_bonus = 0.22 if (
            def_card["dimensions"].get("kicking") == "kicking.sanda"
            or def_card["dimensions"].get("defense") in ("defense.check_frame", "defense.outfight")
        ) else 0.10
        if tid in KICK_IDS and tid != "knee_body" and roll > acc - kick_def_bonus:
            defense_used, outcome = select_kick_defense(def_card, tid, range_band)
        elif roll > acc:
            # Defender successfully defends or counters!
            if def_mentality == "mentality.counter" or consecutive_repeats >= 1:
                defense_used = "parry" if def_option == "defense.parry_catch" else "slip"
                outcome = "evaded"
                counter_triggered = True
            elif def_option in ("defense.slip_roll", "defense.shoulder_roll", "defense.outfight"):
                defense_used = "slip" if "slip" in def_option else "retreat"
                outcome = "evaded"
            else:
                defense_used = "shell_block"
                outcome = "blocked"
        else:
            if roll < acc * 0.32 and ("feint" in att_state["setups"] or "pivot" in att_state["setups"]):
                outcome = "flush"
            elif roll < acc * 0.78:
                outcome = "clean"
            else:
                outcome = "partial"

        # 4. Apply Card-Derived Damage & State Updates
        dmg_info = compute_card_derived_damage(
            k,
            att_card,
            def_card,
            tid,
            outcome,
            att_state,
            def_state,
            in_active_slot=True,
        )

        # Update regional damage & recoil shin damage on checked kicks
        if dmg_info["final_damage"] > 0:
            reg = str(dmg_info["target_region"])
            def_state["damage"][reg] = round(def_state["damage"][reg] + dmg_info["final_damage"], 3)
            if outcome in ("clean", "flush", "counter_hit", "partial"):
                att_state["contact_marks"] += 1
            if dmg_info["damage_type"] == "stamina_drain":
                def_state["fatigue"] = round(def_state["fatigue"] + 0.6 * dmg_info["final_damage"], 2)

        if dmg_info["recoil_leg_damage_to_attacker"] > 0:
            att_state["damage"]["leg"] = round(
                att_state["damage"]["leg"] + dmg_info["recoil_leg_damage_to_attacker"], 3
            )
            att_state["kick_checks_suffered"] += 1

        # Battered lead leg forces an involuntary stance switch!
        forced_stance_switch = False
        if def_state["damage"]["leg"] >= 4.5 and not def_state.get("leg_compromised"):
            def_state["leg_compromised"] = True
            def_state["orientation"] = "southpaw" if def_state["orientation"] == "orthodox" else "orthodox"
            forced_stance_switch = True

        # Update grappling position & 2D arena position
        grappling_pos = update_grappling_position(att_state, def_state, tid, outcome, att_card)
        if att_mentality in ("mentality.swarmer", "mentality.pressure") and arena_cfg["has_walls"]:
            # Pressure fighters drive defender toward the cage/ropes
            direction = 1.0 if def_state["position"][0] >= 0 else -1.0
            def_state["position"][0] = max(-half_w, min(half_w, def_state["position"][0] + 0.45 * direction))
            if half_w - abs(def_state["position"][0]) <= float(arena_cfg["wall_near_m"]):
                def_state["wall_proximity"] = "near"
        elif def_mentality == "mentality.outboxer" and outcome in ("evaded", "blocked"):
            # Outboxer pivots back toward center
            def_state["position"][0] *= 0.6
            def_state["wall_proximity"] = "far"

        # Advance 24fps Fight Clock
        m_stats = MOVE_BASE_STATS.get(tid, {"setup_f": 4, "exec_f": 8, "hold_f": 2, "rec_f": 8})
        exchange_frames = int(m_stats["setup_f"]) + int(m_stats["exec_f"]) + int(m_stats["hold_f"]) + int(m_stats["rec_f"])
        tempo_gap_frames = max(6, int(36 - 4 * max(att_card.get("tempo", 3), def_card.get("tempo", 3))))
        t_start = round(clock_frames / 24.0, 2)
        clock_frames += exchange_frames + tempo_gap_frames
        t_end = round(clock_frames / 24.0, 2)
        att_state["fatigue"] = round(att_state["fatigue"] + 0.35, 2)
        last_attacker_id = attacker_id
        last_recovery_drag = 1.45 + 0.08 * float(m_stats["rec_f"]) + (0.65 if outcome in ("evaded", "blocked", "checked", "caught") else 0.0)

        counter_Followup_event = None

        # 5. Immediate Counter-Attack or Caught-Kick Dump!
        if outcome == "caught":
            att_state["kick_checks_suffered"] += 1
            dump_tid = "sanda_sweep" if "sanda_sweep" in available(k, def_card, ruleset) else (
                "outside_trip" if "outside_trip" in available(k, def_card, ruleset) else "cross"
            )
            dump_dmg = compute_card_derived_damage(
                k, def_card, att_card, dump_tid, "counter_hit", def_state, att_state, in_active_slot=True
            )
            reg_c = str(dump_dmg["target_region"])
            att_state["damage"][reg_c] = round(att_state["damage"][reg_c] + dump_dmg["final_damage"], 3)
            def_state["contact_marks"] += 1
            update_grappling_position(def_state, att_state, dump_tid, "counter_hit", def_card)
            counter_Followup_event = {
                "counter_actor_id": defender_id,
                "trigger": "kick_catch_dump",
                "technique_id": dump_tid,
                "damage": dump_dmg,
            }
        elif counter_triggered:
            def_avail = available(k, def_card, ruleset)
            c_tid = "cross" if "cross" in def_avail else ("hook" if "hook" in def_avail else "haymaker")
            c_dmg = compute_card_derived_damage(
                k, def_card, att_card, c_tid, "counter_hit", def_state, att_state, in_active_slot=True
            )
            reg_c = str(c_dmg["target_region"])
            att_state["damage"][reg_c] = round(att_state["damage"][reg_c] + c_dmg["final_damage"], 3)
            def_state["contact_marks"] += 1
            counter_Followup_event = {
                "counter_actor_id": defender_id,
                "trigger": f"{defense_used}_counter",
                "technique_id": c_tid,
                "damage": c_dmg,
            }

        # 6. Slot Adaptation Check (Switch Slot Plan when stalled or countered twice)
        slot_switched_to = None
        if outcome in ("evaded", "blocked", "checked", "caught", "jammed"):
            att_state["slot_stalls"] += 1
            if att_state["slot_stalls"] >= int(active_plan["abandon_threshold"]) and len(plans) > 1:
                att_state["active_slot_idx"] = (int(att_state["active_slot_idx"]) + 1) % len(plans)
                att_state["slot_Cursor"] = 0
                att_state["slot_stalls"] = 0
                att_state["slot_switches"] += 1
                slot_switched_to = plans[int(att_state["active_slot_idx"])]["slot_id"]
        else:
            att_state["slot_stalls"] = 0

        exchanges.append(
            {
                "exchange_index": len(exchanges) + 1,
                "t_start": t_start,
                "t_end": t_end,
                "frames": exchange_frames,
                "range": range_band,
                "attacker_id": attacker_id,
                "defender_id": defender_id,
                "active_slot_id": active_plan["slot_id"],
                "technique_id": tid,
                "outcome": outcome,
                "defense_used": defense_used,
                "kick_anatomy": kick_detail,
                "damage": dmg_info,
                "counter_followup": counter_Followup_event,
                "grappling_position": grappling_pos,
                "forced_stance_switch": forced_stance_switch,
                "slot_switched_to": slot_switched_to,
            }
        )

        # 7. Check Finish Conditions (KO/TKO via regional damage threshold or 3-stage Submission)
        for fid in ids:
            opp_id = next(i for i in ids if i != fid)
            opp_dmg = actors[opp_id]["damage"]
            if opp_dmg["head"] >= 11.5:
                winner_id = fid
                finish_reason = "KO/TKO (head damage accumulation)"
                break
            if opp_dmg["body"] >= 12.0:
                winner_id = fid
                finish_reason = "TKO (body/liver attrition)"
                break
            if opp_dmg["leg"] >= 12.5:
                winner_id = fid
                finish_reason = "TKO (leg kicks / compromised support)"
                break
            if int(actors[fid].get("submission_stage", 0)) >= 3:
                winner_id = fid
                finish_reason = "Submission (stage 3 lock completion)"
                break
        if winner_id:
            break

    # 8. If Clock Expires, Score by Weighted Damage + Control Marks
    if not winner_id:
        scores = {}
        for fid in ids:
            opp_id = next(i for i in ids if i != fid)
            opp_d = actors[opp_id]["damage"]
            total_dmg_dealt = opp_d["head"] * 1.15 + opp_d["body"] * 1.05 + opp_d["leg"] * 1.0
            scores[fid] = total_dmg_dealt + 1.5 * float(actors[fid]["control_marks"])
        winner_id = max(ids, key=lambda i: (scores[i], i))
        finish_reason = "Decision (clock expired; card-derived damage + control)"

    return {
        "version": "block-v2",
        "ruleset": ruleset,
        "arena": arena,
        "vertical_mode": vertical_mode,
        "seed": seed,
        "duration_requested_s": duration_s,
        "duration_actual_s": round(clock_frames / 24.0, 2),
        "winner_id": winner_id,
        "winner_name": cards[winner_id]["name"],
        "finish_reason": finish_reason,
        "exchange_count": len(exchanges),
        "actors_final": actors,
        "slot_plans": slot_plans,
        "exchanges": exchanges,
    }


# ---------------------------------------------------------------------------
# 8. Level 3: Many-Runs Monte Carlo Simulator & Realistic Director Selector
# ---------------------------------------------------------------------------

def simulate_many_v2(
    a,
    b,
    runs: int = 50,
    ruleset: str = "mma",
    duration_s: float = 60.0,
    arena: str = "cage",
    vertical_mode: str = "grounded",
    directed_winner: Optional[str] = None,
    knowledge: Optional[Knowledge] = None,
) -> Dict[str, object]:
    """Run N seeded v2 fights to compute empirical win rates, method breakdown, and realistic directed runs."""
    k = knowledge or Knowledge()
    card_a, card_b = k.card(a), k.card(b)
    id_a, id_b = card_a["fighter_id"], card_b["fighter_id"]
    wins = {id_a: 0, id_b: 0}
    methods: Dict[str, int] = {}
    matching_runs: List[Dict[str, object]] = []
    all_runs: List[Dict[str, object]] = []

    for s in range(1, runs + 1):
        sim = simulate_fight_v2(
            card_a,
            card_b,
            ruleset=ruleset,
            duration_s=duration_s,
            seed=s,
            arena=arena,
            vertical_mode=vertical_mode,
            knowledge=k,
        )
        w = str(sim["winner_id"])
        wins[w] += 1
        m_key = str(sim["finish_reason"]).split(" (")[0]
        methods[m_key] = methods.get(m_key, 0) + 1
        all_runs.append(sim)
        if directed_winner and w == directed_winner:
            matching_runs.append(sim)

    selected_run = matching_runs[0] if matching_runs else all_runs[0]
    return {
        "fighter_a": id_a,
        "fighter_b": id_b,
        "runs": runs,
        "ruleset": ruleset,
        "arena": arena,
        "win_counts": wins,
        "empirical_win_rate_a": round(wins[id_a] / runs, 3),
        "empirical_win_rate_b": round(wins[id_b] / runs, 3),
        "method_breakdown": methods,
        "directed_winner": directed_winner,
        "representative_fight": selected_run,
    }
