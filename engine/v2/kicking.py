"""Kicking subsystem: biomechanical kick unrolling for BLOCK Simulator v2."""

from __future__ import annotations

from typing import Any

from .data import KICK_IDS, load_model_v2, load_techniques_v2


def unroll_kick_anatomy(
    tid: str,
    card: dict[str, Any],
    orientation: str,
) -> dict[str, Any] | None:
    """Generate the biomechanical kick descriptor for any kick/knee move from model data."""
    if tid not in KICK_IDS:
        return None
    model_cfg = load_model_v2()
    ka_cfg = model_cfg.get("legacy", {}).get("kick_anatomy", {})
    default_kick_opt = str(ka_cfg.get("default_kicking_option", ""))
    school = str(card["dimensions"].get("kicking") or default_kick_opt).split(".")[-1]
    lead_side = "left" if orientation == "orthodox" else "right"
    rear_side = "right" if orientation == "orthodox" else "left"

    templates = ka_cfg.get("templates", {})
    if tid in templates:
        tpl = templates[tid]
        return {
            "kick_family": school,
            "kicking_leg": str(tpl["kicking_leg"]).format(lead_side=lead_side, rear_side=rear_side),
            "chamber": str(tpl["chamber"]),
            "support_foot": str(tpl["support_foot"]).format(lead_side=lead_side, rear_side=rear_side),
            "path": str(tpl["path"]),
            "target_region": str(tpl["target_region"]),
            "striking_surface": str(tpl["striking_surface"]),
            "ending": str(tpl["ending"]),
            "single_leg_exposure_window": str(tpl["single_leg_exposure_window"]),
        }

    if tid == ka_cfg.get("low_kick_id"):
        is_thai = school == ka_cfg.get("thai_school")
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

    if tid in ka_cfg.get("body_kick_ids", []):
        is_switch = tid == ka_cfg.get("switch_kick_id")
        leg_used = f"switched_{lead_side}_power_leg" if is_switch else f"rear_{rear_side}"
        return {
            "kick_family": school,
            "kicking_leg": leg_used,
            "chamber": "switch_hop_hip_load" if is_switch else "open_hip_torque_arc",
            "support_foot": "planted_support_ball_pivot_110deg",
            "path": "horizontal_round_arc_to_ribs",
            "target_region": "body_liver_or_floating_ribs",
            "striking_surface": "lower_shin_bone",
            "ending": "step_down_into_stance" if is_switch else "full_hip_turn_recovery",
            "single_leg_exposure_window": "high_catchable_window",
        }

    t_v2 = load_techniques_v2().get(tid, {})
    if t_v2.get("kind") == "kick":
        side = str(t_v2.get("side") or "rear")
        kicking_leg = f"lead_{lead_side}" if side == "lead" else f"rear_{rear_side}"
        support_foot = f"rear_{rear_side}_planted" if side == "lead" else f"lead_{lead_side}_ball_pivot"
        if t_v2.get("vertical_min") in ("athletic", "aerial"):
            support_foot = "airborne_none"
        line = str(t_v2.get("line") or "rear_round_kick")
        surface = str(t_v2.get("striking_surface") or "shin")
        reg = str(t_v2.get("target_region") or "body")
        return {
            "kick_family": school,
            "kicking_leg": kicking_leg,
            "chamber": f"{line}_chamber",
            "support_foot": support_foot,
            "path": f"{line}_trajectory",
            "target_region": reg,
            "striking_surface": surface,
            "ending": "retract_to_stance",
            "single_leg_exposure_window": "moderate",
        }

    is_jumping_knee = tid == ka_cfg.get("jumping_knee_id")
    return {
        "kick_family": school,
        "kicking_leg": f"rear_{rear_side}",
        "chamber": "airborne_double_knee_tuck" if is_jumping_knee else "clinch_hip_thrust_spear",
        "support_foot": "airborne_none" if is_jumping_knee else f"lead_{lead_side}_ball_rise",
        "path": "rising_vertical_spear" if is_jumping_knee else "diagonal_upward_spear",
        "target_region": "head_chin" if is_jumping_knee else "body_solar_plexus_ribs",
        "striking_surface": "pointed_kneecap",
        "ending": "two_foot_landing_recovery" if is_jumping_knee else "re-establish_clinch_base",
        "single_leg_exposure_window": "high_landing_recovery" if is_jumping_knee else "low",
    }
