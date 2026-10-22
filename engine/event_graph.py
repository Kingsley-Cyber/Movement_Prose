from .fight_state import apply, initial


def graph(plan):
    return {"version": plan["version"], "nodes": plan["events"],
            "dependency_edges": [{"from": dep, "to": e["id"], "type": "requires"} for e in plan["events"] for dep in e["dependencies"]],
            "causal_edges": [{"from": e["cause_id"], "to": e["id"], "type": "causes"} for e in plan["events"] if e["cause_id"]],
            "contact_events": [e["id"] for e in plan["events"] if e["type"] == "contact"],
            "final_winner": plan["selection"]["winner_id"]}


def validate(k, plan, event_graph=None):
    k.schema("fight_plan", plan)
    cards = {c["fighter_id"]: k.card(c) for c in plan["cards"]}
    if len(cards) != 2:
        raise ValueError("duplicate fighter identities")
    expected_initial = initial(k, plan["cards"], plan["ruleset"])
    if plan["initial_state"] != expected_initial:
        raise ValueError("initial state differs from canonical card configuration")
    state, history = expected_initial, {}
    for e in plan["events"]:
        k.schema("event", e)
        k.schema("fight_state", e["state_before"])
        if e["state_before"] != state or e["preconditions"] != {"range": state["range"], "posture": state["actors"][e["actor_id"]]["posture"]}:
            raise ValueError("contradictory state snapshot/preconditions")
        for did in e["source_weakness_ids"]:
            if did.startswith("NULL:"):
                _, dim, victim = did.split(":")
                matches = [s for s in plan["prediction"]["null_seams"] if s["victim_id"] == victim and s["dimension"] == dim and s["reachable"]]
                if not matches:
                    raise ValueError("unsupported NULL explanation")
            elif did not in k.debts:
                raise ValueError("unknown source weakness")
        state = apply(k, state, cards, e, history, plan["ruleset"])
        k.schema("fight_state", state)
        effects = {key: val for key, val in state.items() if val != e["state_before"][key]}
        if state != e["state_after"] or effects != e["effects"]:
            raise ValueError("stored effects/state differ from replay")
        history[e["id"]] = e
    if state != plan["final_state"] or state["time"] != plan["duration"] or not state["finished"]:
        raise ValueError("incomplete timeline")
    if state["resolved_winner"] != plan["selection"]["winner_id"]:
        raise ValueError("outcome contradicts selected winner")
    from .probability import predict
    from .fight_director import PHASES
    if plan["phases"] != PHASES or list(dict.fromkeys(e["phase"] for e in plan["events"])) != PHASES:
        raise ValueError("required tactical phase missing or out of order")
    if plan["prediction"] != predict(*plan["cards"], ruleset=plan["ruleset"], knowledge=k):
        raise ValueError("prediction or matrix trace changed")
    probs = {plan["prediction"]["fighter_a"]: plan["prediction"]["probability_a"], plan["prediction"]["fighter_b"]: plan["prediction"]["probability_b"]}
    if plan["selection"]["original_probabilities"] != probs:
        raise ValueError("selected mode falsifies original probability")
    import random
    draw = random.Random(plan["seed"]).random()
    if plan["selection"]["draw"] != draw:
        raise ValueError("selection seed mismatch")
    if plan["selection"]["mode"] == "predictive":
        ids = sorted(probs)
        if plan["selection"]["winner_id"] != (ids[0] if draw < probs[ids[0]] else ids[1]):
            raise ValueError("predictive winner differs from seeded sample")
    if event_graph is not None:
        k.schema("event_graph", event_graph)
        if event_graph != graph(plan):
            raise ValueError("event graph differs from causal plan")
    return {"status": "PASS", "events_replayed": len(history), "contacts": sum(e["type"] == "contact" for e in plan["events"]),
            "fidelity": plan["fidelity"], "winner": state["resolved_winner"]}
