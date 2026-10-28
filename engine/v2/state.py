"""Dynamic defensive posture and actor state helpers for BLOCK Simulator v2."""

from __future__ import annotations

import random
from typing import Any

from .data import load_model_v2
from .laterality import resolve_actor_laterality


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

    dmg_scale_inv = (
        1.0
        if actor_state.get("posture_mode") == "ground"
        else 1.0 / max(1.0, float(actor_state.get("damage_limit_scale", 1.0)))
    )
    raw_dmg = actor_state.get("damage", {"head": 0.0, "body": 0.0, "leg": 0.0})
    dmg = {k: float(v) * dmg_scale_inv for k, v in raw_dmg.items()}
    fatigue = float(actor_state.get("fatigue", 0.0)) * dmg_scale_inv
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
    active_effs = actor_state.get("active_effects", [])
    eff_vision_delta = sum(float(e.get("value", 0.0)) for e in active_effs if e.get("effect") == "vision")
    vision_eff = max(
        1.0,
        round(
            base_vision - feint_pen - head_pen * float(dmg.get("head", 0.0)) + eff_vision_delta,
            2,
        ),
    )

    balance = str(actor_state.get("balance", "stable"))
    for e in active_effs:
        if e.get("effect") == "low_posture" and height != "grounded":
            height = "low_crouch"
        elif e.get("effect") == "balance":
            eb = str(e.get("value", "compromised"))
            if eb == "off_base" or (eb == "compromised" and balance == "stable"):
                balance = eb
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


def tick_active_effects(actors: dict[str, dict[str, Any]]) -> None:
    """Decrement remaining exchange durations on active effects from prior exchanges and sync attention flags."""
    for st in actors.values():
        effs = st.get("active_effects")
        if not effs:
            continue
        kept: list[dict[str, Any]] = []
        for e in effs:
            rem = int(e.get("remaining", 1)) - 1
            if rem > 0:
                e_copy = dict(e)
                e_copy["remaining"] = rem
                kept.append(e_copy)
        st["active_effects"] = kept
        att = st.setdefault("attention", {"feinted": False, "outside_angle_conceded": False, "focus_line": "neutral"})
        if any(e.get("effect") == "attention" for e in kept):
            att["feinted"] = True
        if any(e.get("effect") == "outside_angle" for e in kept):
            att["outside_angle_conceded"] = True


def apply_technique_effects(
    source_tid: str,
    effects_spec: list[dict[str, Any]] | None,
    actor_id: str,
    opponent_id: str,
    actors: dict[str, dict[str, Any]],
    cards: dict[str, dict[str, Any]],
    range_band: str,
    standing_ladder: list[str],
    rng: random.Random | None = None,
) -> tuple[list[dict[str, Any]], str]:
    """Interpret technique on_success_effects (§7.17) and return (applied_records, updated_range_band)."""
    if not effects_spec:
        return [], range_band

    applied: list[dict[str, Any]] = []
    cur_range = range_band
    for eff in effects_spec:
        chance = eff.get("chance")
        if chance is not None:
            if rng is None or rng.random() >= float(chance):
                continue
        target_id = actor_id if eff.get("target") == "self" else opponent_id
        target_state = actors[target_id]
        eff_type = str(eff.get("effect", ""))
        duration = int(eff.get("exchanges", 1) or 1)
        active_list = target_state.setdefault("active_effects", [])

        if eff_type == "stance_switch":
            target_state["orientation"] = "southpaw" if target_state.get("orientation") == "orthodox" else "orthodox"
            target_state["laterality"] = resolve_actor_laterality(cards[target_id], str(target_state["orientation"]))
        elif eff_type == "push_back":
            steps = int(eff.get("value", 1) or 1)
            if actors[actor_id].get("posture_mode") == "standing":
                actors[actor_id]["grappling_position"] = actors[opponent_id]["grappling_position"] = "standing_neutral"
                actors[actor_id]["grip"] = actors[opponent_id]["grip"] = None
            if cur_range in standing_ladder:
                r_idx = standing_ladder.index(cur_range)
                cur_range = standing_ladder[max(0, r_idx - steps)]
        elif eff_type == "attention":
            target_state.setdefault("attention", {})["feinted"] = True
            active_list.append(
                {
                    "effect": "attention",
                    "value": eff.get("value", "feinted"),
                    "remaining": duration + 1,
                    "source_technique": source_tid,
                }
            )
        elif eff_type == "outside_angle":
            target_state.setdefault("attention", {})["outside_angle_conceded"] = True
            active_list.append(
                {
                    "effect": "outside_angle",
                    "remaining": duration + 1,
                    "source_technique": source_tid,
                }
            )
        elif eff_type == "balance":
            bal_val = str(eff.get("value", "compromised"))
            target_state["balance"] = bal_val
            active_list.append(
                {
                    "effect": "balance",
                    "value": bal_val,
                    "remaining": duration + 1,
                    "source_technique": source_tid,
                }
            )
        elif eff_type == "low_posture":
            active_list.append(
                {
                    "effect": "low_posture",
                    "remaining": duration + 1,
                    "source_technique": source_tid,
                }
            )
        elif eff_type == "lane_penalty":
            active_list.append(
                {
                    "effect": "lane_penalty",
                    "lanes": list(eff.get("lanes", [])),
                    "value": float(eff.get("value", 0.0)),
                    "remaining": duration + 1,
                    "source_technique": source_tid,
                }
            )
        elif eff_type == "vision":
            active_list.append(
                {
                    "effect": "vision",
                    "value": float(eff.get("value", 0.0)),
                    "remaining": duration + 1,
                    "source_technique": source_tid,
                }
            )
        elif eff_type == "skill_penalty":
            active_list.append(
                {
                    "effect": "skill_penalty",
                    "skills": list(eff.get("skills", [])),
                    "value": float(eff.get("value", 0.0)),
                    "remaining": duration + 1,
                    "source_technique": source_tid,
                }
            )

        rec: dict[str, Any] = {
            "source_technique": source_tid,
            "actor_id": actor_id,
            "target_id": target_id,
            "effect": eff_type,
        }
        if "value" in eff:
            rec["value"] = eff["value"]
        if "lanes" in eff:
            rec["lanes"] = list(eff["lanes"])
        if "skills" in eff:
            rec["skills"] = list(eff["skills"])
        if "exchanges" in eff:
            rec["exchanges"] = int(eff["exchanges"])
        applied.append(rec)

    return applied, cur_range
