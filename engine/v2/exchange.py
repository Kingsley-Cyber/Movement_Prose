"""Card-derived damage formula and exchange-by-exchange fight simulator for BLOCK Simulator v2."""

from __future__ import annotations

import copy
import math
import random
from typing import Any

from ..ontology import Knowledge
from .availability import (
    available_v2,
    evaluate_conditional_abilities,
    slot_defense_pool_v2,
    slot_pool_v2,
)
from .cards import compute_school_depth_multiplier, load_card_v2
from .data import (
    ARENA_PRESETS,
    FPS,
    KICK_IDS,
    KIND_ESCAPE,
    KIND_FEINT,
    KIND_MOVEMENT,
    LANDING_QUALITY_MULT,
    MOVE_BASE_STATS,
    TECH_CAUGHT_KICK_DUMP,
    TECH_CLINCH_BREAK,
    TECH_FEINT,
    TECH_KICK_CATCH,
    TECH_PUMMEL,
    TECH_RETREAT,
    TECH_SANDA_SWEEP,
    TECH_SHOVE,
    TECH_STEP,
    TECH_SWITCH_STEP,
    get_attack_profile,
    load_capabilities_v2,
    load_model_v2,
    load_option_behaviors,
    load_positions_v2,
    load_rulesets_v2,
    load_techniques_v2,
    validate_schema_cached,
)
from .defense import (
    compute_kick_defense_window,
    contest_roll,
    resolve_contested_defense,
    select_kick_defense,
    select_native_defense,
)
from .finishes import (
    check_finish_conditions,
    evaluate_decision_winner,
    resolve_standing_count_or_knockdown,
)
from .geometry import (
    apply_movement_displacement,
    band_from_distance,
    clamp_or_fall_at_boundary,
    compute_distance_m,
    compute_wall_and_corner,
    get_arena_preset,
    update_facing,
)
from .grappling import (
    accrue_control_time,
    get_positions_map,
    resolve_grappling_exchange_v2,
    set_pair_position,
    update_grappling_position,
)
from .kicking import unroll_kick_anatomy
from .laterality import (
    apply_side_damage_and_cuts,
    compute_dominance_deltas,
    compute_lead_foot_matchup,
    compute_line_accuracy_modifier,
    get_anatomical_sides,
    resolve_actor_laterality,
    resolve_lead_foot_outside_contest,
    resolve_target_anatomical_side,
)
from .readiness import compute_readiness_profile
from .selection import (
    build_slot_plans,
    evaluate_slot_switch,
    get_initial_slot_index,
    score_and_select_technique_v2,
    select_counter_v2,
    update_slot_stalls,
)
from .state import apply_technique_effects, compute_posture_state, tick_active_effects
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
    equipment: dict[str, Any] | None = None,
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
    t_v2_entry = getattr(k, "techniques_v2", {}).get(tid) or load_techniques_v2(k.root).get(tid, {})
    if tech is None:
        tech = t_v2_entry if t_v2_entry.get("status") != "existing" else {}
    tech_kind = str(t_v2_entry.get("kind") or tech.get("kind") or "")
    target_region = str(tech.get("target_region") or t_v2_entry.get("target_region") or "head")
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
        if attack_lane in kick_fav_lanes or tid in dc.get("kick_power_techniques", []) or tech_kind in ("kick", "knee"):
            delta_kicking = float(kick_prof.get("power_delta", 0.0))

    delta_target = 0.0
    tar_fav_lanes = set(tar_prof.get("favored_lanes", []))
    matched_target = attack_lane in tar_fav_lanes
    if not matched_target:
        for rule in dc.get("target_power_matches", []):
            if target_opt in rule.get("options", []):
                if (
                    target_region in rule.get("regions", [])
                    or tid in rule.get("techniques", [])
                    or (rule.get("techniques") and tech_kind in ("knee", "grip"))
                ):
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

    delta_laterality, _ = compute_dominance_deltas(attacker_card, attacker_state, t_v2_entry, model_cfg)

    dealt_scale = float(d_cfg.get("option_damage_dealt_scale", 0.05))
    delta_dealt = dealt_scale * sum(
        float(beh.get(dims.get(d) or "", {}).get("damage_dealt_multiplier", 1.0)) - 1.0
        for d in ("mentality", "stance", "hands", "target", "kicking", "tie", "defense")
        if dims.get(d)
    )

    att_lo, att_hi = d_cfg.get("attacker_multiplier_clamp", [0.75, 1.75])
    m_attacker = max(
        float(att_lo),
        min(
            float(att_hi),
            1.0
            + delta_mentality
            + delta_stance
            + delta_kicking
            + delta_target
            + delta_other
            + delta_slot
            + delta_wear
            + delta_laterality
            + delta_dealt,
        ),
    )

    m_landing = LANDING_QUALITY_MULT.get(landing_quality, 1.0)
    wall_mult = float(d_cfg.get("wall_landing_multiplier", 1.12))
    if defender_state.get("wall_proximity") == "near" and m_landing > 0:
        m_landing *= wall_mult

    def_dims = defender_card["dimensions"]
    def_hands_id = def_dims.get("hands")
    def_opt_id = def_dims.get("defense")
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

    taken_scale = float(d_cfg.get("option_damage_taken_scale", 0.15))
    delta_taken = taken_scale * sum(
        float(beh.get(def_dims.get(d) or "", {}).get("damage_taken_multiplier", 1.0)) - 1.0
        for d in ("defense", "hands", "stance", "mentality")
        if def_dims.get(d)
    )

    existing_reg_dmg = float(defender_state.get("damage", {}).get(target_region, 0.0))
    comp_per_pt = float(d_cfg.get("compounding_per_damage_point", 0.045))
    def_min = float(d_cfg.get("defender_multiplier_min", 0.60))
    m_wear = 1.0 + comp_per_pt * existing_reg_dmg
    m_defender = max(def_min, (m_guard + delta_taken) * m_wear)

    eq_mult = float((equipment or {}).get("punch_damage_multiplier", 1.0)) if tech_kind == "punch" else 1.0
    throw_mult = (
        float(attacker_state.get("arena_hard_floor_throw_bonus", 1.0))
        if tech_kind in ("takedown", "sweep")
        else 1.0
    )
    final_damage = round(base * m_attacker * m_landing * m_defender * eq_mult * throw_mult, 3)

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


def simulate_fight_v2(
    a: Any,
    b: Any,
    ruleset: str = "mma",
    duration_s: float = 60.0,
    seed: int = 42,
    arena: str = "cage",
    vertical_mode: str = "grounded",
    knowledge: Knowledge | None = None,
    rounds: int | None = None,
    round_length_s: float | None = None,
    rest_s: float | None = None,
    full_fight: bool = False,
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
    ruleset_cfg = load_rulesets_v2(k.root).get("rulesets", {}).get(ruleset, {})

    if full_fight:
        num_rounds = int(rounds if rounds is not None else ruleset_cfg.get("default_rounds", 3))
        r_len_s = float(round_length_s if round_length_s is not None else ruleset_cfg.get("default_round_s", 300.0))
        r_rest_s = float(rest_s if rest_s is not None else ruleset_cfg.get("default_rest_s", 60.0))
        eff_duration_s = min(900.0, num_rounds * r_len_s)
    elif rounds is not None or round_length_s is not None:
        num_rounds = int(rounds if rounds is not None else 1)
        r_len_s = float(round_length_s if round_length_s is not None else (float(duration_s) / max(1, num_rounds)))
        r_rest_s = float(rest_s if rest_s is not None else ruleset_cfg.get("default_rest_s", 60.0))
        eff_duration_s = min(900.0, num_rounds * r_len_s)
    else:
        num_rounds = 1
        r_len_s = float(duration_s)
        r_rest_s = float(rest_s if rest_s is not None else 0.0)
        eff_duration_s = float(duration_s)

    settings: dict[str, Any] = {
        "duration_s": float(eff_duration_s),
        "arena": arena,
        "vertical_mode": vertical_mode,
        "ruleset": ruleset,
        "seed": int(seed),
        "director_winner": None,
        "initiative_override": None,
    }
    if full_fight or rounds is not None or round_length_s is not None:
        settings["rounds"] = num_rounds
        settings["round_length_s"] = r_len_s
        settings["rest_s"] = r_rest_s
    validate_schema_cached(settings, k.root / "schemas" / "fight_settings.schema.json")

    opt_behaviors = load_option_behaviors(k.root)
    model_cfg = load_model_v2(k.root)
    tempo_cfg = model_cfg.get("tempo_rules", {})
    sim_cfg = model_cfg.get("simulation", {})
    dmg_cfg = model_cfg.get("damage", {})
    kd_cfg = model_cfg.get("kick_defense", {})
    fm_cfg = model_cfg.get("fight_momentum", {})
    leg = model_cfg.get("legacy", {})
    sc = leg.get("simulation_config", {})
    init_mentality_map = leg.get("initiative", {}).get("mentality_term", {})
    control_ids = set(leg.get("damage_routing", {}).get("control_ids", []))
    move_fallback = {"base": 1.0, "type": "impact", "setup_f": 4, "exec_f": 8, "hold_f": 2, "rec_f": 8, "lane": "head_straight"}
    nonlane_default = float(model_cfg.get("readiness", {}).get("nonlane_readiness_default", 3.0))

    fatigue_by_tempo = tempo_cfg.get("fatigue_by_tempo", {"1": 0.22, "2": 0.28, "3": 0.34, "4": 0.39, "5": 0.44})
    tech_v2_map = load_techniques_v2(k.root)
    positions_data = load_positions_v2(k.root)
    positions_map = get_positions_map(positions_data)

    cards = {card_a["fighter_id"]: card_a, card_b["fighter_id"]: card_b}
    canonical_ids = sorted(cards.keys())
    rng = random.Random(seed)
    pair_position: dict[str, Any] = {
        "position_id": "standing_neutral",
        "roles": {fid: "neutral" for fid in canonical_ids},
    }
    last_sub_rec: dict[str, Any] | None = None

    arena_cfg = get_arena_preset(arena, model_cfg)
    half_w = float(arena_cfg["half_width_m"])
    arena_wall_pin_bonus = float(arena_cfg.get("wall_pin_bonus", 1.0))
    arena_corner_trap_bonus = float(arena_cfg.get("corner_trap_bonus", 1.0))
    arena_hard_floor_throw_bonus = float(arena_cfg.get("hard_floor_throw_bonus", 1.0))
    arena_restricts_wide_kicks = bool(arena_cfg.get("restricts_wide_kicks", False))

    slot_plans = {fid: build_slot_plans(k, cards[fid], ruleset) for fid in canonical_ids}
    avail_map = {fid: available_v2(k, cards[fid], ruleset) for fid in canonical_ids}
    start_xs = sim_cfg.get("start_x_positions", [-0.8, 0.8])

    actors: dict[str, dict[str, Any]] = {}
    for fid, x0 in zip(canonical_ids, start_xs):
        c = cards[fid]
        orient = "orthodox" if c["orientation"] == "switching" else c["orientation"]
        init_idx = get_initial_slot_index(slot_plans[fid])
        prox0, corner0, _ = compute_wall_and_corner([float(x0), 0.0], arena, model_cfg)
        actors[fid] = {
            "fighter_id": fid,
            "name": c["name"],
            "position": [float(x0), 0.0],
            "facing": [1.0 if x0 < 0 else -1.0, 0.0],
            "orientation": orient,
            "posture_mode": "standing",
            "balance": "stable",
            "grappling_position": "standing_neutral",
            "role": "neutral",
            "control_time_s": 0.0,
            "grip": None,
            "sub_grips": {"underhooks": 0, "wrist_control": False, "head_position": "neutral"},
            "submission_stage": 0,
            "wall_proximity": prox0,
            "in_corner": corner0,
            "arena_wall_pin_bonus": arena_wall_pin_bonus,
            "arena_hard_floor_throw_bonus": arena_hard_floor_throw_bonus,
            "damage": {"head": 0.0, "body": 0.0, "leg": 0.0},
            "damage_by_side": {
                "head_left": 0.0,
                "head_right": 0.0,
                "body_left": 0.0,
                "body_right": 0.0,
                "leg_left": 0.0,
                "leg_right": 0.0,
                "arm_left": 0.0,
                "arm_right": 0.0,
            },
            "cuts": {"left": 0, "right": 0},
            "laterality": resolve_actor_laterality(c, orient),
            "fatigue": 0.0,
            "momentum": [0.0, 0.0],
            "fight_momentum": 0.0,
            "contact_marks": 0,
            "control_marks": 0,
            "active_slot_idx": init_idx,
            "active_slot_id": slot_plans[fid][init_idx]["slot_id"],
            "slot_Cursor": 0,
            "slot_stalls": 0,
            "slot_exchanges": 0,
            "slot_switches": 0,
            "combo_state": {
                "last_tid": None,
                "last_outcome": None,
                "last_def_tid": None,
                "last_def_outcome": None,
                "chain_len": 0,
            },
            "unlocked_abilities": [],
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
            "active_effects": [],
            "knockdowns_round": 0,
            "knockdowns_total": 0,
        }

    ruleset_cfg = load_rulesets_v2(k.root).get("rulesets", {}).get(ruleset, {})
    clinch_rules = ruleset_cfg.get("clinch", {})
    ground_rules = ruleset_cfg.get("ground", {})
    equipment_rules = ruleset_cfg.get("equipment", {})
    legal_kinds_set = set(ruleset_cfg.get("legal_kinds", []))
    punch_only_ruleset = bool(legal_kinds_set and "kick" not in legal_kinds_set) or not clinch_rules.get("allowed", True)

    clock_frames = 0
    max_frames = int(eff_duration_s * FPS)
    round_frames = max(1, int(r_len_s * FPS))
    current_round = 1
    rounds_cfg = model_cfg.get("rounds", {})
    rest_fat_rec = float(rounds_cfg.get("rest_fatigue_recovery_fraction", 0.35))
    range_band = "punch" if punch_only_ruleset else "kick"
    clinch_exchanges = 0
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
    init_mom_weight = float(fm_cfg.get("initiative_weight", 0.5))
    acc_mom_weight = float(fm_cfg.get("accuracy_weight", 0.05))
    fm_landed = float(fm_cfg.get("per_clean_or_flush_landed", 0.15))
    fm_taken = float(fm_cfg.get("per_clean_or_flush_taken", -0.15))
    fm_decay = float(fm_cfg.get("decay_per_exchange", 0.2))
    fm_lo, fm_hi = fm_cfg.get("clamp", [-0.6, 0.6])

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

    kick_blocked_shots = set(sc.get("kick_range_blocked_shots", []))
    pressure_ments = set(sc.get("pressure_mentalities", []))
    outboxer_ment = sc.get("outboxer_mentality")
    outfight_def = sc.get("outfight_defense")
    caught_dump_prio = list(sc.get("caught_kick_dump_priority", []))
    clinch_grips = set(sc.get("clinch_grips", []))

    while clock_frames < max_frames:
        tick_active_effects(actors)
        lead_matchup = (
            "closed_stance"
            if actors[canonical_ids[0]]["orientation"] == actors[canonical_ids[1]]["orientation"]
            else "open_stance"
        )

        # 1. Decide who initiates this exchange in canonical fighter-ID order (§7.2)
        scores_init: dict[str, float] = {}
        for fid in canonical_ids:
            c = cards[fid]
            st = actors[fid]
            mentality = c["dimensions"].get("mentality")
            base_tempo = init_base + init_per_pt * (float(c.get("tempo", 3)) - 3.0)
            sel_prof = opt_behaviors.get(mentality or "", {}).get("selection_profile")
            if sel_prof is not None:
                counter_wait = float(sel_prof.get("initiative_delta", 0.0))
                if "initiative_delta_when_waiting" in sel_prof and last_attacker_id in (None, fid):
                    counter_wait += float(sel_prof.get("initiative_delta_when_waiting", 0.0))
            else:
                m_entry = init_mentality_map.get(mentality, init_mentality_map.get("all_other_mentalities", {}))
                if "only_when" in m_entry:
                    counter_wait = float(m_entry.get("delta", 0.0)) if last_attacker_id in (None, fid) else 0.0
                else:
                    counter_wait = float(m_entry.get("delta", 0.0))
            mom_term = init_mom_weight * float(st.get("fight_momentum", 0.0))
            recovery_cooldown = -last_recovery_drag if fid == last_attacker_id else 0.0
            fatigue_drag = init_fat_drag * float(st["fatigue"])
            leg_drag = init_leg_drag * float(st["damage"]["leg"])
            scores_init[fid] = (
                base_tempo
                + counter_wait
                + mom_term
                + recovery_cooldown
                + fatigue_drag
                + leg_drag
                + rng.uniform(-init_noise, init_noise)
            )

        attacker_id = max(canonical_ids, key=lambda i: (scores_init[i], i))
        defender_id = next(i for i in canonical_ids if i != attacker_id)
        att_card, def_card = cards[attacker_id], cards[defender_id]
        att_state, def_state = actors[attacker_id], actors[defender_id]
        initiative_scores = {fid: round(scores_init[fid], 4) for fid in canonical_ids}

        # Unlock conditional abilities from real state before slot evaluation (§7.5)
        for fid in canonical_ids:
            opp_fid = next(i for i in canonical_ids if i != fid)
            newly_unlocked = evaluate_conditional_abilities(cards[fid], actors[fid], actors[opp_fid], range_band)
            if newly_unlocked:
                un_list = tuple(actors[fid].get("unlocked_abilities", ()))
                slot_plans[fid] = build_slot_plans(k, cards[fid], ruleset, un_list)
                avail_map[fid] = available_v2(k, cards[fid], ruleset, un_list)

        # 2. Select active slot plan, contest range step (one band per exchange)
        plans = slot_plans[attacker_id]
        active_plan = plans[int(att_state["active_slot_idx"]) % len(plans)]
        att_state["active_slot_id"] = active_plan["slot_id"]
        def_avail = avail_map[defender_id]

        att_dims = att_card["dimensions"]
        def_dims = def_card["dimensions"]
        att_mentality = att_dims.get("mentality")
        def_mentality = def_dims.get("mentality")
        def_option = def_dims.get("defense")
        att_stance = att_dims.get("stance")

        standing_ladder = ["kick", "punch", "clinch"]
        ref_break_after = clinch_rules.get("referee_break_after_exchanges")
        pre_clinch_break_steps: list[dict[str, str]] = []
        if att_state["posture_mode"] == "ground":
            if not ground_rules.get("allowed", True):
                set_pair_position(pair_position, "standing_neutral", attacker_id, "neutral", defender_id, actors, positions_map)
                range_band = "punch" if punch_only_ruleset else "kick"
            else:
                range_band = "ground"
        elif att_state["grip"] in clinch_grips or range_band == "clinch":
            should_break = False
            if not clinch_rules.get("allowed", True) or (
                ref_break_after is not None and clinch_exchanges >= int(ref_break_after)
            ):
                should_break = True
            elif str(active_plan["home_range"]) in ("kick", "punch") and def_dims.get("tie") is None:
                should_break = True
            elif str(active_plan["home_range"]) in ("kick", "punch") and contest_roll(
                clinch_exit_prob, band_name=TECH_CLINCH_BREAK, rng=rng, model_cfg=model_cfg
            )[0]:
                should_break = True
            if should_break:
                prev_p = str(pair_position.get("position_id", "standing_neutral"))
                if prev_p != "standing_neutral":
                    if prev_p == "double_underhooks":
                        pre_clinch_break_steps.append(
                            {"from_position": "double_underhooks", "to_position": "over_under", "via_technique": TECH_PUMMEL}
                        )
                        prev_p = "over_under"
                    pre_clinch_break_steps.append(
                        {"from_position": prev_p, "to_position": "standing_neutral", "via_technique": TECH_CLINCH_BREAK}
                    )
                set_pair_position(pair_position, "standing_neutral", attacker_id, "neutral", defender_id, actors, positions_map)
                range_band = "punch"
                clinch_exchanges = 0
            else:
                range_band = "clinch"
        elif punch_only_ruleset:
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
                    if def_state.get("in_corner") and arena_corner_trap_bonus > 1.0:
                        entry_score += (arena_corner_trap_bonus - 1.0)
                dist_score -= entry_leg_pen * float(def_state["damage"]["leg"])

                step_prob = max(
                    float(entry_lo),
                    min(float(entry_hi), 1.0 / (1.0 + math.exp(-(entry_score - dist_score + entry_log_off)))),
                )
                if contest_roll(step_prob, band_name="range_step_in", rng=rng, model_cfg=model_cfg)[0]:
                    range_band = standing_ladder[min(len(standing_ladder) - 1, cur_idx + 1)]
                else:
                    if arena_cfg["has_walls"] or arena_cfg.get("has_drop_hazard"):
                        direction = 1.0 if def_state["position"][0] >= 0 else -1.0
                        raw_fx = float(def_state["position"][0]) + failed_entry_drift * direction
                        raw_fy = float(def_state["position"][1]) + (0.5 * failed_entry_drift * direction if arena_cfg.get("has_corners") else 0.0)
                        clamp_or_fall_at_boundary(def_state, raw_fx, raw_fy, arena, model_cfg, rng=rng)
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
                if contest_roll(pull_prob, band_name="range_step_out", rng=rng, model_cfg=model_cfg)[0]:
                    range_band = standing_ladder[max(0, cur_idx - 1)]

        ex_range = range_band

        # Lead-foot-outside contest in open stance (§7.4.5)
        lfo_winner_id = resolve_lead_foot_outside_contest(
            canonical_ids,
            cards,
            actors,
            lead_matchup,
            range_band,
            rng,
            opt_behaviors=opt_behaviors,
            model_cfg=model_cfg,
        )

        # Feint setup contest before readiness & selection
        feint_prob = min(
            feint_cap,
            sum(
                float(get_attack_profile(att_dims.get(d), opt_behaviors).get("feint_setup_rate", 0.0))
                for d in ("mentality", "stance", "hands", "target")
            ),
        )
        feinted_this_exchange = (
            feint_prob > 0.0 and contest_roll(feint_prob, band_name=TECH_FEINT, rng=rng, model_cfg=model_cfg)[0]
        )
        if feinted_this_exchange:
            def_state["attention"]["feinted"] = True

        # 3. Compute Defender's Pre-Attack Posture & Readiness, then Select Technique via §7.5 Scorer
        def_posture_before = compute_posture_state(def_card, def_state, opt_behaviors)
        def_state["posture"] = def_posture_before
        pre_readiness = compute_readiness_profile(
            k,
            def_card,
            def_state,
            att_card,
            att_state,
            range_band,
            lead_matchup,
            incoming_tid=None,
            opt_behaviors=opt_behaviors,
            model_cfg=model_cfg,
        )

        tid, selection_rec, matched_combo = score_and_select_technique_v2(
            k,
            att_card,
            def_card,
            active_plan,
            att_state,
            pre_readiness,
            range_band,
            ruleset,
            rng,
            model_cfg,
            opt_behaviors,
            tech_v2_map,
        )

        # Update defender's read_memory before computing incoming_tid readiness
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
        def_state["readiness_profile"] = def_readiness

        m_stats = MOVE_BASE_STATS.get(tid, move_fallback)
        attack_lane = str(m_stats.get("lane", "head_straight"))
        lane_readiness = float(def_readiness.get(attack_lane, nonlane_default))

        # 4. Calculate Contested Hit Probability (§7.8 & §7.4)
        t_v2_entry = tech_v2_map.get(tid, {})
        t_kind = str(t_v2_entry.get("kind", "punch"))
        acc_base = float(t_v2_entry.get("accuracy_base_recommended", t_v2_entry.get("accuracy_base", 0.0)))
        combo_acc_bonus = float(matched_combo.get("follow_up_accuracy_bonus", 0.0)) if matched_combo else 0.0
        mom_acc_bonus = acc_mom_weight * float(att_state.get("fight_momentum", 0.0))
        _, lat_acc_delta = compute_dominance_deltas(att_card, att_state, t_v2_entry, model_cfg)
        line_acc_mod = compute_line_accuracy_modifier(lead_matchup, t_v2_entry, lfo_winner_id, attacker_id, model_cfg)

        stop_hit_acc_bonus = (
            0.08
            if t_v2_entry.get("stop_hit") and def_mentality in pressure_ments
            else 0.0
        )
        wide_kick_pen = (
            0.12
            if arena_restricts_wide_kicks and t_v2_entry.get("line") in ("lead_round_kick", "rear_round_kick", "spinning")
            else 0.0
        )
        base_att_skill = (
            base_att_skill_const
            + sum(
                float(get_attack_profile(att_dims.get(d), opt_behaviors).get("accuracy_delta", 0.0))
                for d in ("mentality", "stance", "hands", "target", "kicking", "tie")
            )
            + acc_base
            + lat_acc_delta
            + line_acc_mod
            + combo_acc_bonus
            + mom_acc_bonus
            + stop_hit_acc_bonus
            - wide_kick_pen
        )
        if range_band == "kick" and tid not in KICK_IDS and t_kind not in ("kick", "knee", KIND_MOVEMENT, KIND_FEINT):
            base_att_skill -= (
                kr_shot_pen
                if (tid in kick_blocked_shots or t_kind in ("takedown", "sweep"))
                else kr_punch_pen
            )

        logit_hit = base_att_skill - lane_readiness
        hit_prob = round(max(float(hit_lo), min(float(hit_hi), 1.0 / (1.0 + math.exp(-logit_hit)))), 3)

        seen_map = def_state["read_memory"]["seen_counts"]
        seen_map[tid] = int(seen_map.get(tid, 0)) + 1

        # 5. Roll Outcome & Contested Defensive Response (§7.6)
        kick_detail = unroll_kick_anatomy(tid, att_card, str(att_state["orientation"]))
        defense_used: str | None = None
        defense_rec: dict[str, Any] | None = None
        counter_triggered = False

        _, roll, hit_p_eff = contest_roll(hit_prob, band_name="hit", rng=rng, model_cfg=model_cfg)
        hit_rec = {
            "offense": round(base_att_skill, 4),
            "defense": round(lane_readiness, 4),
            "p_land": round(hit_p_eff, 4),
            "roll": round(roll, 4),
        }

        def_wall = str(def_state.get("wall_proximity", "far"))
        def_wall_near = def_wall == "near"
        kick_def_bonus = compute_kick_defense_window(
            def_card, wall_proximity=def_wall, opt_behaviors=opt_behaviors, model_cfg=model_cfg
        )

        def_plans = slot_plans[defender_id]
        def_active_plan = def_plans[int(def_state["active_slot_idx"]) % len(def_plans)]
        def_reset_defenses = (
            set(def_active_plan["reset_defenses"])
            if def_active_plan.get("goal") == "reset_to_home_range"
            else None
        )
        def_unlocked = tuple(def_state.get("unlocked_abilities", ()))
        inc_cls = str(t_v2_entry.get("incoming_class") or "straight")

        if t_kind in (KIND_MOVEMENT, KIND_FEINT) and inc_cls == "none":
            outcome = "clean"
            if tid == TECH_FEINT:
                def_state["attention"]["feinted"] = True
                feinted_this_exchange = False
            elif tid == TECH_SWITCH_STEP:
                att_state["orientation"] = "southpaw" if att_state["orientation"] == "orthodox" else "orthodox"
                att_state["laterality"] = resolve_actor_laterality(att_card, att_state["orientation"])
                lead_matchup = compute_lead_foot_matchup(
                    actors[canonical_ids[0]]["orientation"], actors[canonical_ids[1]]["orientation"]
                )
        elif tid in KICK_IDS and tid not in kick_excluded and roll > max(kick_min_roll, hit_p_eff - kick_def_bonus):
            defense_used, outcome, def_p_succ, def_roll, def_grant_cap, inc_cls = resolve_contested_defense(
                def_card,
                att_card,
                tid,
                offense_score=base_att_skill,
                lane_readiness=lane_readiness,
                avail_def=def_avail,
                wall_proximity=def_wall,
                reset_slot_defenses=def_reset_defenses,
                rng=rng,
                opt_behaviors=opt_behaviors,
                model_cfg=model_cfg,
                unlocked_abilities=def_unlocked,
            )
            defense_rec = {
                "technique": defense_used,
                "granting_capability": def_grant_cap,
                "p_success": round(def_p_succ, 4),
                "roll": round(def_roll, 4),
            }
        elif roll > hit_p_eff:
            defense_used, outcome, def_p_succ, def_roll, def_grant_cap, inc_cls = resolve_contested_defense(
                def_card,
                att_card,
                tid,
                offense_score=base_att_skill,
                lane_readiness=lane_readiness,
                avail_def=def_avail,
                wall_proximity=def_wall,
                reset_slot_defenses=def_reset_defenses,
                rng=rng,
                opt_behaviors=opt_behaviors,
                model_cfg=model_cfg,
                unlocked_abilities=def_unlocked,
            )
            defense_rec = {
                "technique": defense_used,
                "granting_capability": def_grant_cap,
                "p_success": round(def_p_succ, 4),
                "roll": round(def_roll, 4),
            }
        else:
            if roll < hit_p_eff * flush_frac and (def_state["attention"]["feinted"] or def_posture_before["balance"] != "stable"):
                outcome = "flush"
            elif roll < hit_p_eff * clean_frac:
                outcome = "clean"
            else:
                outcome = "partial"

        if feinted_this_exchange:
            def_state["attention"]["feinted"] = False

        # Contested Counter-Attack Check (§7.9)
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
            if contest_roll(counter_prob, band_name="counter", rng=rng, model_cfg=model_cfg)[0]:
                counter_triggered = True

        # 6. Apply Card-Derived Damage, Side Damage (§7.4.7–7.4.8), & Posture/Recovery Updates
        dmg_info = compute_card_derived_damage(
            k,
            att_card,
            def_card,
            tid,
            outcome,
            att_state,
            def_state,
            in_active_slot=True,
            opt_behaviors=opt_behaviors,
            equipment=equipment_rules,
        )

        att_orient_now = str(att_state["orientation"])
        def_orient_now = str(def_state["orientation"])
        limb_side, target_side = resolve_target_anatomical_side(att_orient_now, def_orient_now, t_v2_entry)
        laterality_rec = {
            "attacker_side": str(t_v2_entry.get("side") or "none"),
            "limb_side": limb_side,
            "target_side": target_side,
            "stance_relation": lead_matchup,
            "lead_foot_outside_winner": lfo_winner_id,
        }

        if dmg_info["final_damage"] > 0:
            reg = str(dmg_info["target_region"])
            t_routing = t_v2_entry.get("damage_routing")
            if tid in control_ids or t_routing == "control":
                def_state["damage"][reg] = round(def_state["damage"][reg] + tie_dmg_frac * dmg_info["final_damage"], 3)
                def_state["fatigue"] = round(def_state["fatigue"] + tie_fat_frac * dmg_info["final_damage"], 2)
                apply_side_damage_and_cuts(
                    def_state,
                    reg,
                    target_side,
                    dmg_info["final_damage"],
                    outcome,
                    t_v2_entry,
                    rng=rng,
                    model_cfg=model_cfg,
                    damage_share=tie_dmg_frac,
                    equipment=equipment_rules,
                )
            elif dmg_info["damage_type"] == "submission" or t_routing == "submission":
                def_state["damage"][reg] = round(def_state["damage"][reg] + sub_dmg_frac * dmg_info["final_damage"], 3)
                def_state["fatigue"] = round(def_state["fatigue"] + sub_fat_frac * dmg_info["final_damage"], 2)
                apply_side_damage_and_cuts(
                    def_state,
                    reg,
                    target_side,
                    dmg_info["final_damage"],
                    outcome,
                    t_v2_entry,
                    rng=rng,
                    model_cfg=model_cfg,
                    damage_share=sub_dmg_frac,
                    equipment=equipment_rules,
                )
            else:
                def_state["damage"][reg] = round(def_state["damage"][reg] + dmg_info["final_damage"], 3)
                side_res = apply_side_damage_and_cuts(
                    def_state,
                    reg,
                    target_side,
                    dmg_info["final_damage"],
                    outcome,
                    t_v2_entry,
                    rng=rng,
                    model_cfg=model_cfg,
                    damage_share=1.0,
                    equipment=equipment_rules,
                )
                body_stam_mult = float(side_res["body_stamina_mult"]) if reg == "body" else 1.0
                if dmg_info["damage_type"] == "stamina_drain":
                    def_state["fatigue"] = round(
                        def_state["fatigue"] + stam_fat_frac * body_stam_mult * dmg_info["final_damage"], 2
                    )
                att_target_opt = att_dims.get("target")
                extra_body_fat = float(
                    opt_behaviors.get(att_target_opt, {}).get("on_body_damage_extra_fatigue_fraction", 0.0)
                ) if att_target_opt else 0.0
                if reg == "body" and extra_body_fat > 0.0:
                    def_state["fatigue"] = round(
                        def_state["fatigue"] + extra_body_fat * body_stam_mult * dmg_info["final_damage"], 2
                    )
            if outcome in ("clean", "flush", "counter_hit", "partial"):
                att_state["contact_marks"] += 1

        if dmg_info["recoil_leg_damage_to_attacker"] > 0:
            recoil_val = dmg_info["recoil_leg_damage_to_attacker"]
            att_state["damage"]["leg"] = round(att_state["damage"]["leg"] + recoil_val, 3)
            recoil_leg_side = limb_side if limb_side in ("left", "right") else get_anatomical_sides(att_orient_now)[1]
            att_state["damage_by_side"][f"leg_{recoil_leg_side}"] = round(
                float(att_state["damage_by_side"].get(f"leg_{recoil_leg_side}", 0.0)) + recoil_val, 3
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

        t_v2_rec = t_v2_entry.get(
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

        per_leg_base = float(model_cfg.get("laterality", {}).get("limb_effects", {}).get("leg_compromise_per_leg", leg_comp_base))
        leg_comp_thresh = per_leg_base + float(
            get_attack_profile(att_dims.get("target"), opt_behaviors).get("leg_compromise_threshold_delta", 0.0)
        )
        def_lead_leg_side, _ = get_anatomical_sides(str(def_state["orientation"]))
        def_lead_leg_dmg = float(def_state.get("damage_by_side", {}).get(f"leg_{def_lead_leg_side}", 0.0))
        forced_stance_switch = False
        if (
            def_lead_leg_dmg >= leg_comp_thresh or def_state["damage"]["leg"] >= leg_comp_thresh
        ) and not def_state.get("leg_compromised"):
            def_state["leg_compromised"] = True
            def_state["orientation"] = "southpaw" if def_state["orientation"] == "orthodox" else "orthodox"
            def_state["laterality"] = resolve_actor_laterality(def_card, def_state["orientation"])
            forced_stance_switch = True

        grappling_pos, grappling_rec, sub_rec = resolve_grappling_exchange_v2(
            pair_position,
            attacker_id,
            defender_id,
            actors,
            cards,
            tid,
            outcome,
            defense_used=defense_used,
            rng=rng,
            opt_behaviors=opt_behaviors,
            model_cfg=model_cfg,
            positions_data=positions_data,
            tech_v2_map=tech_v2_map,
        )
        if sub_rec is not None:
            last_sub_rec = sub_rec
        if pre_clinch_break_steps:
            if grappling_rec is None:
                grappling_rec = {
                    "from_position": pre_clinch_break_steps[0]["from_position"],
                    "to_position": grappling_pos,
                    "via_technique": TECH_CLINCH_BREAK,
                    "transitions": list(pre_clinch_break_steps),
                }
            else:
                grappling_rec["transitions"] = list(pre_clinch_break_steps) + list(grappling_rec.get("transitions", []))
        if (
            active_plan.get("goal") == "reset_to_home_range"
            and att_state.get("posture_mode") == "standing"
            and outcome in ("clean", "flush", "counter_hit", "partial")
            and grappling_pos != "standing_neutral"
        ):
            prev_p = grappling_pos
            grappling_pos = set_pair_position(
                pair_position, "standing_neutral", attacker_id, "neutral", defender_id, actors, positions_map
            )
            step_list = list((grappling_rec or {}).get("transitions", []))
            if prev_p == "double_underhooks":
                step_list.append({"from_position": "double_underhooks", "to_position": "over_under", "via_technique": TECH_PUMMEL})
                prev_p = "over_under"
            step_list.append({"from_position": prev_p, "to_position": "standing_neutral", "via_technique": TECH_CLINCH_BREAK})
            grappling_rec = {
                "from_position": step_list[0]["from_position"],
                "to_position": "standing_neutral",
                "via_technique": TECH_CLINCH_BREAK,
                "transitions": step_list,
            }
        if t_kind in (KIND_MOVEMENT, KIND_FEINT) and outcome in ("clean", "flush", "counter_hit", "partial"):
            apply_movement_displacement(tid, att_state, def_state, arena, model_cfg, rng=rng)
        if defense_used and outcome == "evaded":
            apply_movement_displacement(defense_used, def_state, att_state, arena, model_cfg, rng=rng)

        if (def_mentality == outboxer_ment or def_option == outfight_def) and outcome == "evaded":
            def_state["position"][0] = round(def_state["position"][0] * outfighter_reset, 3)
            def_state["position"][1] = round(def_state["position"][1] * outfighter_reset, 3)
            def_state["wall_proximity"] = "far"
            def_state["in_corner"] = False
        elif att_mentality in pressure_ments and (arena_cfg["has_walls"] or arena_cfg.get("has_drop_hazard")):
            direction = 1.0 if def_state["position"][0] >= 0 else -1.0
            raw_drift_x = float(def_state["position"][0]) + pressure_drift * direction
            raw_drift_y = float(def_state["position"][1]) + (
                0.5 * pressure_drift * direction if arena_cfg.get("has_corners") else 0.0
            )
            clamp_or_fall_at_boundary(def_state, raw_drift_x, raw_drift_y, arena, model_cfg, rng=rng)
        elif (def_mentality == outboxer_ment or def_option == outfight_def) and outcome in ("evaded", "blocked"):
            def_state["position"][0] = round(def_state["position"][0] * outfighter_reset, 3)
            def_state["position"][1] = round(def_state["position"][1] * outfighter_reset, 3)
            def_state["wall_proximity"] = "far"
            def_state["in_corner"] = False

        setup_saved = int(matched_combo.get("setup_frames_saved", 0)) if matched_combo else 0
        eff_setup_f = max(1, int(m_stats["setup_f"]) - setup_saved)
        def_frames = 0
        if defense_used:
            def_fc = tech_v2_map.get(defense_used, {}).get("frame_costs", {})
            def_frames = int(def_fc.get("execution_frames", 0))
        exchange_frames = eff_setup_f + int(m_stats["exec_f"]) + int(m_stats["hold_f"]) + int(m_stats["rec_f"]) + def_frames

        pace_cfg = model_cfg.get("pace", {})
        p_base = int(pace_cfg.get("base_gap_frames", tg_base))
        p_per_pt = int(pace_cfg.get("per_tempo_point", tg_per_pt))
        p_min = int(pace_cfg.get("min_gap_frames", tg_min))
        p_fat_scale = float(pace_cfg.get("fatigue_gap_scale", 0.03))
        att_tempo_val = int(att_card.get("tempo", 3))
        att_patience = float(
            opt_behaviors.get(att_mentality or "", {}).get("selection_profile", {}).get("patience", 1.0)
        )
        raw_gap = max(p_min, p_base - p_per_pt * att_tempo_val) * att_patience * (1.0 + p_fat_scale * float(att_state["fatigue"]))
        tempo_gap_frames = max(p_min, int(round(raw_gap)))

        t_start = round(clock_frames / float(FPS), 2)
        clock_frames += exchange_frames + tempo_gap_frames
        t_end = round(clock_frames / float(FPS), 2)

        energy_cfg = model_cfg.get("energy", {})
        use_e_mult = bool(energy_cfg.get("use_technique_energy_mult", True))
        def_cost_frac = float(energy_cfg.get("defender_cost_fraction", 0.35))
        att_e_mult = float(t_v2_entry.get("energy_mult", 1.0)) if use_e_mult else 1.0
        fatigue_step = float(fatigue_by_tempo.get(str(att_tempo_val), 0.34)) * att_e_mult
        att_state["fatigue"] = round(att_state["fatigue"] + fatigue_step, 2)

        if defense_used:
            def_tempo_val = int(def_card.get("tempo", 3))
            def_e_mult = float(tech_v2_map.get(defense_used, {}).get("energy_mult", 0.35)) if use_e_mult else 1.0
            def_fat_step = def_cost_frac * float(fatigue_by_tempo.get(str(def_tempo_val), 0.34)) * def_e_mult
            def_state["fatigue"] = round(def_state["fatigue"] + def_fat_step, 2)
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
            prev_catch_pos = grappling_pos
            if contest_roll(sweep_prob, band_name="catch_sweep", rng=rng, model_cfg=model_cfg)[0]:
                dump_tid = caught_dump_prio[-1]
                for cand_dump in caught_dump_prio[:-1]:
                    if cand_dump in def_avail:
                        dump_tid = cand_dump
                        break
                dump_dmg = compute_card_derived_damage(
                    k,
                    def_card,
                    att_card,
                    dump_tid,
                    "clean",
                    def_state,
                    att_state,
                    in_active_slot=True,
                    opt_behaviors=opt_behaviors,
                    equipment=equipment_rules,
                )
                reg_c = str(dump_dmg["target_region"])
                att_state["damage"][reg_c] = round(att_state["damage"][reg_c] + dump_dmg["final_damage"], 3)
                dump_t_v2 = tech_v2_map.get(dump_tid, {})
                _, dump_target_side = resolve_target_anatomical_side(
                    str(def_state["orientation"]), str(att_state["orientation"]), dump_t_v2
                )
                apply_side_damage_and_cuts(
                    att_state,
                    reg_c,
                    dump_target_side,
                    dump_dmg["final_damage"],
                    "clean",
                    dump_t_v2,
                    rng=rng,
                    model_cfg=model_cfg,
                    equipment=equipment_rules,
                )
                def_state["contact_marks"] += 1
                def_state["control_marks"] += 1
                catch_steps = list((grappling_rec or {}).get("transitions", []))
                if prev_catch_pos == "standing_neutral":
                    catch_steps.append(
                        {"from_position": "standing_neutral", "to_position": "caught_single_leg", "via_technique": TECH_KICK_CATCH}
                    )
                if sweep_resist >= ck_scram_gte:
                    grappling_pos = set_pair_position(
                        pair_position, "standing_neutral", defender_id, "neutral", attacker_id, actors, positions_map
                    )
                    catch_steps.append(
                        {"from_position": "caught_single_leg", "to_position": "standing_neutral", "via_technique": TECH_CLINCH_BREAK}
                    )
                else:
                    via_dump = dump_tid if dump_tid in (TECH_SANDA_SWEEP, TECH_CAUGHT_KICK_DUMP) else TECH_CAUGHT_KICK_DUMP
                    grappling_pos = set_pair_position(
                        pair_position, "half_guard", defender_id, "top", attacker_id, actors, positions_map
                    )
                    catch_steps.append(
                        {"from_position": "caught_single_leg", "to_position": "half_guard", "via_technique": via_dump}
                    )
                grappling_rec = {
                    "from_position": catch_steps[0]["from_position"] if catch_steps else prev_catch_pos,
                    "to_position": grappling_pos,
                    "via_technique": dump_tid,
                    "contest": "sweep",
                    "transitions": catch_steps,
                }
                counter_followup_event = {
                    "counter_actor_id": defender_id,
                    "trigger": "kick_catch_dump",
                    "technique_id": dump_tid,
                    "damage": dump_dmg,
                }
            elif prev_catch_pos == "standing_neutral":
                grappling_pos = set_pair_position(
                    pair_position, "caught_single_leg", defender_id, "holder", attacker_id, actors, positions_map
                )
                catch_steps = list((grappling_rec or {}).get("transitions", []))
                catch_steps.append(
                    {"from_position": "standing_neutral", "to_position": "caught_single_leg", "via_technique": TECH_KICK_CATCH}
                )
                grappling_rec = {
                    "from_position": "standing_neutral",
                    "to_position": "caught_single_leg",
                    "via_technique": TECH_KICK_CATCH,
                    "contest": TECH_KICK_CATCH,
                    "transitions": catch_steps,
                }
        elif counter_triggered:
            att_readiness = compute_readiness_profile(
                k,
                att_card,
                att_state,
                def_card,
                def_state,
                range_band,
                lead_matchup,
                incoming_tid=None,
                opt_behaviors=opt_behaviors,
                model_cfg=model_cfg,
            )
            # Update defender slot plan so counter selection reflects any slot switch and card-wide counter repertoire
            def_active_plan = def_plans[int(def_state["active_slot_idx"]) % len(def_plans)]
            c_tid = select_counter_v2(
                k,
                def_card,
                att_card,
                def_active_plan,
                def_state,
                att_readiness,
                def_avail,
                range_band,
                ruleset,
                rng,
                model_cfg,
                opt_behaviors,
                tech_v2_map,
            )
            if c_tid:
                c_qual = "counter_hit" if rng.random() < cnt_hit_share else "partial"
                c_dmg = compute_card_derived_damage(
                    k,
                    def_card,
                    att_card,
                    c_tid,
                    c_qual,
                    def_state,
                    att_state,
                    in_active_slot=True,
                    opt_behaviors=opt_behaviors,
                    equipment=equipment_rules,
                )
                reg_c = str(c_dmg["target_region"])
                att_state["damage"][reg_c] = round(att_state["damage"][reg_c] + c_dmg["final_damage"], 3)
                c_t_v2 = tech_v2_map.get(c_tid, {})
                _, c_target_side = resolve_target_anatomical_side(
                    str(def_state["orientation"]), str(att_state["orientation"]), c_t_v2
                )
                apply_side_damage_and_cuts(
                    att_state,
                    reg_c,
                    c_target_side,
                    c_dmg["final_damage"],
                    c_qual,
                    c_t_v2,
                    rng=rng,
                    model_cfg=model_cfg,
                    equipment=equipment_rules,
                )
                def_state["contact_marks"] += 1
                counter_followup_event = {
                    "counter_actor_id": defender_id,
                    "trigger": f"{defense_used}_counter",
                    "technique_id": c_tid,
                    "damage": c_dmg,
                }

        # Apply technique on_success_effects (§7.17) and per-ruleset clinch/ground/edge rules (§8.5)
        effects_applied: list[dict[str, Any]] = []
        att_succeeded = t_kind in (KIND_MOVEMENT, KIND_FEINT) or outcome in ("clean", "flush", "counter_hit", "partial")
        if att_succeeded and t_v2_entry.get("on_success_effects"):
            att_effs, range_band = apply_technique_effects(
                tid,
                t_v2_entry.get("on_success_effects"),
                attacker_id,
                defender_id,
                actors,
                cards,
                range_band,
                standing_ladder,
                rng=rng,
            )
            effects_applied.extend(att_effs)

        if defense_used and outcome in ("evaded", "checked", "caught", "jammed"):
            def_t_v2 = tech_v2_map.get(defense_used, {})
            if def_t_v2.get("on_success_effects"):
                def_effs, range_band = apply_technique_effects(
                    defense_used,
                    def_t_v2.get("on_success_effects"),
                    defender_id,
                    attacker_id,
                    actors,
                    cards,
                    range_band,
                    standing_ladder,
                    rng=rng,
                )
                effects_applied.extend(def_effs)

        if counter_followup_event:
            cf_tid = str(counter_followup_event["technique_id"])
            cf_t_v2 = tech_v2_map.get(cf_tid, {})
            if cf_t_v2.get("on_success_effects"):
                cf_effs, range_band = apply_technique_effects(
                    cf_tid,
                    cf_t_v2.get("on_success_effects"),
                    defender_id,
                    attacker_id,
                    actors,
                    cards,
                    range_band,
                    standing_ladder,
                    rng=rng,
                )
                effects_applied.extend(cf_effs)

        # Push-back position displacement & rooftop_edge drop hazard (§7.3)
        push_steps = sum(
            int(e.get("value", 1) or 1)
            for e in effects_applied
            if e.get("effect") == "push_back" and e.get("target_id") == defender_id
        )
        if push_steps > 0:
            shove_m = float(model_cfg.get("geometry", {}).get("moves_m", {}).get(TECH_SHOVE, 0.6))
            direction = 1.0 if def_state["position"][0] >= 0 else -1.0
            raw_x = float(def_state["position"][0]) + shove_m * push_steps * direction
            if arena_cfg.get("has_drop_hazard") and abs(raw_x) > half_w:
                ef_cfg = model_cfg.get("geometry", {}).get("edge_fall", {})
                p_fall = float(ef_cfg.get("probability", 0.35))
                if def_state.get("balance") in ("off_base", "compromised"):
                    p_fall = min(0.95, p_fall * float(ef_cfg.get("off_base_multiplier", 1.5)))
                if contest_roll(p_fall, band_name="edge_fall", rng=rng, model_cfg=model_cfg)[0]:
                    def_state["fell_from_edge"] = True
                    def_state["position"][0] = round(raw_x, 3)
                else:
                    def_state["position"][0] = round(max(-half_w, min(half_w, raw_x)), 3)
                    def_state["balance"] = "off_base"
                    def_state["wall_proximity"] = "near"
            elif arena_cfg["has_walls"]:
                def_state["position"][0] = round(max(-half_w, min(half_w, raw_x)), 3)
                if half_w - abs(def_state["position"][0]) <= float(arena_cfg["wall_near_m"]):
                    def_state["wall_proximity"] = "near"
            else:
                def_state["position"][0] = round(raw_x, 3)

        # Enforce ruleset ground & clinch rules post-exchange (§8.5)
        if not ground_rules.get("allowed", True):
            is_ground_now = (
                att_state.get("posture_mode") == "ground"
                or def_state.get("posture_mode") == "ground"
                or t_v2_entry.get("result_position") == "standing_knockdown"
            )
            if is_ground_now:
                if (
                    ground_rules.get("on_sweep") == "reset_standing_with_score"
                    and outcome in ("clean", "flush", "counter_hit", "partial")
                    and t_v2_entry.get("result_position") == "standing_knockdown"
                ):
                    att_state["control_marks"] += 1
                grappling_pos = set_pair_position(
                    pair_position, "standing_neutral", attacker_id, "neutral", defender_id, actors, positions_map
                )
                range_band = "punch" if punch_only_ruleset else "kick"

        allowed_grips_cfg = clinch_rules.get("allowed_grips", "all")
        if not clinch_rules.get("allowed", True) or (
            isinstance(allowed_grips_cfg, list)
            and t_kind == "grip"
            and tid not in allowed_grips_cfg
        ):
            if att_state.get("posture_mode") == "standing" and (
                att_state.get("grip") is not None or def_state.get("grip") is not None or grappling_pos != "standing_neutral"
            ):
                grappling_pos = set_pair_position(
                    pair_position, "standing_neutral", attacker_id, "neutral", defender_id, actors, positions_map
                )
                range_band = "punch"
                clinch_exchanges = 0
        elif grappling_pos != "standing_neutral" and att_state.get("posture_mode") == "standing":
            clinch_exchanges += 1
        else:
            clinch_exchanges = 0

        accrue_control_time(pair_position, actors, exchange_frames / float(FPS), positions_data)

        # Update fight_momentum and combo_state (§7.1, §7.5)
        for fid in canonical_ids:
            actors[fid]["fight_momentum"] = float(actors[fid].get("fight_momentum", 0.0)) * (1.0 - fm_decay)
        if outcome in ("clean", "flush") and dmg_info["final_damage"] > 0:
            att_state["fight_momentum"] += fm_landed
            def_state["fight_momentum"] += fm_taken
        if counter_followup_event and counter_followup_event["damage"]["landing_quality"] in ("counter_hit", "clean", "flush"):
            def_state["fight_momentum"] += fm_landed
            att_state["fight_momentum"] += fm_taken
        for fid in canonical_ids:
            actors[fid]["fight_momentum"] = round(
                max(float(fm_lo), min(float(fm_hi), float(actors[fid]["fight_momentum"]))), 4
            )

        prev_chain = int(att_state["combo_state"].get("chain_len", 0)) if matched_combo else 0
        att_state["combo_state"] = {
            "last_tid": tid,
            "last_outcome": outcome,
            "last_def_tid": None,
            "last_def_outcome": None,
            "chain_len": (prev_chain + 1) if outcome not in ("miss", "evaded", "checked", "caught") else 0,
        }
        def_state["combo_state"] = {
            "last_tid": (
                counter_followup_event["technique_id"]
                if counter_followup_event
                else def_state["combo_state"].get("last_tid")
            ),
            "last_outcome": (
                counter_followup_event["damage"]["landing_quality"]
                if counter_followup_event
                else def_state["combo_state"].get("last_outcome")
            ),
            "last_def_tid": defense_used,
            "last_def_outcome": outcome if defense_used else None,
            "chain_len": 1 if (defense_used and outcome in ("evaded", "blocked", "checked", "caught", "jammed")) else 0,
        }

        if tid not in att_state["setups"]:
            att_state["setups"].append(tid)
        if defense_used and defense_used not in def_state["setups"]:
            def_state["setups"].append(defense_used)

        att_state["slot_exchanges"] = int(att_state.get("slot_exchanges", 0)) + 1
        update_slot_stalls(
            str(active_plan.get("abandon_condition", "sequence_denied_or_countered")),
            tid,
            outcome,
            counter_triggered,
            range_band,
            att_state,
            tech_v2_map,
            slot_goal=str(active_plan.get("goal", "head_damage")),
            home_range=str(active_plan.get("home_range", "punch")),
        )
        slot_switched_to, slot_switch_reason = evaluate_slot_switch(
            attacker_id,
            defender_id,
            actors,
            att_card,
            plans,
            range_band,
            exchanges,
            clock_frames,
            max_frames,
            model_cfg,
            tech_v2_map,
        )

        ex_event = {
            "exchange_index": len(exchanges) + 1,
            "round": current_round,
            "t_start": t_start,
            "t_end": t_end,
            "frames": exchange_frames,
            "range": ex_range,
            "lead_foot_matchup": lead_matchup,
            "attacker_id": attacker_id,
            "defender_id": defender_id,
            "active_slot_id": active_plan["slot_id"],
            "technique_id": tid,
            "incoming_class": inc_cls,
            "attack_lane": attack_lane,
            "initiative_scores": initiative_scores,
            "selection": selection_rec,
            "laterality": laterality_rec,
            "combo_id": str(matched_combo["id"]) if matched_combo else None,
            "defender_posture_before": def_posture_before,
            "defender_readiness_profile": def_readiness,
            "lane_readiness_score": lane_readiness,
            "hit_probability": hit_prob,
            "hit": hit_rec,
            "outcome": outcome,
            "defense_used": defense_used,
            "defense": defense_rec,
            "kick_anatomy": kick_detail,
            "damage": dmg_info,
            "counter_followup": counter_followup_event,
            "grappling_position": grappling_pos,
            "grappling": grappling_rec,
            "forced_stance_switch": forced_stance_switch,
            "slot_switched_to": slot_switched_to,
            "slot_switch_reason": slot_switch_reason,
            "effects_applied": effects_applied,
            "state_changes": {
                "defender_damage": copy.deepcopy(def_state["damage"]),
                "attacker_damage": copy.deepcopy(att_state["damage"]),
                "defender_balance": def_state["balance"],
                "attacker_recovery_window": att_state["recovery_window"]["window_type"],
            },
        }
        exchanges.append(ex_event)

        # 7. Check Finish Conditions
        winner_id, finish_reason = check_finish_conditions(
            canonical_ids, actors, model_cfg, ruleset_cfg=ruleset_cfg
        )
        if winner_id:
            break

        # 8. Check Round Break & Rest (§7.1, D2)
        if current_round < num_rounds and clock_frames >= current_round * round_frames:
            current_round += 1
            for fid, x0 in zip(canonical_ids, start_xs):
                st = actors[fid]
                st["fatigue"] = round(float(st["fatigue"]) * (1.0 - rest_fat_rec), 2)
                st["attention"]["feinted"] = False
                st["attention"]["outside_angle_conceded"] = False
                st["stun_exchanges"] = 0
                st["knockdowns_round"] = 0
                st["submission_stage"] = 0
                st["position"] = [float(x0), 0.0]
                st["facing"] = [1.0 if x0 < 0 else -1.0, 0.0]
                prox_r, corner_r, _ = compute_wall_and_corner(st["position"], arena, model_cfg)
                st["wall_proximity"] = prox_r
                st["in_corner"] = corner_r
            grappling_pos = set_pair_position(
                pair_position,
                str(rounds_cfg.get("reset_position_to", "standing_neutral")),
                canonical_ids[0],
                "neutral",
                canonical_ids[1],
                actors,
                positions_map,
            )
            range_band = "punch" if punch_only_ruleset else str(rounds_cfg.get("reset_range_to", "kick"))
            clinch_exchanges = 0
            last_attacker_id = None
            last_recovery_drag = 0.0

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
        "round": current_round,
        "ruleset": ruleset,
        "arena": arena,
        "vertical_mode": vertical_mode,
        "range": range_band,
        "lead_foot_matchup": final_lead,
        "pair_position": copy.deepcopy(pair_position),
        "submission": last_sub_rec,
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
        "duration_requested_s": eff_duration_s,
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
