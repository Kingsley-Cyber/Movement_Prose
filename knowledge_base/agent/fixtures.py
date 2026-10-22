"""Reproducible IRs built from the bundle's own examples."""
import json
from pathlib import Path

from . import BUNDLE_DIR
from .ir import IR, Clip, Event, Selection


def load_examples(bundle_dir=BUNDLE_DIR):
    return json.loads((Path(bundle_dir) / "example_payloads.json").read_text(encoding="utf-8"))


def example_ir(example, engine_profile_id="generic_web_ui"):
    """One bundle example as a single-event IR (actor-keyed like the validator: actor A, target B)."""
    b = example["bindings"]
    entities = {"A": b["actor"], "B": b["target"]}
    end = max(s["end_frame"] for s in example["selections"])
    event = Event(event_id=example["example_id"], actor_id="A", target_id="B", moment_type=example["moment_type"],
                  start_frame=0, end_frame=end, declared_prerequisites=list(example.get("declared_prerequisites", [])))
    selections = [Selection(directive_id=s["directive_id"], event_id=event.event_id, actor_id=s.get("actor_id"),
                            target_id=s.get("target_id"), start_frame=s["start_frame"], end_frame=s["end_frame"])
                  for s in example["selections"]]
    return IR(request=example["example_id"], scene_context=example["context"], entities=entities,
              clip=Clip(editorial_fps=example.get("editorial_fps", 24), duration_seconds=end / 24.0, frame_count=end),
              events=[event], selections=selections, contact_origins={event.event_id: b.get("contact_origin", "")},
              engine_profile_id=engine_profile_id)


def sequence_plan_ir(bundle_dir=BUNDLE_DIR, taste_profile_id="raw_street_brawl", engine_profile_id="generic_web_ui"):
    """Run 001: the bundle's 7-event single exchange, selections from the 4 examples re-bound per event plus
    catalog rows for the three events the examples do not cover (A follow-through, B recoil, B recovery)."""
    doc = load_examples(bundle_dir)
    plan = doc["sequence_plan"]
    ex = dict((e["example_id"], e) for e in doc["examples"])
    windup = ex["windup_eight_slots"]["bindings"]
    entities = {"A": windup["actor"], "B": windup["target"]}
    events = [Event(event_id=e["event_id"], actor_id=e["actor_id"], target_id=e.get("target_id"), moment_type=e["moment_type"],
                    start_frame=e["start_frame"], end_frame=e["end_frame"], depends_on=e.get("depends_on")) for e in plan["events"]]
    by_id = dict((e.event_id, e) for e in events)
    by_id["a_finish"].inherit_from = "a_strike"
    by_id["a_guard"].inherit_from = "a_finish"
    by_id["b_guard"].inherit_from = "b_recoil"
    selections = []

    def take(example_id, event_id, actor="A", target="B"):
        ev = by_id[event_id]
        for s in ex[example_id]["selections"]:
            selections.append(Selection(directive_id=s["directive_id"], event_id=event_id, actor_id=actor, target_id=target,
                                        start_frame=ev.start_frame, end_frame=ev.end_frame))

    def pick(directive_id, event_id, actor="A", target="B", start=None, end=None):
        ev = by_id[event_id]
        selections.append(Selection(directive_id=directive_id, event_id=event_id, actor_id=actor, target_id=target,
                                    start_frame=ev.start_frame if start is None else start,
                                    end_frame=ev.end_frame if end is None else end))

    take("windup_eight_slots", "a_prepare")
    take("travel_eight_slots", "a_strike")
    take("block_contact_overrides", "block_contact")
    for d in ("aa_subject_costume_attachment", "aa_action_followthrough_arc", "aa_time_overlap_offsets"):
        pick(d, "a_finish")
    for d in ("aa_subject_recoil_identity", "aa_action_absorb_recoil", "aa_time_recoil_spacing"):
        pick(d, "b_recoil")
    # the heel slide ends when A's guard recovery (and its settled-debris row on the global environment slot) begins
    pick("aa_env_skid_gouge", "b_recoil", end=by_id["a_guard"].start_frame)
    take("recovery_eight_slots", "a_guard")
    for d in ("aa_subject_recovery_model", "aa_action_guard_recovery"):
        pick(d, "b_guard", actor="B", target="A")
    context = ex["windup_eight_slots"]["context"].split(" This shot")[0]
    return IR(request="One strike and one block: A prepares, drives one straight strike, B blocks with a forearm at a visible "
                      "contact point, A finishes while B recoils into a support step, both recover their guard.",
              scene_context=context, entities=entities,
              clip=Clip(editorial_fps=plan["editorial_fps"], duration_seconds=plan["duration_seconds"], frame_count=plan["frame_count"]),
              events=events, selections=selections, contact_origins={"block_contact": windup["contact_origin"]},
              editorial_operations=list(plan.get("editorial_operations", [])),
              taste_profile_id=taste_profile_id, matched_tags=["raw", "street", "brawl"], engine_profile_id=engine_profile_id)
