"""Deterministic builder and schema validator for BLOCK Simulator v2 data files:
- data/option_behaviors.json (all 57 style options)
- data/techniques_v2.json (38 techniques with frame costs, biomechanics, recovery exposure, base damage)
- data/positions.json (15 grappling positions + 14 transitions)
- data/model_v2.json (readiness math, state modifiers, damage limits, arena presets, slot depth rules)
- cards/v2/sanda_judo.json (worked block-2 fighter card for Mio Tsukihara)
"""

from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import jsonschema
from engine.ontology import ROOT, Knowledge, read, write


LANES = [
    "head_straight",
    "head_hook",
    "head_uppercut",
    "body",
    "leg",
    "entry",
    "clinch",
    "single_support",
]


DEFENSE_TABLE = {
    "defense.slip_roll": {
        "deps": ["seeing the shot (vision >= 3)", "head off centerline", "flexible base"],
        "breaks": ["tired (fatigue >= 5)", "hurt head (head damage >= 4)", "vision blocked", "uppercuts (head_uppercut)"],
        "bonuses": {"head_straight": 1.6, "head_hook": 1.3, "head_uppercut": -0.7, "body": 0.2, "leg": -0.3, "entry": 0.0, "clinch": -0.4, "single_support": 0.1},
        "dmg_taken": 0.90,
    },
    "defense.parry_catch": {
        "deps": ["reading the rhythm", "hands up and relaxed", "kick_catch timing"],
        "breaks": ["feints", "hooks around the guard (head_hook)", "body level changes (body)"],
        "bonuses": {"head_straight": 1.7, "head_hook": -0.6, "head_uppercut": 0.4, "body": -0.5, "leg": 0.5, "entry": 0.2, "clinch": 0.2, "single_support": 1.1},
        "dmg_taken": 0.92,
    },
    "defense.block_absorb": {
        "deps": ["solid guard integrity", "rooted feet"],
        "breaks": ["body damage builds (body >= 4)", "guard integrity wears down", "blinded vision"],
        "bonuses": {"head_straight": 1.1, "head_hook": 1.2, "head_uppercut": 0.6, "body": -0.6, "leg": -0.2, "entry": -0.1, "clinch": 0.3, "single_support": -0.1},
        "dmg_taken": 0.85,
    },
    "defense.outfight": {
        "deps": ["room behind (wall_proximity == far)", "mobile feet (leg damage < 4)"],
        "breaks": ["backed onto the wall or in the corner", "hurt legs (leg damage >= 4)", "high-tempo swarmer pressure"],
        "bonuses": {"head_straight": 1.2, "head_hook": 1.1, "head_uppercut": 1.0, "body": 0.9, "leg": 0.8, "entry": 0.9, "clinch": -0.3, "single_support": 0.4},
        "dmg_taken": 0.92,
    },
    "defense.shoulder_roll": {
        "deps": ["bladed stance", "timing", "lead shoulder raised"],
        "breaks": ["hooks from the open side", "low kicks to the bladed lead leg", "clinch ties"],
        "bonuses": {"head_straight": 1.7, "head_hook": -0.5, "head_uppercut": 0.8, "body": 0.7, "leg": -0.8, "entry": -0.4, "clinch": -0.5, "single_support": -0.2},
        "dmg_taken": 0.89,
    },
    "defense.check_frame": {
        "deps": ["weight on back leg or balanced", "seeing the kick", "uncompromised support leg"],
        "breaks": ["front-loaded weight split", "mid-switch transition", "tired or battered legs", "body punches"],
        "bonuses": {"head_straight": 0.6, "head_hook": 0.4, "head_uppercut": 0.3, "body": -0.5, "leg": 1.9, "entry": 0.3, "clinch": 0.8, "single_support": -0.6},
        "dmg_taken": 0.91,
    },
    "defense.sprawl_pummel": {
        "deps": ["hips high and back", "reaction time", "unfeinted vision"],
        "breaks": ["stance too low or too upright", "high fatigue", "a high-line feint before the shot"],
        "bonuses": {"head_straight": -0.5, "head_hook": -0.2, "head_uppercut": 0.2, "body": 0.4, "leg": 0.3, "entry": 2.1, "clinch": 1.5, "single_support": 0.6},
        "dmg_taken": 0.94,
    },
    "defense.smother": {
        "deps": ["closing distance first", "inside head position"],
        "breaks": ["opponent has superior clinch grips or ties", "intercepting knees/uppercuts on entry"],
        "bonuses": {"head_straight": 0.7, "head_hook": 0.9, "head_uppercut": -0.4, "body": 0.8, "leg": 0.9, "entry": -0.5, "clinch": -0.5, "single_support": 0.2},
        "dmg_taken": 0.90,
    },
}


STANCE_PROFILES = {
    "stance.upright": {
        "weight_split": "rear_heavy",
        "height": "upright_tall",
        "hip_angle": "squared",
        "base_width": "balanced",
        "dmg_dealt": 1.02,
        "dmg_taken": 1.00,
        "deps": ["rear-leg weight distribution for fast shin checks and teeps", "tall posture"],
        "breaks": ["level-change takedown entries (entry)", "body hooks under high elbows (body)"],
        "bonuses": {"head_straight": 0.3, "head_hook": 0.2, "head_uppercut": 0.4, "body": -0.6, "leg": 1.3, "entry": -0.8, "clinch": 0.9, "single_support": 0.5},
    },
    "stance.bladed": {
        "weight_split": "balanced",
        "height": "medium",
        "hip_angle": "bladed",
        "base_width": "narrow_mobile",
        "dmg_dealt": 0.94,
        "dmg_taken": 0.94,
        "deps": ["narrow target silhouette", "in-and-out linear mobility"],
        "breaks": ["low kicks to the turned lead leg (leg)", "direct takedown entries (entry)"],
        "bonuses": {"head_straight": 1.1, "head_hook": 0.3, "head_uppercut": 0.5, "body": 0.8, "leg": -0.9, "entry": -0.6, "clinch": -0.3, "single_support": 0.1},
    },
    "stance.crouch": {
        "weight_split": "front_heavy",
        "height": "low_crouch",
        "hip_angle": "squared",
        "base_width": "wide_rooted",
        "dmg_dealt": 1.15,
        "dmg_taken": 0.96,
        "deps": ["low center of gravity", "loaded legs for hooks and level changes"],
        "breaks": ["rising uppercuts and knees (head_uppercut)", "low kicks to the heavy lead leg (leg)"],
        "bonuses": {"head_straight": 0.9, "head_hook": 0.6, "head_uppercut": -0.9, "body": 0.5, "leg": -0.8, "entry": 0.8, "clinch": 0.4, "single_support": -0.3},
    },
    "stance.balanced": {
        "weight_split": "balanced",
        "height": "medium",
        "hip_angle": "semi_bladed",
        "base_width": "balanced",
        "dmg_dealt": 1.00,
        "dmg_taken": 0.98,
        "deps": ["50/50 weight split", "even readiness to strike or sprawl"],
        "breaks": ["high-tempo specialists overloading one lane", "straight center probes (head_straight)"],
        "bonuses": {"head_straight": -0.3, "head_hook": 0.4, "head_uppercut": 0.4, "body": 0.4, "leg": 0.5, "entry": 0.9, "clinch": 0.6, "single_support": 0.5},
    },
    "stance.planted": {
        "weight_split": "front_heavy",
        "height": "medium",
        "hip_angle": "squared",
        "base_width": "wide_rooted",
        "dmg_dealt": 1.22,
        "dmg_taken": 1.04,
        "deps": ["rooted two-foot base generating maximum punch torque and push resistance"],
        "breaks": ["lateral angle pivots (angle)", "calf and thigh kicks to rooted lead leg (leg)"],
        "bonuses": {"head_straight": 0.2, "head_hook": 0.4, "head_uppercut": 0.3, "body": 0.4, "leg": -1.0, "entry": 0.4, "clinch": 0.7, "single_support": -0.5},
    },
    "stance.switch": {
        "weight_split": "neutral",
        "height": "medium",
        "hip_angle": "switching",
        "base_width": "narrow_mobile",
        "dmg_dealt": 1.08,
        "dmg_taken": 0.98,
        "deps": ["recovered Uno changeover", "shifting lead-foot alignment"],
        "breaks": ["timed entries mid-switch (entry)", "sweeps/kicks while on single support (single_support)"],
        "bonuses": {"head_straight": 0.6, "head_hook": 0.6, "head_uppercut": 0.4, "body": 0.4, "leg": 0.3, "entry": -0.6, "clinch": 0.1, "single_support": -0.7},
    },
    "stance.shuffle": {
        "weight_split": "neutral",
        "height": "upright_tall",
        "hip_angle": "bladed",
        "base_width": "narrow_mobile",
        "dmg_dealt": 0.90,
        "dmg_taken": 0.95,
        "deps": ["continuous foot bounce", "open-floor space"],
        "breaks": ["low kicks timing the bounce (leg)", "single-support sweeps (single_support)"],
        "bonuses": {"head_straight": 0.9, "head_hook": 0.7, "head_uppercut": 0.6, "body": 0.5, "leg": -0.7, "entry": 0.3, "clinch": -0.3, "single_support": -0.7},
    },
}


def build_option_behaviors(k: Knowledge) -> Dict[str, object]:
    records = []
    for opt_id, opt in sorted(k.options.items()):
        dim = opt["dimension"]
        ratings = opt["mma_adaptation"]["ratings"]
        exposes = set(opt["tactical_conditions"]["exposes"])
        answers = set(opt["tactical_conditions"]["answers"])

        bonuses = {lane: 0.0 for lane in LANES}
        for lane in LANES:
            if lane in answers:
                bonuses[lane] += 0.85
            if lane in exposes:
                bonuses[lane] -= 0.75

        posture_prof = {
            "weight_split": "balanced",
            "height": "medium",
            "hip_angle": "semi_bladed",
            "base_width": "balanced",
            "head_position": "centerline_tucked",
            "vision": int(ratings.get("vision", 3)),
            "guard_decay_rate": 0.06,
            "risk_appetite": 1.0,
        }
        dmg_dealt = 1.0
        dmg_taken = 1.0
        deps = [opt["mechanical_advantages"][0]]
        breaks = [d["tradeoff"] for d in opt["derived_liabilities"]] or ["unrecovered commitment"]

        if dim == "hands":
            hc = ratings.get("head_coverage", 3)
            bc = ratings.get("body_coverage", 3)
            vis = ratings.get("vision", 3)
            bonuses["head_straight"] += (hc - 3) * 0.45
            bonuses["head_hook"] += (hc - 3) * 0.40
            bonuses["head_uppercut"] += (hc - 3) * 0.25
            bonuses["body"] += (bc - 3) * 0.45
            posture_prof["vision"] = vis
            posture_prof["head_position"] = (
                "off_center" if opt_id in ("hands.philly_shell", "hands.peekaboo", "hands.shield52", "hands.kronk")
                else ("centerline_high" if opt_id == "hands.hands_down" else "centerline_tucked")
            )
            posture_prof["guard_decay_rate"] = 0.09 if hc >= 4 else 0.05
            dmg_taken = round(1.12 - 0.04 * hc, 3)
        elif dim == "defense":
            d_info = DEFENSE_TABLE[opt_id]
            bonuses = {k_l: round(v_l, 2) for k_l, v_l in d_info["bonuses"].items()}
            deps = d_info["deps"]
            breaks = d_info["breaks"]
            dmg_taken = d_info["dmg_taken"]
            if opt_id in ("defense.slip_roll", "defense.shoulder_roll"):
                posture_prof["head_position"] = "off_center"
        elif dim == "stance":
            s_info = STANCE_PROFILES[opt_id]
            bonuses = {k_l: round(v_l, 2) for k_l, v_l in s_info["bonuses"].items()}
            posture_prof["weight_split"] = s_info["weight_split"]
            posture_prof["height"] = s_info["height"]
            posture_prof["hip_angle"] = s_info["hip_angle"]
            posture_prof["base_width"] = s_info["base_width"]
            dmg_dealt = s_info["dmg_dealt"]
            dmg_taken = s_info["dmg_taken"]
            deps = s_info["deps"]
            breaks = s_info["breaks"]
        elif dim == "mentality":
            m_map = {
                "mentality.slugger": (1.32, 1.08, 1.35),
                "mentality.pressure": (1.15, 1.03, 1.20),
                "mentality.swarmer": (0.90, 1.02, 1.25),
                "mentality.boxer_puncher": (1.10, 0.98, 1.05),
                "mentality.counter": (1.12, 0.90, 0.80),
                "mentality.outboxer": (0.92, 0.90, 0.78),
                "mentality.spoiler": (0.88, 0.88, 0.75),
                "mentality.defensive": (0.86, 0.84, 0.70),
                "mentality.switch_hitter": (1.08, 0.97, 1.05),
                "mentality.slickster": (0.94, 0.90, 0.85),
                "mentality.showman": (1.06, 1.04, 1.20),
                "mentality.technician": (1.05, 0.92, 0.88),
            }
            dmg_dealt, dmg_taken, risk = m_map.get(opt_id, (1.0, 1.0, 1.0))
            posture_prof["risk_appetite"] = risk
        elif dim == "kicking":
            k_mult = {
                "kicking.muay_thai": 1.18,
                "kicking.dutch": 1.14,
                "kicking.karate": 1.12,
                "kicking.sanda": 1.10,
                "kicking.wrestler_teep": 1.04,
                "kicking.none": 1.00,
            }
            dmg_dealt = k_mult.get(opt_id, 1.0)
        elif dim == "target":
            dmg_dealt = 1.10

        records.append(
            {
                "id": opt_id,
                "dimension": dim,
                "lane_readiness_bonus": {k_l: round(bonuses[k_l], 2) for k_l in LANES},
                "damage_dealt_multiplier": dmg_dealt,
                "damage_taken_multiplier": dmg_taken,
                "posture_profile": posture_prof,
                "dependencies": deps,
                "breakdowns": breaks,
            }
        )
    return {"version": "block-2", "options": records}


def build_techniques_v2(k: Knowledge) -> Dict[str, object]:
    from engine.simulator_v2 import MOVE_BASE_STATS

    LANE_BY_TID = {
        "step": "space",
        "retreat": "space",
        "pivot": "space",
        "switch_step": "space",
        "feint": "space",
        "jab": "head_straight",
        "cross": "head_straight",
        "hook": "head_hook",
        "body_hook": "body",
        "uppercut": "head_uppercut",
        "haymaker": "head_hook",
        "parry": "head_straight",
        "shell_block": "head_hook",
        "shield_frame": "head_straight",
        "slip": "head_straight",
        "check": "leg",
        "low_kick": "leg",
        "body_kick": "body",
        "teep": "body",
        "side_kick": "body",
        "sanda_sweep": "single_support",
        "sprawl": "entry",
        "pummel": "clinch",
        "collar_tie": "clinch",
        "knee_body": "body",
        "body_lock": "clinch",
        "double_leg": "entry",
        "single_leg": "entry",
        "outside_trip": "clinch",
        "guard_pull": "clinch",
        "ride": "ground",
        "armbar": "ground",
        "escape": "ground",
        "cage_plum": "clinch",
    }

    SURFACE_BY_TID = {
        "jab": "lead_knuckles",
        "cross": "rear_knuckles",
        "hook": "lead_knuckles",
        "body_hook": "lead_knuckles",
        "uppercut": "rear_knuckles",
        "haymaker": "rear_fist_loop",
        "low_kick": "lower_shin",
        "body_kick": "lower_shin",
        "teep": "ball_of_foot",
        "side_kick": "blade_of_foot",
        "knee_body": "kneecap",
        "sanda_sweep": "instep_and_forearm_reap",
        "outside_trip": "calf_hook_reap",
        "double_leg": "shoulder_drive_and_wrists",
        "single_leg": "chest_wrap_and_shelf",
        "collar_tie": "cupped_palm_behind_neck",
        "body_lock": "clasped_gable_grip",
        "pummel": "inside_forearm_wedge",
        "cage_plum": "double_crown_neck_clamp",
        "shield_frame": "forearm_triangle_bone_wedge",
        "guard_pull": "collar_and_hip_foot_frame",
        "ride": "chest_weight_and_wrist_ride",
        "armbar": "pelvis_fulcrum_on_elbow",
    }

    records = []
    for tid, t in k.techniques.items():
        st = MOVE_BASE_STATS.get(tid, {"base": 0.0, "type": "none", "setup_f": 3, "exec_f": 6, "hold_f": 0, "rec_f": 5})
        dmg_type = str(st["type"])
        if dmg_type in ("movement", "feint"):
            dmg_type = "none"
        kind = t["kind"]
        target_reg = t["target_region"]
        if target_reg not in ("space", "angle", "vision", "head", "body", "leg", "hips", "neck_arm"):
            target_reg = "body"

        if kind in ("kick", "knee"):
            win_type = "single_leg_recovery"
            exp_lanes = ["single_support", "leg", "head_straight", "entry"]
            pen = 1.15 if tid in ("low_kick", "body_kick") else 0.75
        elif tid == "haymaker":
            win_type = "wide_swing_recovery"
            exp_lanes = ["head_straight", "head_hook", "entry", "body"]
            pen = 1.65
        elif kind == "punch":
            win_type = "extended_arm_recovery" if tid in ("cross", "hook", "uppercut", "body_hook") else "short_retract"
            exp_lanes = ["head_straight", "head_hook", "body"]
            pen = 0.70 if win_type == "extended_arm_recovery" else 0.35
        elif kind == "takedown":
            win_type = "sprawled_shot_recovery"
            exp_lanes = ["head_uppercut", "clinch", "body"]
            pen = 1.25
        else:
            win_type = "none"
            exp_lanes = []
            pen = 0.15

        records.append(
            {
                "id": tid,
                "name": t["name"],
                "kind": kind,
                "required_capabilities": t["required_capabilities"],
                "required_range": t["required_range"],
                "attack_lane": LANE_BY_TID.get(tid, "body"),
                "target_region": target_reg,
                "base_damage": float(st["base"]),
                "damage_type": dmg_type,
                "frame_costs": {
                    "setup_frames": int(st["setup_f"]),
                    "execution_frames": int(st["exec_f"]),
                    "contact_hold_frames": int(st["hold_f"]),
                    "recovery_frames": int(st["rec_f"]),
                },
                "biomechanics": {
                    "attacking_limb": t["attacking_limb"],
                    "striking_surface": SURFACE_BY_TID.get(tid, t["attacking_limb"]),
                    "path": t["direction_trajectory"],
                    "height": "high" if target_reg == "head" else ("low" if target_reg == "leg" else ("ground" if "ground" in t["required_range"] else "mid")),
                    "ending": "carry_through" if tid in ("low_kick", "body_kick", "haymaker") else ("mat_settle" if "ground" in t["required_range"] else "snap_back"),
                    "vertical_mode_required": "grounded",
                },
                "recovery_exposure": {
                    "window_type": win_type,
                    "exposed_lanes": exp_lanes,
                    "readiness_penalty": pen,
                },
                "counters": t["defensive_counters"],
            }
        )

    # Add the 9 new v2 kicking & defensive techniques
    extra_v2 = [
        {
            "id": "head_kick",
            "name": "High roundhouse kick",
            "kind": "kick",
            "required_capabilities": ["kickboxing", "karate"],
            "required_range": ["kick"],
            "attack_lane": "head_hook",
            "target_region": "head",
            "base_damage": 3.5,
            "damage_type": "impact",
            "frame_costs": {"setup_frames": 7, "execution_frames": 10, "contact_hold_frames": 4, "recovery_frames": 15},
            "biomechanics": {
                "attacking_limb": "rear leg",
                "striking_surface": "lower_shin_or_instep",
                "path": "High diagonal round arc to temple/neck",
                "height": "high",
                "ending": "carry_through",
                "vertical_mode_required": "grounded",
            },
            "recovery_exposure": {
                "window_type": "single_leg_recovery",
                "exposed_lanes": ["single_support", "leg", "head_straight", "entry"],
                "readiness_penalty": 1.45,
            },
            "counters": ["lean_back", "evade_step_back", "shell_block"],
        },
        {
            "id": "switch_kick",
            "name": "Switch lead round kick",
            "kind": "kick",
            "required_capabilities": ["kickboxing", "switch_step"],
            "required_range": ["kick"],
            "attack_lane": "body",
            "target_region": "body",
            "base_damage": 2.8,
            "damage_type": "stamina_drain",
            "frame_costs": {"setup_frames": 6, "execution_frames": 9, "contact_hold_frames": 3, "recovery_frames": 11},
            "biomechanics": {
                "attacking_limb": "switched lead leg",
                "striking_surface": "lower_shin",
                "path": "Quick hop switch into horizontal rib arc",
                "height": "mid",
                "ending": "step_down_switch",
                "vertical_mode_required": "grounded",
            },
            "recovery_exposure": {
                "window_type": "single_leg_recovery",
                "exposed_lanes": ["single_support", "head_straight", "leg"],
                "readiness_penalty": 1.10,
            },
            "counters": ["check", "kick_catch", "evade_step_back"],
        },
        {
            "id": "spinning_back_kick",
            "name": "Spinning back thrust kick",
            "kind": "kick",
            "required_capabilities": ["karate"],
            "required_range": ["kick"],
            "attack_lane": "body",
            "target_region": "body",
            "base_damage": 3.3,
            "damage_type": "impact",
            "frame_costs": {"setup_frames": 8, "execution_frames": 10, "contact_hold_frames": 4, "recovery_frames": 16},
            "biomechanics": {
                "attacking_limb": "rear leg",
                "striking_surface": "heel_of_foot",
                "path": "180-degree dorsal spin into linear heel thrust to solar plexus",
                "height": "mid",
                "ending": "step_down_switch",
                "vertical_mode_required": "athletic",
            },
            "recovery_exposure": {
                "window_type": "single_leg_recovery",
                "exposed_lanes": ["single_support", "clinch", "entry"],
                "readiness_penalty": 1.55,
            },
            "counters": ["evade_step_back", "pivot", "jam_step"],
        },
        {
            "id": "axe_kick",
            "name": "Vertical heel axe kick",
            "kind": "kick",
            "required_capabilities": ["karate"],
            "required_range": ["kick", "punch"],
            "attack_lane": "head_straight",
            "target_region": "head",
            "base_damage": 3.1,
            "damage_type": "impact",
            "frame_costs": {"setup_frames": 8, "execution_frames": 11, "contact_hold_frames": 3, "recovery_frames": 14},
            "biomechanics": {
                "attacking_limb": "rear leg",
                "striking_surface": "back_of_heel",
                "path": "High vertical lift dropping straight down onto collarbone/crown",
                "height": "high",
                "ending": "snap_back",
                "vertical_mode_required": "athletic",
            },
            "recovery_exposure": {
                "window_type": "single_leg_recovery",
                "exposed_lanes": ["single_support", "head_straight", "leg"],
                "readiness_penalty": 1.35,
            },
            "counters": ["evade_step_back", "pivot", "lean_back"],
        },
        {
            "id": "jumping_knee",
            "name": "Flying switch knee",
            "kind": "knee",
            "required_capabilities": ["kickboxing", "clinch"],
            "required_range": ["punch", "close"],
            "attack_lane": "head_uppercut",
            "target_region": "head",
            "base_damage": 3.6,
            "damage_type": "impact",
            "frame_costs": {"setup_frames": 7, "execution_frames": 10, "contact_hold_frames": 4, "recovery_frames": 16},
            "biomechanics": {
                "attacking_limb": "rear knee",
                "striking_surface": "pointed_kneecap",
                "path": "Explosive upward jump driving knee vertically through centerline",
                "height": "high",
                "ending": "snap_back",
                "vertical_mode_required": "athletic",
            },
            "recovery_exposure": {
                "window_type": "airborne_landing_recovery",
                "exposed_lanes": ["head_straight", "head_hook", "entry", "single_support"],
                "readiness_penalty": 1.75,
            },
            "counters": ["evade_step_back", "parry", "sprawl"],
        },
        {
            "id": "kick_catch",
            "name": "Underhook kick catch trap",
            "kind": "defense",
            "required_capabilities": ["sanda", "boxing"],
            "required_range": ["kick"],
            "attack_lane": "single_support",
            "target_region": "leg",
            "base_damage": 0.0,
            "damage_type": "control",
            "frame_costs": {"setup_frames": 2, "execution_frames": 5, "contact_hold_frames": 2, "recovery_frames": 4},
            "biomechanics": {
                "attacking_limb": "lead arm scoop and rear palm clamp",
                "striking_surface": "forearm_cradle",
                "path": "Absorb round kick on rib guard and wrap ankle/achilles",
                "height": "mid",
                "ending": "clinch_tie",
                "vertical_mode_required": "grounded",
            },
            "recovery_exposure": {"window_type": "none", "exposed_lanes": ["head_straight"], "readiness_penalty": 0.25},
            "counters": ["jab", "cross"],
        },
        {
            "id": "lean_back",
            "name": "Pull-back high-kick evasion",
            "kind": "defense",
            "required_capabilities": ["boxing", "basic_movement"],
            "required_range": ["kick", "punch"],
            "attack_lane": "head_hook",
            "target_region": "space",
            "base_damage": 0.0,
            "damage_type": "none",
            "frame_costs": {"setup_frames": 2, "execution_frames": 5, "contact_hold_frames": 0, "recovery_frames": 4},
            "biomechanics": {
                "attacking_limb": "torso and rear hip",
                "striking_surface": "none",
                "path": "Sway upper torso and head behind rear hip so high arc whiffs",
                "height": "high",
                "ending": "snap_back",
                "vertical_mode_required": "grounded",
            },
            "recovery_exposure": {"window_type": "none", "exposed_lanes": ["body", "leg"], "readiness_penalty": 0.20},
            "counters": ["low_kick", "body_kick"],
        },
        {
            "id": "evade_step_back",
            "name": "Outfighting range pull step",
            "kind": "defense",
            "required_capabilities": ["basic_movement", "karate"],
            "required_range": ["kick", "punch"],
            "attack_lane": "space",
            "target_region": "space",
            "base_damage": 0.0,
            "damage_type": "none",
            "frame_costs": {"setup_frames": 2, "execution_frames": 5, "contact_hold_frames": 0, "recovery_frames": 3},
            "biomechanics": {
                "attacking_limb": "both feet",
                "striking_surface": "none",
                "path": "Push off lead ball of foot to clear the outer arc of the kick",
                "height": "none",
                "ending": "snap_back",
                "vertical_mode_required": "grounded",
            },
            "recovery_exposure": {"window_type": "none", "exposed_lanes": [], "readiness_penalty": 0.10},
            "counters": ["step"],
        },
        {
            "id": "jam_step",
            "name": "Crowding step inside kick chamber",
            "kind": "defense",
            "required_capabilities": ["clinch", "wrestling"],
            "required_range": ["kick", "punch"],
            "attack_lane": "clinch",
            "target_region": "body",
            "base_damage": 0.0,
            "damage_type": "control",
            "frame_costs": {"setup_frames": 2, "execution_frames": 6, "contact_hold_frames": 2, "recovery_frames": 4},
            "biomechanics": {
                "attacking_limb": "forearms and hips",
                "striking_surface": "forearm_frame",
                "path": "Step inside the kicker's knee chamber before extension to smother power",
                "height": "mid",
                "ending": "clinch_tie",
                "vertical_mode_required": "grounded",
            },
            "recovery_exposure": {"window_type": "none", "exposed_lanes": ["head_uppercut"], "readiness_penalty": 0.20},
            "counters": ["knee_body", "uppercut"],
        },
    ]
    records.extend(extra_v2)
    return {"version": "block-2", "techniques": records}


def build_positions_map() -> Dict[str, object]:
    positions = [
        {"id": "standing_neutral", "domain": "standing", "range": "kick", "posture": "standing", "dominant_side_role": "neutral", "allowed_techniques": ["step", "retreat", "pivot", "switch_step", "feint", "jab", "cross", "hook", "body_hook", "uppercut", "haymaker", "low_kick", "body_kick", "head_kick", "teep", "side_kick", "switch_kick", "spinning_back_kick", "axe_kick", "jumping_knee", "double_leg", "single_leg", "collar_tie", "body_lock"]},
        {"id": "caught_single_leg", "domain": "standing", "range": "close", "posture": "standing", "dominant_side_role": "initiator", "allowed_techniques": ["sanda_sweep", "outside_trip", "cross", "single_leg"]},
        {"id": "standing_back_take", "domain": "standing", "range": "clinch", "posture": "standing", "dominant_side_role": "back_controller", "allowed_techniques": ["outside_trip", "body_lock", "knee_body"]},
        {"id": "collar_tie", "domain": "clinch", "range": "clinch", "posture": "standing", "dominant_side_role": "initiator", "allowed_techniques": ["knee_body", "uppercut", "hook", "pummel", "guard_pull", "outside_trip"]},
        {"id": "thai_plum", "domain": "clinch", "range": "clinch", "posture": "standing", "dominant_side_role": "initiator", "allowed_techniques": ["knee_body", "jumping_knee", "outside_trip", "pummel"]},
        {"id": "over_under", "domain": "clinch", "range": "clinch", "posture": "standing", "dominant_side_role": "neutral", "allowed_techniques": ["pummel", "knee_body", "body_lock", "outside_trip"]},
        {"id": "double_underhooks", "domain": "clinch", "range": "clinch", "posture": "standing", "dominant_side_role": "initiator", "allowed_techniques": ["body_lock", "outside_trip", "double_leg", "knee_body"]},
        {"id": "front_body_lock", "domain": "clinch", "range": "clinch", "posture": "standing", "dominant_side_role": "initiator", "allowed_techniques": ["outside_trip", "knee_body", "double_leg"]},
        {"id": "wall_pinned", "domain": "clinch", "range": "clinch", "posture": "standing", "dominant_side_role": "initiator", "allowed_techniques": ["cage_plum", "knee_body", "body_hook", "double_leg", "outside_trip"]},
        {"id": "shot_in", "domain": "transition", "range": "close", "posture": "transition", "dominant_side_role": "initiator", "allowed_techniques": ["double_leg", "single_leg", "sprawl"]},
        {"id": "caught_kick_dump", "domain": "transition", "range": "close", "posture": "transition", "dominant_side_role": "initiator", "allowed_techniques": ["sanda_sweep", "outside_trip"]},
        {"id": "closed_guard_bottom", "domain": "ground", "range": "ground", "posture": "ground", "dominant_side_role": "bottom_guard", "allowed_techniques": ["armbar", "escape"]},
        {"id": "half_guard_top", "domain": "ground", "range": "ground", "posture": "ground", "dominant_side_role": "top", "allowed_techniques": ["ride", "escape"]},
        {"id": "side_control", "domain": "ground", "range": "ground", "posture": "ground", "dominant_side_role": "top", "allowed_techniques": ["ride", "armbar", "escape"]},
        {"id": "mount_or_back_ride", "domain": "ground", "range": "ground", "posture": "ground", "dominant_side_role": "top", "allowed_techniques": ["ride", "armbar", "escape"]},
    ]
    transitions = [
        {"from_position": "standing_neutral", "to_position": "caught_single_leg", "via_technique": "kick_catch", "required_grips": ["caught_leg"], "frame_cost": 7, "counters": ["cross", "escape"]},
        {"from_position": "caught_single_leg", "to_position": "side_control", "via_technique": "sanda_sweep", "required_grips": ["caught_leg"], "frame_cost": 14, "counters": ["retreat"]},
        {"from_position": "standing_neutral", "to_position": "collar_tie", "via_technique": "collar_tie", "required_grips": ["collar"], "frame_cost": 11, "counters": ["pummel", "retreat"]},
        {"from_position": "standing_neutral", "to_position": "thai_plum", "via_technique": "collar_tie", "required_grips": ["collar"], "frame_cost": 11, "counters": ["pummel", "double_leg"]},
        {"from_position": "collar_tie", "to_position": "double_underhooks", "via_technique": "pummel", "required_grips": ["underhooks"], "frame_cost": 12, "counters": ["pummel", "knee_body"]},
        {"from_position": "standing_neutral", "to_position": "front_body_lock", "via_technique": "body_lock", "required_grips": ["body_lock"], "frame_cost": 13, "counters": ["pummel", "sprawl"]},
        {"from_position": "front_body_lock", "to_position": "side_control", "via_technique": "outside_trip", "required_grips": ["body_lock"], "frame_cost": 16, "counters": ["sprawl", "pummel"]},
        {"from_position": "standing_neutral", "to_position": "half_guard_top", "via_technique": "double_leg", "required_grips": ["top"], "frame_cost": 18, "counters": ["sprawl", "uppercut"]},
        {"from_position": "standing_neutral", "to_position": "half_guard_top", "via_technique": "single_leg", "required_grips": ["top"], "frame_cost": 16, "counters": ["sprawl", "check"]},
        {"from_position": "collar_tie", "to_position": "closed_guard_bottom", "via_technique": "guard_pull", "required_grips": ["bottom"], "frame_cost": 14, "counters": ["ride"]},
        {"from_position": "half_guard_top", "to_position": "mount_or_back_ride", "via_technique": "ride", "required_grips": ["top"], "frame_cost": 18, "counters": ["escape"]},
        {"from_position": "closed_guard_bottom", "to_position": "side_control", "via_technique": "armbar", "required_grips": ["bottom"], "frame_cost": 22, "counters": ["ride", "escape"]},
        {"from_position": "half_guard_top", "to_position": "standing_neutral", "via_technique": "escape", "required_grips": [], "frame_cost": 17, "counters": ["ride"]},
        {"from_position": "side_control", "to_position": "standing_neutral", "via_technique": "escape", "required_grips": [], "frame_cost": 18, "counters": ["ride"]},
    ]
    return {"version": "block-2", "positions": positions, "transitions": transitions}


def build_model_v2() -> Dict[str, object]:
    from engine.simulator_v2 import ARENA_PRESETS, LANDING_QUALITY_MULT

    return {
        "version": "block-2",
        "fps": 24,
        "lanes": LANES,
        "readiness_weights": {
            "base_readiness": 3.0,
            "guard_weight": 1.0,
            "method_weight": 1.0,
            "stance_weight": 0.9,
        },
        "state_modifiers": {
            "recovery_window_penalty_scale": 1.0,
            "compromised_balance_penalty": -1.1,
            "off_base_balance_penalty": -1.85,
            "outside_angle_penalty": -1.25,
            "open_stance_rear_lane_penalty": -0.55,
            "wall_near_outfight_penalty": -1.40,
            "feint_attention_penalty": -1.15,
            "repeated_move_read_bonus": 0.85,
            "novel_move_surprise_penalty": -0.30,
            "fatigue_per_point_penalty": -0.14,
            "head_damage_reaction_penalty": -0.22,
            "body_damage_high_guard_drop": -0.25,
            "leg_damage_check_and_mobility_penalty": -0.32,
        },
        "landing_multipliers": LANDING_QUALITY_MULT,
        "regional_damage_limits": {
            "head": 11.5,
            "body": 12.0,
            "leg": 12.5,
        },
        "slot_depth_multipliers": {
            "1": 1.15,
            "2": 1.05,
            "3": 1.00,
            "4": 0.95,
        },
        "arena_presets": ARENA_PRESETS,
    }


def build_mio_card_v2() -> Dict[str, object]:
    return {
        "version": "block-2",
        "fighter_id": "sanda_judo",
        "name": "Mio Tsukihara",
        "combat_identity": "Sanda kick-catcher & Judo trip counter",
        "dimensions": {
            "hands": "hands.high_guard",
            "defense": "defense.parry_catch",
            "stance": "stance.balanced",
            "tie": "tie.judo_sambo",
            "target": "target.mixer",
            "kicking": "kicking.sanda",
            "mentality": "mentality.counter",
        },
        "adaptation": "mma",
        "orientation": "orthodox",
        "slot_count": 2,
        "slot_label": "Two-piece",
        "synchronized_capabilities": [
            {
                "id": "sanda_judo.slot.1",
                "capabilities": ["sanda", "kickboxing", "karate"],
                "description": "Trained synchronized bundle: Sanda kick-catching sweep, side kick, and level-mixing kicks",
                "trigger": "fight_start",
                "sequence": ["side_kick", "low_kick", "sanda_sweep", "body_kick", "teep"],
                "home_range": "kick",
                "goal": "counter_trap",
                "abandon_rule": {"max_consecutive_stalls": 2, "condition": "kicks_blocked_or_jammed"},
                "links": ["sanda_judo.slot.2"],
            },
            {
                "id": "sanda_judo.slot.2",
                "capabilities": ["judo", "wrestling", "clinch", "boxing"],
                "description": "Trained synchronized bundle: Judo body-lock outer reap, clinch tie, sprawl defense, and counter boxing",
                "trigger": "slot_stalled_or_close_range",
                "sequence": ["jab", "cross", "body_lock", "outside_trip", "ride"],
                "home_range": "clinch",
                "goal": "takedown_top_control",
                "abandon_rule": {"max_consecutive_stalls": 2, "condition": "clinch_denied_or_escaped"},
                "links": ["sanda_judo.slot.1"],
            },
        ],
        "baseline_capabilities": ["basic_movement", "untrained_striking"],
        "tempo": 3,
        "preferred_ranges": ["kick", "clinch"],
        "debt_sentence": "Catch kicks into a standing sweep or body-lock outer reap; high guard vision and committed sweep recovery leave straight-line seams.",
        "exploitable_seams": [
            "debt.hands.high_guard.body",
            "debt.hands.high_guard.vision",
            "debt.defense.parry_catch.head_hook",
            "debt.defense.parry_catch.body",
            "debt.stance.balanced.tempo",
            "debt.stance.balanced.head_straight",
            "debt.tie.judo_sambo.tempo",
            "debt.tie.judo_sambo.ground",
            "debt.target.mixer.recovery",
            "debt.target.mixer.tempo",
            "debt.kicking.sanda.head_straight",
            "debt.kicking.sanda.recovery",
            "debt.mentality.counter.tempo",
            "debt.mentality.counter.wall",
        ],
        "active_techniques": [
            "step",
            "retreat",
            "pivot",
            "feint",
            "jab",
            "cross",
            "hook",
            "body_hook",
            "uppercut",
            "haymaker",
            "parry",
            "shell_block",
            "slip",
            "check",
            "low_kick",
            "body_kick",
            "teep",
            "side_kick",
            "sanda_sweep",
            "sprawl",
            "pummel",
            "collar_tie",
            "body_lock",
            "outside_trip",
            "ride",
            "escape",
        ],
        "signature_moves": ["sanda_sweep", "outside_trip", "side_kick"],
        "airborne_training": {
            "allowed_vertical_modes": ["grounded", "athletic"],
            "techniques": ["side_kick"],
        },
        "conditional_abilities": [],
        "combat_limitations": [
            "Listed grappling requires the documented range and connection.",
            "No technique is guaranteed against an active defense.",
        ],
        "fighting_description": {
            "does": "Catch kicks into a Sanda sweep or clinch into an outside trip.",
            "wins": "Bait committed kicks or entries, catch or tie up, and dump the opponent to top control.",
            "avoids": "Extended pocket hook exchanges behind a covered high-guard gaze.",
            "beaten_by": "feinted straight-line entries and sustained ground submission specialists.",
        },
        "appearance": {
            "clothing": "crimson Sanda shorts with black sash trim",
            "identity_anchor": "Mio Tsukihara / Sanda kick-catcher & Judo trip counter",
            "props": [],
        },
        "provenance": {
            "classification": "CANON",
            "label": "[CANON]",
            "source": "Authored block-2 worked example card demonstrating Sanda kick-catch and Judo outer reap.",
        },
    }


def build_all_v2_archetype_cards(k: Knowledge) -> Dict[str, Dict[str, object]]:
    """Build explicit block-2 archetype cards for all 11 canonical fighters + Mio Tsukihara (`sanda_judo`)."""
    from engine.simulator_v2 import build_slot_plans

    signature_overrides = {
        "maleek": ["jab", "body_hook", "cross"],
        "donnell": ["hook", "cross", "body_hook"],
        "detroit": ["cross", "uppercut", "jab"],
        "street": ["haymaker", "cross"],
        "thai": ["teep", "body_kick", "knee_body", "low_kick"],
        "wrestler": ["double_leg", "single_leg", "ride"],
        "karate": ["side_kick", "cross", "jab"],
        "greco": ["body_lock", "outside_trip", "collar_tie"],
        "jiujitsu": ["guard_pull", "armbar", "collar_tie"],
        "macklin": ["wall_tie", "wall_punch", "body_hook", "low_kick"],
        "philly": ["cross", "uppercut", "jab"],
    }
    goal_by_cap = {
        "bjj": "submission_finish",
        "wrestling": "takedown_top_control",
        "judo": "takedown_top_control",
        "sanda": "counter_trap",
        "karate": "counter_trap",
        "kickboxing": "leg_attrition",
        "clinch": "clinch_control",
        "wall_boxing": "clinch_control",
        "boxing": "head_damage",
    }

    cards_v2: Dict[str, Dict[str, object]] = {"sanda_judo": build_mio_card_v2()}
    for path in sorted((ROOT / "cards").glob("*.json")):
        base_card = read(path)
        fid = str(base_card["fighter_id"])
        c_v2 = dict(base_card)
        c_v2["version"] = "block-2"

        plans = build_slot_plans(k, base_card, base_card.get("adaptation", "mma"))
        plan_by_id = {p["slot_id"]: p for p in plans}
        new_slots = []
        for idx, slot in enumerate(base_card["synchronized_capabilities"]):
            sid = slot["id"]
            p = plan_by_id.get(sid, plans[idx % len(plans)])
            caps = slot.get("capabilities", [])
            slot_goal = "head_damage"
            if base_card["dimensions"].get("target") == "target.body_puncher" and "boxing" in caps:
                slot_goal = "body_attrition"
            elif base_card["dimensions"].get("mentality") == "mentality.counter" and "boxing" in caps:
                slot_goal = "counter_trap"
            else:
                for cap_key, g_val in goal_by_cap.items():
                    if cap_key in caps:
                        slot_goal = g_val
                        break

            s_copy = dict(slot)
            s_copy["trigger"] = p["trigger"]
            s_copy["sequence"] = list(p["sequence"])
            s_copy["home_range"] = p["home_range"]
            s_copy["goal"] = slot_goal
            s_copy["abandon_rule"] = {
                "max_consecutive_stalls": 2 if len(base_card["synchronized_capabilities"]) > 1 else 99,
                "condition": "sequence_denied_or_countered",
            }
            s_copy["links"] = [p["next_slot_id"]]
            new_slots.append(s_copy)

        c_v2["synchronized_capabilities"] = new_slots
        active_set = set(base_card["active_techniques"])
        sigs = [m for m in signature_overrides.get(fid, []) if m in active_set]
        if not sigs:
            sigs = [m for m in plans[0]["sequence"][:3] if m in active_set]
        c_v2["signature_moves"] = sigs
        has_athletic = any(k_id in active_set for k_id in ("side_kick", "body_kick", "low_kick", "knee_body"))
        c_v2["airborne_training"] = {
            "allowed_vertical_modes": ["grounded", "athletic"] if has_athletic else ["grounded"],
            "techniques": [m for m in ("side_kick", "body_kick", "knee_body") if m in active_set],
        }
        cards_v2[fid] = c_v2

    return cards_v2


def main():
    k = Knowledge()
    opt_beh = build_option_behaviors(k)
    tech_v2 = build_techniques_v2(k)
    pos_map = build_positions_map()
    mod_v2 = build_model_v2()
    all_cards_v2 = build_all_v2_archetype_cards(k)

    # Validate against all v2 schemas before writing
    jsonschema.validate(opt_beh, read(ROOT / "schemas/option_behavior.schema.json"))
    jsonschema.validate(tech_v2, read(ROOT / "schemas/technique_v2.schema.json"))
    jsonschema.validate(pos_map, read(ROOT / "schemas/position_map.schema.json"))
    jsonschema.validate(mod_v2, read(ROOT / "schemas/model_config_v2.schema.json"))

    card_v2_schema = read(ROOT / "schemas/fighter_card_v2.schema.json")
    for fid, card_obj in sorted(all_cards_v2.items()):
        jsonschema.validate(card_obj, card_v2_schema)
        k.card(card_obj)
        write(ROOT / f"cards/v2/{fid}.json", card_obj)

    write(ROOT / "data/option_behaviors.json", opt_beh)
    write(ROOT / "data/techniques_v2.json", tech_v2)
    write(ROOT / "data/positions.json", pos_map)
    write(ROOT / "data/model_v2.json", mod_v2)
    print(f"Successfully built and schema-validated all v2 data files and {len(all_cards_v2)} block-2 archetype cards.")


if __name__ == "__main__":
    main()
