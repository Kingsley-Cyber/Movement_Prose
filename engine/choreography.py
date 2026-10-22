def groups(events):
    """Keep a complete action, including its setup/contact/reaction, in one shot."""
    current = []
    for e in events:
        if e["type"] == "setup":
            if current:
                raise ValueError("overlapping choreographed actions")
            current = [e]
        elif current:
            current.append(e)
            if e["type"] == "recovery":
                yield current
                current = []
        else:
            yield [e]
    if current:
        raise ValueError("unfinished choreographed action")


def anatomical(limb, orientation):
    lead = "left" if orientation == "orthodox" else "right"
    rear = "right" if orientation == "orthodox" else "left"
    return limb.replace("lead", lead).replace("rear", rear)


def translate(k, events, style="realistic"):
    if style not in ["realistic", "anime"]:
        raise ValueError("unsupported style; no supernatural technique is defined")
    first, last = events[0], events[-1]
    execution = next((e for e in events if e["type"] in ["execution", "movement"]), None)
    contact = next((e for e in events if e["type"] == "contact"), None)
    tech = k.techniques[execution["technique_id"]] if execution else None
    actor = first["actor_id"]
    phases = []
    mapping = {"preparation": ["setup", "assessment", "adjustment", "activation"],
               "initiation": ["execution", "movement"], "execution": ["execution", "movement"],
               "contact": ["contact"], "reaction": ["reaction"], "recovery": ["recovery", "resolution", "aftermath"]}
    for phase, types in mapping.items():
        matching = [e for e in events if e["type"] in types]
        phases.append({"phase": phase, "event_ids": [e["id"] for e in matching],
                       "timing": [{"start": e["timestamp"], "end": e["timestamp"] + e["duration"]} for e in matching],
                       "instructions": [e["intent"] for e in matching] if matching else ["No " + phase + " action in this beat."]})
    return {"movement_id": "movement." + first["id"], "source_event_ids": [e["id"] for e in events],
            "start": first["timestamp"], "end": last["timestamp"] + last["duration"], "phases": phases,
            "actor_id": actor, "target_id": first["target_id"], "technique_id": tech["id"] if tech else None,
            "limb_action": anatomical(tech["attacking_limb"], execution["state_before"]["actors"][actor]["orientation"]) if tech else "Observe/adjust without an invented attack.",
            "motion_trajectory": tech["direction_trajectory"] if tech else first["intent"],
            "contact": {"event_id": contact["id"], "time": contact["timestamp"], "region": tech["target_region"],
                        "outcome": contact["parameters"]["outcome"], "initiator": actor, "recipient": first["target_id"]} if contact else None,
            "start_actors": first["state_before"]["actors"], "end_actors": last["state_after"]["actors"],
            "weight_support": [{"event_id": e["id"], "support": e["state_after"]["actors"][actor]["foot_support"],
                                "balance": e["state_after"]["actors"][actor]["balance"]} for e in events],
            "environment": "Cage or ring floor; no hand grasps the fence. No props are introduced.",
            "prop_interaction": [],
            "visible_consequences": last["state_after"]["actors"][first["target_id"]]["injuries"],
            "motion_class": "realistic semantic staging" if style == "realistic" else "stylized anime exaggeration",
            "physical_claim": "No skeletal solver; not physically verified. Impossible supernatural action requires an explicitly authored technique, absent in this release."}


def choreograph(k, plan, style="realistic"):
    return {"version": plan["version"], "geometry": plan["geometry"], "fidelity": plan["fidelity"],
            "movements": [translate(k, g, style) for g in groups(plan["events"])]}
