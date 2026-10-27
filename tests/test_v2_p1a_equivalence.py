"""Phase P1a verification tests: single source of truth, defense selector equivalence, and wall_assisted alias."""

from __future__ import annotations

import ast
import json
import random
from pathlib import Path

from engine.ontology import ROOT, Knowledge
from engine.simulator_v2 import (
    KICK_IDS,
    MOVE_BASE_STATS,
    load_card_v2,
    normalize_vertical_mode,
    select_kick_defense,
    select_native_defense,
    simulate_fight_v2,
    simulate_many_v2,
)
import simulate_fight


def _legacy_select_kick_defense(
    defender_card: dict,
    kick_tid: str,
    range_band: str,
    lane_readiness: float = 3.5,
    attacker_card: dict | None = None,
    rng: random.Random | None = None,
    opt_behaviors: dict | None = None,
    wall_proximity: str = "far",
) -> tuple[str, str]:
    beh = opt_behaviors or {}
    def_opt = defender_card["dimensions"].get("defense") or ""
    kick_opt = defender_card["dimensions"].get("kicking") or ""

    if kick_tid in ("body_kick", "low_kick", "switch_kick", "teep", "side_kick") and (
        kick_opt == "kicking.sanda" or def_opt == "defense.parry_catch"
    ):
        if rng is None:
            if kick_tid in ("body_kick", "low_kick", "switch_kick"):
                return "kick_catch", "caught"
        else:
            base_catch = 0.44 if kick_tid in ("body_kick", "switch_kick") else (0.32 if kick_tid in ("teep", "side_kick") else 0.18)
            def_catch_bonus = (
                float(beh.get(kick_opt, {}).get("attack_profile", {}).get("kick_catch_bonus", 0.0))
                + float(beh.get(def_opt, {}).get("attack_profile", {}).get("kick_catch_bonus", 0.0))
            )
            att_kick_opt = (attacker_card or {}).get("dimensions", {}).get("kicking") or ""
            retract_mod = float(beh.get(att_kick_opt, {}).get("attack_profile", {}).get("kick_retraction_delta", 0.0))
            catch_prob = max(0.10, min(0.65, base_catch + def_catch_bonus + retract_mod + 0.05 * (lane_readiness - 3.0)))
            if rng.random() < catch_prob:
                return "kick_catch", "caught"

    if kick_tid in ("low_kick", "body_kick", "switch_kick") and def_opt == "defense.check_frame":
        return "check", "checked"
    if def_opt == "defense.outfight" and kick_tid in ("low_kick", "body_kick", "head_kick", "spinning_back_kick", "teep", "side_kick"):
        if wall_proximity == "near":
            return "shell_block", "blocked"
        return "evade_step_back", "evaded"
    if def_opt in ("defense.slip_roll", "defense.shoulder_roll") and kick_tid in ("head_kick", "axe_kick"):
        return "lean_back", "evaded"
    if def_opt in ("defense.smother", "defense.sprawl_pummel") and kick_tid in ("teep", "body_kick", "spinning_back_kick"):
        return "jam_step", "jammed"
    if def_opt == "defense.block_absorb":
        return "retreat", "blocked"
    return "shell_block", "blocked"


def _legacy_select_native_defense(
    defender_card: dict,
    incoming_tid: str,
    range_band: str,
    avail_def: set[str],
    wall_proximity: str = "far",
) -> tuple[str, str]:
    def_opt = defender_card["dimensions"].get("defense") or "defense.block_absorb"
    hands_opt = defender_card["dimensions"].get("hands") or "hands.high_guard"

    if incoming_tid in ("double_leg", "single_leg", "outside_trip", "sanda_sweep", "body_lock", "collar_tie", "wall_tie", "guard_pull"):
        if def_opt == "defense.sprawl_pummel":
            if "sprawl" in avail_def and incoming_tid in ("double_leg", "single_leg"):
                return "sprawl", "evaded"
            if "pummel" in avail_def:
                return "pummel", "blocked"
        elif def_opt == "defense.smother":
            if "pummel" in avail_def:
                return "pummel", "jammed"
            if "wall_tie" in avail_def:
                return "wall_tie", "jammed"
        elif def_opt == "defense.outfight":
            if wall_proximity == "near":
                return ("shell_block" if "shell_block" in avail_def else "retreat"), "blocked"
            return ("pivot" if "pivot" in avail_def else "retreat"), "evaded"
        elif def_opt == "defense.check_frame":
            if "shield_frame" in avail_def:
                return "shield_frame", "blocked"
        if "sprawl" in avail_def and incoming_tid in ("double_leg", "single_leg"):
            return "sprawl", "evaded"
        if "pummel" in avail_def:
            return "pummel", "blocked"
        return "retreat", "evaded"

    if def_opt == "defense.parry_catch":
        if incoming_tid in ("jab", "cross", "teep", "haymaker") and "parry" in avail_def:
            return "parry", "evaded"
        return ("shell_block" if "shell_block" in avail_def else "retreat"), "blocked"
    if def_opt in ("defense.slip_roll", "defense.shoulder_roll"):
        if "slip" in avail_def:
            return "slip", "evaded"
        return ("pivot" if "pivot" in avail_def else "retreat"), "evaded"
    if def_opt == "defense.outfight":
        if wall_proximity == "near":
            return ("shell_block" if "shell_block" in avail_def else "retreat"), "blocked"
        return ("pivot" if ("pivot" in avail_def and incoming_tid in ("jab", "cross")) else "retreat"), "evaded"
    if def_opt == "defense.check_frame":
        if "shield_frame" in avail_def:
            return "shield_frame", "blocked"
        if hands_opt == "hands.long_guard":
            return "retreat", "evaded"
        return ("shell_block" if "shell_block" in avail_def else "retreat"), "blocked"
    if def_opt == "defense.smother":
        if "pummel" in avail_def:
            return "pummel", "jammed"
        if "shield_frame" in avail_def:
            return "shield_frame", "blocked"
        return "step", "jammed"
    if def_opt == "defense.sprawl_pummel":
        if hands_opt == "hands.philly_shell" and "slip" in avail_def:
            return "slip", "evaded"
        return ("shell_block" if "shell_block" in avail_def else "retreat"), "blocked"

    if "shell_block" in avail_def:
        return "shell_block", "blocked"
    return "retreat", "blocked"


def test_data_driven_defense_selectors_match_legacy_exhaustively():
    opt_raw = json.loads((ROOT / "data/option_behaviors.json").read_text(encoding="utf-8"))["options"]
    opt_map = {o["id"]: o for o in opt_raw}
    def_opts = [o["id"] for o in opt_raw if o["dimension"] == "defense"] + [None]
    kick_opts = [o["id"] for o in opt_raw if o["dimension"] == "kicking"] + [None]
    hands_opts = [o["id"] for o in opt_raw if o["dimension"] == "hands"] + [None]
    all_tids = sorted(MOVE_BASE_STATS.keys())

    avail_subsets = [
        set(),
        {"shell_block"},
        {"slip", "pivot"},
        {"parry", "shell_block"},
        {"sprawl", "pummel", "wall_tie", "shield_frame"},
        {"sprawl", "pummel", "wall_tie", "shield_frame", "shell_block", "slip", "pivot", "parry"},
    ]

    for d_opt in def_opts:
        for h_opt in hands_opts:
            card = {"dimensions": {"defense": d_opt, "hands": h_opt, "kicking": "kicking.none"}}
            for tid in all_tids:
                for wall in ("far", "near"):
                    for avail in avail_subsets:
                        assert select_native_defense(card, tid, "punch", avail, wall_proximity=wall) == _legacy_select_native_defense(
                            card, tid, "punch", avail, wall_proximity=wall
                        )

    for d_opt in def_opts:
        for k_opt in kick_opts:
            card = {"dimensions": {"defense": d_opt, "kicking": k_opt}}
            att_card = {"dimensions": {"kicking": "kicking.karate"}}
            for kick_tid in sorted(KICK_IDS):
                for wall in ("far", "near"):
                    assert select_kick_defense(card, kick_tid, "kick", wall_proximity=wall, opt_behaviors=opt_map) == _legacy_select_kick_defense(
                        card, kick_tid, "kick", wall_proximity=wall, opt_behaviors=opt_map
                    )
                    rng1 = random.Random(19)
                    rng2 = random.Random(19)
                    assert select_kick_defense(
                        card, kick_tid, "kick", lane_readiness=3.4, attacker_card=att_card, rng=rng1, opt_behaviors=opt_map, wall_proximity=wall
                    ) == _legacy_select_kick_defense(
                        card, kick_tid, "kick", lane_readiness=3.4, attacker_card=att_card, rng=rng2, opt_behaviors=opt_map, wall_proximity=wall
                    )


def test_vertical_mode_wall_assisted_normalized_to_aerial(capsys):
    k = Knowledge()
    assert normalize_vertical_mode("wall_assisted") == "aerial"
    assert normalize_vertical_mode("aerial") == "aerial"
    assert normalize_vertical_mode("athletic") == "athletic"
    assert normalize_vertical_mode("grounded") == "grounded"

    r1 = simulate_fight_v2("sanda_judo", "thai", seed=7, vertical_mode="wall_assisted", knowledge=k)
    r2 = simulate_fight_v2("sanda_judo", "thai", seed=7, vertical_mode="aerial", knowledge=k)
    assert r1["vertical_mode"] == "aerial"
    assert r1["final_state_v2"]["vertical_mode"] == "aerial"
    assert r1 == r2

    m1 = simulate_many_v2("sanda_judo", "thai", runs=3, vertical_mode="wall_assisted", knowledge=k)
    assert m1["vertical_mode"] == "aerial"

    rc = simulate_fight.main(["sanda_judo", "thai", "--seed", "7", "--vertical-mode", "wall_assisted", "--json"])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["vertical_mode"] == "aerial"


def test_zero_disallowed_literals_in_engine_v2():
    option_ids = {o["id"] for o in json.loads((ROOT / "data/option_behaviors.json").read_text())["options"]}
    tech_ids = {t["id"] for t in json.loads((ROOT / "data/techniques_v2.json").read_text())["techniques"]}
    fighter_ids = {p.stem for p in (ROOT / "cards/v2").glob("*.json")}

    v2_dir = ROOT / "engine" / "v2"
    targets = [p for p in sorted(v2_dir.glob("*.py")) if p.name not in ("__init__.py", "data.py")]
    assert len(targets) >= 10

    violations = []
    for path in targets:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        docstring_nodes = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if (
                    node.body
                    and isinstance(node.body[0], ast.Expr)
                    and isinstance(node.body[0].value, ast.Constant)
                    and isinstance(node.body[0].value.value, str)
                ):
                    docstring_nodes.add(node.body[0].value)
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str) and node not in docstring_nodes:
                val = node.value
                if val in fighter_ids and val not in ("street", "karate"):
                    violations.append((path.name, node.lineno, "fighter_id", val))
                elif val in option_ids:
                    violations.append((path.name, node.lineno, "option_id", val))
                elif val in tech_ids:
                    violations.append((path.name, node.lineno, "technique_id", val))

    assert violations == [], f"Disallowed literals found in engine/v2/: {violations}"
