"""Pair-level grappling position graph, skill contests, scrambles, and staged submissions (§7.12, §8.3, §8.4)."""

from __future__ import annotations

import math
import random
from typing import Any

from .data import (
    KIND_ESCAPE,
    TECH_BODY_LOCK,
    TECH_CLINCH_BREAK,
    TECH_COLLAR_TIE,
    TECH_GUARD_PULL,
    TECH_KICK_CATCH,
    TECH_STAND_UP,
    TECH_SUBMISSION_ESCAPE,
    TECH_UNDERHOOK,
    get_attack_profile,
    load_capabilities_v2,
    load_model_v2,
    load_option_behaviors,
    load_positions_v2,
    load_techniques_v2,
)
from .defense import contest_roll
from .laterality import compute_dominance_deltas

CONTEST_SKILLS: dict[str, tuple[str, str]] = {
    "clinch_control": ("clinch_control", "clinch_control"),
    "clinch_escape": ("clinch_control", "clinch_control"),
    "takedown": ("takedown_offense", "takedown_defense"),
    "takedown_defense": ("takedown_defense", "takedown_offense"),
    "sweep": ("takedown_offense", "scramble"),
    TECH_GUARD_PULL: ("bottom_game", "top_control"),
    "scramble": ("scramble", "scramble"),
    "pass": ("top_control", "bottom_game"),
    "sweep_ground": ("bottom_game", "top_control"),
    KIND_ESCAPE: ("bottom_game", "top_control"),
    TECH_STAND_UP: (TECH_STAND_UP, "top_control"),
    "control": ("top_control", "bottom_game"),
    "submission": ("submission_offense", "submission_defense"),
}


def get_positions_map(root_positions: dict[str, Any] | None = None) -> dict[str, dict[str, Any]]:
    raw = root_positions if root_positions is not None else load_positions_v2()
    return {p["id"]: p for p in raw.get("positions", [])}


def normalize_position_id(pos_id: str, positions_map: dict[str, dict[str, Any]]) -> str:
    p = positions_map.get(pos_id, {})
    if p.get("status") == "deprecated" and p.get("alias_of"):
        return str(p["alias_of"])
    return pos_id


def compute_grappling_skill(
    card: dict[str, Any],
    actor_state: dict[str, Any],
    skill_name: str,
    opt_behaviors: dict[str, dict[str, Any]] | None = None,
    model_cfg: dict[str, Any] | None = None,
) -> float:
    """Compute a fighter's effective grappling skill (0-5 scale) from tie profile + option modifiers - active penalties (§8.4)."""
    beh = opt_behaviors if opt_behaviors is not None else load_option_behaviors()
    m_cfg = model_cfg if model_cfg is not None else load_model_v2()
    dims = card.get("dimensions", {})
    tie_id = dims.get("tie")
    if tie_id and tie_id in beh and "grappling_profile" in beh[tie_id]:
        prof = beh[tie_id]["grappling_profile"]
    else:
        prof = m_cfg.get("grappling", {}).get("null_tie_profile", {})

    val = float(prof.get(skill_name, 1.0))
    wall_near = actor_state.get("wall_proximity") == "near"
    for d in ("defense", "stance", "mentality", "hands", "kicking", "target"):
        oid = dims.get(d)
        if not oid or oid not in beh:
            continue
        ometa = beh[oid]
        cond = ometa.get("grappling_modifiers_condition", {})
        if cond.get("unless") == "wall_near" and wall_near:
            continue
        g_mods = ometa.get("grappling_modifiers", {})
        val += float(g_mods.get(skill_name, 0.0))

    for eff in actor_state.get("active_effects", []):
        if eff.get("effect") == "skill_penalty" and skill_name in eff.get("skills", []):
            val -= float(eff.get("value", 0.0))

    return val


def set_pair_position(
    pair_position: dict[str, Any],
    to_pos_id: str,
    actor_id: str,
    actor_role_after: str,
    opponent_id: str,
    actors: dict[str, dict[str, Any]],
    positions_map: dict[str, dict[str, Any]],
) -> str:
    """Update pair_position and synchronize both actors' grappling_position, role, posture_mode, and grips."""
    canon_pos = normalize_position_id(to_pos_id, positions_map)
    pos_meta = positions_map.get(canon_pos, positions_map.get("standing_neutral", {}))
    roles_list = list(pos_meta.get("roles", ["neutral", "neutral"]))
    if len(roles_list) >= 2:
        if actor_role_after == roles_list[0]:
            opp_role = roles_list[1]
        elif actor_role_after == roles_list[1]:
            opp_role = roles_list[0]
        else:
            actor_role_after = roles_list[0]
            opp_role = roles_list[1]
    else:
        opp_role = "neutral"

    pair_position["position_id"] = canon_pos
    pair_position["roles"] = {actor_id: actor_role_after, opponent_id: opp_role}

    att_st = actors[actor_id]
    opp_st = actors[opponent_id]
    att_st["grappling_position"] = canon_pos
    opp_st["grappling_position"] = canon_pos
    att_st["role"] = actor_role_after
    opp_st["role"] = opp_role

    domain = str(pos_meta.get("domain", "standing"))
    if domain == "ground" or canon_pos == "scramble":
        att_st["posture_mode"] = opp_st["posture_mode"] = "ground"
        att_st["grip"] = "top" if actor_role_after == "top" else ("bottom" if actor_role_after == "bottom" else None)
        opp_st["grip"] = "top" if opp_role == "top" else ("bottom" if opp_role == "bottom" else None)
    else:
        att_st["posture_mode"] = opp_st["posture_mode"] = "standing"
        att_st["submission_stage"] = opp_st["submission_stage"] = 0
        if canon_pos == "standing_neutral":
            att_st["grip"] = opp_st["grip"] = None
            att_st["sub_grips"] = {"underhooks": 0, "wrist_control": False, "head_position": "neutral"}
            opp_st["sub_grips"] = {"underhooks": 0, "wrist_control": False, "head_position": "neutral"}
        elif canon_pos in (TECH_COLLAR_TIE, "thai_plum", "front_headlock"):
            att_st["grip"], opp_st["grip"] = "collar", "controlled"
            att_st["sub_grips"]["head_position"] = "inside_control"
        elif canon_pos in ("front_body_lock", "standing_back_take"):
            att_st["grip"], opp_st["grip"] = TECH_BODY_LOCK, "controlled"
            att_st["sub_grips"]["underhooks"] = 2
        elif canon_pos == "wall_pinned":
            att_st["grip"], opp_st["grip"] = "single_tie", "controlled"
            att_st["sub_grips"]["underhooks"] = 1
        elif canon_pos in ("over_under", "double_underhooks"):
            att_st["grip"], opp_st["grip"] = "single_tie", "single_tie"
            att_st["sub_grips"]["underhooks"] = 2 if canon_pos == "double_underhooks" else 1
        elif canon_pos == "caught_single_leg":
            att_st["grip"], opp_st["grip"] = "single_tie", "controlled"

    return canon_pos


def find_transition_row(
    from_pos: str,
    actor_role: str,
    via_tid: str,
    transitions: list[dict[str, Any]],
    via_outcome_only: bool = False,
) -> dict[str, Any] | None:
    """Find a direct matching transition row from from_pos in data/positions.json."""
    for tr in transitions:
        if tr.get("from_position") != from_pos or tr.get("via_technique") != via_tid:
            continue
        has_vo = bool(tr.get("via_outcome"))
        if via_outcome_only != has_vo:
            continue
        tr_role = tr.get("actor_role", "any")
        if tr_role in ("any", actor_role) or (from_pos == "standing_neutral" and tr_role == "neutral"):
            return tr
    for tr in transitions:
        if tr.get("from_position") != from_pos or tr.get("via_technique") != via_tid:
            continue
        has_vo = bool(tr.get("via_outcome"))
        if via_outcome_only != has_vo:
            continue
        return tr
    return None


def find_transition_path(
    from_pos: str,
    actor_role: str,
    via_tid: str,
    transitions: list[dict[str, Any]],
) -> tuple[list[dict[str, str]], dict[str, Any] | None]:
    """Find a direct transition row or shortest valid graph path ending with via_tid in data/positions.json."""
    direct = find_transition_row(from_pos, actor_role, via_tid, transitions, via_outcome_only=False)
    if direct is not None:
        return (
            [{"from_position": from_pos, "to_position": str(direct["to_position"]), "via_technique": via_tid}],
            direct,
        )

    target_rows = [
        tr for tr in transitions if tr.get("via_technique") == via_tid and not tr.get("via_outcome")
    ]
    if not target_rows:
        return [], None

    # 1-hop bridge in transitions: from_pos -> mid_pos -> target_tr.from_position (when mid_pos == target_tr.from_position)
    for target_tr in target_rows:
        req_from = str(target_tr["from_position"])
        for br1 in transitions:
            if br1.get("via_outcome"):
                continue
            if br1.get("from_position") == from_pos and br1.get("to_position") == req_from:
                return (
                    [
                        {
                            "from_position": from_pos,
                            "to_position": req_from,
                            "via_technique": str(br1["via_technique"]),
                        },
                        {
                            "from_position": req_from,
                            "to_position": str(target_tr["to_position"]),
                            "via_technique": via_tid,
                        },
                    ],
                    target_tr,
                )

    # 2-hop bridge in transitions: from_pos -> mid1 -> req_from
    for target_tr in target_rows:
        req_from = str(target_tr["from_position"])
        for br1 in transitions:
            if br1.get("via_outcome") or br1.get("from_position") != from_pos:
                continue
            mid1 = str(br1["to_position"])
            for br2 in transitions:
                if br2.get("via_outcome"):
                    continue
                if br2.get("from_position") == mid1 and br2.get("to_position") == req_from:
                    return (
                        [
                            {
                                "from_position": from_pos,
                                "to_position": mid1,
                                "via_technique": str(br1["via_technique"]),
                            },
                            {
                                "from_position": mid1,
                                "to_position": req_from,
                                "via_technique": str(br2["via_technique"]),
                            },
                            {
                                "from_position": req_from,
                                "to_position": str(target_tr["to_position"]),
                                "via_technique": via_tid,
                            },
                        ],
                        target_tr,
                    )

    return [], None


def resolve_grappling_exchange_v2(
    pair_position: dict[str, Any],
    actor_id: str,
    opponent_id: str,
    actors: dict[str, dict[str, Any]],
    cards: dict[str, dict[str, Any]],
    tid: str,
    outcome: str,
    defense_used: str | None = None,
    rng: random.Random | None = None,
    opt_behaviors: dict[str, dict[str, Any]] | None = None,
    model_cfg: dict[str, Any] | None = None,
    positions_data: dict[str, Any] | None = None,
    tech_v2_map: dict[str, dict[str, Any]] | None = None,
) -> tuple[str, dict[str, Any] | None, dict[str, Any] | None]:
    """Resolve pair-level grappling transitions, contests, scrambles, and staged submissions (§7.12)."""
    m_cfg = model_cfg if model_cfg is not None else load_model_v2()
    beh = opt_behaviors if opt_behaviors is not None else load_option_behaviors()
    pos_raw = positions_data if positions_data is not None else load_positions_v2()
    positions_map = get_positions_map(pos_raw)
    transitions = pos_raw.get("transitions", [])
    t_map = tech_v2_map if tech_v2_map is not None else load_techniques_v2()
    t_entry = t_map.get(tid, {})
    kind = str(t_entry.get("kind", ""))

    att_st = actors[actor_id]
    opp_st = actors[opponent_id]
    att_card = cards[actor_id]
    opp_card = cards[opponent_id]

    cur_pos = normalize_position_id(str(pair_position.get("position_id", att_st.get("grappling_position", "standing_neutral"))), positions_map)
    cur_role = str(pair_position.get("roles", {}).get(actor_id, att_st.get("role") or "neutral"))

    g_cfg = m_cfg.get("grappling", {})
    slope = float(g_cfg.get("contest_slope", 0.9))
    lo, hi = g_cfg.get("probability_clamp", [0.08, 0.80])
    scram_margin = float(g_cfg.get("scramble_margin", 0.15))

    # 1. Handle failed attacks (defended takedown or clinch entry)
    if outcome not in ("clean", "flush", "counter_hit", "partial"):
        if defense_used:
            att_tr = find_transition_row(cur_pos, cur_role, tid, transitions, via_outcome_only=False)
            if att_tr is not None and att_tr.get("to_position") == "shot_in":
                def_tr = find_transition_row("shot_in", "defender", defense_used, transitions, via_outcome_only=False)
                if def_tr is not None:
                    to_p = str(def_tr["to_position"])
                    role_after = str(def_tr.get("actor_role_after", "neutral"))
                    new_pos = set_pair_position(pair_position, to_p, opponent_id, role_after, actor_id, actors, positions_map)
                    return (
                        new_pos,
                        {
                            "from_position": cur_pos,
                            "to_position": new_pos,
                            "via_technique": defense_used,
                            "intermediate_position": "shot_in",
                            "outcome": "defended",
                            "transitions": [
                                {"from_position": cur_pos, "to_position": "shot_in", "via_technique": tid},
                                {"from_position": "shot_in", "to_position": new_pos, "via_technique": defense_used},
                            ],
                        },
                        None,
                    )
            opp_cur_role = str(pair_position.get("roles", {}).get(opponent_id, opp_st.get("role") or "neutral"))
            def_direct_tr = find_transition_row(cur_pos, opp_cur_role, defense_used, transitions, via_outcome_only=False)
            if def_direct_tr is not None and def_direct_tr.get("from_position") == cur_pos:
                to_p = str(def_direct_tr["to_position"])
                role_after = str(def_direct_tr.get("actor_role_after", "neutral"))
                new_pos = set_pair_position(pair_position, to_p, opponent_id, role_after, actor_id, actors, positions_map)
                return (
                    new_pos,
                    {
                        "from_position": cur_pos,
                        "to_position": new_pos,
                        "via_technique": defense_used,
                        "outcome": "defended",
                        "transitions": [
                            {"from_position": cur_pos, "to_position": new_pos, "via_technique": defense_used}
                        ],
                    },
                    None,
                )
        gt_cfg = m_cfg.get("legacy", {}).get("grappling_transitions", {})
        if tid == gt_cfg.get("ride_id") and att_st.get("posture_mode") == "ground":
            new_pos = set_pair_position(pair_position, "standing_neutral", opponent_id, "neutral", actor_id, actors, positions_map)
            return (
                new_pos,
                {
                    "from_position": cur_pos,
                    "to_position": new_pos,
                    "via_technique": TECH_STAND_UP,
                    "outcome": "escaped_ride",
                    "transitions": [
                        {"from_position": cur_pos, "to_position": new_pos, "via_technique": TECH_STAND_UP}
                    ],
                },
                None,
            )
        return cur_pos, None, None

    # 2. Staged submissions (§7.12: 3 stages, contested per-stage escapes, failed-attempt transition rows)
    if kind == "submission":
        sub_cfg = g_cfg.get("submission", {})
        esc_bases = list(sub_cfg.get("escape_base_per_stage", [0.55, 0.40, 0.25]))
        fat_esc_pen = float(sub_cfg.get("fatigue_escape_penalty_per_point", 0.04))
        att_sub_off = compute_grappling_skill(att_card, att_st, "submission_offense", beh, m_cfg)
        opp_sub_def = compute_grappling_skill(opp_card, opp_st, "submission_defense", beh, m_cfg)
        opp_fat = float(opp_st.get("fatigue", 0.0))

        cur_stage = int(att_st.get("submission_stage", 0))
        if (att_sub_off - opp_sub_def) >= 2.5 and outcome in ("clean", "flush"):
            stages_to_test = 3 if outcome == "flush" else 2
        elif outcome == "flush":
            stages_to_test = 2
        else:
            stages_to_test = 1
        escaped = False
        stage_rolls: list[dict[str, Any]] = []

        for _ in range(stages_to_test):
            if cur_stage >= 3:
                break
            base_esc = float(esc_bases[min(cur_stage, len(esc_bases) - 1)])
            p_esc = max(0.05, min(0.90, base_esc + 0.08 * (opp_sub_def - att_sub_off) - fat_esc_pen * opp_fat))
            if rng is not None:
                esc_won, esc_roll, esc_p_eff = contest_roll(p_esc, band_name=TECH_SUBMISSION_ESCAPE, rng=rng, model_cfg=m_cfg)
            else:
                esc_won, esc_roll, esc_p_eff = False, 0.99, p_esc
            stage_rolls.append(
                {
                    "stage": cur_stage + 1,
                    "p_escape": round(esc_p_eff, 4),
                    "roll": round(esc_roll, 4),
                    "escaped": bool(esc_won),
                }
            )
            if esc_won:
                escaped = True
                break
            cur_stage += 1

        if escaped:
            att_st["submission_stage"] = 0
            opp_st["control_marks"] = int(opp_st.get("control_marks", 0)) + 1
            fail_tr = find_transition_row(cur_pos, cur_role, tid, transitions, via_outcome_only=True)
            if fail_tr is not None and fail_tr.get("from_position") == cur_pos:
                to_p = str(fail_tr["to_position"])
                role_after = str(fail_tr.get("actor_role_after", cur_role))
                new_pos = set_pair_position(pair_position, to_p, actor_id, role_after, opponent_id, actors, positions_map)
                tr_steps = [{"from_position": cur_pos, "to_position": new_pos, "via_technique": tid}]
            else:
                new_pos = cur_pos
                tr_steps = []
            sub_rec = {
                "technique_id": tid,
                "stage_reached": cur_stage,
                "escaped": True,
                "stage_rolls": stage_rolls,
                "position_after": new_pos,
            }
            return (
                new_pos,
                {
                    "from_position": cur_pos,
                    "to_position": new_pos,
                    "via_technique": tid,
                    "contest": "submission",
                    "escaped": True,
                    "transitions": tr_steps,
                },
                sub_rec,
            )

        att_st["submission_stage"] = cur_stage
        att_st["sub_grips"]["wrist_control"] = True
        att_st["control_marks"] = int(att_st.get("control_marks", 0)) + 1
        sub_rec = {
            "technique_id": tid,
            "stage_reached": cur_stage,
            "escaped": False,
            "stage_rolls": stage_rolls,
            "position_after": cur_pos,
        }
        return (
            cur_pos,
            {
                "from_position": cur_pos,
                "to_position": cur_pos,
                "via_technique": tid,
                "contest": "submission",
                "stage": cur_stage,
                "transitions": [],
            },
            sub_rec,
        )

    # 3. Look up transition row or graph path in data/positions.json (or via technique result_position)
    path_steps, tr = find_transition_path(cur_pos, cur_role, tid, transitions)
    res_pos = t_entry.get("result_position")
    if tr is None and res_pos is None and kind not in ("grip", "takedown", "sweep", "control", KIND_ESCAPE):
        return cur_pos, None, None

    contest_type = (
        str(
            tr.get(
                "contest",
                "clinch_control"
                if kind == "grip"
                else ("takedown" if kind == "takedown" else ("sweep" if kind == "sweep" else (TECH_STAND_UP if kind == KIND_ESCAPE else "control"))),
            )
        )
        if tr
        else (
            "clinch_control"
            if kind == "grip"
            else ("takedown" if kind == "takedown" else ("sweep" if kind == "sweep" else (TECH_STAND_UP if kind == KIND_ESCAPE else "control")))
        )
    )
    att_skill_name, opp_skill_name = CONTEST_SKILLS.get(contest_type, ("clinch_control", "clinch_control"))
    att_skill = compute_grappling_skill(att_card, att_st, att_skill_name, beh, m_cfg)
    opp_skill = compute_grappling_skill(opp_card, opp_st, opp_skill_name, beh, m_cfg)
    if contest_type == "sweep":
        att_tie = opp_card["dimensions"].get("tie")
        att_stance = opp_card["dimensions"].get("stance")
        opp_skill += float(get_attack_profile(att_tie, beh).get("sweep_resistance", 0.0)) + float(
            get_attack_profile(att_stance, beh).get("sweep_resistance", 0.0)
        )

    fat_pen = float(g_cfg.get("fatigue_penalty_per_point", 0.08))
    modifiers = -fat_pen * (float(att_st.get("fatigue", 0.0)) - float(opp_st.get("fatigue", 0.0)))
    grip_bonus = g_cfg.get("grip_bonus", {})
    uh = int(att_st.get("sub_grips", {}).get("underhooks", 0))
    if uh >= 2:
        modifiers += float(grip_bonus.get("double_underhooks", 0.45))
    elif uh == 1:
        modifiers += float(grip_bonus.get(TECH_UNDERHOOK, 0.25))
    if att_st.get("sub_grips", {}).get("wrist_control"):
        modifiers += float(grip_bonus.get("wrist_control", 0.3))
    if att_st.get("sub_grips", {}).get("head_position") == "inside_control":
        modifiers += float(grip_bonus.get("head_inside", 0.3))

    pos_bonus = g_cfg.get("position_advantage_bonus", {})
    if cur_role == "top":
        modifiers += float(pos_bonus.get("top", 0.3))
    elif cur_role == "back_controller":
        modifiers += float(pos_bonus.get("back_controller", 0.4))
    elif cur_role in ("tier", "plum_holder", "locker", "pinner", "controller", "dominant"):
        modifiers += float(pos_bonus.get("dominant_clinch", 0.25))

    wall_bonus = g_cfg.get("wall_bonus", {})
    if contest_type == "takedown" and opp_st.get("wall_proximity") == "near":
        modifiers += float(wall_bonus.get("pinner_takedown", 0.4))
    elif contest_type == TECH_STAND_UP and att_st.get("wall_proximity") == "near":
        modifiers += float(wall_bonus.get("pinned_wall_walk", 0.3))

    lat_g_delta, _ = compute_dominance_deltas(att_card, att_st, t_entry, m_cfg)
    modifiers += lat_g_delta

    logit = slope * (att_skill - opp_skill + modifiers)
    p_trans = max(float(lo), min(float(hi), 1.0 / (1.0 + math.exp(-logit))))
    if rng is not None:
        won_tr, tr_roll, tr_p_eff = contest_roll(p_trans, band_name="grappling", rng=rng, model_cfg=m_cfg)
    else:
        won_tr, tr_roll, tr_p_eff = True, 0.1, p_trans

    tr_steps: list[dict[str, str]] = []
    intermediate_pos: str | None = None

    # Determine target position & role
    if tr is not None:
        to_pos = str(tr["to_position"])
        role_after = str(tr.get("actor_role_after", "neutral"))
        prefix_steps = path_steps[:-1]
        last_from = str(tr["from_position"])
        # If double_leg/single_leg enters shot_in, immediately chain shot_in -> half_guard (or scramble within scramble_margin)
        if to_pos == "shot_in":
            intermediate_pos = "shot_in"
            tr_steps.extend(path_steps)
            scram_tr = find_transition_row("shot_in", "shooter", tid, transitions, via_outcome_only=True)
            fin_tr = find_transition_row("shot_in", "shooter", tid, transitions, via_outcome_only=False)
            if abs(tr_roll - tr_p_eff) < scram_margin and scram_tr is not None:
                to_pos = str(scram_tr["to_position"])
                role_after = str(scram_tr.get("actor_role_after", "neutral"))
                tr_steps.append({"from_position": "shot_in", "to_position": to_pos, "via_technique": tid})
            elif fin_tr is not None:
                to_pos = str(fin_tr["to_position"])
                role_after = str(fin_tr.get("actor_role_after", "top"))
                tr_steps.append({"from_position": "shot_in", "to_position": to_pos, "via_technique": tid})
        else:
            vo_tr = find_transition_row(last_from, cur_role, tid, transitions, via_outcome_only=True)
            if abs(tr_roll - tr_p_eff) < scram_margin and vo_tr is not None and vo_tr.get("from_position") == last_from:
                to_pos = str(vo_tr["to_position"])
                role_after = str(vo_tr.get("actor_role_after", cur_role))
                tr_steps.extend(prefix_steps)
                tr_steps.append({"from_position": last_from, "to_position": to_pos, "via_technique": tid})
            elif not won_tr and (
                contest_type in ("pass", "sweep_ground")
                or (contest_type == TECH_STAND_UP and cur_pos == "closed_guard" and cur_role == "top")
            ):
                return (
                    cur_pos,
                    {
                        "from_position": cur_pos,
                        "to_position": cur_pos,
                        "via_technique": tid,
                        "contest": contest_type,
                        "p_success": round(tr_p_eff, 4),
                        "roll": round(tr_roll, 4),
                        "succeeded": False,
                        "transitions": [],
                    },
                    None,
                )
            else:
                tr_steps.extend(path_steps)
    elif res_pos:
        to_pos = str(res_pos)
        p_meta = positions_map.get(normalize_position_id(to_pos, positions_map), {})
        r_list = p_meta.get("roles", ["neutral", "neutral"])
        role_after = str(r_list[0]) if r_list else "neutral"
    else:
        return cur_pos, None, None

    new_pos = set_pair_position(pair_position, to_pos, actor_id, role_after, opponent_id, actors, positions_map)

    grap_rec: dict[str, Any] = {
        "from_position": cur_pos,
        "to_position": new_pos,
        "via_technique": tid,
        "contest": contest_type,
        "actor_role_after": pair_position["roles"][actor_id],
        "p_success": round(tr_p_eff, 4),
        "roll": round(tr_roll, 4),
        "succeeded": True,
        "transitions": tr_steps,
    }
    if intermediate_pos:
        grap_rec["intermediate_position"] = intermediate_pos
    return new_pos, grap_rec, None


def accrue_control_time(
    pair_position: dict[str, Any],
    actors: dict[str, dict[str, Any]],
    duration_s: float,
    positions_data: dict[str, Any] | None = None,
) -> None:
    """Accrue control_time_s for each actor based on position control_value_per_second (§7.12)."""
    pos_map = get_positions_map(positions_data)
    pos_id = normalize_position_id(str(pair_position.get("position_id", "standing_neutral")), pos_map)
    p_meta = pos_map.get(pos_id, {})
    ctrl_vals = p_meta.get("control_value_per_second", {})
    roles = pair_position.get("roles", {})
    for fid, st in actors.items():
        r = str(roles.get(fid, st.get("role") or "neutral"))
        rate = float(ctrl_vals.get(r, 0.0))
        if rate > 0.0 and duration_s > 0.0:
            st["control_time_s"] = round(float(st.get("control_time_s", 0.0)) + rate * duration_s, 3)


def update_grappling_position(
    actor_state: dict[str, Any],
    defender_state: dict[str, Any],
    tid: str,
    outcome: str,
    actor_card: dict[str, Any],
) -> str:
    """Backward-compatible wrapper around resolve_grappling_exchange_v2."""
    pair_pos = {
        "position_id": str(actor_state.get("grappling_position", "standing_neutral")),
        "roles": {
            "att": str(actor_state.get("role") or ("top" if actor_state.get("grip") == "top" else ("bottom" if actor_state.get("grip") == "bottom" else "neutral"))),
            "def": str(defender_state.get("role") or ("top" if defender_state.get("grip") == "top" else ("bottom" if defender_state.get("grip") == "bottom" else "neutral"))),
        },
    }
    def_card = {"dimensions": {}}
    actors = {"att": actor_state, "def": defender_state}
    cards = {"att": actor_card, "def": def_card}
    new_pos, _, _ = resolve_grappling_exchange_v2(
        pair_pos, "att", "def", actors, cards, tid, outcome, rng=None
    )
    return new_pos
