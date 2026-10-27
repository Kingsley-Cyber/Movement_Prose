"""Phase P9 tests: flash knockdowns, stuns, standing counts, per-round decision scoring & canonical tie-breaks (§7.14, D4, D16)."""

from __future__ import annotations

import copy
import json
import random
from pathlib import Path

import jsonschema

from engine.ontology import Knowledge
from engine.v2 import (
    compute_readiness_profile,
    evaluate_decision_winner,
    load_card_v2,
    load_model_v2,
    load_option_behaviors,
    load_rulesets_v2,
    load_techniques_v2,
    simulate_fight_v2,
)
from engine.v2.finishes import (
    check_and_resolve_flash_knockdown,
    check_finish_conditions,
    compute_decision_scores,
)

ROOT = Path(__file__).resolve().parent.parent


def test_p9_flash_knockdown_stun_readiness_penalty_and_standing_count() -> None:
    k = Knowledge()
    model_cfg = load_model_v2(k.root)
    opt_beh = load_option_behaviors(k.root)
    rulesets = load_rulesets_v2(k.root)["rulesets"]
    niran = load_card_v2(k, "thai")
    donnell = load_card_v2(k, "donnell")

    base_state = {
        "posture_mode": "standing",
        "balance": "stable",
        "grip": None,
        "sub_grips": {"underhooks": 0},
        "wall_proximity": "far",
        "damage": {"head": 8.0, "body": 0.0, "leg": 0.0},
        "fatigue": 1.0,
        "stun_exchanges": 0,
        "knockdowns": 0,
        "knockdowns_round": 0,
        "knockdowns_total": 0,
        "fight_momentum": 0.0,
        "recovery_window": {"window_type": "none", "last_technique_id": None, "exposed_lanes": [], "readiness_penalty": 0.0},
        "attention": {"focus_line": "neutral", "feinted": False, "outside_angle_conceded": False},
        "read_memory": {"seen_counts": {}, "consecutive_same_move_by_opponent": 0},
    }
    att_state = copy.deepcopy(base_state)
    def_state = copy.deepcopy(base_state)

    r_unstunned = compute_readiness_profile(
        k, niran, def_state, donnell, att_state, "punch", "closed_stance", opt_behaviors=opt_beh, model_cfg=model_cfg
    )

    dmg_info = {"final_damage": 2.5, "damage_type": "impact", "target_region": "head"}
    # With head_dmg = 8.0 (> 4.0) and flush (+0.08), p_kd = 0.04*(4.0) + 0.08 = 0.24
    triggered = False
    for s in range(1, 30):
        st_att = copy.deepcopy(att_state)
        st_def = copy.deepcopy(def_state)
        kd, sc, stun = check_and_resolve_flash_knockdown(
            dmg_info,
            "flush",
            st_att,
            st_def,
            ruleset_cfg=rulesets["boxing"],
            model_cfg=model_cfg,
            rng=random.Random(s),
        )
        if kd:
            triggered = True
            assert stun is True
            assert st_def["stun_exchanges"] == 2
            assert st_def["knockdowns"] == 1
            assert st_def["knockdowns_round"] == 1
            assert sc is not None and "p_recover" in sc and "recovered" in sc
            assert st_att["fight_momentum"] > 0.0 and st_def["fight_momentum"] < 0.0
            r_stunned = compute_readiness_profile(
                k, niran, st_def, donnell, st_att, "punch", "closed_stance", opt_behaviors=opt_beh, model_cfg=model_cfg
            )
            assert r_stunned["head_straight"] < r_unstunned["head_straight"] - 0.35
            break
    assert triggered


def test_p9_per_round_decision_scoring_and_canonical_coin_tiebreak() -> None:
    k = Knowledge()
    model_cfg = load_model_v2(k.root)
    rulesets = load_rulesets_v2(k.root)["rulesets"]
    tech_map = load_techniques_v2(k.root)

    canonical_ids = ["detroit", "philly"]
    actors = {
        "detroit": {"damage": {"head": 5.0, "body": 0.0, "leg": 0.0}, "control_marks": 0},
        "philly": {"damage": {"head": 4.0, "body": 0.0, "leg": 0.0}, "control_marks": 0},
    }
    # Round 1 & Round 2 won narrowly by detroit; Round 3 won big by philly -> detroit wins 2 rounds to 1
    exchanges = [
        {
            "round": 1,
            "t_start": 0.0,
            "t_end": 1.0,
            "attacker_id": "detroit",
            "defender_id": "philly",
            "technique_id": "cross",
            "outcome": "clean",
            "damage": {"final_damage": 2.0},
            "grappling_position": "standing_neutral",
            "state_changes": {
                "attacker_damage": {"head": 0.0, "body": 0.0, "leg": 0.0},
                "defender_damage": {"head": 2.0, "body": 0.0, "leg": 0.0},
            },
        },
        {
            "round": 2,
            "t_start": 180.0,
            "t_end": 181.0,
            "attacker_id": "detroit",
            "defender_id": "philly",
            "technique_id": "cross",
            "outcome": "clean",
            "damage": {"final_damage": 2.0},
            "grappling_position": "standing_neutral",
            "state_changes": {
                "attacker_damage": {"head": 0.0, "body": 0.0, "leg": 0.0},
                "defender_damage": {"head": 4.0, "body": 0.0, "leg": 0.0},
            },
        },
        {
            "round": 3,
            "t_start": 360.0,
            "t_end": 361.0,
            "attacker_id": "philly",
            "defender_id": "detroit",
            "technique_id": "cross",
            "outcome": "flush",
            "damage": {"final_damage": 8.0},
            "grappling_position": "standing_neutral",
            "state_changes": {
                "attacker_damage": {"head": 4.0, "body": 0.0, "leg": 0.0},
                "defender_damage": {"head": 8.0, "body": 0.0, "leg": 0.0},
            },
        },
    ]
    dec = compute_decision_scores(
        canonical_ids, actors, exchanges=exchanges, ruleset_cfg=rulesets["boxing"], model_cfg=model_cfg, tech_v2_map=tech_map
    )
    assert dec["rounds_won"] == {"detroit": 2, "philly": 1}
    assert dec["totals"]["philly"] > dec["totals"]["detroit"]
    winner_id, _ = evaluate_decision_winner(
        canonical_ids, actors, model_cfg, exchanges=exchanges, ruleset_cfg=rulesets["boxing"], rng=random.Random(1), tech_v2_map=tech_map
    )
    assert winner_id == "detroit"

    # Exact tiebreak test: identical scores -> seeded coin in canonical order (both fighters win across seeds)
    tied_actors = {
        "detroit": {"damage": {"head": 0.0, "body": 0.0, "leg": 0.0}, "control_marks": 0},
        "philly": {"damage": {"head": 0.0, "body": 0.0, "leg": 0.0}, "control_marks": 0},
    }
    winners = set()
    for s in range(1, 20):
        w, _ = evaluate_decision_winner(
            canonical_ids, tied_actors, model_cfg, exchanges=[], ruleset_cfg=rulesets["mma"], rng=random.Random(s)
        )
        assert tied_actors["detroit"]["_last_decision_info"]["tiebreak"] is True
        winners.add(w)
    assert winners == {"detroit", "philly"}


def test_p9_exchange_and_state_schema_validation_on_full_fight() -> None:
    k = Knowledge()
    state_schema = json.loads((ROOT / "schemas" / "fight_state_v2.schema.json").read_text())
    event_schema = json.loads((ROOT / "schemas" / "exchange_event_v2.schema.json").read_text())

    res = simulate_fight_v2("donnell", "thai", ruleset="muay_thai", full_fight=True, seed=7, knowledge=k)
    jsonschema.validate(res["final_state_v2"], state_schema)
    assert "decision_scores" in res["final_state_v2"]
    for ex in res["exchanges"]:
        jsonschema.validate(ex, event_schema)
        assert isinstance(ex["knockdown"], bool)
        assert isinstance(ex["stun_applied"], bool)
