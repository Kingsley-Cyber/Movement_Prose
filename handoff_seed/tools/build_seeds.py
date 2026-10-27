"""Build validated backfill seed data for the Movement_Prose Fight Simulator v2.1 handoff.

Reads the live v2 data from the repo (to preserve existing calibrated values), adds the
new fields/techniques/positions/rulesets/model constants, cross-validates every reference,
and writes JSON seeds + markdown tables used by the handoff document.

Usage: python3 build_seeds.py <repo_root> <out_dir>
"""
from __future__ import annotations

import copy
import json
import sys
from collections import OrderedDict, defaultdict
from pathlib import Path

REPO = Path(sys.argv[1])
OUT = Path(sys.argv[2])
OUT.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Vocabulary
# ---------------------------------------------------------------------------
LANES = ["head_straight", "head_hook", "head_uppercut", "body", "leg", "entry", "clinch", "single_support"]
NONLANE = ["space", "ground"]
OPENINGS = LANES + ["vision", "recovery", "tempo", "angle", "wall", "ground"]
RULESETS = ["boxing", "kickboxing", "muay_thai", "mma", "street", "lethwei"]
RANGES = ["outside", "kick", "punch", "close", "clinch", "ground"]
KINDS = ["movement", "feint", "punch", "elbow", "kick", "knee", "defense", "grip", "takedown", "sweep",
         "control", "ground_strike", "submission", "escape"]
LINES = ["lead_straight", "rear_straight", "lead_round", "rear_round", "lead_uppercut", "rear_uppercut", "overhand",
         "lead_round_kick", "rear_round_kick", "lead_linear_kick", "rear_linear_kick", "spinning", "knee", "elbow",
         "grapple", "ground", "none"]
TSR = ["opposite_of_limb", "center", "defender_lead", "defender_rear", "grip_side", "none"]
USAGE = ["attack", "counter", "defense", "both", "movement"]
VMIN = ["grounded", "athletic", "aerial"]
RESOLUTION = ["strike", "grapple", "movement", "defense", "submission"]
REGIONS = ["space", "angle", "vision", "head", "body", "leg", "hips", "neck_arm"]  # current schema enum
DTYPES = ["none", "impact", "buildup", "stamina_drain", "control", "submission"]  # current schema enum; cuts use cut_chance

existing_v2 = {t["id"]: t for t in json.load(open(REPO / "data/techniques_v2.json"))["techniques"]}
v1_tech = {t["id"]: t for t in json.load(open(REPO / "data/techniques.json"))["techniques"]}
debts = json.load(open(REPO / "data/debt_registry.json"))["debts"]
options = {o["id"]: o for o in json.load(open(REPO / "data/engine_index.json"))["options"]}
model_v2 = json.load(open(REPO / "data/model_v2.json"))
existing_pos = json.load(open(REPO / "data/positions.json"))
EXISTING_POS = {p["id"]: p for p in existing_pos["positions"]}
EXISTING_TR = existing_pos["transitions"]

CAPS_EXISTING = {"anti_grappling", "basic_movement", "bjj", "boxing", "cage_plum", "clinch", "inside_combinations",
                 "judo", "karate", "kickboxing", "pressure_footwork", "sanda", "shield", "switch_step",
                 "untrained_striking", "wall_boxing", "wrestling"}
CAPS_NEW = OrderedDict([
    ("muay_thai", "Full Muay Thai school: shin kicks, teeps, straight and clinch knees, elbows, plum, check, catch-and-dump."),
    ("acrobatics", "Anime/acrobatic movement school: cartwheel and wall-assisted kicks. Requires airborne_training and an aerial vertical mode."),
    ("counter_boxing", "PROPOSAL (owner decision D7): counter-punching school for Darius Reed's hollow second slot: pull counter and check hook."),
])
ALL_CAPS = CAPS_EXISTING | set(CAPS_NEW)

STRIKE_SCHOOLS = ["boxing", "kickboxing", "muay_thai", "karate", "sanda", "untrained_striking", "wrestling"]


def frames(s, e, h, r):
    return {"setup_frames": s, "execution_frames": e, "contact_hold_frames": h, "recovery_frames": r}


def rec(window, lanes, pen):
    return {"window_type": window, "exposed_lanes": lanes, "readiness_penalty": pen}


# ---------------------------------------------------------------------------
# New fields for the 45 existing techniques (values preserve current behaviour)
# accuracy_base / energy_mult: CURRENT engine behaviour is accuracy 0 (haymaker -0.22) and no
# per-technique energy. "rec_" columns are the recommended values to switch on in Phase P7/P5.
# ---------------------------------------------------------------------------
X = {}


def ext(tid, **kw):
    X[tid] = kw


ext("step", side="none", limb="feet", line="none", tsr="none", usage="movement", resolution="movement", energy=0.25, exploits=["tempo"])
ext("retreat", side="none", limb="feet", line="none", tsr="none", usage="movement", resolution="movement", energy=0.25, exploits=[])
ext("pivot", side="none", limb="feet", line="none", tsr="none", usage="movement", resolution="movement", energy=0.30, exploits=["angle"])
ext("switch_step", side="none", limb="feet", line="none", tsr="none", usage="movement", resolution="movement", energy=0.30, exploits=["angle"])
ext("feint", side="lead", limb="lead hand", line="none", tsr="none", usage="attack", resolution="movement", energy=0.20, exploits=["vision", "tempo"])
ext("jab", side="lead", limb="fist", line="lead_straight", tsr="center", energy=0.55, rec_acc=0.15, exploits=["head_straight", "tempo"], caps_add=["kickboxing", "muay_thai", "karate", "sanda"])
ext("cross", side="rear", limb="fist", line="rear_straight", tsr="center", energy=0.80, rec_acc=0.0, exploits=["head_straight", "recovery"], caps_add=["kickboxing", "muay_thai", "karate", "sanda"])
ext("hook", side="lead", limb="fist", line="lead_round", tsr="opposite_of_limb", energy=0.85, rec_acc=-0.05, exploits=["head_hook", "angle"], caps_add=["kickboxing", "muay_thai", "sanda"])
ext("body_hook", side="lead", limb="fist", line="lead_round", tsr="opposite_of_limb", energy=0.85, rec_acc=0.0, exploits=["body"], caps_add=["kickboxing", "muay_thai", "sanda"])
ext("uppercut", side="rear", limb="fist", line="rear_uppercut", tsr="center", energy=0.85, rec_acc=-0.05, exploits=["head_uppercut"], caps_add=["kickboxing", "muay_thai"])
ext("haymaker", side="rear", limb="fist", line="overhand", tsr="opposite_of_limb", energy=1.25, acc=-0.22, rec_acc=-0.22, exploits=["head_hook"])
ext("parry", side="rear", limb="palm", line="none", tsr="none", usage="defense", resolution="defense", energy=0.30, exploits=[], caps_add=["kickboxing", "muay_thai", "karate", "sanda"])
ext("shell_block", side="both", limb="forearms", line="none", tsr="none", usage="defense", resolution="defense", energy=0.35, exploits=[], caps_add=["kickboxing", "muay_thai"])
ext("shield_frame", side="both", limb="forearms", line="none", tsr="none", usage="defense", resolution="defense", energy=0.35, exploits=["angle"])
ext("slip", side="none", limb="torso", line="none", tsr="none", usage="defense", resolution="defense", energy=0.35, exploits=[])
ext("check", side="lead", limb="shin", line="none", tsr="none", usage="defense", resolution="defense", energy=0.40, exploits=[], caps_add=["muay_thai"])
ext("low_kick", side="rear", limb="shin", line="rear_round_kick", tsr="opposite_of_limb", energy=0.95, rec_acc=0.05, catch=0.18, exploits=["leg"], caps_add=["muay_thai", "sanda", "karate"])
ext("body_kick", side="rear", limb="shin", line="rear_round_kick", tsr="opposite_of_limb", energy=1.10, rec_acc=0.0, catch=0.44, exploits=["body"], caps_add=["muay_thai", "sanda"])
ext("teep", side="lead", limb="foot", line="lead_linear_kick", tsr="center", energy=0.75, rec_acc=0.05, catch=0.32, exploits=["body", "entry"], caps_add=["muay_thai", "sanda"], stop_hit=True)
ext("side_kick", side="lead", limb="foot", line="lead_linear_kick", tsr="center", energy=1.00, rec_acc=0.0, catch=0.32, exploits=["body", "entry"], caps_add=["sanda"], stop_hit=True)
ext("sprawl", side="none", limb="hips", line="none", tsr="none", usage="defense", resolution="defense", energy=0.60, exploits=[])
ext("pummel", side="both", limb="arms", line="grapple", tsr="grip_side", usage="both", resolution="grapple", energy=0.90, exploits=["clinch"], caps_add=["muay_thai"])
ext("collar_tie", side="both", limb="arms", line="grapple", tsr="grip_side", resolution="grapple", energy=0.80, exploits=["clinch"], caps_add=["muay_thai"], result_pos="collar_tie")
ext("cage_plum", side="both", limb="arms", line="grapple", tsr="grip_side", resolution="grapple", energy=0.90, exploits=["clinch", "wall"], result_pos="thai_plum")
ext("knee_body", side="rear", limb="knee", line="knee", tsr="center", energy=0.95, rec_acc=0.05, catch=0.0, exploits=["body", "clinch"], caps_add=["muay_thai"])
ext("body_lock", side="both", limb="arms", line="grapple", tsr="grip_side", resolution="grapple", energy=1.00, exploits=["clinch"], result_pos="front_body_lock")
ext("double_leg", side="both", limb="arms", line="grapple", tsr="grip_side", resolution="grapple", energy=1.60, rec_acc=-0.05, exploits=["entry"], result_pos="shot_in")
ext("single_leg", side="lead", limb="arms", line="grapple", tsr="defender_lead", resolution="grapple", energy=1.45, rec_acc=0.0, exploits=["entry", "single_support"], result_pos="shot_in")
ext("outside_trip", side="lead", limb="leg", line="grapple", tsr="grip_side", resolution="grapple", energy=1.25, exploits=["clinch", "single_support"], result_pos="side_control", legal=["muay_thai", "mma", "street"])
ext("sanda_sweep", side="lead", limb="leg", line="grapple", tsr="grip_side", resolution="grapple", energy=1.10, exploits=["single_support"], result_pos="half_guard", legal=["muay_thai", "mma", "street"], requires_position=["caught_single_leg"])
ext("ride", side="both", limb="hips", line="ground", tsr="none", resolution="grapple", energy=1.00, exploits=["ground"], requires_position=["closed_guard:top", "half_guard:top", "side_control:top", "mount:top", "back_control:top", "turtle:top"])
ext("guard_pull", side="both", limb="legs", line="grapple", tsr="none", resolution="grapple", energy=0.90, exploits=["clinch"], result_pos="closed_guard")
ext("armbar", side="both", limb="hips", line="ground", tsr="grip_side", joint="elbow", resolution="submission", energy=1.20, exploits=["ground"], requires_position=["closed_guard:bottom", "mount:top", "side_control:top"])
ext("escape", side="none", limb="hips", line="ground", tsr="none", usage="both", resolution="grapple", energy=1.20, exploits=[], requires_position=["any_ground:bottom"])
ext("wall_tie", side="both", limb="forearms", line="grapple", tsr="grip_side", resolution="grapple", energy=0.90, exploits=["wall", "clinch"], result_pos="wall_pinned", requires_wall=True)
ext("wall_punch", side="lead", limb="fist", line="lead_round", tsr="opposite_of_limb", energy=0.75, rec_acc=0.05, exploits=["wall", "body"], requires_position=["wall_pinned"])
ext("head_kick", side="rear", limb="shin", line="rear_round_kick", tsr="opposite_of_limb", energy=1.25, rec_acc=-0.12, catch=0.12, exploits=["head_hook"], caps_add=["muay_thai"])
ext("switch_kick", side="lead", limb="shin", line="lead_round_kick", tsr="opposite_of_limb", energy=1.15, rec_acc=-0.03, catch=0.44, exploits=["body"], caps_set=["kickboxing", "muay_thai", "karate"])
ext("spinning_back_kick", side="rear", limb="heel", line="spinning", tsr="center", energy=1.30, rec_acc=-0.10, catch=0.20, exploits=["body", "entry"], vmin="grounded")
ext("axe_kick", side="rear", limb="heel", line="rear_linear_kick", tsr="center", energy=1.30, rec_acc=-0.10, catch=0.10, exploits=["head_straight", "vision"], vmin="grounded")
ext("jumping_knee", side="rear", limb="knee", line="knee", tsr="center", energy=1.50, rec_acc=-0.12, catch=0.0, exploits=["entry", "head_uppercut"], vmin="athletic",
    airborne={"takeoff_frames": 3, "apex_frames": 4, "landing_frames": 5, "landing_exposed_lanes": ["entry", "single_support", "head_hook"], "landing_penalty": 1.10},
    caps_set=["kickboxing", "muay_thai", "clinch"], requires_airborne_training=True)
ext("kick_catch", side="both", limb="arms", line="none", tsr="none", usage="defense", resolution="defense", energy=0.45, exploits=["single_support"], caps_add=["muay_thai"], result_pos="caught_single_leg")
ext("lean_back", side="none", limb="torso", line="none", tsr="none", usage="defense", resolution="defense", energy=0.30, exploits=[], caps_set=["boxing", "basic_movement"])
ext("evade_step_back", side="none", limb="feet", line="none", tsr="none", usage="defense", resolution="defense", energy=0.30, exploits=[])
ext("jam_step", side="none", limb="arms", line="none", tsr="none", usage="defense", resolution="defense", energy=0.45, exploits=["entry"], caps_set=["clinch", "wrestling", "anti_grappling", "muay_thai"])

# ---------------------------------------------------------------------------
# New techniques
# ---------------------------------------------------------------------------
NEW = []


def new(tid, name, kind, caps, rng, lane, region, dmg, dtype, fr, rc, *, side, limb, surface, line, tsr,
        energy, acc=0.0, legal=None, vmin="grounded", usage="attack", resolution="strike", catch=None,
        cut=0.0, joint="none", airborne=None, requires_position=None, requires_grip=None, result_pos=None,
        counters=None, exploits=None, notes="", requires_wall=False, requires_airborne_training=False,
        stop_hit=False, proposal=False):
    NEW.append({
        "id": tid, "name": name, "kind": kind, "required_capabilities": caps, "required_range": rng,
        "attack_lane": lane, "target_region": region, "base_damage": dmg, "damage_type": dtype,
        "frame_costs": fr, "recovery_exposure": rc,
        "biomechanics": {"attacking_limb": limb, "striking_surface": surface, "path": notes or name,
                         "height": "high" if region == "head" else ("low" if region == "leg" else "mid"),
                         "ending": "snap_back", "vertical_mode_required": vmin},
        "counters": counters or [],
        "_x": dict(side=side, limb=limb, line=line, tsr=tsr, energy=energy, acc=acc, rec_acc=acc, legal=legal,
                   vmin=vmin, usage=usage, resolution=resolution, catch=catch, cut=cut, joint=joint,
                   airborne=airborne, requires_position=requires_position, requires_grip=requires_grip,
                   result_pos=result_pos, exploits=exploits or [], requires_wall=requires_wall,
                   requires_airborne_training=requires_airborne_training, stop_hit=stop_hit, proposal=proposal),
    })


ARM = ["head_straight", "head_hook", "body"]
SLR = ["single_support", "leg", "head_straight", "entry"]
# Punches
new("rear_hook", "Rear hook", "punch", ["boxing", "kickboxing", "muay_thai"], ["punch", "close"], "head_hook", "head", 2.8, "impact", frames(6, 8, 3, 10), rec("extended_arm_recovery", ARM, 0.8),
    side="rear", limb="fist", surface="rear_knuckles", line="rear_round", tsr="opposite_of_limb", energy=0.95, acc=-0.06, counters=["shell_block", "bob_weave"], exploits=["head_hook"])
new("lead_uppercut", "Lead uppercut", "punch", ["boxing", "kickboxing", "muay_thai"], ["punch", "close"], "head_uppercut", "head", 2.3, "impact", frames(5, 7, 3, 9), rec("extended_arm_recovery", ARM, 0.65),
    side="lead", limb="fist", surface="lead_knuckles", line="lead_uppercut", tsr="center", energy=0.85, acc=-0.03, counters=["shell_block", "parry"], exploits=["head_uppercut"])
new("overhand", "Overhand", "punch", ["boxing", "kickboxing", "muay_thai"], ["punch"], "head_hook", "head", 3.0, "impact", frames(7, 9, 3, 12), rec("wide_swing_recovery", ["head_straight", "head_hook", "entry", "body"], 1.05),
    side="rear", limb="fist", surface="rear_knuckles", line="overhand", tsr="opposite_of_limb", energy=1.05, acc=-0.10, counters=["slip", "bob_weave", "shell_block"], exploits=["head_hook", "vision"])
new("body_jab", "Body jab", "punch", ["boxing", "kickboxing", "muay_thai", "karate", "sanda"], ["punch"], "body", "body", 1.1, "buildup", frames(3, 5, 2, 6), rec("short_retract", ["head_hook", "head_straight"], 0.45),
    side="lead", limb="fist", surface="lead_knuckles", line="lead_straight", tsr="center", energy=0.60, acc=0.05, counters=["parry", "shell_block"], exploits=["body", "tempo", "vision"])
new("rear_body_hook", "Rear body hook", "punch", ["boxing", "kickboxing", "muay_thai"], ["punch", "close"], "body", "body", 2.6, "stamina_drain", frames(6, 8, 3, 9), rec("extended_arm_recovery", ARM, 0.75),
    side="rear", limb="fist", surface="rear_knuckles", line="rear_round", tsr="opposite_of_limb", energy=0.95, acc=-0.03, counters=["shell_block"], exploits=["body"])
new("shovel_hook", "Shovel hook", "punch", ["inside_combinations"], ["close", "clinch"], "body", "body", 2.4, "stamina_drain", frames(4, 6, 3, 7), rec("short_retract", ["head_straight", "head_hook"], 0.45),
    side="lead", limb="fist", surface="lead_knuckles", line="lead_round", tsr="opposite_of_limb", energy=0.80, acc=0.04, counters=["shell_block", "pummel"], exploits=["body", "clinch"])
new("short_uppercut", "Short uppercut", "punch", ["inside_combinations"], ["close", "clinch"], "head_uppercut", "head", 2.4, "impact", frames(4, 6, 3, 7), rec("short_retract", ["head_hook", "body"], 0.45),
    side="rear", limb="fist", surface="rear_knuckles", line="rear_uppercut", tsr="center", energy=0.80, acc=0.04, counters=["shell_block"], exploits=["head_uppercut", "clinch"])
new("check_hook", "Check hook", "punch", ["counter_boxing"], ["punch", "close"], "head_hook", "head", 2.4, "impact", frames(3, 6, 3, 8), rec("short_retract", ["body", "head_straight"], 0.5),
    side="lead", limb="fist", surface="lead_knuckles", line="lead_round", tsr="opposite_of_limb", energy=0.80, acc=0.08, usage="counter", counters=["shell_block"], exploits=["recovery", "angle", "head_hook"], proposal=True)
new("pull_counter", "Pull counter", "punch", ["counter_boxing"], ["punch"], "head_straight", "head", 2.2, "impact", frames(3, 6, 3, 8), rec("extended_arm_recovery", ARM, 0.6),
    side="rear", limb="fist", surface="rear_knuckles", line="rear_straight", tsr="center", energy=0.75, acc=0.08, usage="counter", counters=["parry"], exploits=["recovery", "head_straight"], proposal=True)
new("shield_counter_hook", "52 lateral counter", "punch", ["shield"], ["punch", "close"], "head_hook", "head", 2.2, "impact", frames(3, 6, 3, 8), rec("short_retract", ["body"], 0.45),
    side="lead", limb="fist", surface="lead_knuckles", line="lead_round", tsr="opposite_of_limb", energy=0.70, acc=0.06, usage="counter", counters=["shell_block"], exploits=["recovery", "angle"],
    notes="Forearm wedge redirects the punch, then a short lateral hook returns along the opened line.")
new("superman_punch", "Superman punch", "punch", ["kickboxing", "muay_thai"], ["kick", "punch"], "head_straight", "head", 2.9, "impact", frames(7, 8, 3, 13), rec("airborne_landing_recovery", ["entry", "single_support", "head_hook"], 1.2),
    side="rear", limb="fist", surface="rear_knuckles", line="rear_straight", tsr="center", energy=1.20, acc=-0.04, vmin="athletic", requires_airborne_training=True,
    airborne={"takeoff_frames": 3, "apex_frames": 3, "landing_frames": 5, "landing_exposed_lanes": ["entry", "single_support", "head_hook"], "landing_penalty": 1.0},
    counters=["slip", "evade_step_back"], exploits=["vision", "head_straight"], notes="Fake knee or kick, hop, then a rear straight from the air.")
new("spinning_backfist", "Spinning backfist", "punch", ["kickboxing", "karate"], ["punch"], "head_hook", "head", 2.8, "impact", frames(6, 8, 3, 12), rec("wide_swing_recovery", ["entry", "body", "head_straight"], 1.2),
    side="rear", limb="fist", surface="back_of_fist", line="spinning", tsr="opposite_of_limb", energy=1.10, acc=-0.08, legal=["kickboxing", "mma", "street"], counters=["shell_block", "evade_step_back"], exploits=["head_hook", "angle"])
new("wild_hook", "Wild hook", "punch", ["untrained_striking"], ["punch", "close"], "head_hook", "head", 2.6, "impact", frames(7, 9, 3, 13), rec("wide_swing_recovery", ["head_straight", "head_hook", "entry", "body"], 1.35),
    side="lead", limb="fist", surface="lead_fist_loop", line="lead_round", tsr="opposite_of_limb", energy=1.10, acc=-0.18, counters=["shell_block", "slip"], exploits=["head_hook"])
new("brawler_straight", "Brawler straight", "punch", ["untrained_striking"], ["punch"], "head_straight", "head", 2.2, "impact", frames(6, 8, 3, 10), rec("extended_arm_recovery", ARM, 0.85),
    side="rear", limb="fist", surface="rear_fist", line="rear_straight", tsr="center", energy=0.95, acc=-0.10, counters=["parry", "slip"], exploits=["head_straight"])
new("shove", "Shove", "movement", ["untrained_striking", "basic_movement"], ["punch", "close", "clinch"], "entry", "body", 0.0, "none", frames(3, 6, 2, 5), rec("short_retract", ["head_straight"], 0.3),
    side="both", limb="palms", surface="palms", line="none", tsr="center", energy=0.60, acc=0.05, usage="both", resolution="movement", counters=["pummel"], exploits=["tempo", "wall"],
    notes="Two-hand push: moves the opponent back one range band and breaks a clinch on success.")
new("headbutt", "Headbutt", "punch", ["untrained_striking", "clinch"], ["close", "clinch"], "head_straight", "head", 2.8, "impact", frames(4, 5, 3, 8), rec("short_retract", ["head_uppercut"], 0.6),
    side="none", limb="forehead", surface="forehead", line="none", tsr="center", energy=0.80, acc=0.0, legal=["street"], cut=0.15, counters=["pummel"], exploits=["clinch", "head_straight"])
# Elbows
new("horizontal_elbow", "Horizontal elbow", "elbow", ["muay_thai"], ["close", "clinch"], "head_hook", "head", 2.6, "impact", frames(4, 6, 3, 8), rec("short_retract", ["head_straight", "body"], 0.5),
    side="rear", limb="elbow", surface="elbow_point", line="elbow", tsr="opposite_of_limb", energy=0.85, acc=0.02, cut=0.25, counters=["shell_block", "pummel"], exploits=["head_hook", "clinch"])
new("uppercut_elbow", "Uppercut elbow", "elbow", ["muay_thai"], ["close", "clinch"], "head_uppercut", "head", 2.5, "impact", frames(4, 6, 3, 8), rec("short_retract", ["head_hook", "body"], 0.5),
    side="rear", limb="elbow", surface="elbow_point", line="elbow", tsr="center", energy=0.85, acc=0.0, cut=0.15, counters=["shell_block"], exploits=["head_uppercut", "clinch"])
new("spinning_elbow", "Spinning elbow", "elbow", ["muay_thai"], ["punch", "close"], "head_hook", "head", 3.2, "impact", frames(6, 8, 3, 12), rec("wide_swing_recovery", ["entry", "body", "head_straight"], 1.25),
    side="rear", limb="elbow", surface="elbow_point", line="spinning", tsr="opposite_of_limb", energy=1.10, acc=-0.08, cut=0.30, counters=["shell_block", "evade_step_back"], exploits=["head_hook", "angle"])
# Kicks
new("calf_kick", "Calf kick", "kick", ["kickboxing", "muay_thai", "sanda"], ["kick", "punch"], "leg", "leg", 2.0, "buildup", frames(4, 7, 3, 8), rec("single_leg_recovery", SLR, 0.85),
    side="rear", limb="shin", surface="lower_shin", line="rear_round_kick", tsr="opposite_of_limb", energy=0.85, acc=0.05, catch=0.12, counters=["check"], exploits=["leg"])
new("oblique_kick", "Oblique kick", "kick", ["kickboxing", "karate"], ["kick"], "leg", "leg", 1.6, "buildup", frames(3, 6, 2, 6), rec("single_leg_recovery", ["single_support", "head_straight"], 0.6),
    side="lead", limb="foot", surface="sole", line="lead_linear_kick", tsr="defender_lead", joint="knee", energy=0.65, acc=0.08, catch=0.08, counters=["evade_step_back"], exploits=["leg", "entry"], stop_hit=True,
    notes="Lead-leg stomp to the front of the opponent's lead knee; doubles as a stop-hit on entries.")
new("front_kick", "Front kick", "kick", ["karate"], ["kick"], "body", "body", 2.2, "impact", frames(5, 7, 3, 9), rec("single_leg_recovery", SLR, 0.75),
    side="rear", limb="foot", surface="ball_of_foot", line="rear_linear_kick", tsr="center", energy=0.90, acc=0.02, catch=0.30, counters=["parry", "evade_step_back"], exploits=["body", "entry"], stop_hit=True)
new("spinning_hook_kick", "Spinning hook kick", "kick", ["karate"], ["kick"], "head_hook", "head", 3.4, "impact", frames(8, 10, 4, 16), rec("wide_swing_recovery", ["single_support", "entry", "body"], 1.6),
    side="rear", limb="heel", surface="heel", line="spinning", tsr="opposite_of_limb", energy=1.35, acc=-0.12, catch=0.06, counters=["evade_step_back", "jam_step"], exploits=["head_hook"])
new("question_mark_kick", "Question-mark kick", "kick", ["karate"], ["kick"], "head_hook", "head", 3.2, "impact", frames(7, 9, 4, 14), rec("single_leg_recovery", SLR, 1.35),
    side="rear", limb="shin", surface="instep", line="rear_round_kick", tsr="opposite_of_limb", energy=1.25, acc=0.02, catch=0.10, counters=["lean_back", "evade_step_back"], exploits=["head_hook", "vision"],
    notes="Chambers like a body kick, turns over to the head at the last moment.")
new("jumping_switch_kick", "Jumping switch kick", "kick", ["karate", "kickboxing"], ["kick"], "head_hook", "head", 3.0, "impact", frames(7, 9, 3, 15), rec("airborne_landing_recovery", ["single_support", "entry"], 1.3),
    side="lead", limb="shin", surface="instep", line="lead_round_kick", tsr="opposite_of_limb", energy=1.45, acc=-0.10, catch=0.15, vmin="athletic", requires_airborne_training=True,
    airborne={"takeoff_frames": 3, "apex_frames": 3, "landing_frames": 5, "landing_exposed_lanes": ["single_support", "entry"], "landing_penalty": 1.1},
    counters=["evade_step_back"], exploits=["head_hook"])
new("flying_side_kick", "Flying side kick", "kick", ["karate"], ["outside", "kick"], "body", "body", 3.4, "impact", frames(8, 10, 4, 18), rec("airborne_landing_recovery", ["single_support", "entry", "head_straight"], 1.5),
    side="lead", limb="foot", surface="blade_of_foot", line="lead_linear_kick", tsr="center", energy=1.60, acc=-0.12, catch=0.15, vmin="athletic", requires_airborne_training=True,
    airborne={"takeoff_frames": 4, "apex_frames": 3, "landing_frames": 6, "landing_exposed_lanes": ["single_support", "entry", "head_straight"], "landing_penalty": 1.3},
    counters=["evade_step_back", "pivot"], exploits=["entry", "body"])
new("cartwheel_kick", "Cartwheel kick", "kick", ["acrobatics"], ["kick"], "head_hook", "head", 3.0, "impact", frames(9, 12, 4, 18), rec("airborne_landing_recovery", ["single_support", "entry", "body"], 1.6),
    side="rear", limb="heel", surface="heel", line="spinning", tsr="opposite_of_limb", energy=1.70, acc=-0.14, catch=0.05, vmin="aerial", requires_airborne_training=True,
    airborne={"takeoff_frames": 4, "apex_frames": 4, "landing_frames": 6, "landing_exposed_lanes": ["single_support", "entry", "body"], "landing_penalty": 1.4},
    counters=["evade_step_back", "jam_step"], exploits=["head_hook", "vision"])
new("wall_run_kick", "Wall-run kick", "kick", ["acrobatics"], ["punch", "kick"], "head_hook", "head", 3.3, "impact", frames(9, 11, 4, 18), rec("airborne_landing_recovery", ["single_support", "entry", "body"], 1.6),
    side="rear", limb="shin", surface="instep", line="rear_round_kick", tsr="opposite_of_limb", energy=1.80, acc=-0.12, catch=0.05, vmin="aerial", requires_airborne_training=True, requires_wall=True,
    airborne={"takeoff_frames": 5, "apex_frames": 4, "landing_frames": 6, "landing_exposed_lanes": ["single_support", "entry", "body"], "landing_penalty": 1.4},
    counters=["evade_step_back"], exploits=["head_hook", "wall"], notes="Runs a step up the wall (requires the attacker to be near a wall) and kicks on the way down.")
# Knees
new("straight_knee", "Straight knee", "knee", ["muay_thai", "kickboxing"], ["close", "punch"], "body", "body", 2.6, "stamina_drain", frames(4, 7, 3, 9), rec("single_leg_recovery", ["single_support", "head_straight"], 0.7),
    side="rear", limb="knee", surface="kneecap", line="knee", tsr="center", energy=0.95, acc=0.03, catch=0.05, counters=["jam_step", "shell_block"], exploits=["body", "entry"], stop_hit=True)
new("knee_head_clinch", "Clinch knee to head", "knee", ["muay_thai"], ["clinch"], "head_uppercut", "head", 3.4, "impact", frames(5, 7, 3, 9), rec("single_leg_recovery", ["single_support"], 0.6),
    side="rear", limb="knee", surface="kneecap", line="knee", tsr="center", energy=1.05, acc=0.0, catch=0.0, legal=["muay_thai", "mma", "street"], requires_grip=["collar", "plum"], counters=["pummel"], exploits=["head_uppercut", "clinch"])
new("flying_knee", "Flying knee", "knee", ["muay_thai", "kickboxing"], ["kick", "punch"], "head_uppercut", "head", 3.8, "impact", frames(8, 10, 4, 18), rec("airborne_landing_recovery", ["entry", "single_support", "head_hook"], 1.5),
    side="rear", limb="knee", surface="kneecap", line="knee", tsr="center", energy=1.60, acc=-0.12, catch=0.04, vmin="athletic", requires_airborne_training=True,
    airborne={"takeoff_frames": 4, "apex_frames": 3, "landing_frames": 6, "landing_exposed_lanes": ["entry", "single_support", "head_hook"], "landing_penalty": 1.2},
    counters=["evade_step_back", "pivot"], exploits=["entry", "head_uppercut"])
# Defenses
new("bob_weave", "Bob and weave", "defense", ["boxing"], ["punch", "close"], "head_hook", "space", 0.0, "none", frames(3, 6, 0, 5), rec("none", ["head_uppercut"], 0.2),
    side="none", limb="torso", surface="none", line="none", tsr="none", energy=0.40, usage="defense", resolution="defense", exploits=[])
new("shoulder_roll", "Shoulder roll", "defense", ["boxing"], ["punch"], "head_straight", "space", 0.0, "none", frames(2, 5, 0, 4), rec("none", ["head_hook"], 0.2),
    side="lead", limb="lead shoulder", surface="shoulder", line="none", tsr="none", energy=0.30, usage="defense", resolution="defense", exploits=[])
new("whizzer", "Whizzer", "defense", ["wrestling", "anti_grappling", "judo"], ["punch", "clinch"], "entry", "space", 0.0, "none", frames(3, 6, 0, 5), rec("none", ["head_straight"], 0.25),
    side="both", limb="arm over underhook", surface="arm", line="grapple", tsr="none", energy=0.60, usage="defense", resolution="defense", legal=["mma", "street"], exploits=[])
new("clinch_break", "Clinch break", "escape", ["basic_movement"], ["clinch", "close"], "clinch", "space", 0.0, "none", frames(4, 7, 0, 5), rec("none", ["head_straight"], 0.25),
    side="both", limb="forearms", surface="frames", line="grapple", tsr="none", energy=0.60, usage="both", resolution="grapple", legal=RULESETS, exploits=[],
    notes="Frame, push and step out of any standing tie back to punch range.")
new("submission_escape", "Submission escape", "escape", ["basic_movement"], ["ground", "clinch"], "ground", "space", 0.0, "none", frames(4, 10, 0, 6), rec("none", [], 0.2),
    side="both", limb="hands and hips", surface="none", line="ground", tsr="none", energy=0.90, usage="defense", resolution="grapple", exploits=[],
    notes="Generic escape attempt against a submission stage (hand fight, posture up, stack, hitchhiker); odds come from grappling profiles.")
# Grips / clinch
new("underhook", "Underhook", "grip", ["clinch", "wrestling", "muay_thai"], ["clinch", "close"], "clinch", "body", 0.2, "control", frames(3, 6, 2, 5), rec("none", ["head_straight"], 0.2),
    side="lead", limb="arm", surface="arm", line="grapple", tsr="grip_side", energy=0.70, resolution="grapple", result_pos="over_under", exploits=["clinch"])
new("double_collar_tie", "Thai plum", "grip", ["muay_thai"], ["clinch"], "clinch", "body", 0.6, "stamina_drain", frames(4, 7, 2, 6), rec("none", ["body"], 0.25),
    side="both", limb="hands", surface="palms_behind_crown", line="grapple", tsr="grip_side", energy=0.90, resolution="grapple", result_pos="thai_plum", requires_position=["collar_tie"], exploits=["clinch", "head_uppercut"])
new("snap_down", "Snap down", "grip", ["wrestling"], ["clinch"], "clinch", "head", 0.3, "control", frames(3, 6, 2, 6), rec("none", ["body"], 0.3),
    side="both", limb="hands", surface="palms", line="grapple", tsr="none", energy=0.80, resolution="grapple", legal=["mma", "street"], result_pos="front_headlock", requires_position=["collar_tie"], exploits=["clinch", "entry"])
# Takedowns / sweeps
new("ankle_pick", "Ankle pick", "takedown", ["wrestling"], ["punch", "clinch"], "single_support", "leg", 1.6, "impact", frames(4, 9, 3, 11), rec("sprawled_shot_recovery", ["head_uppercut", "clinch"], 1.0),
    side="lead", limb="hand", surface="palm_on_heel", line="grapple", tsr="defender_lead", energy=1.20, acc=0.02, resolution="grapple", result_pos="half_guard", counters=["sprawl", "pummel"], exploits=["single_support", "entry"])
new("inside_trip", "Inside trip", "takedown", ["judo", "wrestling"], ["clinch"], "clinch", "body", 2.2, "impact", frames(4, 9, 3, 11), rec("sprawled_shot_recovery", ["head_uppercut", "clinch"], 1.0),
    side="lead", limb="leg", surface="calf_hook", line="grapple", tsr="grip_side", energy=1.15, resolution="grapple", legal=["muay_thai", "mma", "street"], result_pos="closed_guard", counters=["whizzer", "pummel"], exploits=["clinch", "single_support"])
new("hip_throw", "Hip throw", "takedown", ["judo"], ["clinch"], "clinch", "body", 3.0, "impact", frames(5, 11, 4, 13), rec("sprawled_shot_recovery", ["head_uppercut", "clinch", "body"], 1.25),
    side="both", limb="hips", surface="hip_fulcrum", line="grapple", tsr="grip_side", energy=1.45, acc=-0.04, resolution="grapple", result_pos="side_control", requires_position=["over_under", "collar_tie", "front_body_lock"], counters=["whizzer", "sprawl"], exploits=["clinch"])
new("foot_sweep", "Foot sweep", "sweep", ["judo", "karate", "sanda"], ["kick", "punch", "clinch"], "single_support", "leg", 1.2, "impact", frames(3, 6, 3, 8), rec("single_leg_recovery", ["single_support", "head_straight"], 0.6),
    side="lead", limb="sole", surface="sole_of_foot", line="grapple", tsr="defender_lead", energy=0.70, acc=-0.02, resolution="grapple", result_pos="standing_knockdown", counters=["switch_step"], exploits=["single_support", "tempo"],
    notes="Timed sweep of a stepping foot; on success the opponent is knocked off balance or down without the sweeper taking top position.")
new("caught_kick_dump", "Caught-kick dump", "sweep", ["muay_thai", "sanda", "wrestling"], ["kick", "punch"], "single_support", "body", 2.4, "impact", frames(4, 8, 3, 10), rec("short_retract", ["head_straight"], 0.5),
    side="both", limb="arms and legs", surface="trip", line="grapple", tsr="grip_side", energy=1.00, resolution="grapple", legal=["muay_thai", "mma", "street"], result_pos="half_guard", requires_position=["caught_single_leg"], counters=["clinch_break"], exploits=["single_support"])
new("body_lock_takedown", "Body-lock takedown", "takedown", ["wrestling", "judo"], ["clinch"], "clinch", "body", 2.6, "impact", frames(5, 10, 4, 12), rec("sprawled_shot_recovery", ["head_uppercut", "clinch"], 1.0),
    side="both", limb="arms", surface="gable_grip", line="grapple", tsr="grip_side", energy=1.35, resolution="grapple", result_pos="side_control", requires_position=["front_body_lock", "standing_back_take", "wall_pinned"], counters=["whizzer", "pummel"], exploits=["clinch", "wall"])
new("suplex", "Suplex", "takedown", ["wrestling"], ["clinch"], "clinch", "head", 3.4, "impact", frames(6, 12, 4, 14), rec("sprawled_shot_recovery", ["head_uppercut", "clinch", "body"], 1.3),
    side="both", limb="hips", surface="arch", line="grapple", tsr="none", energy=1.70, acc=-0.06, resolution="grapple", result_pos="side_control", requires_position=["standing_back_take", "front_body_lock"], counters=["whizzer"], exploits=["clinch"])
# Ground control / transitions
new("pass_guard", "Guard pass", "control", ["bjj", "wrestling"], ["ground"], "ground", "hips", 0.4, "control", frames(5, 14, 3, 8), rec("none", [], 0.3),
    side="both", limb="hips and hands", surface="pressure", line="ground", tsr="none", energy=1.20, resolution="grapple", result_pos="side_control", requires_position=["closed_guard:top", "half_guard:top"], counters=["re_guard", "guard_sweep"], exploits=["ground"])
new("advance_to_mount", "Mount", "control", ["bjj", "wrestling"], ["ground"], "ground", "hips", 0.4, "control", frames(4, 12, 3, 7), rec("none", [], 0.3),
    side="both", limb="knees and hips", surface="pressure", line="ground", tsr="none", energy=1.00, resolution="grapple", result_pos="mount", requires_position=["side_control:top"], counters=["hip_escape"], exploits=["ground"])
new("take_back", "Take the back", "control", ["bjj", "wrestling"], ["ground", "clinch"], "ground", "hips", 0.4, "control", frames(4, 12, 3, 8), rec("none", [], 0.3),
    side="both", limb="hooks", surface="hooks", line="ground", tsr="none", energy=1.10, resolution="grapple", result_pos="back_control", requires_position=["turtle:top", "front_headlock", "standing_back_take", "scramble"], counters=["hip_escape"], exploits=["ground"])
new("guard_sweep", "Guard sweep", "control", ["bjj"], ["ground"], "ground", "hips", 0.6, "control", frames(5, 12, 3, 9), rec("none", [], 0.4),
    side="both", limb="legs and hips", surface="hooks", line="ground", tsr="none", energy=1.15, resolution="grapple", result_pos="mount", requires_position=["closed_guard:bottom", "half_guard:bottom"], counters=["pass_guard"], exploits=["ground"])
new("re_guard", "Recover guard", "escape", ["bjj"], ["ground"], "ground", "space", 0.0, "none", frames(4, 10, 2, 7), rec("none", [], 0.3),
    side="both", limb="legs", surface="frames", line="ground", tsr="none", energy=0.90, usage="both", resolution="grapple", result_pos="closed_guard", requires_position=["half_guard:bottom", "side_control:bottom"], exploits=[])
new("hip_escape", "Hip escape", "escape", ["bjj", "wrestling", "anti_grappling"], ["ground"], "ground", "space", 0.0, "none", frames(4, 10, 2, 7), rec("none", [], 0.3),
    side="both", limb="hips", surface="frames", line="ground", tsr="none", energy=0.90, usage="both", resolution="grapple", result_pos="half_guard", requires_position=["side_control:bottom", "mount:bottom", "back_control:bottom"], exploits=[])
new("technical_standup", "Technical stand-up", "escape", ["anti_grappling", "bjj", "wrestling"], ["ground"], "ground", "space", 0.0, "none", frames(4, 11, 2, 7), rec("none", ["head_straight"], 0.35),
    side="both", limb="post hand and leg", surface="frames", line="ground", tsr="none", energy=1.00, usage="both", resolution="grapple", result_pos="standing_neutral", requires_position=["any_ground:bottom"], exploits=[])
new("wall_walk", "Wall walk", "escape", ["anti_grappling", "wrestling"], ["ground"], "ground", "space", 0.0, "none", frames(4, 12, 2, 7), rec("none", ["head_straight"], 0.35),
    side="both", limb="back and legs", surface="wall", line="ground", tsr="none", energy=1.10, usage="both", resolution="grapple", result_pos="standing_neutral", requires_position=["any_ground:bottom"], requires_wall=True, exploits=[])
new("stand_up", "Scramble to feet", "escape", ["basic_movement"], ["ground"], "ground", "space", 0.0, "none", frames(5, 12, 2, 8), rec("none", ["head_straight", "entry"], 0.45),
    side="both", limb="hands and knees", surface="none", line="ground", tsr="none", energy=1.20, usage="both", resolution="grapple", result_pos="standing_neutral", requires_position=["any_ground:bottom"], exploits=[],
    notes="Untrained get-up; low odds against trained top control.")
new("ground_strike", "Ground punches", "ground_strike", ["boxing", "kickboxing", "muay_thai", "karate", "sanda", "untrained_striking", "wrestling"], ["ground"], "ground", "head", 1.8, "impact", frames(3, 6, 2, 6), rec("none", [], 0.25),
    side="both", limb="fist", surface="knuckles_or_hammerfist", line="ground", tsr="center", energy=0.80, resolution="strike", requires_position=["closed_guard:top", "half_guard:top", "side_control:top", "mount:top", "back_control:top", "turtle:top"], exploits=["ground"])
new("ground_elbow", "Ground elbows", "ground_strike", ["muay_thai", "wrestling"], ["ground"], "ground", "head", 2.2, "impact", frames(3, 6, 2, 6), rec("none", [], 0.25),
    side="both", limb="elbow", surface="elbow_point", line="ground", tsr="center", energy=0.85, resolution="strike", cut=0.30, requires_position=["half_guard:top", "side_control:top", "mount:top"], exploits=["ground"])
# Submissions
SUBPOS = {
    "triangle": ["closed_guard:bottom"],
    "rear_naked_choke": ["back_control:top"],
    "guillotine": ["front_headlock", "closed_guard:bottom"],
    "kimura": ["closed_guard:bottom", "side_control:top", "half_guard:top"],
    "arm_triangle": ["side_control:top", "mount:top"],
}
new("triangle", "Triangle choke", "submission", ["bjj"], ["ground"], "ground", "neck_arm", 3.8, "submission", frames(8, 16, 6, 12), rec("none", [], 0.4),
    side="both", limb="legs", surface="legs_around_neck_and_arm", line="ground", tsr="grip_side", joint="neck", energy=1.25, resolution="submission", requires_position=SUBPOS["triangle"], counters=["submission_escape"], exploits=["ground"])
new("rear_naked_choke", "Rear-naked choke", "submission", ["bjj", "wrestling"], ["ground"], "ground", "neck_arm", 4.0, "submission", frames(6, 14, 6, 10), rec("none", [], 0.3),
    side="both", limb="arms", surface="forearm_across_neck", line="ground", tsr="none", joint="neck", energy=1.10, resolution="submission", requires_position=SUBPOS["rear_naked_choke"], counters=["submission_escape"], exploits=["ground"])
new("guillotine", "Guillotine", "submission", ["bjj", "wrestling", "clinch"], ["clinch", "ground"], "ground", "neck_arm", 3.6, "submission", frames(6, 14, 6, 11), rec("none", ["body"], 0.5),
    side="both", limb="arms", surface="forearm_under_chin", line="ground", tsr="none", joint="neck", energy=1.25, resolution="submission", requires_position=SUBPOS["guillotine"], counters=["submission_escape"], exploits=["ground", "entry"])
new("kimura", "Kimura", "submission", ["bjj", "judo", "wrestling"], ["ground"], "ground", "neck_arm", 3.6, "submission", frames(7, 15, 6, 11), rec("none", [], 0.4),
    side="both", limb="arms", surface="figure_four_on_wrist", line="ground", tsr="grip_side", joint="shoulder", energy=1.15, resolution="submission", requires_position=SUBPOS["kimura"], counters=["submission_escape"], exploits=["ground"])
new("arm_triangle", "Arm-triangle choke", "submission", ["bjj", "wrestling"], ["ground"], "ground", "neck_arm", 3.7, "submission", frames(7, 15, 6, 11), rec("none", [], 0.4),
    side="both", limb="arms and shoulder", surface="shoulder_into_neck", line="ground", tsr="grip_side", joint="neck", energy=1.20, resolution="submission", requires_position=SUBPOS["arm_triangle"], counters=["submission_escape"], exploits=["ground"])
# Movement / pressure
new("cut_off_step", "Cut-off step", "movement", ["pressure_footwork"], ["kick", "punch"], "space", "space", 0.0, "none", frames(3, 6, 0, 4), rec("none", [], 0.15),
    side="none", limb="feet", surface="feet", line="none", tsr="none", energy=0.35, usage="movement", resolution="movement", exploits=["angle", "wall", "tempo"],
    notes="Steps across the opponent's exit line: blocks lateral escape and pushes them toward the wall or corner.")

# ---------------------------------------------------------------------------
# Style packs (taekwondo, capoeira, catch wrestling, lethwei, kung fu variants)
# ---------------------------------------------------------------------------
exec(open(Path(__file__).with_name("style_packs.py")).read())
CAPS_NEW.update(STYLE_CAPS)
ALL_CAPS = CAPS_EXISTING | set(CAPS_NEW)

# ---------------------------------------------------------------------------
# Assemble the full catalog
# ---------------------------------------------------------------------------
catalog = []
for tid, base in existing_v2.items():
    t = copy.deepcopy(base)
    x = X.get(tid)
    if x is None:
        raise SystemExit(f"missing extension for existing technique {tid}")
    caps = list(t["required_capabilities"])
    if "caps_set" in x:
        caps = list(x["caps_set"])
    for c in x.get("caps_add", []):
        if c not in caps:
            caps.append(c)
    t["required_capabilities"] = caps
    t["_x"] = x
    catalog.append(t)
for t in NEW:
    catalog.append(t)
_by_id = {t["id"]: t for t in catalog}
for cap, tids in STYLE_GRANTS.items():
    for tid in tids:
        assert tid in _by_id, (cap, tid)
        if cap not in _by_id[tid]["required_capabilities"]:
            _by_id[tid]["required_capabilities"].append(cap)
for cap, src in STYLE_GRANT_FROM.items():
    for t in catalog:
        if src in t["required_capabilities"] and cap not in t["required_capabilities"]:
            t["required_capabilities"].append(cap)
for tid, extra in STYLE_POSITION_EXTRA.items():
    x = _by_id[tid]["_x"]
    x["requires_position"] = list(x.get("requires_position") or []) + extra

# ---------------------------------------------------------------------------
# Rulesets (single source of legality: technique.legal_in is DERIVED from these)
# ---------------------------------------------------------------------------
rulesets = OrderedDict()
rulesets["boxing"] = {
    "legal_kinds": ["movement", "feint", "punch", "defense"],
    "allowed_techniques": ["clinch_break"],
    "banned_techniques": ["headbutt", "shove", "spinning_backfist", "superman_punch", "kick_catch", "check", "sprawl", "whizzer", "jam_step", "pummel", "submission_escape", "wall_punch"],
    "clinch": {"allowed": False, "referee_break_after_exchanges": 0, "allowed_grips": [], "note": "Any tie is separated immediately (holding)."},
    "ground": {"allowed": False, "on_knockdown": "standing_count"},
    "environment": "ring", "default_rounds": 3, "default_round_s": 180,
    "decision_weights": {"clean_strikes": 0.5, "damage": 0.35, "control": 0.0, "aggression": 0.15},
}
rulesets["kickboxing"] = {
    "legal_kinds": ["movement", "feint", "punch", "kick", "knee", "defense", "grip"],
    "allowed_techniques": ["clinch_break"],
    "banned_techniques": ["headbutt", "knee_head_clinch", "cage_plum", "body_lock", "wall_tie", "underhook", "double_collar_tie", "snap_down", "sprawl", "whizzer", "submission_escape"],
    "clinch": {"allowed": True, "referee_break_after_exchanges": 1, "allowed_grips": ["collar_tie"], "note": "One knee from the collar tie, then the referee separates."},
    "ground": {"allowed": False, "on_knockdown": "standing_count"},
    "environment": "ring", "default_rounds": 3, "default_round_s": 180,
    "decision_weights": {"clean_strikes": 0.45, "damage": 0.4, "control": 0.0, "aggression": 0.15},
}
rulesets["muay_thai"] = {
    "legal_kinds": ["movement", "feint", "punch", "elbow", "kick", "knee", "defense", "grip", "sweep"],
    "allowed_techniques": ["clinch_break", "outside_trip", "inside_trip", "sanda_sweep"],
    "banned_techniques": ["headbutt", "snap_down", "sprawl", "submission_escape"],
    "clinch": {"allowed": True, "referee_break_after_exchanges": None, "allowed_grips": ["collar_tie", "double_collar_tie", "underhook", "pummel", "body_lock", "cage_plum", "wall_tie"], "note": "Full clinch fighting; separated only when it stalls."},
    "ground": {"allowed": False, "on_knockdown": "standing_count", "on_sweep": "reset_standing_with_score"},
    "environment": "ring", "default_rounds": 5, "default_round_s": 180,
    "decision_weights": {"clean_strikes": 0.35, "damage": 0.4, "control": 0.15, "aggression": 0.10},
}
rulesets["mma"] = {
    "legal_kinds": KINDS, "allowed_techniques": [],
    "banned_techniques": ["headbutt"],
    "clinch": {"allowed": True, "referee_break_after_exchanges": None, "allowed_grips": "all", "note": "Stalled clinches may be separated (optional)."},
    "ground": {"allowed": True, "on_knockdown": "fight_continues"},
    "environment": "cage", "default_rounds": 3, "default_round_s": 300,
    "decision_weights": {"clean_strikes": 0.4, "damage": 0.3, "control": 0.2, "aggression": 0.1},
    "notes": "Exact unified-rules details (e.g. elbow and grounded-opponent knee restrictions) are configurable; check current rules before encoding specifics.",
}
rulesets["street"] = {
    "legal_kinds": KINDS, "allowed_techniques": [], "banned_techniques": [],
    "clinch": {"allowed": True, "referee_break_after_exchanges": None, "allowed_grips": "all", "note": "No referee."},
    "ground": {"allowed": True, "on_knockdown": "fight_continues"},
    "environment": "any", "default_rounds": 1, "default_round_s": 120,
    "decision_weights": {"clean_strikes": 0.35, "damage": 0.45, "control": 0.15, "aggression": 0.05},
    "notes": "Anime street fights: headbutts and shoves allowed, no standing counts, no rounds by default.",
}


rulesets["lethwei"] = copy.deepcopy(LETHWEI_RULESET)
for rs, tids in STYLE_BANNED.items():
    rulesets[rs]["banned_techniques"] = rulesets[rs]["banned_techniques"] + [t for t in tids if t not in rulesets[rs]["banned_techniques"]]
for rs, tids in STYLE_ALLOWED.items():
    rulesets[rs]["allowed_techniques"] = rulesets[rs]["allowed_techniques"] + [t for t in tids if t not in rulesets[rs]["allowed_techniques"]]
for rs in rulesets:
    rulesets[rs]["equipment"] = EQUIPMENT[rs]
    rulesets[rs]["knockdown_rules"] = KNOCKDOWN_RULES[rs]
    rulesets[rs]["default_rest_s"] = REST_S[rs]


def derive_legal(tid, kind):
    out = []
    for rs, cfg in rulesets.items():
        if tid in cfg["banned_techniques"]:
            continue
        if kind in cfg["legal_kinds"] or tid in cfg["allowed_techniques"]:
            out.append(rs)
    return out


LEGAL_NOTES = []
final = []
for t in catalog:
    x = t.pop("_x")
    kind = t["kind"]
    legal = derive_legal(t["id"], kind)
    intended = x.get("legal")
    if intended and sorted(intended) != sorted(legal):
        LEGAL_NOTES.append((t["id"], sorted(intended), sorted(legal)))
    rec_exp = t.get("recovery_exposure") or rec("none", [], 0.15)
    entry = OrderedDict()
    entry["id"] = t["id"]
    entry["name"] = t["name"]
    entry["kind"] = kind
    entry["usage"] = x.get("usage", "defense" if kind == "defense" else "attack")
    entry["resolution"] = x.get("resolution", "strike")
    entry["required_capabilities"] = t["required_capabilities"]
    entry["legal_in"] = legal
    entry["required_range"] = t["required_range"]
    entry["requires_position"] = x.get("requires_position")
    entry["requires_grip"] = x.get("requires_grip")
    entry["requires_wall"] = bool(x.get("requires_wall", False))
    entry["requires_airborne_training"] = bool(x.get("requires_airborne_training", False))
    entry["vertical_min"] = x.get("vmin", "grounded")
    entry["side"] = x.get("side", "none")
    entry["limb"] = x.get("limb", t["biomechanics"].get("attacking_limb"))
    entry["striking_surface"] = t["biomechanics"].get("striking_surface")
    entry["line"] = x.get("line", "none")
    entry["attack_lane"] = t["attack_lane"]
    entry["target_region"] = t["target_region"]
    bm = dict(t["biomechanics"])
    bm["vertical_mode_required"] = x.get("vmin", bm.get("vertical_mode_required", "grounded"))
    if t["id"] not in existing_v2:
        if "ground" in t["required_range"] and len(t["required_range"]) == 1:
            bm["height"] = "ground"
        if kind == "grip":
            bm["ending"] = "clinch_tie"
        elif kind in ("takedown", "sweep", "control", "ground_strike", "submission", "escape") and "ground" in t["required_range"] + [x.get("result_pos") or ""] + ["ground" if (x.get("result_pos") or "") in ("half_guard", "side_control", "closed_guard", "mount", "back_control") else ""]:
            bm["ending"] = "mat_settle"
        elif x.get("line") in ("rear_round_kick", "lead_round_kick", "spinning"):
            bm["ending"] = "carry_through"
    entry["biomechanics"] = bm
    entry["region_family"] = {"space": "none", "angle": "none", "vision": "none", "hips": "body", "neck_arm": "submission_target"}.get(t["target_region"], t["target_region"])
    entry["target_side_rule"] = x.get("tsr", "none")
    entry["joint_target"] = x.get("joint", "none")
    entry["base_damage"] = t["base_damage"]
    entry["damage_type"] = t["damage_type"]
    entry["cut_chance"] = x.get("cut", 0.0)
    entry["accuracy_base"] = x.get("acc", 0.0)
    entry["accuracy_base_recommended"] = x.get("rec_acc", x.get("acc", 0.0))
    entry["energy_mult"] = x.get("energy", 1.0)
    entry["catchability"] = x.get("catch") if kind in ("kick", "knee") else None
    entry["stop_hit"] = bool(x.get("stop_hit", False))
    entry["frame_costs"] = t["frame_costs"]
    entry["recovery_exposure"] = rec_exp
    entry["airborne"] = x.get("airborne")
    entry["result_position"] = x.get("result_pos")
    entry["counters"] = t.get("counters", [])
    entry["exploits_openings"] = x.get("exploits", [])
    entry["status"] = "proposal_owner_decision" if x.get("proposal") else ("existing" if t["id"] in existing_v2 else "new")
    final.append(entry)

DATA_CORRECTIONS = {"wall_tie": {"attack_lane": "clinch"}, "escape": {"attack_lane": "space"}}
for t in final:
    for k, v in DATA_CORRECTIONS.get(t["id"], {}).items():
        t[k] = v
INCOMING_OVERRIDE = {"shove": "clinch_entry"}
INCOMING_OVERRIDE.update(STYLE_INCOMING_OVERRIDE)


def incoming_class(t):
    if t["id"] in INCOMING_OVERRIDE:
        return INCOMING_OVERRIDE[t["id"]]
    k = t["kind"]
    if k in ("movement", "feint", "defense", "control", "escape"):
        return "none"
    if k == "submission":
        return "submission"
    if k == "ground_strike":
        return "ground_strike"
    if k in ("takedown", "sweep"):
        return "takedown"
    if k == "grip":
        return "clinch_entry"
    if k in ("elbow", "knee"):
        return k
    lane, line = t["attack_lane"], t["line"]
    if k == "kick":
        if lane in ("leg", "single_support"):
            return "kick_low"
        if lane.startswith("head"):
            return "kick_high"
        if line in ("lead_linear_kick", "rear_linear_kick"):
            return "kick_linear"
        return "kick_body"
    if k == "punch":
        if lane == "body":
            return "body_punch"
        if line in ("lead_uppercut", "rear_uppercut"):
            return "uppercut"
        if line in ("lead_round", "rear_round", "overhand", "spinning"):
            return "hook"
        return "straight"
    raise ValueError(t["id"])


ALL_CLASSES = ["straight", "hook", "uppercut", "body_punch", "elbow", "knee", "kick_low", "kick_body", "kick_linear", "kick_high", "takedown", "clinch_entry"]
STRIKES = ["straight", "hook", "uppercut", "body_punch", "elbow", "knee", "kick_low", "kick_body", "kick_linear", "kick_high"]
DEFENDS = {
    "parry": (["straight", "kick_linear"], ["hook", "body_punch", "kick_low", "kick_high", "takedown", "clinch_entry", "knee", "elbow"], "evaded", {}),
    "shell_block": (["hook", "uppercut", "body_punch", "elbow", "kick_high", "kick_body"], ["takedown", "clinch_entry", "kick_low"], "blocked", {}),
    "shield_frame": (["straight", "hook", "clinch_entry", "elbow", "knee"], ["kick_low", "takedown"], "blocked", {}),
    "slip": (["straight"], ["body_punch", "uppercut", "kick_low", "kick_body", "kick_linear", "takedown", "knee"], "evaded", {}),
    "bob_weave": (["hook"], ["uppercut", "knee", "takedown", "body_punch", "kick_body"], "evaded", {}),
    "shoulder_roll": (["straight"], ["uppercut", "body_punch", "kick_high", "takedown"], "evaded", {}),
    "lean_back": (["kick_high", "uppercut"], ["body_punch", "kick_low", "kick_body", "takedown", "clinch_entry"], "evaded", {}),
    "evade_step_back": (["kick_low", "kick_body", "kick_linear", "kick_high", "straight"], ["clinch_entry"], "evaded", {}),
    "check": (["kick_low", "kick_body"], ["straight", "hook", "uppercut", "body_punch", "takedown", "clinch_entry", "kick_linear", "kick_high"], "checked", {}),
    "kick_catch": (["kick_body", "kick_linear"], ["kick_low", "kick_high"], "caught", {}),
    "jam_step": (["kick_body", "kick_linear", "knee"], ["kick_low", "kick_high", "straight"], "jammed", {}),
    "sprawl": (["takedown"], [c for c in STRIKES if c != "knee"], "evaded", {}),
    "whizzer": (["takedown", "clinch_entry"], [c for c in STRIKES if c not in ("knee", "elbow", "body_punch")], "blocked", {}),
    "pummel": (["clinch_entry", "takedown", "knee"], ["straight", "kick_low", "kick_body", "kick_linear", "kick_high"], "jammed", {"takedown": "blocked", "clinch_entry": "blocked"}),
    "retreat": (["straight", "kick_high", "kick_linear"], ["takedown"], "evaded", {}),
    "pivot": (["straight", "takedown", "clinch_entry"], ["hook"], "evaded", {}),
    "clinch_break": (["clinch_entry"], [], "evaded", {}),
}
DEFENDS.update(STYLE_DEFENDS)
for t in final:
    t["on_success_effects"] = STYLE_EFFECTS.get(t["id"], [])
    for e in t["on_success_effects"]:
        assert e["effect"] in EFFECT_TYPES, (t["id"], e)
    t["incoming_class"] = incoming_class(t)
    if t["id"] in DEFENDS:
        d, poor, res, by = DEFENDS[t["id"]]
        assert not (set(d) & set(poor)), t["id"]
        t["defends"] = {"designed_for": d, "poor_for": poor, "success_result": res, "result_by_class": by}
    else:
        t["defends"] = None
    if t["kind"] in ("grip", "control") or t["id"] in ("pummel", "guard_pull"):
        t["damage_routing"] = "control"
    elif t["kind"] == "submission":
        t["damage_routing"] = "submission"
    else:
        t["damage_routing"] = "strike"

ids = [t["id"] for t in final]
assert len(ids) == len(set(ids)), "duplicate technique id"
IDSET = set(ids)

# ---------------------------------------------------------------------------
# Positions (pair-level state: one position + a role per fighter)
# ---------------------------------------------------------------------------
tmap0 = {t["id"]: t for t in final}
POS = [
    # id, domain, range, roles, control_value_per_s (per role), strikes_allowed_roles
    ("standing_neutral", "standing", "kick", ["neutral", "neutral"], {"neutral": 0.0}),
    ("caught_single_leg", "standing", "close", ["holder", "held"], {"holder": 0.4, "held": 0.0}),
    ("standing_back_take", "clinch", "clinch", ["back_controller", "controlled"], {"back_controller": 0.6, "controlled": 0.0}),
    ("collar_tie", "clinch", "clinch", ["tier", "tied"], {"tier": 0.3, "tied": 0.0}),
    ("thai_plum", "clinch", "clinch", ["plum_holder", "plummed"], {"plum_holder": 0.5, "plummed": 0.0}),
    ("over_under", "clinch", "clinch", ["neutral", "neutral"], {"neutral": 0.0}),
    ("double_underhooks", "clinch", "clinch", ["dominant", "controlled"], {"dominant": 0.5, "controlled": 0.0}),
    ("front_body_lock", "clinch", "clinch", ["locker", "locked"], {"locker": 0.5, "locked": 0.0}),
    ("wall_pinned", "clinch", "clinch", ["pinner", "pinned"], {"pinner": 0.5, "pinned": 0.0}),
    ("front_headlock", "clinch", "clinch", ["controller", "controlled"], {"controller": 0.6, "controlled": 0.0}),
    ("shot_in", "transition", "close", ["shooter", "defender"], {"shooter": 0.2, "defender": 0.0}),
    ("scramble", "transition", "ground", ["neutral", "neutral"], {"neutral": 0.0}),
    ("standing_knockdown", "transition", "ground", ["standing", "downed"], {"standing": 0.3, "downed": 0.0}),
    ("closed_guard", "ground", "ground", ["top", "bottom"], {"top": 0.4, "bottom": 0.3}),
    ("half_guard", "ground", "ground", ["top", "bottom"], {"top": 0.6, "bottom": 0.1}),
    ("side_control", "ground", "ground", ["top", "bottom"], {"top": 0.9, "bottom": 0.0}),
    ("mount", "ground", "ground", ["top", "bottom"], {"top": 1.2, "bottom": 0.0}),
    ("back_control", "ground", "ground", ["top", "bottom"], {"top": 1.3, "bottom": 0.0}),
    ("turtle", "ground", "ground", ["top", "bottom"], {"top": 0.7, "bottom": 0.0}),
]
LEGACY_POSITION_MAP = {
    "closed_guard_bottom": "closed_guard (role bottom)",
    "half_guard_top": "half_guard (role top)",
    "mount_or_back_ride": "mount (role top) — or back_control (role top) when entered via take_back",
    "side_control": "side_control (role top/bottom by actor)",
    "shot_in": "shot_in", "caught_kick_dump": "caught_single_leg -> sweep transition (no standalone position)",
}
ROLE_TO_DOMINANT = {"neutral": "neutral", "top": "top", "back_controller": "back_controller", "bottom": "bottom_guard"}
GROUND_POS = ["closed_guard", "half_guard", "side_control", "mount", "back_control", "turtle", "leg_entanglement"]
STANDING_RANGES = {"outside", "kick", "punch", "close", "clinch"}


def allowed_for(pid, dom):
    out = []
    for t in final:
        req = [r.split(":")[0] for r in (t["requires_position"] or [])]
        if "any_ground" in req and pid in GROUND_POS:
            out.append(t["id"]); continue
        if pid in req:
            out.append(t["id"]); continue
        if req:
            continue
        if dom == "standing" and pid == "standing_neutral" and set(t["required_range"]) & (STANDING_RANGES - {"clinch"}):
            out.append(t["id"])
        elif dom == "clinch" and "clinch" in t["required_range"] and t["kind"] not in ("control", "ground_strike", "submission"):
            out.append(t["id"])
    return sorted(set(out))


POS += STYLE_POS
POSIDS = {row[0] for row in POS}

# Transitions: (from, from_role_of_actor, technique, to, actor_role_after, contest, counters)
TR = [
    ("standing_neutral", "neutral", "collar_tie", "collar_tie", "tier", "clinch_control", ["clinch_break", "pummel"]),
    ("standing_neutral", "neutral", "underhook", "over_under", "neutral", "clinch_control", ["whizzer", "clinch_break"]),
    ("standing_neutral", "neutral", "pummel", "over_under", "neutral", "clinch_control", ["clinch_break"]),
    ("standing_neutral", "neutral", "body_lock", "front_body_lock", "locker", "clinch_control", ["pummel", "sprawl", "clinch_break"]),
    ("standing_neutral", "neutral", "wall_tie", "wall_pinned", "pinner", "clinch_control", ["clinch_break", "pummel"]),
    ("standing_neutral", "neutral", "cage_plum", "thai_plum", "plum_holder", "clinch_control", ["pummel", "clinch_break"]),
    ("standing_neutral", "neutral", "double_leg", "shot_in", "shooter", "takedown", ["sprawl", "whizzer", "straight_knee"]),
    ("standing_neutral", "neutral", "single_leg", "shot_in", "shooter", "takedown", ["sprawl", "whizzer"]),
    ("standing_neutral", "neutral", "ankle_pick", "half_guard", "top", "takedown", ["sprawl", "switch_step"]),
    ("standing_neutral", "neutral", "kick_catch", "caught_single_leg", "holder", "kick_catch", ["clinch_break"]),
    ("standing_neutral", "neutral", "foot_sweep", "standing_knockdown", "standing", "sweep", ["switch_step"]),
    ("standing_neutral", "neutral", "guard_pull", "closed_guard", "bottom", "guard_pull", ["clinch_break"]),
    ("collar_tie", "tier", "double_collar_tie", "thai_plum", "plum_holder", "clinch_control", ["pummel", "clinch_break"]),
    ("collar_tie", "tier", "snap_down", "front_headlock", "controller", "clinch_control", ["clinch_break"]),
    ("collar_tie", "tier", "guard_pull", "closed_guard", "bottom", "guard_pull", ["clinch_break"]),
    ("collar_tie", "tied", "pummel", "over_under", "neutral", "clinch_control", ["collar_tie"]),
    ("collar_tie", "any", "clinch_break", "standing_neutral", "neutral", "clinch_escape", []),
    ("thai_plum", "plummed", "clinch_break", "standing_neutral", "neutral", "clinch_escape", ["knee_head_clinch"]),
    ("thai_plum", "plummed", "pummel", "over_under", "neutral", "clinch_control", ["knee_head_clinch"]),
    ("over_under", "neutral", "pummel", "double_underhooks", "dominant", "clinch_control", ["whizzer"]),
    ("over_under", "neutral", "body_lock", "front_body_lock", "locker", "clinch_control", ["whizzer"]),
    ("over_under", "neutral", "hip_throw", "side_control", "top", "takedown", ["whizzer", "sprawl"]),
    ("over_under", "neutral", "inside_trip", "closed_guard", "top", "takedown", ["whizzer"]),
    ("over_under", "any", "clinch_break", "standing_neutral", "neutral", "clinch_escape", []),
    ("double_underhooks", "dominant", "body_lock", "front_body_lock", "locker", "clinch_control", ["whizzer"]),
    ("double_underhooks", "controlled", "pummel", "over_under", "neutral", "clinch_control", []),
    ("front_body_lock", "locker", "outside_trip", "side_control", "top", "takedown", ["whizzer", "sprawl"]),
    ("front_body_lock", "locker", "body_lock_takedown", "side_control", "top", "takedown", ["whizzer"]),
    ("front_body_lock", "locker", "inside_trip", "closed_guard", "top", "takedown", ["whizzer"]),
    ("front_body_lock", "locker", "take_back", "standing_back_take", "back_controller", "clinch_control", ["pummel"]),
    ("front_body_lock", "locked", "clinch_break", "standing_neutral", "neutral", "clinch_escape", []),
    ("standing_back_take", "back_controller", "body_lock_takedown", "back_control", "top", "takedown", ["clinch_break"]),
    ("standing_back_take", "back_controller", "suplex", "side_control", "top", "takedown", ["whizzer"]),
    ("standing_back_take", "controlled", "clinch_break", "standing_neutral", "neutral", "clinch_escape", []),
    ("wall_pinned", "pinner", "body_lock_takedown", "half_guard", "top", "takedown", ["whizzer"]),
    ("wall_pinned", "pinner", "double_leg", "half_guard", "top", "takedown", ["sprawl", "whizzer"]),
    ("wall_pinned", "pinned", "clinch_break", "standing_neutral", "neutral", "clinch_escape", []),
    ("front_headlock", "controller", "take_back", "back_control", "top", "scramble", ["stand_up"]),
    ("front_headlock", "controlled", "clinch_break", "standing_neutral", "neutral", "clinch_escape", []),
    ("shot_in", "shooter", "double_leg", "half_guard", "top", "takedown", ["sprawl", "whizzer"]),
    ("shot_in", "shooter", "single_leg", "half_guard", "top", "takedown", ["whizzer"]),
    ("shot_in", "defender", "sprawl", "front_headlock", "controller", "takedown_defense", []),
    ("shot_in", "defender", "whizzer", "standing_neutral", "neutral", "takedown_defense", []),
    ("caught_single_leg", "holder", "sanda_sweep", "half_guard", "top", "sweep", ["clinch_break"]),
    ("caught_single_leg", "holder", "caught_kick_dump", "half_guard", "top", "sweep", ["clinch_break"]),
    ("caught_single_leg", "held", "clinch_break", "standing_neutral", "neutral", "clinch_escape", []),
    ("standing_knockdown", "downed", "stand_up", "standing_neutral", "neutral", "stand_up", []),
    ("scramble", "neutral", "take_back", "back_control", "top", "scramble", []),
    ("scramble", "neutral", "stand_up", "standing_neutral", "neutral", "scramble", []),
    ("closed_guard", "top", "pass_guard", "half_guard", "top", "pass", ["re_guard", "guard_sweep"]),
    ("half_guard", "top", "pass_guard", "side_control", "top", "pass", ["re_guard"]),
    ("side_control", "top", "advance_to_mount", "mount", "top", "pass", ["hip_escape"]),
    ("turtle", "top", "take_back", "back_control", "top", "pass", ["stand_up"]),
    ("closed_guard", "bottom", "guard_sweep", "mount", "top", "sweep_ground", ["pass_guard"]),
    ("half_guard", "bottom", "guard_sweep", "half_guard", "top", "sweep_ground", []),
    ("half_guard", "bottom", "re_guard", "closed_guard", "bottom", "escape", []),
    ("side_control", "bottom", "re_guard", "half_guard", "bottom", "escape", []),
    ("side_control", "bottom", "hip_escape", "half_guard", "bottom", "escape", []),
    ("mount", "bottom", "hip_escape", "half_guard", "bottom", "escape", []),
    ("back_control", "bottom", "hip_escape", "closed_guard", "top", "escape", []),
    ("any_ground", "bottom", "technical_standup", "standing_neutral", "neutral", "stand_up", []),
    ("any_ground", "bottom", "wall_walk", "standing_neutral", "neutral", "stand_up", []),
    ("any_ground", "bottom", "stand_up", "standing_neutral", "neutral", "stand_up", []),
    ("any_ground", "bottom", "escape", "standing_neutral", "neutral", "stand_up", []),
    ("closed_guard", "top", "ride", "closed_guard", "top", "control", []),
    ("half_guard", "top", "ride", "half_guard", "top", "control", []),
    ("side_control", "top", "ride", "side_control", "top", "control", []),
    ("mount", "top", "ride", "mount", "top", "control", []),
    ("back_control", "top", "ride", "back_control", "top", "control", []),
]
CONTESTS = ["clinch_control", "clinch_escape", "takedown", "takedown_defense", "kick_catch", "sweep", "guard_pull",
            "scramble", "pass", "sweep_ground", "escape", "stand_up", "control", "submission"]
CONTEST_SKILLS = {
    "clinch_control": ["clinch_control", "clinch_control"],
    "clinch_escape": ["clinch_control", "clinch_control"],
    "takedown": ["takedown_offense", "takedown_defense"],
    "takedown_defense": ["takedown_defense", "takedown_offense"],
    "kick_catch": ["technique.catchability roll (see 7.11)", "-"],
    "sweep": ["takedown_offense", "scramble + sweep_resistance"],
    "guard_pull": ["bottom_game", "top_control"],
    "scramble": ["scramble", "scramble"],
    "pass": ["top_control", "bottom_game"],
    "sweep_ground": ["bottom_game", "top_control"],
    "escape": ["bottom_game", "top_control"],
    "stand_up": ["stand_up", "top_control"],
    "control": ["top_control", "bottom_game"],
    "submission": ["submission_offense", "submission_defense"],
}
OUTCOME_TR = [
    ("shot_in", "shooter", "double_leg", "scramble", "neutral", "scramble", [], "takedown contest decided within scramble_margin"),
    ("shot_in", "shooter", "single_leg", "scramble", "neutral", "scramble", [], "takedown contest decided within scramble_margin"),
    ("side_control", "bottom", "stand_up", "turtle", "bottom", "stand_up", [], "stand-up failed within scramble_margin: bottom fighter ends on knees"),
    ("mount", "bottom", "hip_escape", "turtle", "bottom", "escape", [], "escape half-succeeds: bottom fighter turns to knees"),
    ("scramble", "neutral", "stand_up", "turtle", "bottom", "scramble", [], "scramble lost: loser ends on knees, winner on top"),
    ("closed_guard", "bottom", "armbar", "half_guard", "bottom", "submission", [], "failed attempt (defender escaped): defender stacks and passes to half guard"),
    ("closed_guard", "bottom", "triangle", "half_guard", "bottom", "submission", [], "failed attempt (defender escaped): defender postures out and passes"),
    ("mount", "top", "armbar", "scramble", "neutral", "submission", [], "failed attempt (defender escaped): defender pulls the arm free and comes up"),
    ("back_control", "top", "rear_naked_choke", "closed_guard", "bottom", "submission", [], "failed attempt (defender escaped): defender turns in, attacker keeps guard"),
    ("front_headlock", "controller", "guillotine", "closed_guard", "bottom", "submission", [], "failed attempt (defender escaped): attacker falls to closed guard"),
    ("side_control", "top", "arm_triangle", "half_guard", "top", "submission", [], "failed attempt (defender escaped): bottom fighter recovers half guard"),
    ("side_control", "top", "kimura", "half_guard", "top", "submission", [], "failed attempt (defender escaped): bottom fighter recovers half guard"),
]
TR += STYLE_TR
OUTCOME_TR += STYLE_OUTCOME_TR
expanded = []
for frm, frole, via, to, arole, contest, ctr in TR:
    if frm == "any_ground":
        for gp in GROUND_POS:
            expanded.append((gp, frole, via, to, arole, contest, ctr, None))
    else:
        expanded.append((frm, frole, via, to, arole, contest, ctr, None))
expanded += OUTCOME_TR
transitions = []
for frm, frole, via, to, arole, contest, ctr, outcome in expanded:
    t = tmap0[via]
    f = t["frame_costs"]
    tr = {"from_position": frm, "to_position": to, "via_technique": via,
          "required_grips": list(t["requires_grip"] or []),
          "frame_cost": int(f["setup_frames"] + f["execution_frames"] + f["contact_hold_frames"] + f["recovery_frames"]),
          "counters": ctr, "actor_role": frole, "actor_role_after": arole, "contest": contest}
    if outcome:
        tr["via_outcome"] = outcome
    transitions.append(tr)
# ---- position records (existing ids keep their current domain/range/posture/role; allowed lists are unions) ----
VIA_FROM = defaultdict(set)
for tr in transitions:
    VIA_FROM[tr["from_position"]].add(tr["via_technique"])
positions = []
for pid, dom, rng, roles, cv in POS:
    ex = EXISTING_POS.get(pid)
    allowed = set(allowed_for(pid, dom)) | VIA_FROM.get(pid, set()) | set(ex["allowed_techniques"] if ex else [])
    rec_ = OrderedDict()
    rec_["id"] = pid
    rec_["domain"] = ex["domain"] if ex else dom
    rec_["range"] = ex["range"] if ex else rng
    rec_["posture"] = ex["posture"] if ex else {"standing": "standing", "clinch": "standing", "transition": "transition", "ground": "ground"}[dom]
    rec_["dominant_side_role"] = ex["dominant_side_role"] if ex else ROLE_TO_DOMINANT.get(roles[0], "initiator")
    rec_["allowed_techniques"] = sorted(allowed)
    rec_["roles"] = roles
    rec_["control_value_per_second"] = cv
    rec_["status"] = "existing" if ex else "new"
    positions.append(rec_)
for legacy, target in [("closed_guard_bottom", "closed_guard"), ("half_guard_top", "half_guard"), ("mount_or_back_ride", "mount"), ("caught_kick_dump", "caught_single_leg")]:
    ex = EXISTING_POS[legacy]
    rec_ = OrderedDict((k, ex[k]) for k in ("id", "domain", "range", "posture", "dominant_side_role", "allowed_techniques"))
    rec_["status"] = "deprecated"
    rec_["alias_of"] = target
    positions.append(rec_)
LEGACY_TRANSITION_MAP = [
    {"existing": "standing_neutral -> caught_single_leg via kick_catch", "v2_1": "kept (actor role holder)"},
    {"existing": "caught_single_leg -> side_control via sanda_sweep", "v2_1": "re-targeted: caught_single_leg (holder) -> half_guard (top) via sanda_sweep; rulesets without ground reset to standing and score the sweep"},
    {"existing": "standing_neutral -> collar_tie via collar_tie", "v2_1": "kept (actor role tier)"},
    {"existing": "standing_neutral -> thai_plum via collar_tie", "v2_1": "replaced: standing_neutral -> thai_plum via cage_plum, and collar_tie -> thai_plum via double_collar_tie"},
    {"existing": "collar_tie -> double_underhooks via pummel", "v2_1": "replaced: collar_tie (tied) -> over_under via pummel, then over_under -> double_underhooks via pummel"},
    {"existing": "standing_neutral -> front_body_lock via body_lock", "v2_1": "kept (actor role locker)"},
    {"existing": "front_body_lock -> side_control via outside_trip", "v2_1": "kept (actor role top)"},
    {"existing": "standing_neutral -> half_guard_top via double_leg", "v2_1": "re-routed through shot_in: standing_neutral -> shot_in -> half_guard (top) or scramble"},
    {"existing": "standing_neutral -> half_guard_top via single_leg", "v2_1": "re-routed through shot_in (as double_leg)"},
    {"existing": "collar_tie -> closed_guard_bottom via guard_pull", "v2_1": "kept as collar_tie (tier) -> closed_guard (actor role bottom)"},
    {"existing": "half_guard_top -> mount_or_back_ride via ride", "v2_1": "replaced: ride holds position; half_guard -> side_control via pass_guard; side_control -> mount via advance_to_mount; turtle/scramble/front_headlock -> back_control via take_back"},
    {"existing": "closed_guard_bottom -> side_control via armbar", "v2_1": "replaced by submission outcome rows: a FAILED armbar from closed_guard bottom -> half_guard (attacker stays bottom); success ends the fight"},
    {"existing": "half_guard_top -> standing_neutral via escape", "v2_1": "kept as half_guard (bottom) -> standing_neutral via escape/stand_up/technical_standup/wall_walk"},
    {"existing": "side_control -> standing_neutral via escape", "v2_1": "kept as side_control (bottom) -> standing_neutral via escape/stand_up/technical_standup/wall_walk"},
]

# reachability check from standing_neutral
reach = {"standing_neutral"}
changed = True
while changed:
    changed = False
    for tr in transitions:
        if tr["from_position"] in reach and tr["to_position"] not in reach:
            reach.add(tr["to_position"]); changed = True
UNREACHABLE = sorted(POSIDS - reach)

# ---------------------------------------------------------------------------
# Opening -> technique exploit map and debt backfill
# ---------------------------------------------------------------------------
exploit_map = defaultdict(list)
for t in final:
    for o in t["exploits_openings"]:
        assert o in OPENINGS, (t["id"], o)
        exploit_map[o].append(t["id"])
RANGE_ORDER = ["clinch", "close", "punch", "kick", "outside"]


def near(r1, r2):
    if r1 == r2:
        return True
    if r1 in RANGE_ORDER and r2 in RANGE_ORDER:
        return abs(RANGE_ORDER.index(r1) - RANGE_ORDER.index(r2)) <= 1
    return False


debt_backfill = []
tmap = {t["id"]: t for t in final}
for d in debts:
    current = list(d["technique_ids"])
    add = []
    for tid in exploit_map.get(d["opening"], []):
        if tid in current:
            continue
        t = tmap[tid]
        if not (set(t["legal_in"]) & set(d["ruleset"])):
            continue
        if t["usage"] in ("defense",):
            continue
        if d["required_range"] == "ground":
            if not t["requires_position"] and "ground" not in t["required_range"]:
                continue
        elif not any(near(r, d["required_range"]) for r in t["required_range"]):
            continue
        add.append(tid)
    debt_backfill.append({"debt_id": d["id"], "opening": d["opening"], "required_range": d["required_range"],
                          "current_technique_ids": current, "add_technique_ids": add})

# ---------------------------------------------------------------------------
# Combination chains (recoil of N loads N+1; a follow-up gets a setup discount)
# ---------------------------------------------------------------------------
COMBOS = [
    ("boxing_1_2", ["jab", "cross"], "boxing", 0.06, 2),
    ("boxing_1_2_3", ["jab", "cross", "hook"], "boxing", 0.06, 2),
    ("boxing_body_head", ["body_jab", "overhand"], "boxing", 0.08, 2),
    ("boxing_hook_body_head", ["body_hook", "hook"], "boxing", 0.07, 2),
    ("boxing_uppercut_hook", ["uppercut", "hook"], "boxing", 0.06, 2),
    ("boxing_double_jab_cross", ["jab", "jab", "cross"], "boxing", 0.05, 2),
    ("inside_shovel_upper", ["shovel_hook", "short_uppercut"], "inside_combinations", 0.08, 2),
    ("pressure_cut_body", ["cut_off_step", "rear_body_hook"], "pressure_footwork", 0.06, 2),
    ("dutch_finish_low", ["jab", "cross", "hook", "low_kick"], "kickboxing", 0.08, 3),
    ("dutch_body_low", ["body_hook", "low_kick"], "kickboxing", 0.07, 2),
    ("kickboxing_cross_head_kick", ["cross", "head_kick"], "kickboxing", 0.06, 3),
    ("kb_calf_cross", ["calf_kick", "cross"], "kickboxing", 0.05, 2),
    ("thai_teep_body_kick", ["teep", "body_kick"], "muay_thai", 0.06, 2),
    ("thai_check_return", ["check", "body_kick"], "muay_thai", 0.10, 2),
    ("thai_plum_knees", ["double_collar_tie", "knee_head_clinch"], "muay_thai", 0.08, 2),
    ("thai_elbow_knee", ["horizontal_elbow", "knee_body"], "muay_thai", 0.07, 2),
    ("thai_cross_switch_kick", ["cross", "switch_kick"], "muay_thai", 0.06, 2),
    ("karate_feint_side_kick", ["feint", "side_kick"], "karate", 0.08, 2),
    ("karate_body_then_head", ["body_kick", "question_mark_kick"], "karate", 0.08, 3),
    ("karate_front_kick_cross", ["front_kick", "cross"], "karate", 0.05, 2),
    ("sanda_catch_sweep", ["kick_catch", "sanda_sweep"], "sanda", 0.10, 2),
    ("sanda_side_kick_cross", ["side_kick", "cross"], "sanda", 0.05, 2),
    ("wrestling_jab_level_change", ["jab", "double_leg"], "wrestling", 0.08, 2),
    ("wrestling_snap_go_behind", ["snap_down", "take_back"], "wrestling", 0.08, 2),
    ("wrestling_single_to_pick", ["single_leg", "ankle_pick"], "wrestling", 0.06, 2),
    ("judo_lock_trip", ["body_lock", "outside_trip"], "judo", 0.08, 2),
    ("judo_underhook_throw", ["underhook", "hip_throw"], "judo", 0.08, 2),
    ("bjj_tie_pull", ["collar_tie", "guard_pull"], "bjj", 0.06, 2),
    ("bjj_sweep_mount_armbar", ["guard_sweep", "armbar"], "bjj", 0.08, 2),
    ("bjj_pass_mount_choke", ["pass_guard", "advance_to_mount"], "bjj", 0.06, 2),
    ("wall_tie_punch", ["wall_tie", "wall_punch"], "wall_boxing", 0.07, 2),
    ("shield_redirect_counter", ["shield_frame", "shield_counter_hook"], "shield", 0.10, 2),
    ("counter_parry_shoot", ["parry", "cross"], "boxing", 0.08, 2),
    ("brawler_straight_hook", ["brawler_straight", "wild_hook"], "untrained_striking", 0.03, 2),
    ("brawler_shove_haymaker", ["shove", "haymaker"], "untrained_striking", 0.05, 2),
]
COMBOS += STYLE_COMBOS
combinations = []
for cid, chain, school, bonus, saves in COMBOS:
    for tid in chain:
        assert tid in IDSET, (cid, tid)
    first_kind = tmap0[chain[0]]["kind"]
    trigger_on = "defended" if first_kind == "defense" else ("executed" if first_kind in ("movement", "feint", "grip", "control") else "landed")
    combinations.append({"id": cid, "chain": chain, "school": school, "follow_up_accuracy_bonus": bonus,
                         "setup_frames_saved": saves, "trigger_on": trigger_on,
                         "requires_previous_outcome": {"landed": ["clean", "partial", "blocked"], "defended": ["evaded", "blocked", "checked", "caught", "jammed"], "executed": ["any_non_failure"]}[trigger_on],
                         "same_slot_required": True})

# ---------------------------------------------------------------------------
# Validation of references
# ---------------------------------------------------------------------------
errors = []
for t in final:
    for c in t["required_capabilities"]:
        if c not in ALL_CAPS:
            errors.append(f"{t['id']}: unknown capability {c}")
    for c in t["counters"]:
        if c not in IDSET:
            errors.append(f"{t['id']}: counter {c} not a technique")
    if t["kind"] not in KINDS:
        errors.append(f"{t['id']}: bad kind")
    if t["line"] not in LINES:
        errors.append(f"{t['id']}: bad line {t['line']}")
    if t["target_side_rule"] not in TSR:
        errors.append(f"{t['id']}: bad tsr")
    if t["usage"] not in USAGE:
        errors.append(f"{t['id']}: bad usage")
    if t["resolution"] not in RESOLUTION:
        errors.append(f"{t['id']}: bad resolution")
    if t["vertical_min"] not in VMIN:
        errors.append(f"{t['id']}: bad vmin")
    if t["attack_lane"] not in LANES + NONLANE:
        errors.append(f"{t['id']}: bad lane {t['attack_lane']}")
    if t["target_region"] not in REGIONS:
        errors.append(f"{t['id']}: bad region {t['target_region']}")
    if t["damage_type"] not in DTYPES:
        errors.append(f"{t['id']}: bad dtype {t['damage_type']}")
    if t["kind"] in ("kick", "knee") and t["catchability"] is None:
        errors.append(f"{t['id']}: kick/knee without catchability")
    if t["vertical_min"] != "grounded" and not t["airborne"]:
        errors.append(f"{t['id']}: airborne technique without airborne phases")
    if t["airborne"] and not t["requires_airborne_training"]:
        errors.append(f"{t['id']}: airborne technique must require airborne training")
    if t["result_position"] and t["result_position"] not in POSIDS:
        errors.append(f"{t['id']}: result position {t['result_position']} unknown")
    for rp in t["requires_position"] or []:
        base = rp.split(":")[0]
        if base not in POSIDS and base != "any_ground":
            errors.append(f"{t['id']}: requires unknown position {rp}")
    for r in t["required_range"]:
        if r not in RANGES:
            errors.append(f"{t['id']}: bad range {r}")
    if any(v <= 0 for k, v in t["frame_costs"].items() if k != "contact_hold_frames"):
        errors.append(f"{t['id']}: non-positive frames")
for tr in transitions:
    if tr["from_position"] not in POSIDS and tr["from_position"] != "any_ground":
        errors.append(f"transition from unknown {tr['from_position']}")
    if tr["to_position"] not in POSIDS:
        errors.append(f"transition to unknown {tr['to_position']}")
    if tr["via_technique"] not in IDSET:
        errors.append(f"transition via unknown {tr['via_technique']}")
    if tr["contest"] not in CONTESTS:
        errors.append(f"transition bad contest {tr['contest']}")
    for c in tr["counters"]:
        if c not in IDSET:
            errors.append(f"transition counter unknown {c}")
# every capability (except proposals/conditional) must grant >= 2 non-basic techniques
grants = defaultdict(list)
for t in final:
    for c in t["required_capabilities"]:
        grants[c].append(t["id"])
for c in sorted(ALL_CAPS):
    non_basic = [g for g in grants.get(c, []) if tmap[g]["kind"] not in ("movement", "feint")]
    if c not in ("basic_movement", "switch_step", "cage_plum", "pressure_footwork") and len(non_basic) < 2:
        errors.append(f"capability {c} grants fewer than 2 non-basic techniques: {non_basic}")
if UNREACHABLE:
    errors.append(f"positions unreachable from standing_neutral: {UNREACHABLE}")
if errors:
    print("\n".join(errors))
    raise SystemExit(f"{len(errors)} validation errors")

# ---------------------------------------------------------------------------
# Write seeds
# ---------------------------------------------------------------------------
# ---- extended technique schema (current schema + new optional fields + extended kind enum) ----
import jsonschema
cur = json.load(open(REPO / "schemas/technique_v2.schema.json"))
item = cur["properties"]["techniques"]["items"]
item["properties"]["kind"]["enum"] = sorted(set(item["properties"]["kind"]["enum"]) | {"elbow", "sweep", "ground_strike", "escape"})
NEWPROPS = {
    "usage": {"enum": USAGE}, "resolution": {"enum": RESOLUTION},
    "legal_in": {"type": "array", "items": {"enum": RULESETS}, "minItems": 1},
    "requires_position": {"type": ["array", "null"], "items": {"type": "string"}},
    "requires_grip": {"type": ["array", "null"], "items": {"type": "string"}},
    "requires_wall": {"type": "boolean"}, "requires_airborne_training": {"type": "boolean"},
    "vertical_min": {"enum": VMIN}, "side": {"enum": ["lead", "rear", "both", "none", "either"]},
    "limb": {"type": "string"}, "striking_surface": {"type": ["string", "null"]}, "line": {"enum": LINES},
    "target_side_rule": {"enum": TSR}, "joint_target": {"enum": ["none", "knee", "elbow", "shoulder", "neck", "ankle"]},
    "region_family": {"enum": ["none", "head", "body", "leg", "submission_target"]},
    "cut_chance": {"type": "number", "minimum": 0, "maximum": 1},
    "accuracy_base": {"type": "number"}, "accuracy_base_recommended": {"type": "number"},
    "energy_mult": {"type": "number", "minimum": 0}, "catchability": {"type": ["number", "null"], "minimum": 0, "maximum": 1},
    "stop_hit": {"type": "boolean"},
    "airborne": {"type": ["object", "null"]}, "result_position": {"type": ["string", "null"]},
    "exploits_openings": {"type": "array", "items": {"enum": OPENINGS}},
    "status": {"enum": ["existing", "new", "proposal_owner_decision"]},
    "incoming_class": {"enum": ["none", "straight", "hook", "uppercut", "body_punch", "elbow", "knee", "kick_low", "kick_body", "kick_linear", "kick_high", "takedown", "clinch_entry", "ground_strike", "submission"]},
    "defends": {"type": ["object", "null"], "required": ["designed_for", "poor_for", "success_result"],
                "properties": {"designed_for": {"type": "array", "items": {"type": "string"}}, "poor_for": {"type": "array", "items": {"type": "string"}},
                               "success_result": {"enum": ["evaded", "blocked", "checked", "caught", "jammed"]},
                               "result_by_class": {"type": "object", "additionalProperties": {"enum": ["evaded", "blocked", "checked", "caught", "jammed"]}}},
                "additionalProperties": False},
    "damage_routing": {"enum": ["strike", "control", "submission"]},
    "on_success_effects": {"type": "array", "items": {"type": "object", "required": ["target", "effect"],
                           "properties": {"target": {"enum": ["opponent", "self"]}, "effect": {"enum": EFFECT_TYPES},
                                          "value": {"type": ["number", "string"]}, "lanes": {"type": "array", "items": {"enum": LANES}},
                                          "skills": {"type": "array", "items": {"type": "string"}}, "chance": {"type": "number", "minimum": 0, "maximum": 1},
                                          "exchanges": {"type": "integer", "minimum": 1}}, "additionalProperties": False}},
}
item["properties"].update(NEWPROPS)
jsonschema.validate({"version": "block-2", "techniques": final}, cur)
(OUT / "technique_v2.schema.extended.json").write_text(json.dumps(cur, indent=1) + "\n")

(OUT / "techniques_v2_backfill.json").write_text(json.dumps({"version": "block-2", "techniques": final}, indent=1) + "\n")
(OUT / "positions_v2_backfill.json").write_text(json.dumps({"version": "block-2", "positions": positions, "transitions": transitions,
                                                            "contests": CONTESTS, "contest_skill_map": CONTEST_SKILLS, "legacy_position_map": LEGACY_POSITION_MAP,
                                                            "legacy_transition_map": LEGACY_TRANSITION_MAP}, indent=1) + "\n")
(OUT / "rulesets_v2.json").write_text(json.dumps({"version": "block-2", "rulesets": rulesets}, indent=1) + "\n")
(OUT / "debt_registry_v2_overlay.json").write_text(json.dumps({
    "version": "block-2",
    "base_registry": "data/debt_registry.json",
    "merge_rule": "v2 engine only: effective technique_ids(debt) = base technique_ids + add_technique_ids, filtered by ruleset legality and slot availability at run time. data/debt_registry.json is NOT edited (engine/audit.py requires v1 technique ids there).",
    "opening_to_techniques": {k: sorted(v) for k, v in sorted(exploit_map.items())},
    "debts": debt_backfill}, indent=1) + "\n")
(OUT / "combinations_v2_backfill.json").write_text(json.dumps({"version": "block-2", "combinations": combinations}, indent=1) + "\n")
CORE = {"karate": ["side_kick", "teep", "body_kick", "spinning_back_kick"],
        "basic_movement": ["step", "retreat", "pivot", "feint", "clinch_break", "stand_up", "submission_escape"]}
for cap, core in CORE.items():
    for tid in core:
        assert cap in tmap[tid]["required_capabilities"], (cap, tid)
(OUT / "capability_grants.json").write_text(json.dumps({"version": "block-2", "new_capabilities": CAPS_NEW,
                                                        "core": CORE,
                                                        "defense_prepend": STYLE_DEFENSE_PREPEND,
                                                        "core_rule": "attack/movement availability = core(cap) + (grants(cap) & active_techniques) over trained capabilities; defenses = every defense granted by a trained capability; core ids not yet in data/techniques_v2.json are ignored",
                                                        "grants": {c: sorted(grants.get(c, [])) for c in sorted(ALL_CAPS)}}, indent=1) + "\n")

# ---------------------------------------------------------------------------
# Markdown tables for the handoff
# ---------------------------------------------------------------------------
def md_table(headers, rows):
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    for r in rows:
        out.append("| " + " | ".join(str(c) for c in r) + " |")
    return "\n".join(out)


def fr(t):
    f = t["frame_costs"]
    return f"{f['setup_frames']}/{f['execution_frames']}/{f['contact_hold_frames']}/{f['recovery_frames']}"


groups = OrderedDict([
    ("Movement & feints", ("movement", "feint")),
    ("Punches", ("punch",)),
    ("Elbows", ("elbow",)),
    ("Kicks", ("kick",)),
    ("Knees", ("knee",)),
    ("Defenses", ("defense",)),
    ("Grips & clinch", ("grip",)),
    ("Takedowns & sweeps", ("takedown", "sweep")),
    ("Ground control, strikes & escapes", ("control", "ground_strike", "escape")),
    ("Submissions", ("submission",)),
])
md = []
for title, kinds in groups.items():
    rows = []
    for t in final:
        if t["kind"] in kinds:
            rows.append([f"`{t['id']}`", t["status"].replace("proposal_owner_decision", "PROPOSAL"), ", ".join(t["required_capabilities"]),
                         ", ".join(t["legal_in"]) if len(t["legal_in"]) < 5 else "all",
                         ",".join(t["required_range"]), t["side"], t["line"], t["attack_lane"], t["target_region"],
                         t["target_side_rule"], t["base_damage"], t["damage_type"], fr(t),
                         f"{t['recovery_exposure']['window_type']} {t['recovery_exposure']['readiness_penalty']}",
                         t["accuracy_base_recommended"], t["energy_mult"],
                         "" if t["catchability"] is None else t["catchability"], t["cut_chance"] or "",
                         t["vertical_min"] if t["vertical_min"] != "grounded" else "",
                         ", ".join(t["requires_position"] or []) + (" +wall" if t["requires_wall"] else ""),
                         t["result_position"] or ""])
    md.append(f"#### {title}\n\n" + md_table(
        ["id", "status", "capabilities (any)", "legal in", "range", "side", "line", "lane", "region", "side rule", "dmg", "type",
         "frames s/e/h/r", "recovery window", "acc", "energy", "catch", "cut", "vertical", "requires", "result position"], rows))
(OUT / "techniques_tables.md").write_text("\n\n".join(md) + "\n")

pos_md = md_table(["position", "status", "domain", "range", "roles", "control value / s", "allowed techniques"],
                  [[f"`{p['id']}`", p.get("status", ""), p["domain"], p["range"], " / ".join(p.get("roles", [])) or f"alias of `{p.get('alias_of')}`",
                    ", ".join(f"{k} {v}" for k, v in p.get("control_value_per_second", {}).items()), len(p["allowed_techniques"])] for p in positions])
tr_md = md_table(["from (actor role)", "via", "to (actor role after)", "contest", "frames", "counters", "outcome condition"],
                 [[f"`{t['from_position']}` ({t['actor_role']})", f"`{t['via_technique']}`", f"`{t['to_position']}` ({t['actor_role_after']})", t["contest"], t["frame_cost"], ", ".join(t["counters"]), t.get("via_outcome", "")] for t in transitions])
cs_md = md_table(["contest", "actor skill", "opponent skill"], [[f"`{k}`", v[0], v[1]] for k, v in CONTEST_SKILLS.items()])
(OUT / "positions_tables.md").write_text(pos_md + "\n\n" + tr_md + "\n\n**Contest → grappling-profile skills** (actor vs opponent):\n\n" + cs_md + "\n")

rs_md = md_table(["ruleset", "legal kinds", "banned techniques", "clinch", "ground", "env", "default rounds × s", "decision weights"],
                 [[f"`{k}`", ", ".join(v["legal_kinds"]) if v["legal_kinds"] != KINDS else "all", ", ".join(v["banned_techniques"]) or "none",
                   v["clinch"]["note"], v["ground"].get("on_knockdown"), v["environment"], f"{v['default_rounds']} × {v['default_round_s']}",
                   ", ".join(f"{a} {b}" for a, b in v["decision_weights"].items())] for k, v in rulesets.items()])
(OUT / "rulesets_table.md").write_text(rs_md + "\n")

cap_md = md_table(["capability", "status", "grants (techniques whose any-of capability list includes it)"],
                  [[f"`{c}`", "NEW" if c in CAPS_NEW else "existing", ", ".join(f"`{g}`" for g in sorted(grants.get(c, [])))] for c in sorted(ALL_CAPS)])
(OUT / "capability_table.md").write_text(cap_md + "\n")

combo_md = md_table(["combo", "chain", "school", "follow-up accuracy bonus", "setup frames saved"],
                    [[f"`{c['id']}`", " → ".join(c["chain"]), c["school"], c["follow_up_accuracy_bonus"], c["setup_frames_saved"]] for c in combinations])
(OUT / "combinations_table.md").write_text(combo_md + "\n")

ex_md = md_table(["opening", "techniques that exploit it"], [[f"`{k}`", ", ".join(f"`{x}`" for x in sorted(v))] for k, v in sorted(exploit_map.items())])
(OUT / "exploit_map_table.md").write_text(ex_md + "\n")

added_total = sum(len(d["add_technique_ids"]) for d in debt_backfill)
summary = {
    "techniques_total": len(final),
    "techniques_existing": sum(1 for t in final if t["status"] == "existing"),
    "techniques_new": sum(1 for t in final if t["status"] == "new"),
    "techniques_proposal": sum(1 for t in final if t["status"] == "proposal_owner_decision"),
    "positions": len(positions), "transitions": len(transitions), "rulesets": len(rulesets),
    "combinations": len(combinations), "debts": len(debt_backfill), "debt_technique_additions": added_total,
    "capabilities_total": len(ALL_CAPS), "capabilities_new": list(CAPS_NEW),
    "data_corrections": DATA_CORRECTIONS,
}
(OUT / "seed_summary.json").write_text(json.dumps(summary, indent=1) + "\n")
print(json.dumps(summary, indent=1))
print("legality notes (intended vs derived):", LEGAL_NOTES)
