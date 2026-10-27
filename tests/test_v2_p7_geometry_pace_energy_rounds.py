"""Phase P7 tests: 2-D geometry, arena presets, initiator pace, technique/defender energy, rounds & CLI."""

from __future__ import annotations

import json
import math

from engine.ontology import Knowledge
from engine.simulator_v2 import (
    compute_card_derived_damage,
    compute_readiness_profile,
    load_card_v2,
    simulate_fight_v2,
    simulate_many_v2,
)
from engine.v2.geometry import (
    apply_movement_displacement,
    band_from_distance,
    compute_distance_m,
    compute_wall_and_corner,
)
import simulate_fight


def test_p7_geometry_2d_displacements_corners_and_bands():
    k = Knowledge()
    assert band_from_distance(0.45, "standing") == "clinch"
    assert band_from_distance(0.70, "standing") == "close"
    assert band_from_distance(1.05, "standing") == "punch"
    assert band_from_distance(1.65, "standing") == "kick"
    assert band_from_distance(2.40, "standing") == "outside"
    assert band_from_distance(1.65, "ground") == "ground"

    # Ring has corners; cage does not
    prox_ring, corner_ring, _ = compute_wall_and_corner([2.7, 2.7], "ring")
    assert prox_ring == "near"
    assert corner_ring is True

    prox_cage, corner_cage, _ = compute_wall_and_corner([2.7, 2.7], "cage")
    assert prox_cage == "near"
    assert corner_cage is False

    # Pivot rotates opponent in 2-D around attacker scaled by lateral_freedom
    att = {"position": [0.0, 0.0], "facing": [1.0, 0.0], "wall_proximity": "far", "in_corner": False}
    dfn = {"position": [1.0, 0.0], "facing": [-1.0, 0.0], "wall_proximity": "far", "in_corner": False}
    apply_movement_displacement("pivot", att, dfn, "open_floor")
    assert abs(dfn["position"][1]) > 0.4
    assert math.isclose(compute_distance_m(att["position"], dfn["position"]), 1.0, abs_tol=0.05)


def test_p7_outfighter_wins_more_in_open_floor_than_narrow_alley():
    k = Knowledge()
    aya = load_card_v2(k, "karate")
    donnell = load_card_v2(k, "donnell")

    open_res = simulate_many_v2(aya, donnell, runs=60, arena="open_floor", knowledge=k)
    alley_res = simulate_many_v2(aya, donnell, runs=60, arena="narrow_alley", knowledge=k)

    assert open_res["empirical_win_rate_a"] > alley_res["empirical_win_rate_a"]


def test_p7_initiator_pace_defender_energy_and_rounds_rest():
    k = Knowledge()
    mio = load_card_v2(k, "sanda_judo")
    niran = load_card_v2(k, "thai")

    # Multi-round simulation records round numbers and resets between rounds
    sim_rounds = simulate_fight_v2(
        mio,
        niran,
        ruleset="boxing",
        rounds=3,
        round_length_s=20.0,
        rest_s=60.0,
        seed=11,
        knowledge=k,
    )
    assert sim_rounds["duration_requested_s"] == 60.0
    rounds_seen = {ex["round"] for ex in sim_rounds["exchanges"]}
    assert 1 in rounds_seen
    assert sim_rounds["final_state_v2"]["round"] >= 1


def test_p7_cli_full_fight_and_rounds_flags(capsys):
    rc = simulate_fight.main(
        ["sanda_judo", "thai", "--ruleset", "boxing", "--rounds", "2", "--round-length", "15", "--seed", "5", "--json"]
    )
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["duration_requested_s"] == 30.0
    assert out["winner_id"] in ("sanda_judo", "thai")


def test_p7_option_damage_dealt_and_taken_multipliers_wired_within_d9_bounds():
    k = Knowledge()
    rook = load_card_v2(k, "street")
    darius = load_card_v2(k, "detroit")
    dummy_state = {"fatigue": 0.0, "damage": {"head": 0.0, "body": 0.0, "leg": 0.0}, "wall_proximity": "far", "setups": []}
    rook_cross = compute_card_derived_damage(k, rook, darius, "cross", "clean", dummy_state, dummy_state)
    darius_cross = compute_card_derived_damage(k, darius, rook, "cross", "clean", dummy_state, dummy_state)
    assert rook_cross["attacker_multiplier"] > darius_cross["attacker_multiplier"] * 1.25
