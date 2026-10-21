"""§3. Closed vocabularies (strict enums) for Fight Move System."""

from typing import Dict, Set

STANCES: Set[str] = {"orthodox", "southpaw"}

SCREEN_SIDES: Set[str] = {"left", "right"}

FACINGS: Set[str] = {"left", "right"}

SUPPORT_BASES: Set[str] = {
    "standing",
    "crouched",
    "airborne",
    "kneeling",
    "supine",
    "prone",
    "clinched",
}

RANGE_BANDS: Set[str] = {
    "outside",
    "kick",
    "punch",
    "pocket",
    "clinch",
    "ground",
}

# Ordered range bands from farthest to closest for deterministic step_closer / step_further
RANGE_ORDER = ["outside", "kick", "punch", "pocket", "clinch", "ground"]

RANGE_CAPTION_WORDS: Dict[str, str] = {
    "outside": "beyond kicking reach, a full stride apart",
    "kick": "at a full leg's length apart",
    "punch": "at a full arm's length apart",
    "pocket": "half an arm's length apart in close pocket range",
    "clinch": "chest to chest in a tight clinch",
    "ground": "tangled at canvas level",
}

RANGE_DELTAS: Set[str] = {
    "same",
    "close_one",
    "open_one",
    "to_clinch",
    "to_punch",
    "to_kick",
    "to_ground",
}

REGIMES: Set[str] = {
    "standup_striking",
    "clinch",
    "ground",
    "transition",
}

STYLES: Set[str] = {
    "boxing",
    "muay_thai",
    "mma",
    "baki",
    "freestyle_sakuga",
}

COILS: Set[str] = {
    "neutral",
    "loaded_lead",
    "loaded_rear",
    "overcommitted_forward",
    "recoiling_back",
    "spinning_cw",
    "spinning_ccw",
    "level_low",
}

GUARDS: Set[str] = {
    "high",
    "low",
    "framing",
    "clinching",
    "striking",
    "occupied",
}

LIMBS: Set[str] = {
    "lead_hand",
    "rear_hand",
    "lead_elbow",
    "rear_elbow",
    "lead_knee",
    "rear_knee",
    "lead_leg",
    "rear_leg",
    "head",
    "hips",
    "both_hands",
    "full_body",
}

HINGES: Set[str] = {
    "shoulder_extension",
    "elbow_flex",
    "hip_whip",
    "knee_drive",
    "ankle_pivot",
    "spine_arch",
    "full_body_drop",
}

PATHS: Set[str] = {
    "straight",
    "arc_horizontal",
    "arc_vertical",
    "full_rotation",
    "ground_arc",
    "downward",
    "push",
    "none",
}

LEVELS: Set[str] = {
    "low",
    "mid",
    "high",
}

CONTACTS: Set[str] = {
    "strike",
    "grapple",
    "evade",
    "block",
    "none",
}

FORCE_LOCAL: Set[str] = {
    "forward_straight",
    "arc_lead_to_rear",
    "arc_rear_to_lead",
    "upward",
    "downward",
    "pull_inward",
    "none",
}

FORCE_CAMERA: Set[str] = {
    "toward_screen_left",
    "toward_screen_right",
    "toward_camera",
    "away_from_camera",
    "upward",
    "downward",
    "none",
}

BLEED_TIERS: Set[int] = {1, 2, 3}

# Impulse / Reaction strength tiers (V22): 0=none, 1=light/jab, 2=medium/committed, 3=heavy/knockout
IMPULSE_TIERS: Set[int] = {0, 1, 2, 3}

# Spacing / Easing Curve Profiles (V21)
EASING_CURVES: Set[str] = {
    "slow_in_snap_hold_ease_out",
    "explosive_snap_hold_recoil",
    "coil_whip_hold_settle",
    "smooth_ease_in_out",
    "sudden_jolt_settle",
}

# Center-of-mass positions relative to support base (V19)
COM_POSITIONS: Set[str] = {
    "centered",
    "over_lead_foot",
    "over_rear_foot",
    "shifted_inside",
    "shifted_outside",
    "outside_support_falling",
    "airborne_trajectory",
}

# Camera Angle Visibility / Occlusion Table (V20)
# Maps camera shot archetype substrings to fighter-local limbs that risk occlusion
CAMERA_OCCLUSION_TABLE: Dict[str, Set[str]] = {
    "worm_eye": {"hips", "lead_leg", "rear_leg"},
    "extreme_close_up_head": {"lead_leg", "rear_leg", "lead_knee", "rear_knee", "hips"},
    "over_B_right_shoulder": {"lead_hand", "lead_elbow"},
    "over_A_left_shoulder": {"rear_hand", "rear_elbow"},
    "flat_90deg_profile": {"rear_hand", "rear_elbow"},
}

MOVE_CLASSES: Set[str] = {
    "STRIKE.LINEAR",
    "STRIKE.ARC_HORIZ",
    "STRIKE.ARC_VERT",
    "STRIKE.FULL_ROT",
    "STRIKE.DOWNWARD",
    "THROW.PROJECT",
    "TAKEDOWN.LEG",
    "SWEEP.LOW_ROT",
    "EVADE.SLIP",
    "EVADE.ROOT",
    "EVADE.LEVEL",
    "BLOCK.PASSIVE",
    "BLOCK.ACTIVE",
    "GRAPPLE.ATTACH",
    "GRAPPLE.MAINTAIN",
    "GRAPPLE.RELEASE",
    "LOCOMOTION.APPROACH",
    "LOCOMOTION.RETREAT",
    "LOCOMOTION.CIRCLE",
    "RECOVERY.STAND",
    "RECOVERY.RESET",
    "IMPACT.REACTION",
}

EFFORT_WEIGHT: Set[str] = {"light", "strong"}
EFFORT_TIME: Set[str] = {"sustained", "sudden"}
EFFORT_SPACE: Set[str] = {"direct", "indirect"}
EFFORT_FLOW: Set[str] = {"bound", "free"}
