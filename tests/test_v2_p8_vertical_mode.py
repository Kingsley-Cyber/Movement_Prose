"""Phase P8 tests: vertical mode gating (§7.13, §10.10, D14), airborne phases, frames & landing counter window."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import jsonschema

from engine.ontology import Knowledge
from engine.v2 import (
    available_v2,
    build_slot_plans,
    is_technique_vertically_allowed,
    load_card_v2,
    load_techniques_v2,
    simulate_fight_v2,
    slot_pool_v2,
)

ROOT = Path(__file__).resolve().parent.parent


def _airborne_technique_ids(k: Knowledge) -> set[str]:
    techs = load_techniques_v2(k.root)
    return {
        tid
        for tid, t in techs.items()
        if t.get("vertical_min", "grounded") != "grounded"
        or t.get("requires_airborne_training", False)
        or isinstance(t.get("airborne"), dict)
    }


def test_p8_zero_airborne_events_in_grounded_mode_and_untrained_cards() -> None:
    k = Knowledge()
    air_tids = _airborne_technique_ids(k)
    assert len(air_tids) == 11

    tkd = k.card(ROOT / "handoff_seed" / "style_templates" / "tpl_taekwondo.json")
    cap = k.card(ROOT / "handoff_seed" / "style_templates" / "tpl_capoeira.json")

    # 1. Under grounded mode, neither availability nor slot pools include any airborne techniques
    assert available_v2(k, tkd, "mma", vertical_mode="grounded") & air_tids == set()
    assert available_v2(k, cap, "street", vertical_mode="grounded") & air_tids == set()
    for p in build_slot_plans(k, tkd, "mma", vertical_mode="grounded"):
        assert set(p["full_pool"]) & air_tids == set()
        assert set(p["sequence"]) & air_tids == set()

    # 2. Simulate 20 fights in grounded mode between airborne-capable templates -> zero airborne events
    for seed in range(1, 21):
        res = simulate_fight_v2(tkd, cap, ruleset="street", vertical_mode="grounded", duration_s=60.0, seed=seed, knowledge=k)
        for ex in res["exchanges"]:
            assert ex["technique_id"] not in air_tids
            assert ex["state_changes"]["attacker_recovery_window"] != "airborne_landing_recovery"
            if ex.get("counter_followup"):
                assert ex["counter_followup"]["technique_id"] not in air_tids

    # 3. Strip airborne_training from tkd and cap and run in aerial mode -> zero airborne events
    tkd_untrained = copy.deepcopy(tkd)
    tkd_untrained["airborne_training"] = {"allowed_vertical_modes": ["grounded"], "techniques": []}
    cap_untrained = copy.deepcopy(cap)
    cap_untrained["airborne_training"] = {"allowed_vertical_modes": ["grounded", "athletic", "aerial"], "techniques": []}
    assert available_v2(k, tkd_untrained, "mma", vertical_mode="aerial") & air_tids == set()
    assert available_v2(k, cap_untrained, "street", vertical_mode="aerial") & air_tids == set()

    for seed in range(1, 15):
        res = simulate_fight_v2(
            tkd_untrained, cap_untrained, ruleset="street", vertical_mode="aerial", duration_s=60.0, seed=seed, knowledge=k
        )
        for ex in res["exchanges"]:
            assert ex["technique_id"] not in air_tids


def test_p8_athletic_and_aerial_gating_hierarchy() -> None:
    k = Knowledge()
    techs = load_techniques_v2(k.root)
    tkd = k.card(ROOT / "handoff_seed" / "style_templates" / "tpl_taekwondo.json")
    cap = k.card(ROOT / "handoff_seed" / "style_templates" / "tpl_capoeira.json")

    # Taekwondo has athletic airborne moves (double_roundhouse, tornado_kick, jumping_back_kick)
    av_tkd_grounded = available_v2(k, tkd, "mma", vertical_mode="grounded")
    av_tkd_athletic = available_v2(k, tkd, "mma", vertical_mode="athletic")
    assert {"double_roundhouse", "tornado_kick", "jumping_back_kick"}.isdisjoint(av_tkd_grounded)
    assert {"double_roundhouse", "tornado_kick", "jumping_back_kick"} <= av_tkd_athletic

    # Capoeira has au (athletic) and cartwheel_kick (aerial)
    av_cap_grounded = available_v2(k, cap, "street", vertical_mode="grounded")
    av_cap_athletic = available_v2(k, cap, "street", vertical_mode="athletic")
    av_cap_aerial = available_v2(k, cap, "street", vertical_mode="aerial")
    av_cap_wall = available_v2(k, cap, "street", vertical_mode="wall_assisted")

    assert "au" not in av_cap_grounded and "cartwheel_kick" not in av_cap_grounded
    assert "au" in av_cap_athletic and "cartwheel_kick" not in av_cap_athletic
    assert {"au", "cartwheel_kick"} <= av_cap_aerial
    assert av_cap_wall == av_cap_aerial

    assert is_technique_vertically_allowed(techs["cartwheel_kick"], cap, "athletic") is False
    assert is_technique_vertically_allowed(techs["cartwheel_kick"], cap, "aerial") is True


def test_p8_airborne_execution_frames_recovery_window_and_counter_rate() -> None:
    k = Knowledge()
    techs = load_techniques_v2(k.root)
    state_schema = json.loads((ROOT / "schemas" / "fight_state_v2.schema.json").read_text())
    event_schema = json.loads((ROOT / "schemas" / "exchange_event_v2.schema.json").read_text())

    # Build a dedicated airborne attacker card (Taekwondo slot 1 starting with airborne kicks) vs counter-fighter
    tkd_air = copy.deepcopy(k.card(ROOT / "handoff_seed" / "style_templates" / "tpl_taekwondo.json"))
    tkd_air["synchronized_capabilities"][0]["sequence"] = [
        "tornado_kick",
        "jumping_back_kick",
        "double_roundhouse",
    ]
    philly = load_card_v2(k, "philly")

    airborne_exchanges = []
    airborne_defended = 0
    airborne_countered = 0

    for seed in range(1, 45):
        res = simulate_fight_v2(
            tkd_air, philly, ruleset="mma", vertical_mode="athletic", duration_s=60.0, seed=seed, knowledge=k
        )
        if seed <= 3:
            jsonschema.validate(res["final_state_v2"], state_schema)
            for ex in res["exchanges"]:
                jsonschema.validate(ex, event_schema)
        for ex in res["exchanges"]:
            tid = ex["technique_id"]
            t_entry = techs.get(tid, {})
            air_cfg = t_entry.get("airborne")
            if isinstance(air_cfg, dict):
                airborne_exchanges.append(ex)
                fc = t_entry["frame_costs"]
                min_base_frames = (
                    max(1, int(fc["setup_frames"]) - 3)
                    + int(fc["execution_frames"])
                    + int(fc["contact_hold_frames"])
                    + int(fc["recovery_frames"])
                    + int(air_cfg["takeoff_frames"])
                    + int(air_cfg["apex_frames"])
                    + int(air_cfg["landing_frames"])
                )
                assert ex["frames"] >= min_base_frames
                assert ex["state_changes"]["attacker_recovery_window"] == "airborne_landing_recovery"
                if ex["outcome"] in ("evaded", "blocked", "jammed"):
                    airborne_defended += 1
                    if ex.get("counter_followup") is not None:
                        airborne_countered += 1

    assert len(airborne_exchanges) >= 25
    assert airborne_defended >= 10
    # Airborne attacks give +0.10 counter bonus on landing recovery
    assert airborne_countered / airborne_defended >= 0.25
