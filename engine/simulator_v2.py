"""BLOCK Fight Simulator v2: Dynamic Defensive Posture, Per-Lane Readiness Calculator,
Exchange Resolver, First-Class Kicking Subsystem, Grappling Position Map, Slot Gameplans,
Real 24fps Fight Clock, 2D Arena Presets, and Monte Carlo Many-Runs Simulator.

Implements the complete v2 specification while preserving 100% backward compatibility
with all v1 modules and all 107 existing tests.
"""

from __future__ import annotations

import copy
import math
import random
from typing import Dict, List, Optional, Tuple

import jsonschema

from .capabilities import admitted_slots, available, training
from .ontology import ROOT, Knowledge, read


LANES = [
    "head_straight",
    "head_hook",
    "head_uppercut",
    "body",
    "leg",
    "entry",
    "clinch",
    "single_support",
]


# ---------------------------------------------------------------------------
# 1. Move Base Stats & Lane / Frame Catalog
# ---------------------------------------------------------------------------

MOVE_BASE_STATS: Dict[str, Dict[str, object]] = {
    "step": {"base": 0.0, "type": "movement", "setup_f": 3, "exec_f": 6, "hold_f": 0, "rec_f": 4, "lane": "space"},
    "retreat": {"base": 0.0, "type": "movement", "setup_f": 2, "exec_f": 6, "hold_f": 0, "rec_f": 4, "lane": "space"},
    "pivot": {"base": 0.0, "type": "movement", "setup_f": 3, "exec_f": 7, "hold_f": 0, "rec_f": 4, "lane": "space"},
    "switch_step": {"base": 0.0, "type": "movement", "setup_f": 3, "exec_f": 8, "hold_f": 0, "rec_f": 5, "lane": "space"},
    "feint": {"base": 0.0, "type": "feint", "setup_f": 2, "exec_f": 5, "hold_f": 0, "rec_f": 3, "lane": "space"},
    "jab": {"base": 1.0, "type": "buildup", "setup_f": 3, "exec_f": 5, "hold_f": 2, "rec_f": 5, "lane": "head_straight"},
    "cross": {"base": 2.0, "type": "impact", "setup_f": 5, "exec_f": 7, "hold_f": 3, "rec_f": 8, "lane": "head_straight"},
    "hook": {"base": 2.5, "type": "impact", "setup_f": 5, "exec_f": 8, "hold_f": 3, "rec_f": 9, "lane": "head_hook"},
    "body_hook": {"base": 2.3, "type": "stamina_drain", "setup_f": 5, "exec_f": 8, "hold_f": 3, "rec_f": 8, "lane": "body"},
    "uppercut": {"base": 2.7, "type": "impact", "setup_f": 6, "exec_f": 8, "hold_f": 3, "rec_f": 10, "lane": "head_uppercut"},
    "haymaker": {"base": 3.2, "type": "impact", "setup_f": 9, "exec_f": 11, "hold_f": 4, "rec_f": 16, "lane": "head_hook"},
    "teep": {"base": 1.4, "type": "stamina_drain", "setup_f": 4, "exec_f": 7, "hold_f": 2, "rec_f": 7, "lane": "body"},
    "low_kick": {"base": 2.2, "type": "buildup", "setup_f": 5, "exec_f": 8, "hold_f": 3, "rec_f": 10, "lane": "leg"},
    "body_kick": {"base": 2.6, "type": "stamina_drain", "setup_f": 6, "exec_f": 9, "hold_f": 3, "rec_f": 12, "lane": "body"},
    "side_kick": {"base": 2.3, "type": "impact", "setup_f": 5, "exec_f": 8, "hold_f": 3, "rec_f": 10, "lane": "body"},
    "head_kick": {"base": 3.5, "type": "impact", "setup_f": 7, "exec_f": 10, "hold_f": 4, "rec_f": 15, "lane": "head_hook"},
    "switch_kick": {"base": 2.8, "type": "stamina_drain", "setup_f": 6, "exec_f": 9, "hold_f": 3, "rec_f": 11, "lane": "body"},
    "spinning_back_kick": {"base": 3.3, "type": "impact", "setup_f": 8, "exec_f": 10, "hold_f": 4, "rec_f": 16, "lane": "body", "vertical": "athletic"},
    "axe_kick": {"base": 3.1, "type": "impact", "setup_f": 8, "exec_f": 11, "hold_f": 3, "rec_f": 14, "lane": "head_straight", "vertical": "athletic"},
    "knee_body": {"base": 2.8, "type": "stamina_drain", "setup_f": 4, "exec_f": 7, "hold_f": 3, "rec_f": 8, "lane": "body"},
    "jumping_knee": {"base": 3.6, "type": "impact", "setup_f": 7, "exec_f": 10, "hold_f": 4, "rec_f": 16, "lane": "head_uppercut", "vertical": "athletic"},
    "pummel": {"base": 0.4, "type": "stamina_drain", "setup_f": 4, "exec_f": 8, "hold_f": 2, "rec_f": 6, "lane": "clinch"},
    "collar_tie": {"base": 0.5, "type": "stamina_drain", "setup_f": 4, "exec_f": 7, "hold_f": 2, "rec_f": 6, "lane": "clinch"},
    "body_lock": {"base": 0.6, "type": "stamina_drain", "setup_f": 5, "exec_f": 8, "hold_f": 2, "rec_f": 7, "lane": "clinch"},
    "cage_plum": {"base": 0.8, "type": "stamina_drain", "setup_f": 5, "exec_f": 8, "hold_f": 3, "rec_f": 7, "lane": "clinch"},
    "shield_frame": {"base": 0.5, "type": "buildup", "setup_f": 3, "exec_f": 6, "hold_f": 2, "rec_f": 5, "lane": "head_straight"},
    "double_leg": {"base": 2.4, "type": "impact", "setup_f": 6, "exec_f": 12, "hold_f": 4, "rec_f": 14, "lane": "entry"},
    "single_leg": {"base": 2.1, "type": "buildup", "setup_f": 5, "exec_f": 11, "hold_f": 4, "rec_f": 12, "lane": "entry"},
    "outside_trip": {"base": 2.5, "type": "impact", "setup_f": 5, "exec_f": 10, "hold_f": 4, "rec_f": 12, "lane": "clinch"},
    "sanda_sweep": {"base": 2.6, "type": "impact", "setup_f": 4, "exec_f": 9, "hold_f": 4, "rec_f": 11, "lane": "single_support"},
    "guard_pull": {"base": 0.8, "type": "stamina_drain", "setup_f": 4, "exec_f": 10, "hold_f": 2, "rec_f": 8, "lane": "clinch"},
    "ride": {"base": 1.1, "type": "stamina_drain", "setup_f": 4, "exec_f": 14, "hold_f": 4, "rec_f": 9, "lane": "clinch"},
    "armbar": {"base": 3.8, "type": "submission", "setup_f": 8, "exec_f": 16, "hold_f": 6, "rec_f": 12, "lane": "clinch"},
    "escape": {"base": 0.0, "type": "movement", "setup_f": 5, "exec_f": 12, "hold_f": 0, "rec_f": 8, "lane": "space"},
    "wall_tie": {"base": 0.7, "type": "stamina_drain", "setup_f": 4, "exec_f": 8, "hold_f": 2, "rec_f": 6, "lane": "clinch"},
    "wall_punch": {"base": 2.4, "type": "stamina_drain", "setup_f": 4, "exec_f": 8, "hold_f": 3, "rec_f": 7, "lane": "body"},
}


ARENA_PRESETS: Dict[str, Dict[str, object]] = {
    "ring": {"id": "ring", "half_width_m": 3.0, "wall_near_m": 0.6, "has_walls": True, "has_corners": True, "corner_trap_bonus": 1.15, "lateral_freedom": 1.0},
    "cage": {"id": "cage", "half_width_m": 3.5, "wall_near_m": 0.65, "has_walls": True, "has_corners": False, "wall_pin_bonus": 1.20, "lateral_freedom": 1.1},
    "open_floor": {"id": "open_floor", "half_width_m": 50.0, "wall_near_m": 0.0, "has_walls": False, "has_corners": False, "lateral_freedom": 1.35},
    "narrow_alley": {"id": "narrow_alley", "half_width_m": 1.6, "wall_near_m": 0.5, "has_walls": True, "has_corners": True, "restricts_wide_kicks": True, "lateral_freedom": 0.55},
    "rooftop_edge": {"id": "rooftop_edge", "half_width_m": 2.8, "wall_near_m": 0.6, "has_walls": False, "has_drop_hazard": True, "lateral_freedom": 0.85},
    "dojo": {"id": "dojo", "half_width_m": 4.0, "wall_near_m": 0.6, "has_walls": True, "hard_floor_throw_bonus": 1.20, "lateral_freedom": 1.15},
}


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


def _load_option_behaviors(root=ROOT) -> Dict[str, Dict[str, object]]:
    path = root / "data/option_behaviors.json"
    if path.exists():
        data = read(path)
        return {o["id"]: o for o in data["options"]}
    return {}


def load_card_v2(k: Knowledge, value) -> Dict[str, object]:
    """Resolve a predefined archetype ID, file path, or card dict, preferring explicit block-2 cards in cards/v2/."""
    if isinstance(value, str):
        v2_path = k.root / "cards" / "v2" / f"{value}.json"
        if v2_path.exists():
            return k.card(v2_path)
    return k.card(value)


def available_v2(k: Knowledge, card: Dict[str, object], ruleset: str = "mma") -> set:
    """Return the fighter's legal v2 technique set, including the Karate kick family
    (front kick `teep`, round kick `body_kick`, side kick `side_kick`, and `spinning_back_kick`)
    when the fighter has trained `karate` + `kicking.karate` under MMA rules.
    """
    avail = set(available(k, card, ruleset))
    caps = training(card)
    if ruleset == "mma" and "karate" in caps and card["dimensions"].get("kicking") == "kicking.karate":
        avail.update({"side_kick", "teep", "body_kick", "spinning_back_kick"})
    return avail


def list_archetypes_v2(knowledge: Optional[Knowledge] = None) -> List[Dict[str, object]]:
    """Return a structured catalog of all predefined block-2 fighter archetypes in cards/v2/*.json."""
    k = knowledge or Knowledge()
    archetypes: List[Dict[str, object]] = []
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


# ---------------------------------------------------------------------------
# 2. Dynamic Defensive Posture & Per-Lane Readiness Calculator
# ---------------------------------------------------------------------------

def compute_posture_state(
    card: Dict[str, object],
    actor_state: Dict[str, object],
    opt_behaviors: Dict[str, Dict[str, object]],
) -> Dict[str, object]:
    """Build the fighter's live defensive posture from guard + stance + defense method + current damage/fatigue/range."""
    dims = card["dimensions"]
    guard_id = dims.get("hands")
    stance_id = dims.get("stance")
    def_id = dims.get("defense")

    g_prof = opt_behaviors.get(guard_id, {}).get("posture_profile", {}) if guard_id else {}
    s_prof = opt_behaviors.get(stance_id, {}).get("posture_profile", {}) if stance_id else {}
    d_prof = opt_behaviors.get(def_id, {}).get("posture_profile", {}) if def_id else {}

    weight_split = str(s_prof.get("weight_split", "balanced"))
    height = str(s_prof.get("height", "medium"))
    hip_angle = str(s_prof.get("hip_angle", "semi_bladed"))
    base_width = str(s_prof.get("base_width", "balanced"))
    head_pos = str(d_prof.get("head_position", g_prof.get("head_position", "centerline_tucked")))
    base_vision = float(g_prof.get("vision", 3.0))
    decay_rate = float(g_prof.get("guard_decay_rate", 0.06))

    dmg = actor_state.get("damage", {"head": 0.0, "body": 0.0, "leg": 0.0})
    fatigue = float(actor_state.get("fatigue", 0.0))
    rec_win = actor_state.get("recovery_window", {}).get("window_type", "none")

    # Dynamic shifts during the fight:
    if actor_state.get("posture_mode") == "ground":
        height = "grounded"
        base_width = "mat"
    elif rec_win == "single_leg_recovery":
        base_width = "single_leg"
    elif float(dmg.get("leg", 0.0)) >= 4.0 and weight_split == "rear_heavy":
        # Battered leg prevents shifting weight back cleanly to check
        weight_split = "front_heavy"

    if actor_state.get("grip") in ("collar", "controlled") and height != "grounded":
        head_pos = "pulled_down"
    elif fatigue >= 5.0 or float(dmg.get("head", 0.0)) >= 4.5:
        head_pos = "centerline_high"

    # Guard integrity decays as body damage and fatigue accumulate
    guard_integrity = max(
        0.25,
        round(1.0 - decay_rate * (0.6 * float(dmg.get("body", 0.0)) + 0.35 * fatigue), 3),
    )
    vision_eff = max(
        1.0,
        round(
            base_vision
            - (0.8 if actor_state.get("attention", {}).get("feinted") else 0.0)
            - 0.12 * float(dmg.get("head", 0.0)),
            2,
        ),
    )

    balance = str(actor_state.get("balance", "stable"))
    if balance not in ("stable", "compromised", "off_base"):
        balance = "stable"

    return {
        "guard_id": guard_id,
        "stance_id": stance_id,
        "defense_method_id": def_id,
        "weight_split": weight_split,
        "height": height,
        "hip_angle": hip_angle,
        "base_width": base_width,
        "balance": balance,
        "head_position": head_pos,
        "vision_effective": vision_eff,
        "guard_integrity": guard_integrity,
    }


def compute_readiness_profile(
    k: Knowledge,
    card: Dict[str, object],
    actor_state: Dict[str, object],
    opponent_card: Dict[str, object],
    opponent_state: Dict[str, object],
    range_band: str,
    lead_foot_matchup: str,
    incoming_tid: Optional[str] = None,
    opt_behaviors: Optional[Dict[str, Dict[str, object]]] = None,
) -> Dict[str, float]:
    """Compute the fighter's 8-lane defensive readiness profile for the current moment:
    Readiness(lane) = GuardCoverage + MethodFit + StanceFit + StateModifiers(recovery, balance,
                      range, angle, lead_matchup, space, attention, reads, fatigue, damage, mentality, grips).
    """
    beh = opt_behaviors if opt_behaviors is not None else _load_option_behaviors(k.root)
    posture = compute_posture_state(card, actor_state, beh)
    dims = card["dimensions"]
    guard_id = dims.get("hands")
    def_id = dims.get("defense")
    stance_id = dims.get("stance")
    tie_id = dims.get("tie")
    mentality_id = dims.get("mentality")

    g_bonuses = beh.get(guard_id, {}).get("lane_readiness_bonus", {}) if guard_id else {}
    d_bonuses = beh.get(def_id, {}).get("lane_readiness_bonus", {}) if def_id else {}
    s_bonuses = beh.get(stance_id, {}).get("lane_readiness_bonus", {}) if stance_id else {}
    t_bonuses = beh.get(tie_id, {}).get("lane_readiness_bonus", {}) if tie_id else {}

    dmg = actor_state.get("damage", {"head": 0.0, "body": 0.0, "leg": 0.0})
    fatigue = float(actor_state.get("fatigue", 0.0))
    rec_win = actor_state.get("recovery_window", {})
    exposed_lanes = set(rec_win.get("exposed_lanes", []))
    rec_penalty = float(rec_win.get("readiness_penalty", 0.0))
    att_info = actor_state.get("attention", {})
    read_mem = actor_state.get("read_memory", {"seen_counts": {}, "consecutive_same_move_by_opponent": 0})

    profile: Dict[str, float] = {}
    for lane in LANES:
        score = 3.0  # Baseline neutral readiness

        # 1. In clinch or ground, defense becomes posture, tie & hand-fighting rather than guard
        if range_band in ("clinch", "ground"):
            score += 0.35 * float(g_bonuses.get(lane, 0.0))
            score += 1.15 * float(t_bonuses.get(lane, -0.6 if tie_id is None else 0.0))
            underhooks = int(actor_state.get("sub_grips", {}).get("underhooks", 0))
            score += 0.35 * underhooks
        else:
            # Guard, defense method, and stance describe the same unified posture;
            # cap their combined static lane bonus to [-1.20, +1.25] so coherent cards
            # (e.g. peekaboo + slip_roll + crouch) don't triple-stack to +4.25.
            g_val = float(g_bonuses.get(lane, 0.0))
            if range_band in ("kick", "outside") and g_val < 0 and lane in ("head_straight", "head_hook", "head_uppercut"):
                g_val *= 0.15
            static_posture_bonus = (
                g_val * float(posture["guard_integrity"])
                + float(d_bonuses.get(lane, 0.0))
                + 0.85 * float(s_bonuses.get(lane, 0.0))
            )
            score += max(-1.20, min(1.25, static_posture_bonus))
            if range_band in ("kick", "outside"):
                if def_id == "defense.outfight":
                    score += 0.25
                if stance_id == "stance.bladed":
                    score += 0.15

        # 2. Defense method situational breakdowns (only when damaged, fatigued, feinted, or trapped)
        if def_id == "defense.slip_roll":
            if fatigue >= 4.0 or float(dmg["head"]) >= 3.5 or float(posture["vision_effective"]) < 2.2:
                score -= 0.55
        elif def_id == "defense.parry_catch":
            if att_info.get("feinted"):
                score -= 0.65
        elif def_id == "defense.block_absorb":
            if float(dmg["body"]) >= 3.5:
                score -= 0.55
        elif def_id == "defense.outfight":
            if actor_state.get("wall_proximity") == "near" or float(dmg["leg"]) >= 3.5:
                score -= 0.95
        elif def_id == "defense.shoulder_roll":
            if lead_foot_matchup == "open_stance" and lane == "head_hook":
                score -= 0.45
        elif def_id == "defense.check_frame":
            if posture["weight_split"] == "front_heavy" or posture["base_width"] == "single_leg" or float(dmg["leg"]) >= 4.0:
                if lane in ("leg", "single_support"):
                    score -= 0.85
        elif def_id == "defense.sprawl_pummel":
            if att_info.get("feinted") or fatigue >= 4.5:
                if lane == "entry":
                    score -= 0.65
        elif def_id == "defense.smother":
            opp_tie = opponent_card["dimensions"].get("tie")
            if opp_tie in ("tie.thai_plum", "tie.greco", "tie.judo_sambo", "tie.freestyle") and lane == "clinch":
                score -= 0.45

        # 3. Recovery window from the fighter's own prior attack
        if lane in exposed_lanes:
            score -= rec_penalty
        else:
            score -= 0.35 * rec_penalty

        # 4. Balance state
        if posture["balance"] == "compromised":
            score -= 0.95
        elif posture["balance"] == "off_base":
            score -= 1.65

        # 5. Outside angle & Lead-foot matchup (open vs. closed stance)
        if att_info.get("outside_angle_conceded"):
            score -= 1.10
        if lead_foot_matchup == "open_stance" and lane in ("head_straight", "body"):
            score -= 0.35

        # 6. Attention (feints pull the guard/eyes)
        if att_info.get("feinted"):
            if att_info.get("focus_line") == "high_drawn" and lane in ("body", "leg", "entry"):
                score -= 1.10
            else:
                score -= 0.55

        # 7. Reads (read memory: modest bonus against repeated move, never an unbreakable wall)
        if incoming_tid:
            seen_n = int(read_mem.get("seen_counts", {}).get(incoming_tid, 0))
            consec_n = int(read_mem.get("consecutive_same_move_by_opponent", 0))
            if seen_n == 0:
                score -= 0.20  # Novelty surprise
            else:
                score += min(0.85, 0.16 * seen_n + 0.24 * consec_n)

        # 8. Regional Damage & Fatigue Effects
        score -= 0.10 * fatigue
        if lane in ("head_straight", "head_hook"):
            # Body damage brings the elbows down, opening the head!
            score -= 0.14 * float(dmg["body"])
            score -= 0.10 * float(dmg["head"])
        elif lane == "leg":
            score -= 0.20 * float(dmg["leg"])

        # 9. Mentality risk acceptance, 52-shield pocket defense & Low-Tempo defensive patience
        if mentality_id == "mentality.slugger":
            score -= 0.25
        elif mentality_id in ("mentality.defensive", "mentality.counter", "mentality.spoiler", "mentality.outboxer", "mentality.boxer_puncher"):
            score += 0.25
        if guard_id == "hands.shield52" and range_band in ("punch", "close", "clinch"):
            score += 0.45

        tempo_val = int(card.get("tempo", 3))
        if tempo_val < 3:
            score += 0.25 * (3 - tempo_val)

        # Compress additive readiness modifiers around neutral 3.0 and cap in [1.45, 4.85]
        # so no stacked guard+stance+defense wall hits an unbreakable 6.0+ or collapses to 0.20
        compressed = 3.0 + 0.55 * (score - 3.0)
        profile[lane] = round(max(1.45, min(4.85, compressed)), 3)

    return profile


# ---------------------------------------------------------------------------
# 3. First-Class Kicking Subsystem (Unrolled Anatomy & School Defenses)
# ---------------------------------------------------------------------------

def unroll_kick_anatomy(tid: str, card: Dict[str, object], orientation: str) -> Optional[Dict[str, object]]:
    """Generate the 6-part biomechanical kick descriptor for any kick/knee move."""
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


def select_kick_defense(
    defender_card: Dict[str, object],
    kick_tid: str,
    range_band: str,
    lane_readiness: float = 3.5,
    attacker_card: Optional[Dict[str, object]] = None,
    rng: Optional[random.Random] = None,
) -> Tuple[str, str]:
    """Return (defense_action, outcome_effect) native to defender's defense & kicking dimensions.
    When rng is provided during live simulation, kick catches are contested rolls rather than guaranteed.
    """
    def_opt = defender_card["dimensions"].get("defense") or ""
    kick_opt = defender_card["dimensions"].get("kicking") or ""

    if kick_tid in ("body_kick", "low_kick", "switch_kick", "teep", "side_kick") and (
        kick_opt == "kicking.sanda" or def_opt == "defense.parry_catch"
    ):
        if rng is None:
            # Deterministic canonical mapping when called directly in unit tests without rng
            if kick_tid in ("body_kick", "low_kick", "switch_kick"):
                return "kick_catch", "caught"
        else:
            # Contested kick catch: body kicks easiest, teep/side kick medium, low kicks hardest
            base_catch = 0.46 if kick_tid in ("body_kick", "switch_kick") else (0.34 if kick_tid in ("teep", "side_kick") else 0.20)
            sanda_specialist_bonus = 0.14 if (kick_opt == "kicking.sanda" and def_opt == "defense.parry_catch") else 0.0
            att_kick_opt = (attacker_card or {}).get("dimensions", {}).get("kicking") or ""
            retract_mod = -0.08 if att_kick_opt in ("kicking.karate", "kicking.dutch", "kicking.sanda") else 0.0
            catch_prob = max(0.10, min(0.65, base_catch + sanda_specialist_bonus + retract_mod + 0.05 * (lane_readiness - 3.0)))
            if rng.random() < catch_prob:
                return "kick_catch", "caught"

    if kick_tid in ("low_kick", "body_kick", "switch_kick") and def_opt == "defense.check_frame":
        return "check", "checked"
    if def_opt == "defense.outfight" and kick_tid in ("low_kick", "body_kick", "head_kick", "spinning_back_kick", "teep", "side_kick"):
        return "evade_step_back", "evaded"
    if def_opt in ("defense.slip_roll", "defense.shoulder_roll") and kick_tid in ("head_kick", "axe_kick"):
        return "lean_back", "evaded"
    if def_opt in ("defense.smother", "defense.sprawl_pummel") and kick_tid in ("teep", "body_kick", "spinning_back_kick"):
        return "jam_step", "jammed"
    if def_opt == "defense.block_absorb":
        return "retreat", "blocked"
    return "shell_block", "blocked"


def select_native_defense(
    defender_card: Dict[str, object],
    incoming_tid: str,
    range_band: str,
    avail_def: set,
) -> Tuple[str, str]:
    """Select the defender's native posture-driven defensive action and outcome (never borrowing untrained moves)."""
    def_opt = defender_card["dimensions"].get("defense") or "defense.block_absorb"
    hands_opt = defender_card["dimensions"].get("hands") or "hands.high_guard"

    # Grappling / clinch / takedown entries
    if incoming_tid in ("double_leg", "single_leg", "outside_trip", "sanda_sweep", "body_lock", "collar_tie", "wall_tie", "guard_pull"):
        if def_opt == "defense.sprawl_pummel":
            if "sprawl" in avail_def and incoming_tid in ("double_leg", "single_leg"):
                return "sprawl", "evaded"
            if "pummel" in avail_def:
                return "pummel", "blocked"
        elif def_opt == "defense.smother":
            if "pummel" in avail_def:
                return "pummel", "jammed"
            if "wall_tie" in avail_def:
                return "wall_tie", "jammed"
        elif def_opt == "defense.outfight":
            return ("pivot" if "pivot" in avail_def else "retreat"), "evaded"
        elif def_opt == "defense.check_frame":
            if "shield_frame" in avail_def:
                return "shield_frame", "blocked"
        if "sprawl" in avail_def and incoming_tid in ("double_leg", "single_leg"):
            return "sprawl", "evaded"
        if "pummel" in avail_def:
            return "pummel", "blocked"
        return "retreat", "evaded"

    # Strikes (punches / knees)
    if def_opt == "defense.parry_catch":
        if incoming_tid in ("jab", "cross", "teep", "haymaker") and "parry" in avail_def:
            return "parry", "evaded"
        return ("shell_block" if "shell_block" in avail_def else "retreat"), "blocked"
    if def_opt in ("defense.slip_roll", "defense.shoulder_roll"):
        if "slip" in avail_def:
            return "slip", "evaded"
        return ("pivot" if "pivot" in avail_def else "retreat"), "evaded"
    if def_opt == "defense.outfight":
        return ("pivot" if ("pivot" in avail_def and incoming_tid in ("jab", "cross")) else "retreat"), "evaded"
    if def_opt == "defense.check_frame":
        if "shield_frame" in avail_def:
            return "shield_frame", "blocked"
        if hands_opt == "hands.long_guard":
            return "retreat", "evaded"
        return ("shell_block" if "shell_block" in avail_def else "retreat"), "blocked"
    if def_opt == "defense.smother":
        if "pummel" in avail_def:
            return "pummel", "jammed"
        if "shield_frame" in avail_def:
            return "shield_frame", "blocked"
        return "step", "jammed"
    if def_opt == "defense.sprawl_pummel":
        if hands_opt == "hands.philly_shell" and "slip" in avail_def:
            return "slip", "evaded"
        return ("shell_block" if "shell_block" in avail_def else "retreat"), "blocked"

    # defense.block_absorb (e.g. Rook Mercer): native forearm/shoulder brace or step-back
    if "shell_block" in avail_def:
        return "shell_block", "blocked"
    return "retreat", "blocked"


# ---------------------------------------------------------------------------
# 4. Card-Derived Damage Formula (Additive Modifiers & School-Based Depth)
# ---------------------------------------------------------------------------

MENTALITY_POWER_DELTA: Dict[str, float] = {
    "mentality.slugger": 0.28,
    "mentality.pressure": 0.12,
    "mentality.boxer_puncher": 0.08,
    "mentality.switch_hitter": 0.06,
    "mentality.technician": 0.04,
    "mentality.counter": 0.00,
    "mentality.swarmer": -0.10,
    "mentality.outboxer": 0.00,
    "mentality.spoiler": -0.05,
    "mentality.defensive": -0.05,
    "mentality.slickster": -0.03,
    "mentality.showman": 0.04,
}

STANCE_POWER_DELTA: Dict[str, float] = {
    "stance.planted": 0.20,
    "stance.crouch": 0.12,
    "stance.balanced": 0.00,
    "stance.upright": 0.00,
    "stance.switch": 0.06,
    "stance.bladed": 0.00,
    "stance.shuffle": -0.03,
}

SLOT_DEPTH_MULT: Dict[int, float] = {
    1: 1.15,
    2: 1.05,
    3: 1.00,
    4: 0.95,
}

LANDING_QUALITY_MULT: Dict[str, float] = {
    "evaded": 0.0,
    "miss": 0.0,
    "caught": 0.08,
    "checked": 0.10,
    "jammed": 0.18,
    "blocked": 0.18,
    "partial": 0.50,
    "clean": 1.00,
    "counter_hit": 1.42,
    "flush": 1.55,
}


def compute_school_depth_multiplier(card: Dict[str, object], k: Optional[Knowledge] = None) -> float:
    """Compute depth multiplier based on BOTH total trained schools and slot count so cramming
    more schools into fewer slots never grants an unfair depth bonus.
    """
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
    return SLOT_DEPTH_MULT.get(effective_breadth, 1.0)


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
    """Compute qualitative Card-Derived Damage using additive attacker modifiers (never multiplicative double-taxing)."""
    stats = MOVE_BASE_STATS.get(tid, {"base": 1.0, "type": "impact", "lane": "head_straight"})
    base = float(stats["base"])
    if base <= 0.0:
        return {
            "technique_id": tid,
            "target_region": "head",
            "base_damage": 0.0,
            "attacker_multiplier": 1.0,
            "landing_multiplier": 0.0,
            "defender_multiplier": 1.0,
            "final_damage": 0.0,
            "recoil_leg_damage_to_attacker": 0.0,
            "damage_type": stats["type"],
            "landing_quality": landing_quality,
        }

    mentality = attacker_card["dimensions"].get("mentality") or "mentality.boxer_puncher"
    stance = attacker_card["dimensions"].get("stance") or "stance.balanced"
    target_opt = attacker_card["dimensions"].get("target") or "target.mixer"
    kicking_opt = attacker_card["dimensions"].get("kicking") or "kicking.none"

    tech = k.techniques.get(tid, {})
    target_region = tech.get("target_region", "head")
    if tid == "single_leg":
        target_region = "leg"
    elif tid == "body_kick" and kicking_opt == "kicking.karate" and int(attacker_state.get("slot_Cursor", 0)) % 2 == 1:
        # Karate/TKD roundhouse kicks split levels between high-section head and floating ribs
        target_region = "head"
    elif target_region not in ("head", "body", "leg"):
        target_region = "head" if tid in ("head_kick", "axe_kick", "jumping_knee") else "body"

    delta_mentality = MENTALITY_POWER_DELTA.get(mentality, 0.0)
    if mentality == "mentality.counter" and landing_quality == "counter_hit":
        delta_mentality = 0.45

    delta_stance = STANCE_POWER_DELTA.get(stance, 0.0)
    if stance == "stance.crouch" and tid in ("hook", "body_hook", "uppercut"):
        delta_stance += 0.06
    if stance == "stance.switch" and "switch_step" in attacker_state.get("setups", []):
        delta_stance += 0.08

    delta_kicking = 0.0
    if tid in KICK_IDS:
        if kicking_opt == "kicking.muay_thai" and tid in ("low_kick", "body_kick", "head_kick", "knee_body", "jumping_knee"):
            delta_kicking = 0.18
        elif kicking_opt == "kicking.dutch" and tid == "low_kick":
            delta_kicking = 0.16
        elif kicking_opt == "kicking.karate" and tid in ("side_kick", "spinning_back_kick", "axe_kick", "teep", "body_kick"):
            delta_kicking = 0.16
        elif kicking_opt == "kicking.sanda" and tid in ("side_kick", "low_kick", "body_kick", "teep"):
            delta_kicking = 0.14

    delta_target = 0.0
    if (
        (target_opt == "target.head_hunter" and target_region == "head")
        or (target_opt in ("target.body_puncher", "target.liver_ribs") and target_region == "body")
        or (target_opt == "target.leg_chopper" and target_region == "leg")
        or (target_opt == "target.knee_clincher" and tid in ("knee_body", "jumping_knee", "collar_tie"))
    ):
        delta_target = 0.12

    slot_depth = compute_school_depth_multiplier(attacker_card, k)
    delta_slot = (slot_depth - 1.0) if in_active_slot else -0.15

    att_fatigue = float(attacker_state.get("fatigue", 0.0))
    att_leg_dmg = float(attacker_state.get("damage", {}).get("leg", 0.0))
    delta_wear = -0.012 * att_fatigue - (0.03 * att_leg_dmg if tid in KICK_IDS else 0.015 * att_leg_dmg)

    # Additive sum clamped to [0.75, 1.75]
    m_attacker = max(0.75, min(1.75, 1.0 + delta_mentality + delta_stance + delta_kicking + delta_target + delta_slot + delta_wear))

    m_landing = LANDING_QUALITY_MULT.get(landing_quality, 1.0)
    if defender_state.get("wall_proximity") == "near" and m_landing > 0:
        m_landing *= 1.12

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

    m_guard = 1.14 - 0.06 * cov
    if def_opt_id == "defense.block_absorb":
        if landing_quality == "blocked":
            # Native block_absorb takes a little more bleed-through when passively bracing
            m_landing = 0.24
        elif target_region == "head":
            m_guard *= 0.90

    existing_reg_dmg = float(defender_state.get("damage", {}).get(target_region, 0.0))
    m_wear = 1.0 + 0.045 * existing_reg_dmg
    m_defender = max(0.60, m_guard * m_wear)

    final_damage = round(base * m_attacker * m_landing * m_defender, 3)

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
# 5. Slots as Tactical Gameplans (Supports Both block-1 and block-2 Cards)
# ---------------------------------------------------------------------------

def build_slot_plans(k: Knowledge, card: Dict[str, object], ruleset: str = "mma") -> List[Dict[str, object]]:
    """Build executable SlotPlan objects from card.synchronized_capabilities."""
    all_avail = available_v2(k, card, ruleset)
    plans: List[Dict[str, object]] = []
    slots = admitted_slots(card, k)
    depth_mult = compute_school_depth_multiplier(card, k)
    kicking_opt = card["dimensions"].get("kicking") or "kicking.none"
    target_opt = card["dimensions"].get("target") or "target.mixer"

    for idx, slot in enumerate(slots):
        caps = set(slot.get("capabilities", []))
        explicit_seq = [m for m in slot.get("sequence", []) if m in all_avail]
        if explicit_seq and not ("karate" in caps and kicking_opt == "kicking.karate" and len(explicit_seq) <= 3):
            clean_seq = explicit_seq
        else:
            slot_moves = [
                tid
                for tid in card["active_techniques"]
                if tid in all_avail
                and tid != "escape"
                and k.techniques[tid]["kind"] in ("punch", "kick", "knee", "takedown", "grip", "control", "submission")
                and (set(k.techniques[tid]["required_capabilities"]) & caps)
            ]
            if "karate" in caps and kicking_opt == "kicking.karate" and ruleset == "mma":
                for km in ("side_kick", "teep", "body_kick", "spinning_back_kick"):
                    if km in all_avail and km not in slot_moves:
                        slot_moves.append(km)
            if not slot_moves:
                slot_moves = [
                    tid
                    for tid in card["active_techniques"]
                    if tid in all_avail and k.techniques[tid]["kind"] in ("punch", "kick", "takedown", "grip")
                ]

            ordered_seq: List[str] = []
            if "sanda" in caps and "sanda_sweep" in slot_moves:
                ordered_seq.extend([m for m in ("low_kick", "body_kick", "teep", "sanda_sweep", "side_kick") if m in slot_moves])
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
                ordered_seq.extend([m for m in ("side_kick", "teep", "body_kick", "spinning_back_kick", "jab", "cross") if m in slot_moves or m in all_avail])
            elif "boxing" in caps:
                if target_opt == "target.body_puncher":
                    ordered_seq.extend([m for m in ("jab", "body_hook", "cross", "uppercut", "hook") if m in slot_moves])
                elif card["dimensions"].get("mentality") == "mentality.counter":
                    ordered_seq.extend([m for m in ("jab", "cross", "uppercut", "hook", "body_hook") if m in slot_moves])
                else:
                    ordered_seq.extend([m for m in ("jab", "cross", "hook", "body_hook", "uppercut") if m in slot_moves])
            else:
                ordered_seq.extend(slot_moves)

            seen_m = set()
            clean_seq = []
            for m in ordered_seq + slot_moves:
                if m in all_avail and m not in seen_m:
                    seen_m.add(m)
                    clean_seq.append(m)

        home_range = slot.get("home_range")
        if not home_range:
            home_range = "punch"
            if any(c in caps for c in ("bjj", "wrestling", "judo", "clinch")):
                home_range = "clinch"
            elif any(c in caps for c in ("kickboxing", "karate", "sanda")):
                home_range = "kick"

        abandon_rule = slot.get("abandon_rule", {})
        max_stalls = int(abandon_rule.get("max_consecutive_stalls", 999 if len(slots) == 1 else 2))
        next_slot_id = (slot.get("links") or [slots[(idx + 1) % len(slots)]["id"]])[0]

        plans.append(
            {
                "slot_id": slot["id"],
                "slot_index": idx,
                "capabilities": sorted(caps),
                "sequence": clean_seq or ["jab"],
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


# ---------------------------------------------------------------------------
# 6. Grappling Position & Grip Map State Updater
# ---------------------------------------------------------------------------

def update_grappling_position(
    actor_state: Dict[str, object],
    defender_state: Dict[str, object],
    tid: str,
    outcome: str,
    actor_card: Dict[str, object],
) -> str:
    if outcome not in ("clean", "flush", "counter_hit", "partial"):
        if outcome == "jammed":
            actor_state["grappling_position"] = "over_under"
            defender_state["grappling_position"] = "over_under"
        elif tid == "ride" and actor_state.get("posture_mode") == "ground":
            # Bottom defender stuffed/scrambled out of the ride attempt and returns to standing!
            actor_state["posture_mode"] = defender_state["posture_mode"] = "standing"
            actor_state["grappling_position"] = defender_state["grappling_position"] = "standing_neutral"
            actor_state["grip"] = defender_state["grip"] = None
            actor_state["submission_stage"] = defender_state["submission_stage"] = 0
        return str(actor_state.get("grappling_position", "standing_neutral"))

    tie_opt = actor_card["dimensions"].get("tie")
    if tid == "collar_tie":
        pos = "thai_plum" if tie_opt == "tie.thai_plum" else "collar_tie"
        actor_state["grappling_position"] = pos
        defender_state["grappling_position"] = "collar_tie"
        actor_state["sub_grips"]["head_position"] = "inside_control"
        actor_state["grip"], defender_state["grip"] = "collar", "controlled"
    elif tid == "body_lock":
        actor_state["grappling_position"] = "front_body_lock"
        defender_state["grappling_position"] = "over_under"
        actor_state["sub_grips"]["underhooks"] = 2
        actor_state["grip"], defender_state["grip"] = "body_lock", "controlled"
    elif tid == "wall_tie":
        actor_state["grappling_position"] = "wall_pinned"
        defender_state["grappling_position"] = "wall_pinned"
        actor_state["sub_grips"]["underhooks"] = 1
        actor_state["grip"], defender_state["grip"] = "single_tie", "controlled"
    elif tid == "pummel":
        actor_state["grappling_position"] = "double_underhooks"
        defender_state["grappling_position"] = "over_under"
        actor_state["sub_grips"]["underhooks"] = min(2, actor_state["sub_grips"].get("underhooks", 0) + 1)
    elif tid in ("double_leg", "single_leg", "outside_trip", "sanda_sweep"):
        actor_state["posture_mode"] = defender_state["posture_mode"] = "ground"
        actor_state["grappling_position"] = "side_control" if tid in ("outside_trip", "sanda_sweep") else "half_guard_top"
        defender_state["grappling_position"] = "closed_guard_bottom"
        actor_state["grip"], defender_state["grip"] = "top", "bottom"
        actor_state["control_marks"] += 1
    elif tid == "guard_pull":
        actor_state["posture_mode"] = defender_state["posture_mode"] = "ground"
        actor_state["grappling_position"] = "closed_guard_bottom"
        defender_state["grappling_position"] = "half_guard_top"
        actor_state["grip"], defender_state["grip"] = "bottom", "top"
        actor_state["control_marks"] += 1
    elif tid == "ride":
        actor_state["grappling_position"] = "mount_or_back_ride"
        defender_state["grappling_position"] = "closed_guard_bottom"
        actor_state["control_marks"] += 1
    elif tid == "armbar":
        stage = int(actor_state.get("submission_stage", 0)) + 1
        actor_state["submission_stage"] = stage
        actor_state["sub_grips"]["wrist_control"] = True
        actor_state["grappling_position"] = "side_control"
        actor_state["control_marks"] += 1
    elif tid in ("escape", "retreat") and actor_state.get("posture_mode") == "ground":
        actor_state["posture_mode"] = defender_state["posture_mode"] = "standing"
        actor_state["grappling_position"] = defender_state["grappling_position"] = "standing_neutral"
        actor_state["grip"] = defender_state["grip"] = None
        actor_state["submission_stage"] = defender_state["submission_stage"] = 0

    return str(actor_state["grappling_position"])


# ---------------------------------------------------------------------------
# 7. Level 2: Order-Invariant Exchange-by-Exchange Simulator (`simulate_fight_v2`)
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
    """Run a clock-driven, card-authentic v2 fight simulation between fighter A and fighter B.
    Canonical fighter-ID sorting guarantees order invariance: simulate_fight_v2(A, B, seed)
    and simulate_fight_v2(B, A, seed) produce the exact same winner and exchanges.
    """
    k = knowledge or Knowledge()
    card_a, card_b = load_card_v2(k, a), load_card_v2(k, b)
    if card_a["fighter_id"] == card_b["fighter_id"]:
        raise ValueError("two distinct fighter IDs are required")

    settings = {
        "duration_s": float(duration_s),
        "arena": arena,
        "vertical_mode": vertical_mode,
        "ruleset": ruleset,
        "seed": int(seed),
        "director_winner": None,
        "initiative_override": None,
    }
    jsonschema.validate(settings, read(k.root / "schemas/fight_settings.schema.json"))

    opt_behaviors = _load_option_behaviors(k.root)
    tech_v2_map = {t["id"]: t for t in read(k.root / "data/techniques_v2.json")["techniques"]} if (k.root / "data/techniques_v2.json").exists() else {}

    cards = {card_a["fighter_id"]: card_a, card_b["fighter_id"]: card_b}
    # Canonical sorting ensures order-invariant RNG draws and exchange resolution
    canonical_ids = sorted(cards.keys())
    rng = random.Random(seed)

    arena_cfg = ARENA_PRESETS.get(arena, ARENA_PRESETS["cage"])
    half_w = float(arena_cfg["half_width_m"])

    slot_plans = {fid: build_slot_plans(k, cards[fid], ruleset) for fid in canonical_ids}

    actors: Dict[str, Dict[str, object]] = {}
    for fid, x0 in zip(canonical_ids, [-0.8, 0.8]):
        c = cards[fid]
        orient = "orthodox" if c["orientation"] == "switching" else c["orientation"]
        actors[fid] = {
            "fighter_id": fid,
            "name": c["name"],
            "position": [x0, 0.0],
            "facing": [1.0 if x0 < 0 else -1.0, 0.0],
            "orientation": orient,
            "posture_mode": "standing",
            "balance": "stable",
            "grappling_position": "standing_neutral",
            "grip": None,
            "sub_grips": {"underhooks": 0, "wrist_control": False, "head_position": "neutral"},
            "submission_stage": 0,
            "wall_proximity": "far",
            "damage": {"head": 0.0, "body": 0.0, "leg": 0.0},
            "fatigue": 0.0,
            "momentum": [0.0, 0.0],
            "contact_marks": 0,
            "control_marks": 0,
            "active_slot_idx": 0,
            "active_slot_id": slot_plans[fid][0]["slot_id"],
            "slot_Cursor": 0,
            "slot_stalls": 0,
            "slot_switches": 0,
            "kick_checks_suffered": 0,
            "recent_moves": [],
            "setups": [],
            "recovery_window": {
                "window_type": "none",
                "last_technique_id": None,
                "exposed_lanes": [],
                "readiness_penalty": 0.0,
            },
            "attention": {
                "focus_line": "neutral",
                "feinted": False,
                "outside_angle_conceded": False,
            },
            "read_memory": {
                "seen_counts": {},
                "consecutive_same_move_by_opponent": 0,
            },
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
        lead_matchup = (
            "closed_stance"
            if actors[canonical_ids[0]]["orientation"] == actors[canonical_ids[1]]["orientation"]
            else "open_stance"
        )

        # 1. Decide who initiates this exchange in canonical fighter-ID order
        scores_init = {}
        for fid in canonical_ids:
            c = cards[fid]
            st = actors[fid]
            mentality = c["dimensions"].get("mentality")
            base_tempo = 3.0 + 0.30 * (float(c.get("tempo", 3)) - 3.0)
            counter_wait = -0.35 if (mentality == "mentality.counter" and last_attacker_id in (None, fid)) else (
                0.35 if mentality in ("mentality.swarmer", "mentality.pressure") else 0.0
            )
            recovery_cooldown = -last_recovery_drag if fid == last_attacker_id else 0.0
            fatigue_drag = -0.08 * float(st["fatigue"])
            leg_drag = -0.10 * float(st["damage"]["leg"])
            scores_init[fid] = base_tempo + counter_wait + recovery_cooldown + fatigue_drag + leg_drag + rng.uniform(-0.85, 0.85)

        attacker_id = max(canonical_ids, key=lambda i: (scores_init[i], i))
        defender_id = next(i for i in canonical_ids if i != attacker_id)
        att_card, def_card = cards[attacker_id], cards[defender_id]
        att_state, def_state = actors[attacker_id], actors[defender_id]

        # 2. Select active slot plan, contest range step (one band per exchange), & select technique
        plans = slot_plans[attacker_id]
        active_plan = plans[int(att_state["active_slot_idx"]) % len(plans)]
        att_state["active_slot_id"] = active_plan["slot_id"]
        seq: List[str] = list(active_plan["sequence"])
        att_avail = available_v2(k, att_card, ruleset)
        def_avail = available_v2(k, def_card, ruleset)

        att_mentality = att_card["dimensions"].get("mentality")
        def_mentality = def_card["dimensions"].get("mentality")
        def_option = def_card["dimensions"].get("defense")
        att_stance = att_card["dimensions"].get("stance")
        def_stance = def_card["dimensions"].get("stance")

        standing_ladder = ["kick", "punch", "clinch"]
        if att_state["posture_mode"] == "ground":
            range_band = "ground"
        elif att_state["grip"] in ("collar", "body_lock", "single_tie"):
            # If attacker is an outboxer/kicker trapped in clinch, contest a tie-break to step back to punch range
            if str(active_plan["home_range"]) in ("kick", "punch") and def_card["dimensions"].get("tie") is None:
                att_state["grip"] = def_state["grip"] = None
                att_state["grappling_position"] = def_state["grappling_position"] = "standing_neutral"
                range_band = "punch"
            elif str(active_plan["home_range"]) in ("kick", "punch") and rng.random() < 0.42:
                att_state["grip"] = def_state["grip"] = None
                att_state["grappling_position"] = def_state["grappling_position"] = "standing_neutral"
                range_band = "punch"
            else:
                range_band = "clinch"
        elif ruleset == "boxing":
            range_band = "punch"
        else:
            desired_range = str(active_plan["home_range"])
            if desired_range not in standing_ladder:
                desired_range = "punch"
            if range_band not in standing_ladder:
                range_band = "kick"
            cur_idx = standing_ladder.index(range_band)
            des_idx = standing_ladder.index(desired_range)
            if des_idx > cur_idx:
                # Attacker wants to step in (kick -> punch or punch -> clinch): contest footwork vs distance control!
                entry_score = 0.0
                if att_mentality in ("mentality.pressure", "mentality.swarmer"):
                    entry_score += 0.45
                if att_stance in ("stance.crouch", "stance.shuffle"):
                    entry_score += 0.30
                entry_score += 0.08 * (float(att_card.get("tempo", 3)) - 3.0)

                dist_score = 0.0
                if def_option == "defense.outfight":
                    dist_score += 0.65
                if def_card["dimensions"].get("hands") == "hands.long_guard":
                    dist_score += 0.35
                if def_stance == "stance.bladed":
                    dist_score += 0.35
                if def_card["dimensions"].get("kicking") in ("kicking.karate", "kicking.muay_thai", "kicking.sanda"):
                    dist_score += 0.25
                if def_state.get("wall_proximity") == "near":
                    dist_score -= 0.65
                dist_score -= 0.12 * float(def_state["damage"]["leg"])

                step_prob = max(0.18, min(0.82, 1.0 / (1.0 + math.exp(-(entry_score - dist_score + 0.35)))))
                if rng.random() < step_prob:
                    range_band = standing_ladder[min(len(standing_ladder) - 1, cur_idx + 1)]
                else:
                    # Distance control holds range at cur_idx, but out-fighter drifts slightly toward wall
                    if arena_cfg["has_walls"]:
                        direction = 1.0 if def_state["position"][0] >= 0 else -1.0
                        def_state["position"][0] = round(max(-half_w, min(half_w, def_state["position"][0] + 0.28 * direction)), 3)
                        if half_w - abs(def_state["position"][0]) <= float(arena_cfg["wall_near_m"]):
                            def_state["wall_proximity"] = "near"
            elif des_idx < cur_idx:
                # Attacker wants to step out (clinch -> punch or punch -> kick)
                pull_prob = 0.72 if (att_mentality == "mentality.outboxer" or att_card["dimensions"].get("defense") == "defense.outfight") else 0.58
                if att_state.get("wall_proximity") == "near":
                    pull_prob -= 0.20
                if rng.random() < pull_prob:
                    range_band = standing_ladder[max(0, cur_idx - 1)]

        filtered_seq = [
            m for m in seq
            if m != "escape" and not (att_state["kick_checks_suffered"] >= 2 and m in ("low_kick", "body_kick"))
        ] or seq

        # Filter to techniques that reach at the current contested range_band when possible
        # Takedown shots (double_leg / single_leg) require closing to punch/close range first rather than free kick-range teleports
        range_matching_seq = [
            m for m in filtered_seq
            if m in k.techniques and (
                (range_band in k.techniques[m]["required_range"] and not (range_band == "kick" and m in ("double_leg", "single_leg")))
                or (
                    range_band == "punch"
                    and (
                        "close" in k.techniques[m]["required_range"]
                        or m in ("low_kick", "body_kick", "teep", "switch_kick")
                        or (att_card["dimensions"].get("tie") in ("tie.greco", "tie.judo_sambo") and m in ("body_lock", "outside_trip", "collar_tie"))
                    )
                )
            )
        ]
        active_seq = range_matching_seq or filtered_seq

        cursor = int(att_state["slot_Cursor"])
        tid = active_seq[cursor % len(active_seq)]
        att_state["slot_Cursor"] = cursor + 1

        if range_band == "ground":
            if att_state["grip"] == "top" and "ride" in att_avail:
                tid = "ride"
            elif att_state["grip"] == "bottom" and "armbar" in att_avail:
                tid = "armbar"
            elif "escape" in att_avail:
                tid = "escape"
            elif att_state["grip"] == "top":
                top_strikes = [m for m in ("cross", "hook", "body_hook", "jab", "haymaker") if m in att_avail]
                tid = top_strikes[cursor % len(top_strikes)] if top_strikes else "retreat"
            else:
                tid = "retreat" if "retreat" in att_avail else ("pummel" if "pummel" in att_avail else "jab")
        elif range_band == "kick" and tid not in KICK_IDS:
            # Attacker was kept at kick range and doesn't have a kick in this slot: look for a trained kick or closing probe
            kick_fallbacks = [m for m in ("side_kick", "teep", "low_kick", "body_kick", "jab") if m in att_avail]
            if kick_fallbacks:
                tid = kick_fallbacks[cursor % len(kick_fallbacks)]

        # Update defender's read_memory before computing defender readiness
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

        def_state["read_memory"]["consecutive_same_move_by_opponent"] = consecutive_repeats

        # 3. Compute Defender's Dynamic Posture & 8-Lane Readiness Profile
        def_posture_before = compute_posture_state(def_card, def_state, opt_behaviors)
        def_readiness = compute_readiness_profile(
            k,
            def_card,
            def_state,
            att_card,
            att_state,
            range_band,
            lead_matchup,
            incoming_tid=tid,
            opt_behaviors=opt_behaviors,
        )
        def_state["posture"] = def_posture_before
        def_state["readiness_profile"] = def_readiness

        m_stats = MOVE_BASE_STATS.get(tid, {"base": 1.0, "type": "impact", "setup_f": 4, "exec_f": 8, "hold_f": 2, "rec_f": 8, "lane": "head_straight"})
        attack_lane = str(m_stats.get("lane", "head_straight"))
        lane_readiness = float(def_readiness.get(attack_lane, 3.0))

        # 4. Calculate Contested Hit Probability (Strictly Capped in [0.10, 0.85])
        base_att_skill = 3.30
        if att_mentality == "mentality.slugger":
            base_att_skill -= 0.12
        elif att_mentality == "mentality.outboxer":
            # Out-boxer edge is accuracy and distance timing, not power penalty
            base_att_skill += 0.22
        elif att_mentality in ("mentality.technician", "mentality.boxer_puncher", "mentality.counter"):
            base_att_skill += 0.25
        if att_stance == "stance.bladed":
            base_att_skill += 0.12
        elif att_stance == "stance.switch":
            # Switch-stance angle disguise bonus
            base_att_skill += 0.28
        if range_band == "kick" and tid not in KICK_IDS:
            # Throwing a punch or shooting an un-setup takedown from kick range when kept outside has lower reach accuracy
            base_att_skill -= (0.75 if tid in ("double_leg", "single_leg") else 0.55)

        logit_hit = base_att_skill - lane_readiness
        hit_prob = round(max(0.10, min(0.85, 1.0 / (1.0 + math.exp(-logit_hit)))), 3)

        # Record move in defender's seen_counts for future exchanges
        seen_map = def_state["read_memory"]["seen_counts"]
        seen_map[tid] = int(seen_map.get(tid, 0)) + 1

        # 5. Roll Outcome & Native Posture Defensive Response (Nothing Guaranteed)
        kick_detail = unroll_kick_anatomy(tid, att_card, str(att_state["orientation"]))
        defense_used = None
        counter_triggered = False

        roll = rng.random()
        if def_card["dimensions"].get("kicking") == "kicking.sanda" and def_option == "defense.parry_catch":
            kick_def_bonus = 0.24
        elif def_card["dimensions"].get("kicking") == "kicking.sanda" or def_option in ("defense.check_frame", "defense.outfight"):
            kick_def_bonus = 0.16
        else:
            kick_def_bonus = 0.08

        if tid in KICK_IDS and tid != "knee_body" and roll > max(0.10, hit_prob - kick_def_bonus):
            defense_used, outcome = select_kick_defense(
                def_card, tid, range_band, lane_readiness=lane_readiness, attacker_card=att_card, rng=rng
            )
        elif roll > hit_prob:
            defense_used, outcome = select_native_defense(def_card, tid, range_band, def_avail)
        else:
            if roll < hit_prob * 0.28 and (def_state["attention"]["feinted"] or def_posture_before["balance"] != "stable"):
                outcome = "flush"
            elif roll < hit_prob * 0.76:
                outcome = "clean"
            else:
                outcome = "partial"

        # Contested Counter-Attack Check:
        # Requires: (1) attacker missed/was defended and is in recovery window (rec_f >= 6),
        #           (2) defender has a trained counter at this range,
        #           (3) contested counter roll succeeds (never guaranteed, no double-dipping on lane_readiness!).
        att_rec_f = int(m_stats.get("rec_f", 6))
        if outcome in ("evaded", "blocked", "jammed") and att_rec_f >= 6:
            def_beh = opt_behaviors.get(def_mentality, {}).get("exchange_Hook_values", {})
            base_counter = float(def_beh.get("counter_tendency", 0.20))
            if def_option in ("defense.parry_catch", "defense.slip_roll", "defense.shoulder_roll"):
                base_counter += 0.10
            elif def_option == "defense.outfight" and range_band == "kick":
                base_counter += 0.12
            read_bonus = 0.07 * min(3, consecutive_repeats)
            low_tempo_bonus = 0.06 * max(0, 3 - int(def_card.get("tempo", 3)))
            rec_window_bonus = 0.03 * max(0, att_rec_f - 7)
            att_hands_id = att_card["dimensions"].get("hands")
            att_head_cov = (
                k.options[att_hands_id]["mma_adaptation"]["ratings"].get("head_coverage", 3)
                if att_hands_id and att_hands_id in k.options
                else 3
            )
            att_guard_resist = 0.05 * (att_head_cov - 3)
            counter_prob = max(
                0.10,
                min(0.55, base_counter + read_bonus + low_tempo_bonus + rec_window_bonus - att_guard_resist - 0.03 * float(def_state["fatigue"])),
            )
            if rng.random() < counter_prob:
                counter_triggered = True

        # 6. Apply Card-Derived Damage & Posture/Recovery Updates
        dmg_info = compute_card_derived_damage(
            k, att_card, def_card, tid, outcome, att_state, def_state, in_active_slot=True
        )

        if dmg_info["final_damage"] > 0:
            reg = str(dmg_info["target_region"])
            if tid in ("collar_tie", "cage_plum", "body_lock", "wall_tie", "pummel", "guard_pull", "ride"):
                # Clinch ties, guard pulls, and top rides primarily drain stamina and build positional control
                def_state["damage"][reg] = round(def_state["damage"][reg] + 0.25 * dmg_info["final_damage"], 3)
                def_state["fatigue"] = round(def_state["fatigue"] + 0.65 * dmg_info["final_damage"], 2)
            elif dmg_info["damage_type"] == "submission":
                # Submissions finish via submission_stage progression while taxing limb/stamina
                def_state["damage"][reg] = round(def_state["damage"][reg] + 0.30 * dmg_info["final_damage"], 3)
                def_state["fatigue"] = round(def_state["fatigue"] + 0.55 * dmg_info["final_damage"], 2)
            else:
                def_state["damage"][reg] = round(def_state["damage"][reg] + dmg_info["final_damage"], 3)
                if dmg_info["damage_type"] == "stamina_drain":
                    def_state["fatigue"] = round(def_state["fatigue"] + 0.55 * dmg_info["final_damage"], 2)
            if outcome in ("clean", "flush", "counter_hit", "partial"):
                att_state["contact_marks"] += 1

        if dmg_info["recoil_leg_damage_to_attacker"] > 0:
            att_state["damage"]["leg"] = round(
                att_state["damage"]["leg"] + dmg_info["recoil_leg_damage_to_attacker"], 3
            )
            att_state["kick_checks_suffered"] += 1

        # Update balance & recovery window for next exchange
        if outcome in ("flush", "counter_hit", "caught"):
            def_state["balance"] = "off_base" if outcome != "caught" else "stable"
            if outcome == "caught":
                att_state["balance"] = "compromised"
        elif outcome in ("clean", "checked", "jammed"):
            def_state["balance"] = "compromised" if outcome == "clean" else "stable"
            if outcome in ("checked", "jammed"):
                att_state["balance"] = "compromised"
        else:
            def_state["balance"] = "stable"
            att_state["balance"] = "stable"

        t_v2_rec = tech_v2_map.get(tid, {}).get("recovery_exposure", {
            "window_type": "short_retract",
            "exposed_lanes": ["head_straight"],
            "readiness_penalty": 0.4,
        })
        att_state["recovery_window"] = {
            "window_type": t_v2_rec["window_type"],
            "last_technique_id": tid,
            "exposed_lanes": list(t_v2_rec["exposed_lanes"]),
            "readiness_penalty": float(t_v2_rec["readiness_penalty"]) * (1.25 if outcome in ("evaded", "miss", "checked", "caught") else 0.60),
        }
        def_state["recovery_window"] = {
            "window_type": "none",
            "last_technique_id": defense_used,
            "exposed_lanes": [],
            "readiness_penalty": 0.0,
        }

        forced_stance_switch = False
        if def_state["damage"]["leg"] >= 4.5 and not def_state.get("leg_compromised"):
            def_state["leg_compromised"] = True
            def_state["orientation"] = "southpaw" if def_state["orientation"] == "orthodox" else "orthodox"
            forced_stance_switch = True

        grappling_pos = update_grappling_position(att_state, def_state, tid, outcome, att_card)
        if att_mentality in ("mentality.swarmer", "mentality.pressure") and arena_cfg["has_walls"]:
            direction = 1.0 if def_state["position"][0] >= 0 else -1.0
            def_state["position"][0] = round(max(-half_w, min(half_w, def_state["position"][0] + 0.42 * direction)), 3)
            if half_w - abs(def_state["position"][0]) <= float(arena_cfg["wall_near_m"]):
                def_state["wall_proximity"] = "near"
        elif (def_mentality == "mentality.outboxer" or def_option == "defense.outfight") and outcome in ("evaded", "blocked"):
            def_state["position"][0] = round(def_state["position"][0] * 0.55, 3)
            def_state["wall_proximity"] = "far"

        exchange_frames = int(m_stats["setup_f"]) + int(m_stats["exec_f"]) + int(m_stats["hold_f"]) + int(m_stats["rec_f"])
        tempo_gap_frames = max(6, int(36 - 4 * max(att_card.get("tempo", 3), def_card.get("tempo", 3))))
        t_start = round(clock_frames / 24.0, 2)
        clock_frames += exchange_frames + tempo_gap_frames
        t_end = round(clock_frames / 24.0, 2)
        att_tempo_val = int(att_card.get("tempo", 3))
        fatigue_step = 0.22 if att_tempo_val == 1 else (0.28 if att_tempo_val == 2 else (0.34 if att_tempo_val == 3 else (0.39 if att_tempo_val == 4 else 0.44)))
        att_state["fatigue"] = round(att_state["fatigue"] + fatigue_step, 2)
        last_attacker_id = attacker_id
        last_recovery_drag = 1.45 + 0.08 * float(m_stats["rec_f"]) + (0.65 if outcome in ("evaded", "blocked", "checked", "caught") else 0.0)

        counter_followup_event = None
        if outcome == "caught":
            att_state["kick_checks_suffered"] += 1
            # Contested sweep attempt: kicker's balance and tie can resist or hop out!
            att_tie = att_card["dimensions"].get("tie")
            sweep_resist = 0.22 if att_tie in ("tie.freestyle", "tie.greco", "tie.anti_grappling", "tie.judo_sambo") else 0.0
            sweep_prob = max(0.18, min(0.68, 0.62 - sweep_resist - 0.04 * float(def_state["fatigue"])))
            if rng.random() < sweep_prob:
                dump_tid = "sanda_sweep" if "sanda_sweep" in def_avail else (
                    "outside_trip" if "outside_trip" in def_avail else "cross"
                )
                # A caught-kick sweep wins position and deals clean dump impact (1.0x rather than 1.42x counter_hit)
                dump_dmg = compute_card_derived_damage(
                    k, def_card, att_card, dump_tid, "clean", def_state, att_state, in_active_slot=True
                )
                reg_c = str(dump_dmg["target_region"])
                att_state["damage"][reg_c] = round(att_state["damage"][reg_c] + dump_dmg["final_damage"], 3)
                def_state["contact_marks"] += 1
                def_state["control_marks"] += 1
                if att_tie in ("tie.freestyle", "tie.greco", "tie.anti_grappling", "tie.judo_sambo"):
                    # Opponent's tie turns the sweep into a standing clinch scramble instead of instant mat control
                    def_state["grappling_position"] = att_state["grappling_position"] = "over_under"
                    grappling_pos = "over_under"
                else:
                    def_state["posture_mode"] = att_state["posture_mode"] = "ground"
                    def_state["grappling_position"] = "half_guard_top"
                    att_state["grappling_position"] = "closed_guard_bottom"
                    def_state["grip"], att_state["grip"] = "top", "bottom"
                    grappling_pos = "half_guard_top"
                counter_followup_event = {
                    "counter_actor_id": defender_id,
                    "trigger": "kick_catch_dump",
                    "technique_id": dump_tid,
                    "damage": dump_dmg,
                }
        elif counter_triggered:
            # Choose a trained counter that reaches at current range_band
            if range_band == "kick":
                c_candidates = [m for m in ("side_kick", "teep", "low_kick", "body_kick", "cross", "jab") if m in def_avail]
            elif range_band == "clinch":
                c_candidates = [m for m in ("knee_body", "uppercut", "body_hook", "outside_trip", "hook") if m in def_avail]
            else:
                c_candidates = [m for m in ("cross", "uppercut", "hook", "body_hook", "jab", "haymaker") if m in def_avail]
            if c_candidates:
                c_tid = c_candidates[0]
                c_qual = "counter_hit" if rng.random() < 0.62 else "partial"
                c_dmg = compute_card_derived_damage(
                    k, def_card, att_card, c_tid, c_qual, def_state, att_state, in_active_slot=True
                )
                reg_c = str(c_dmg["target_region"])
                att_state["damage"][reg_c] = round(att_state["damage"][reg_c] + c_dmg["final_damage"], 3)
                def_state["contact_marks"] += 1
                counter_followup_event = {
                    "counter_actor_id": defender_id,
                    "trigger": f"{defense_used}_counter",
                    "technique_id": c_tid,
                    "damage": c_dmg,
                }

        slot_switched_to = None
        if outcome in ("evaded", "blocked", "checked", "caught", "jammed"):
            att_state["slot_stalls"] += 1
            if att_state["slot_stalls"] >= int(active_plan["abandon_threshold"]) and len(plans) > 1:
                att_state["active_slot_idx"] = (int(att_state["active_slot_idx"]) + 1) % len(plans)
                att_state["slot_Cursor"] = 0
                att_state["slot_stalls"] = 0
                att_state["slot_switches"] += 1
                slot_switched_to = plans[int(att_state["active_slot_idx"])]["slot_id"]
                att_state["active_slot_id"] = slot_switched_to
        else:
            att_state["slot_stalls"] = 0

        ex_event = {
            "exchange_index": len(exchanges) + 1,
            "t_start": t_start,
            "t_end": t_end,
            "frames": exchange_frames,
            "range": range_band,
            "lead_foot_matchup": lead_matchup,
            "attacker_id": attacker_id,
            "defender_id": defender_id,
            "active_slot_id": active_plan["slot_id"],
            "technique_id": tid,
            "attack_lane": attack_lane,
            "defender_posture_before": def_posture_before,
            "defender_readiness_profile": def_readiness,
            "lane_readiness_score": lane_readiness,
            "hit_probability": hit_prob,
            "outcome": outcome,
            "defense_used": defense_used,
            "kick_anatomy": kick_detail,
            "damage": dmg_info,
            "counter_followup": counter_followup_event,
            "grappling_position": grappling_pos,
            "forced_stance_switch": forced_stance_switch,
            "slot_switched_to": slot_switched_to,
            "state_changes": {
                "defender_damage": copy.deepcopy(def_state["damage"]),
                "attacker_damage": copy.deepcopy(att_state["damage"]),
                "defender_balance": def_state["balance"],
                "attacker_recovery_window": att_state["recovery_window"]["window_type"],
            },
        }
        exchanges.append(ex_event)

        # 7. Check Finish Conditions
        for fid in canonical_ids:
            opp_id = next(i for i in canonical_ids if i != fid)
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

    if not winner_id:
        scores = {}
        for fid in canonical_ids:
            opp_id = next(i for i in canonical_ids if i != fid)
            opp_d = actors[opp_id]["damage"]
            total_dmg_dealt = opp_d["head"] * 1.15 + opp_d["body"] * 1.05 + opp_d["leg"] * 1.0
            scores[fid] = total_dmg_dealt + 1.5 * float(actors[fid]["control_marks"])
        winner_id = max(canonical_ids, key=lambda i: (scores[i], i))
        finish_reason = "Decision (clock expired; card-derived damage + control)"

    # Recompute final postures & readiness profiles for final state schema validation
    final_lead = (
        "closed_stance"
        if actors[canonical_ids[0]]["orientation"] == actors[canonical_ids[1]]["orientation"]
        else "open_stance"
    )
    for fid in canonical_ids:
        opp_id = next(i for i in canonical_ids if i != fid)
        actors[fid]["posture"] = compute_posture_state(cards[fid], actors[fid], opt_behaviors)
        actors[fid]["readiness_profile"] = compute_readiness_profile(
            k, cards[fid], actors[fid], cards[opp_id], actors[opp_id], range_band, final_lead, opt_behaviors=opt_behaviors
        )

    final_state_v2 = {
        "version": "block-2",
        "clock_frames": clock_frames,
        "time_s": round(clock_frames / 24.0, 2),
        "arena": arena,
        "vertical_mode": vertical_mode,
        "range": range_band,
        "lead_foot_matchup": final_lead,
        "actors": actors,
    }

    return {
        "version": "block-v2",
        "ruleset": ruleset,
        "arena": arena,
        "vertical_mode": vertical_mode,
        "seed": seed,
        "fighter_a": card_a["fighter_id"],
        "fighter_b": card_b["fighter_id"],
        "duration_requested_s": duration_s,
        "duration_actual_s": round(clock_frames / 24.0, 2),
        "winner_id": winner_id,
        "winner_name": cards[winner_id]["name"],
        "finish_reason": finish_reason,
        "exchange_count": len(exchanges),
        "final_state_v2": final_state_v2,
        "actors_final": actors,
        "slot_plans": slot_plans,
        "exchanges": exchanges,
    }


# ---------------------------------------------------------------------------
# 8. Level 3: Many-Runs Monte Carlo Simulator & Director Mode (`simulate_many_v2`)
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
    """Run N seeded v2 fights to compute empirical win rates, method breakdown, deciding slots/lanes,
    and realistic directed runs validated against simulation_result_v2.schema.json.
    """
    k = knowledge or Knowledge()
    card_a, card_b = load_card_v2(k, a), load_card_v2(k, b)
    id_a, id_b = card_a["fighter_id"], card_b["fighter_id"]
    wins = {id_a: 0, id_b: 0}
    methods: Dict[str, int] = {}
    deciding_slots: Dict[str, int] = {}
    deciding_lanes: Dict[str, int] = {}
    matching_runs: List[Dict[str, object]] = []
    all_runs: List[Dict[str, object]] = []
    total_dur = 0.0

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
        total_dur += float(sim["duration_actual_s"])
        m_key = str(sim["finish_reason"]).split(" (")[0]
        methods[m_key] = methods.get(m_key, 0) + 1
        if sim["exchanges"]:
            last_ex = sim["exchanges"][-1]
            s_id = str(last_ex["active_slot_id"])
            l_id = str(last_ex["attack_lane"])
            deciding_slots[s_id] = deciding_slots.get(s_id, 0) + 1
            deciding_lanes[l_id] = deciding_lanes.get(l_id, 0) + 1
        all_runs.append(sim)
        if directed_winner and w == directed_winner:
            matching_runs.append(sim)

    selected_run = matching_runs[0] if matching_runs else all_runs[0]
    result = {
        "version": "block-2",
        "fighter_a": id_a,
        "fighter_b": id_b,
        "runs": runs,
        "ruleset": ruleset,
        "arena": arena,
        "vertical_mode": vertical_mode,
        "win_counts": wins,
        "empirical_win_rate_a": round(wins[id_a] / runs, 3),
        "empirical_win_rate_b": round(wins[id_b] / runs, 3),
        "method_breakdown": methods,
        "average_duration_s": round(total_dur / runs, 2),
        "deciding_slots": deciding_slots,
        "deciding_weakness_lanes": deciding_lanes,
        "directed_winner": directed_winner,
        "representative_fight": selected_run,
    }
    jsonschema.validate(result, read(k.root / "schemas/simulation_result_v2.schema.json"))
    return result


# ---------------------------------------------------------------------------
# 9. Bridge: Simulated v2 Exchanges -> Atomic Causal Beats (`Prep -> Commit -> Contact -> Consequence -> Recovery`)
# ---------------------------------------------------------------------------

def compile_simulated_fight_to_atomic_beats(
    sim_result: Dict[str, object],
    max_beats: int = 6,
) -> Dict[str, object]:
    """Translate the key exchanges of a `simulate_fight_v2` result into 1-Contact-Per-Beat
    `AtomicCausalBeat` blocks (`Prep -> Commit -> Contact -> Consequence -> Recovery`)
    plus single-sentence unlabeled natural-language prose.
    """
    from fight_move_system.atomic_causal_compiler import AtomicCausalBeat

    exchanges = list(sim_result.get("exchanges", []))
    actors_final = sim_result.get("actors_final", {})
    names = {fid: str(info.get("name", fid)) for fid, info in actors_final.items()}

    # Select up to `max_beats` high-impact or state-shifting exchanges (always including first and last)
    if len(exchanges) <= max_beats:
        selected = exchanges
    else:
        scored = sorted(
            exchanges[1:-1],
            key=lambda e: (
                1 if e.get("counter_followup") else 0,
                1 if e.get("outcome") in ("flush", "clean", "caught", "checked") else 0,
                float(e.get("damage", {}).get("final_damage", 0.0)),
            ),
            reverse=True,
        )[: max(0, max_beats - 2)]
        chosen_indices = {exchanges[0]["exchange_index"], exchanges[-1]["exchange_index"]} | {
            e["exchange_index"] for e in scored
        }
        selected = [e for e in exchanges if e["exchange_index"] in chosen_indices][:max_beats]

    beats: List[AtomicCausalBeat] = []
    for idx, ex in enumerate(selected, start=1):
        att_id = str(ex["attacker_id"])
        def_id = str(ex["defender_id"])
        att_name = names.get(att_id, att_id)
        def_name = names.get(def_id, def_id)
        tid = str(ex["technique_id"])
        outcome = str(ex["outcome"])
        posture = ex["defender_posture_before"]
        kick = ex.get("kick_anatomy")
        dmg = ex["damage"]
        counter = ex.get("counter_followup")
        pos_after = str(ex["grappling_position"])

        prep = (
            f"At {ex['range']} range ({ex['lead_foot_matchup']}), {def_name} holds {posture['guard_id']} "
            f"with {posture['weight_split']} weight and {posture['head_position']} head alignment "
            f"(lane {ex['attack_lane']} readiness {ex['lane_readiness_score']:.2f})"
        )
        if kick:
            commit = (
                f"{att_name} executes `{tid}` from `{ex['active_slot_id']}` using `{kick['kicking_leg']}` "
                f"({kick['chamber']} chamber, {kick['support_foot']} support pivot, {kick['path']} path)"
            )
            surface = kick["striking_surface"]
        else:
            commit = f"{att_name} initiates `{tid}` from `{ex['active_slot_id']}` along the `{ex['attack_lane']}` lane"
            surface = "striking limb"

        if outcome in ("clean", "flush", "partial"):
            contact = (
                f"{att_name}'s {surface} lands `{outcome}` on {def_name}'s {dmg['target_region']} "
                f"(card-derived damage {dmg['final_damage']:.2f})"
            )
            consequence = (
                f"From that impact, {def_name}'s balance shifts to `{ex['state_changes']['defender_balance']}` "
                f"in `{pos_after}` position"
            )
        elif outcome == "checked":
            contact = (
                f"{def_name} raises a hard shin block (`{ex['defense_used']}`) that meets {att_name}'s kicking shin on contact"
            )
            consequence = (
                f"From the shin-on-shin collision, {att_name} absorbs {dmg['recoil_leg_damage_to_attacker']:.2f} "
                f"recoil leg damage and stumbles onto compromised support"
            )
        elif outcome == "caught" and counter:
            contact = (
                f"{def_name} traps {att_name}'s kicking leg with `{ex['defense_used']}` and immediately sweeps the standing support "
                f"with `{counter['technique_id']}`"
            )
            consequence = (
                f"From the caught-kick dump, {att_name} crashes to the mat for {counter['damage']['final_damage']:.2f} "
                f"counter damage into `{pos_after}`"
            )
        elif counter:
            contact = (
                f"{def_name} uses `{ex['defense_used']}` to clear `{tid}` and fires an immediate counter `{counter['technique_id']}` "
                f"to {att_name}'s {counter['damage']['target_region']}"
            )
            consequence = (
                f"From the counter strike, {att_name} takes {counter['damage']['final_damage']:.2f} damage "
                f"while {def_name} takes the angle"
            )
        else:
            contact = f"{def_name} neutralizes `{tid}` with `{ex['defense_used'] or outcome}` across the `{ex['attack_lane']}` lane"
            consequence = f"With the attack denied, {def_name} preserves `{ex['state_changes']['defender_balance']}` balance"

        rec_win = ex["state_changes"]["attacker_recovery_window"]
        slot_note = f" and switches gameplan to `{ex['slot_switched_to']}`" if ex.get("slot_switched_to") else ""
        recovery = (
            f"{att_name} retracts through `{rec_win}` recovery{slot_note} while {def_name} resets guard in `{pos_after}`"
        )

        beats.append(
            AtomicCausalBeat(
                beat_id=f"BEAT_{idx:02d}",
                title=f"{ex['t_start']:.2f}s-{ex['t_end']:.2f}s | {att_name} `{tid}` -> {outcome.upper()}",
                named_contact_id=f"ex_{ex['exchange_index']}_{tid}_{outcome}",
                view="locked 180-degree full-body profile framing",
                prep=prep,
                commit=commit,
                contact=contact,
                consequence=consequence,
                recovery=recovery,
                license="1-frame contact accent on primary collision only",
                a_support_after="mat" if pos_after in ("side_control", "half_guard_top", "closed_guard_bottom", "mount_or_back_ride") else "two_feet",
                b_support_after="mat" if pos_after in ("side_control", "half_guard_top", "closed_guard_bottom", "mount_or_back_ride") else "two_feet",
            )
        )

    return {
        "beat_count": len(beats),
        "labeled_ir": "\n\n".join(b.render_labeled_block() for b in beats),
        "unlabeled_prose": "\n\n".join(b.render_unlabeled_seedance_sentence() for b in beats),
        "beats": [
            {
                "beat_id": b.beat_id,
                "title": b.title,
                "labeled_ir": b.render_labeled_block(),
                "unlabeled_prose": b.render_unlabeled_seedance_sentence(),
            }
            for b in beats
        ],
    }


# ---------------------------------------------------------------------------
# 10. Automated Round-Robin Balance Auditor & Top-3 Imbalance Cause Reporter
# ---------------------------------------------------------------------------

def explain_matchup_top_causes_v2(
    many_result: Dict[str, object],
    card_a: Dict[str, object],
    card_b: Dict[str, object],
) -> List[str]:
    """Extract the top 3 concrete mechanical causes explaining a pairwise matchup outcome."""
    id_a, id_b = str(card_a["fighter_id"]), str(card_b["fighter_id"])
    wa = float(many_result["empirical_win_rate_a"])
    wb = float(many_result["empirical_win_rate_b"])
    fav_card, dog_card = (card_a, card_b) if wa >= wb else (card_b, card_a)
    fav_id, dog_id = str(fav_card["fighter_id"]), str(dog_card["fighter_id"])

    rep = many_result["representative_fight"]
    exchanges = list(rep.get("exchanges", []))
    total_ex = max(1, len(exchanges))

    # 1. Range distribution & footwork control
    range_counts: Dict[str, int] = {}
    fav_rdy_list: List[float] = []
    dog_rdy_list: List[float] = []
    counter_count = 0
    catch_or_check_count = 0

    for ex in exchanges:
        r = str(ex["range"])
        range_counts[r] = range_counts.get(r, 0) + 1
        if ex["defender_id"] == fav_id:
            fav_rdy_list.append(float(ex["lane_readiness_score"]))
        else:
            dog_rdy_list.append(float(ex["lane_readiness_score"]))
        if ex.get("counter_followup") and ex["counter_followup"].get("counter_actor_id") == fav_id:
            counter_count += 1
        if ex["defender_id"] == fav_id and ex["outcome"] in ("caught", "checked"):
            catch_or_check_count += 1

    top_range, top_range_n = max(range_counts.items(), key=lambda kv: kv[1]) if range_counts else ("punch", 0)
    top_lane = (
        max(many_result["deciding_weakness_lanes"].items(), key=lambda kv: kv[1])[0]
        if many_result.get("deciding_weakness_lanes")
        else "head_straight"
    )
    top_method = (
        max(many_result["method_breakdown"].items(), key=lambda kv: kv[1])[0]
        if many_result.get("method_breakdown")
        else "Decision"
    )
    fav_avg_rdy = sum(fav_rdy_list) / max(1, len(fav_rdy_list))
    dog_avg_rdy = sum(dog_rdy_list) / max(1, len(dog_rdy_list))
    fav_ctrl = int(rep["actors_final"][fav_id].get("control_marks", 0))

    causes = [
        (
            f"Range & Footwork Control: {top_range_n}/{total_ex} exchanges ({top_range_n / total_ex * 100:.0f}%) "
            f"took place at `{top_range}` range (favoring {fav_id}'s {fav_card['dimensions'].get('stance')} / {fav_card['dimensions'].get('mentality')})"
        ),
        (
            f"Posture & Seam Readiness Delta: {fav_id} maintained {fav_avg_rdy:.2f} avg lane readiness vs "
            f"{dog_id}'s {dog_avg_rdy:.2f}, exploiting the `{top_lane}` seam toward `{top_method}` finishes"
        ),
        (
            f"Tactical Counters & Control: {fav_id} generated {counter_count} contested counters, "
            f"{catch_or_check_count} kick catches/checks, and {fav_ctrl} grappling control marks"
        ),
    ]
    return causes


def audit_round_robin_balance_v2(
    runs_per_pair: int = 200,
    ruleset: str = "mma",
    duration_s: float = 60.0,
    arena: str = "cage",
    verify_order_invariance_seeds: int = 5,
    knowledge: Optional[Knowledge] = None,
) -> Dict[str, object]:
    """Run an all-pairs round-robin balance audit across all 12 predefined block-2 archetypes,
    verifying:
      1. Order invariance (`simulate_fight_v2(A, B, s) == simulate_fight_v2(B, A, s)`),
      2. Overall archetype win rates within `[0.35, 0.65]`,
      3. No individual pairwise matchup exceeding `0.85`,
      4. Automatic Top-3 mechanical cause attribution for every pair.
    """
    k = knowledge or Knowledge()
    v2_dir = k.root / "cards" / "v2"
    ids = sorted([p.stem for p in v2_dir.glob("*.json")]) if v2_dir.exists() else sorted(list(k.cards.keys()))
    cards_map = {fid: load_card_v2(k, fid) for fid in ids}

    wins = {fid: 0.0 for fid in ids}
    matches = {fid: 0 for fid in ids}
    pairwise_records: List[Dict[str, object]] = []
    order_invariance_ok = True

    for i, a in enumerate(ids):
        for b in ids[i + 1 :]:
            res = simulate_many_v2(
                cards_map[a],
                cards_map[b],
                runs=runs_per_pair,
                ruleset=ruleset,
                duration_s=duration_s,
                arena=arena,
                knowledge=k,
            )
            wa = float(res["empirical_win_rate_a"])
            wb = float(res["empirical_win_rate_b"])
            wins[a] += wa
            wins[b] += wb
            matches[a] += 1
            matches[b] += 1

            # Verify order invariance on sample seeds
            for s in range(1, verify_order_invariance_seeds + 1):
                f_ab = simulate_fight_v2(cards_map[a], cards_map[b], ruleset=ruleset, duration_s=duration_s, seed=s, arena=arena, knowledge=k)
                f_ba = simulate_fight_v2(cards_map[b], cards_map[a], ruleset=ruleset, duration_s=duration_s, seed=s, arena=arena, knowledge=k)
                if f_ab["winner_id"] != f_ba["winner_id"] or f_ab["exchange_count"] != f_ba["exchange_count"]:
                    order_invariance_ok = False

            causes = explain_matchup_top_causes_v2(res, cards_map[a], cards_map[b])
            pairwise_records.append(
                {
                    "fighter_a": a,
                    "fighter_b": b,
                    "win_rate_a": wa,
                    "win_rate_b": wb,
                    "max_win_rate": round(max(wa, wb), 3),
                    "method_breakdown": res["method_breakdown"],
                    "top_3_causes": causes,
                }
            )

    overall_rates = {
        fid: round(wins[fid] / max(1, matches[fid]), 3)
        for fid in sorted(ids, key=lambda x: wins[x] / max(1, matches[x]), reverse=True)
    }
    pairwise_records.sort(key=lambda r: float(r["max_win_rate"]), reverse=True)
    max_pair_rate = max((float(r["max_win_rate"]) for r in pairwise_records), default=0.5)
    outliers_overall = {
        fid: rate for fid, rate in overall_rates.items() if rate < 0.35 or rate > 0.65
    }
    outliers_pairwise = [r for r in pairwise_records if float(r["max_win_rate"]) > 0.85]

    return {
        "runs_per_pair": runs_per_pair,
        "ruleset": ruleset,
        "duration_s": duration_s,
        "arena": arena,
        "archetype_count": len(ids),
        "pair_count": len(pairwise_records),
        "order_invariance_verified": order_invariance_ok,
        "archetype_overall_win_rates": overall_rates,
        "all_within_target_band_35_65": len(outliers_overall) == 0,
        "overall_outliers": outliers_overall,
        "max_pairwise_win_rate": max_pair_rate,
        "no_sweep_above_85": len(outliers_pairwise) == 0,
        "pairwise_outliers_above_85": outliers_pairwise,
        "top_skewed_pairs": pairwise_records[:10],
        "pairwise_matrix": pairwise_records,
    }

