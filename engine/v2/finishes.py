"""Finish condition checks and decision scoring for BLOCK Simulator v2."""

from __future__ import annotations

import random
from typing import Any

from .data import load_model_v2
from .defense import contest_roll


def resolve_standing_count_or_knockdown(
    defender_state: dict[str, Any],
    ruleset_cfg: dict[str, Any] | None = None,
    model_cfg: dict[str, Any] | None = None,
    rng: random.Random | None = None,
) -> dict[str, Any] | None:
    """Apply knockdown counters and resolve standing count or MMA ground follow-up hook (§7.14, §8.5)."""
    m_cfg = model_cfg if model_cfg is not None else load_model_v2()
    defender_state["knockdowns_round"] = int(defender_state.get("knockdowns_round", 0)) + 1
    defender_state["knockdowns_total"] = int(defender_state.get("knockdowns_total", 0)) + 1

    r_cfg = ruleset_cfg or {}
    on_kd = str(r_cfg.get("ground", {}).get("on_knockdown", "fight_continues"))
    if on_kd == "standing_count":
        sc_cfg = m_cfg.get("knockdowns", {}).get("standing_count", {})
        rec_base = float(sc_cfg.get("recover_base", 0.8))
        rec_per_hd = float(sc_cfg.get("recover_per_head_damage", -0.05))
        head_dmg = float(defender_state.get("damage", {}).get("head", 0.0))
        p_recover = max(0.05, min(0.95, rec_base + rec_per_hd * head_dmg))
        recovered, roll, p_eff = contest_roll(p_recover, band_name="standing_count", rng=rng, model_cfg=m_cfg)
        if not recovered:
            defender_state["failed_standing_count"] = True
        return {
            "p_recover": round(p_eff, 4),
            "roll": round(roll, 4),
            "recovered": bool(recovered),
        }

    fu_bonus = float(
        m_cfg.get("knockdowns", {}).get("mma_follow_up", {}).get("ground_strike_bonus_after_knockdown", 0.15)
    )
    defender_state["knockdown_followup_bonus"] = fu_bonus
    return None


def check_finish_conditions(
    canonical_ids: list[str],
    actors: dict[str, dict[str, Any]],
    model_cfg: dict[str, Any] | None = None,
    ruleset_cfg: dict[str, Any] | None = None,
) -> tuple[str | None, str | None]:
    """Check regional damage thresholds, knockdown rules, ring-out falls, and submission stages in canonical fighter order."""
    m_cfg = model_cfg if model_cfg is not None else load_model_v2()
    reg_limits = m_cfg.get("regional_damage_limits", {})
    head_lim = float(reg_limits.get("head", 11.5))
    body_lim = float(reg_limits.get("body", 12.0))
    leg_lim = float(reg_limits.get("leg", 12.5))
    sub_stage_lim = int(m_cfg.get("simulation", {}).get("finish_thresholds", {}).get("submission_stage", 3))
    kd_rules = (ruleset_cfg or {}).get("knockdown_rules", {})
    per_round_lim = kd_rules.get("per_round_limit")
    per_fight_lim = kd_rules.get("per_fight_limit")

    for fid in canonical_ids:
        opp_id = next(i for i in canonical_ids if i != fid)
        opp_st = actors[opp_id]
        opp_dmg = opp_st["damage"]
        if opp_st.get("fell_from_edge"):
            return fid, "Fall (ring-out)"
        if opp_st.get("failed_standing_count"):
            return fid, "KO (failed standing count)"
        if per_round_lim is not None and int(opp_st.get("knockdowns_round", 0)) >= int(per_round_lim):
            return fid, f"TKO ({int(per_round_lim)}-knockdown rule in round)"
        if per_fight_lim is not None and int(opp_st.get("knockdowns_total", 0)) >= int(per_fight_lim):
            return fid, f"TKO ({int(per_fight_lim)}-knockdown rule in fight)"
        if float(opp_dmg["head"]) >= head_lim:
            return fid, "KO/TKO (head damage accumulation)"
        if float(opp_dmg["body"]) >= body_lim:
            return fid, "TKO (body/liver attrition)"
        if float(opp_dmg["leg"]) >= leg_lim:
            return fid, "TKO (leg kicks / compromised support)"
        if int(actors[fid].get("submission_stage", 0)) >= sub_stage_lim:
            return fid, "Submission (stage 3 lock completion)"
    return None, None


def evaluate_decision_winner(
    canonical_ids: list[str],
    actors: dict[str, dict[str, Any]],
    model_cfg: dict[str, Any] | None = None,
) -> tuple[str, str]:
    """Evaluate decision winner when clock expires."""
    m_cfg = model_cfg if model_cfg is not None else load_model_v2()
    dw = m_cfg.get("simulation", {}).get("decision_weights", {})
    w_head = float(dw.get("head", 1.15))
    w_body = float(dw.get("body", 1.05))
    w_leg = float(dw.get("leg", 1.0))
    w_ctrl = float(dw.get("control_mark", 1.5))

    scores: dict[str, float] = {}
    for fid in canonical_ids:
        opp_id = next(i for i in canonical_ids if i != fid)
        opp_d = actors[opp_id]["damage"]
        total_dmg_dealt = float(opp_d["head"]) * w_head + float(opp_d["body"]) * w_body + float(opp_d["leg"]) * w_leg
        scores[fid] = total_dmg_dealt + w_ctrl * float(actors[fid]["control_marks"])
    winner_id = max(canonical_ids, key=lambda i: (scores[i], i))
    return winner_id, "Decision (clock expired; card-derived damage + control)"
