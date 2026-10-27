"""8-lane defensive readiness profile calculator for BLOCK Simulator v2."""

from __future__ import annotations

from typing import Any

from ..ontology import Knowledge
from .data import LANES, get_attack_profile, load_model_v2, load_option_behaviors
from .state import compute_posture_state


def _apply_range_lane_bonus(
    opt_meta: dict[str, Any] | None,
    range_band: str,
    lane: str,
    wall_near: bool,
) -> float:
    if not opt_meta:
        return 0.0
    rlb = opt_meta.get("range_lane_bonus")
    if not rlb:
        return 0.0
    if range_band not in rlb.get("ranges", []):
        return 0.0
    if rlb.get("unless") == "wall_near" and wall_near:
        return 0.0
    lanes_spec = rlb.get("lanes", "all")
    if lanes_spec != "all" and lane not in lanes_spec:
        return 0.0
    return float(rlb.get("delta", 0.0))


def _matches_breakdown_rule(
    rule: dict[str, Any],
    lane: str,
    fatigue: float,
    dmg: dict[str, Any],
    posture: dict[str, Any],
    att_info: dict[str, Any],
    wall_near: bool,
    lead_foot_matchup: str,
    opp_tie: str | None,
) -> bool:
    lanes_spec = rule.get("lanes", "all")
    if lanes_spec != "all" and lane not in lanes_spec:
        return False
    when_any = rule.get("when_any", {})
    for cond_key, cond_val in when_any.items():
        if cond_key == "fatigue_gte" and fatigue >= float(cond_val):
            return True
        if cond_key == "head_damage_gte" and float(dmg["head"]) >= float(cond_val):
            return True
        if cond_key == "body_damage_gte" and float(dmg["body"]) >= float(cond_val):
            return True
        if cond_key == "leg_damage_gte" and float(dmg["leg"]) >= float(cond_val):
            return True
        if cond_key == "vision_lt" and float(posture["vision_effective"]) < float(cond_val):
            return True
        if cond_key == "feinted" and bool(att_info.get("feinted")) == bool(cond_val):
            return True
        if cond_key == "wall_near" and wall_near == bool(cond_val):
            return True
        if cond_key == "stance_relation" and lead_foot_matchup == str(cond_val):
            return True
        if cond_key == "weight_split" and posture["weight_split"] == str(cond_val):
            return True
        if cond_key == "base_width" and posture["base_width"] == str(cond_val):
            return True
        if cond_key == "opponent_tie_in" and opp_tie in cond_val:
            return True
    return False


def compute_readiness_profile(
    k: Knowledge,
    card: dict[str, Any],
    actor_state: dict[str, Any],
    opponent_card: dict[str, Any],
    opponent_state: dict[str, Any],
    range_band: str,
    lead_foot_matchup: str,
    incoming_tid: str | None = None,
    opt_behaviors: dict[str, dict[str, Any]] | None = None,
    model_cfg: dict[str, Any] | None = None,
) -> dict[str, float]:
    """Compute the fighter's 8-lane defensive readiness profile for the current moment."""
    beh = opt_behaviors if opt_behaviors is not None else load_option_behaviors(k.root)
    m_cfg = model_cfg if model_cfg is not None else load_model_v2(k.root)
    dim_cfg = m_cfg.get("diminishing_returns", {})
    tempo_cfg = m_cfg.get("tempo_rules", {})
    state_mods = m_cfg.get("state_modifiers", {})
    r_cfg = m_cfg.get("readiness", {})
    w_cfg = m_cfg.get("readiness_weights", {})
    p_rules = m_cfg.get("legacy", {}).get("posture_rules_machine", {})

    posture = compute_posture_state(card, actor_state, beh)
    dims = card["dimensions"]
    guard_id = dims.get("hands")
    def_id = dims.get("defense")
    stance_id = dims.get("stance")
    tie_id = dims.get("tie")
    target_id = dims.get("target")
    kicking_id = dims.get("kicking")
    mentality_id = dims.get("mentality")

    g_opt = beh.get(guard_id) if guard_id else None
    d_opt = beh.get(def_id) if def_id else None
    s_opt = beh.get(stance_id) if stance_id else None

    g_bonuses = g_opt.get("lane_readiness_bonus", {}) if g_opt else {}
    d_bonuses = d_opt.get("lane_readiness_bonus", {}) if d_opt else {}
    s_bonuses = s_opt.get("lane_readiness_bonus", {}) if s_opt else {}
    t_bonuses = beh.get(tie_id, {}).get("lane_readiness_bonus", {}) if tie_id else {}
    tar_seams = beh.get(target_id, {}).get("lane_readiness_bonus", {}) if target_id else {}
    kick_seams = beh.get(kicking_id, {}).get("lane_readiness_bonus", {}) if kicking_id else {}
    men_seams = beh.get(mentality_id, {}).get("lane_readiness_bonus", {}) if mentality_id else {}

    dmg = actor_state.get("damage", {"head": 0.0, "body": 0.0, "leg": 0.0})
    fatigue = float(actor_state.get("fatigue", 0.0))
    rec_win = actor_state.get("recovery_window", {})
    exposed_lanes = set(rec_win.get("exposed_lanes", []))
    rec_penalty = float(rec_win.get("readiness_penalty", 0.0))
    att_info = actor_state.get("attention", {})
    read_mem = actor_state.get("read_memory", {"seen_counts": {}, "consecutive_same_move_by_opponent": 0})
    wall_near = actor_state.get("wall_proximity") == "near"

    asymptote = float(dim_cfg.get("posture_asymptote", 2.40))
    compression = float(dim_cfg.get("readiness_compression", 0.62))
    min_rdy = float(dim_cfg.get("min_readiness", 1.45))
    max_rdy = float(dim_cfg.get("max_readiness", 4.85))
    tempo_damping = float(dim_cfg.get("tempo_defensive_damping", 0.65))
    base_readiness = float(w_cfg.get("base_readiness", 3.0))
    stance_weight = float(w_cfg.get("stance_weight", 0.85))

    def_read_gain = float(get_attack_profile(mentality_id, beh).get("read_gain_multiplier", 1.0))
    opp_dims = opponent_card.get("dimensions", {})
    att_read_decay = (
        float(get_attack_profile(opp_dims.get("target"), beh).get("read_decay_factor", 1.0))
        * float(get_attack_profile(opp_dims.get("mentality"), beh).get("read_decay_factor", 1.0))
        * float(get_attack_profile(opp_dims.get("stance"), beh).get("read_decay_factor", 1.0))
    )
    opp_tie = opp_dims.get("tie")
    def_breakdown_rules = d_opt.get("breakdown_rules", []) if d_opt else []
    damped_mentality = p_rules.get("damped_mentality")

    clinch_g_w = float(r_cfg.get("clinch_guard_weight", 0.35))
    clinch_t_w = float(r_cfg.get("clinch_tie_weight", 1.15))
    null_tie_def = float(r_cfg.get("null_tie_lane_default", -0.6))
    uh_bonus = float(r_cfg.get("underhook_bonus_per_hook", 0.35))
    kick_head_scale = float(r_cfg.get("kick_range_head_seam_scale", 0.15))
    off_seam_scale = float(r_cfg.get("offensive_seam_scale", 0.50))
    men_neg_scale = float(r_cfg.get("mentality_negative_scale", 0.50))
    rec_non_exp_frac = float(r_cfg.get("recovery_non_exposed_fraction", 0.35))
    feint_pen = float(r_cfg.get("feint_penalty", -0.55))
    read_per_seen = float(r_cfg.get("read_per_seen", 0.16))
    read_per_consec = float(r_cfg.get("read_per_consecutive", 0.24))

    comp_bal_pen = abs(float(state_mods.get("compromised_balance_penalty", -0.95)))
    off_bal_pen = abs(float(state_mods.get("off_base_balance_penalty", -1.65)))
    out_ang_pen = abs(float(state_mods.get("outside_angle_penalty", -1.10)))
    open_rear_pen = abs(float(state_mods.get("open_stance_rear_lane_penalty", -0.35)))
    feint_att_pen = abs(float(state_mods.get("feint_attention_penalty", -1.10)))
    rep_read_cap = float(state_mods.get("repeated_move_read_bonus", 0.85))
    novel_pen = abs(float(state_mods.get("novel_move_surprise_penalty", -0.20)))
    fat_pen_per_pt = abs(float(state_mods.get("fatigue_per_point_penalty", -0.10)))
    head_dmg_pen = abs(float(state_mods.get("head_damage_reaction_penalty", -0.10)))
    body_dmg_pen = abs(float(state_mods.get("body_damage_high_guard_drop", -0.14)))
    leg_dmg_pen = abs(float(state_mods.get("leg_damage_check_and_mobility_penalty", -0.20)))

    profile: dict[str, float] = {}
    for lane in LANES:
        score = base_readiness

        # 1. In clinch or ground, defense becomes posture, tie & hand-fighting rather than guard
        if range_band in ("clinch", "ground"):
            score += clinch_g_w * float(g_bonuses.get(lane, 0.0))
            score += clinch_t_w * float(t_bonuses.get(lane, null_tie_def if tie_id is None else 0.0))
            underhooks = int(actor_state.get("sub_grips", {}).get("underhooks", 0))
            score += uh_bonus * underhooks
        else:
            g_val = float(g_bonuses.get(lane, 0.0))
            if range_band in ("kick", "outside") and g_val < 0 and lane in ("head_straight", "head_hook", "head_uppercut"):
                g_val *= kick_head_scale
            static_posture_bonus = (
                g_val * float(posture["guard_integrity"])
                + float(d_bonuses.get(lane, 0.0))
                + stance_weight * float(s_bonuses.get(lane, 0.0))
            )
            score += static_posture_bonus / (1.0 + abs(static_posture_bonus) / asymptote)
            if range_band in ("kick", "outside"):
                score += _apply_range_lane_bonus(d_opt, range_band, lane, wall_near)
                score += _apply_range_lane_bonus(s_opt, range_band, lane, wall_near)

        # 1b. Seam exposures from offensive options (target, kicking, mentality)
        men_val = float(men_seams.get(lane, 0.0))
        seam_total = off_seam_scale * (float(tar_seams.get(lane, 0.0)) + float(kick_seams.get(lane, 0.0))) + (
            men_val if men_val > 0 else men_neg_scale * men_val
        )
        score += seam_total

        # 2. Defense method situational breakdowns (first matching rule per option)
        for rule in def_breakdown_rules:
            if _matches_breakdown_rule(
                rule, lane, fatigue, dmg, posture, att_info, wall_near, lead_foot_matchup, opp_tie
            ):
                if "delta_from_model" in rule:
                    key_parts = str(rule["delta_from_model"]).split(".")
                    val = m_cfg
                    for kp in key_parts:
                        val = val.get(kp, {}) if isinstance(val, dict) else None
                    delta = float(val if isinstance(val, (int, float)) else rule.get("delta_default", -1.25))
                    score += delta
                else:
                    score += float(rule.get("delta", 0.0))
                break

        # 3. Recovery window from the fighter's own prior attack
        if lane in exposed_lanes:
            score -= rec_penalty
        else:
            score -= rec_non_exp_frac * rec_penalty

        # 4. Balance state
        if posture["balance"] == "compromised":
            score -= comp_bal_pen
        elif posture["balance"] == "off_base":
            score -= off_bal_pen

        # 5. Outside angle & Lead-foot matchup (open vs. closed stance)
        if att_info.get("outside_angle_conceded"):
            score -= out_ang_pen
        if lead_foot_matchup == "open_stance" and lane in ("head_straight", "body"):
            score -= open_rear_pen

        # 6. Attention (feints pull the guard/eyes)
        if att_info.get("feinted"):
            if att_info.get("focus_line") == "high_drawn" and lane in ("body", "leg", "entry"):
                score -= feint_att_pen
            else:
                score += feint_pen

        # 7. Reads (read memory: scaled by defender's read_gain_multiplier and attacker's read_decay_factor)
        if incoming_tid:
            seen_n = int(read_mem.get("seen_counts", {}).get(incoming_tid, 0))
            consec_n = int(read_mem.get("consecutive_same_move_by_opponent", 0))
            if seen_n == 0:
                score -= novel_pen
            else:
                raw_read = min(rep_read_cap, read_per_seen * seen_n + read_per_consec * consec_n)
                score += raw_read * def_read_gain * att_read_decay

        # 8. Regional Damage & Fatigue Effects
        score -= fat_pen_per_pt * fatigue
        if lane in ("head_straight", "head_hook"):
            score -= body_dmg_pen * float(dmg["body"])
            score -= head_dmg_pen * float(dmg["head"])
        elif lane == "leg":
            score -= leg_dmg_pen * float(dmg["leg"])

        # 9. Guard range-lane bonus (e.g. 52-shield pocket defense) & Low-Tempo defensive patience
        score += _apply_range_lane_bonus(g_opt, range_band, lane, wall_near)

        tempo_val = int(card.get("tempo", 3))
        if tempo_val < 3:
            low_tempo_per_pt = float(tempo_cfg.get("low_tempo_readiness_per_point", 0.22))
            damp = tempo_damping if mentality_id == damped_mentality else 1.0
            score += damp * low_tempo_per_pt * (3 - tempo_val)

        # Compress additive readiness modifiers around neutral base_readiness and cap in [min_rdy, max_rdy]
        compressed = base_readiness + compression * (score - base_readiness)
        profile[lane] = round(max(min_rdy, min(max_rdy, compressed)), 3)

    return profile
