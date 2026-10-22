"""Deterministic semantic reducer. Stored snapshots are verified by replay."""
import copy
import math
from .capabilities import available


def initial(k, cards, ruleset):
    d = k.model["range_distance_m"]["kick"]
    state = {"time": 0, "round": 1, "phase": "initial_assessment", "range": "kick", "actors": {},
             "observed": [], "resolved_winner": None, "finished": False}
    for c, x in zip(cards, [-d / 2, d / 2]):
        state["actors"][c["fighter_id"]] = {
            "position": [x, 0.0], "facing": [1.0 if x < 0 else -1.0, 0.0],
            "orientation": "orthodox" if c["orientation"] == "switching" else c["orientation"],
            "stance": c["dimensions"]["stance"], "guard": c["dimensions"]["hands"],
            "posture": "standing", "foot_support": "two_feet", "balance": "stable", "momentum": [0.0, 0.0],
            "damage": {"head": 0, "body": 0, "leg": 0}, "fatigue": 0, "grip": None,
            "wall_proximity": "far", "tactical_initiative": False,
            "active_vulnerabilities": list(c["exploitable_seams"]), "available_responses": sorted(available(k, c, ruleset)),
            "injuries": [], "temporary_advantages": [], "activated_abilities": [], "setups": [], "pending": None,
            "contact_marks": 0, "control_marks": 0}
    return state


def check_technique(k, state, card, event):
    actor = state["actors"][card["fighter_id"]]
    tid = event["technique_id"]
    if tid not in available(k, card, event["_ruleset"], actor["activated_abilities"]):
        raise ValueError("unavailable technique: " + str(tid))
    tech = k.techniques[tid]
    if state["range"] not in tech["required_range"]:
        raise ValueError("invalid technique range: " + tid)
    config = tech["required_body_configuration"]
    if actor["posture"] != config["posture"]:
        raise ValueError("invalid body configuration")
    if config["grip"] and actor["grip"] != config["grip"]:
        raise ValueError("unearned grip prerequisite")
    if actor["balance"] != "stable":
        raise ValueError("unrecovered balance")
    return tech


def observe(k, state, card, e, history):
    if e["actor_id"] not in state["observed"]:
        state["observed"].append(e["actor_id"])


def setup(k, state, card, e, history):
    a = state["actors"][e["actor_id"]]
    if a["pending"]:
        raise ValueError("previous action has not recovered")
    t = check_technique(k, state, card, e)
    for requirement in t["setup_actions"]:
        if requirement == "observe":
            if e["actor_id"] not in state["observed"]:
                raise ValueError("missing observation")
        elif requirement == "grip":
            if not a["grip"]:
                raise ValueError("missing grip setup")
        elif requirement not in a["setups"]:
            raise ValueError("missing setup: " + requirement)
    a["pending"] = {"technique_id": t["id"], "stage": "prepared", "setup_id": e["id"], "contact_id": None}


def _pending(k, state, card, e):
    t = check_technique(k, state, card, e)
    p = state["actors"][e["actor_id"]]["pending"]
    if not p or p["technique_id"] != t["id"] or p["stage"] != "prepared":
        raise ValueError("execution before setup")
    p["stage"] = "executed"
    p["execution_id"] = e["id"]
    return t


def move(k, state, card, e, history):
    t = _pending(k, state, card, e)
    if t["kind"] != "movement":
        raise ValueError("movement requires movement technique")
    a, b = state["actors"][e["actor_id"]], state["actors"][e["target_id"]]
    if a["grip"] or b["grip"]:
        raise ValueError("release established grips before moving away")
    old = list(a["position"])
    dx, dy = a["position"][0] - b["position"][0], a["position"][1] - b["position"][1]
    dist = math.hypot(dx, dy)
    if "to_range" in e["parameters"]:
        dest = e["parameters"]["to_range"]
        order = k.model["range_order"]
        if dest not in order or abs(order.index(dest) - order.index(state["range"])) != 1:
            raise ValueError("nonadjacent range transition")
        if t["id"] not in ["step", "retreat"]:
            raise ValueError("unsupported range movement")
        if (t["id"] == "step") != (order.index(dest) < order.index(state["range"])):
            raise ValueError("movement direction conflicts with technique")
        nd = k.model["range_distance_m"][dest]
        a["position"] = [b["position"][0] + dx / dist * nd, b["position"][1] + dy / dist * nd]
        state["range"] = dest
    elif t["id"] == "pivot":
        # Lateral travel derives from the adjacent close/punch staging gap.
        lateral = k.model["range_distance_m"]["punch"] - k.model["range_distance_m"]["close"]
        theta = math.atan2(lateral, dist)
        a["position"] = [b["position"][0] + dx * math.cos(theta) - dy * math.sin(theta),
                         b["position"][1] + dx * math.sin(theta) + dy * math.cos(theta)]
        a["temporary_advantages"] = ["new angle established"]
    elif t["id"] == "switch_step":
        a["orientation"] = "southpaw" if a["orientation"] == "orthodox" else "orthodox"
        a["temporary_advantages"] = ["lead line changed after recovered Uno step"]
    else:
        raise ValueError("movement lacks a target")
    if any(abs(v) > k.model["arena_half_width_m"] for v in a["position"]):
        raise ValueError("movement leaves arena")
    a["momentum"] = [(x - y) / e["duration"] for x, y in zip(a["position"], old)]


def execute(k, state, card, e, history):
    t = _pending(k, state, card, e)
    a = state["actors"][e["actor_id"]]
    if t["kind"] == "movement":
        raise ValueError("movement must use movement handler")
    if "feint" in t["setup_actions"]:
        a["setups"].remove("feint")
    a["foot_support"] = t["balance_support"]["during"]
    if t["kind"] == "feint":
        a["temporary_advantages"] = ["opponent invited to attend the high line"]


def contact(k, state, card, e, history):
    a, b = state["actors"][e["actor_id"]], state["actors"][e["target_id"]]
    p = a["pending"]
    if not p or p["stage"] != "executed" or p["technique_id"] != e["technique_id"] or p["contact_id"]:
        raise ValueError("contact without a unique preceding execution")
    t = k.techniques[e["technique_id"]]
    if not t["contact_conditions"]["requires_event"]:
        raise ValueError("noncontact technique cannot cause contact")
    if e["cause_id"] != p["execution_id"]:
        raise ValueError("contact causal predecessor must be its execution")
    if e["parameters"].get("outcome") not in ["landed", "blocked"]:
        raise ValueError("contact outcome required")
    p["contact_id"] = e["id"]
    if e["parameters"]["outcome"] == "blocked":
        return
    effects = t["expected_state_changes"]
    if "damage_region" in effects:
        region = effects["damage_region"]
        b["damage"][region] += 1
        if region + " contact mark" not in b["injuries"]:
            b["injuries"].append(region + " contact mark")
        a["contact_marks"] += 1
    if "grip" in effects:
        if a["grip"] or b["grip"]:
            raise ValueError("release old grip before establishing a new one")
        a["grip"], b["grip"] = effects["grip"], "controlled"
    if effects.get("frame"):
        a["setups"].append("shield_frame")
    if effects.get("posture") == "ground":
        if a["grip"] or b["grip"]:
            required = t["required_body_configuration"]["grip"]
            if not required or a["grip"] != required:
                raise ValueError("takedown cannot replace an unrelated grip")
        a["posture"] = b["posture"] = "ground"
        a["grip"] = effects["control"]
        b["grip"] = "bottom" if a["grip"] == "top" else "top"
        state["range"] = "ground"
        a["foot_support"] = b["foot_support"] = "mat"
        # A fall is a contact-caused transition, not a disconnected teleport.
        b["position"] = [a["position"][0] + (k.model["range_distance_m"]["clinch"] if a["position"][0] < b["position"][0] else -k.model["range_distance_m"]["clinch"]), a["position"][1]]
        a["control_marks"] += 1
    if t["kind"] in ["control", "submission"]:
        a["control_marks"] += 1
    a["tactical_initiative"], b["tactical_initiative"] = True, False


def react(k, state, card, e, history):
    cause = history.get(e["cause_id"])
    if not cause or cause["actor_id"] != e["target_id"] or cause["target_id"] != e["actor_id"]:
        raise ValueError("reaction identity does not match trigger")
    anticipation = e["parameters"].get("anticipation", False)
    if cause["type"] != "contact" and not (anticipation and cause["type"] == "execution"):
        raise ValueError("reaction before trigger/contact")
    response = e["parameters"].get("response_technique")
    if response:
        a = state["actors"][e["actor_id"]]
        if response not in available(k, card, e["_ruleset"], a["activated_abilities"]):
            raise ValueError("unsupported defensive response")
        t = k.techniques[response]
        if state["range"] not in t["required_range"] or a["posture"] != t["required_body_configuration"]["posture"]:
            raise ValueError("defensive response has incompatible position")
        if t["kind"] not in ["defense", "movement"]:
            raise ValueError("reaction cannot inject an attack")


def recover(k, state, card, e, history):
    a = state["actors"][e["actor_id"]]
    p = a["pending"]
    if not p or p["stage"] != "executed" or p["technique_id"] != e["technique_id"]:
        raise ValueError("recovery without execution")
    t = k.techniques[e["technique_id"]]
    if t["contact_conditions"]["requires_event"] and not p["contact_id"]:
        raise ValueError("missing required contact event")
    a["pending"] = None
    a["balance"], a["momentum"] = "stable", [0.0, 0.0]
    a["foot_support"] = "mat" if a["posture"] == "ground" else "two_feet"
    a["fatigue"] += 1
    if t["id"] not in a["setups"]:
        a["setups"].append(t["id"])


def activate(k, state, card, e, history):
    a = state["actors"][e["actor_id"]]
    ability = next((v for v in card["conditional_abilities"] if v["id"] == e["parameters"].get("ability_id")), None)
    if not ability or ability["id"] in a["activated_abilities"]:
        raise ValueError("unknown or repeated capability activation")
    gates = ability["gates"]
    if not ability["trained"] or state["range"] != gates["range"] or a["wall_proximity"] != gates["wall"] or gates["previous_setup"] not in a["setups"]:
        raise ValueError("conditional capability gates unmet")
    a["activated_abilities"].append(ability["id"])
    a["available_responses"] = sorted(available(k, card, e["_ruleset"], a["activated_abilities"]))


def adjust(k, state, card, e, history):
    a = state["actors"][e["actor_id"]]
    if e["parameters"].get("release_grip"):
        if not a["grip"] or a["grip"] == "controlled":
            raise ValueError("actor cannot release opponent-owned grip")
        if state["range"] == "ground":
            raise ValueError("ground recovery requires a technique")
        for actor in state["actors"].values():
            actor["grip"] = None
    guard = e["parameters"].get("guard")
    if guard:
        permitted = {card["dimensions"]["hands"]}
        permitted.update(c for composite in card.get("composites", []) for c in composite["components"] if c.startswith("hands."))
        if guard not in permitted:
            raise ValueError("unsupported guard change")
        a["guard"] = guard


def resolve(k, state, card, e, history):
    if any(a["pending"] for a in state["actors"].values()):
        raise ValueError("unrecovered action at resolution")
    winner = e["parameters"].get("winner_id")
    if winner not in state["actors"] or winner != e["actor_id"]:
        raise ValueError("invalid winner identity")
    scores = {i: a["contact_marks"] + a["control_marks"] for i, a in state["actors"].items()}
    loser = next(i for i in scores if i != winner)
    if scores[winner] <= scores[loser]:
        raise ValueError("selected winner lacks demonstrated contact/control advantage")
    state["resolved_winner"] = winner


def aftermath(k, state, card, e, history):
    if not state["resolved_winner"]:
        raise ValueError("aftermath before resolution")
    state["finished"] = True


HANDLERS = {"assessment": observe, "setup": setup, "movement": move, "execution": execute,
            "contact": contact, "reaction": react, "recovery": recover, "activation": activate,
            "adjustment": adjust, "resolution": resolve, "aftermath": aftermath}


def apply(k, state, cards, event, history, ruleset):
    e = dict(event, _ruleset=ruleset)
    if e["actor_id"] not in cards or e["target_id"] not in cards or e["actor_id"] == e["target_id"]:
        raise ValueError("inverted/invalid actor identities")
    if e["id"] in history:
        raise ValueError("duplicate event")
    if e["technique_id"] is not None and e["technique_id"] not in k.techniques:
        raise ValueError("unknown event technique reference")
    if e["timestamp"] < state["time"]:
        raise ValueError("time moves backward")
    if e["type"] not in HANDLERS:
        raise ValueError("unknown state handler")
    if history and (e["cause_id"] not in history or e["cause_id"] not in e["dependencies"] or any(d not in history for d in e["dependencies"])):
        raise ValueError("missing causal prerequisite")
    if not history and (e["type"] != "assessment" or e["cause_id"] is not None):
        raise ValueError("fight must begin with assessment")
    if state["finished"] or (state["resolved_winner"] and e["type"] != "aftermath"):
        raise ValueError("combat continues after resolution")
    result = copy.deepcopy(state)
    HANDLERS[e["type"]](k, result, cards[e["actor_id"]], e, history)
    result["time"] = e["timestamp"] + e["duration"]
    result["phase"] = e["phase"]
    ids = list(result["actors"])
    for i in ids:
        a, b = result["actors"][i], result["actors"][next(j for j in ids if j != i)]
        dx, dy = b["position"][0] - a["position"][0], b["position"][1] - a["position"][1]
        distance = math.hypot(dx, dy)
        if distance == 0:
            raise ValueError("contradictory overlapping actor positions")
        a["facing"] = [dx / distance, dy / distance]
        a["wall_proximity"] = "near" if k.model["arena_half_width_m"] - max(abs(v) for v in a["position"]) <= k.model["wall_near_m"] else "far"
    return result
