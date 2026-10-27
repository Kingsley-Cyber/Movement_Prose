"""Finish condition checks and decision scoring for BLOCK Simulator v2."""

from __future__ import annotations

from typing import Any

from .data import load_model_v2


def check_finish_conditions(
    canonical_ids: list[str],
    actors: dict[str, dict[str, Any]],
    model_cfg: dict[str, Any] | None = None,
) -> tuple[str | None, str | None]:
    """Check regional damage thresholds and submission stages in canonical fighter order."""
    m_cfg = model_cfg if model_cfg is not None else load_model_v2()
    reg_limits = m_cfg.get("regional_damage_limits", {})
    head_lim = float(reg_limits.get("head", 11.5))
    body_lim = float(reg_limits.get("body", 12.0))
    leg_lim = float(reg_limits.get("leg", 12.5))
    sub_stage_lim = int(m_cfg.get("simulation", {}).get("finish_thresholds", {}).get("submission_stage", 3))

    for fid in canonical_ids:
        opp_id = next(i for i in canonical_ids if i != fid)
        opp_dmg = actors[opp_id]["damage"]
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
