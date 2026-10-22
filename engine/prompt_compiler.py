import json
from .choreography import groups


def anchors(actors, cards):
    return {i: {"position": a["position"], "facing": a["facing"], "orientation": a["orientation"],
                "stance": a["stance"], "guard": a["guard"], "injuries": a["injuries"], "damage": a["damage"],
                "posture": a["posture"], "grip": a["grip"], "clothing": cards[i]["appearance"]["clothing"],
                "props": cards[i]["appearance"]["props"]} for i, a in actors.items()}


def shots(k, plan, choreography):
    cards = {c["fighter_id"]: c for c in plan["cards"]}
    event_groups = list(groups(plan["events"]))
    result = []
    for g, motion in zip(event_groups, choreography["movements"]):
        first, last = g[0], g[-1]
        contact = motion["contact"]
        result.append({"shot_id": "shot." + first["id"], "source_event_ids": motion["source_event_ids"],
                       "duration": motion["end"] - motion["start"], "location": k.model["rulesets"][plan["ruleset"]]["environment"] + " / fixed arena floor",
                       "characters": [{"fighter_id": c["fighter_id"], "name": c["name"], "appearance": c["appearance"]} for c in plan["cards"]],
                       "starting_positions": {i: a["position"] for i, a in first["state_before"]["actors"].items()},
                       "required_action": first["intent"], "motion_trajectory": motion["limb_action"] + ": " + motion["motion_trajectory"],
                       "action_timing": {"start": motion["start"], "end": motion["end"], "phases": motion["phases"]},
                       "contact_timing": contact,
                       "defensive_response": " ".join(e["intent"] for e in g if e["type"] == "reaction") or "Observe the other actor without inventing a counter.",
                       "performance": "Show attention before commitment; show strain and retained contact marks after impact.",
                       "environmental_reaction": "Feet maintain floor contact except the documented single-support beat; falls follow the contact event only.",
                       "camera": {"world_position": [0, -k.model["arena_half_width_m"]], "movement": "fixed side of action axis", "visibility": "both full bodies, active limb and contact region in frame", "cut_rule": "No cut during the contact and immediate reaction."},
                       "lens_intent": "Wide full-body two-shot; prioritize target visibility over facial close-ups.",
                       "animation_style": motion["motion_class"], "lighting": "Stable overhead arena light; preserve clothing colors.",
                       "continuity_constraints": {"start": anchors(first["state_before"]["actors"], cards), "end": anchors(last["state_after"]["actors"], cards),
                                                   "axis": "+x is screen right, +y away from camera; do not reverse the camera side", "environment": "same arena, no props"},
                       "negative_constraints": ["No identity or clothing swaps", "No off-frame contact", "No injury reset", "No new grips or techniques", "No fence grabbing", "No teleporting or unearned flight"],
                       "required_visual_references": [c["appearance"]["identity_anchor"] + "; " + c["appearance"]["clothing"] for c in plan["cards"]] + ["Starting geometry and stance from structured continuity anchors; references are requirements, not supplied generated images."]})
    return {"version": plan["version"], "shots": result}


def compile_shot(shot):
    timing = shot["action_timing"]
    sequence = " ".join(p["phase"] + ": " + " ".join(p["instructions"]) + " at " + json.dumps(p["timing"]) for p in timing["phases"])
    prompt = ("Keep identities " + json.dumps(shot["characters"], ensure_ascii=False) + ". " + shot["animation_style"] + ". "
              + shot["lighting"] + " " + shot["lens_intent"] + " Camera: " + json.dumps(shot["camera"]) + ". "
              + "Begin exactly at " + json.dumps(shot["continuity_constraints"]["start"]) + ". "
              + shot["motion_trajectory"] + " " + sequence + " Contact: " + json.dumps(shot["contact_timing"]) + ". "
              + shot["defensive_response"] + " " + shot["environmental_reaction"] + " Finish at "
              + json.dumps(shot["continuity_constraints"]["end"]) + ". Avoid: " + "; ".join(shot["negative_constraints"]) + ".")
    return {"profile": "model-agnostic-prose", "shot_id": shot["shot_id"], "source_event_ids": shot["source_event_ids"],
            "duration": shot["duration"], "prompt": prompt, "structured_shot": shot,
            "limitations": "Prompt instructions cannot guarantee exact motion, identity, contact timing or physical correctness. No provider-specific capabilities are assumed."}


def validate_visuals(k, plan, choreography, shotlist, prompts):
    # Independent reference/continuity checks supplement deterministic compilation.
    ids = [e["id"] for e in plan["events"]]
    mapped = [i for s in shotlist["shots"] for i in s["source_event_ids"]]
    if mapped != ids:
        raise ValueError("shot coverage or temporal order differs from event graph")
    if len(prompts) != len(shotlist["shots"]):
        raise ValueError("missing compiled prompts")
    contacts = {e["id"]: e for e in plan["events"] if e["type"] == "contact"}
    represented = {}
    previous_end = None
    for s, prompt in zip(shotlist["shots"], prompts):
        k.schema("shot", s)
        if previous_end is not None and s["continuity_constraints"]["start"] != previous_end:
            raise ValueError("shot continuity mismatch")
        previous_end = s["continuity_constraints"]["end"]
        if s["camera"]["visibility"] != "both full bodies, active limb and contact region in frame":
            raise ValueError("camera obscures contact")
        if s["contact_timing"]:
            cid = s["contact_timing"]["event_id"]
            if cid not in contacts or s["contact_timing"]["time"] != contacts[cid]["timestamp"]:
                raise ValueError("contact timing differs from fight")
            represented[cid] = s["shot_id"]
        if prompt != compile_shot(s):
            raise ValueError("compiled prompt lost structured constraints")
    if set(represented) != set(contacts):
        raise ValueError("missing contact visualization")
    from .choreography import choreograph
    style = "anime" if choreography["movements"][0]["motion_class"] == "stylized anime exaggeration" else "realistic"
    if choreography != choreograph(k, plan, style) or shotlist != shots(k, plan, choreography):
        raise ValueError("choreography/shot differs from source events")
    return {"status": "PASS", "shots": len(shotlist["shots"]), "prompts": len(prompts), "contacts_visible": len(represented)}
