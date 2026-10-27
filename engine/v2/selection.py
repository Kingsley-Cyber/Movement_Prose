"""Slot gameplan construction, trigger/abandon evaluation (§7.16), and weighted seeded selection (§7.5) for BLOCK Simulator v2."""

from __future__ import annotations

import math
import random
from pathlib import Path
from typing import Any, Iterable

from ..capabilities import admitted_slots
from ..ontology import Knowledge
from .availability import slot_defense_pool_v2, slot_pool_v2
from .cards import compute_school_depth_multiplier
from .data import (
    KIND_DEFENSE,
    KIND_ESCAPE,
    KIND_FEINT,
    KIND_GROUND_STRIKE,
    KIND_MOVEMENT,
    TECH_CLINCH_BREAK,
    TECH_CUT_OFF_STEP,
    TECH_FEINT,
    TECH_GUARD_PULL,
    TECH_RETREAT,
    TECH_STAND_UP,
    TECH_STEP,
    load_capabilities_v2,
    load_combinations_v2,
    load_debt_registry_v2,
    load_model_v2,
    load_option_behaviors,
    load_techniques_v2,
)

_COMBO_INDEX_CACHE: dict[str, list[dict[str, Any]]] = {}
_DEBT_INDEX_CACHE: dict[str, dict[str, dict[str, Any]]] = {}


def _get_combos(root: Path) -> list[dict[str, Any]]:
    key = str(root.resolve())
    cached = _COMBO_INDEX_CACHE.get(key)
    if cached is None:
        raw = load_combinations_v2(root)
        cached = list(raw.get("combinations", []))
        _COMBO_INDEX_CACHE[key] = cached
    return cached


def _get_debt_map(k: Knowledge) -> dict[str, dict[str, Any]]:
    key = str(k.root.resolve())
    cached = _DEBT_INDEX_CACHE.get(key)
    if cached is not None:
        return cached
    overlay_raw = load_debt_registry_v2(k.root).get("debts", [])
    overlay_by_id: dict[str, list[str]] = {}
    if isinstance(overlay_raw, list):
        for item in overlay_raw:
            did = str(item.get("debt_id", ""))
            if did:
                overlay_by_id[did] = [str(x) for x in item.get("add_technique_ids", [])]
    elif isinstance(overlay_raw, dict):
        for did, item in overlay_raw.items():
            overlay_by_id[str(did)] = [str(x) for x in item.get("add_technique_ids", [])]

    debt_map: dict[str, dict[str, Any]] = {}
    for did, d_base in k.debts.items():
        base_tids = set(d_base.get("technique_ids", []))
        add_tids = set(overlay_by_id.get(did, []))
        debt_map[did] = {
            "required_range": str(d_base.get("required_range", "punch")),
            "ruleset_legality": set(d_base.get("ruleset_legality", [])),
            "technique_ids": base_tids | add_tids,
        }
    _DEBT_INDEX_CACHE[key] = debt_map
    return debt_map


def build_slot_plans(
    k: Knowledge,
    card: dict[str, Any],
    ruleset: str = "mma",
    activated: Iterable[str] = (),
) -> list[dict[str, Any]]:
    """Build executable SlotPlan objects honoring card triggers, links, abandon rules, and per-slot pools (§6.0.3, §7.5)."""
    tech_v2 = load_techniques_v2(k.root)
    opt_beh = load_option_behaviors(k.root)
    plans: list[dict[str, Any]] = []
    slots = admitted_slots(card, k)
    depth_mult = compute_school_depth_multiplier(card, k)
    mentality_opt = card["dimensions"].get("mentality")
    default_stalls = int(
        opt_beh.get(mentality_opt or "", {}).get("selection_profile", {}).get("switch_after_stalls", 2)
    )
    pref_ranges = card.get("preferred_ranges") or ["punch"]

    for idx, slot in enumerate(slots):
        caps = set(slot.get("capabilities", []))
        s_pool = slot_pool_v2(k, card, caps, ruleset, activated)
        non_counter_pool = {tid for tid in s_pool if tech_v2.get(tid, {}).get("usage") != "counter"}

        explicit_seq = [m for m in slot.get("sequence", []) if m in s_pool]
        if explicit_seq:
            clean_seq = explicit_seq
        else:
            clean_seq = [
                tid
                for tid in card.get("active_techniques", [])
                if tid in non_counter_pool and tech_v2.get(tid, {}).get("kind") != KIND_DEFENSE
            ]
            if not clean_seq:
                clean_seq = sorted(non_counter_pool) or [TECH_STEP]

        home_range = slot.get("home_range") or str(pref_ranges[0])
        goal = str(slot.get("goal") or "head_damage")
        trigger = str(slot.get("trigger") or ("fight_start" if idx == 0 else "slot_stalled_or_countered"))
        abandon_rule = slot.get("abandon_rule", {})
        max_stalls = int(abandon_rule.get("max_consecutive_stalls", default_stalls))
        abandon_cond = str(abandon_rule.get("condition") or "sequence_denied_or_countered")
        links = list(slot.get("links") or [])

        reset_defs: set[str] = set()
        if goal == "reset_to_home_range":
            reset_defs = slot_defense_pool_v2(k, card, caps, ruleset, activated)

        plans.append(
            {
                "slot_id": str(slot.get("id", f"{card['fighter_id']}.slot.{idx + 1}")),
                "slot_index": idx,
                "capabilities": list(slot.get("capabilities", [])),
                "sequence": clean_seq,
                "pool": sorted(non_counter_pool),
                "full_pool": sorted(s_pool),
                "reset_defenses": sorted(reset_defs),
                "home_range": str(home_range),
                "goal": goal,
                "depth_multiplier": depth_mult,
                "trigger": trigger,
                "abandon_condition": abandon_cond,
                "abandon_threshold": max_stalls,
                "links": links,
                "next_slot_id": links[0] if links else slots[(idx + 1) % len(slots)]["id"],
            }
        )
    return plans


def get_initial_slot_index(plans: list[dict[str, Any]]) -> int:
    """Return the index of the slot with trigger == 'fight_start', or 0 if none (§7.16)."""
    for idx, p in enumerate(plans):
        if p.get("trigger") == "fight_start":
            return idx
    return 0


def check_trigger_holds(
    trigger: str,
    actor_id: str,
    opp_id: str,
    actors: dict[str, dict[str, Any]],
    range_band: str,
    exchanges: list[dict[str, Any]],
    clock_frames: int,
    max_frames: int,
    abandon_fired: bool,
    model_cfg: dict[str, Any],
    tech_v2_map: dict[str, dict[str, Any]],
) -> bool:
    """Evaluate a §7.16 slot trigger predicate against the current fight state."""
    thresh = model_cfg.get("slot_triggers", {}).get("thresholds", {})
    commit_min = float(thresh.get("commit_penalty_min", 0.45))
    hurt_head = float(thresh.get("hurt_head_damage", 6.0))
    late_frac = float(thresh.get("late_fight_fraction", 0.70))
    behind_margin = float(thresh.get("behind_margin", 1.0))
    basic_core = load_capabilities_v2().get("capabilities", {}).get("basic_movement", {}).get("core", [])
    circle_out_ids = {str(basic_core[1]), str(basic_core[2])} if len(basic_core) > 2 else set()

    actor_st = actors[actor_id]
    opp_st = actors[opp_id]

    if trigger == "fight_start":
        return len(exchanges) == 0
    if trigger in ("slot_stalled", "slot_stalled_or_countered"):
        return abandon_fired
    if trigger == "slot_stalled_or_close_range":
        return abandon_fired or range_band in ("close", "clinch")
    if trigger == "opponent_kicks":
        for ex in exchanges[-2:]:
            if ex["attacker_id"] == opp_id:
                tk = tech_v2_map.get(ex["technique_id"], {}).get("kind")
                if tk in ("kick", "knee"):
                    return True
        return False
    if trigger == "opponent_commits":
        if exchanges and exchanges[-1]["attacker_id"] == opp_id:
            last_ex = exchanges[-1]
            if last_ex["outcome"] in ("miss", "evaded", "blocked", "checked", "caught", "jammed"):
                rec_pen = float(
                    tech_v2_map.get(last_ex["technique_id"], {})
                    .get("recovery_exposure", {})
                    .get("readiness_penalty", 0.0)
                )
                return rec_pen >= commit_min
        return False
    if trigger == "opponent_enters":
        if len(exchanges) >= 2 and exchanges[-1]["attacker_id"] == opp_id:
            ladder = ["outside", "kick", "punch", "close", "clinch", "ground"]
            r_prev = exchanges[-2]["range"]
            r_last = exchanges[-1]["range"]
            if r_prev in ladder and r_last in ladder and ladder.index(r_last) > ladder.index(r_prev):
                return True
        return False
    if trigger == "opponent_circles_out":
        opp_actions: list[str] = []
        for ex in reversed(exchanges):
            if ex["attacker_id"] == opp_id:
                opp_actions.append(str(ex["technique_id"]))
            elif ex["defender_id"] == opp_id and ex.get("defense_used"):
                opp_actions.append(str(ex["defense_used"]))
            if len(opp_actions) >= 3:
                break
        return sum(1 for a in opp_actions[:3] if a in circle_out_ids) >= 2
    if trigger == "opponent_clinches_or_shoots":
        if exchanges and exchanges[-1]["attacker_id"] == opp_id:
            tk = tech_v2_map.get(exchanges[-1]["technique_id"], {}).get("kind")
            if tk in ("grip", "takedown", "sweep") and exchanges[-1]["outcome"] in (
                "clean",
                "flush",
                "partial",
                "counter_hit",
                "jammed",
            ):
                return True
        return range_band == "clinch" or actor_st.get("grappling_position", "standing_neutral") != "standing_neutral"
    if trigger == "opponent_on_wall":
        return opp_st.get("wall_proximity") == "near"
    if trigger == "self_on_wall":
        return actor_st.get("wall_proximity") == "near"
    if trigger == "close_range_reached":
        return range_band in ("close", "clinch")
    if trigger == "self_hurt":
        return (
            float(actor_st["damage"]["head"]) >= hurt_head
            or int(actor_st.get("stun_exchanges", 0)) > 0
            or int(actor_st.get("knockdowns", 0)) > 0
        )
    if trigger == "opponent_hurt":
        return float(opp_st["damage"]["head"]) >= hurt_head or int(opp_st.get("stun_exchanges", 0)) > 0
    if trigger == "clinch_entered":
        return range_band == "clinch"
    if trigger == "ground_entered":
        return range_band == "ground" or actor_st.get("posture_mode") == "ground"
    if trigger == "late_fight":
        return clock_frames >= late_frac * max(1, max_frames)
    if trigger == "behind_on_score":
        own_dmg = sum(float(v) for v in opp_st["damage"].values())
        opp_dmg = sum(float(v) for v in actor_st["damage"].values())
        return (opp_dmg - own_dmg) >= behind_margin
    return False


def update_slot_stalls(
    condition: str,
    tid: str,
    outcome: str,
    counter_triggered: bool,
    range_band: str,
    att_state: dict[str, Any],
    tech_v2_map: dict[str, dict[str, Any]],
    slot_goal: str = "head_damage",
    home_range: str = "punch",
) -> None:
    """Update att_state['slot_stalls'] after an exchange according to the active slot's abandon_condition (§7.16)."""
    tk = tech_v2_map.get(tid, {}).get("kind", "punch")
    is_closing_to_clinch = (
        tid in (TECH_STEP, TECH_CUT_OFF_STEP)
        and home_range in ("clinch", "ground")
        and range_band not in ("clinch", "ground")
    )
    is_non_reset_move = (
        tk in (KIND_MOVEMENT, KIND_FEINT)
        and slot_goal != "reset_to_home_range"
        and not is_closing_to_clinch
    )
    landed = (
        outcome in ("partial", "clean", "flush", "counter_hit")
        and not counter_triggered
        and not is_non_reset_move
        and not is_closing_to_clinch
    )
    failed = (
        outcome in ("miss", "evaded", "blocked", "checked", "caught", "jammed")
        or counter_triggered
        or is_non_reset_move
    )

    if condition == "kicks_blocked_or_jammed":
        if tk in ("kick", "knee"):
            if outcome in ("blocked", "checked", "caught", "jammed"):
                att_state["slot_stalls"] = int(att_state.get("slot_stalls", 0)) + 1
            elif landed:
                att_state["slot_stalls"] = 0
    elif condition == "clinch_denied_or_escaped":
        if tk in ("grip", "takedown", "sweep", KIND_ESCAPE):
            if failed:
                att_state["slot_stalls"] = int(att_state.get("slot_stalls", 0)) + 1
            elif landed:
                att_state["slot_stalls"] = 0
        elif failed:
            att_state["slot_stalls"] = int(att_state.get("slot_stalls", 0)) + 1
    elif condition == "pocket_stalled":
        if range_band in ("punch", "close"):
            if not landed:
                att_state["slot_stalls"] = int(att_state.get("slot_stalls", 0)) + 1
            else:
                att_state["slot_stalls"] = 0
        elif failed:
            att_state["slot_stalls"] = int(att_state.get("slot_stalls", 0)) + 1
    else:
        if failed:
            att_state["slot_stalls"] = int(att_state.get("slot_stalls", 0)) + 1
        elif landed:
            att_state["slot_stalls"] = 0


def _plan_has_ground_kit(plan: dict[str, Any], tech_v2_map: dict[str, dict[str, Any]]) -> bool:
    if plan.get("goal") in ("submission_finish", "takedown_top_control"):
        return True
    return any(
        "ground" in tech_v2_map.get(tid, {}).get("required_range", []) and tid != TECH_STAND_UP
        for tid in plan.get("full_pool", plan.get("pool", []))
    )


def evaluate_slot_switch(
    actor_id: str,
    opp_id: str,
    actors: dict[str, dict[str, Any]],
    card: dict[str, Any],
    plans: list[dict[str, Any]],
    range_band: str,
    exchanges: list[dict[str, Any]],
    clock_frames: int,
    max_frames: int,
    model_cfg: dict[str, Any],
    tech_v2_map: dict[str, dict[str, Any]],
) -> tuple[str | None, str | None]:
    """Evaluate §7.16 slot switching rules: (1) reset_to_home_range completion, (2) abandon rule, (3) reactive trigger pre-emption."""
    if len(plans) <= 1:
        return None, None

    actor_st = actors[actor_id]
    cur_idx = int(actor_st.get("active_slot_idx", 0)) % len(plans)
    cur_plan = plans[cur_idx]
    plan_by_id = {p["slot_id"]: (i, p) for i, p in enumerate(plans)}

    # When on the ground, prefer slots that actually contain a trained ground kit
    if range_band == "ground" or actor_st.get("posture_mode") == "ground":
        if not _plan_has_ground_kit(cur_plan, tech_v2_map):
            for idx, p in enumerate(plans):
                if _plan_has_ground_kit(p, tech_v2_map):
                    actor_st["active_slot_idx"] = idx
                    actor_st["active_slot_id"] = p["slot_id"]
                    actor_st["slot_stalls"] = 0
                    actor_st["slot_exchanges"] = 0
                    actor_st["slot_switches"] = int(actor_st.get("slot_switches", 0)) + 1
                    return str(p["slot_id"]), "ground_entered"
        elif not any(
            _plan_has_ground_kit(p, tech_v2_map) and p["slot_id"] != cur_plan["slot_id"] for p in plans
        ):
            return None, None

    thresh = model_cfg.get("slot_triggers", {}).get("thresholds", {})
    min_preempt = int(thresh.get("min_exchanges_before_preempt", 2))

    is_standing_neutral = (
        actor_st.get("posture_mode") == "standing"
        and actor_st.get("grappling_position", "standing_neutral") == "standing_neutral"
    )

    # Rule 3: reset_to_home_range completion when back standing_neutral
    if (
        cur_plan.get("goal") == "reset_to_home_range"
        and is_standing_neutral
        and int(actor_st.get("slot_exchanges", 0)) >= 1
    ):
        target_sid = (cur_plan.get("links") or [plans[(cur_idx + 1) % len(plans)]["slot_id"]])[0]
        if target_sid in plan_by_id and target_sid != cur_plan["slot_id"]:
            new_idx, new_plan = plan_by_id[target_sid]
            actor_st["active_slot_idx"] = new_idx
            actor_st["active_slot_id"] = new_plan["slot_id"]
            actor_st["slot_stalls"] = 0
            actor_st["slot_exchanges"] = 0
            actor_st["slot_switches"] = int(actor_st.get("slot_switches", 0)) + 1
            return str(new_plan["slot_id"]), "reset_complete"

    # Rule 1: abandon rule fired
    abandon_fired = int(actor_st.get("slot_stalls", 0)) >= int(cur_plan.get("abandon_threshold", 2))
    if abandon_fired:
        links = cur_plan.get("links") or []
        chosen_idx: int | None = None
        for l_sid in links:
            if l_sid in plan_by_id:
                cand_idx, cand_plan = plan_by_id[l_sid]
                if cand_plan.get("goal") == "reset_to_home_range" and is_standing_neutral:
                    continue
                if check_trigger_holds(
                    str(cand_plan.get("trigger", "")),
                    actor_id,
                    opp_id,
                    actors,
                    range_band,
                    exchanges,
                    clock_frames,
                    max_frames,
                    True,
                    model_cfg,
                    tech_v2_map,
                ):
                    chosen_idx = cand_idx
                    break
        if chosen_idx is None:
            non_reset_links = [
                l_sid
                for l_sid in links
                if l_sid in plan_by_id and plan_by_id[l_sid][1].get("goal") != "reset_to_home_range"
            ]
            if non_reset_links:
                chosen_idx = plan_by_id[non_reset_links[0]][0]
            else:
                for offset in range(1, len(plans) + 1):
                    cand_i = (cur_idx + offset) % len(plans)
                    if plans[cand_i].get("goal") != "reset_to_home_range":
                        chosen_idx = cand_i
                        break
                if chosen_idx is None:
                    chosen_idx = (cur_idx + 1) % len(plans)
        new_plan = plans[chosen_idx]
        if new_plan["slot_id"] != cur_plan["slot_id"]:
            actor_st["active_slot_idx"] = chosen_idx
            actor_st["active_slot_id"] = new_plan["slot_id"]
            actor_st["slot_Cursor"] = 0
            actor_st["slot_stalls"] = 0
            actor_st["slot_exchanges"] = 0
            actor_st["slot_switches"] = int(actor_st.get("slot_switches", 0)) + 1
            return str(new_plan["slot_id"]), "abandon_rule"

    # Rule 2: reactive trigger pre-emption after min_exchanges_before_preempt exchanges in current slot
    if int(actor_st.get("slot_exchanges", 0)) >= min_preempt:
        links = cur_plan.get("links") or []
        for l_sid in links:
            if l_sid not in plan_by_id or l_sid == cur_plan["slot_id"]:
                continue
            cand_idx, cand_plan = plan_by_id[l_sid]
            trig = str(cand_plan.get("trigger", ""))
            if trig in ("fight_start", "slot_stalled", "slot_stalled_or_countered"):
                continue
            if cand_plan.get("goal") == "reset_to_home_range":
                continue
            if check_trigger_holds(
                trig,
                actor_id,
                opp_id,
                actors,
                range_band,
                exchanges,
                clock_frames,
                max_frames,
                False,
                model_cfg,
                tech_v2_map,
            ):
                actor_st["active_slot_idx"] = cand_idx
                actor_st["active_slot_id"] = cand_plan["slot_id"]
                actor_st["slot_Cursor"] = 0
                actor_st["slot_stalls"] = 0
                actor_st["slot_exchanges"] = 0
                actor_st["slot_switches"] = int(actor_st.get("slot_switches", 0)) + 1
                return str(cand_plan["slot_id"]), f"reactive:{trig}"

    return None, None


def _satisfies_goal_predicate(goal: str, tid: str, t_v2: dict[str, Any]) -> bool:
    """Evaluate §7.16 goal_alignment predicate."""
    kind = str(t_v2.get("kind", ""))
    usage = str(t_v2.get("usage", ""))
    reg_fam = str(t_v2.get("region_family", ""))
    exploits = t_v2.get("exploits_openings", [])
    req_rng = t_v2.get("required_range", [])
    res_pos = t_v2.get("result_position")

    if goal == "head_damage":
        return reg_fam == "head"
    if goal == "body_attrition":
        return reg_fam == "body"
    if goal == "leg_attrition":
        return reg_fam == "leg"
    if goal == "counter_trap":
        return usage in ("counter", "both") or kind == KIND_FEINT or "recovery" in exploits
    if goal == "clinch_control":
        return kind in ("grip", "knee", "elbow") and "clinch" in req_rng
    if goal == "takedown_top_control":
        return kind in ("grip", "takedown", "sweep", "control", KIND_GROUND_STRIKE)
    if goal == "submission_finish":
        return kind == "submission" or tid == TECH_GUARD_PULL or res_pos in ("closed_guard", "back_control", "mount")
    if goal == "wall_pressure":
        return "wall" in exploits or tid == TECH_CUT_OFF_STEP
    if goal == "reset_to_home_range":
        return kind in (KIND_MOVEMENT, KIND_ESCAPE)
    if goal == "position":
        return kind in ("grip", "control") or res_pos is not None
    return False


def _match_combination(
    tid: str,
    slot_caps: set[str],
    combo_state: dict[str, Any] | None,
    max_combo_len: float,
    combos: list[dict[str, Any]],
) -> dict[str, Any] | None:
    if not combo_state:
        return None
    chain_len = int(combo_state.get("chain_len", 0))
    if chain_len >= int(math.ceil(max_combo_len)):
        return None

    last_tid = combo_state.get("last_tid")
    last_out = combo_state.get("last_outcome")
    last_def_tid = combo_state.get("last_def_tid")
    last_def_out = combo_state.get("last_def_outcome")

    for c in combos:
        if c.get("school") not in slot_caps:
            continue
        chain = c.get("chain", [])
        trig = c.get("trigger_on")
        req_out = c.get("requires_previous_outcome", [])
        if trig == "defended":
            prev_m = last_def_tid
            prev_o = last_def_out
            out_ok = prev_o in req_out
        elif trig == "executed":
            prev_m = last_tid
            prev_o = last_out
            out_ok = prev_o not in (None, "miss", "evaded", "checked", "caught")
        else:
            prev_m = last_tid
            prev_o = last_out
            out_ok = prev_o in req_out or prev_o in ("flush", "counter_hit")

        if not prev_m or not out_ok:
            continue
        for idx in range(len(chain) - 1):
            if chain[idx] == prev_m and chain[idx + 1] == tid:
                return c
    return None


def _compute_opp_debt_exploit_set(
    k: Knowledge,
    opp_card: dict[str, Any],
    ruleset: str,
    range_band: str,
) -> set[str]:
    debt_map = _get_debt_map(k)
    opp_debts: set[str] = set(opp_card.get("exploitable_seams", []))
    for oid in opp_card.get("dimensions", {}).values():
        if oid and oid in k.options:
            opp_debts.update(k.options[oid].get("exploitable_debt_ids", []))

    ladder = ["ground", "clinch", "close", "punch", "kick", "outside"]
    cur_idx = ladder.index(range_band) if range_band in ladder else 3
    exploit_tids: set[str] = set()
    for did in opp_debts:
        d_info = debt_map.get(did)
        if not d_info or ruleset not in d_info["ruleset_legality"]:
            continue
        d_rng = d_info["required_range"]
        d_idx = ladder.index(d_rng) if d_rng in ladder else 3
        if abs(d_idx - cur_idx) <= 1:
            exploit_tids.update(d_info["technique_ids"])
    return exploit_tids


def _granting_capability_for_attack(
    tid: str,
    slot_caps: set[str],
    tech_v2_map: dict[str, dict[str, Any]],
) -> str:
    req = tech_v2_map.get(tid, {}).get("required_capabilities", [])
    for c in req:
        if c in slot_caps:
            return str(c)
    if "basic_movement" in req:
        return "basic_movement"
    if req:
        return str(req[0])
    return "basic_movement"


def build_candidate_pool_v2(
    card: dict[str, Any],
    active_plan: dict[str, Any],
    att_state: dict[str, Any],
    range_band: str,
    tech_v2_map: dict[str, dict[str, Any]],
) -> list[str]:
    """Build the §7.5 candidate pool for the active slot at the current range and position."""
    full_pool = list(active_plan.get("full_pool", active_plan.get("pool", [])))
    seq = list(active_plan.get("sequence", []))
    seq_set = set(seq)
    sig_set = set(card.get("signature_moves", []))
    goal = str(active_plan.get("goal", "head_damage"))
    basic_core = set(load_capabilities_v2().get("capabilities", {}).get("basic_movement", {}).get("core", []))
    att_dims = card.get("dimensions", {})
    wall_near = att_state.get("wall_proximity") == "near"
    cur_grip = att_state.get("grip")
    checked_kicks = int(att_state.get("kick_checks_suffered", 0)) >= 2

    if att_state.get("grappling_position") == "standing_knockdown" and TECH_STAND_UP in full_pool:
        return [TECH_STAND_UP]

    if range_band == "ground":
        cur_pos = str(att_state.get("grappling_position", "closed_guard"))
        if cur_pos == "closed_guard_bottom":
            cur_pos = "closed_guard"
        elif cur_pos == "half_guard_top":
            cur_pos = "half_guard"
        elif cur_pos == "mount_or_back_ride":
            cur_pos = "mount"
        cur_role = str(
            att_state.get("role")
            or ("top" if cur_grip == "top" else ("bottom" if cur_grip == "bottom" else "neutral"))
        )
        is_top = cur_role == "top" or cur_grip == "top"

        exact_cands: list[str] = []
        role_cands: list[str] = []
        for tid in full_pool:
            t = tech_v2_map.get(tid, {})
            if t.get("usage") not in ("attack", "both", "movement") or t.get("kind") == KIND_DEFENSE:
                continue
            if "ground" not in t.get("required_range", []):
                continue
            if t.get("requires_wall") and not wall_near:
                continue
            req_pos = t.get("requires_position")
            if isinstance(req_pos, list) and req_pos:
                role_tag = ":top" if is_top else ":bottom"
                if not any(role_tag in str(p) or ":" not in str(p) for p in req_pos):
                    continue
                matched_exact = False
                for p in req_pos:
                    p_clean = str(p).split(" ")[0]
                    req_p, req_r = p_clean.split(":", 1) if ":" in p_clean else (p_clean, None)
                    if (req_p in (cur_pos, "any_ground")) and (req_r in (None, cur_role) or cur_role == "neutral"):
                        matched_exact = True
                        break
                if matched_exact:
                    exact_cands.append(tid)
                role_cands.append(tid)
            else:
                exact_cands.append(tid)
                role_cands.append(tid)

        ground_cands = exact_cands if exact_cands else role_cands
        if not is_top and goal == "submission_finish":
            sub_cands = [
                tid
                for tid in ground_cands
                if tech_v2_map.get(tid, {}).get("kind") == "submission"
                or (
                    tech_v2_map.get(tid, {}).get("kind") == "control"
                    and tid not in basic_core
                    and float(tech_v2_map.get(tid, {}).get("base_damage", 0.0)) > 0.0
                )
            ]
            if sub_cands:
                return sorted(set(sub_cands))
            non_basic_esc = [tid for tid in ground_cands if tid not in basic_core]
            if non_basic_esc:
                return sorted(set(non_basic_esc))
        elif not is_top:
            ground_cands = [
                tid for tid in ground_cands if tech_v2_map.get(tid, {}).get("kind") in (KIND_ESCAPE, "control")
            ] or ground_cands
            non_basic_esc = [tid for tid in ground_cands if tid not in basic_core]
            if non_basic_esc:
                return sorted(set(non_basic_esc))
        if ground_cands:
            return sorted(set(ground_cands))
        if TECH_STAND_UP in full_pool:
            return [TECH_STAND_UP]
        return [TECH_RETREAT if TECH_RETREAT in full_pool else TECH_STEP]

    if goal == "reset_to_home_range":
        reset_cands = [tid for tid in seq if tid in full_pool]
        if reset_cands:
            return sorted(set(reset_cands))

    cands: list[str] = []
    punch_kicks = set(load_model_v2().get("legacy", {}).get("simulation_config", {}).get("punch_range_kicks", []))
    for tid in full_pool:
        t = tech_v2_map.get(tid, {})
        kind = str(t.get("kind", ""))
        usage = str(t.get("usage", ""))
        if usage not in ("attack", "both", "movement") or kind == KIND_DEFENSE:
            continue
        if t.get("requires_wall") and not wall_near:
            continue
        req_grip = t.get("requires_grip")
        if req_grip and cur_grip not in req_grip:
            continue
        req_pos = t.get("requires_position")
        if req_pos == ["caught_single_leg"]:
            continue
        if checked_kicks and kind == "kick" and t.get("attack_lane") == "leg" and tid not in seq_set:
            continue
        if tid in basic_core:
            if tid not in seq_set and tid not in sig_set and not (tid == TECH_FEINT and goal == "counter_trap"):
                continue

        req_rng = t.get("required_range", [])
        if range_band == "kick":
            if "kick" in req_rng:
                cands.append(tid)
        elif range_band == "punch":
            if (
                "punch" in req_rng
                or "close" in req_rng
                or (
                    "kick" in req_rng
                    and kind in ("kick", "knee")
                    and tid in punch_kicks
                    and (goal == "leg_attrition" or str(active_plan.get("home_range")) == "kick")
                )
                or (att_dims.get("tie") is not None and "clinch" in req_rng and kind in ("grip", "takedown", "submission"))
            ):
                cands.append(tid)
        elif range_band == "clinch":
            if "clinch" in req_rng or "close" in req_rng:
                cands.append(tid)
        else:
            if range_band in req_rng:
                cands.append(tid)

    if not cands and range_band == "clinch":
        for tid in full_pool:
            t = tech_v2_map.get(tid, {})
            kind = str(t.get("kind", ""))
            usage = str(t.get("usage", ""))
            if usage not in ("attack", "both") or kind in (KIND_DEFENSE, KIND_MOVEMENT, KIND_ESCAPE, "takedown", "sweep"):
                continue
            if tid in basic_core and tid not in seq_set:
                continue
            req_rng = t.get("required_range", [])
            if "punch" in req_rng:
                cands.append(tid)

    # If at kick range in a punch/clinch slot with no kick-range attacks, allow non-shot slot attacks (they incur §7.8 kick-range penalty)
    if not cands and range_band == "kick":
        kick_blocked = set(load_model_v2().get("legacy", {}).get("simulation_config", {}).get("kick_range_blocked_shots", []))
        for tid in full_pool:
            if tid in kick_blocked:
                continue
            t = tech_v2_map.get(tid, {})
            kind = str(t.get("kind", ""))
            usage = str(t.get("usage", ""))
            if usage not in ("attack", "both") or kind in (KIND_DEFENSE, KIND_MOVEMENT, KIND_ESCAPE, "submission", KIND_GROUND_STRIKE, "control"):
                continue
            if tid in basic_core and tid not in seq_set:
                continue
            req_rng = t.get("required_range", [])
            if "punch" in req_rng or "close" in req_rng or "clinch" in req_rng:
                cands.append(tid)

    if cands:
        return sorted(set(cands))

    # Empty pool policy (§7.5)
    ladder = ["ground", "clinch", "close", "punch", "kick", "outside"]
    home_rng = str(active_plan.get("home_range", "punch"))
    if range_band in ladder and home_rng in ladder and range_band != home_rng:
        if ladder.index(home_rng) < ladder.index(range_band) and TECH_STEP in full_pool:
            return [TECH_STEP]
        if ladder.index(home_rng) > ladder.index(range_band) and TECH_RETREAT in full_pool:
            return [TECH_RETREAT]
    if range_band == "clinch" and TECH_CLINCH_BREAK in full_pool:
        return [TECH_CLINCH_BREAK]
    if TECH_STEP in full_pool:
        return [TECH_STEP]
    return [full_pool[0]] if full_pool else [TECH_STEP]


def score_and_select_technique_v2(
    k: Knowledge,
    att_card: dict[str, Any],
    def_card: dict[str, Any],
    active_plan: dict[str, Any],
    att_state: dict[str, Any],
    def_readiness: dict[str, float],
    range_band: str,
    ruleset: str,
    rng: random.Random,
    model_cfg: dict[str, Any],
    opt_behaviors: dict[str, dict[str, Any]],
    tech_v2_map: dict[str, dict[str, Any]],
) -> tuple[str, dict[str, Any], dict[str, Any] | None]:
    """Score candidate techniques using §7.5 model.selection features and sample via softmax(score / temperature)."""
    sel_cfg = model_cfg.get("selection", {})
    temperature = max(0.05, float(sel_cfg.get("temperature", 0.6)))
    weights = sel_cfg.get("weights", {})
    w_seq_next = float(weights.get("seq_next", 1.0))
    w_seq_other = float(weights.get("seq_other", 0.35))
    w_target_pref = float(weights.get("target_pref", 0.6))
    w_range_fit = float(weights.get("range_fit", 0.8))
    w_open_seam = float(weights.get("open_seam", 0.9))
    w_debt_exploit = float(weights.get("debt_exploit", 0.5))
    w_repeats = float(weights.get("repeats", -0.6))
    w_combo = float(weights.get("combo_follow_up", 0.7))
    w_sig = float(weights.get("signature", 0.3))
    w_mom = float(weights.get("momentum", 0.2))
    w_goal = float(weights.get("goal_alignment", 0.5))
    seam_thresh = float(sel_cfg.get("open_seam_readiness_below", 2.6))
    nonlane_map = model_cfg.get("readiness", {}).get("nonlane_lane_map", {"ground": "clinch", "space": None})
    nonlane_def = float(model_cfg.get("readiness", {}).get("nonlane_readiness_default", 3.0))

    candidates = build_candidate_pool_v2(att_card, active_plan, att_state, range_band, tech_v2_map)
    seq = list(active_plan.get("sequence", []))
    cursor = int(att_state.get("slot_Cursor", 0))
    pointed_idx = cursor % len(seq) if seq else 0
    pointed_tid = seq[pointed_idx] if seq else None
    if pointed_tid not in candidates and seq:
        for offset in range(1, len(seq)):
            cand_idx = (cursor + offset) % len(seq)
            alt_tid = seq[cand_idx]
            if alt_tid in candidates:
                pointed_idx = cand_idx
                pointed_tid = alt_tid
                break
    seq_set = set(seq)
    sig_set = set(att_card.get("signature_moves", []))
    goal = str(active_plan.get("goal", "head_damage"))

    att_dims = att_card.get("dimensions", {})
    target_opt = att_dims.get("target")
    kicking_opt = att_dims.get("kicking")
    mentality_opt = att_dims.get("mentality")
    target_fav = set(opt_behaviors.get(target_opt or "", {}).get("attack_profile", {}).get("favored_lanes", []))
    kick_fav = set(opt_behaviors.get(kicking_opt or "", {}).get("attack_profile", {}).get("favored_lanes", []))

    ment_meta = opt_behaviors.get(mentality_opt or "", {})
    sel_prof = ment_meta.get("selection_profile", {})
    post_risk = float(ment_meta.get("posture_profile", {}).get("risk_appetite", 1.0))
    risk_mult = 0.5 * (float(sel_prof.get("risk", 1.0)) + post_risk)
    max_combo_len = float(sel_prof.get("combo_length", 2.0))
    fight_mom = float(att_state.get("fight_momentum", 0.0))

    recent_3 = list(att_state.get("recent_moves", []))[-3:]
    slot_caps = set(active_plan.get("capabilities", []))
    unlocked = att_state.get("unlocked_abilities", [])
    if unlocked:
        for ab in att_card.get("conditional_abilities", []):
            if ab.get("id") in unlocked and ab.get("grants_capability"):
                slot_caps.add(str(ab["grants_capability"]))

    combos = _get_combos(k.root)
    combo_state = att_state.get("combo_state")
    opp_debt_tids = _compute_opp_debt_exploit_set(k, def_card, ruleset, range_band)

    scored: list[tuple[str, float, dict[str, Any] | None]] = []
    for tid in candidates:
        t = tech_v2_map.get(tid, {})
        kind = str(t.get("kind", ""))
        raw_lane = str(t.get("attack_lane", "head_straight"))
        mapped_lane = nonlane_map.get(raw_lane, raw_lane) if raw_lane in nonlane_map else raw_lane
        lane_rdy = float(def_readiness.get(mapped_lane, nonlane_def)) if mapped_lane else nonlane_def

        f_seq_next = 1.0 if tid == pointed_tid else 0.0
        f_seq_other = 1.0 if (tid in seq_set and f_seq_next == 0.0) else 0.0
        fav_set = (target_fav | kick_fav) if kind in ("kick", "knee") else target_fav
        f_target_pref = 1.0 if raw_lane in fav_set else 0.0

        req_rng = t.get("required_range", [])
        if req_rng and range_band == req_rng[0]:
            f_range_fit = 1.0
        else:
            f_range_fit = 0.6

        f_open_seam = 1.0 if lane_rdy < seam_thresh else 0.0
        f_debt = 1.0 if tid in opp_debt_tids else 0.0
        f_repeats = float(sum(1 for m in recent_3 if m == tid))

        matched_c = _match_combination(tid, slot_caps, combo_state, max_combo_len, combos)
        f_combo = 1.0 if matched_c is not None else 0.0
        f_sig = 1.0 if tid in sig_set else 0.0

        rec_pen = float(t.get("recovery_exposure", {}).get("readiness_penalty", 0.35))
        commit_val = min(1.0, rec_pen / 0.8)
        f_mom = fight_mom * commit_val * risk_mult
        f_goal = 1.0 if _satisfies_goal_predicate(goal, tid, t) else 0.0

        total_score = (
            w_seq_next * f_seq_next
            + w_seq_other * f_seq_other
            + w_target_pref * f_target_pref
            + w_range_fit * f_range_fit
            + w_open_seam * f_open_seam
            + w_debt_exploit * f_debt
            + w_repeats * f_repeats
            + w_combo * f_combo
            + w_sig * f_sig
            + w_mom * f_mom
            + w_goal * f_goal
        )
        scored.append((tid, total_score, matched_c))

    if len(scored) == 1:
        chosen_tid, _, chosen_combo = scored[0]
    else:
        max_s = max(s for _, s, _ in scored)
        exps = [math.exp((s - max_s) / temperature) for _, s, _ in scored]
        total_exp = sum(exps)
        u = rng.random() * total_exp
        acc = 0.0
        chosen_tid, _, chosen_combo = scored[-1]
        for (c_tid, _, c_combo), w in zip(scored, exps):
            acc += w
            if u <= acc:
                chosen_tid = c_tid
                chosen_combo = c_combo
                break

    if seq and chosen_tid == pointed_tid:
        att_state["slot_Cursor"] = pointed_idx + 1

    grant_cap = _granting_capability_for_attack(chosen_tid, slot_caps, tech_v2_map)
    selection_rec = {
        "candidates": [{"tid": c_tid, "score": round(c_score, 4)} for c_tid, c_score, _ in scored],
        "chosen": chosen_tid,
        "slot_id": str(active_plan["slot_id"]),
        "granting_capability": grant_cap,
    }
    return chosen_tid, selection_rec, chosen_combo


def select_counter_v2(
    k: Knowledge,
    def_card: dict[str, Any],
    att_card: dict[str, Any],
    def_plan: dict[str, Any],
    def_state: dict[str, Any],
    att_readiness: dict[str, float],
    def_avail: set[str],
    range_band: str,
    ruleset: str,
    rng: random.Random,
    model_cfg: dict[str, Any],
    opt_behaviors: dict[str, dict[str, Any]],
    tech_v2_map: dict[str, dict[str, Any]],
) -> str | None:
    """Select a counter-attack technique using the §7.5 scorer over trained techniques with usage in (counter, both, attack)."""
    sel_cfg = model_cfg.get("selection", {})
    temperature = max(0.05, float(sel_cfg.get("temperature", 0.6)))
    weights = sel_cfg.get("weights", {})
    seam_thresh = float(sel_cfg.get("open_seam_readiness_below", 2.6))
    nonlane_map = model_cfg.get("readiness", {}).get("nonlane_lane_map", {"ground": "clinch", "space": None})
    nonlane_def = float(model_cfg.get("readiness", {}).get("nonlane_readiness_default", 3.0))

    # Candidate pool for counters: active slot pool (plus any card counter-only techniques in def_avail) that reach at range_band
    slot_pool = set(def_plan.get("full_pool", def_avail))
    cands: list[str] = []
    for tid in sorted(def_avail):
        t = tech_v2_map.get(tid, {})
        kind = str(t.get("kind", ""))
        usage = str(t.get("usage", ""))
        if tid not in slot_pool and usage != "counter":
            continue
        if usage not in ("counter", "both", "attack") or kind in (KIND_DEFENSE, KIND_MOVEMENT, KIND_FEINT, KIND_ESCAPE):
            continue
        if float(t.get("base_damage", 0.0)) <= 0.0:
            continue
        req_rng = t.get("required_range", [])
        if (
            range_band in req_rng
            or (range_band == "punch" and "close" in req_rng)
            or (range_band == "clinch" and ("close" in req_rng or "punch" in req_rng))
            or (range_band == "kick" and "punch" in req_rng and kind not in ("takedown", "sweep", "submission", KIND_GROUND_STRIKE, "control"))
        ):
            cands.append(tid)

    if not cands:
        return None
    if len(cands) == 1:
        return cands[0]

    def_dims = def_card.get("dimensions", {})
    target_opt = def_dims.get("target")
    kicking_opt = def_dims.get("kicking")
    target_fav = set(opt_behaviors.get(target_opt or "", {}).get("attack_profile", {}).get("favored_lanes", []))
    kick_fav = set(opt_behaviors.get(kicking_opt or "", {}).get("attack_profile", {}).get("favored_lanes", []))
    seq = list(def_plan.get("sequence", []))
    seq_set = set(seq)
    sig_set = set(def_card.get("signature_moves", []))
    recent_3 = list(def_state.get("recent_moves", []))[-3:]
    opp_debt_tids = _compute_opp_debt_exploit_set(k, att_card, ruleset, range_band)

    scored: list[tuple[str, float]] = []
    for tid in cands:
        t = tech_v2_map.get(tid, {})
        kind = str(t.get("kind", ""))
        usage = str(t.get("usage", ""))
        raw_lane = str(t.get("attack_lane", "head_straight"))
        mapped_lane = nonlane_map.get(raw_lane, raw_lane) if raw_lane in nonlane_map else raw_lane
        lane_rdy = float(att_readiness.get(mapped_lane, nonlane_def)) if mapped_lane else nonlane_def

        # Counter-only techniques get seq_next weight when available as a counter
        f_seq = 1.0 if usage == "counter" else (1.0 if tid in seq_set else 0.0)
        w_seq_cnt = float(weights.get("seq_next", 1.0)) if usage == "counter" else float(weights.get("seq_other", 0.35))
        fav_set = (target_fav | kick_fav) if kind in ("kick", "knee") else target_fav
        f_target = 1.0 if raw_lane in fav_set else 0.0
        req_rng = t.get("required_range", [])
        f_rng = 1.0 if (req_rng and range_band == req_rng[0]) else 0.6
        f_seam = 1.0 if lane_rdy < seam_thresh else 0.0
        f_debt = 1.0 if tid in opp_debt_tids else 0.0
        f_rep = float(sum(1 for m in recent_3 if m == tid))
        f_sig = 1.0 if tid in sig_set else 0.0
        f_goal = 1.0 if (usage == "counter" or "recovery" in t.get("exploits_openings", [])) else 0.0

        sc = (
            w_seq_cnt * f_seq
            + float(weights.get("target_pref", 0.6)) * f_target
            + float(weights.get("range_fit", 0.8)) * f_rng
            + float(weights.get("open_seam", 0.9)) * f_seam
            + float(weights.get("debt_exploit", 0.5)) * f_debt
            + float(weights.get("repeats", -0.6)) * f_rep
            + float(weights.get("signature", 0.3)) * f_sig
            + float(weights.get("goal_alignment", 0.5)) * f_goal
        )
        scored.append((tid, sc))

    max_s = max(s for _, s in scored)
    exps = [math.exp((s - max_s) / temperature) for _, s in scored]
    tot = sum(exps)
    u = rng.random() * tot
    acc = 0.0
    for (c_tid, _), w in zip(scored, exps):
        acc += w
        if u <= acc:
            return c_tid
    return scored[-1][0]
