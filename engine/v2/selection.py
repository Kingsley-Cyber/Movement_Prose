"""Slot gameplan construction, trigger/abandon evaluation (§7.16), and technique selection for BLOCK Simulator v2."""

from __future__ import annotations

from typing import Any, Iterable

from ..capabilities import admitted_slots
from ..ontology import Knowledge
from .availability import slot_defense_pool_v2, slot_pool_v2
from .cards import compute_school_depth_multiplier
from .data import KIND_ESCAPE, load_capabilities_v2, load_model_v2, load_option_behaviors, load_techniques_v2


def _matches_slot_fallback(
    when: dict[str, Any],
    caps: set[str],
    slot_moves: list[str],
    kicking_opt: str,
    target_opt: str,
    mentality_opt: str | None,
) -> bool:
    if "caps_has" in when and when["caps_has"] not in caps:
        return False
    if "caps_has_any" in when and not any(c in caps for c in when["caps_has_any"]):
        return False
    if "slot_moves_has" in when and when["slot_moves_has"] not in slot_moves:
        return False
    if "kicking" in when and kicking_opt != when["kicking"]:
        return False
    if "target" in when and target_opt != when["target"]:
        return False
    if "mentality" in when and mentality_opt != when["mentality"]:
        return False
    return True


def build_slot_plans(
    k: Knowledge,
    card: dict[str, Any],
    ruleset: str = "mma",
    activated: Iterable[str] = (),
) -> list[dict[str, Any]]:
    """Build executable SlotPlan objects honoring card triggers, links, abandon rules, and per-slot pools (§6.0.3, §7.5)."""
    model_cfg = load_model_v2(k.root)
    sp_cfg = model_cfg.get("legacy", {}).get("slot_plans", {})
    default_opts = sp_cfg.get("default_options", {})
    karate_opt_id = sp_cfg.get("karate_option")
    excluded_tid = sp_cfg.get("excluded_technique")
    karate_mma_append = sp_cfg.get("karate_mma_append", [])
    empty_seq_fallback = sp_cfg.get("empty_sequence_fallback", [])
    fallback_orders = sp_cfg.get("fallback_orders", [])
    home_range_default = sp_cfg.get("home_range_default", {})

    tech_v2 = load_techniques_v2(k.root)
    opt_beh = load_option_behaviors(k.root)
    plans: list[dict[str, Any]] = []
    slots = admitted_slots(card, k)
    depth_mult = compute_school_depth_multiplier(card, k)
    kicking_opt = str(card["dimensions"].get("kicking") or default_opts.get("kicking", ""))
    target_opt = str(card["dimensions"].get("target") or default_opts.get("target", ""))
    mentality_opt = card["dimensions"].get("mentality")
    default_stalls = int(
        opt_beh.get(mentality_opt or "", {}).get("selection_profile", {}).get("switch_after_stalls", 2)
    )

    for idx, slot in enumerate(slots):
        caps = set(slot.get("capabilities", []))
        s_pool = slot_pool_v2(k, card, caps, ruleset, activated)
        non_counter_pool = {tid for tid in s_pool if tech_v2.get(tid, {}).get("usage") != "counter"}

        explicit_seq = [m for m in slot.get("sequence", []) if m in s_pool]
        if explicit_seq:
            clean_seq = explicit_seq
        else:
            t_lookup = {**tech_v2, **k.techniques}
            slot_moves = [
                tid
                for tid in card["active_techniques"]
                if tid in non_counter_pool
                and tid != excluded_tid
                and tid in t_lookup
                and t_lookup[tid]["kind"] in ("punch", "kick", "knee", "takedown", "grip", "control", "submission")
                and (set(t_lookup[tid]["required_capabilities"]) & caps)
            ]
            if "karate" in caps and kicking_opt == karate_opt_id and ruleset == "mma":
                for km in karate_mma_append:
                    if km in non_counter_pool and km not in slot_moves:
                        slot_moves.append(km)
            if not slot_moves:
                slot_moves = [
                    tid
                    for tid in sorted(non_counter_pool)
                    if tid in t_lookup and t_lookup[tid]["kind"] in ("punch", "kick", "takedown", "grip", KIND_ESCAPE, "movement")
                ]

            ordered_seq: list[str] = []
            for rule in fallback_orders:
                if _matches_slot_fallback(
                    rule.get("when", {}), caps, slot_moves, kicking_opt, target_opt, mentality_opt
                ):
                    order_spec = rule.get("order")
                    if order_spec == "slot_moves":
                        ordered_seq.extend(slot_moves)
                    else:
                        pool_mode = rule.get("pool", "slot_moves")
                        if pool_mode == "slot_moves_or_available":
                            ordered_seq.extend([m for m in order_spec if m in slot_moves or m in non_counter_pool])
                        else:
                            ordered_seq.extend([m for m in order_spec if m in slot_moves])
                    break

            seen_m: set[str] = set()
            clean_seq = []
            for m in ordered_seq + slot_moves:
                if m in non_counter_pool and m not in seen_m:
                    seen_m.add(m)
                    clean_seq.append(m)

        home_range = slot.get("home_range")
        if not home_range:
            home_range = str(home_range_default.get("else", "punch"))
            if any(c in caps for c in home_range_default.get("clinch", [])):
                home_range = "clinch"
            elif any(c in caps for c in home_range_default.get("kick", [])):
                home_range = "kick"

        abandon_rule = slot.get("abandon_rule") or {}
        max_stalls = int(
            abandon_rule.get("max_consecutive_stalls", 999 if len(slots) == 1 else default_stalls)
        )
        abandon_cond = str(abandon_rule.get("condition", "sequence_denied_or_countered"))
        links = list(slot.get("links") or [slots[(idx + 1) % len(slots)]["id"]])
        next_slot_id = links[0]
        goal = str(slot.get("goal", "head_damage"))
        reset_defs = (
            sorted(slot_defense_pool_v2(k, card, caps, ruleset, activated))
            if goal == "reset_to_home_range"
            else []
        )

        plans.append(
            {
                "slot_id": slot["id"],
                "slot_index": idx,
                "capabilities": sorted(caps),
                "sequence": clean_seq or [m for m in empty_seq_fallback if m in non_counter_pool] or sorted(non_counter_pool),
                "pool": sorted(non_counter_pool),
                "full_pool": sorted(s_pool),
                "reset_defenses": reset_defs,
                "home_range": home_range,
                "goal": goal,
                "depth_multiplier": depth_mult,
                "trigger": slot.get("trigger", "fight_start" if idx == 0 else "slot_stalled_or_countered"),
                "abandon_condition": abandon_cond,
                "abandon_threshold": max_stalls,
                "links": links,
                "next_slot_id": next_slot_id,
            }
        )
    return plans


def get_initial_slot_index(plans: list[dict[str, Any]]) -> int:
    """Return the index of the slot with trigger == 'fight_start' (or 0 if none)."""
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
    """Evaluate a slot trigger predicate against current fight state and recent exchanges (§7.16)."""
    thresh = model_cfg.get("slot_triggers", {}).get("thresholds", {})
    commit_min = float(thresh.get("commit_penalty_min", 0.45))
    hurt_head = float(thresh.get("hurt_head_damage", 6.0))
    late_frac = float(thresh.get("late_fight_fraction", 0.70))
    behind_margin = float(thresh.get("behind_margin", 1.0))

    basic_core = load_capabilities_v2().get("capabilities", {}).get("basic_movement", {}).get("core", [])
    circle_out_ids = set(basic_core[1:3])  # retreat, pivot

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
) -> None:
    """Update att_state['slot_stalls'] after an exchange according to the active slot's abandon_condition (§7.16)."""
    landed = outcome in ("partial", "clean", "flush", "counter_hit") and not counter_triggered
    failed = outcome in ("miss", "evaded", "blocked", "checked", "caught", "jammed") or counter_triggered
    tk = tech_v2_map.get(tid, {}).get("kind", "punch")

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
        # sequence_denied_or_countered (default)
        if failed:
            att_state["slot_stalls"] = int(att_state.get("slot_stalls", 0)) + 1
        elif landed:
            att_state["slot_stalls"] = 0


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
