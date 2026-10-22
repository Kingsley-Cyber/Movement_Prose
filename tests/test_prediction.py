import copy
import itertools
import math
import pytest
from engine.probability import predict
from engine.capabilities import reachable


def test_deck_is_deterministic_complementary_finite(cards, knowledge):
    for a, b in itertools.combinations(cards.values(), 2):
        for rules in ["mma", "boxing"]:
            ab = predict(a, b, rules, knowledge)
            ba = predict(b, a, rules, knowledge)
            assert math.isfinite(ab["logit_a"])
            assert 0 < ab["probability_a"] < 1
            assert math.isclose(ab["probability_a"] + ba["probability_a"], 1)
            assert math.isclose(ab["logit_a"], -ba["logit_a"])
            assert math.isclose(sum(t["normalized_weight"] for t in ab["matrix_edges"]), 1)
            expected = math.fsum(t["weighted_contribution"] for t in ab["matrix_edges"]) + ab["slot_effect"]["logit"] + ab["null_effect"]["logit"]
            assert ab["logit_a"] == expected
    a, b = cards["maleek"], cards["donnell"]
    assert predict(a, b, knowledge=knowledge) == predict(a, b, knowledge=knowledge)


def test_maleek_donnell_baseline_is_explained_coin_flip(cards, knowledge):
    result = predict(cards["maleek"], cards["donnell"], knowledge=knowledge)
    assert .45 <= result["probability_a"] <= .55
    assert result["range_control"]["early_initiator"] == "donnell"
    assert result["slot_effect"]["logit"] == 0
    assert result["null_effect"]["logit"] == 0
    assert len(result["top_tactical_influences"]) == 3
    assert result["confidence"]["classification"] == "uncalibrated"
    assert any(w["opening"] == "leg" and w["victim_id"] == "donnell" for w in result["accessible_weaknesses"])


def test_boxing_renormalizes_only_applicable_matrices(cards, knowledge):
    result = predict(cards["maleek"], cards["donnell"], "boxing", knowledge)
    assert {e["matrix_id"] for e in result["matrix_edges"]} == {"mentality_mentality", "stance_stance", "hands_target", "defense_target"}
    assert not any(s["reachable"] for s in result["null_seams"])
    assert all(not t["matrix_id"].startswith("tie") for t in result["matrix_edges"])


def test_documented_mma_adaptation_changes_guard_kick_and_entry_exposure(cards, knowledge):
    boxer = copy.deepcopy(cards["philly"])
    boxer["adaptation"] = "boxing"
    mma = copy.deepcopy(boxer)
    mma["adaptation"] = "mma"
    pbox = predict(boxer, cards["wrestler"], "mma", knowledge)
    pmma = predict(mma, cards["wrestler"], "mma", knowledge)
    cb, cm = pbox["resolved_configurations"]["philly"], pmma["resolved_configurations"]["philly"]
    assert cm["options"]["hands"]["ratings"]["takedown_readiness"] > cb["options"]["hands"]["ratings"]["takedown_readiness"]
    assert cm["options"]["hands"]["exposure_weights"]["entry"] < cb["options"]["hands"]["exposure_weights"]["entry"]
    assert cm["options"]["stance"]["exposure_weights"]["leg"] < cb["options"]["stance"]["exposure_weights"]["leg"]
    assert pmma["logit_a"] != pbox["logit_a"]
    assert any("sprawl" in o["description"] for o in cm["options"].values() if o)


def test_unknown_card_and_pure_boxer_submission_rejected(cards, knowledge):
    broken = copy.deepcopy(cards["donnell"])
    broken["active_techniques"].append("armbar")
    with pytest.raises(ValueError, match="training"):
        predict(broken, cards["maleek"], knowledge=knowledge)
    broken = copy.deepcopy(cards["donnell"])
    broken["dimensions"]["hands"] = "hands.fake"
    with pytest.raises(ValueError, match="reference"):
        predict(broken, cards["maleek"], knowledge=knowledge)
