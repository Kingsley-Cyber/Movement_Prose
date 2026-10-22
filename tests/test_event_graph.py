import copy
import pytest
from engine.event_graph import graph, validate
from engine.fight_state import apply


def test_graph_contacts_dependencies_and_state_effects(fight, knowledge):
    g = graph(fight)
    assert validate(knowledge, fight, g)["status"] == "PASS"
    seen = set()
    for e in g["nodes"]:
        assert set(e["dependencies"]) <= seen
        if seen:
            assert e["cause_id"] in seen
        seen.add(e["id"])
    assert set(g["contact_events"]) == {e["id"] for e in fight["events"] if e["type"] == "contact"}


@pytest.mark.parametrize("defect", ["contact", "identity", "technique", "setup", "position", "injury", "trigger", "prediction", "winner"])
def test_negative_fight_inputs_cannot_be_reported_valid(fight, knowledge, defect):
    broken = copy.deepcopy(fight)
    if defect == "contact":
        broken["events"] = [e for e in broken["events"] if e["type"] != "contact"]
    elif defect == "identity":
        e = next(e for e in broken["events"] if e["type"] == "reaction")
        e["actor_id"], e["target_id"] = e["target_id"], e["actor_id"]
    elif defect == "technique":
        next(e for e in broken["events"] if e["type"] == "execution")["technique_id"] = "armbar"
    elif defect == "setup":
        broken["events"] = [e for e in broken["events"] if e["type"] != "setup"]
    elif defect == "position":
        broken["events"][0]["state_after"]["actors"]["maleek"]["position"] = [0, 0]
    elif defect == "injury":
        e = next(e for e in broken["events"] if e["type"] == "contact")
        e["state_after"]["actors"][e["target_id"]]["damage"] = {"head": 0, "body": 0, "leg": 0}
    elif defect == "trigger":
        next(e for e in broken["events"] if e["type"] == "reaction")["cause_id"] = "future_event"
    elif defect == "prediction":
        broken["prediction"]["probability_a"] = 1
    else:
        broken["selection"]["winner_id"] = next(i for i in ["maleek", "donnell"] if i != broken["selection"]["winner_id"])
    with pytest.raises((ValueError, KeyError)):
        validate(knowledge, broken)


def test_reducer_rejects_unearned_execution_and_range_transition(fight, knowledge):
    movement = next(e for e in fight["events"] if e["type"] == "movement")
    cards = {c["fighter_id"]: c for c in fight["cards"]}
    history = {e["id"]: e for e in fight["events"] if e["timestamp"] < movement["timestamp"]}
    broken = copy.deepcopy(movement)
    broken["parameters"]["to_range"] = "clinch"
    with pytest.raises(ValueError, match="nonadjacent"):
        apply(knowledge, movement["state_before"], cards, broken, history, "mma")
    state = copy.deepcopy(movement["state_before"])
    state["actors"][movement["actor_id"]]["pending"] = None
    with pytest.raises(ValueError, match="setup"):
        apply(knowledge, state, cards, movement, history, "mma")
