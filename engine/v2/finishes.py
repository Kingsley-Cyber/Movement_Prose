"""Finish condition checks, flash knockdowns, standing counts, and per-round decision scoring (§7.14) for BLOCK Simulator v2."""

from __future__ import annotations

import random
from typing import Any

from .data import KIND_ESCAPE, KIND_FEINT, KIND_MOVEMENT, load_model_v2
from .defense import contest_roll


def resolve_standing_count_or_knockdown(
    defender_state: dict[str, Any],
    ruleset_cfg: dict[str, Any] | None = None,
    model_cfg: dict[str, Any] | None = None,
    rng: random.Random | None = None,
    damage_limit_scale: float = 1.0,
) -> dict[str, Any] | None:
    """Apply knockdown counters and resolve standing count or MMA ground follow-up hook (§7.14, §8.5)."""
    m_cfg = model_cfg if model_cfg is not None else load_model_v2()
    defender_state["knockdowns_round"] = int(defender_state.get("knockdowns_round", 0)) + 1
    defender_state["knockdowns_total"] = int(defender_state.get("knockdowns_total", 0)) + 1
    defender_state["knockdowns"] = int(defender_state["knockdowns_total"])

    r_cfg = ruleset_cfg or {}
    on_kd = str(r_cfg.get("ground", {}).get("on_knockdown", "fight_continues"))
    if on_kd == "standing_count":
        sc_cfg = m_cfg.get("knockdowns", {}).get("standing_count", {})
        rec_base = float(sc_cfg.get("recover_base", 0.8))
        rec_per_hd = float(sc_cfg.get("recover_per_head_damage", -0.05))
        head_dmg = float(defender_state.get("damage", {}).get("head", 0.0)) / max(1.0, float(damage_limit_scale))
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


def check_and_resolve_flash_knockdown(
    dmg_info: dict[str, Any],
    landing_quality: str,
    scorer_state: dict[str, Any],
    target_state: dict[str, Any],
    ruleset_cfg: dict[str, Any] | None = None,
    model_cfg: dict[str, Any] | None = None,
    rng: random.Random | None = None,
    damage_limit_scale: float = 1.0,
) -> tuple[bool, dict[str, Any] | None, bool]:
    """Roll for a flash knockdown and stun on head impacts above threshold_head_damage (§7.14)."""
    m_cfg = model_cfg if model_cfg is not None else load_model_v2()
    kd_cfg = m_cfg.get("knockdowns", {})
    fk_cfg = kd_cfg.get("flash_knockdown", {})
    req_types = set(fk_cfg.get("requires_damage_type", ["impact"]))
    req_regions = set(fk_cfg.get("requires_region", ["head"]))
    req_results = set(fk_cfg.get("results", ["clean", "flush", "counter_hit"]))

    if (
        float(dmg_info.get("final_damage", 0.0)) <= 0.0
        or str(dmg_info.get("damage_type", "")) not in req_types
        or str(dmg_info.get("target_region", "")) not in req_regions
        or landing_quality not in req_results
    ):
        return False, None, False

    ch_cfg = fk_cfg.get("chance", {})
    thresh = float(ch_cfg.get("threshold_head_damage", 4.0))
    head_dmg = float(target_state.get("damage", {}).get("head", 0.0)) / max(1.0, float(damage_limit_scale))
    if head_dmg <= thresh:
        return False, None, False

    per_pt = float(ch_cfg.get("per_point_over", 0.04))
    flush_b = float(ch_cfg.get("flush_bonus", 0.08))
    cnt_b = float(ch_cfg.get("counter_hit_bonus", 0.06))
    cap = float(ch_cfg.get("cap", 0.45))

    p_kd = per_pt * (head_dmg - thresh)
    if landing_quality == "flush":
        p_kd += flush_b
    elif landing_quality == "counter_hit":
        p_kd += cnt_b
    p_kd = min(cap, max(0.0, p_kd))
    if p_kd <= 0.0:
        return False, None, False

    kd_hit, _, _ = contest_roll(p_kd, band_name="knockdown_chance", rng=rng, model_cfg=m_cfg)
    if not kd_hit:
        return False, None, False

    stun_ex = int(kd_cfg.get("stun", {}).get("exchanges", 2))
    target_state["stun_exchanges"] = max(int(target_state.get("stun_exchanges", 0)), stun_ex)
    target_state["balance"] = "off_base"
    standing_count = resolve_standing_count_or_knockdown(
        target_state, ruleset_cfg=ruleset_cfg, model_cfg=m_cfg, rng=rng, damage_limit_scale=damage_limit_scale
    )
    fm_kd = float(m_cfg.get("fight_momentum", {}).get("per_knockdown", 0.4))
    scorer_state["fight_momentum"] = float(scorer_state.get("fight_momentum", 0.0)) + fm_kd
    target_state["fight_momentum"] = float(target_state.get("fight_momentum", 0.0)) - fm_kd
    return True, standing_count, True


def check_finish_conditions(
    canonical_ids: list[str],
    actors: dict[str, dict[str, Any]],
    model_cfg: dict[str, Any] | None = None,
    ruleset_cfg: dict[str, Any] | None = None,
    damage_limit_scale: float = 1.0,
) -> tuple[str | None, str | None]:
    """Check regional damage thresholds, knockdown rules, ring-out falls, and submission stages in canonical fighter order."""
    m_cfg = model_cfg if model_cfg is not None else load_model_v2()
    reg_limits = m_cfg.get("regional_damage_limits", {})
    head_lim = float(reg_limits.get("head", 11.5)) * float(damage_limit_scale)
    body_lim = float(reg_limits.get("body", 12.0)) * float(damage_limit_scale)
    leg_lim = float(reg_limits.get("leg", 12.5)) * float(damage_limit_scale)
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


def compute_decision_scores(
    canonical_ids: list[str],
    actors: dict[str, dict[str, Any]],
    exchanges: list[dict[str, Any]] | None = None,
    ruleset_cfg: dict[str, Any] | None = None,
    model_cfg: dict[str, Any] | None = None,
    tech_v2_map: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Compute per-round and total decision scores using ruleset decision_weights (§7.14)."""
    m_cfg = model_cfg if model_cfg is not None else load_model_v2()
    sim_dw = m_cfg.get("simulation", {}).get("decision_weights", {})
    w_head = float(sim_dw.get("head", 1.15))
    w_body = float(sim_dw.get("body", 1.05))
    w_leg = float(sim_dw.get("leg", 1.0))
    w_ctrl_mark = float(sim_dw.get("control_mark", 1.5))

    rs_dw = (ruleset_cfg or {}).get(
        "decision_weights",
        {"clean_strikes": 0.4, "damage": 0.3, "control": 0.2, "aggression": 0.1},
    )
    w_clean = float(rs_dw.get("clean_strikes", 0.4))
    w_dmg = float(rs_dw.get("damage", 0.3))
    w_ctrl = float(rs_dw.get("control", 0.2))
    w_agg = float(rs_dw.get("aggression", 0.1))

    if not exchanges:
        totals: dict[str, float] = {}
        for fid in canonical_ids:
            opp_id = next(i for i in canonical_ids if i != fid)
            opp_d = actors[opp_id]["damage"]
            total_dmg_dealt = float(opp_d["head"]) * w_head + float(opp_d["body"]) * w_body + float(opp_d["leg"]) * w_leg
            totals[fid] = round(total_dmg_dealt + w_ctrl_mark * float(actors[fid].get("control_marks", 0)), 4)
        id0, id1 = canonical_ids[0], canonical_ids[1]
        rw = {
            id0: 1 if totals[id0] > totals[id1] + 1e-9 else 0,
            id1: 1 if totals[id1] > totals[id0] + 1e-9 else 0,
        }
        return {"rounds": [], "rounds_won": rw, "totals": totals}

    by_round: dict[int, list[dict[str, Any]]] = {}
    for ex in exchanges:
        r_num = int(ex.get("round", 1))
        by_round.setdefault(r_num, []).append(ex)

    round_records: list[dict[str, Any]] = []
    rounds_won = {fid: 0 for fid in canonical_ids}
    totals = {fid: 0.0 for fid in canonical_ids}
    prev_dmg = {fid: {"head": 0.0, "body": 0.0, "leg": 0.0} for fid in canonical_ids}

    for r_num in sorted(by_round.keys()):
        r_exchanges = by_round[r_num]
        clean_cnt = {fid: 0.0 for fid in canonical_ids}
        agg_cnt = {fid: 0.0 for fid in canonical_ids}
        kd_cnt = {fid: 0.0 for fid in canonical_ids}
        ctrl_sec = {fid: 0.0 for fid in canonical_ids}
        ctrl_trans = {fid: 0.0 for fid in canonical_ids}

        for ex in r_exchanges:
            att_id = str(ex["attacker_id"])
            def_id = str(ex["defender_id"])
            tid = str(ex["technique_id"])
            out = str(ex["outcome"])
            t_kind = str((tech_v2_map or {}).get(tid, {}).get("kind", "punch"))
            if t_kind not in (KIND_MOVEMENT, KIND_FEINT, KIND_ESCAPE):
                agg_cnt[att_id] += 1.0
            if out in ("clean", "flush", "counter_hit") and float(ex.get("damage", {}).get("final_damage", 0.0)) > 0.0:
                clean_cnt[att_id] += 1.0
            cf = ex.get("counter_followup")
            if cf and float(cf.get("damage", {}).get("final_damage", 0.0)) > 0.0:
                cf_actor = str(cf.get("counter_actor_id", def_id))
                if cf_actor in clean_cnt:
                    clean_cnt[cf_actor] += 1.0
            if ex.get("knockdown"):
                kd_scorer = def_id if (cf and out in ("evaded", "blocked", "jammed")) else att_id
                if kd_scorer in kd_cnt:
                    kd_cnt[kd_scorer] += 1.0
            g_rec = ex.get("grappling")
            if g_rec and g_rec.get("to_position") not in (None, "standing_neutral"):
                ctrl_trans[att_id] += 1.0
            if ex.get("grappling_position") not in (None, "standing_neutral"):
                dur_ex = max(0.0, float(ex.get("t_end", 0.0)) - float(ex.get("t_start", 0.0)))
                ctrl_sec[att_id] += 0.5 * dur_ex

        last_sc = r_exchanges[-1].get("state_changes", {})
        last_att = str(r_exchanges[-1]["attacker_id"])
        last_def = str(r_exchanges[-1]["defender_id"])
        end_dmg = {
            last_att: dict(last_sc.get("attacker_damage", actors[last_att]["damage"])),
            last_def: dict(last_sc.get("defender_damage", actors[last_def]["damage"])),
        }

        r_scores: dict[str, float] = {}
        for fid in canonical_ids:
            opp_id = next(i for i in canonical_ids if i != fid)
            d_head = max(0.0, float(end_dmg[opp_id]["head"]) - float(prev_dmg[opp_id]["head"]))
            d_body = max(0.0, float(end_dmg[opp_id]["body"]) - float(prev_dmg[opp_id]["body"]))
            d_leg = max(0.0, float(end_dmg[opp_id]["leg"]) - float(prev_dmg[opp_id]["leg"]))
            dmg_score = w_head * d_head + w_body * d_body + w_leg * d_leg + 2.0 * kd_cnt[fid]
            ctrl_score = ctrl_sec[fid] + w_ctrl_mark * ctrl_trans[fid]
            r_val = (
                w_clean * clean_cnt[fid]
                + w_dmg * dmg_score
                + w_ctrl * ctrl_score
                + w_agg * (0.5 * agg_cnt[fid])
            )
            r_scores[fid] = round(r_val, 4)
            totals[fid] = round(totals[fid] + r_val, 4)

        prev_dmg = end_dmg
        id0, id1 = canonical_ids[0], canonical_ids[1]
        r_winner: str | None = None
        if r_scores[id0] > r_scores[id1] + 1e-9:
            rounds_won[id0] += 1
            r_winner = id0
        elif r_scores[id1] > r_scores[id0] + 1e-9:
            rounds_won[id1] += 1
            r_winner = id1
        round_records.append({"round": r_num, "scores": r_scores, "winner_id": r_winner})

    return {
        "rounds": round_records,
        "rounds_won": rounds_won,
        "totals": totals,
    }


def evaluate_decision_winner(
    canonical_ids: list[str],
    actors: dict[str, dict[str, Any]],
    model_cfg: dict[str, Any] | None = None,
    exchanges: list[dict[str, Any]] | None = None,
    ruleset_cfg: dict[str, Any] | None = None,
    rng: random.Random | None = None,
    tech_v2_map: dict[str, dict[str, Any]] | None = None,
) -> tuple[str, str]:
    """Evaluate decision winner when clock expires (§7.14: rounds won -> total score -> seeded coin in canonical order)."""
    dec_info = compute_decision_scores(
        canonical_ids,
        actors,
        exchanges=exchanges,
        ruleset_cfg=ruleset_cfg,
        model_cfg=model_cfg,
        tech_v2_map=tech_v2_map,
    )
    id0, id1 = canonical_ids[0], canonical_ids[1]
    rw0, rw1 = int(dec_info["rounds_won"][id0]), int(dec_info["rounds_won"][id1])
    tot0, tot1 = float(dec_info["totals"][id0]), float(dec_info["totals"][id1])

    tiebreak_used = False
    if rw0 != rw1:
        winner_id = id0 if rw0 > rw1 else id1
    elif abs(tot0 - tot1) > 1e-9:
        winner_id = id0 if tot0 > tot1 else id1
    else:
        tiebreak_used = True
        coin = rng.random() if rng is not None else 0.0
        winner_id = id0 if coin < 0.5 else id1

    dec_info["tiebreak"] = tiebreak_used
    for fid in canonical_ids:
        actors[fid]["decision_score_total"] = dec_info["totals"][fid]
    actors[id0]["_last_decision_info"] = dec_info
    return winner_id, "Decision (clock expired; card-derived damage + control)"

