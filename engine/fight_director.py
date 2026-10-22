import copy
import random
from .capabilities import available
from .fight_state import apply, initial
from .ontology import Knowledge
from .probability import predict


PHASES = ["initial_assessment", "range_establishment", "first_meaningful_exchange", "first_weakness_exploited",
          "defensive_adaptation", "tactical_escalation", "counter_adaptation", "turning_point", "resolution", "aftermath"]


class Builder:
    def __init__(self, k, cards, ruleset):
        self.k, self.ruleset = k, ruleset
        self.cards = {c["fighter_id"]: c for c in cards}
        self.state = initial(k, cards, ruleset)
        self.events, self.history = [], {}
        self.phase = PHASES[0]

    def opponent(self, actor):
        return next(i for i in self.cards if i != actor)

    def emit(self, kind, actor, tid=None, parameters=None, cause=None, why=None, debts=()):
        previous = self.events[-1]["id"] if self.events else None
        cause = cause or previous
        event = {"id": "e" + str(len(self.events) + 1), "type": kind, "phase": self.phase,
                 "actor_id": actor, "target_id": self.opponent(actor), "technique_id": tid,
                 "timestamp": len(self.events), "duration": 1, "cause_id": cause,
                 "dependencies": sorted(set(x for x in [previous, cause] if x)),
                 "source_weakness_ids": list(debts),
                 "intent": why or "Recover support and preserve the causal sequence.",
                 "preconditions": {"range": self.state["range"], "posture": self.state["actors"][actor]["posture"]},
                 "parameters": parameters or {}}
        self.state = apply(self.k, self.state, self.cards, event, self.history, self.ruleset)
        self.events.append(event)
        self.history[event["id"]] = event
        return event["id"]

    def stage(self, actor, dest):
        order = self.k.model["range_order"]
        if self.state["range"] == "ground":
            if dest != "ground":
                raise ValueError("cannot stage a standing action from an established ground position")
            return
        if self.state["range"] == dest:
            return
        if any(a["grip"] for a in self.state["actors"].values()):
            owner = next(i for i, a in self.state["actors"].items() if a["grip"] != "controlled")
            self.emit("adjustment", owner, parameters={"release_grip": True}, why="Release the established attachment before changing range.")
        while self.state["range"] != dest:
            now, target = order.index(self.state["range"]), order.index(dest)
            next_range = order[now + (1 if target > now else -1)]
            tid = "retreat" if target > now else "step"
            self.action(actor, tid, {"to_range": next_range}, why="Establish " + next_range + " through one adjacent range step.")

    def action(self, actor, tid, parameters=None, why=None, debts=(), landed=True):
        t = self.k.techniques[tid]
        if "feint" in t["setup_actions"] and "feint" not in self.state["actors"][actor]["setups"]:
            self.action(actor, "feint", why="Invite the opponent to attend the head line before changing the attack.", debts=debts)
        self.emit("setup", actor, tid, why=why or t["description"], debts=debts)
        ex = self.emit("movement" if t["kind"] == "movement" else "execution", actor, tid, parameters,
                       why=why or t["description"], debts=debts)
        if t["kind"] == "feint":
            self.emit("reaction", self.opponent(actor), parameters={"anticipation": True}, cause=ex,
                      why="Attend the shown high line; the feint has no contact.", debts=debts)
        elif t["contact_conditions"]["requires_event"]:
            defender = self.cards[self.opponent(actor)]
            choices = sorted(x for x in available(self.k, defender, self.ruleset)
                             if self.k.techniques[x]["kind"] == "defense"
                             and self.state["range"] in self.k.techniques[x]["required_range"]
                             and self.k.techniques[x]["required_body_configuration"]["posture"] == self.state["actors"][defender["fighter_id"]]["posture"])
            if choices:
                self.emit("reaction", self.opponent(actor), parameters={"anticipation": True, "response_technique": choices[0]},
                          cause=ex, why="Attempt a trained defensive response; success remains contingent.", debts=debts)
            contact = self.emit("contact", actor, tid, {"outcome": "landed" if landed else "blocked"}, cause=ex,
                                why="Resolve explicit contact with the " + t["target_region"] + ".", debts=debts)
            self.emit("reaction", self.opponent(actor), parameters={"anticipation": False}, cause=contact,
                      why="Show the consequence of contact; preserve established damage and position.", debts=debts)
        self.emit("recovery", actor, tid, why=t["recovery_requirements"], debts=debts)

    def attack(self, actor, tid, why, debts=()):
        t = self.k.techniques[tid]
        # A high-line feint must be made before closing beyond its range.
        # Movement preserves the earned setup token; execution consumes it.
        if "feint" in t["setup_actions"] and "feint" not in self.state["actors"][actor]["setups"]:
            if self.state["range"] not in self.k.techniques["feint"]["required_range"]:
                self.stage(actor, "close")
            self.action(actor, "feint", why="Draw high attention before entering the technique's required range.", debts=debts)
        if self.state["range"] not in t["required_range"]:
            dest = next((r for r in t["required_range"] if r in self.k.model["range_order"]), "ground")
            self.stage(actor, dest)
        self.action(actor, tid, why=why, debts=debts)


def select_attack(k, card, prediction, opponent, ruleset):
    tids = available(k, card, ruleset)
    seams = [s for s in prediction["null_seams"] if s["attacker_id"] == card["fighter_id"] and s["reachable"]]
    if seams:
        seam = seams[0]
        candidates = seam["technique_ids"]
        # A direct leg entry operationalizes the absence of a tie, rather than
        # giving an unrelated generic punch a NULL advantage.
        tid = next((t for t in candidates if k.techniques[t]["kind"] == "takedown"), candidates[0])
        return tid, ["NULL:" + seam["dimension"] + ":" + opponent], seam["reason"]
    candidates = [w for w in prediction["accessible_weaknesses"] if w["attacker_id"] == card["fighter_id"]]
    target = k.options[card["dimensions"]["target"]] if card["dimensions"]["target"] else None
    preference = target["technique_refs"] if target else []
    valid = [(t, w) for w in candidates for t in w["technique_ids"] if t in tids
             and k.techniques[t]["kind"] in ["punch", "kick", "takedown", "grip"]
             and not k.techniques[t]["required_body_configuration"]["grip"]]
    if valid:
        tid, weakness = min(valid, key=lambda x: (x[0] not in preference, x[0]))
        return tid, [weakness["debt_id"]], weakness["mechanism"]
    tid = next((t for t in preference if t in tids and k.techniques[t]["kind"] in ["punch", "kick"]),
               next(t for t in sorted(tids) if k.techniques[t]["kind"] == "punch"))
    return tid, [], "Use a trained target line without claiming a special style advantage."


def plan(a, b, ruleset="mma", duration=60, seed=42, winner=None, knowledge=None):
    k = knowledge or Knowledge()
    a, b = k.card(a), k.card(b)
    if not isinstance(seed, int) or not isinstance(duration, (float, int)) or not 0 < duration < float("inf"):
        raise ValueError("finite positive duration and integer seed required")
    prediction = predict(a, b, ruleset, k)
    probabilities = {a["fighter_id"]: prediction["probability_a"], b["fighter_id"]: prediction["probability_b"]}
    draw = random.Random(seed).random()
    canonical = sorted(probabilities)
    sampled = canonical[0] if draw < probabilities[canonical[0]] else canonical[1]
    if winner is not None and winner not in probabilities:
        raise ValueError("director winner must be a participating fighter ID")
    selection = {"mode": "director-controlled" if winner else "predictive", "winner_id": winner or sampled,
                 "draw": draw, "original_probabilities": probabilities,
                 "label": "Explicitly dramatized author-selected path; prediction unchanged." if winner else
                 "Seeded outcome, sampled in sorted fighter-ID order; conditional path to that outcome."}
    winner = selection["winner_id"]
    cards = {c["fighter_id"]: c for c in [a, b]}
    loser = next(i for i in cards if i != winner)
    build = Builder(k, [a, b], ruleset)
    for actor in cards:
        build.emit("assessment", actor, why=cards[actor]["fighting_description"]["does"])
    early = prediction["range_control"]["early_initiator"]
    build.phase = PHASES[1]
    build.stage(early, "punch")
    build.phase = PHASES[2]
    opening = next(t for t in ["jab", "haymaker"] if t in available(k, cards[early], ruleset))
    build.attack(early, opening, "Establish the preferred early tempo and make the opponent answer the head threat.")
    main, debts, mechanism = select_attack(k, cards[winner], prediction, loser, ruleset)
    build.phase = PHASES[3]
    build.attack(winner, main, "Reach the first weakness: " + mechanism, debts)
    build.phase = PHASES[4]
    if build.state["range"] == "ground":
        # A bottom non-grappler may struggle, but receives no trained escape.
        build.emit("adjustment", loser, why="Try to frame and recover posture from the established bottom position; no trained escape is invented.", debts=debts)
    elif build.state["range"] == "clinch":
        build.emit("adjustment", loser, why="Protect posture and seek inside space; the existing tie remains until explicitly released.", debts=debts)
    else:
        movers = [c for c in cards.values() if "switch_step" in available(k, c, ruleset)]
        if movers:
            mover = movers[0]["fighter_id"]
            build.stage(mover, "punch")
            build.action(mover, "switch_step", why="Uno changes the lead line after the pressure entry; the transition must recover.")
        else:
            build.action(loser, "pivot", why="Attempt a lateral exit from the first exploited line.")
    build.phase = PHASES[5]
    ground = build.state["range"] == "ground"
    grip = build.state["actors"][winner]["grip"]
    winner_tids = available(k, cards[winner], ruleset)
    if ground:
        follow = "ride" if grip == "top" and "ride" in winner_tids else "armbar" if grip == "bottom" and "armbar" in winner_tids else "escape"
        if follow not in winner_tids:
            raise ValueError("no trained continuation from selected ground entry")
        build.attack(winner, follow, "Capitalize on the established control rather than resetting to unrelated striking.", debts)
    elif grip == "collar" and "knee_body" in winner_tids:
        build.attack(winner, "knee_body", "The earned collar tie directs a body knee.", debts)
    elif grip == "body_lock" and "outside_trip" in winner_tids:
        build.attack(winner, "outside_trip", "The earned body lock loads the near support for a small outer reap.", debts)
    else:
        counter, _, _ = select_attack(k, cards[loser], prediction, winner, ruleset)
        # Keep the alternate branch standing unless the loser has earned the
        # winning control path. The selected outcome never grants capabilities.
        if k.techniques[counter]["kind"] not in ["punch", "kick"]:
            counter = next(t for t in ["cross", "haymaker"] if t in available(k, cards[loser], ruleset))
        build.attack(loser, counter, "Counter the recovery and force a tactical answer; the selected path is still reversible.")
    build.phase = PHASES[6]
    if build.state["range"] in ["ground", "clinch"]:
        build.emit("adjustment", loser, why="Contest the existing connection; the failed attempt does not erase top control or injury.", debts=debts)
    else:
        build.stage(winner, "punch")
        build.action(winner, "pivot", why="Change the attack angle after the counter rather than repeating the same line.", debts=debts)
    build.phase = PHASES[7]
    if build.state["range"] == "ground":
        tid = "ride" if build.state["actors"][winner]["grip"] == "top" and "ride" in winner_tids else "armbar" if "armbar" in winner_tids else "escape"
        build.attack(winner, tid, "Deny the attempted reversal with the previously established control.", debts)
    elif build.state["actors"][winner]["grip"] == "collar" and "knee_body" in winner_tids:
        build.attack(winner, "knee_body", "The defender has not broken the collar tie; repeat the legal torso line.", debts)
    else:
        # Use a defined technique transition when the new angle opens a legal
        # target; the combination remains a contingent path, not a guarantee.
        from .ontology import read
        combos = read(k.root / "data/combinations.json")["combinations"]
        transitions = [c["to"] for c in combos if c["from"] == "pivot" and c["to"] in winner_tids
                       and "pivot" in build.state["actors"][winner]["setups"]]
        follow = [(tid, w) for tid in transitions for w in prediction["accessible_weaknesses"]
                  if w["attacker_id"] == winner and tid in w["technique_ids"]]
        if follow:
            tid, weakness = follow[0]
            build.attack(winner, tid, "The recovered angle enables the defined combination into the loaded support leg.", [weakness["debt_id"]])
        else:
            build.attack(winner, main, "Return to the reachable seam after the opponent adjustment: " + mechanism, debts)
    # Demonstrate an advantage in actual recorded effects. This finite deficit
    # is measured from the ledger, not an invented maximum exchange count.
    while build.state["actors"][winner]["contact_marks"] + build.state["actors"][winner]["control_marks"] <= build.state["actors"][loser]["contact_marks"] + build.state["actors"][loser]["control_marks"]:
        if build.state["range"] == "ground":
            tid = "ride" if build.state["actors"][winner]["grip"] == "top" and "ride" in winner_tids else "armbar" if "armbar" in winner_tids else "escape"
        elif build.state["actors"][winner]["grip"] == "collar" and "knee_body" in winner_tids:
            tid = "knee_body"
        elif build.state["actors"][winner]["grip"] == "body_lock" and "outside_trip" in winner_tids:
            tid = "outside_trip"
        else:
            tid = main
            if k.techniques[tid]["kind"] == "grip":
                owners = [i for i, actor in build.state["actors"].items() if actor["grip"] and actor["grip"] != "controlled"]
                if owners:
                    build.emit("adjustment", owners[0], parameters={"release_grip": True}, why="Release the tie to re-establish a scoring strike.")
                tid = next(t for t in ["body_hook", "haymaker"] if t in winner_tids)
        before = build.state["actors"][winner]["contact_marks"] + build.state["actors"][winner]["control_marks"]
        build.attack(winner, tid, "Establish a demonstrated contact/control advantage in this conditional outcome path.", debts)
        after = build.state["actors"][winner]["contact_marks"] + build.state["actors"][winner]["control_marks"]
        if after <= before:
            raise ValueError("selected path cannot demonstrate a winning advantage")
    build.phase = PHASES[8]
    build.emit("resolution", winner, parameters={"winner_id": winner},
               why="Award the condensed BLOCK exhibition on the recorded contact/control advantage; this is not official commission scoring.", debts=debts)
    build.phase = PHASES[9]
    build.emit("aftermath", winner, why="Separate after the decision. Retain all contact marks, fatigue and established posture.")
    # The time unit derives from requested duration divided by actual events.
    events = []
    state = initial(k, [a, b], ruleset)
    history = {}
    for i, raw in enumerate(build.events):
        e = dict(raw, timestamp=duration * i / len(build.events), duration=duration * (i + 1) / len(build.events) - duration * i / len(build.events))
        e["state_before"] = copy.deepcopy(state)
        state = apply(k, state, cards, e, history, ruleset)
        e["state_after"] = copy.deepcopy(state)
        e["effects"] = {key: value for key, value in state.items() if value != e["state_before"][key]}
        events.append(e)
        history[e["id"]] = e
    return {"version": k.model["version"], "ruleset": ruleset, "duration": duration, "seed": seed, "selection": selection,
            "cards": [a, b], "prediction": prediction, "initial_state": initial(k, [a, b], ruleset), "events": events,
            "final_state": state, "phases": PHASES,
            "geometry": {"units": "meters", "world_axes": "+x screen right; +y away from camera", "limbs": "anatomical left/right resolved at each execution", "arena_half_width_m": k.model["arena_half_width_m"]},
            "fidelity": "Semantically validated staging; no IK, skeletal solver, or biomechanical proof.",
            "conclusion": cards[winner]["name"] + " wins the condensed CANON exhibition by demonstrated contact/control; the original uncalibrated prediction is preserved."}
