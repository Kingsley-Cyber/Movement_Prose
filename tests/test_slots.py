import copy
import math
from engine.capabilities import null_seams
from engine.probability import predict


def test_net_slot_term_is_once_in_logit(cards, knowledge):
    a = copy.deepcopy(cards["wrestler"])
    base = predict(a, cards["donnell"], knowledge=knowledge)
    a["slot_count"] += 1
    a["slot_label"] = "Triad"
    a["synchronized_capabilities"].append({"id": "extra_synchronization", "capabilities": ["basic_movement"], "description": "Test the supplied coefficient without changing available techniques."})
    changed = predict(a, cards["donnell"], knowledge=knowledge)
    assert math.isclose(changed["logit_a"] - base["logit_a"], .15)
    assert changed["matrix_edges"] == base["matrix_edges"]


def test_null_requires_legal_trained_reachable_entry(cards, knowledge):
    seams = null_seams(knowledge, cards["wrestler"], cards["donnell"], "mma")
    assert len(seams) == 1 and seams[0]["reachable"]
    assert "double_leg" in seams[0]["technique_ids"]
    assert not null_seams(knowledge, cards["maleek"], cards["donnell"], "mma")[0]["reachable"]
    assert not null_seams(knowledge, cards["wrestler"], cards["donnell"], "boxing")[0]["reachable"]


def test_null_is_one_penalty_even_with_multiple_entries(cards, knowledge):
    p = predict(cards["donnell"], cards["wrestler"], knowledge=knowledge)
    assert p["null_effect"] == {"a_count": 1, "b_count": 0, "logit": -.20}
    assert len(p["null_seams"][0]["technique_ids"]) > 1


def test_representative_complete_deck_and_specific_two_slot_upset(cards, knowledge):
    two = [c for c in cards.values() if c["slot_count"] == 2]
    three = [c for c in cards.values() if c["slot_count"] == 3]
    results = [predict(a, b, knowledge=knowledge)["probability_a"] for a in three for b in two]
    assert sum(p > .5 for p in results) > len(results) / 2
    upset = predict(cards["wrestler"], cards["donnell"], knowledge=knowledge)
    assert upset["probability_a"] > .5
    assert upset["slot_effect"]["logit"] == -.15
    assert upset["null_effect"]["logit"] == .20
    # Remove only the reachable missing-capability term: this reverses the edge.
    assert upset["logit_a"] - upset["null_effect"]["logit"] < 0
