import copy
import pytest
from engine.fight_director import plan, Builder, PHASES
from engine.event_graph import validate
from engine.capabilities import available


def test_seeded_plan_repeats_and_reversed_order_selects_same_identity(cards, knowledge, fight):
    assert fight == plan(cards["maleek"], cards["donnell"], seed=42, knowledge=knowledge)
    reverse = plan(cards["donnell"], cards["maleek"], seed=42, knowledge=knowledge)
    assert reverse["selection"]["winner_id"] == fight["selection"]["winner_id"]
    assert list(dict.fromkeys(e["phase"] for e in fight["events"])) == PHASES
    assert validate(knowledge, fight)["status"] == "PASS"


def test_director_mode_preserves_original_prediction(cards, knowledge, fight):
    other = next(i for i in ["maleek", "donnell"] if i != fight["selection"]["winner_id"])
    directed = plan(cards["maleek"], cards["donnell"], winner=other, seed=42, knowledge=knowledge)
    assert directed["prediction"] == fight["prediction"]
    assert directed["selection"]["mode"] == "director-controlled"
    assert directed["final_state"]["resolved_winner"] == other
    assert validate(knowledge, directed)["status"] == "PASS"


@pytest.mark.parametrize("name", ["maleek", "donnell", "macklin", "detroit", "philly", "wrestler", "thai", "jiujitsu", "greco", "karate"])
def test_roster_can_direct_its_trained_win_path(name, cards, knowledge):
    result = plan(cards[name], cards["street"], winner=name, seed=42, knowledge=knowledge)
    assert validate(knowledge, result)["status"] == "PASS"
    assert result["final_state"]["resolved_winner"] == name
    for e in result["events"]:
        if e["type"] in ["execution", "movement"]:
            assert e["technique_id"] in available(knowledge, next(c for c in result["cards"] if c["fighter_id"] == e["actor_id"]), "mma", e["state_before"]["actors"][e["actor_id"]]["activated_abilities"])


def test_two_slot_upset_is_a_ground_control_fight(cards, knowledge, fight):
    upset = plan(cards["wrestler"], cards["donnell"], seed=42, knowledge=knowledge)
    assert upset["prediction"]["probability_a"] > .5
    assert upset["selection"]["winner_id"] == "wrestler"
    assert any(e["technique_id"] == "double_leg" and e["type"] == "contact" for e in upset["events"])
    assert any(e["technique_id"] == "ride" for e in upset["events"])
    assert any("NULL:tie:donnell" in e["source_weakness_ids"] for e in upset["events"])
    assert upset["final_state"]["range"] == "ground"
    assert any(e["technique_id"] == "switch_step" for e in fight["events"])
    assert any(e["technique_id"] == "low_kick" for e in fight["events"])
    assert fight["final_state"]["range"] != upset["final_state"]["range"]
    assert validate(knowledge, upset)["status"] == "PASS"


def test_maleek_conditional_cage_plum_requires_all_gates(cards, knowledge):
    b = Builder(knowledge, [cards["maleek"], cards["donnell"]], "mma")
    for actor in b.cards:
        b.emit("assessment", actor)
    assert "cage_plum" not in available(knowledge, cards["maleek"], "mma")
    with pytest.raises(ValueError, match="gates"):
        b.emit("activation", "maleek", parameters={"ability_id": "maleek.cage_plum"})
    # Legal adjacent steps take both actors to the cage; no snapshot is patched.
    b.stage("maleek", "outside")
    b.stage("donnell", "punch")
    b.stage("maleek", "kick")
    b.stage("donnell", "punch")
    b.stage("maleek", "kick")
    b.stage("donnell", "clinch")
    assert b.state["actors"]["maleek"]["wall_proximity"] == "near"
    with pytest.raises(ValueError, match="gates"):
        b.emit("activation", "maleek", parameters={"ability_id": "maleek.cage_plum"})
    b.action("maleek", "shield_frame")
    b.emit("activation", "maleek", parameters={"ability_id": "maleek.cage_plum"})
    b.action("maleek", "cage_plum")
    b.action("maleek", "knee_body")
    assert b.state["actors"]["donnell"]["damage"]["body"] > 0
    assert "maleek.cage_plum" in b.state["actors"]["maleek"]["activated_abilities"]
