"""Phase P4 tests: Laterality, anatomical sides, mirror invariance, and southpaw edge (§7.4, §10.3)."""

from __future__ import annotations

import copy
from pathlib import Path
from unittest.mock import patch

import jsonschema

from engine.ontology import ROOT, Knowledge, read
from engine.v2.cards import list_archetypes_v2, load_card_v2
from engine.v2.data import load_model_v2, load_techniques_v2
from engine.simulator_v2 import compute_card_derived_damage, simulate_fight_v2, simulate_many_v2
from engine.v2.laterality import (
    compute_dominance_deltas,
    get_anatomical_sides,
    resolve_actor_laterality,
    resolve_target_anatomical_side,
)


def _mirror_side(val: str) -> str:
    if val == "left":
        return "right"
    if val == "right":
        return "left"
    return val


def _mirror_card(card: dict) -> dict:
    c = copy.deepcopy(card)
    orig_orient = str(c.get("orientation") or "orthodox")
    base_orient = "orthodox" if orig_orient == "switching" else orig_orient
    c["orientation"] = "southpaw" if base_orient == "orthodox" else "orthodox"
    lat = resolve_actor_laterality(card, base_orient)
    c["laterality"] = {
        "dominant_hand": _mirror_side(lat["dominant_hand"]),
        "dominant_leg": _mirror_side(lat["dominant_leg"]),
        "opposite_stance_experience": lat["opposite_stance_experience"],
    }
    return c


def test_p4_natural_cards_zero_dominance_deltas_and_cross_dominant_template():
    """Verify natural cards get zero dominance deltas (keeping Darius/Rook identical) and JKD template is cross-dominant."""
    k = Knowledge()
    tech_map = load_techniques_v2(k.root)
    model_cfg = load_model_v2(k.root)

    ids = [a["fighter_id"] for a in list_archetypes_v2(k)]
    for fid in ids:
        card = load_card_v2(k, fid)
        orient = "orthodox" if card["orientation"] == "switching" else card["orientation"]
        lat = resolve_actor_laterality(card, orient)
        assert lat["natural"] is True
        for tid in ("jab", "cross", "hook", "low_kick", "body_kick"):
            pwr_d, acc_d = compute_dominance_deltas(card, {"orientation": orient, "laterality": lat}, tech_map[tid], model_cfg)
            assert pwr_d == 0.0 and acc_d == 0.0

    # Verify Darius/Rook damage numbers are unchanged when adding explicit natural laterality block
    rook = load_card_v2(k, "street")
    darius = load_card_v2(k, "detroit")
    rook_explicit = copy.deepcopy(rook)
    rook_explicit["laterality"] = {"dominant_hand": "right", "dominant_leg": "right", "opposite_stance_experience": "normal"}
    darius_explicit = copy.deepcopy(darius)
    darius_explicit["laterality"] = {"dominant_hand": "left", "dominant_leg": "left", "opposite_stance_experience": "normal"}

    dummy_state = {"fatigue": 0.0, "damage": {"head": 0.0, "body": 0.0, "leg": 0.0}, "wall_proximity": "far", "setups": []}
    assert compute_card_derived_damage(k, rook, darius, "cross", "clean", dummy_state, dummy_state) == compute_card_derived_damage(
        k, rook_explicit, darius_explicit, "cross", "clean", dummy_state, dummy_state
    )
    assert compute_card_derived_damage(k, darius, rook, "cross", "counter_hit", dummy_state, dummy_state) == compute_card_derived_damage(
        k, darius_explicit, rook_explicit, "cross", "counter_hit", dummy_state, dummy_state
    )

    # Jeet Kune Do template is southpaw with right-hand/right-leg dominance (cross-dominant: strong side forward)
    jkd = read(ROOT / "handoff_seed/style_templates/tpl_jeet_kune_do.json")
    lat_jkd = resolve_actor_laterality(jkd, "southpaw")
    assert lat_jkd["natural"] is False
    lead_pwr, lead_acc = compute_dominance_deltas(jkd, {"orientation": "southpaw", "laterality": lat_jkd}, tech_map["jab"], model_cfg)
    rear_pwr, rear_acc = compute_dominance_deltas(jkd, {"orientation": "southpaw", "laterality": lat_jkd}, tech_map["cross"], model_cfg)
    assert lead_pwr == 0.08 and lead_acc == 0.04
    assert rear_pwr == -0.06 and rear_acc == -0.02


def test_p4_mirror_laterality_invariance():
    """§7.4.9 / §10.3: Mirror both fighters' orientation, dominance, sides AND liver_side -> identical results."""
    k = Knowledge()
    base_model = copy.deepcopy(load_model_v2(k.root))
    mirrored_model = copy.deepcopy(base_model)
    mirrored_model["laterality"]["body_sides"]["liver_side"] = "left"

    # Flip familiarity defaults so mirrored orthodox<->southpaw have identical exposure
    fam_def = mirrored_model["laterality"]["familiarity"]["exposure_default"]
    fam_def["orthodox_facing_southpaw"], fam_def["southpaw_facing_orthodox"] = (
        fam_def["southpaw_facing_orthodox"],
        fam_def["orthodox_facing_southpaw"],
    )

    pairs = [("detroit", "donnell"), ("sanda_judo", "thai"), ("karate", "wrestler"), ("jiujitsu", "street")]
    for fa, fb in pairs:
        ca = load_card_v2(k, fa)
        cb = load_card_v2(k, fb)
        ca_m = _mirror_card(ca)
        cb_m = _mirror_card(cb)

        for s in (1, 2, 3):
            res_orig = simulate_fight_v2(ca, cb, seed=s, knowledge=k)
            with patch("engine.v2.exchange.load_model_v2", return_value=mirrored_model), patch(
                "engine.v2.laterality.load_model_v2", return_value=mirrored_model
            ), patch("engine.v2.readiness.load_model_v2", return_value=mirrored_model):
                res_mirr = simulate_fight_v2(ca_m, cb_m, seed=s, knowledge=k)

            assert res_orig["winner_id"] == res_mirr["winner_id"]
            assert res_orig["finish_reason"] == res_mirr["finish_reason"]
            assert len(res_orig["exchanges"]) == len(res_mirr["exchanges"])
            for ex_o, ex_m in zip(res_orig["exchanges"], res_mirr["exchanges"]):
                assert ex_o["attacker_id"] == ex_m["attacker_id"]
                assert ex_o["technique_id"] == ex_m["technique_id"]
                assert ex_o["outcome"] == ex_m["outcome"]
                assert ex_o["damage"]["final_damage"] == ex_m["damage"]["final_damage"]
                assert ex_o["laterality"]["limb_side"] == _mirror_side(ex_m["laterality"]["limb_side"])
                assert ex_o["laterality"]["target_side"] == _mirror_side(ex_m["laterality"]["target_side"])

            for fid in (fa, fb):
                d_o = res_orig["final_state_v2"]["actors"][fid]["damage_by_side"]
                d_m = res_mirr["final_state_v2"]["actors"][fid]["damage_by_side"]
                assert d_o["head_left"] == d_m["head_right"]
                assert d_o["head_right"] == d_m["head_left"]
                assert d_o["body_left"] == d_m["body_right"]
                assert d_o["body_right"] == d_m["body_left"]
                assert d_o["leg_left"] == d_m["leg_right"]
                assert d_o["leg_right"] == d_m["leg_left"]


def test_p4_southpaw_only_edge_within_target_band_and_schema_validation():
    """§7.4.9 / §10.3: Two identical natural cards except stance (orthodox vs southpaw) -> southpaw edge in [0, 0.05]."""
    k = Knowledge()
    state_schema = read(ROOT / "schemas/fight_state_v2.schema.json")
    ex_schema = read(ROOT / "schemas/exchange_event_v2.schema.json")

    base_card = load_card_v2(k, "donnell")
    ortho_card = copy.deepcopy(base_card)
    ortho_card["fighter_id"] = "probe_ortho"
    ortho_card["name"] = "Probe Orthodox"
    ortho_card["orientation"] = "orthodox"
    ortho_card["laterality"] = {"dominant_hand": "right", "dominant_leg": "right", "opposite_stance_experience": "normal"}

    south_card = copy.deepcopy(base_card)
    south_card["fighter_id"] = "probe_southpaw"
    south_card["name"] = "Probe Southpaw"
    south_card["orientation"] = "southpaw"
    south_card["laterality"] = {"dominant_hand": "left", "dominant_leg": "left", "opposite_stance_experience": "normal"}

    # Validate state & exchange schemas with P4 laterality fields
    single = simulate_fight_v2(ortho_card, south_card, seed=11, knowledge=k)
    jsonschema.validate(single["final_state_v2"], state_schema)
    for ex in single["exchanges"]:
        jsonschema.validate(ex, ex_schema)
        assert ex.get("laterality") is not None

    # Measure direct head-to-head southpaw-only edge across 400 seeds (§10.3: two cards identical except stance -> southpaw edge within [0, 0.05])
    r_direct = simulate_many_v2(south_card, ortho_card, runs=400, knowledge=k)
    edge = float(r_direct["empirical_win_rate_a"]) - 0.50
    assert 0.0 <= edge <= 0.05, f"Southpaw edge {edge:.3f} outside [0.0, 0.05] band"
