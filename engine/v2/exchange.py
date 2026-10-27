"""Card-derived damage formula and exchange-by-exchange fight simulator for BLOCK Simulator v2."""

from __future__ import annotations

import copy
import math
import random
from typing import Any

from ..ontology import Knowledge
from .availability import available_v2
from .cards import compute_school_depth_multiplier, load_card_v2
from .data import (
    ARENA_PRESETS,
    FPS,
    KICK_IDS,
    LANDING_QUALITY_MULT,
    MOVE_BASE_STATS,
    get_attack_profile,
    load_model_v2,
    load_option_behaviors,
    load_techniques_v2,
    validate_schema_cached,
)
from .defense import select_kick_defense, select_native_defense
from .finishes import check_finish_conditions, evaluate_decision_winner
from .grappling import update_grappling_position
from .kicking import unroll_kick_anatomy
from .readiness import compute_readiness_profile
from .selection import build_slot_plans
from .state import compute_posture_state
from .vertical import normalize_vertical_mode


def compute_card_derived_damage(
    k: Knowledge,
    attacker_card: dict[str, Any],
    defender_card: dict[str, Any],
    tid: str,
    landing_quality: str,
    attacker_state: dict[str, Any],
    defender_state: dict[str, Any],
    in_active_slot: bool = True,
    opt_behaviors: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Compute qualitative Card-Derived Damage using additive attacker modifiers from data/option_behaviors.json."""
    model_cfg = load_model_v2(k.root)
    d_cfg = model_cfg.get("damage", {})
    dc = model_cfg.get("legacy", {}).get("damage_config", {})
    move_fallback = {"base": 1.0, "type": "impact", "lane": "head_straight"}

    stats = MOVE_BASE_STATS.get(tid, move_fallback)
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

    beh = opt_behaviors if opt_behaviors is not None else load_option_behaviors(k.root)
    dims = attacker_card["dimensions"]
    def_opts = dc.get("default_options", {})
    mentality = str(dims.get("mentality") or def_opts.get("mentality", ""))
    stance = str(dims.get("stance") or def_opts.get("stance", ""))
    target_opt = str(dims.get("target") or def_opts.get("target", ""))
    kicking_opt = str(dims.get("kicking") or def_opts.get("kicking", ""))
    hands_opt = dims.get("hands")
    def_opt = dims.get("defense")
    tie_opt = dims.get("tie")

    tech = k.techniques.get(tid)
    if tech is None:
        t_v2 = getattr(k, "techniques_v2", {}).get(tid, {})
        tech = t_v2 if t_v2.get("status") != "existing" else {}
    target_region = str(tech.get("target_region", "head"))
    split_kick = dc.get("karate_split_kick", {})
    if tid == dc.get("single_leg_id"):
        target_region = "leg"
    elif (
        tid == split_kick.get("technique")
        and kicking_opt == split_kick.get("kicking_option")
        and int(attacker_state.get("slot_Cursor", 0)) % 2 == 1
    ):
        target_region = str(split_kick.get("region", "head"))
    elif target_region not in ("head", "body", "leg"):
        target_region = "head" if tid in dc.get("non_standard_head_techniques", []) else "body"

    attack_lane = str(stats.get("lane", "head_straight"))

    men_prof = get_attack_profile(mentality, beh)
    st_prof = get_attack_profile(stance, beh)
    kick_prof = get_attack_profile(kicking_opt, beh)
    tar_prof = get_attack_profile(target_opt, beh)
    hands_prof = get_attack_profile(hands_opt, beh)
    def_prof = get_attack_profile(def_opt, beh)
    tie_prof = get_attack_profile(tie_opt, beh)

    delta_mentality = float(men_prof.get("power_delta", 0.0))
    if landing_quality == "counter_hit":
        delta_mentality += (
            float(men_prof.get("counter_power_delta", 0.0))
            + float(hands_prof.get("counter_power_delta", 0.0))
            + float(def_prof.get("counter_power_delta", 0.0))
        )

    delta_stance = float(st_prof.get("power_delta", 0.0))
    crouch_cfg = dc.get("crouch_bonus", {})
    if stance == crouch_cfg.get("option") and tid in crouch_cfg.get("techniques", []):
        delta_stance += float(crouch_cfg.get("delta", 0.06))
    switch_cfg = dc.get("switch_bonus", {})
    if stance == switch_cfg.get("option") and switch_cfg.get("setup") in attacker_state.get("setups", []):
        delta_stance += float(switch_cfg.get("delta", 0.08))

    delta_kicking = 0.0
    if tid in KICK_IDS:
        kick_fav_lanes = set(kick_prof.get("favored_lanes", []))
        if attack_lane in kick_fav_lanes or tid in dc.get("kick_power_techniques", []):
            delta_kicking = float(kick_prof.get("power_delta", 0.0))

    delta_target = 0.0
    tar_fav_lanes = set(tar_prof.get("favored_lanes", []))
    matched_target = attack_lane in tar_fav_lanes
    if not matched_target:
        for rule in dc.get("target_power_matches", []):
            if target_opt in rule.get("options", []):
                if target_region in rule.get("regions", []) or tid in rule.get("techniques", []):
                    matched_target = True
                    break
    if matched_target:
        delta_target = float(tar_prof.get("power_delta", 0.0))

    tie_lanes = set(dc.get("tie_power_lanes", ["clinch", "entry", "single_support"]))
    delta_other = float(hands_prof.get("power_delta", 0.0)) + (
        float(tie_prof.get("power_delta", 0.0)) if attack_lane in tie_lanes else 0.0
    )

    slot_depth = compute_school_depth_multiplier(attacker_card, k)
    off_slot_pen = float(d_cfg.get("off_slot_penalty", -0.15))
    delta_slot = (slot_depth - 1.0) if in_active_slot else off_slot_pen

    att_fatigue = float(attacker_state.get("fatigue", 0.0))
    att_leg_dmg = float(attacker_state.get("damage", {}).get("leg", 0.0))
    fat_wear = abs(float(d_cfg.get("fatigue_wear_per_point", -0.012)))
    leg_wear_kick = abs(float(d_cfg.get("leg_wear_kick_per_point", -0.03)))
    leg_wear_other = abs(float(d_cfg.get("leg_wear_other_per_point", -0.015)))
    delta_wear = -fat_wear * att_fatigue - (leg_wear_kick * att_leg_dmg if tid in KICK_IDS else leg_wear_other * att_leg_dmg)

    att_lo, att_hi = d_cfg.get("attacker_multiplier_clamp", [0.75, 1.75])
    m_attacker = max(
        float(att_lo),
        min(
            float(att_hi),
            1.0 + delta_mentality + delta_stance + delta_kicking + delta_target + delta_other + delta_slot + delta_wear,
        ),
    )

    m_landing = LANDING_QUALITY_MULT.get(landing_quality, 1.0)
    wall_mult = float(d_cfg.get("wall_landing_multiplier", 1.12))
    if defender_state.get("wall_proximity") == "near" and m_landing > 0:
        m_landing *= wall_mult

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

    g_intercept = float(d_cfg.get("guard_mitigation_intercept", 1.14))
    g_per_pt = float(d_cfg.get("guard_mitigation_per_coverage_point", 0.06))
    m_guard = g_intercept - g_per_pt * cov

    def_opt_dmg_rules = beh.get(def_opt_id, {}).get("damage_rules") if def_opt_id else None
    if def_opt_dmg_rules:
        if landing_quality == "blocked" and "blocked_landing_multiplier" in def_opt_dmg_rules:
            m_landing = float(def_opt_dmg_rules["blocked_landing_multiplier"])
        elif target_region == "head" and "head_guard_factor" in def_opt_dmg_rules:
            m_guard *= float(def_opt_dmg_rules["head_guard_factor"])

    existing_reg_dmg = float(defender_state.get("damage", {}).get(target_region, 0.0))
    comp_per_pt = float(d_cfg.get("compounding_per_damage_point", 0.045))
    def_min = float(d_cfg.get("defender_multiplier_min", 0.60))
    m_wear = 1.0 + comp_per_pt * existing_reg_dmg
    m_defender = max(def_min, m_guard * m_wear)

    final_damage = round(base * m_attacker * m_landing * m_defender, 3)

    recoil_leg_damage = 0.0
    if landing_quality == "checked" and tid in dc.get("check_recoil_techniques", []):
        recoil_frac = float(d_cfg.get("check_recoil_fraction", 0.65))
        recoil_leg_damage = round(base * recoil_frac * m_attacker, 3)

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


def _eval_kick_defense_bonus(
    def_kicking: str | None,
    def_option: str | None,
    wall_near: bool,
    tiers: list[dict[str, Any]],
) -> float:
    for tier in tiers:
        if tier.get("default"):
            return float(tier["bonus"])
        if "when_all" in tier:
            ok = True
            for clause in tier["when_all"]:
                if "kicking" in clause and def_kicking != clause["kicking"]:
                    ok = False
                if "defense" in clause and def_option != clause["defense"]:
                    ok = False
            if ok:
                return float(tier["bonus"])
        if "when_any" in tier:
            for clause in tier["when_any"]:
                ok = True
                if "kicking" in clause and def_kicking != clause["kicking"]:
                    ok = False
                if "defense" in clause and def_option != clause["defense"]:
                    ok = False
                if "wall_near" in clause and wall_near != bool(clause["wall_near"]):
                    ok = False
                if ok:
                    return float(tier["bonus"])
    return 0.08


def simulate_fight_v2(
    a: Any,
    b: Any,
    ruleset: str = "mma",
    duration_s: float = 60.0,
    seed: int = 42,
    arena: str = "cage",
    vertical_mode: str = "grounded",
    knowledge: Knowledge | None = None,
) -> dict[str, Any]:
    """Run a clock-driven, card-authentic v2 fight simulation between fighter A and fighter B.
    Canonical fighter-ID sorting guarantees order invariance: simulate_fight_v2(A, B, seed)
    and simulate_fight_v2(B, A, seed) produce the exact same winner and exchanges.
    """
    k = knowledge or Knowledge()
    card_a, card_b = load_card_v2(k, a), load_card_v2(k, b)
    if card_a["fighter_id"] == card_b["fighter_id"]:
        raise ValueError("two distinct fighter IDs are required")

    vertical_mode = normalize_vertical_mode(vertical_mode)

    settings = {
        "duration_s": float(duration_s),
        "arena": arena,
        "vertical_mode": vertical_mode,
        "ruleset": ruleset,
        "seed": int(seed),
        "director_winner": None,
        "initiative_override": None,
    }
    validate_schema_cached(settings, k.root / "schemas" / "fight_settings.schema.json")

    opt_behaviors = load_option_behaviors(k.root)
    model_cfg = load_model_v2(k.root)
    tempo_cfg = model_cfg.get("tempo_rules", {})
    sim_cfg = model_cfg.get("simulation", {})
    dmg_cfg = model_cfg.get("damage", {})
    kd_cfg = model_cfg.get("kick_defense", {})
    leg = model_cfg.get("legacy", {})
    sc = leg.get("simulation_config", {})
    init_mentality_map = leg.get("initiative", {}).get("mentality_term", {})
    kd_tiers = leg.get("kick_defense_bonus_tiers", {}).get("tiers", [])
    control_ids = set(leg.get("damage_routing", {}).get("control_ids", []))
    move_fallback = {"base": 1.0, "type": "impact", "setup_f": 4, "exec_f": 8, "hold_f": 2, "rec_f": 8, "lane": "head_straight"}
    nonlane_default = float(model_cfg.get("readiness", {}).get("nonlane_readiness_default", 3.0))

    fatigue_by_tempo = tempo_cfg.get("fatigue_by_tempo", {"1": 0.22, "2": 0.28, "3": 0.34, "4": 0.39, "5": 0.44})
    tech_v2_map = load_techniques_v2(k.root)

    cards = {card_a["fighter_id"]: card_a, card_b["fighter_id"]: card_b}
    canonical_ids = sorted(cards.keys())
    rng = random.Random(seed)

    arena_cfg = ARENA_PRESETS.get(arena, ARENA_PRESETS["cage"])
    half_w = float(arena_cfg["half_width_m"])

    slot_plans = {fid: build_slot_plans(k, cards[fid], ruleset) for fid in canonical_ids}
    start_xs = sim_cfg.get("start_x_positions", [-0.8, 0.8])

    actors: dict[str, dict[str, Any]] = {}
    for fid, x0 in zip(canonical_ids, start_xs):
        c = cards[fid]
        orient = "orthodox" if c["orientation"] == "switching" else c["orientation"]
        actors[fid] = {
            "fighter_id": fid,
            "name": c["name"],
            "position": [float(x0), 0.0],
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
    max_frames = int(duration_s * FPS)
    range_band = "kick" if ruleset == "mma" else "punch"
    exchanges: list[dict[str, Any]] = []
    finish_reason: str | None = None
    winner_id: str | None = None
    last_attacker_id: str | None = None
    last_recovery_drag: float = 0.0

    init_base = float(tempo_cfg.get("initiative_base", 3.0))
    init_per_pt = float(tempo_cfg.get("initiative_per_point", 0.30))
    init_fat_drag = float(sim_cfg.get("initiative_fatigue_drag", -0.08))
    init_leg_drag = float(sim_cfg.get("initiative_leg_drag", -0.10))
    init_noise = float(sim_cfg.get("initiative_noise", 0.85))
    clinch_exit_prob = float(sim_cfg.get("clinch_exit_probability", 0.42))
    entry_wall_pen = abs(float(sim_cfg.get("entry_wall_distance_penalty", -0.65)))
    entry_leg_pen = abs(float(sim_cfg.get("entry_leg_distance_penalty", -0.12)))
    entry_log_off = float(sim_cfg.get("entry_logistic_offset", 0.35))
    entry_lo, entry_hi = sim_cfg.get("entry_probability_clamp", [0.18, 0.82])
    failed_entry_drift = float(sim_cfg.get("failed_entry_wall_drift_m", 0.28))
    pull_out_outfighter = float(sim_cfg.get("pull_out_probability_outfighter", 0.72))
    pull_out_default = float(sim_cfg.get("pull_out_probability_default", 0.58))
    pull_out_wall_pen = abs(float(sim_cfg.get("pull_out_wall_penalty", -0.20)))
    feint_cap = float(sim_cfg.get("feint_probability_cap", 0.55))
    base_att_skill_const = float(sim_cfg.get("base_attack_skill", 3.30))
    kr_shot_pen = abs(float(sim_cfg.get("kick_range_shot_penalty", -0.75)))
    kr_punch_pen = abs(float(sim_cfg.get("kick_range_punch_penalty", -0.55)))
    hit_lo, hit_hi = sim_cfg.get("hit_probability_clamp", [0.10, 0.85])
    flush_frac = float(sim_cfg.get("flush_band_fraction", 0.28))
    clean_frac = float(sim_cfg.get("clean_band_fraction", 0.76))
    cnt_min_rec = int(sim_cfg.get("counter_min_recovery_frames", 6))
    cnt_read_bonus = float(sim_cfg.get("counter_read_bonus_per_repeat", 0.07))
    cnt_read_cap = int(sim_cfg.get("counter_read_repeats_cap", 3))
    cnt_rec_bonus = float(sim_cfg.get("counter_recovery_bonus_per_frame_over_7", 0.03))
    cnt_guard_res = float(sim_cfg.get("counter_guard_resist_per_point", 0.05))
    cnt_fat_pen = float(sim_cfg.get("counter_fatigue_penalty_per_point", 0.03))
    cnt_lo, cnt_hi = sim_cfg.get("counter_probability_clamp", [0.10, 0.55])
    cnt_hit_share = float(sim_cfg.get("counter_hit_share", 0.62))
    rec_pen_default = float(sim_cfg.get("recovery_penalty_default", 0.4))
    rec_pen_fail_mult = float(sim_cfg.get("recovery_penalty_failed_multiplier", 1.25))
    rec_pen_land_mult = float(sim_cfg.get("recovery_penalty_landed_multiplier", 0.60))
    leg_comp_base = float(sim_cfg.get("leg_compromise_threshold", 4.5))
    pressure_drift = float(sim_cfg.get("pressure_wall_drift_m", 0.42))
    outfighter_reset = float(sim_cfg.get("outfighter_reset_factor", 0.55))

    tg_cfg = sim_cfg.get("tempo_gap_frames", {})
    tg_base = int(tg_cfg.get("base", 36))
    tg_per_pt = int(tg_cfg.get("per_tempo_point", 4))
    tg_min = int(tg_cfg.get("min", 6))

    rd_cfg = sim_cfg.get("recovery_drag", {})
    rd_base = float(rd_cfg.get("base", 1.45))
    rd_per_f = float(rd_cfg.get("per_recovery_frame", 0.08))
    rd_fail_extra = float(rd_cfg.get("failed_attack_extra", 0.65))
    rd_fail_outcomes = set(rd_cfg.get("failed_outcomes", ["evaded", "blocked", "checked", "caught"]))

    ck_cfg = sim_cfg.get("caught_kick_sweep", {})
    ck_base = float(ck_cfg.get("base", 0.62))
    ck_lo, ck_hi = ck_cfg.get("clamp", [0.18, 0.68])
    ck_fat_pt = float(ck_cfg.get("fatigue_per_point", 0.04))
    ck_scram_gte = float(ck_cfg.get("scramble_if_resistance_gte", 0.12))

    kick_min_roll = float(kd_cfg.get("kick_path_min_roll", 0.10))
    kick_excluded = set(kd_cfg.get("kick_path_excluded", []))

    tie_dmg_frac = float(dmg_cfg.get("tie_damage_fraction", 0.25))
    tie_fat_frac = float(dmg_cfg.get("tie_fatigue_fraction", 0.65))
    sub_dmg_frac = float(dmg_cfg.get("submission_damage_fraction", 0.30))
    sub_fat_frac = float(dmg_cfg.get("submission_fatigue_fraction", 0.55))
    stam_fat_frac = float(dmg_cfg.get("stamina_drain_fatigue_fraction", 0.55))

    excl_from_seq = sc.get("excluded_from_sequence")
    checked_kicks_filter = set(sc.get("checked_kicks_filter", []))
    kick_blocked_shots = set(sc.get("kick_range_blocked_shots", []))
    punch_range_kicks = set(sc.get("punch_range_kicks", []))
    punch_clinch_ties = set(sc.get("punch_range_clinch_ties", []))
    punch_clinch_moves = set(sc.get("punch_range_clinch_moves", []))
    ground_top_ctrl = str(sc.get("ground_top_control", ""))
    ground_bot_sub = str(sc.get("ground_bottom_sub", ""))
    ground_esc = str(sc.get("ground_escape", ""))
    ground_top_strikes = list(sc.get("ground_top_strikes", []))
    ground_fb_chain = list(sc.get("ground_fallback_chain", []))
    kick_fallbacks_list = list(sc.get("kick_range_fallbacks", []))
    haymaker_pen = sc.get("haymaker_penalty", {})
    pressure_ments = set(sc.get("pressure_mentalities", []))
    outboxer_ment = sc.get("outboxer_mentality")
    outfight_def = sc.get("outfight_defense")
    caught_dump_prio = list(sc.get("caught_kick_dump_priority", []))
    counter_cands_map = sc.get("counter_candidates_by_range", {})
    clinch_grips = set(sc.get("clinch_grips", []))

    while clock_frames < max_frames:
        lead_matchup = (
            "closed_stance"
            if actors[canonical_ids[0]]["orientation"] == actors[canonical_ids[1]]["orientation"]
            else "open_stance"
        )

        # 1. Decide who initiates this exchange in canonical fighter-ID order
        scores_init: dict[str, float] = {}
        for fid in canonical_ids:
            c = cards[fid]
            st = actors[fid]
            mentality = c["dimensions"].get("mentality")
            base_tempo = init_base + init_per_pt * (float(c.get("tempo", 3)) - 3.0)
            m_entry = init_mentality_map.get(mentality, init_mentality_map.get("all_other_mentalities", {}))
            if "only_when" in m_entry:
                counter_wait = float(m_entry.get("delta", 0.0)) if last_attacker_id in (None, fid) else 0.0
            else:
                counter_wait = float(m_entry.get("delta", 0.0))
            recovery_cooldown = -last_recovery_drag if fid == last_attacker_id else 0.0
            fatigue_drag = init_fat_drag * float(st["fatigue"])
            leg_drag = init_leg_drag * float(st["damage"]["leg"])
            scores_init[fid] = (
                base_tempo + counter_wait + recovery_cooldown + fatigue_drag + leg_drag + rng.uniform(-init_noise, init_noise)
            )

        attacker_id = max(canonical_ids, key=lambda i: (scores_init[i], i))
        defender_id = next(i for i in canonical_ids if i != attacker_id)
        att_card, def_card = cards[attacker_id], cards[defender_id]
        att_state, def_state = actors[attacker_id], actors[defender_id]

        # 2. Select active slot plan, contest range step (one band per exchange), & select technique
        plans = slot_plans[attacker_id]
        active_plan = plans[int(att_state["active_slot_idx"]) % len(plans)]
        att_state["active_slot_id"] = active_plan["slot_id"]
        seq: list[str] = list(active_plan["sequence"])
        att_avail = available_v2(k, att_card, ruleset)
        def_avail = available_v2(k, def_card, ruleset)

        att_dims = att_card["dimensions"]
        def_dims = def_card["dimensions"]
        att_mentality = att_dims.get("mentality")
        def_mentality = def_dims.get("mentality")
        def_option = def_dims.get("defense")
        att_stance = att_dims.get("stance")

        standing_ladder = ["kick", "punch", "clinch"]
        if att_state["posture_mode"] == "ground":
            range_band = "ground"
        elif att_state["grip"] in clinch_grips:
            if str(active_plan["home_range"]) in ("kick", "punch") and def_dims.get("tie") is None:
                att_state["grip"] = def_state["grip"] = None
                att_state["grappling_position"] = def_state["grappling_position"] = "standing_neutral"
                range_band = "punch"
            elif str(active_plan["home_range"]) in ("kick", "punch") and rng.random() < clinch_exit_prob:
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
                entry_score = sum(
                    float(get_attack_profile(att_dims.get(d), opt_behaviors).get("entry_delta", 0.0))
                    for d in ("mentality", "stance", "defense", "hands", "tie", "kicking", "target")
                )
                entry_score += float(tempo_cfg.get("entry_per_point", 0.08)) * (float(att_card.get("tempo", 3)) - 3.0)

                def_wall_near = def_state.get("wall_proximity") == "near"
                dist_score = 0.0
                for d in ("mentality", "stance", "defense", "hands", "tie", "kicking", "target"):
                    oid = def_dims.get(d)
                    ometa = opt_behaviors.get(oid, {}) if oid else {}
                    dc_cond = ometa.get("distance_control_condition", {})
                    if dc_cond.get("unless") == "wall_near" and def_wall_near:
                        continue
                    dist_score += float(ometa.get("attack_profile", {}).get("distance_control_delta", 0.0))

                if def_wall_near:
                    dist_score -= entry_wall_pen
                dist_score -= entry_leg_pen * float(def_state["damage"]["leg"])

                step_prob = max(
                    float(entry_lo),
                    min(float(entry_hi), 1.0 / (1.0 + math.exp(-(entry_score - dist_score + entry_log_off)))),
                )
                if rng.random() < step_prob:
                    range_band = standing_ladder[min(len(standing_ladder) - 1, cur_idx + 1)]
                else:
                    if arena_cfg["has_walls"]:
                        direction = 1.0 if def_state["position"][0] >= 0 else -1.0
                        def_state["position"][0] = round(
                            max(-half_w, min(half_w, def_state["position"][0] + failed_entry_drift * direction)), 3
                        )
                        if half_w - abs(def_state["position"][0]) <= float(arena_cfg["wall_near_m"]):
                            def_state["wall_proximity"] = "near"
            elif des_idx < cur_idx:
                att_men_meta = opt_behaviors.get(att_mentality, {}) if att_mentality else {}
                att_def_meta = opt_behaviors.get(att_dims.get("defense"), {}) if att_dims.get("defense") else {}
                pull_prob = float(
                    att_men_meta.get("pull_out_probability")
                    or att_def_meta.get("pull_out_probability")
                    or (
                        pull_out_outfighter
                        if (att_mentality == outboxer_ment or att_dims.get("defense") == outfight_def)
                        else pull_out_default
                    )
                )
                if att_state.get("wall_proximity") == "near":
                    pull_prob -= pull_out_wall_pen
                if rng.random() < pull_prob:
                    range_band = standing_ladder[max(0, cur_idx - 1)]

        filtered_seq = [
            m
            for m in seq
            if m != excl_from_seq and not (att_state["kick_checks_suffered"] >= 2 and m in checked_kicks_filter)
        ] or seq

        range_matching_seq = []
        for m in filtered_seq:
            m_info = k.techniques.get(m)
            if m_info is None:
                t_v2 = tech_v2_map.get(m)
                if t_v2 and t_v2.get("status") != "existing":
                    m_info = t_v2
            if m_info is None:
                continue
            req_rng = m_info["required_range"]
            if (range_band in req_rng and not (range_band == "kick" and m in kick_blocked_shots)) or (
                range_band == "punch"
                and (
                    "close" in req_rng
                    or m in punch_range_kicks
                    or (att_dims.get("tie") in punch_clinch_ties and m in punch_clinch_moves)
                )
            ):
                range_matching_seq.append(m)
        active_seq = range_matching_seq or filtered_seq

        cursor = int(att_state["slot_Cursor"])
        tid = active_seq[cursor % len(active_seq)]
        att_state["slot_Cursor"] = cursor + 1

        if range_band == "ground":
            if att_state["grip"] == "top" and ground_top_ctrl in att_avail:
                tid = ground_top_ctrl
            elif att_state["grip"] == "bottom" and ground_bot_sub in att_avail:
                tid = ground_bot_sub
            elif ground_esc in att_avail:
                tid = ground_esc
            elif att_state["grip"] == "top":
                top_strikes = [m for m in ground_top_strikes if m in att_avail]
                tid = top_strikes[cursor % len(top_strikes)] if top_strikes else ground_fb_chain[0]
            else:
                tid = ground_fb_chain[-1]
                for fb_m in ground_fb_chain[:-1]:
                    if fb_m in att_avail:
                        tid = fb_m
                        break
        elif range_band == "kick" and tid not in KICK_IDS:
            kick_fallbacks = [m for m in kick_fallbacks_list if m in att_avail]
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

        feint_prob = min(
            feint_cap,
            sum(
                float(get_attack_profile(att_dims.get(d), opt_behaviors).get("feint_setup_rate", 0.0))
                for d in ("mentality", "stance", "hands", "target")
            ),
        )
        feinted_this_exchange = feint_prob > 0.0 and rng.random() < feint_prob
        if feinted_this_exchange:
            def_state["attention"]["feinted"] = True

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
            model_cfg=model_cfg,
        )
        def_state["posture"] = def_posture_before
        def_state["readiness_profile"] = def_readiness

        m_stats = MOVE_BASE_STATS.get(tid, move_fallback)
        attack_lane = str(m_stats.get("lane", "head_straight"))
        lane_readiness = float(def_readiness.get(attack_lane, nonlane_default))

        # 4. Calculate Contested Hit Probability
        base_att_skill = base_att_skill_const + sum(
            float(get_attack_profile(att_dims.get(d), opt_behaviors).get("accuracy_delta", 0.0))
            for d in ("mentality", "stance", "hands", "target", "kicking", "tie")
        )
        if tid == haymaker_pen.get("technique"):
            base_att_skill += float(haymaker_pen.get("delta", -0.22))
        if range_band == "kick" and tid not in KICK_IDS:
            base_att_skill -= kr_shot_pen if tid in kick_blocked_shots else kr_punch_pen

        logit_hit = base_att_skill - lane_readiness
        hit_prob = round(max(float(hit_lo), min(float(hit_hi), 1.0 / (1.0 + math.exp(-logit_hit)))), 3)

        seen_map = def_state["read_memory"]["seen_counts"]
        seen_map[tid] = int(seen_map.get(tid, 0)) + 1

        # 5. Roll Outcome & Native Posture Defensive Response
        kick_detail = unroll_kick_anatomy(tid, att_card, str(att_state["orientation"]))
        defense_used = None
        counter_triggered = False

        roll = rng.random()
        def_wall = str(def_state.get("wall_proximity", "far"))
        def_wall_near = def_wall == "near"
        kick_def_bonus = _eval_kick_defense_bonus(def_dims.get("kicking"), def_option, def_wall_near, kd_tiers)

        if tid in KICK_IDS and tid not in kick_excluded and roll > max(kick_min_roll, hit_prob - kick_def_bonus):
            defense_used, outcome = select_kick_defense(
                def_card,
                tid,
                range_band,
                lane_readiness=lane_readiness,
                attacker_card=att_card,
                rng=rng,
                opt_behaviors=opt_behaviors,
                wall_proximity=def_wall,
            )
        elif roll > hit_prob:
            defense_used, outcome = select_native_defense(def_card, tid, range_band, def_avail, wall_proximity=def_wall)
        else:
            if roll < hit_prob * flush_frac and (def_state["attention"]["feinted"] or def_posture_before["balance"] != "stable"):
                outcome = "flush"
            elif roll < hit_prob * clean_frac:
                outcome = "clean"
            else:
                outcome = "partial"

        if feinted_this_exchange:
            def_state["attention"]["feinted"] = False

        # Contested Counter-Attack Check
        att_rec_f = int(m_stats.get("rec_f", 6))
        if outcome in ("evaded", "blocked", "jammed") and att_rec_f >= cnt_min_rec:
            base_counter = 0.0
            for d in ("mentality", "defense", "hands", "stance"):
                oid = def_dims.get(d)
                ometa = opt_behaviors.get(oid, {}) if oid else {}
                ct_cond = ometa.get("counter_tendency_condition")
                if ct_cond:
                    if "ranges" in ct_cond and range_band not in ct_cond["ranges"]:
                        continue
                    if ct_cond.get("unless") == "wall_near" and def_wall_near:
                        continue
                base_counter += float(ometa.get("attack_profile", {}).get("counter_tendency", 0.0))

            read_bonus = cnt_read_bonus * min(cnt_read_cap, consecutive_repeats)
            low_tempo_bonus = float(tempo_cfg.get("low_tempo_counter_per_point", 0.05)) * max(0, 3 - int(def_card.get("tempo", 3)))
            rec_window_bonus = cnt_rec_bonus * max(0, att_rec_f - 7)
            att_hands_id = att_dims.get("hands")
            att_head_cov = (
                k.options[att_hands_id]["mma_adaptation"]["ratings"].get("head_coverage", 3)
                if att_hands_id and att_hands_id in k.options
                else 3
            )
            att_guard_resist = cnt_guard_res * (att_head_cov - 3)
            counter_prob = max(
                float(cnt_lo),
                min(
                    float(cnt_hi),
                    base_counter + read_bonus + low_tempo_bonus + rec_window_bonus - att_guard_resist - cnt_fat_pen * float(def_state["fatigue"]),
                ),
            )
            if rng.random() < counter_prob:
                counter_triggered = True

        # 6. Apply Card-Derived Damage & Posture/Recovery Updates
        dmg_info = compute_card_derived_damage(
            k, att_card, def_card, tid, outcome, att_state, def_state, in_active_slot=True, opt_behaviors=opt_behaviors
        )

        if dmg_info["final_damage"] > 0:
            reg = str(dmg_info["target_region"])
            if tid in control_ids:
                def_state["damage"][reg] = round(def_state["damage"][reg] + tie_dmg_frac * dmg_info["final_damage"], 3)
                def_state["fatigue"] = round(def_state["fatigue"] + tie_fat_frac * dmg_info["final_damage"], 2)
            elif dmg_info["damage_type"] == "submission":
                def_state["damage"][reg] = round(def_state["damage"][reg] + sub_dmg_frac * dmg_info["final_damage"], 3)
                def_state["fatigue"] = round(def_state["fatigue"] + sub_fat_frac * dmg_info["final_damage"], 2)
            else:
                def_state["damage"][reg] = round(def_state["damage"][reg] + dmg_info["final_damage"], 3)
                if dmg_info["damage_type"] == "stamina_drain":
                    def_state["fatigue"] = round(def_state["fatigue"] + stam_fat_frac * dmg_info["final_damage"], 2)
                att_target_opt = att_dims.get("target")
                extra_body_fat = float(
                    opt_behaviors.get(att_target_opt, {}).get("on_body_damage_extra_fatigue_fraction", 0.0)
                ) if att_target_opt else 0.0
                if reg == "body" and extra_body_fat > 0.0:
                    def_state["fatigue"] = round(def_state["fatigue"] + extra_body_fat * dmg_info["final_damage"], 2)
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

        t_v2_rec = tech_v2_map.get(tid, {}).get(
            "recovery_exposure",
            {
                "window_type": "short_retract",
                "exposed_lanes": ["head_straight"],
                "readiness_penalty": rec_pen_default,
            },
        )
        att_state["recovery_window"] = {
            "window_type": t_v2_rec["window_type"],
            "last_technique_id": tid,
            "exposed_lanes": list(t_v2_rec["exposed_lanes"]),
            "readiness_penalty": float(t_v2_rec["readiness_penalty"])
            * (rec_pen_fail_mult if outcome in ("evaded", "miss", "checked", "caught") else rec_pen_land_mult),
        }
        def_state["recovery_window"] = {
            "window_type": "none",
            "last_technique_id": defense_used,
            "exposed_lanes": [],
            "readiness_penalty": 0.0,
        }

        leg_comp_thresh = leg_comp_base + float(
            get_attack_profile(att_dims.get("target"), opt_behaviors).get("leg_compromise_threshold_delta", 0.0)
        )
        forced_stance_switch = False
        if def_state["damage"]["leg"] >= leg_comp_thresh and not def_state.get("leg_compromised"):
            def_state["leg_compromised"] = True
            def_state["orientation"] = "southpaw" if def_state["orientation"] == "orthodox" else "orthodox"
            forced_stance_switch = True

        grappling_pos = update_grappling_position(att_state, def_state, tid, outcome, att_card)
        if att_mentality in pressure_ments and arena_cfg["has_walls"]:
            direction = 1.0 if def_state["position"][0] >= 0 else -1.0
            def_state["position"][0] = round(
                max(-half_w, min(half_w, def_state["position"][0] + pressure_drift * direction)), 3
            )
            if half_w - abs(def_state["position"][0]) <= float(arena_cfg["wall_near_m"]):
                def_state["wall_proximity"] = "near"
        elif (def_mentality == outboxer_ment or def_option == outfight_def) and outcome in ("evaded", "blocked"):
            def_state["position"][0] = round(def_state["position"][0] * outfighter_reset, 3)
            def_state["wall_proximity"] = "far"

        exchange_frames = int(m_stats["setup_f"]) + int(m_stats["exec_f"]) + int(m_stats["hold_f"]) + int(m_stats["rec_f"])
        tempo_gap_frames = max(tg_min, int(tg_base - tg_per_pt * max(att_card.get("tempo", 3), def_card.get("tempo", 3))))
        t_start = round(clock_frames / float(FPS), 2)
        clock_frames += exchange_frames + tempo_gap_frames
        t_end = round(clock_frames / float(FPS), 2)
        att_tempo_val = int(att_card.get("tempo", 3))
        fatigue_step = float(fatigue_by_tempo.get(str(att_tempo_val), 0.34))
        att_state["fatigue"] = round(att_state["fatigue"] + fatigue_step, 2)
        last_attacker_id = attacker_id
        last_recovery_drag = rd_base + rd_per_f * float(m_stats["rec_f"]) + (rd_fail_extra if outcome in rd_fail_outcomes else 0.0)

        counter_followup_event = None
        if outcome == "caught":
            att_state["kick_checks_suffered"] += 1
            att_tie = att_dims.get("tie")
            sweep_resist = float(get_attack_profile(att_tie, opt_behaviors).get("sweep_resistance", 0.0)) + float(
                get_attack_profile(att_stance, opt_behaviors).get("sweep_resistance", 0.0)
            )
            sweep_prob = max(float(ck_lo), min(float(ck_hi), ck_base - sweep_resist - ck_fat_pt * float(def_state["fatigue"])))
            if rng.random() < sweep_prob:
                dump_tid = caught_dump_prio[-1]
                for cand_dump in caught_dump_prio[:-1]:
                    if cand_dump in def_avail:
                        dump_tid = cand_dump
                        break
                dump_dmg = compute_card_derived_damage(
                    k, def_card, att_card, dump_tid, "clean", def_state, att_state, in_active_slot=True, opt_behaviors=opt_behaviors
                )
                reg_c = str(dump_dmg["target_region"])
                att_state["damage"][reg_c] = round(att_state["damage"][reg_c] + dump_dmg["final_damage"], 3)
                def_state["contact_marks"] += 1
                def_state["control_marks"] += 1
                if sweep_resist >= ck_scram_gte:
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
            c_list = counter_cands_map.get(range_band, counter_cands_map.get("default", []))
            c_candidates = [m for m in c_list if m in def_avail]
            if c_candidates:
                c_tid = c_candidates[0]
                c_qual = "counter_hit" if rng.random() < cnt_hit_share else "partial"
                c_dmg = compute_card_derived_damage(
                    k, def_card, att_card, c_tid, c_qual, def_state, att_state, in_active_slot=True, opt_behaviors=opt_behaviors
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
        winner_id, finish_reason = check_finish_conditions(canonical_ids, actors, model_cfg)
        if winner_id:
            break

    if not winner_id:
        winner_id, finish_reason = evaluate_decision_winner(canonical_ids, actors, model_cfg)

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
        "time_s": round(clock_frames / float(FPS), 2),
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
        "duration_actual_s": round(clock_frames / float(FPS), 2),
        "winner_id": winner_id,
        "winner_name": cards[winner_id]["name"],
        "finish_reason": finish_reason,
        "exchange_count": len(exchanges),
        "final_state_v2": final_state_v2,
        "actors_final": actors,
        "slot_plans": slot_plans,
        "exchanges": exchanges,
    }
