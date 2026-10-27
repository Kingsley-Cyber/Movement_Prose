"""Dynamic defensive posture and actor state helpers for BLOCK Simulator v2."""

from __future__ import annotations

from typing import Any

from .data import load_model_v2


def compute_posture_state(
    card: dict[str, Any],
    actor_state: dict[str, Any],
    opt_behaviors: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Build the fighter's live defensive posture from guard + stance + defense method + current damage/fatigue/range."""
    model_cfg = load_model_v2()
    p_cfg = model_cfg.get("posture", {})
    p_rules = model_cfg.get("legacy", {}).get("posture_rules_machine", {})

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
    decay_default = float(p_cfg.get("guard_decay_rate_default", 0.06))
    decay_rate = float(g_prof.get("guard_decay_rate", decay_default))

    dmg = actor_state.get("damage", {"head": 0.0, "body": 0.0, "leg": 0.0})
    fatigue = float(actor_state.get("fatigue", 0.0))
    rec_win = actor_state.get("recovery_window", {}).get("window_type", "none")

    # Dynamic shifts during the fight:
    if actor_state.get("posture_mode") == "ground":
        height = "grounded"
        base_width = "mat"
    elif rec_win == "single_leg_recovery":
        base_width = str(p_rules.get("single_leg_recovery_base_width", "balanced"))
    elif float(dmg.get("leg", 0.0)) >= float(p_cfg.get("rear_heavy_to_front_heavy_leg_damage", 4.0)) and weight_split == "rear_heavy":
        weight_split = "front_heavy"

    if actor_state.get("grip") in ("collar", "controlled") and height != "grounded":
        head_pos = "pulled_down"
    elif fatigue >= float(p_cfg.get("head_position_high_fatigue", 5.0)) or float(dmg.get("head", 0.0)) >= float(p_cfg.get("head_position_high_head_damage", 4.5)):
        head_pos = "centerline_high"

    # Guard integrity decays as body damage and fatigue accumulate
    guard_min = float(p_cfg.get("guard_integrity_min", 0.25))
    body_w = float(p_cfg.get("guard_decay_body_weight", 0.6))
    fat_w = float(p_cfg.get("guard_decay_fatigue_weight", 0.35))
    guard_integrity = max(
        guard_min,
        round(1.0 - decay_rate * (body_w * float(dmg.get("body", 0.0)) + fat_w * fatigue), 3),
    )

    feint_pen = float(p_cfg.get("vision_feint_penalty", 0.8)) if actor_state.get("attention", {}).get("feinted") else 0.0
    head_pen = float(p_cfg.get("vision_per_head_damage", 0.12))
    vision_eff = max(
        1.0,
        round(
            base_vision - feint_pen - head_pen * float(dmg.get("head", 0.0)),
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
