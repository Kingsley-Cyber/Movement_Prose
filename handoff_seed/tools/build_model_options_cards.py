"""Build the model_v2 constant registry, option-behavior additions and per-card fix proposals.

Every constant currently hardcoded in engine/simulator_v2.py (commit 0d0734d) is listed with its
current value and source line so the refactor can move it into data WITHOUT changing behaviour.
`legacy` holds verbatim tables/rules that P1a must reproduce exactly (golden equality).
`new_sections` carry starting defaults for new mechanics (tuned later by audits).

Usage: python3 build_model_options_cards.py <repo_root> <seed_dir>
"""
from __future__ import annotations

import json
import sys
from collections import OrderedDict
from pathlib import Path

REPO = Path(sys.argv[1])
OUT = Path(sys.argv[2])
sys.path.insert(0, str(REPO))
from engine import simulator_v2 as SIM  # noqa: E402  (read-only: exact legacy tables)

model = json.load(open(REPO / "data/model_v2.json"))
ob = {o["id"]: o for o in json.load(open(REPO / "data/option_behaviors.json"))["options"]}
seed_tech = {t["id"]: t for t in json.load(open(OUT / "techniques_v2_backfill.json"))["techniques"]}
OPTION_IDS = set(ob)

SRC = "engine/simulator_v2.py"


def c(value, line, note=""):
    return {"value": value, "source": f"{SRC}:{line}", "note": note}


# ---------------------------------------------------------------------------
# 1. Constants to move into data (values = what runs today)
# ---------------------------------------------------------------------------
engine_constants = OrderedDict()
engine_constants["posture"] = OrderedDict([
    ("guard_decay_rate_default", c(0.06, 208)),
    ("rear_heavy_to_front_heavy_leg_damage", c(4.0, 220, "battered leg stops the fighter loading the rear leg to check")),
    ("head_position_high_fatigue", c(5.0, 226)),
    ("head_position_high_head_damage", c(4.5, 226)),
    ("guard_integrity_min", c(0.25, 231)),
    ("guard_decay_body_weight", c(0.6, 232)),
    ("guard_decay_fatigue_weight", c(0.35, 232)),
    ("vision_feint_penalty", c(0.8, 238)),
    ("vision_per_head_damage", c(0.12, 239)),
])
engine_constants["readiness"] = OrderedDict([
    ("baseline", c(3.0, 328)),
    ("clinch_guard_weight", c(0.35, 332)),
    ("clinch_tie_weight", c(1.15, 333)),
    ("null_tie_lane_default", c(-0.6, 333)),
    ("underhook_bonus_per_hook", c(0.35, 335)),
    ("kick_range_head_seam_scale", c(0.15, 341, "hands_down style head penalties shrink at kick/outside range")),
    ("stance_weight", c(0.85, 345, "model_v2.readiness_weights.stance_weight duplicates this but is never read")),
    ("offensive_seam_scale", c(0.50, 356)),
    ("mentality_positive_scale", c(1.0, 357, "only mentality.defensive has positive lanes")),
    ("mentality_negative_scale", c(0.50, 357)),
    ("recovery_non_exposed_fraction", c(0.35, 396)),
    ("balance_compromised", c(-0.95, 400, "model_v2.state_modifiers has the same value but code uses the literal")),
    ("balance_off_base", c(-1.65, 402)),
    ("outside_angle_conceded", c(-1.10, 406, "flag is never set to True anywhere: dead branch until P4 lead-foot-outside sets it")),
    ("open_stance_lane_penalty", c(-0.35, 408, "applies to head_straight and body for whichever fighter defends")),
    ("feint_high_drawn_penalty", c(-1.10, 413, "focus_line is never set to high_drawn: dead branch")),
    ("feint_penalty", c(-0.55, 415)),
    ("novelty_penalty", c(-0.20, 422)),
    ("read_per_seen", c(0.16, 424)),
    ("read_per_consecutive", c(0.24, 424)),
    ("read_cap", c(0.85, 424)),
    ("fatigue_per_point", c(-0.10, 428)),
    ("body_damage_head_lanes_per_point", c(-0.14, 431)),
    ("head_damage_head_lanes_per_point", c(-0.10, 432)),
    ("leg_damage_leg_lane_per_point", c(-0.20, 434)),
    ("nonlane_readiness_default", c(3.0, 1376, "def_readiness.get(lane, 3.0): techniques whose lane is not one of the 8 lanes (space) roll against 3.0")),
])
engine_constants["kick_defense"] = OrderedDict([
    ("catch_clamp", c([0.10, 0.65], 598)),
    ("catch_readiness_factor", c(0.05, 598)),
    ("kick_path_min_roll", c(0.10, 1411, "kick defense path fires when roll > max(0.10, hit_prob - kick_def_bonus)")),
    ("kick_path_excluded", c(["knee_body"], 1411, "knee_body never takes the kick-defense path")),
])
engine_constants["damage"] = OrderedDict([
    ("crouch_hook_bonus", c(0.06, 800)),
    ("switch_after_step_bonus", c(0.08, 802, "dead: attacker 'setups' is never appended")),
    ("off_slot_penalty", c(-0.15, 826)),
    ("fatigue_wear_per_point", c(-0.012, 830)),
    ("leg_wear_kick_per_point", c(-0.03, 830)),
    ("leg_wear_other_per_point", c(-0.015, 830)),
    ("attacker_multiplier_clamp", c([0.75, 1.75], 834)),
    ("wall_landing_multiplier", c(1.12, 844)),
    ("guard_mitigation_intercept", c(1.14, 860)),
    ("guard_mitigation_per_coverage_point", c(0.06, 860)),
    ("block_absorb_blocked_landing", c(0.24, 864, "keyed to defense.block_absorb -> option data damage_rules")),
    ("block_absorb_head_guard_factor", c(0.90, 866, "keyed to defense.block_absorb -> option data damage_rules")),
    ("compounding_per_damage_point", c(0.045, 869)),
    ("defender_multiplier_min", c(0.60, 870)),
    ("check_recoil_fraction", c(0.65, 876)),
    ("landing_multipliers", c(dict(SIM.LANDING_QUALITY_MULT), 700, "duplicated in model_v2.landing_multipliers but the code table is what runs")),
    ("slot_depth_multipliers", c({str(k): v for k, v in SIM.SLOT_DEPTH_MULT.items()}, 693, "duplicated in model_v2.slot_depth_multipliers but the code table is what runs")),
    ("tie_damage_fraction", c(0.25, 1472, "techniques with damage_routing=control")),
    ("tie_fatigue_fraction", c(0.65, 1473)),
    ("submission_damage_fraction", c(0.30, 1476)),
    ("submission_fatigue_fraction", c(0.55, 1477)),
    ("stamina_drain_fatigue_fraction", c(0.55, 1481)),
])
engine_constants["simulation"] = OrderedDict([
    ("start_x_positions", c([-0.8, 0.8], 1126)),
    ("initiative_fatigue_drag", c(-0.08, 1201)),
    ("initiative_leg_drag", c(-0.10, 1202)),
    ("initiative_noise", c(0.85, 1203)),
    ("clinch_exit_probability", c(0.42, 1235, "attacker holding a grip whose slot home range is kick/punch leaves the clinch with this probability; automatic exit when the defender has no tie option")),
    ("entry_wall_distance_penalty", c(-0.65, 1265)),
    ("entry_leg_distance_penalty", c(-0.12, 1266)),
    ("entry_logistic_offset", c(0.35, 1268)),
    ("entry_probability_clamp", c([0.18, 0.82], 1268)),
    ("failed_entry_wall_drift_m", c(0.28, 1275)),
    ("pull_out_probability_outfighter", c(0.72, 1280, "keyed to mentality.outboxer OR defense.outfight -> option field pull_out_probability (max of the fighter's options, else the default)")),
    ("pull_out_probability_default", c(0.58, 1280)),
    ("pull_out_wall_penalty", c(-0.20, 1282)),
    ("feint_probability_cap", c(0.55, 1347)),
    ("base_attack_skill", c(3.30, 1379)),
    ("kick_range_punch_penalty", c(-0.55, 1388)),
    ("kick_range_shot_penalty", c(-0.75, 1388, "double_leg/single_leg; data form: techniques of kind takedown with required_range punch")),
    ("hit_probability_clamp", c([0.10, 0.85], 1391)),
    ("flush_band_fraction", c(0.28, 1425)),
    ("clean_band_fraction", c(0.76, 1427)),
    ("counter_min_recovery_frames", c(6, 1440)),
    ("counter_read_bonus_per_repeat", c(0.07, 1446)),
    ("counter_read_repeats_cap", c(3, 1446)),
    ("counter_recovery_bonus_per_frame_over_7", c(0.03, 1448)),
    ("counter_guard_resist_per_point", c(0.05, 1455)),
    ("counter_fatigue_penalty_per_point", c(0.03, 1458)),
    ("counter_probability_clamp", c([0.10, 0.55], 1457)),
    ("counter_hit_share", c(0.62, 1600)),
    ("recovery_penalty_default", c(0.4, 1510)),
    ("recovery_penalty_failed_multiplier", c(1.25, 1516)),
    ("recovery_penalty_landed_multiplier", c(0.60, 1516)),
    ("leg_compromise_threshold", c(4.5, 1525)),
    ("pressure_wall_drift_m", c(0.42, 1535)),
    ("outfighter_reset_factor", c(0.55, 1539)),
    ("tempo_gap_frames", c({"base": 36, "per_tempo_point": 4, "min": 6, "uses": "max(tempo_A, tempo_B)"}, 1543)),
    ("recovery_drag", c({"base": 1.45, "per_recovery_frame": 0.08, "failed_attack_extra": 0.65, "failed_outcomes": ["evaded", "blocked", "checked", "caught"]}, 1551)),
    ("caught_kick_sweep", c({"base": 0.62, "clamp": [0.18, 0.68], "fatigue_per_point": 0.04, "scramble_if_resistance_gte": 0.12}, 1561)),
    ("finish_thresholds", c({"head": 11.5, "body": 12.0, "leg": 12.5, "submission_stage": 3}, 1664, "duplicated in model_v2.regional_damage_limits but code literals run")),
    ("decision_weights", c({"head": 1.15, "body": 1.05, "leg": 1.0, "control_mark": 1.5}, 1688)),
])

# Constants whose value already lives in an existing data/model_v2.json key: read that key, never duplicate it.
ALIASES = {
    ("readiness", "baseline"): "readiness_weights.base_readiness",
    ("readiness", "stance_weight"): "readiness_weights.stance_weight",
    ("readiness", "balance_compromised"): "state_modifiers.compromised_balance_penalty",
    ("readiness", "balance_off_base"): "state_modifiers.off_base_balance_penalty",
    ("readiness", "outside_angle_conceded"): "state_modifiers.outside_angle_penalty",
    ("readiness", "open_stance_lane_penalty"): "state_modifiers.open_stance_rear_lane_penalty",
    ("readiness", "feint_high_drawn_penalty"): "state_modifiers.feint_attention_penalty",
    ("readiness", "novelty_penalty"): "state_modifiers.novel_move_surprise_penalty",
    ("readiness", "read_cap"): "state_modifiers.repeated_move_read_bonus",
    ("readiness", "fatigue_per_point"): "state_modifiers.fatigue_per_point_penalty",
    ("readiness", "body_damage_head_lanes_per_point"): "state_modifiers.body_damage_high_guard_drop",
    ("readiness", "head_damage_head_lanes_per_point"): "state_modifiers.head_damage_reaction_penalty",
    ("readiness", "leg_damage_leg_lane_per_point"): "state_modifiers.leg_damage_check_and_mobility_penalty",
    ("damage", "landing_multipliers"): "landing_multipliers",
    ("damage", "slot_depth_multipliers"): "slot_depth_multipliers",
}


def _get(path):
    node = model
    for part in path.split("."):
        node = node[part]
    return node


ALIAS_MISMATCHES = []
for (sec, name), path in ALIASES.items():
    entry = engine_constants[sec][name]
    entry["existing_key"] = path
    if _get(path) != entry["value"]:
        ALIAS_MISMATCHES.append({"constant": f"{sec}.{name}", "code": entry["value"], "data": _get(path), "existing_key": path})
fin = engine_constants["simulation"]["finish_thresholds"]
fin["existing_key"] = "regional_damage_limits (head/body/leg); submission_stage is new: simulation.finish_thresholds.submission_stage"
for reg in ("head", "body", "leg"):
    if model["regional_damage_limits"][reg] != fin["value"][reg]:
        ALIAS_MISMATCHES.append({"constant": f"finish_thresholds.{reg}", "code": fin["value"][reg], "data": model["regional_damage_limits"][reg]})
ARENA_MATCH = model["arena_presets"] == SIM.ARENA_PRESETS
assert ARENA_MATCH, "model arena_presets differs from code ARENA_PRESETS"
assert not ALIAS_MISMATCHES, ALIAS_MISMATCHES

# ---------------------------------------------------------------------------
# 2. Legacy tables and rules (P1a reproduces them exactly; later phases retire them)
# ---------------------------------------------------------------------------
GRAPPLE_ENTRY_IDS = ["double_leg", "single_leg", "outside_trip", "sanda_sweep", "body_lock", "collar_tie", "wall_tie", "guard_pull"]


def step(action, outcome, needs_trained=True, **when):
    d = {"action": action, "outcome": outcome, "needs_trained": needs_trained}
    if when:
        d["when"] = when
    return d


legacy = OrderedDict()
legacy["move_stats"] = {"source": f"{SRC}:38-75 (MOVE_BASE_STATS)", "table": SIM.MOVE_BASE_STATS,
                        "fallback": {"base": 1.0, "type": "impact", "setup_f": 4, "exec_f": 8, "hold_f": 2, "rec_f": 8, "lane": "head_straight"},
                        "note": "P1a reads this table verbatim (the field 'vertical' is never read). P1b switches to data/techniques_v2.json; expected diffs are listed in retire_in_p1b."}
legacy["retire_in_p1b"] = {
    "technique_data_differences": [
        {"technique": "step/retreat/pivot/switch_step/escape", "field": "damage_type label", "legacy": "movement", "data": "none", "effect": "label only (base damage 0)"},
        {"technique": "feint", "field": "damage_type label", "legacy": "feint", "data": "none", "effect": "label only (base damage 0)"},
        {"technique": "ride, armbar", "field": "attack_lane", "legacy": "clinch", "data": "ground", "effect": "readiness lane; reproduce with readiness.nonlane_lane_map ground->clinch"},
        {"technique": "escape", "field": "attack_lane", "legacy": "space", "data": "ground", "effect": "seed corrects data to space"},
        {"technique": "wall_tie", "field": "attack_lane", "legacy": "clinch", "data": "body", "effect": "seed corrects data to clinch (it is a grip)"},
        {"technique": "spinning_back_kick", "field": "vertical", "legacy": "athletic", "data": "grounded", "effect": "none today (never read); seed keeps grounded"},
    ],
}
legacy["kick_ids"] = {"value": sorted(SIM.KICK_IDS), "source": f"{SRC}:88-99",
                      "export_rule": "Keep the exported name KICK_IDS. P1a: exactly this set. From P5: every technique with kind kick or knee in data/techniques_v2.json (a superset; the CLI test only gets stricter)."}
legacy["kick_defense_rules"] = {
    "source": f"{SRC}:565-614 (select_kick_defense)",
    "semantics": "Evaluate rules in order; the first rule whose 'when' holds returns (action, outcome). A rule with 'roll' runs that roll only when rng is given; if the roll fails, continue with the next rule. When rng is None the 'no_rng' branch is used. No rule checks training (that is defect B5).",
    "rules": [
        {"id": "catch", "when": {"kick_in": ["body_kick", "low_kick", "switch_kick", "teep", "side_kick"], "any_of": [{"kicking": "kicking.sanda"}, {"defense": "defense.parry_catch"}]},
         "roll": {"p": "clamp(base_catch[kick] + kick_catch_bonus(kicking) + kick_catch_bonus(defense) + kick_retraction_delta(attacker kicking) + 0.05*(lane_readiness-3.0), 0.10, 0.65)",
                  "base_catch": {"body_kick": 0.44, "switch_kick": 0.44, "teep": 0.32, "side_kick": 0.32, "low_kick": 0.18}},
         "no_rng": {"kick_in": ["body_kick", "low_kick", "switch_kick"], "action": "kick_catch", "outcome": "caught", "else": "continue"},
         "action": "kick_catch", "outcome": "caught"},
        {"id": "check", "when": {"kick_in": ["low_kick", "body_kick", "switch_kick"], "defense": "defense.check_frame"}, "action": "check", "outcome": "checked"},
        {"id": "outfight_wall", "when": {"defense": "defense.outfight", "kick_in": ["low_kick", "body_kick", "head_kick", "spinning_back_kick", "teep", "side_kick"], "wall_near": True}, "action": "shell_block", "outcome": "blocked"},
        {"id": "outfight", "when": {"defense": "defense.outfight", "kick_in": ["low_kick", "body_kick", "head_kick", "spinning_back_kick", "teep", "side_kick"]}, "action": "evade_step_back", "outcome": "evaded"},
        {"id": "lean_back", "when": {"defense_in": ["defense.slip_roll", "defense.shoulder_roll"], "kick_in": ["head_kick", "axe_kick"]}, "action": "lean_back", "outcome": "evaded"},
        {"id": "jam", "when": {"defense_in": ["defense.smother", "defense.sprawl_pummel"], "kick_in": ["teep", "body_kick", "spinning_back_kick"]}, "action": "jam_step", "outcome": "jammed"},
        {"id": "absorb", "when": {"defense": "defense.block_absorb"}, "action": "retreat", "outcome": "blocked"},
        {"id": "default", "when": {}, "action": "shell_block", "outcome": "blocked"},
    ],
}
legacy["kick_defense_bonus_tiers"] = {
    "source": f"{SRC}:1404-1409",
    "tiers": [
        {"when_all": [{"kicking": "kicking.sanda"}, {"defense": "defense.parry_catch"}], "bonus": 0.24},
        {"when_any": [{"kicking": "kicking.sanda"}, {"defense": "defense.check_frame"}, {"defense": "defense.outfight", "wall_near": False}], "bonus": 0.16},
        {"default": True, "bonus": 0.08},
    ],
}
legacy["native_defense_rules"] = {
    "source": f"{SRC}:617-686 (select_native_defense)",
    "semantics": ("Defaults: missing defense option = defense.block_absorb, missing hands = hands.high_guard. Class 'grapple_entry' = incoming technique in grapple_entry_ids; everything else is 'strike'. "
                  "For the defender's option take its step list for the class and return the first step whose 'when' holds and (if needs_trained) whose action is in avail_def. "
                  "If no step returns and fallthrough is true, run the generic list. 'wall_near' means wall_proximity == 'near'."),
    "grapple_entry_ids": GRAPPLE_ENTRY_IDS,
    "grapple_entry": {
        "defense.sprawl_pummel": {"steps": [step("sprawl", "evaded", incoming_in=["double_leg", "single_leg"]), step("pummel", "blocked")], "fallthrough": True},
        "defense.smother": {"steps": [step("pummel", "jammed"), step("wall_tie", "jammed")], "fallthrough": True},
        "defense.outfight": {"steps": [step("shell_block", "blocked", wall_near=True), step("retreat", "blocked", False, wall_near=True),
                                       step("pivot", "evaded"), step("retreat", "evaded", False)], "fallthrough": False},
        "defense.check_frame": {"steps": [step("shield_frame", "blocked")], "fallthrough": True},
        "generic": {"steps": [step("sprawl", "evaded", incoming_in=["double_leg", "single_leg"]), step("pummel", "blocked"), step("retreat", "evaded", False)]},
    },
    "strike": {
        "defense.parry_catch": [step("parry", "evaded", incoming_in=["jab", "cross", "teep", "haymaker"]), step("shell_block", "blocked"), step("retreat", "blocked", False)],
        "defense.slip_roll": [step("slip", "evaded"), step("pivot", "evaded"), step("retreat", "evaded", False)],
        "defense.shoulder_roll": [step("slip", "evaded"), step("pivot", "evaded"), step("retreat", "evaded", False)],
        "defense.outfight": [step("shell_block", "blocked", wall_near=True), step("retreat", "blocked", False, wall_near=True),
                             step("pivot", "evaded", incoming_in=["jab", "cross"]), step("retreat", "evaded", False)],
        "defense.check_frame": [step("shield_frame", "blocked"), step("retreat", "evaded", False, hands="hands.long_guard"), step("shell_block", "blocked"), step("retreat", "blocked", False)],
        "defense.smother": [step("pummel", "jammed"), step("shield_frame", "blocked"), step("step", "jammed", False)],
        "defense.sprawl_pummel": [step("slip", "evaded", hands="hands.philly_shell"), step("shell_block", "blocked"), step("retreat", "blocked", False)],
        "defense.block_absorb": [step("shell_block", "blocked"), step("retreat", "blocked", False)],
    },
}
legacy["breakdown_rules"] = {
    "source": f"{SRC}:362-390",
    "semantics": "Per defense option, rules are checked in order and only the FIRST matching rule applies (only defense.outfight has two rules). A rule matches when any condition in when_any holds AND the lane is in 'lanes' ('all' = every lane).",
    "rules": {
        "defense.slip_roll": [{"when_any": {"fatigue_gte": 4.0, "head_damage_gte": 3.5, "vision_lt": 1.8}, "lanes": "all", "delta": -0.55}],
        "defense.parry_catch": [{"when_any": {"feinted": True}, "lanes": "all", "delta": -0.65}],
        "defense.block_absorb": [{"when_any": {"body_damage_gte": 3.5}, "lanes": "all", "delta": -0.55}],
        "defense.outfight": [{"when_any": {"wall_near": True}, "lanes": "all", "delta_from_model": "state_modifiers.wall_near_outfight_penalty", "delta_default": -1.25},
                             {"when_any": {"leg_damage_gte": 3.5}, "lanes": "all", "delta": -0.95}],
        "defense.shoulder_roll": [{"when_any": {"stance_relation": "open_stance"}, "lanes": ["head_hook"], "delta": -0.45}],
        "defense.check_frame": [{"when_any": {"weight_split": "front_heavy", "base_width": "single_leg", "leg_damage_gte": 4.0}, "lanes": ["leg", "single_support"], "delta": -0.85}],
        "defense.sprawl_pummel": [{"when_any": {"feinted": True, "fatigue_gte": 4.5}, "lanes": ["entry"], "delta": -0.65}],
        "defense.smother": [{"when_any": {"opponent_tie_in": ["tie.thai_plum", "tie.greco", "tie.judo_sambo", "tie.freestyle"]}, "lanes": ["clinch"], "delta": -0.45}],
    },
}
legacy["range_lane_bonuses"] = {
    "source": f"{SRC}:350-352, 438",
    "rules": {"hands.shield52": {"ranges": ["punch", "close", "clinch"], "lanes": "all", "delta": 0.45},
              "defense.outfight": {"ranges": ["kick", "outside"], "lanes": "all", "delta": 0.25, "unless": "wall_near"},
              "stance.bladed": {"ranges": ["kick", "outside"], "lanes": "all", "delta": 0.15}},
}
legacy["initiative"] = {
    "source": f"{SRC}:1188-1205",
    "formula": "initiative_base + initiative_per_point*(tempo-3) + mentality_term + (-last_recovery_drag if this fighter attacked last) + fatigue_drag*fatigue + leg_drag*leg_damage + U(-noise, +noise)",
    "mentality_term": {"mentality.counter": {"delta": -0.35, "only_when": "no exchange yet OR this fighter initiated the previous exchange"},
                       "mentality.swarmer": {"delta": 0.35}, "mentality.pressure": {"delta": 0.35}, "all_other_mentalities": {"delta": 0.0}},
    "tie_break": "max by (score, fighter_id): fighter-ID tie-break (continuous noise makes exact ties practically impossible); P9 replaces with a seeded coin",
}
legacy["counter_tendency_rule"] = {"source": f"{SRC}:1443-1445", "rule": "counter base = sum of attack_profile.counter_tendency over mentality, defense, hands, stance; defense.outfight's term counts only at kick range and not at the wall"}
legacy["damage_routing"] = {"source": f"{SRC}:1470-1486",
                            "control_ids": ["collar_tie", "cage_plum", "body_lock", "wall_tie", "pummel", "guard_pull", "ride"],
                            "rule": "control ids: damage x0.25 and fatigue +0.65 x damage; submissions: damage x0.30, fatigue +0.55 x damage; others: full damage, stamina_drain adds 0.55 x damage fatigue; target.liver_ribs adds 0.22 x damage fatigue on body damage",
                            "data_form": "technique.damage_routing (control | submission | strike) + target option on_body_damage_extra_fatigue_fraction"}
legacy["slot_plans"] = {
    "source": f"{SRC}:895-997 (build_slot_plans)",
    "explicit_sequence_rule": "explicit = [m for m in slot.sequence if m in card_available]; use it unless empty or (karate in slot caps and kicking.karate and len(explicit) <= 3)",
    "slot_moves": "active_techniques that are available, != 'escape', kind in (punch, kick, knee, takedown, grip, control, submission) and share a capability with the slot; karate+kicking.karate+mma appends side_kick, teep, body_kick, spinning_back_kick; if empty: available active techniques of kind punch/kick/takedown/grip",
    "fallback_orders": [
        {"when": {"caps_has": "sanda", "slot_moves_has": "sanda_sweep"}, "order": ["low_kick", "body_kick", "teep", "sanda_sweep", "side_kick"], "pool": "slot_moves"},
        {"when": {"caps_has_any": ["judo", "wrestling"]}, "order": ["body_lock", "outside_trip", "double_leg", "single_leg", "ride"], "pool": "slot_moves"},
        {"when": {"caps_has": "bjj"}, "order": ["collar_tie", "guard_pull", "armbar"], "pool": "slot_moves"},
        {"when": {"caps_has": "clinch"}, "order": ["collar_tie", "knee_body", "body_lock", "pummel"], "pool": "slot_moves"},
        {"when": {"caps_has": "kickboxing", "kicking": "kicking.dutch"}, "order": ["jab", "cross", "body_hook", "low_kick", "body_kick"], "pool": "slot_moves_or_available"},
        {"when": {"caps_has": "kickboxing", "kicking": "kicking.muay_thai"}, "order": ["teep", "body_kick", "low_kick", "knee_body"], "pool": "slot_moves_or_available"},
        {"when": {"caps_has": "kickboxing"}, "order": ["teep", "low_kick", "body_kick"], "pool": "slot_moves"},
        {"when": {"caps_has": "karate"}, "order": ["side_kick", "teep", "body_kick", "spinning_back_kick", "jab", "cross"], "pool": "slot_moves_or_available"},
        {"when": {"caps_has": "boxing", "target": "target.body_puncher"}, "order": ["jab", "body_hook", "cross", "uppercut", "hook"], "pool": "slot_moves"},
        {"when": {"caps_has": "boxing", "mentality": "mentality.counter"}, "order": ["jab", "cross", "uppercut", "hook", "body_hook"], "pool": "slot_moves"},
        {"when": {"caps_has": "boxing"}, "order": ["jab", "cross", "hook", "body_hook", "uppercut"], "pool": "slot_moves"},
        {"when": {}, "order": "slot_moves", "pool": "slot_moves"},
    ],
    "after_order": "sequence = dedupe(order + slot_moves) filtered to card_available; empty -> ['jab']",
    "home_range_default": {"clinch": ["bjj", "wrestling", "judo", "clinch"], "kick": ["kickboxing", "karate", "sanda"], "else": "punch"},
    "abandon_default": "max_consecutive_stalls = 999 if the card has one admitted slot else 2",
    "reorder": "plans sorted by (home_range != preferred_ranges[0], slot_index); then trigger := fight_start for the first, slot_stalled_or_countered for the rest; next_slot_id := next plan cyclically (card links are overwritten: defect B2)",
}
legacy["range_ladder"] = {
    "source": f"{SRC}:1226-1284",
    "rules": ["standing ladder = [kick, punch, clinch]; ground posture forces range ground; boxing forces punch",
              "attacker holding collar/body_lock/single_tie with slot home range kick or punch: defender tie null -> leave to punch automatically; else leave with clinch_exit_probability 0.42; otherwise stay clinch",
              "stepping in one band: entry = sum(entry_delta over mentality, stance, defense, hands, tie, kicking, target) + entry_per_point*(tempo-3); distance = sum(distance_control_delta over the defender's same 7 dims, excluding defense.outfight at the wall) - 0.65 at the wall - 0.12*leg damage; p = clamp(sigmoid(entry - distance + 0.35), 0.18, 0.82); failure drifts the defender 0.28 m toward the wall in walled arenas",
              "stepping out one band: p = 0.72 if mentality.outboxer or defense.outfight else 0.58, -0.20 when the attacker is at the wall"],
}
legacy["selection_rules"] = {
    "source": f"{SRC}:1286-1347",
    "rules": ["filtered = sequence without 'escape' and, once kick_checks_suffered >= 2, without low_kick and body_kick (falls back to the full sequence if empty)",
              "range match: technique reaches if the range is in its required_range (but never double_leg/single_leg at kick range), or at punch range if 'close' is in its required_range, or it is one of low_kick/body_kick/teep/switch_kick, or the attacker's tie is tie.greco/tie.judo_sambo and it is body_lock/outside_trip/collar_tie",
              "pick = range-matched list (else filtered) at slot_Cursor modulo length; the cursor advances every exchange",
              "ground: top with ride available -> ride; bottom with armbar -> armbar; else escape if available; else top strikes [cross, hook, body_hook, jab, haymaker] at the cursor; else retreat, then pummel, then jab",
              "kick range and the pick is not in KICK_IDS: pick from [side_kick, teep, low_kick, body_kick, jab] that are available, at the cursor",
              "recent moves window = 6; consecutive repeats feed read memory",
              "feint chance = min(0.55, sum of feint_setup_rate over mentality, stance, hands, target)"],
}
legacy["damage_rules"] = {
    "source": f"{SRC}:743-875 (compute_card_derived_damage)",
    "rules": ["base <= 0 -> zero-damage record",
              "region overrides: single_leg -> leg; body_kick with kicking.karate on an odd slot cursor -> head; regions other than head/body/leg -> head for head_kick/axe_kick/jumping_knee, else body",
              "stance.crouch +0.06 power on hook/body_hook/uppercut; stance.switch +0.08 when 'switch_step' is in setups (never true today)",
              "kicking power_delta applies to KICK_IDS when the lane is a kicking favored lane or the id is in [side_kick, spinning_back_kick, axe_kick, teep, low_kick, body_kick, head_kick, knee_body, jumping_knee]",
              "target power_delta applies when the lane is a target favored lane, or head_hunter+head, body_puncher/liver_ribs+body, leg_chopper+leg, knee_clincher+[knee_body, jumping_knee, collar_tie]",
              "hands power_delta always; tie power_delta when the lane is clinch/entry/single_support; counter_hit adds counter_power_delta of mentality, hands and defense",
              "slot delta = depth multiplier - 1 in the active slot, else -0.15; wear = -0.012*fatigue - (0.03 if kick else 0.015)*leg damage; attacker clamp [0.75, 1.75]",
              "landing x1.12 at the wall; guard = 1.14 - 0.06*coverage (defender hands mma_adaptation ratings: head_coverage/body_coverage/takedown_readiness); block_absorb: blocked landing 0.24, head guard x0.90; defender = max(0.60, guard*(1 + 0.045*region damage))",
              "checked low_kick/body_kick/switch_kick recoil = base*0.65*attacker multiplier onto the kicker's leg"],
    "data_forms": "stance.crouch power_bonus_for {techniques, delta}; stance.switch power_bonus_after_setup; target options target_power_match {regions, techniques}; technique field check_recoil; model.damage.tie_power_lanes",
}
legacy["caught_kick"] = {"source": f"{SRC}:1553-1585",
                         "rule": "on 'caught': kicker kick_checks_suffered += 1; sweep p = clamp(0.62 - (tie + stance sweep_resistance) - 0.04*holder fatigue, 0.18, 0.68); dump technique = sanda_sweep if available else outside_trip else cross (clean); resistance >= 0.12 -> over_under clinch, else ground with holder half_guard_top / kicker closed_guard_bottom"}
legacy["counter_candidates"] = {"source": f"{SRC}:1590-1600",
                                "rule": "first available of: kick range [side_kick, teep, low_kick, body_kick, cross, jab]; clinch [knee_body, uppercut, body_hook, outside_trip, hook]; otherwise [cross, uppercut, hook, body_hook, jab, haymaker]; quality counter_hit with p 0.62 else partial"}
legacy["posture_rules"] = {"source": f"{SRC}:215-222", "rule": "ground -> height grounded, base mat; recovery window single_leg_recovery -> base single_leg; leg damage >= 4.0 with rear_heavy -> front_heavy"}
legacy["inventory"] = "reference/literal_inventory.json lists every remaining option-id and technique-id literal by line and function (93 option literals on 76 lines; 364 technique literals on 186 lines incl. the MOVE_BASE_STATS/KICK_IDS tables)"
legacy["decision"] = {"source": f"{SRC}:1683-1690", "score": "1.15*opp_head + 1.05*opp_body + 1.0*opp_leg + 1.5*control_marks", "tie_break": "max by (score, fighter_id): fighter-ID tie-break (defect D7)"}

# ---------------------------------------------------------------------------
# 3. New sections (starting defaults; tuned by audits)
# ---------------------------------------------------------------------------
new_sections = OrderedDict()
new_sections["readiness"] = {
    "nonlane_lane_map": {"ground": "clinch", "space": None, "note": "None = use nonlane_readiness_default (3.0). Reproduces legacy lanes for ride/armbar once technique data is read (P1b)."},
}
new_sections["laterality"] = {
    "reference": "natural_stance",
    "natural_definition": "A fighter is NATURAL when the dominant hand and dominant leg are on the REAR side of their current stance (orthodox: right; southpaw: left). Natural fighters get ZERO dominance deltas, so every card without a laterality block (and every D3 default) behaves exactly as today.",
    "missing_block": {"dominant_hand": "rear side of the card orientation (switching -> orthodox, i.e. right)", "dominant_leg": "same as hand", "opposite_stance_experience": "normal"},
    "hand_deltas": {
        "cross_dominant": {"lead_power": 0.08, "lead_accuracy": 0.04, "rear_power": -0.06, "rear_accuracy": -0.02},
        "ambidextrous": {"lead_power": 0.04, "lead_accuracy": 0.02, "rear_power": -0.02, "rear_accuracy": 0.0},
    },
    "leg_deltas": {
        "cross_dominant": {"lead_power": 0.08, "lead_accuracy": 0.03, "rear_power": -0.06, "rear_accuracy": -0.02},
        "both": {"lead_power": 0.04, "lead_accuracy": 0.02, "rear_power": -0.02, "rear_accuracy": 0.0},
    },
    "switch_trained_rear_penalty_scale": 0.5,
    "switching_rule": "When a fighter changes stance mid-fight (switch_step, stance.switch, forced switch from leg damage) the rear side changes, so a natural fighter becomes cross-dominant until they switch back.",
    "power_applies_to": "attacker additive sum (damage) for punches/elbows by hand side and kicks/knees by leg side; techniques with side 'both' or 'none' get 0",
    "line_accuracy_modifiers": {
        "closed_stance": {"lead_straight": 0.08, "lead_round": 0.05, "rear_straight": -0.04, "rear_round_kick": -0.02, "lead_linear_kick": 0.03},
        "open_stance": {"rear_straight": 0.08, "lead_straight": -0.05, "rear_round_kick": 0.06, "lead_round": 0.03, "rear_round": 0.02},
    },
    "lead_foot_outside": {"applies_in": "open_stance", "ranges": ["kick", "punch"], "contest_slope": 1.0,
                          "winner_rear_power_line_accuracy_bonus": 0.06, "loser_sets_outside_angle_conceded": True,
                          "loser_penalty_from": "engine_constants.readiness.outside_angle_conceded (-1.10)",
                          "rear_power_lines": ["rear_straight", "rear_round", "rear_round_kick", "overhand"]},
    "familiarity": {"exposure_default": {"orthodox_facing_southpaw": 0.25, "southpaw_facing_orthodox": 0.85, "same_stance": 1.0},
                    "card_override": {"low": 0.15, "normal": None, "high": 0.9},
                    "read_gain_at_zero_exposure": 0.80, "novelty_penalty_multiplier_at_zero_exposure": 1.5,
                    "formula": "read_gain *= lerp(read_gain_at_zero_exposure, 1.0, exposure); novelty_penalty *= lerp(novelty_penalty_multiplier_at_zero_exposure, 1.0, exposure)"},
    "body_sides": {"liver_side": "right", "liver_stamina_multiplier": 1.25, "spleen_stamina_multiplier": 1.05},
    "limb_effects": {"leg_compromise_per_leg": 4.5, "arm_damage_power_penalty_per_point": 0.03, "arm_damage_power_penalty_cap": 0.15,
                     "lead_leg_damage_kick_power_penalty_per_point": 0.03},
    "cuts": {"vision_penalty_per_cut_level_same_side": 0.40, "max_cut_level": 3, "doctor_stoppage_enabled": False, "doctor_check_cut_level": 3, "doctor_stoppage_probability": 0.25},
    "state_fields": "Store side damage in a NEW actor field damage_by_side {head_left, head_right, body_left, body_right, leg_left, leg_right, arm_left, arm_right}; keep actor.damage {head, body, leg} as the totals (fight_state_v2 closes that object).",
    "grappling_side_preference": {"enabled": False, "note": "Research links grappling side preference to footedness; leave off until P6 is stable."},
}
new_sections["grappling"] = {
    "contest_slope": 0.9, "probability_clamp": [0.08, 0.80],
    "profile_scale_note": "grappling_profile values are 0-5 like engine_index ratings; contest uses (actor_skill - opponent_skill + modifiers)",
    "null_tie_profile": dict(takedown_offense=0.0, takedown_defense=1.5, clinch_control=1.0, top_control=1.0, bottom_game=0.5,
                             submission_offense=0.0, submission_defense=1.0, scramble=1.5, stand_up=1.5),
    "null_tie_note": "Used when a card's tie dimension is null. tie.null is NOT an option (option_behaviors.json must keep exactly 57 options).",
    "fatigue_penalty_per_point": 0.08, "position_advantage_bonus": {"top": 0.30, "dominant_clinch": 0.25, "back_controller": 0.40},
    "grip_bonus": {"underhook": 0.25, "double_underhooks": 0.45, "wrist_control": 0.30, "head_inside": 0.30, "caught_leg": 0.60},
    "wall_bonus": {"pinner_takedown": 0.40, "pinned_wall_walk": 0.30},
    "setup_bonus": {"feint": 0.25, "strike_landed_previous_exchange": 0.20, "level_change": 0.15},
    "scramble_margin": 0.15,
    "scramble_rule": "If |roll - p| < scramble_margin on a takedown or stand-up contest, the pair goes to the transition's via_outcome target (scramble or turtle) instead of success/failure.",
    "submission": {"stages": 3, "escape_base_per_stage": [0.55, 0.40, 0.25], "fatigue_escape_penalty_per_point": 0.04, "damage_per_stage_fraction": 0.30,
                   "reset_on_escape": True, "on_escape": "apply the transition row with contest 'submission' from the current position (failed attempt), else stay"},
    "control_value_source": "positions.control_value_per_second",
    "ground_strike_accuracy_base": 3.1,
    "untrained_stand_up_base": 0.20,
}
new_sections["vertical"] = {
    "modes": {"grounded": ["grounded"], "athletic": ["grounded", "athletic"], "aerial": ["grounded", "athletic", "aerial"]},
    "aliases": {"wall_assisted": "aerial"},
    "gating": "a technique with vertical_min V is usable only if V is in modes[fight vertical_mode] AND V is in card.airborne_training.allowed_vertical_modes AND (technique.requires_airborne_training is false OR the id is in card.airborne_training.techniques)",
    "landing_counter_bonus": 0.10, "airborne_miss_exposure_multiplier": 1.2,
}
new_sections["knockdowns"] = {
    "flash_knockdown": {"requires_damage_type": ["impact"], "requires_region": ["head"], "results": ["clean", "flush", "counter_hit"],
                        "chance": {"threshold_head_damage": 4.0, "per_point_over": 0.04, "flush_bonus": 0.08, "counter_hit_bonus": 0.06, "cap": 0.45}},
    "stun": {"exchanges": 2, "readiness_penalty": -0.8},
    "standing_count": {"rulesets": ["boxing", "kickboxing", "muay_thai"], "recover_base": 0.80, "recover_per_head_damage": -0.05, "three_knockdown_rule": True},
    "mma_follow_up": {"ground_strike_bonus_after_knockdown": 0.15},
    "event_fields": "Record knockdowns in new exchange fields (knockdown, standing_count); the outcome enum of exchange_event_v2 is closed.",
}
new_sections["rounds"] = {"rest_fatigue_recovery_fraction": 0.35, "rest_damage_recovery_fraction": 0.0, "clear_stun_and_feint": True,
                          "reset_range_to": "kick", "reset_position_to": "standing_neutral", "reset_slot_to_start": False}
new_sections["energy"] = {"use_technique_energy_mult": True, "attacker_cost": "fatigue_by_tempo[tempo] * technique.energy_mult",
                          "defender_cost_fraction": 0.35, "accuracy_per_fatigue_point": 0.0,
                          "note": "Average energy_mult over a typical exchange mix is ~1.0 so tempo calibration roughly holds. accuracy_per_fatigue_point stays 0.0 (fatigue already lowers readiness and damage) until an audit asks for it."}
new_sections["selection"] = {
    "temperature": 0.6,
    "weights": {"seq_next": 1.0, "seq_other": 0.35, "target_pref": 0.6, "range_fit": 0.8, "open_seam": 0.9, "debt_exploit": 0.5,
                "repeats": -0.6, "combo_follow_up": 0.7, "signature": 0.3, "momentum": 0.2, "goal_alignment": 0.5},
    "features": {
        "seq_next": "1 if the technique is the slot sequence item at the slot pointer, else 0. The pointer starts at 0 on every slot entry and advances by one each time the slot throws its pointed item (any result); it wraps.",
        "seq_other": "1 if the technique is elsewhere in the active slot's sequence, else 0",
        "target_pref": "1 if technique.attack_lane is in the favored_lanes of the card's target option (or of its kicking option, for kicks and knees), else 0",
        "range_fit": "1.0 if the current range equals technique.required_range[0]; 0.6 if it is another listed range",
        "open_seam": "1 if the defender's readiness on technique.attack_lane (this exchange's profile) is below open_seam_readiness_below, else 0",
        "debt_exploit": "1 if the technique is in the effective technique_ids (base + v2 overlay) of a debt of the opponent (opponent options' exploitable_debt_ids + card exploitable_seams) whose ruleset includes this ruleset and whose required_range is within one band of the current range",
        "repeats": "how many of this fighter's last 3 attacks used this technique (0-3)",
        "combo_follow_up": "1 if (previous own technique, this technique) are consecutive in a combination chain whose school is one of the active slot's capabilities and whose trigger_on matches the previous exchange's result",
        "signature": "1 if the technique is in card.signature_moves",
        "momentum": "fight_momentum * commit(t), where commit(t) = min(1, recovery_exposure.readiness_penalty / 0.8)",
        "goal_alignment": "1 if the technique satisfies goal_predicates[slot.goal], else 0",
    },
    "goal_predicates": {
        "head_damage": "region_family == head",
        "body_attrition": "region_family == body",
        "leg_attrition": "region_family == leg",
        "counter_trap": "usage in (counter, both) OR kind == feint OR 'recovery' in exploits_openings",
        "clinch_control": "kind in (grip, knee, elbow) and 'clinch' in required_range",
        "takedown_top_control": "kind in (takedown, sweep, control, ground_strike)",
        "submission_finish": "kind == submission OR id == guard_pull OR result_position in (closed_guard, back_control, mount)",
        "wall_pressure": "'wall' in exploits_openings OR id == cut_off_step",
        "reset_to_home_range": "kind in (movement, escape)",
        "position": "kind in (grip, control) OR result_position is not null",
    },
    "open_seam_readiness_below": 2.6,
    "candidate_pool": "active slot pool (slot grants via core + active_techniques, plus basic_movement core) INTERSECT legal in ruleset INTERSECT vertical gating INTERSECT reachable now (range, position role, grips, wall), usage in (attack, both, movement); counter-only techniques excluded",
    "empty_pool_policy": ["standing and current range != slot home_range: choose step (to close) or retreat (to open) toward home range",
                          "in a clinch or ground position: choose the first trained escape for the actor's role (clinch_break, stand_up, technical_standup, hip_escape)",
                          "otherwise: step (basic_movement core, always trained)"],
    "sampling": "p_i = softmax(score_i / temperature); one rng.random() draw per choice; candidates sorted by technique id before sampling so order never depends on dict iteration",
    "counter_choice": "same scorer over trained techniques with usage in (counter, both, attack) that reach at the current range; counter-only techniques are eligible only here",
}
new_sections["slot_triggers"] = {
    "evaluation": "At the start of each exchange, before selection. Triggers are evaluated from state and the previous exchange record.",
    "thresholds": {"commit_penalty_min": 0.45, "hurt_head_damage": 6.0, "late_fight_fraction": 0.70, "behind_margin": 1.0, "min_exchanges_before_preempt": 2},
    "predicates": {
        "fight_start": "the slot active at exchange 1 (exactly one slot per card should carry it; if none, the first slot)",
        "slot_stalled": "the active slot's abandon rule fired this exchange",
        "slot_stalled_or_countered": "same as slot_stalled (being countered already counts as a stall)",
        "slot_stalled_or_close_range": "slot_stalled OR range in (close, clinch)",
        "opponent_kicks": "the opponent's last attack (within the last 2 exchanges) was a kick or knee",
        "opponent_commits": "the opponent's last attack had recovery_exposure.readiness_penalty >= commit_penalty_min",
        "opponent_enters": "the opponent closed the range by one band in the previous exchange",
        "opponent_circles_out": "the opponent used pivot or retreat in 2 of their last 3 actions",
        "opponent_clinches_or_shoots": "the opponent attempted a grip, takedown or sweep in the previous exchange, or the pair position is a clinch/transition position where the opponent holds the dominant role",
        "opponent_on_wall": "opponent wall_proximity == near",
        "self_on_wall": "own wall_proximity == near",
        "close_range_reached": "range in (close, clinch)",
        "self_hurt": "own head damage >= hurt_head_damage OR stunned OR knocked down this round",
        "opponent_hurt": "opponent head damage >= hurt_head_damage OR stunned",
        "clinch_entered": "pair position domain == clinch",
        "ground_entered": "pair position domain == ground",
        "late_fight": "elapsed time >= late_fight_fraction of the scheduled fight",
        "behind_on_score": "own running decision score < opponent's by >= behind_margin",
    },
    "stall_conditions": {
        "sequence_denied_or_countered": "an own attack from this slot ends miss/evaded/blocked/checked/caught/jammed, or the fighter is counter-hit; the count resets when an own attack lands partial or better",
        "kicks_blocked_or_jammed": "an own kick or knee ends blocked/checked/caught/jammed",
        "clinch_denied_or_escaped": "an own grip/takedown attempt fails or the opponent escapes a clinch position",
        "pocket_stalled": "two consecutive exchanges at punch or close range without an own landed attack",
        "default": "sequence_denied_or_countered",
    },
    "switching": ["If the abandon rule fired: go to the first slot in links whose trigger holds; if none holds, the first slot in links; if links is empty, the next slot by index (wrapping).",
                  "Otherwise a linked slot whose trigger is reactive (any trigger except fight_start and slot_stalled*) and holds pre-empts, but only after the active slot has run min_exchanges_before_preempt exchanges.",
                  "A slot with goal reset_to_home_range: while it is active, defenses granted by its capabilities move to the front of every applicable defense list; when the pair is back at standing_neutral and at the card's preferred_ranges[0], follow its links."],
    "record": "exchange.slot_switched_to and new field slot_switch_reason",
}
new_sections["pace"] = {"gap_uses": "initiating fighter's tempo and mentality patience", "base_gap_frames": 36, "per_tempo_point": 4, "min_gap_frames": 6, "fatigue_gap_scale": 0.03}
new_sections["fight_momentum"] = {"state_field": "actor.fight_momentum (scalar). Do NOT reuse actor.momentum: fight_state_v2 defines it as a 2-number vector.",
                                  "per_clean_or_flush_landed": 0.15, "per_clean_or_flush_taken": -0.15, "per_knockdown": 0.4, "decay_per_exchange": 0.2,
                                  "clamp": [-0.6, 0.6], "initiative_weight": 0.5, "accuracy_weight": 0.05}
new_sections["defense_contest"] = {
    "slope": 1.0, "probability_clamp": [0.15, 0.85],
    "formula": "after the hit roll fails: p = clamp(sigmoid(slope * (readiness[lane] - offense + defense_fit)), lo, hi); success -> the defense technique's result for this class; failure -> failure_result",
    "defense_fit": {"designed_for": 0.4, "general": 0.0, "poor_for": -0.4},
    "failure_result": "blocked",
    "kick_catch": "kick_catch uses the catch roll (technique.catchability) instead of this contest; a failed catch is 'blocked'",
    "ground_strike_defense": {"technique": None, "success_result": "blocked", "note": "ground strikes are defended by the position (no technique pick)"},
    "selection": "Build the ordered list: kicking option kick_defense_prepend[class] + hands option defense_prepend[class] + defense option native_defense.by_class[class] (or at_wall[class] when wall_near and present). Remove duplicates, keep trained techniques, take the first; if none, retreat. With rng=None the legacy entry points return this first pick and its success result (no roll).",
    "incoming_class_rules": [
        "kind in (movement, feint, defense, control, escape) -> none (no defense step), unless technique.incoming_class overrides",
        "kind == submission -> submission (staged escape rolls, no defense pick)",
        "kind == ground_strike -> ground_strike",
        "kind in (takedown, sweep) -> takedown",
        "kind == grip -> clinch_entry",
        "kind == elbow -> elbow",
        "kind == knee -> knee",
        "kind == kick: lane in (leg, single_support) -> kick_low; lane starts with head -> kick_high; line in (lead_linear_kick, rear_linear_kick) -> kick_linear; else kick_body",
        "kind == punch: lane == body -> body_punch; line in (lead_uppercut, rear_uppercut) -> uppercut; line in (lead_round, rear_round, overhand, spinning) -> hook; else straight",
    ],
    "kick_defense_window": {"base": 0.08, "clamp": [0.08, 0.24],
                            "rule": "kicks and knees except knee_body take the kick-defense path when roll > max(0.10, p_land - window); window = base + sum of option kick_defense_window_delta (additive, replaces legacy tiers in P5)"},
}
new_sections["geometry"] = {
    "distances_m": {"clinch": 0.45, "close": 0.70, "punch": 1.05, "kick": 1.65, "outside": 2.40},
    "band_from_distance": "nearest band by distance; ground positions override to range 'ground'",
    "moves_m": {"step": 0.35, "retreat": 0.40, "cut_off_step": 0.25, "shove": 0.60, "pivot_angle_deg": 35},
    "pivot_rule": "rotate the opponent around the pivoting fighter by pivot_angle_deg * arena.lateral_freedom",
    "wall_rule": "wall_proximity = near when distance to the closest wall < arena.wall_near_m; in_corner when two walls are within wall_near_m",
    "arenas": {
        "ring": {"shape": "square", "half_width_m": 3.0, "walls": "ropes", "corners": True},
        "cage": {"shape": "octagon", "radius_m": 3.5, "walls": "fence", "corners": False},
        "open_floor": {"shape": "open", "radius_m": 50.0, "walls": None, "corners": False},
        "narrow_alley": {"shape": "corridor", "half_width_m": 1.6, "half_length_m": 15.0, "walls": "both long sides", "corners": False},
        "rooftop_edge": {"shape": "platform", "half_width_m": 2.8, "walls": None, "edge": "drop"},
        "dojo": {"shape": "square", "half_width_m": 4.0, "walls": "walls", "corners": True},
    },
    "edge_fall": {"arenas": ["rooftop_edge"], "trigger": "a fighter ends an exchange beyond the edge", "probability": 0.35, "off_base_multiplier": 1.5,
                  "on_fall": "fight ends, method 'Fall (ring-out)'; otherwise the fighter is pulled back to the edge with balance off_base"},
    "preset_fields": "Keep every existing arena_presets field in data/model_v2.json and keep exporting ARENA_PRESETS (the test checks its six keys). New fields are additive.",
}
new_sections["finishes"] = {
    "tiebreak": "No draws (the CLI test requires a winner). If decision scores are equal within 1e-9, draw one rng.random() in canonical order: < 0.5 -> first canonical fighter wins. Record result.decision_tiebreak = true.",
    "decision": "per round with ruleset decision_weights (clean_strikes, damage, control, aggression); fight winner = more rounds won, then total score, then the tiebreak above",
}
new_sections["director"] = {"selection": "medoid_of_winning_runs", "implausible_below_win_rate": 0.05, "upset_below_win_rate": 0.20,
                            "feature_vector": ["method", "finish_time_s", "damage_head", "damage_body", "damage_leg", "control_time_s", "slot_path"],
                            "no_win": "If the requested winner wins none of the runs, return no fight and say so (never return a losing run)."}
new_sections["audits"] = {"seeds_per_pair": 200, "overall_band": [0.35, 0.65], "pair_max": 0.85, "anti_flatten_min_std": 0.04,
                          "style_sanity_min": 0.60, "option_dominant_delta": 0.12, "option_useless_abs_delta": 0.01,
                          "diversity_min_distinct_openings_of_60": {"brawler": 12, "default": 25},
                          "mirror": {"tolerance": 0.0, "also_mirror": ["laterality.body_sides.liver_side"]},
                          "southpaw_only_edge_range": [0.0, 0.05]}

new_sections["mastery"] = {
    "decision": "D23; mechanics in handoff 7.18; calibrated by RANK_MASTERY_STRESS_TEST.md (562,880 fights on 0d0734d)",
    "levels": {"novice": -1, "trained": 0, "expert": 1, "master": 2, "grandmaster": 3},
    "default_rank": "trained",
    "contest_logit_per_level": 0.20,
    "damage_dealt_log_per_level": 0.04,
    "damage_taken_log_per_level": 0.04,
    "seam_shrink_by_level": {"-1": -0.25, "0": 0.0, "1": 0.10, "2": 0.25, "3": 0.40},
    "bands": {"hit": [0.05, 0.95], "counter": [0.05, 0.75], "kick_catch": [0.05, 0.85], "catch_sweep": [0.05, 0.90], "feint": [0.01, 0.80], "default": [0.05, 0.95]},
    "contests": ["hit", "defense_contest", "counter", "kick_catch", "check", "catch_sweep", "range_step_in", "range_step_out", "clinch_break", "feint",
                 "grappling_transition", "scramble", "submission_stage_escape", "stand_up"],
    "not_affected": ["initiative_noise", "counter_quality", "effect_chance", "knockdown_chance", "director_selection"],
    "effective_level": "slot level = mean level of the slot's capabilities except basic_movement (none left -> card rank); attacker: the slot it attacks from; defender: the slot it last attacked from (start: fight_start slot)",
    "school_mastery_rule": "rank is a ceiling: no school above the card's rank; unlisted schools sit at the card's rank",
    "calibration_targets": {"plus1": [0.65, 0.70], "plus2": [0.78, 0.87], "plus3": [0.87, 0.95]},
    "calibrated_on": "0d0734d; holdout seeds: +1 68.1% (same style) / 65.9% (different styles), +2 83.6% / 78.8%, +3 92.4% / 88.8%. Re-calibrate at P13 (handoff 10.16).",
}

model_complete = OrderedDict()
model_complete["existing_model_v2_keys_preserved"] = model
model_complete["engine_constants_to_move_into_data"] = engine_constants
model_complete["legacy"] = legacy
model_complete["new_sections"] = new_sections
(OUT / "model_v2_complete_seed.json").write_text(json.dumps(model_complete, indent=1) + "\n")

# ---------------------------------------------------------------------------
# 4. Option behaviour additions (data that replaces option-ID branches in code)
# ---------------------------------------------------------------------------
add = OrderedDict()


def put(oid, key, value):
    assert oid in OPTION_IDS, oid
    add.setdefault(oid, OrderedDict())[key] = value


GRAPPLING = {
    "tie.thai_plum": dict(takedown_offense=1.5, takedown_defense=2.5, clinch_control=4.5, top_control=1.5, bottom_game=1.0, submission_offense=0.5, submission_defense=1.5, scramble=2.5, stand_up=2.5),
    "tie.greco": dict(takedown_offense=3.5, takedown_defense=4.0, clinch_control=4.5, top_control=3.5, bottom_game=1.5, submission_offense=1.0, submission_defense=2.5, scramble=3.0, stand_up=3.0),
    "tie.folk_ride": dict(takedown_offense=3.5, takedown_defense=3.0, clinch_control=2.5, top_control=4.5, bottom_game=2.0, submission_offense=1.5, submission_defense=2.5, scramble=3.5, stand_up=3.5),
    "tie.freestyle": dict(takedown_offense=4.5, takedown_defense=3.5, clinch_control=2.5, top_control=3.5, bottom_game=2.0, submission_offense=1.0, submission_defense=2.5, scramble=4.0, stand_up=3.5),
    "tie.judo_sambo": dict(takedown_offense=4.0, takedown_defense=3.5, clinch_control=3.5, top_control=3.0, bottom_game=2.0, submission_offense=2.5, submission_defense=3.0, scramble=3.0, stand_up=3.0),
    "tie.bjj": dict(takedown_offense=1.5, takedown_defense=2.0, clinch_control=2.5, top_control=3.5, bottom_game=4.5, submission_offense=4.5, submission_defense=4.5, scramble=3.0, stand_up=2.0),
    "tie.wall_boxing": dict(takedown_offense=1.5, takedown_defense=2.5, clinch_control=3.5, top_control=1.5, bottom_game=1.0, submission_offense=0.5, submission_defense=1.5, scramble=2.0, stand_up=2.5),
    "tie.anti_grappling": dict(takedown_offense=1.0, takedown_defense=4.5, clinch_control=2.5, top_control=1.5, bottom_game=1.5, submission_offense=0.5, submission_defense=3.0, scramble=3.5, stand_up=4.5),
}
for k, v in GRAPPLING.items():
    put(k, "grappling_profile", v)
GRAPPLING_MODS = {
    "defense.sprawl_pummel": dict(takedown_defense=1.0, scramble=0.25),
    "defense.smother": dict(clinch_control=0.5),
    "defense.outfight": dict(takedown_defense=0.5),
    "stance.crouch": dict(takedown_defense=0.25),
    "stance.upright": dict(takedown_defense=-0.5, clinch_control=0.5),
    "stance.balanced": dict(takedown_defense=0.25, takedown_offense=0.25),
    "stance.planted": dict(takedown_defense=0.25, scramble=-0.25),
    "stance.shuffle": dict(takedown_defense=-0.25, scramble=0.25),
    "stance.bladed": dict(takedown_defense=-0.25),
    "stance.switch": dict(takedown_defense=-0.25),
    "mentality.pressure": dict(takedown_offense=0.25),
    "mentality.swarmer": dict(clinch_control=0.25),
    "mentality.spoiler": dict(clinch_control=0.25),
    "mentality.defensive": dict(takedown_defense=0.25, submission_defense=0.25),
}
GRAPPLING_MOD_CONDITIONS = {"defense.outfight": {"unless": "wall_near"}}
for k, v in GRAPPLING_MODS.items():
    put(k, "grappling_modifiers", v)
    if k in GRAPPLING_MOD_CONDITIONS:
        put(k, "grappling_modifiers_condition", GRAPPLING_MOD_CONDITIONS[k])
LFO = {"stance.switch": 0.20, "stance.shuffle": 0.15, "stance.bladed": 0.10, "stance.balanced": 0.05, "stance.planted": -0.10,
       "stance.upright": -0.05, "mentality.technician": 0.15, "mentality.outboxer": 0.10,
       "mentality.slickster": 0.10, "mentality.switch_hitter": 0.10, "mentality.pressure": 0.05, "mentality.counter": 0.05}
for k, v in LFO.items():
    put(k, "lead_foot_outside_delta", v)
# Selection profiles: initiative values reproduce the legacy code exactly (counter -0.35 when waiting; swarmer/pressure +0.35; all others 0)
SELECTION = {
    "mentality.counter": dict(initiative_delta=0.0, initiative_delta_when_waiting=-0.35, switch_after_stalls=2, patience=1.25, risk=0.8, combo_length=1.5),
    "mentality.swarmer": dict(initiative_delta=0.35, switch_after_stalls=3, patience=0.80, risk=1.1, combo_length=3.0),
    "mentality.pressure": dict(initiative_delta=0.35, switch_after_stalls=3, patience=0.85, risk=1.05, combo_length=2.5),
    "mentality.slugger": dict(initiative_delta=0.0, switch_after_stalls=4, patience=1.0, risk=1.3, combo_length=1.5),
    "mentality.outboxer": dict(initiative_delta=0.0, switch_after_stalls=2, patience=1.15, risk=0.85, combo_length=2.0),
    "mentality.boxer_puncher": dict(initiative_delta=0.0, switch_after_stalls=2, patience=1.0, risk=1.0, combo_length=2.5),
    "mentality.technician": dict(initiative_delta=0.0, switch_after_stalls=1, patience=1.10, risk=0.85, combo_length=2.0),
    "mentality.defensive": dict(initiative_delta=0.0, switch_after_stalls=2, patience=1.30, risk=0.7, combo_length=1.5),
    "mentality.spoiler": dict(initiative_delta=0.0, switch_after_stalls=2, patience=1.05, risk=0.9, combo_length=1.5),
    "mentality.slickster": dict(initiative_delta=0.0, switch_after_stalls=2, patience=1.10, risk=0.85, combo_length=2.0),
    "mentality.showman": dict(initiative_delta=0.0, switch_after_stalls=3, patience=0.95, risk=1.2, combo_length=2.0),
    "mentality.switch_hitter": dict(initiative_delta=0.0, switch_after_stalls=1, patience=1.0, risk=1.0, combo_length=2.5),
}
SELECTION_NOTE = ("initiative_delta_when_waiting applies when no exchange has happened yet or this fighter initiated the previous exchange. "
                  "switch_after_stalls is only a default for slots without abandon_rule.max_consecutive_stalls. patience multiplies the reset gap (P7). "
                  "risk scales the momentum feature and the commit penalty in selection (P3). combo_length caps chained follow-ups (P3).")
for k, v in SELECTION.items():
    put(k, "selection_profile", v)


def S(*ids):
    return list(ids)


R_BLOCKED = {"technique": "retreat", "result": "blocked"}
NATIVE = {
    "defense.slip_roll": {
        "straight": S("slip", "bob_weave", "pivot", "retreat"), "hook": S("bob_weave", "shell_block", "pivot", "retreat"),
        "uppercut": S("lean_back", "shell_block", "retreat"), "body_punch": S("shell_block", "retreat"),
        "elbow": S("shell_block", "retreat"), "knee": S("shell_block", "retreat"),
        "kick_low": S("check", "evade_step_back", "retreat"), "kick_body": S("shell_block", "evade_step_back", "retreat"),
        "kick_linear": S("evade_step_back", "retreat"), "kick_high": S("lean_back", "shell_block", "retreat"),
        "takedown": S("sprawl", "pummel", "retreat"), "clinch_entry": S("pummel", "clinch_break", "retreat")},
    "defense.shoulder_roll": {
        "straight": S("shoulder_roll", "slip", "pivot", "retreat"), "hook": S("shell_block", "bob_weave", "retreat"),
        "uppercut": S("lean_back", "shell_block", "retreat"), "body_punch": S("shell_block", "retreat"),
        "elbow": S("shell_block", "retreat"), "knee": S("shell_block", "retreat"),
        "kick_low": S("check", "evade_step_back", "retreat"), "kick_body": S("shell_block", "evade_step_back", "retreat"),
        "kick_linear": S("evade_step_back", "retreat"), "kick_high": S("lean_back", "shell_block", "retreat"),
        "takedown": S("sprawl", "pummel", "retreat"), "clinch_entry": S("pummel", "clinch_break", "retreat")},
    "defense.parry_catch": {
        "straight": S("parry", "shell_block", "retreat"), "hook": S("shell_block", "retreat"),
        "uppercut": S("parry", "shell_block", "retreat"), "body_punch": S("shell_block", "retreat"),
        "elbow": S("shell_block", "retreat"), "knee": S("shell_block", "retreat"),
        "kick_low": S("kick_catch", "check", "evade_step_back", "retreat"), "kick_body": S("kick_catch", "shell_block", "retreat"),
        "kick_linear": S("kick_catch", "parry", "evade_step_back", "retreat"), "kick_high": S("shell_block", "lean_back", "retreat"),
        "takedown": S("sprawl", "pummel", "retreat"), "clinch_entry": S("pummel", "clinch_break", "retreat")},
    "defense.check_frame": {
        "straight": S("shield_frame", "parry", "shell_block", "retreat"), "hook": S("shield_frame", "shell_block", "retreat"),
        "uppercut": S("shell_block", "retreat"), "body_punch": S("shell_block", "shield_frame", "retreat"),
        "elbow": S("shield_frame", "shell_block", "retreat"), "knee": S("shield_frame", "shell_block", "retreat"),
        "kick_low": S("check", "evade_step_back", "retreat"), "kick_body": S("check", "shell_block", "retreat"),
        "kick_linear": S("parry", "evade_step_back", "retreat"), "kick_high": S("shell_block", "lean_back", "retreat"),
        "takedown": S("shield_frame", "sprawl", "whizzer", "retreat"), "clinch_entry": S("shield_frame", "pummel", "clinch_break", "retreat")},
    "defense.outfight": {
        "straight": S("pivot", "evade_step_back", "retreat"), "hook": S("evade_step_back", "pivot", "retreat"),
        "uppercut": S("evade_step_back", "retreat"), "body_punch": S("evade_step_back", "retreat"),
        "elbow": S("evade_step_back", "retreat"), "knee": S("evade_step_back", "retreat"),
        "kick_low": S("evade_step_back", "pivot", "retreat"), "kick_body": S("evade_step_back", "pivot", "retreat"),
        "kick_linear": S("evade_step_back", "pivot", "retreat"), "kick_high": S("evade_step_back", "lean_back", "retreat"),
        "takedown": S("pivot", "sprawl", "retreat"), "clinch_entry": S("pivot", "clinch_break", "retreat")},
    "defense.smother": {
        "straight": S("jam_step", "pummel", "shield_frame", "shell_block", "retreat"), "hook": S("jam_step", "pummel", "shell_block", "retreat"),
        "uppercut": S("shell_block", "pummel", "retreat"), "body_punch": S("shell_block", "pummel", "retreat"),
        "elbow": S("pummel", "shell_block", "retreat"), "knee": S("pummel", "shell_block", "retreat"),
        "kick_low": S("jam_step", "check", "retreat"), "kick_body": S("jam_step", "shell_block", "retreat"),
        "kick_linear": S("jam_step", "shell_block", "retreat"), "kick_high": S("jam_step", "shell_block", "retreat"),
        "takedown": S("pummel", "whizzer", "sprawl", "retreat"), "clinch_entry": S("pummel", "clinch_break", "retreat")},
    "defense.sprawl_pummel": {
        "straight": S("shell_block", "slip", "retreat"), "hook": S("shell_block", "retreat"),
        "uppercut": S("shell_block", "retreat"), "body_punch": S("shell_block", "retreat"),
        "elbow": S("pummel", "shell_block", "retreat"), "knee": S("pummel", "shell_block", "retreat"),
        "kick_low": S("check", "jam_step", "retreat"), "kick_body": S("jam_step", "shell_block", "retreat"),
        "kick_linear": S("jam_step", "retreat"), "kick_high": S("shell_block", "retreat"),
        "takedown": S("sprawl", "whizzer", "pummel", "retreat"), "clinch_entry": S("pummel", "whizzer", "retreat")},
    "defense.block_absorb": {
        "straight": ["shell_block", R_BLOCKED], "hook": ["shell_block", R_BLOCKED], "uppercut": ["shell_block", R_BLOCKED],
        "body_punch": ["shell_block", R_BLOCKED], "elbow": ["shell_block", R_BLOCKED], "knee": ["shell_block", R_BLOCKED],
        "kick_low": ["check", R_BLOCKED], "kick_body": ["shell_block", R_BLOCKED], "kick_linear": ["shell_block", R_BLOCKED],
        "kick_high": ["shell_block", R_BLOCKED], "takedown": S("sprawl", "pummel", "retreat"), "clinch_entry": S("pummel", "retreat")},
}
AT_WALL = {
    "defense.outfight": {cls: S("shell_block", "retreat") for cls in ("straight", "hook", "uppercut", "body_punch", "elbow", "knee", "kick_low", "kick_body", "kick_linear", "kick_high")}
    | {"takedown": S("sprawl", "whizzer", "shell_block", "retreat"), "clinch_entry": S("clinch_break", "shell_block", "retreat")},
}
CLASSES = ["straight", "hook", "uppercut", "body_punch", "elbow", "knee", "kick_low", "kick_body", "kick_linear", "kick_high", "takedown", "clinch_entry"]
for oid, lists in NATIVE.items():
    assert set(lists) == set(CLASSES), (oid, set(CLASSES) ^ set(lists))
    nd = {"by_class": lists}
    if oid in AT_WALL:
        nd["at_wall"] = AT_WALL[oid]
    put(oid, "native_defense", nd)
put("hands.philly_shell", "defense_prepend", {"straight": ["shoulder_roll"]})

# v2 option support: an option is supported when the v1 rule passes OR any trained technique is in supported_by_v2.
# This lets the new schools back the existing 57 options without editing v1 data (engine_index technique_refs).
STRIKE_KINDS = ("punch", "elbow", "kick", "knee")


def techs(pred):
    return sorted(t["id"] for t in seed_tech.values() if t["status"] != "existing" and pred(t))


def caps_of(t):
    return set(t["required_capabilities"])


SUPPORT = {
    "target.head_hunter": techs(lambda t: t["kind"] in STRIKE_KINDS and t["region_family"] == "head"),
    "target.body_puncher": techs(lambda t: t["kind"] in ("punch", "elbow") and t["region_family"] == "body"),
    "target.liver_ribs": techs(lambda t: t["kind"] in ("punch", "elbow") and t["region_family"] == "body"),
    "target.leg_chopper": techs(lambda t: t["kind"] == "kick" and t["region_family"] == "leg"),
    "target.knee_clincher": techs(lambda t: t["kind"] == "knee"),
    "target.mixer": techs(lambda t: t["kind"] in STRIKE_KINDS and t["base_damage"] > 0),
    "kicking.karate": techs(lambda t: t["kind"] == "kick" and bool(caps_of(t) & {"karate", "taekwondo", "capoeira", "jeet_kune_do", "hung_gar", "wing_chun"})),
    "kicking.muay_thai": techs(lambda t: t["kind"] == "kick" and bool(caps_of(t) & {"muay_thai", "lethwei"})),
    "kicking.dutch": techs(lambda t: t["kind"] == "kick" and "kickboxing" in caps_of(t)),
    "kicking.sanda": techs(lambda t: t["kind"] == "kick" and "sanda" in caps_of(t)),
    "hands.long_guard": ["chain_punch", "lead_straight_intercept", "piercing_palm", "finger_jab", "tan_sao", "bong_sao", "pak_sao"],
    "defense.parry_catch": ["tan_sao", "bong_sao", "pak_sao", "lap_sao", "push_hands_redirect"],
    "defense.slip_roll": ["esquiva", "negativa"],
    "defense.smother": ["top_elbow", "iron_mountain_lean", "clinch_headbutt"],
    "tie.folk_ride": ["cross_face", "cradle", "neck_crank"],
    "tie.judo_sambo": ["quick_grip_throw", "turning_throw", "kick_into_throw"],
    "tie.thai_plum": ["clinch_headbutt"],
    "mentality.counter": ["lead_straight_intercept", "push_hands_redirect", "deflect_parry_punch", "brush_knee_palm"],
    "mentality.showman": ["armada", "meia_lua_de_compasso", "tornado_kick", "au", "ginga"],
    "mentality.slickster": ["ginga", "circle_walk"],
    "mentality.technician": ["lead_straight_intercept", "cut_kick"],
    "mentality.pressure": ["chain_punch", "stomp_thrust_punch"],
    "mentality.swarmer": ["chain_punch", "stomp_thrust_punch"],
    "mentality.slugger": ["lunging_headbutt", "clinch_headbutt", "bridge_smash"],
    "stance.planted": ["stomp_thrust_punch", "bridge_smash", "tiger_claw"],
    "stance.shuffle": ["ginga", "circle_walk", "bounce_step"],
    "stance.bladed": ["cut_kick", "lead_straight_intercept"],
}
for oid, ids in SUPPORT.items():
    for tid in ids:
        assert tid in seed_tech, (oid, tid)
    put(oid, "supported_by_v2", ids)


# Style presets the owner MAY add later (D20). Not merged: the tests pin 57 options, 8 tie options and 6 kicking options,
# and knowledge options come from the v1 file data/engine_index.json.
def preset(base, new_id, changes, note):
    rec_ = json.loads(json.dumps(ob[base]))
    rec_["id"] = new_id
    for path, val in changes.items():
        node = rec_
        parts = path.split(".")
        for part in parts[:-1]:
            node = node[part]
        node[parts[-1]] = val
    return {"proposed_option": rec_, "derived_from": base, "why": note}


kr = ob["kicking.karate"]["attack_profile"]
PRESETS = [
    preset("kicking.karate", "kicking.taekwondo", {"attack_profile.kick_retraction_delta": round(kr["kick_retraction_delta"] - 0.03, 3),
                                                   "attack_profile.accuracy_delta": round(kr["accuracy_delta"] + 0.02, 3),
                                                   "attack_profile.power_delta": round(kr["power_delta"] - 0.02, 3),
                                                   "attack_profile.feint_setup_rate": round(kr["feint_setup_rate"] + 0.05, 3),
                                                   "attack_profile.favored_lanes": ["head_hook", "body"]},
           "fast, snapping instep kicks that retract even faster than karate (lower catch chance): more accuracy, less power"),
    preset("kicking.karate", "kicking.capoeira", {"attack_profile.kick_retraction_delta": round(kr["kick_retraction_delta"] + 0.12, 3),
                                                  "attack_profile.power_delta": round(kr["power_delta"] + 0.02, 3),
                                                  "attack_profile.feint_setup_rate": round(kr["feint_setup_rate"] + 0.08, 3),
                                                  "attack_profile.favored_lanes": ["head_hook"]},
           "deceptive spinning and crescent kicks: more power and deception, slower to retract (easier to catch than karate)"),
    preset("stance.shuffle", "stance.ginga", {"attack_profile.feint_setup_rate": round(ob["stance.shuffle"]["attack_profile"]["feint_setup_rate"] + 0.08, 3),
                                              "lane_readiness_bonus.single_support": round(ob["stance.shuffle"]["lane_readiness_bonus"]["single_support"] - 0.10, 3)},
           "constant rocking movement: harder to read, briefly on one leg"),
    preset("tie.folk_ride", "tie.catch_wrestling", {"attack_profile.sweep_resistance": 0.22},
           "rides plus submissions from top (grappling profile: top 4.5, sub off 4.0)"),
    preset("hands.long_guard", "hands.centerline", {"lane_readiness_bonus.head_straight": round(ob["hands.long_guard"]["lane_readiness_bonus"]["head_straight"] + 0.15, 3),
                                                    "lane_readiness_bonus.head_hook": round(ob["hands.long_guard"]["lane_readiness_bonus"]["head_hook"] - 0.10, 3)},
           "Wing Chun man sao / wu sao: owns the centerline, weaker against wide hooks"),
]
existing_retracts = {o["attack_profile"]["kick_retraction_delta"] for k, o in ob.items() if k.startswith("kicking.")}
existing_sweeps = {o["attack_profile"]["sweep_resistance"] for k, o in ob.items() if k.startswith("tie.")}
for pr in PRESETS:
    ap = pr["proposed_option"]["attack_profile"]
    if pr["proposed_option"]["id"].startswith("kicking."):
        assert ap["kick_retraction_delta"] not in existing_retracts, pr["proposed_option"]["id"]
    if pr["proposed_option"]["id"].startswith("tie."):
        assert ap["sweep_resistance"] not in existing_sweeps, pr["proposed_option"]["id"]
PRESET_REQUIREMENTS = ["add the option to data/engine_index.json (v1 knowledge index: ratings, technique_refs, exploitable_debt_ids)",
                       "add its debts to data/debt_registry.json with v1 technique ids",
                       "add the behavior record to data/option_behaviors.json",
                       "owner approval to change the pinned test counts: 57 options, 8 tie options, 6 kicking options (rule 9)"]
put("kicking.sanda", "kick_defense_prepend", {"kick_body": ["kick_catch"], "kick_low": ["kick_catch"], "kick_linear": ["kick_catch"]})
put("kicking.muay_thai", "kick_defense_prepend", {"kick_low": ["check"], "kick_body": ["check"]})
KDW = {"kicking.sanda": 0.08, "defense.parry_catch": 0.08, "defense.check_frame": 0.08, "defense.outfight": 0.08, "kicking.muay_thai": 0.04}
for k, v in KDW.items():
    put(k, "kick_defense_window_delta", v if k != "defense.outfight" else {"value": v, "unless": "wall_near"})
for k, rules in legacy["breakdown_rules"]["rules"].items():
    put(k, "breakdown_rules", rules)
for k, r in legacy["range_lane_bonuses"]["rules"].items():
    put(k, "range_lane_bonus", r)
put("defense.outfight", "counter_tendency_condition", {"ranges": ["kick"], "unless": "wall_near"})
put("defense.outfight", "distance_control_condition", {"unless": "wall_near"})
put("defense.outfight", "pull_out_probability", 0.72)
put("mentality.outboxer", "pull_out_probability", 0.72)
put("target.liver_ribs", "on_body_damage_extra_fatigue_fraction", 0.22)
put("defense.block_absorb", "damage_rules", {"blocked_landing_multiplier": 0.24, "head_guard_factor": 0.90, "source": f"{SRC}:864-866"})

option_additions = OrderedDict()
option_additions["per_option"] = add
option_additions["selection_profile_note"] = SELECTION_NOTE
option_additions["defense_list_rules"] = {
    "classes": CLASSES + ["ground_strike", "submission"],
    "entries": "a technique id, or {technique, result} to override that technique's success result for this option",
    "order": "kicking.kick_defense_prepend[class] + hands.defense_prepend[class] + defense.native_defense (at_wall list when wall_near and present); dedupe; keep trained; first wins; none -> retreat",
    "test_guards": ["defense.block_absorb straight list never reaches a basic_movement defense before retreat (Rook must return 'retreat')",
                    "defense.outfight straight list starts with pivot (Aya vs cross must return pivot or retreat)",
                    "defense.outfight kick_high starts with evade_step_back; at_wall starts with shell_block",
                    "defense.check_frame kick_low starts with check; Niran never returns slip",
                    "kicking.sanda prepends kick_catch for kick_body (Mio vs body_kick returns kick_catch)"],
}
option_additions["option_preset_proposals"] = {"decision": "D20", "requires": PRESET_REQUIREMENTS, "presets": PRESETS}
option_additions["unused_fields_today"] = ["damage_dealt_multiplier and damage_taken_multiplier (schema-required, never read): wire them in P7 as additive terms (dealt-1 into the attacker sum, taken-1 into the defender multiplier) and re-tune; never delete them",
                                           "dependencies and breakdowns (prose, schema-required): keep as documentation; breakdown_rules is the machine form",
                                           "posture_profile.risk_appetite: wire into selection risk (P3) or remove from the schema and data together"]
option_additions["owner_notes"] = ["mentality.defensive keeps positive lane readiness (the only offensive-dimension exception; the test exempts it). Owner decision D10."]
(OUT / "option_behavior_additions.json").write_text(json.dumps(option_additions, indent=1) + "\n")

# cross-check every technique referenced in defense lists exists in the seed catalog and is a defense/movement/both
for oid, lists in NATIVE.items():
    for cls, entries in lists.items():
        for e in entries:
            tid = e["technique"] if isinstance(e, dict) else e
            assert tid in seed_tech, (oid, cls, tid)
            assert seed_tech[tid]["usage"] in ("defense", "movement", "both") or seed_tech[tid]["kind"] in ("defense", "movement", "escape"), (oid, tid)

# ---------------------------------------------------------------------------
# 5. Card fixes (proposals; owner approves card changes). Cards keep version "block-2".
# ---------------------------------------------------------------------------
cards = {p.stem: json.load(open(p)) for p in sorted((REPO / "cards/v2").glob("*.json"))}
NATURAL = {"orthodox": ("right", "right"), "southpaw": ("left", "left"), "switching": ("right", "right")}
fixes = OrderedDict()
for fid, card in cards.items():
    hand, leg = NATURAL[card["orientation"]]
    fixes[fid] = OrderedDict(name=card["name"], orientation=card["orientation"],
                             laterality_proposal={"dominant_hand": hand, "dominant_leg": leg, "opposite_stance_experience": "normal",
                                                  "effect": "natural stance: zero dominance deltas (identical to having no block)"},
                             slot_changes=[], active_techniques_add=[], owner_decisions=[])
F = fixes


def slot_fix(fid, slot, problem, **proposal):
    F[fid]["slot_changes"].append({"slot": slot, "problem": problem, "proposal": proposal})


AR = lambda n, cond="sequence_denied_or_countered": {"max_consecutive_stalls": n, "condition": cond}  # noqa: E731
slot_fix("detroit", "detroit.slot.2", "basic_movement grants no strikes; the sequence uses boxing moves the slot does not grant",
         capabilities=["boxing", "counter_boxing"], sequence=["feint", "jab", "pull_counter", "check_hook", "cross"],
         trigger="opponent_commits", home_range="punch", goal="counter_trap", abandon_rule=AR(2), links=["detroit.slot.1"],
         note="differs from slot.1 by the counter-only tools and the trap; pull_counter/check_hook are usable only as counters, the slot's attacks are feint/jab/cross")
F["detroit"]["active_techniques_add"] += ["pull_counter", "check_hook"]
F["detroit"]["owner_decisions"].append("D7: approve new capability counter_boxing (pull_counter, check_hook) or relabel Darius Reed a 1-slot Brawler")
slot_fix("donnell", "donnell.slot.2", "pressure_footwork grants no strikes; the sequence is all boxing",
         capabilities=["boxing", "pressure_footwork"], sequence=["cut_off_step", "body_jab", "hook", "rear_hook", "body_hook"],
         trigger="opponent_circles_out", home_range="punch", goal="wall_pressure", abandon_rule=AR(2), links=["donnell.slot.3", "donnell.slot.1"])
F["donnell"]["active_techniques_add"] += ["cut_off_step", "body_jab", "rear_hook"]
slot_fix("donnell", "donnell.slot.3", "inside_combinations grants nothing today; the sequence is all boxing",
         capabilities=["inside_combinations"], sequence=["shovel_hook", "short_uppercut"],
         trigger="close_range_reached", home_range="close", goal="head_damage", abandon_rule=AR(2, "pocket_stalled"), links=["donnell.slot.1"])
F["donnell"]["active_techniques_add"] += ["shovel_hook", "short_uppercut"]
slot_fix("karate", "karate.slot.1", "teep/body_kick/spinning_back_kick are reachable only through the hidden grant in available_v2()",
         sequence=["side_kick", "teep", "body_kick", "oblique_kick", "head_kick", "spinning_back_kick"],
         note="the karate core repertoire (side_kick, teep, body_kick, spinning_back_kick) replaces the hidden grant in data; oblique_kick and head_kick must be added to active_techniques")
F["karate"]["active_techniques_add"] += ["oblique_kick", "head_kick"]
slot_fix("karate", "karate.slot.3", "anti_grappling grants only defensive tools; the sequence lists boxing strikes and a kick",
         capabilities=["anti_grappling"], sequence=["clinch_break", "technical_standup", "pivot", "retreat"],
         trigger="opponent_clinches_or_shoots", home_range="kick", goal="reset_to_home_range", abandon_rule=AR(2, "clinch_denied_or_escaped"), links=["karate.slot.1"],
         note="reset slot: while active, its defenses (sprawl, whizzer, jam_step) move to the front of the defense lists")
F["karate"]["active_techniques_add"] += ["technical_standup", "clinch_break"]
slot_fix("maleek", "maleek.slot.2", "jab/cross/body_hook were not granted by kickboxing+switch_step",
         sequence=["switch_step", "jab", "cross", "body_hook", "low_kick", "calf_kick", "body_kick"], note="fixed by D11 (kickboxing grants basic punches)")
F["maleek"]["active_techniques_add"] += ["calf_kick"]
slot_fix("maleek", "maleek.slot.3", "the anti_grappling slot throws the whole striking game",
         capabilities=["anti_grappling"], sequence=["clinch_break", "pivot", "retreat"], trigger="opponent_clinches_or_shoots",
         home_range="punch", goal="reset_to_home_range", abandon_rule=AR(2, "clinch_denied_or_escaped"), links=["maleek.slot.1"])
F["maleek"]["active_techniques_add"] += ["clinch_break"]
F["maleek"]["owner_decisions"].append("Wire the maleek.cage_plum conditional ability (wall + clinch + shield_frame setup); today it never unlocks")
slot_fix("sanda_judo", "sanda_judo.slot.1", "body_kick/low_kick are not granted by boxing+sanda in v1 data",
         note="fixed by data: sanda grants side/body/low kicks, teep, kick_catch, sanda_sweep, foot_sweep")
slot_fix("sanda_judo", "sanda_judo.slot.3", "double_leg/single_leg are in the sequence but not in active_techniques, so the built plan collapses to [outside_trip, ride]",
         sequence=["outside_trip", "inside_trip", "single_leg", "ride"], note="add inside_trip and single_leg to active_techniques (D1)")
F["sanda_judo"]["active_techniques_add"] += ["inside_trip", "single_leg"]
F["sanda_judo"]["owner_decisions"].append("D1: canonical Mio - current v2 (orthodox, tempo 3, parry_catch) vs original (southpaw, tempo 2, check_frame); name 'Mio Takahashi' in docs vs 'Mio Tsukihara' on the card")
slot_fix("street", "street.slot.1", "one move only (haymaker): 4 distinct 5-move openings in 60 fights",
         sequence=["brawler_straight", "wild_hook", "haymaker", "shove"], note="new untrained_striking techniques (D12); still one plan, abandon threshold stays 99; defense stays retreat")
F["street"]["active_techniques_add"] += ["brawler_straight", "wild_hook", "shove"]
slot_fix("thai", "thai.slot.2", "knee_body requires clinch, not kickboxing",
         capabilities=["muay_thai"], sequence=["teep", "body_kick", "low_kick", "straight_knee", "switch_kick"], note="or keep kickboxing and replace knee_body with straight_knee")
F["thai"]["active_techniques_add"] += ["straight_knee", "switch_kick"]
F["thai"]["owner_decisions"].append("D8: move Niran Sol to the new muay_thai capability (elbows, plum knees) - recommended for a Muay Thai identity")
for fid in F:
    F[fid]["all_cards"] = ["keep version 'block-2' (tests and the block-2 slot-budget check depend on it); add optional 'revision': 1",
                           "laterality block optional: natural stance = no effect; a cross-dominant block changes damage/accuracy and must be re-checked against the line-188 damage test for detroit and street",
                           "every sequence item must be granted by the slot's own capabilities (or basic_movement core) and be in active_techniques (or a capability core)",
                           "triggers, links and abandon_rule are honoured by the engine from P2 (not overwritten)",
                           "signature_moves stay strings (technique ids); optional signature_chains lists combination ids from data/combinations_v2.json"]
# validate proposed sequences against the seed and the schema vocabulary
GOALS = {"head_damage", "body_attrition", "leg_attrition", "clinch_control", "takedown_top_control", "counter_trap", "submission_finish", "wall_pressure", "reset_to_home_range", "position"}
for fid, f in F.items():
    for sc in f["slot_changes"]:
        p = sc["proposal"]
        for tid in p.get("sequence", []):
            assert tid in seed_tech, (fid, tid)
        if "goal" in p:
            assert p["goal"] in GOALS, (fid, p["goal"])
        if "trigger" in p:
            assert p["trigger"] in new_sections["slot_triggers"]["predicates"], (fid, p["trigger"])
        if "abandon_rule" in p:
            assert p["abandon_rule"]["condition"] in new_sections["slot_triggers"]["stall_conditions"], (fid, p["abandon_rule"])
    for tid in f["active_techniques_add"]:
        assert tid in seed_tech, (fid, tid)
(OUT / "card_fixes.json").write_text(json.dumps(fixes, indent=1) + "\n")


# ---------------------------------------------------------------------------
# 6. Markdown tables
# ---------------------------------------------------------------------------
def md_table(headers, rows):
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    for r in rows:
        out.append("| " + " | ".join(str(x) for x in r) + " |")
    return "\n".join(out)


rows = []
for section, items in engine_constants.items():
    for name, v in items.items():
        val = v["value"]
        if isinstance(val, (dict, list)):
            val = json.dumps(val).replace("|", "/")
        target = f"read existing `{v['existing_key']}`" if "existing_key" in v else f"new `{section}.{name}`"
        rows.append([section, f"`{name}`", f"`{val}`", v["source"].split(":")[1], target, v["note"]])
(OUT / "constants_table.md").write_text(md_table(["section", "constant", "current value", "line", "data key", "note"], rows) + "\n")

g_rows = [[f"`{k}`"] + [v[x] for x in ("takedown_offense", "takedown_defense", "clinch_control", "top_control", "bottom_game", "submission_offense", "submission_defense", "scramble", "stand_up")]
          for k, v in list(GRAPPLING.items()) + [("model.grappling.null_tie_profile (tie = null)", new_sections["grappling"]["null_tie_profile"])]]
(OUT / "grappling_table.md").write_text(md_table(["tie option", "TD off", "TD def", "clinch", "top", "bottom", "sub off", "sub def", "scramble", "stand-up"], g_rows) + "\n")
s_rows = [[f"`{k}`", v["initiative_delta"], v.get("initiative_delta_when_waiting", ""), v["switch_after_stalls"], v["patience"], v["risk"], v["combo_length"]] for k, v in SELECTION.items()]
(OUT / "selection_table.md").write_text(md_table(["mentality", "initiative Δ", "Δ when waiting", "default stalls before switch", "patience (gap ×)", "risk", "combo length"], s_rows) + "\n")


def fmt_entry(e):
    return f"{e['technique']}→{e['result']}" if isinstance(e, dict) else e


d_rows = []
for oid, lists in NATIVE.items():
    for cls in CLASSES:
        d_rows.append([f"`{oid}`", cls, " → ".join(fmt_entry(e) for e in lists[cls]), " → ".join(AT_WALL.get(oid, {}).get(cls, []))])
(OUT / "defense_lists_table.md").write_text(md_table(["defense option", "incoming class", "ordered list (first trained wins)", "at wall"], d_rows) + "\n")
t_rows = [[f"`{k}`", v] for k, v in new_sections["slot_triggers"]["predicates"].items()]
(OUT / "triggers_table.md").write_text(md_table(["trigger", "holds when"], t_rows) + "\n")
cf_rows = []
for fid, f in F.items():
    for sc in f["slot_changes"]:
        p = sc["proposal"]
        parts = []
        if "capabilities" in p:
            parts.append("caps `" + json.dumps(p["capabilities"]) + "`")
        if "sequence" in p:
            parts.append("seq `" + " → ".join(p["sequence"]) + "`")
        for key in ("trigger", "home_range", "goal"):
            if key in p:
                parts.append(f"{key} `{p[key]}`")
        if "abandon_rule" in p:
            parts.append(f"abandon `{p['abandon_rule']['max_consecutive_stalls']}× {p['abandon_rule']['condition']}`")
        if "links" in p:
            parts.append("links `" + ", ".join(p["links"]) + "`")
        if "note" in p:
            parts.append(p["note"])
        cf_rows.append([f"`{fid}` ({f['name']})", sc["slot"].split(".", 1)[1], sc["problem"], "; ".join(parts)])
    if f["active_techniques_add"]:
        cf_rows.append([f"`{fid}`", "active_techniques", "proposal needs these listed", ", ".join(f"`{t}`" for t in f["active_techniques_add"])])
(OUT / "card_fixes_table.md").write_text(md_table(["card", "slot", "problem", "proposal"], cf_rows) + "\n")
print("model/options/cards seeds written")
