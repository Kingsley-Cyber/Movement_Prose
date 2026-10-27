"""Data-driven defense lists, defense contests (§7.6), kick-defense window, and unified contest helper for BLOCK Simulator v2."""

from __future__ import annotations

import math
import random
from typing import Any

from .data import (
    KIND_GROUND_STRIKE,
    OPT_DEFAULT_DEFENSE,
    TECH_KICK_CATCH,
    TECH_RETREAT,
    TECH_STEP,
    get_attack_profile,
    load_capabilities_v2,
    load_model_v2,
    load_option_behaviors,
    load_techniques_v2,
)


def contest_roll(
    p: float,
    actor_level: float = 0.0,
    opponent_level: float = 0.0,
    band_name: str = "default",
    rng: random.Random | None = None,
    model_cfg: dict[str, Any] | None = None,
) -> tuple[bool, float, float]:
    """Resolve a contested probability roll through the unified contest helper (§7.6, §7.18.3).

    Returns (won, roll, p_effective). When actor_level == opponent_level, p_effective == p.
    """
    m_cfg = model_cfg if model_cfg is not None else load_model_v2()
    mastery_cfg = m_cfg.get("mastery", {})
    bands = mastery_cfg.get("bands", {})
    band = bands.get(band_name, bands.get("default", [0.05, 0.95]))
    lo, hi = float(band[0]), float(band[1])

    p_eff = float(p)
    level_diff = float(actor_level) - float(opponent_level)
    if abs(level_diff) > 1e-9:
        kappa = float(mastery_cfg.get("contest_logit_per_level", 0.20))
        p_clamped = max(1e-6, min(1.0 - 1e-6, p_eff))
        logit_p = math.log(p_clamped / (1.0 - p_clamped))
        shifted = 1.0 / (1.0 + math.exp(-(logit_p + kappa * level_diff)))
        p_eff = max(lo, min(hi, shifted))

    if rng is None:
        return p_eff >= 0.5, 0.0, p_eff
    roll = rng.random()
    return roll < p_eff, roll, p_eff


def contest(
    p: float,
    actor_level: float = 0.0,
    opponent_level: float = 0.0,
    band_name: str = "default",
    rng: random.Random | None = None,
    model_cfg: dict[str, Any] | None = None,
) -> bool:
    """Boolean wrapper around contest_roll (§7.6)."""
    won, _, _ = contest_roll(p, actor_level, opponent_level, band_name, rng, model_cfg)
    return won


def compute_kick_defense_window(
    defender_card: dict[str, Any],
    wall_proximity: str = "far",
    opt_behaviors: dict[str, dict[str, Any]] | None = None,
    model_cfg: dict[str, Any] | None = None,
) -> float:
    """Compute the additive kick-defense window (§7.6): clamp(0.08 + sum(option kick_defense_window_delta), [0.08, 0.24])."""
    beh = opt_behaviors if opt_behaviors is not None else load_option_behaviors()
    m_cfg = model_cfg if model_cfg is not None else load_model_v2()
    kdw_cfg = m_cfg.get("defense_contest", {}).get("kick_defense_window", {})
    base = float(kdw_cfg.get("base", 0.08))
    lo, hi = kdw_cfg.get("clamp", [0.08, 0.24])
    wall_near = wall_proximity == "near"

    total_delta = 0.0
    dims = defender_card.get("dimensions", {})
    for d in ("mentality", "stance", "defense", "hands", "tie", "kicking", "target"):
        oid = dims.get(d)
        if not oid or oid not in beh:
            continue
        delta_spec = beh[oid].get("kick_defense_window_delta")
        if delta_spec is None:
            continue
        if isinstance(delta_spec, dict):
            if delta_spec.get("unless") == "wall_near" and wall_near:
                continue
            total_delta += float(delta_spec.get("value", 0.0))
        else:
            total_delta += float(delta_spec)

    return max(float(lo), min(float(hi), base + total_delta))


def _trained_capabilities_of_card(card: dict[str, Any], unlocked: tuple[str, ...] = ()) -> set[str]:
    trained = set(card.get("baseline_capabilities", []))
    for slot in card.get("synchronized_capabilities", []):
        trained.update(slot.get("capabilities", []))
    if unlocked:
        for ab in card.get("conditional_abilities", []):
            if ab.get("id") in unlocked and ab.get("grants_capability"):
                trained.add(str(ab["grants_capability"]))
    return trained


def _granting_capability_for_defense(
    tid: str,
    trained_caps: set[str],
    tech_v2: dict[str, dict[str, Any]],
) -> str:
    req = tech_v2.get(tid, {}).get("required_capabilities", [])
    for c in req:
        if c in trained_caps:
            return str(c)
    if req:
        return str(req[0])
    return "basic_movement"


def pick_ordered_defense(
    defender_card: dict[str, Any],
    incoming_tid: str,
    avail_def: set[str] | None = None,
    wall_proximity: str = "far",
    reset_slot_defenses: set[str] | None = None,
    opt_behaviors: dict[str, dict[str, Any]] | None = None,
    unlocked_abilities: tuple[str, ...] = (),
) -> tuple[str, str, str, str]:
    """Build the §7.6 ordered defense list for incoming_tid's class and return (def_tid, success_result, inc_cls, granting_cap)."""
    beh = opt_behaviors if opt_behaviors is not None else load_option_behaviors()
    tech_v2 = load_techniques_v2()
    caps_v2 = load_capabilities_v2().get("capabilities", {})

    t_in = tech_v2.get(incoming_tid, {})
    inc_cls = str(t_in.get("incoming_class") or "straight")
    trained_caps = _trained_capabilities_of_card(defender_card, unlocked_abilities)

    dims = defender_card.get("dimensions", {})
    def_opt = str(dims.get("defense") or OPT_DEFAULT_DEFENSE)
    hands_opt = str(dims.get("hands") or "")
    kick_opt = str(dims.get("kicking") or "")
    wall_near = wall_proximity == "near"

    default_fallback_res = "blocked" if def_opt == OPT_DEFAULT_DEFENSE else "evaded"
    if inc_cls in ("none", "submission"):
        return TECH_RETREAT, default_fallback_res, inc_cls, "basic_movement"
    if inc_cls == KIND_GROUND_STRIKE:
        return TECH_RETREAT, "blocked", inc_cls, "basic_movement"

    raw_entries: list[Any] = []

    # 1. Reset slot defense priority for grapple entries (§7.6)
    if reset_slot_defenses and inc_cls in ("takedown", "clinch_entry"):
        nd_reset = beh.get(def_opt, {}).get("native_defense", {}).get("by_class", {}).get(inc_cls, [])
        for entry in nd_reset:
            tid_e = entry["technique"] if isinstance(entry, dict) else str(entry)
            if tid_e in reset_slot_defenses:
                raw_entries.append(entry)
        for tid_r in sorted(reset_slot_defenses):
            def_meta_r = tech_v2.get(tid_r, {}).get("defends") or {}
            if inc_cls in def_meta_r.get("designed_for", []):
                raw_entries.append(tid_r)

    # 2. Trained school defense_prepend[class]
    for cap in sorted(trained_caps):
        cap_prep = caps_v2.get(cap, {}).get("defense_prepend", {}).get(inc_cls, [])
        if cap_prep:
            raw_entries.extend(cap_prep)

    # 3. Kicking option kick_defense_prepend[class]
    if kick_opt and kick_opt in beh:
        k_prep = beh[kick_opt].get("kick_defense_prepend", {}).get(inc_cls, [])
        if k_prep:
            raw_entries.extend(k_prep)

    # 4. Hands option defense_prepend[class]
    if hands_opt and hands_opt in beh:
        h_prep = beh[hands_opt].get("defense_prepend", {}).get(inc_cls, [])
        if h_prep:
            raw_entries.extend(h_prep)

    # 5. Defense option native_defense (at_wall when wall_near and present, else by_class)
    nd = beh.get(def_opt, beh.get(OPT_DEFAULT_DEFENSE, {})).get("native_defense", {})
    at_wall = nd.get("at_wall", {})
    by_class = nd.get("by_class", {})
    if wall_near and inc_cls in at_wall:
        raw_entries.extend(at_wall[inc_cls])
    else:
        raw_entries.extend(by_class.get(inc_cls, []))

    always_avail = {TECH_RETREAT, TECH_STEP}
    seen_tids: set[str] = set()
    chosen_tid = TECH_RETREAT
    chosen_override_res: str | None = None

    for entry in raw_entries:
        if isinstance(entry, dict):
            cand_tid = str(entry["technique"])
            cand_res = str(entry.get("result") or "") or None
        else:
            cand_tid = str(entry)
            cand_res = None
        if cand_tid in seen_tids:
            continue
        seen_tids.add(cand_tid)
        if avail_def is not None and cand_tid not in always_avail and cand_tid not in avail_def:
            continue
        chosen_tid = cand_tid
        chosen_override_res = cand_res
        break

    if chosen_override_res is not None:
        success_res = chosen_override_res
    elif chosen_tid == TECH_RETREAT and def_opt == OPT_DEFAULT_DEFENSE:
        success_res = "blocked"
    else:
        def_meta = tech_v2.get(chosen_tid, {}).get("defends") or {}
        res_by_cls = def_meta.get("result_by_class", {})
        success_res = str(res_by_cls.get(inc_cls) or def_meta.get("success_result") or default_fallback_res)

    grant_cap = _granting_capability_for_defense(chosen_tid, trained_caps, tech_v2)
    return chosen_tid, success_res, inc_cls, grant_cap


def resolve_contested_defense(
    defender_card: dict[str, Any],
    attacker_card: dict[str, Any] | None,
    incoming_tid: str,
    offense_score: float,
    lane_readiness: float,
    avail_def: set[str] | None,
    wall_proximity: str = "far",
    reset_slot_defenses: set[str] | None = None,
    rng: random.Random | None = None,
    opt_behaviors: dict[str, dict[str, Any]] | None = None,
    model_cfg: dict[str, Any] | None = None,
    defender_level: float = 0.0,
    attacker_level: float = 0.0,
    unlocked_abilities: tuple[str, ...] = (),
) -> tuple[str | None, str, float, float, str, str]:
    """Pick the defender's ordered defense and resolve the §7.6 defense or kick-catch contest.

    Returns (def_tid, outcome, p_success, roll, granting_cap, incoming_class).
    """
    beh = opt_behaviors if opt_behaviors is not None else load_option_behaviors()
    m_cfg = model_cfg if model_cfg is not None else load_model_v2()
    tech_v2 = load_techniques_v2()
    dc_cfg = m_cfg.get("defense_contest", {})
    kd_cfg = m_cfg.get("kick_defense", {})

    def_tid, success_res, inc_cls, grant_cap = pick_ordered_defense(
        defender_card,
        incoming_tid,
        avail_def=avail_def,
        wall_proximity=wall_proximity,
        reset_slot_defenses=reset_slot_defenses,
        opt_behaviors=beh,
        unlocked_abilities=unlocked_abilities,
    )

    if rng is None:
        if inc_cls == KIND_GROUND_STRIKE:
            return None, "blocked", 1.0, 0.0, "basic_movement", inc_cls
        return def_tid, success_res, 1.0, 0.0, grant_cap, inc_cls

    fail_res = str(dc_cfg.get("failure_result", "blocked"))

    if inc_cls == KIND_GROUND_STRIKE:
        slope = float(dc_cfg.get("slope", 1.0))
        dc_lo, dc_hi = dc_cfg.get("probability_clamp", [0.15, 0.85])
        raw_p = 1.0 / (1.0 + math.exp(-slope * (lane_readiness - offense_score)))
        p_def = max(float(dc_lo), min(float(dc_hi), raw_p))
        _, roll, p_eff = contest_roll(
            p_def, defender_level, attacker_level, "defense_contest", rng=rng, model_cfg=m_cfg
        )
        return None, "blocked", p_eff, roll, "basic_movement", inc_cls

    # Kick catch uses the catchability roll (§7.6, §7.11)
    if def_tid == TECH_KICK_CATCH:
        catch_lo, catch_hi = kd_cfg.get("catch_clamp", [0.10, 0.65])
        catch_rdy_factor = float(kd_cfg.get("catch_readiness_factor", 0.05))
        t_in = tech_v2.get(incoming_tid, {})
        base_catch = float(t_in.get("catchability") or 0.18)
        dims = defender_card.get("dimensions", {})
        kick_opt = str(dims.get("kicking") or "")
        def_opt = str(dims.get("defense") or "")
        def_catch_bonus = (
            float(get_attack_profile(kick_opt, beh).get("kick_catch_bonus", 0.0))
            + float(get_attack_profile(def_opt, beh).get("kick_catch_bonus", 0.0))
        )
        att_kick_opt = str((attacker_card or {}).get("dimensions", {}).get("kicking") or "")
        retract_mod = float(get_attack_profile(att_kick_opt, beh).get("kick_retraction_delta", 0.0))
        catch_prob = max(
            float(catch_lo),
            min(
                float(catch_hi),
                base_catch + def_catch_bonus + retract_mod + catch_rdy_factor * (lane_readiness - 3.0),
            ),
        )
        won, roll, p_eff = contest_roll(
            catch_prob, defender_level, attacker_level, TECH_KICK_CATCH, rng=rng, model_cfg=m_cfg
        )
        return def_tid, (success_res if won else fail_res), p_eff, roll, grant_cap, inc_cls

    # Standard defense contest (§7.6): p = clamp(sigmoid(slope * (readiness - offense + defense_fit)), 0.15, 0.85)
    slope = float(dc_cfg.get("slope", 1.0))
    dc_lo, dc_hi = dc_cfg.get("probability_clamp", [0.15, 0.85])
    fit_cfg = dc_cfg.get("defense_fit", {"designed_for": 0.4, "general": 0.0, "poor_for": -0.4})
    def_meta = tech_v2.get(def_tid, {}).get("defends") or {}
    if inc_cls in def_meta.get("designed_for", []):
        fit = float(fit_cfg.get("designed_for", 0.4))
    elif inc_cls in def_meta.get("poor_for", []):
        fit = float(fit_cfg.get("poor_for", -0.4))
    else:
        fit = float(fit_cfg.get("general", 0.0))

    raw_p = 1.0 / (1.0 + math.exp(-slope * (lane_readiness - offense_score + fit)))
    p_def = max(float(dc_lo), min(float(dc_hi), raw_p))
    won, roll, p_eff = contest_roll(
        p_def, defender_level, attacker_level, "defense_contest", rng=rng, model_cfg=m_cfg
    )
    return def_tid, (success_res if won else fail_res), p_eff, roll, grant_cap, inc_cls


def select_kick_defense(
    defender_card: dict[str, Any],
    kick_tid: str,
    range_band: str,
    lane_readiness: float = 3.5,
    attacker_card: dict[str, Any] | None = None,
    rng: random.Random | None = None,
    opt_behaviors: dict[str, dict[str, Any]] | None = None,
    wall_proximity: str = "far",
    avail_def: set[str] | None = None,
    offense_score: float = 3.0,
) -> tuple[str, str]:
    """Return (defense_action, outcome_effect) native to defender's defense & kicking dimensions (§7.6)."""
    if rng is None:
        def_tid, success_res, _, _ = pick_ordered_defense(
            defender_card,
            kick_tid,
            avail_def=avail_def,
            wall_proximity=wall_proximity,
            opt_behaviors=opt_behaviors,
        )
        return def_tid, success_res
    def_tid, outcome, _, _, _, _ = resolve_contested_defense(
        defender_card,
        attacker_card,
        kick_tid,
        offense_score=offense_score,
        lane_readiness=lane_readiness,
        avail_def=avail_def,
        wall_proximity=wall_proximity,
        rng=rng,
        opt_behaviors=opt_behaviors,
    )
    return str(def_tid or TECH_RETREAT), outcome


def select_native_defense(
    defender_card: dict[str, Any],
    incoming_tid: str,
    range_band: str,
    avail_def: set[str] | None = None,
    wall_proximity: str = "far",
    reset_slot_defenses: set[str] | None = None,
    rng: random.Random | None = None,
    offense_score: float = 3.0,
    lane_readiness: float = 3.0,
) -> tuple[str, str]:
    """Select the defender's native posture-driven defensive action and outcome (§7.6)."""
    if rng is None:
        def_tid, success_res, _, _ = pick_ordered_defense(
            defender_card,
            incoming_tid,
            avail_def=avail_def,
            wall_proximity=wall_proximity,
            reset_slot_defenses=reset_slot_defenses,
        )
        return def_tid, success_res
    def_tid, outcome, _, _, _, _ = resolve_contested_defense(
        defender_card,
        None,
        incoming_tid,
        offense_score=offense_score,
        lane_readiness=lane_readiness,
        avail_def=avail_def,
        wall_proximity=wall_proximity,
        reset_slot_defenses=reset_slot_defenses,
        rng=rng,
    )
    return str(def_tid or TECH_RETREAT), outcome
