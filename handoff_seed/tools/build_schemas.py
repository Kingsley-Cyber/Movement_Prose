"""Extend the v2 schemas additively, assemble drop-in target data files, apply the proposed card
fixes to copies, and prove three things:

1. every CURRENT repo data file and card still validates against the extended schemas (additive);
2. every target data file and proposed card validates against the extended schemas;
3. the slot-gating card validator flags today's leaky slots and passes the proposed cards.

Usage: python3 build_schemas.py <repo_root> <seed_dir> <out_dir>
Writes <out_dir>/schemas, <out_dir>/data, <out_dir>/cards_proposed, <out_dir>/validation_report.json
"""
from __future__ import annotations

import copy
import json
import sys
from collections import OrderedDict
from pathlib import Path

import jsonschema

REPO = Path(sys.argv[1])
SEED = Path(sys.argv[2])
OUT = Path(sys.argv[3])
for sub in ("schemas", "data", "cards_proposed", "style_templates"):
    (OUT / sub).mkdir(parents=True, exist_ok=True)


def read(p):
    return json.load(open(p))


def write(p, obj):
    Path(p).write_text(json.dumps(obj, indent=1, ensure_ascii=False) + "\n")


LANES = ["head_straight", "head_hook", "head_uppercut", "body", "leg", "entry", "clinch", "single_support"]
RANGES = ["outside", "kick", "punch", "close", "clinch", "ground"]
CLASSES = ["straight", "hook", "uppercut", "body_punch", "elbow", "knee", "kick_low", "kick_body", "kick_linear", "kick_high", "takedown", "clinch_entry"]
RESULTS_DEF = ["evaded", "blocked", "checked", "caught", "jammed"]
SKILLS = ["takedown_offense", "takedown_defense", "clinch_control", "top_control", "bottom_game", "submission_offense", "submission_defense", "scramble", "stand_up"]
RULESETS = ["boxing", "kickboxing", "muay_thai", "mma", "street", "lethwei"]
NUM = {"type": "number"}
STR = {"type": "string", "minLength": 1}
STRS = {"type": "array", "items": STR}

seed_tech = read(SEED / "techniques_v2_backfill.json")
seed_pos = read(SEED / "positions_v2_backfill.json")
seed_rules = read(SEED / "rulesets_v2.json")
seed_combos = read(SEED / "combinations_v2_backfill.json")
seed_debt = read(SEED / "debt_registry_v2_overlay.json")
seed_caps = read(SEED / "capability_grants.json")
seed_model = read(SEED / "model_v2_complete_seed.json")
seed_opts = read(SEED / "option_behavior_additions.json")
seed_fixes = read(SEED / "card_fixes.json")
TECH = {t["id"]: t for t in seed_tech["techniques"]}
CONTESTS = seed_pos["contests"]

schemas = {}

# ---------------------------------------------------------------- fighter card
s = read(REPO / "schemas/fighter_card_v2.schema.json")
s["title"] = s["title"] + " (v2.1 additive extension)"
s["properties"]["revision"] = {"type": "integer", "minimum": 1}
s["properties"]["laterality"] = {
    "type": "object", "required": ["dominant_hand", "dominant_leg"],
    "properties": {"dominant_hand": {"enum": ["right", "left", "ambidextrous"]}, "dominant_leg": {"enum": ["right", "left", "both"]},
                   "opposite_stance_experience": {"enum": ["low", "normal", "high"]}},
    "additionalProperties": False}
s["properties"]["signature_chains"] = STRS
RANKS = ["novice", "trained", "expert", "master", "grandmaster"]
s["properties"]["rank"] = {"enum": RANKS, "description": "D23 / handoff 7.18: story rank; missing = trained (no effect)"}
s["properties"]["school_mastery"] = {"type": "object", "propertyNames": {"pattern": "^[a-z_]+$"}, "additionalProperties": {"enum": RANKS},
                                     "description": "per-school rank; schools not listed sit at the card's rank; no value may exceed rank (validator)"}
slot = s["properties"]["synchronized_capabilities"]["items"]
slot["properties"]["goal"]["enum"] = slot["properties"]["goal"]["enum"] + ["wall_pressure", "reset_to_home_range", "position"]
schemas["fighter_card_v2.schema.json"] = s

# ---------------------------------------------------------------- option behavior
s = read(REPO / "schemas/option_behavior.schema.json")
s["title"] = s["title"] + " (v2.1 additive extension)" if "title" in s else "Option behavior (v2.1 additive extension)"
item = s["properties"]["options"]["items"]
ENTRY = {"oneOf": [STR, {"type": "object", "required": ["technique", "result"], "properties": {"technique": STR, "result": {"enum": RESULTS_DEF}}, "additionalProperties": False}]}
CLASS_LISTS = {"type": "object", "propertyNames": {"enum": CLASSES}, "additionalProperties": {"type": "array", "minItems": 1, "items": ENTRY}}
LANESPEC = {"oneOf": [{"const": "all"}, {"type": "array", "items": {"enum": LANES}}]}
item["properties"].update({
    "grappling_profile": {"type": "object", "required": SKILLS, "properties": {k: {"type": "number", "minimum": 0, "maximum": 5} for k in SKILLS}, "additionalProperties": False},
    "grappling_modifiers": {"type": "object", "propertyNames": {"enum": SKILLS}, "additionalProperties": NUM},
    "grappling_modifiers_condition": {"type": "object", "properties": {"unless": {"enum": ["wall_near"]}}, "additionalProperties": False},
    "lead_foot_outside_delta": NUM,
    "selection_profile": {"type": "object", "required": ["initiative_delta", "switch_after_stalls", "patience", "risk", "combo_length"],
                          "properties": {"initiative_delta": NUM, "initiative_delta_when_waiting": NUM, "switch_after_stalls": {"type": "integer", "minimum": 1},
                                         "patience": {"type": "number", "exclusiveMinimum": 0}, "risk": {"type": "number", "exclusiveMinimum": 0},
                                         "combo_length": {"type": "number", "exclusiveMinimum": 0}, "pull_out_probability": {"type": "number", "minimum": 0, "maximum": 1}},
                          "additionalProperties": False},
    "native_defense": {"type": "object", "required": ["by_class"], "properties": {"by_class": CLASS_LISTS, "at_wall": CLASS_LISTS}, "additionalProperties": False},
    "defense_prepend": {"type": "object", "propertyNames": {"enum": CLASSES}, "additionalProperties": STRS},
    "kick_defense_prepend": {"type": "object", "propertyNames": {"enum": CLASSES}, "additionalProperties": STRS},
    "kick_defense_window_delta": {"oneOf": [NUM, {"type": "object", "required": ["value"], "properties": {"value": NUM, "unless": {"enum": ["wall_near"]}}, "additionalProperties": False}]},
    "breakdown_rules": {"type": "array", "items": {"type": "object", "required": ["when_any", "lanes"],
                                                  "properties": {"when_any": {"type": "object"}, "lanes": LANESPEC, "delta": NUM, "delta_from_model": STR, "delta_default": NUM},
                                                  "additionalProperties": False}},
    "range_lane_bonus": {"type": "object", "required": ["ranges", "lanes", "delta"],
                         "properties": {"ranges": {"type": "array", "items": {"enum": RANGES}}, "lanes": LANESPEC, "delta": NUM, "unless": {"enum": ["wall_near"]}},
                         "additionalProperties": False},
    "counter_tendency_condition": {"type": "object", "properties": {"ranges": {"type": "array", "items": {"enum": RANGES}}, "unless": {"enum": ["wall_near"]}}, "additionalProperties": False},
    "on_body_damage_extra_fatigue_fraction": {"type": "number", "minimum": 0},
    "distance_control_condition": {"type": "object", "properties": {"unless": {"enum": ["wall_near"]}}, "additionalProperties": False},
    "pull_out_probability": {"type": "number", "minimum": 0, "maximum": 1},
    "supported_by_v2": STRS,
    "damage_rules": {"type": "object"},
})
schemas["option_behavior.schema.json"] = s

# ---------------------------------------------------------------- positions
s = read(REPO / "schemas/position_map.schema.json")
pi = s["properties"]["positions"]["items"]
pi["properties"].update({"roles": {"type": "array", "minItems": 2, "maxItems": 2, "items": STR},
                         "control_value_per_second": {"type": "object", "additionalProperties": {"type": "number", "minimum": 0}},
                         "status": {"enum": ["existing", "new", "deprecated"]}, "alias_of": STR})
ti = s["properties"]["transitions"]["items"]
ti["properties"].update({"actor_role": STR, "actor_role_after": STR, "contest": {"enum": CONTESTS}, "via_outcome": STR})
s["properties"].update({"contests": {"type": "array", "items": STR}, "contest_skill_map": {"type": "object"},
                        "legacy_position_map": {"type": "object"}, "legacy_transition_map": {"type": "array"}})
schemas["position_map.schema.json"] = s

# ---------------------------------------------------------------- model config
s = read(REPO / "schemas/model_config_v2.schema.json")
NEW_MODEL_SECTIONS = ["posture", "readiness", "kick_defense", "damage", "simulation", "legacy", "laterality", "grappling", "vertical", "knockdowns",
                      "rounds", "energy", "selection", "slot_triggers", "pace", "fight_momentum", "defense_contest", "geometry", "finishes", "director", "audits",
                      "mastery"]
for k in NEW_MODEL_SECTIONS:
    assert k not in s["properties"], k
    s["properties"][k] = {"type": "object"}
schemas["model_config_v2.schema.json"] = s

# ---------------------------------------------------------------- fight settings
s = read(REPO / "schemas/fight_settings.schema.json")
s["properties"]["ruleset"]["enum"] = RULESETS
s["properties"].update({"rounds": {"type": "integer", "minimum": 1, "maximum": 12}, "round_length_s": {"type": "number", "exclusiveMinimum": 0, "maximum": 600},
                        "rest_s": {"type": "number", "minimum": 0}, "fps": {"const": 24}, "runs": {"type": "integer", "minimum": 1}})
schemas["fight_settings.schema.json"] = s

# ---------------------------------------------------------------- fight state
s = read(REPO / "schemas/fight_state_v2.schema.json")
actor = s["properties"]["actors"]["additionalProperties"]
actor["properties"].update({
    "damage_by_side": {"type": "object", "required": ["head_left", "head_right", "body_left", "body_right", "leg_left", "leg_right", "arm_left", "arm_right"],
                       "properties": {k: {"type": "number", "minimum": 0} for k in ["head_left", "head_right", "body_left", "body_right", "leg_left", "leg_right", "arm_left", "arm_right"]},
                       "additionalProperties": False},
    "cuts": {"type": "object", "properties": {"left": {"type": "integer", "minimum": 0, "maximum": 3}, "right": {"type": "integer", "minimum": 0, "maximum": 3}}, "additionalProperties": False},
    "laterality": {"type": "object", "properties": {"dominant_hand": STR, "dominant_leg": STR, "opposite_stance_experience": STR, "natural": {"type": "boolean"}}},
    "fight_momentum": {"type": "number", "minimum": -1, "maximum": 1},
    "knockdowns": {"type": "integer", "minimum": 0}, "stun_exchanges": {"type": "integer", "minimum": 0}, "slot_stalls": {"type": "integer", "minimum": 0},
    "combo_state": {"type": ["object", "null"]}, "airborne_phase": {"enum": ["none", "takeoff", "apex", "landing"]},
    "grips": {"type": "object"}, "control_time_s": {"type": "number", "minimum": 0}, "role": {"type": ["string", "null"]},
})
s["properties"].update({"round": {"type": "integer", "minimum": 1}, "ruleset": {"enum": RULESETS},
                        "pair_position": {"type": "object", "required": ["position_id", "roles"], "properties": {"position_id": STR, "roles": {"type": "object", "additionalProperties": STR}}},
                        "submission": {"type": ["object", "null"]}, "decision_scores": {"type": "object"}})
schemas["fight_state_v2.schema.json"] = s

# ---------------------------------------------------------------- exchange event
s = read(REPO / "schemas/exchange_event_v2.schema.json")
OBJN = {"type": ["object", "null"]}
s["properties"].update({"round": {"type": "integer", "minimum": 1}, "incoming_class": STR, "initiative_scores": {"type": "object"},
                        "selection": OBJN, "laterality": OBJN, "hit": OBJN, "defense": OBJN, "grappling": OBJN, "damage_breakdown": OBJN,
                        "knockdown": {"type": "boolean"}, "standing_count": OBJN, "stun_applied": {"type": "boolean"},
                        "slot_switch_reason": {"type": ["string", "null"]}, "combo_id": {"type": ["string", "null"]}, "rank_levels": OBJN})
schemas["exchange_event_v2.schema.json"] = s

# ---------------------------------------------------------------- simulation result
s = read(REPO / "schemas/simulation_result_v2.schema.json")
s["properties"].update({"method_split": {"type": "object"}, "finish_time_distribution": {"type": "object"}, "slot_path_frequencies": {"type": "object"},
                        "deciding_causes": {"type": "array"}, "director": OBJN, "parallel_workers": {"type": "integer", "minimum": 1}})
schemas["simulation_result_v2.schema.json"] = s

# ---------------------------------------------------------------- technique (from build_seeds)
schemas["technique_v2.schema.json"] = read(SEED / "technique_v2.schema.extended.json")

# ---------------------------------------------------------------- new schemas
schemas["rulesets_v2.schema.json"] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema", "title": "BLOCK Rulesets v2.1", "type": "object",
    "required": ["version", "rulesets"], "additionalProperties": False,
    "properties": {"version": {"const": "block-2"}, "rulesets": {"type": "object", "propertyNames": {"enum": RULESETS}, "additionalProperties": {
        "type": "object", "additionalProperties": False,
        "required": ["legal_kinds", "allowed_techniques", "banned_techniques", "clinch", "ground", "environment", "default_rounds", "default_round_s", "decision_weights"],
        "properties": {
            "legal_kinds": STRS, "allowed_techniques": STRS, "banned_techniques": STRS,
            "clinch": {"type": "object", "required": ["allowed", "referee_break_after_exchanges", "allowed_grips"],
                       "properties": {"allowed": {"type": "boolean"}, "referee_break_after_exchanges": {"type": ["integer", "null"], "minimum": 0},
                                      "allowed_grips": {"oneOf": [{"const": "all"}, STRS]}, "note": {"type": "string"}}, "additionalProperties": False},
            "ground": {"type": "object", "required": ["allowed", "on_knockdown"],
                       "properties": {"allowed": {"type": "boolean"}, "on_knockdown": {"enum": ["standing_count", "fight_continues"]},
                                      "on_sweep": {"enum": ["reset_standing_with_score", "continue"]}}, "additionalProperties": False},
            "environment": STR, "default_rounds": {"type": "integer", "minimum": 1}, "default_round_s": {"type": "number", "exclusiveMinimum": 0},
            "decision_weights": {"type": "object", "required": ["clean_strikes", "damage", "control", "aggression"], "additionalProperties": {"type": "number", "minimum": 0}},
            "equipment": {"type": "object", "required": ["gloves", "punch_damage_multiplier", "cut_chance_bonus"],
                          "properties": {"gloves": {"type": "boolean"}, "punch_damage_multiplier": {"type": "number", "minimum": 0.5, "maximum": 2.0},
                                         "cut_chance_bonus": {"type": "number", "minimum": 0, "maximum": 0.5}}, "additionalProperties": False},
            "knockdown_rules": {"type": "object", "properties": {"per_round_limit": {"type": ["integer", "null"], "minimum": 1}, "per_fight_limit": {"type": ["integer", "null"], "minimum": 1}},
                                "additionalProperties": False},
            "default_rest_s": {"type": "number", "minimum": 0},
            "notes": {"type": "string"}}}}}}
schemas["combinations_v2.schema.json"] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema", "title": "BLOCK Combination chains v2.1", "type": "object",
    "required": ["version", "combinations"], "additionalProperties": False,
    "properties": {"version": {"const": "block-2"}, "combinations": {"type": "array", "items": {
        "type": "object", "additionalProperties": False,
        "required": ["id", "chain", "school", "follow_up_accuracy_bonus", "setup_frames_saved", "trigger_on", "requires_previous_outcome", "same_slot_required"],
        "properties": {"id": STR, "chain": {"type": "array", "minItems": 2, "items": STR}, "school": STR,
                       "follow_up_accuracy_bonus": {"type": "number", "minimum": 0, "maximum": 0.2}, "setup_frames_saved": {"type": "integer", "minimum": 0},
                       "trigger_on": {"enum": ["landed", "defended", "executed"]}, "requires_previous_outcome": STRS, "same_slot_required": {"type": "boolean"}}}}}}
schemas["debt_registry_v2.schema.json"] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema", "title": "BLOCK debt registry v2 overlay", "type": "object",
    "required": ["version", "base_registry", "merge_rule", "debts"], "additionalProperties": False,
    "properties": {"version": {"const": "block-2"}, "base_registry": {"const": "data/debt_registry.json"}, "merge_rule": STR,
                   "opening_to_techniques": {"type": "object", "additionalProperties": STRS},
                   "debts": {"type": "array", "items": {"type": "object", "required": ["debt_id", "add_technique_ids"],
                                                        "properties": {"debt_id": STR, "opening": STR, "required_range": STR, "current_technique_ids": STRS, "add_technique_ids": STRS},
                                                        "additionalProperties": False}}}}
schemas["capabilities_v2.schema.json"] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema", "title": "BLOCK capabilities v2.1", "type": "object",
    "required": ["version", "capabilities"], "additionalProperties": False,
    "properties": {"version": {"const": "block-2"}, "core_rule": STR, "capabilities": {"type": "object", "additionalProperties": {
        "type": "object", "required": ["description", "core", "modifier", "status"], "additionalProperties": False,
        "properties": {"description": STR, "core": STRS, "modifier": {"type": "boolean"}, "status": {"enum": ["existing", "new", "proposal_owner_decision"]},
                       "defense_prepend": {"type": "object", "propertyNames": {"enum": CLASSES}, "additionalProperties": STRS}}}}}}

for name, sch in schemas.items():
    jsonschema.Draft202012Validator.check_schema(sch)
    write(OUT / "schemas" / name, sch)

# =============================================================================
# Target data files
# =============================================================================
model = copy.deepcopy(seed_model["existing_model_v2_keys_preserved"])
for section, items in seed_model["engine_constants_to_move_into_data"].items():
    sec = model.setdefault(section, OrderedDict())
    for name, entry in items.items():
        if name == "finish_thresholds":
            sec[name] = {"submission_stage": entry["value"]["submission_stage"],
                         "regional_limits_key": "regional_damage_limits"}
            continue
        if "existing_key" in entry:
            continue
        sec[name] = entry["value"]
model["legacy"] = seed_model["legacy"]
for section, body in seed_model["new_sections"].items():
    if section in model and isinstance(model[section], dict):
        model[section].update(body)
    else:
        model[section] = body
write(OUT / "data/model_v2.json", model)

opts = read(REPO / "data/option_behaviors.json")
for o in opts["options"]:
    for k, v in seed_opts["per_option"].get(o["id"], {}).items():
        o[k] = v
write(OUT / "data/option_behaviors.json", opts)
write(OUT / "data/techniques_v2.json", seed_tech)
write(OUT / "data/positions.json", seed_pos)
write(OUT / "data/rulesets_v2.json", seed_rules)
write(OUT / "data/combinations_v2.json", seed_combos)
write(OUT / "data/debt_registry_v2.json", seed_debt)

CAP_DESC = {
    "anti_grappling": "Takedown and clinch defense: sprawl, whizzer, jam step, pummel, wall walk and get-ups.",
    "basic_movement": "Everyone: footwork, feints, lean-back and step-back evasions, clinch break, stand-up.",
    "bjj": "Guard pulls, sweeps, passes, back takes and submissions.",
    "boxing": "Punches (jab, cross, hooks, uppercuts, body shots) and boxing defense (parry, shell, slip, roll).",
    "cage_plum": "Conditional: plum and knees against the cage/wall.",
    "clinch": "Collar ties, body locks, pummeling and clinch knees.",
    "inside_combinations": "Short inside punches: shovel hook, short uppercut.",
    "judo": "Grips, trips and throws.",
    "karate": "Distance kicking (side, front, round, spinning) with straight punches.",
    "kickboxing": "Punches plus round kicks, teeps, checks and knees.",
    "pressure_footwork": "Modifier: cut-off steps that trap an opponent against the wall. Only alongside a striking school.",
    "sanda": "Kicks, kick catches and catch-sweeps, foot sweeps.",
    "shield": "Shield frame defense and the counter hook off it.",
    "switch_step": "Modifier: switching stance mid-exchange. Only alongside a school.",
    "untrained_striking": "Untrained power: wild hooks, haymakers, straights, shoves, headbutts (street).",
    "wall_boxing": "Wall ties and punches while pinning an opponent to the wall.",
    "wrestling": "Shots, trips, rides, ground control and escapes.",
}
caps = OrderedDict()
for cid in sorted(seed_caps["grants"]):
    status = "existing"
    desc = CAP_DESC.get(cid)
    if cid in seed_caps["new_capabilities"]:
        desc = seed_caps["new_capabilities"][cid]
        status = "proposal_owner_decision" if cid == "counter_boxing" else "new"
    caps[cid] = {"description": desc, "core": seed_caps["core"].get(cid, []), "modifier": cid in ("switch_step", "pressure_footwork"), "status": status}
    if cid in seed_caps.get("defense_prepend", {}):
        caps[cid]["defense_prepend"] = seed_caps["defense_prepend"][cid]
write(OUT / "data/capabilities_v2.json", {"version": "block-2", "core_rule": seed_caps["core_rule"], "capabilities": caps})

# =============================================================================
# Proposed cards (copies; owner approval required before they replace cards/v2)
# =============================================================================
current_cards = {p.stem: read(p) for p in sorted((REPO / "cards/v2").glob("*.json"))}
proposed = {}
for fid, card in current_cards.items():
    c = copy.deepcopy(card)
    fx = seed_fixes[fid]
    c["revision"] = 1
    for sc in fx["slot_changes"]:
        slot_obj = next(s_ for s_ in c["synchronized_capabilities"] if s_["id"] == sc["slot"])
        for key in ("capabilities", "sequence", "trigger", "home_range", "goal", "abandon_rule", "links"):
            if key in sc["proposal"]:
                slot_obj[key] = sc["proposal"][key]
    for tid in fx["active_techniques_add"]:
        if tid not in c["active_techniques"]:
            c["active_techniques"].append(tid)
    proposed[fid] = c
    write(OUT / "cards_proposed" / f"{fid}.json", c)

# =============================================================================
# Validation
# =============================================================================
report = OrderedDict()


def check(label, instance, schema):
    try:
        jsonschema.validate(instance, schema)
        return {"check": label, "ok": True}
    except jsonschema.ValidationError as e:
        return {"check": label, "ok": False, "error": e.message[:240], "path": "/".join(str(x) for x in e.absolute_path)}


S = {k: v for k, v in schemas.items()}
CUR = {k: read(REPO / "schemas" / k) for k in schemas if (REPO / "schemas" / k).exists()}
add = []
add.append(check("current data/option_behaviors.json vs extended", read(REPO / "data/option_behaviors.json"), S["option_behavior.schema.json"]))
add.append(check("current data/techniques_v2.json vs extended", read(REPO / "data/techniques_v2.json"), S["technique_v2.schema.json"]))
add.append(check("current data/positions.json vs extended", read(REPO / "data/positions.json"), S["position_map.schema.json"]))
add.append(check("current data/model_v2.json vs extended", read(REPO / "data/model_v2.json"), S["model_config_v2.schema.json"]))
for fid, card in current_cards.items():
    add.append(check(f"current cards/v2/{fid}.json vs extended", card, S["fighter_card_v2.schema.json"]))
for p in sorted((REPO / "cards").glob("*.json")):
    add.append(check(f"block-1 cards/{p.name} vs extended", read(p), S["fighter_card_v2.schema.json"]))
report["additivity_current_data_vs_extended_schemas"] = add

tgt = []
tgt.append(check("target data/option_behaviors.json vs extended", opts, S["option_behavior.schema.json"]))
tgt.append(check("target data/techniques_v2.json vs extended", seed_tech, S["technique_v2.schema.json"]))
tgt.append(check("target data/positions.json vs extended", seed_pos, S["position_map.schema.json"]))
tgt.append(check("target data/model_v2.json vs extended", model, S["model_config_v2.schema.json"]))
tgt.append(check("target data/rulesets_v2.json", seed_rules, S["rulesets_v2.schema.json"]))
tgt.append(check("target data/combinations_v2.json", seed_combos, S["combinations_v2.schema.json"]))
tgt.append(check("target data/debt_registry_v2.json", seed_debt, S["debt_registry_v2.schema.json"]))
tgt.append(check("target data/capabilities_v2.json", read(OUT / "data/capabilities_v2.json"), S["capabilities_v2.schema.json"]))
for fid, card in proposed.items():
    tgt.append(check(f"proposed card {fid} vs extended", card, S["fighter_card_v2.schema.json"]))
report["targets_vs_extended_schemas"] = tgt

old = []
old.append(check("target option_behaviors.json vs CURRENT schema", opts, CUR["option_behavior.schema.json"]))
old.append(check("target techniques_v2.json vs CURRENT schema", seed_tech, CUR["technique_v2.schema.json"]))
old.append(check("target positions.json vs CURRENT schema", seed_pos, CUR["position_map.schema.json"]))
old.append(check("target model_v2.json vs CURRENT schema", model, CUR["model_config_v2.schema.json"]))
report["targets_vs_current_schemas (expected to fail: replace schema and data in the same commit)"] = old
assert len(opts["options"]) == 57, "option count must stay 57"

# ---- slot-gating validator (reference implementation of the §6.1 rules) ----
GRANTS = seed_caps["grants"]
CORE = seed_caps["core"]
BASIC = set(GRANTS["basic_movement"])
MODIFIERS = {"switch_step", "pressure_footwork"}
PRED = seed_model["new_sections"]["slot_triggers"]["predicates"]
STALLS = seed_model["new_sections"]["slot_triggers"]["stall_conditions"]


def card_available(card):
    trained = set(card["baseline_capabilities"]) | {c for s_ in card["synchronized_capabilities"] for c in s_["capabilities"]}
    active = set(card["active_techniques"])
    out = set()
    for cap in trained:
        g = set(GRANTS.get(cap, []))
        out |= set(CORE.get(cap, [])) | (g & active)
        out |= {t for t in g if TECH[t]["kind"] == "defense" or TECH[t]["usage"] == "defense"}
    return out, trained


def validate_card_slots(card):
    problems = []
    avail, trained = card_available(card)
    slot_ids = [s_["id"] for s_ in card["synchronized_capabilities"]]
    starts = [s_["id"] for s_ in card["synchronized_capabilities"] if s_.get("trigger") == "fight_start"]
    if len(starts) != 1:
        problems.append(f"expected exactly one fight_start slot, found {starts}")
    pools = {}
    for s_ in card["synchronized_capabilities"]:
        caps_ = set(s_["capabilities"])
        granted = set()
        for cap in caps_ | {"basic_movement"}:
            granted |= set(GRANTS.get(cap, []))
        attack_pool = {t for t in granted if t in avail and TECH[t]["usage"] in ("attack", "both", "counter") and TECH[t]["kind"] not in ("movement", "feint")}
        nonbasic = attack_pool - BASIC
        reset = s_.get("goal") == "reset_to_home_range"
        if reset:
            tools = {t for t in granted - BASIC if TECH[t]["kind"] in ("defense", "escape")}
            if len(tools) < 2:
                problems.append(f"{s_['id']}: reset slot grants fewer than 2 defense/escape tools")
        elif len(nonbasic) < 2:
            problems.append(f"{s_['id']}: slot grants fewer than 2 usable non-basic attacking techniques ({sorted(nonbasic)})")
        if caps_ and caps_ <= MODIFIERS:
            problems.append(f"{s_['id']}: modifier capability without a school")
        for tid in s_.get("sequence", []):
            if tid not in granted:
                problems.append(f"{s_['id']}: sequence item '{tid}' is not granted by the slot's capabilities {sorted(caps_)}")
            elif tid not in avail:
                problems.append(f"{s_['id']}: sequence item '{tid}' is granted but not trained (not in active_techniques or a core)")
        if s_.get("trigger") and s_["trigger"] not in PRED:
            problems.append(f"{s_['id']}: unknown trigger '{s_['trigger']}'")
        cond = (s_.get("abandon_rule") or {}).get("condition")
        if cond and cond not in STALLS:
            problems.append(f"{s_['id']}: unknown abandon condition '{cond}'")
        for ln in s_.get("links", []):
            if ln not in slot_ids:
                problems.append(f"{s_['id']}: link '{ln}' is not a slot of this card")
        pools[s_["id"]] = frozenset(t for t in granted - BASIC if t in avail and TECH[t]["kind"] != "defense")
    level = {"novice": -1, "trained": 0, "expert": 1, "master": 2, "grandmaster": 3}
    cap_rank = level[card.get("rank", "trained")]
    for school, r in (card.get("school_mastery") or {}).items():
        if school not in trained:
            problems.append(f"school_mastery: '{school}' is not a capability this card trains")
        if level[r] > cap_rank:
            problems.append(f"school_mastery: '{school}' at {r} exceeds the card's rank {card.get('rank', 'trained')} (rank is a ceiling)")
    seen = {}
    for sid, pool in pools.items():
        if pool and pool in seen:
            problems.append(f"{sid}: identical non-basic technique pool (attacks + movement) to {seen[pool]}")
        seen.setdefault(pool, sid)
    return problems


report["slot_validator_current_cards"] = {fid: validate_card_slots(c) for fid, c in current_cards.items()}
report["slot_validator_proposed_cards"] = {fid: validate_card_slots(c) for fid, c in proposed.items()}

# ---- D23 rank fields: a ranked card passes the schema and the validator; a card breaking the ceiling is rejected ----
_ranked = copy.deepcopy(proposed["donnell"])
_ranked["rank"] = "master"
_ranked["school_mastery"] = {"boxing": "master", "inside_combinations": "expert"}
jsonschema.validate(_ranked, schemas["fighter_card_v2.schema.json"])
_bad = copy.deepcopy(_ranked)
_bad["school_mastery"] = {"boxing": "grandmaster", "judo": "trained"}
_bad_problems = [p_ for p_ in validate_card_slots(_bad) if p_.startswith("school_mastery")]
report["rank_fields_check"] = {"ranked_card_schema_ok": True,
                               "ranked_card_validator_problems": [p_ for p_ in validate_card_slots(_ranked) if p_.startswith("school_mastery")],
                               "ceiling_breaking_card_rejected": _bad_problems}
assert not report["rank_fields_check"]["ranked_card_validator_problems"] and len(_bad_problems) == 2, report["rank_fields_check"]

# ---- test guards on the target defense lists (mirror the existing assertions) ----
NAT = {o["id"]: o for o in opts["options"]}


def first_defense(card, cls, wall=False):
    avail, _ = card_available(card)
    d = card["dimensions"]
    lst = []
    trained = set(card["baseline_capabilities"]) | {c for s_ in card["synchronized_capabilities"] for c in s_["capabilities"]}
    for cap in sorted(trained):
        lst += seed_caps.get("defense_prepend", {}).get(cap, {}).get(cls, [])
    lst += NAT.get(d.get("kicking") or "", {}).get("kick_defense_prepend", {}).get(cls, [])
    lst += NAT.get(d.get("hands") or "", {}).get("defense_prepend", {}).get(cls, [])
    nd = NAT[d.get("defense") or "defense.block_absorb"]["native_defense"]
    lst += (nd.get("at_wall", {}).get(cls) if wall and cls in nd.get("at_wall", {}) else nd["by_class"][cls])
    for e in lst:
        tid = e["technique"] if isinstance(e, dict) else e
        if tid in avail:
            return tid
    return "retreat"


guards = OrderedDict()
cc = current_cards
guards["rook cross -> retreat (test)"] = first_defense(cc["street"], "straight") == "retreat"
guards["rook has no shell_block (test)"] = "shell_block" not in card_available(cc["street"])[0]
guards["niran cross != slip (test)"] = first_defense(cc["thai"], "straight") != "slip"
guards["aya cross in (pivot, retreat) (test)"] = first_defense(cc["karate"], "straight") in ("pivot", "retreat")
guards["niran low_kick -> check (test)"] = first_defense(cc["thai"], "kick_low") == "check"
guards["mio body_kick -> kick_catch (test)"] = first_defense(cc["sanda_judo"], "kick_body") == "kick_catch"
guards["aya head_kick far -> evade_step_back (test)"] = first_defense(cc["karate"], "kick_high") == "evade_step_back"
guards["aya head_kick at wall -> shell_block (test)"] = first_defense(cc["karate"], "kick_high", wall=True) == "shell_block"
guards["aya karate core reproduces hidden grant (test)"] = {"side_kick", "teep", "body_kick", "spinning_back_kick"} <= card_available(cc["karate"])[0]
report["test_guards_on_target_data"] = guards
assert all(guards.values()), guards

# ---- availability parity: legacy (active & v1 grants) vs seed rule, attacks only ----
v1 = {t["id"]: t for t in read(REPO / "data/techniques.json")["techniques"]}
parity = OrderedDict()
for fid, card in current_cards.items():
    trained = set(card["baseline_capabilities"]) | {c for s_ in card["synchronized_capabilities"] for c in s_["capabilities"]}
    legacy_av = {t for t in card["active_techniques"] if t in v1 and "mma" in v1[t]["ruleset_legality"] and set(v1[t]["required_capabilities"]) & trained}
    if "karate" in trained and card["dimensions"].get("kicking") == "kicking.karate":
        legacy_av |= {"side_kick", "teep", "body_kick", "spinning_back_kick"}
    new_av, _ = card_available(card)
    new_av = {t for t in new_av if "mma" in TECH[t]["legal_in"]}
    att = lambda xs: {t for t in xs if TECH[t]["kind"] not in ("defense",) and TECH[t]["usage"] != "defense"}  # noqa: E731
    parity[fid] = {"attacks_only_in_legacy": sorted(att(legacy_av) - att(new_av)), "attacks_only_in_v2_1": sorted(att(new_av) - att(legacy_av)),
                   "defenses_added_by_pool_rule": sorted((new_av - legacy_av) - att(new_av))}
report["availability_parity_mma"] = parity

# ---- style templates: one starter card per style, existing 57 options only ----
exec(open(Path(__file__).with_name("style_templates.py")).read())
sys.path.insert(0, str(REPO))
from engine.capabilities import OPTION_REQUIRED_TECHS, UNTRAINED_PUNCH_OPTIONS  # noqa: E402
IDX = {o["id"]: o for o in read(REPO / "data/engine_index.json")["options"]}
SUP = {o["id"]: set(o.get("supported_by_v2", [])) for o in opts["options"]}
LABELS = {1: "Brawler", 2: "Two-piece", 3: "Triad", 4: "Anomaly"}


def option_supported_v2(card, oid):
    if oid is None:
        return True
    trained = set(card["baseline_capabilities"]) | {c for s_ in card["synchronized_capabilities"] for c in s_["capabilities"]}
    active = {t for t in card["active_techniques"] if t in TECH and set(TECH[t]["required_capabilities"]) & trained}
    o = IDX[oid]
    trefs = o["technique_refs"]
    if o["dimension"] == "tie":
        v1 = any(t in active for t in trefs if t != "body_hook")
    elif o["dimension"] == "kicking":
        if oid == "kicking.none":
            v1 = bool(active)
        else:
            v1 = (oid == "kicking.sanda" and "sanda_sweep" in active) or any(t in active for t in trefs if TECH[t]["kind"] == "kick")
    elif oid in OPTION_REQUIRED_TECHS:
        v1 = bool(OPTION_REQUIRED_TECHS[oid] & active)
    else:
        v1 = any(t in active for t in trefs) or (oid in UNTRAINED_PUNCH_OPTIONS and "untrained_striking" in trained and "haymaker" in active)
    return v1 or bool(SUP.get(oid, set()) & active)


tpl_report = OrderedDict()
style_rows = []
for spec in TEMPLATES:
    fid = spec["id"]
    slots = []
    for i, sl in enumerate(spec["slots"], 1):
        slots.append({"id": f"{fid}.slot.{i}", "capabilities": sl["caps"], "description": sl["desc"], "trigger": sl["trigger"], "sequence": sl["seq"],
                      "home_range": sl["home"], "goal": sl["goal"], "abandon_rule": {"max_consecutive_stalls": sl["stalls"], "condition": sl["cond"]},
                      "links": [f"{fid}.slot.{j}" for j in sl["links"]]})
    active = []
    for tid in ["step", "retreat", "pivot", "feint"] + [m for sl in spec["slots"] for m in sl["seq"]] + spec.get("extra_active", []):
        if tid not in active:
            active.append(tid)
    seams = sorted({d for o in spec["dims"].values() if o for d in IDX[o]["exploitable_debt_ids"]})
    card = OrderedDict()
    card["version"] = "block-2"
    card["revision"] = 1
    card["fighter_id"] = fid
    card["name"] = f"{spec['style']} template"
    card["combat_identity"] = f"{spec['style']} starter build (rename and customize)"
    card["dimensions"] = spec["dims"]
    card["adaptation"] = "mma"
    card["orientation"] = spec["orientation"]
    if "laterality" in spec:
        card["laterality"] = spec["laterality"]
    card["slot_count"] = len(slots)
    card["slot_label"] = LABELS[len(slots)]
    card["synchronized_capabilities"] = slots
    card["baseline_capabilities"] = ["basic_movement", "untrained_striking"]
    card["tempo"] = spec["tempo"]
    card["preferred_ranges"] = spec["preferred"]
    card["debt_sentence"] = f"{spec['style']} template: every option's weakness is listed in exploitable_seams."
    card["exploitable_seams"] = seams
    card["active_techniques"] = active
    card["signature_moves"] = spec["signature"]
    card["airborne_training"] = spec["airborne"]
    card["conditional_abilities"] = []
    card["combat_limitations"] = [f"Template card for {spec['style']}: replace with the character's own limitations."]
    card["fighting_description"] = {"does": spec["slots"][0]["desc"], "wins": "By the style's signature tools (see signature_moves).",
                                    "avoids": "Fighting outside its home range.", "beaten_by": "Opponents who exploit its listed seams."}
    card["appearance"] = {"clothing": "TBD", "identity_anchor": "TBD", "props": []}
    card["provenance"] = {"classification": "CANON", "note": "style template from the v2.1 handoff; rename and customize before use"}
    problems = []
    try:
        jsonschema.validate(card, schemas["fighter_card_v2.schema.json"])
    except jsonschema.ValidationError as e:
        problems.append("schema: " + e.message[:160])
    problems += validate_card_slots(card)
    for dim, oid in spec["dims"].items():
        if oid is not None and not option_supported_v2(card, oid):
            problems.append(f"option {oid} not backed by trained techniques")
    trained = set(card["baseline_capabilities"]) | {c for s_ in slots for c in s_["capabilities"]}
    for tid in active:
        if tid not in TECH:
            problems.append(f"unknown technique {tid}")
        elif not (set(TECH[tid]["required_capabilities"]) & trained):
            problems.append(f"technique without training: {tid}")
        elif TECH[tid]["requires_airborne_training"] and tid not in spec["airborne"]["techniques"]:
            problems.append(f"airborne technique not in airborne_training: {tid}")
    for s_ in slots:
        if len(s_["capabilities"]) > 2:
            problems.append(f"{s_['id']}: more than 2 capabilities")
    tpl_report[fid] = problems
    write(OUT / "style_templates" / f"{fid}.json", card)
    school = fid[len("tpl_"):]
    assert school in seed_caps["grants"], school
    granted = sorted(t for t in TECH if school in TECH[t]["required_capabilities"])
    picks = ", ".join(f"{d} `{(o or 'null').split('.', 1)[-1]}`" for d, o in spec["dims"].items())
    alts = "; ".join(f"{d}: " + "/".join(x.split(".", 1)[1] for x in v) for d, v in spec.get("alt", {}).items())
    style_rows.append([spec["style"], f"`{school}`", len(granted), picks, alts or "", f"`{fid}`",
                       " / ".join(f"[{'+'.join(sl['caps'])}]" for sl in spec["slots"]), ", ".join(f"`{m}`" for m in spec["signature"]), spec["ruleset_home"]])
report["style_templates"] = tpl_report
assert all(not v for v in tpl_report.values()), tpl_report
hdr = ["style", "school", "moves granted", "recipe (7 picks from the existing 57 options)", "acceptable swaps", "template", "slots", "signature", "natural ruleset"]
md = ["| " + " | ".join(hdr) + " |", "|" + "|".join("---" for _ in hdr) + "|"] + ["| " + " | ".join(str(c) for c in r) + " |" for r in style_rows]
(OUT / "style_packs_table.md").write_text("\n".join(md) + "\n")

write(OUT / "validation_report.json", report)
fails = [r for r in report["additivity_current_data_vs_extended_schemas"] + report["targets_vs_extended_schemas"] if not r["ok"]]
print("schemas:", len(schemas), "| additivity+target checks:", len(report["additivity_current_data_vs_extended_schemas"]) + len(report["targets_vs_extended_schemas"]), "| failures:", len(fails))
for f in fails:
    print("  FAIL", f)
print("vs current schemas:", [(r["check"], r["ok"]) for r in old])
print("slot validator, current cards:", {k: len(v) for k, v in report["slot_validator_current_cards"].items()})
print("slot validator, proposed cards:", {k: v for k, v in report["slot_validator_proposed_cards"].items() if v})
print("availability parity (attacks lost):", {k: v["attacks_only_in_legacy"] for k, v in parity.items() if v["attacks_only_in_legacy"]})
print("style templates:", {k: (v or "ok") for k, v in tpl_report.items()})
assert not fails
