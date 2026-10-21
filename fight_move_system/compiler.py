"""§8. 2-Layer Unrolled Fluid Stack Wording Compiler (sakuga_Xperiment format) & V15/V18 Scanners."""

import json
import re
from typing import Any, Dict, List, Optional, Set, Tuple

from .chain import CHAIN_FRAME_KEY, CHAIN_KEY, build_causal_string, scan_prompt_v18
from .dyad import DyadState
from .enums import RANGE_CAPTION_WORDS
from .lexicon import Lexicon
from .state import FighterState
from .validator import ValidationResult, load_thresholds, validate_clip

# Forbidden franchise / anime trope names (V15)
FORBIDDEN_FRANCHISE_TERMS = {
    "triceratops fist",
    "mach punch",
    "mach straight",
    "cockroach dash",
    "kamehameha",
    "rasengan",
    "gomu gomu",
    "black flash",
}

# Exact z-separation in metres per Dyad range_band so A and B never merge at 0.2m
RANGE_METRES: Dict[str, float] = {
    "outside": 1.35,
    "kick": 1.10,
    "punch": 0.80,
    "pocket": 0.65,
    "clinch": 0.58,
    "ground": 0.85,
}

RANGE_REACH_LABEL: Dict[str, str] = {
    "outside": "beyond kicking reach (1.35m)",
    "kick": "one full leg's length (1.10m)",
    "punch": "one full arm's length (0.80m)",
    "pocket": "half an arm's length (0.65m)",
    "clinch": "chest-to-chest clinch reach (0.58m)",
    "ground": "ground scramble reach (0.85m)",
}

SUPPORT_Y_HEIGHT: Dict[str, float] = {
    "standing": 0.84,
    "crouched": 0.62,
    "clinched": 0.80,
    "kneeling": 0.48,
    "supine": 0.22,
    "prone": 0.22,
    "airborne": 1.22,
}

LEVEL_TARGET_Y: Dict[str, float] = {
    "low": 0.24,
    "mid": 1.08,
    "high": 1.44,
}

LEVEL_TARGET_ANATOMY: Dict[str, str] = {
    "low": "lead_ankle_and_calf",
    "mid": "floating_ribs_and_solar_plexus",
    "high": "jawline_and_chin",
}

LIMB_SURFACE_TAG: Dict[str, str] = {
    "lead_hand": "left_fist_punch",
    "rear_hand": "right_fist_cross",
    "lead_elbow": "left_elbow_and_forearm",
    "rear_elbow": "right_elbow_and_forearm",
    "lead_knee": "left_kneecap",
    "rear_knee": "right_kneecap",
    "lead_leg": "left_shin_and_instep",
    "rear_leg": "right_heel_and_shin",
    "both_hands": "both_hands_and_open_palm_shell",
    "head": "head_slip",
    "hips": "hip_weave",
    "full_body": "full_body",
}


COIL_VISIBLE_PROSE: Dict[str, str] = {
    "neutral": "balanced fighting stance, hips square",
    "loaded_lead": "weight loaded on lead foot, lead hip coiled",
    "loaded_rear": "weight loaded on rear foot, hips coiled back",
    "overcommitted_forward": "torso leaning forward over lead knee",
    "recoiling_back": "weight rocking onto rear heel",
    "spinning_cw": "hips rotating clockwise through back-turned pivot",
    "spinning_ccw": "hips rotating counter-clockwise through back-turned pivot",
    "level_low": "knees bent low in crouched dip",
}

COM_VISIBLE_PROSE: Dict[str, str] = {
    "centered": "center of mass centered between both feet",
    "over_lead_foot": "center of mass stacked over lead foot",
    "over_rear_foot": "center of mass anchored over rear foot",
    "shifted_inside": "center of mass slipped inside the center line",
    "shifted_outside": "center of mass slipped outside the lead shoulder",
    "staggering_off_balance": "center of mass jolted off-balance, staggering to recover",
    "outside_support_falling": "center of mass knocked outside the support base into a fall",
    "airborne_trajectory": "center of mass rising along airborne trajectory",
}

SPECIFIC_CAMERA_LOOK_BY_MOVE: Dict[str, str] = {
    "low_calf_kick": "A_right_shin_chopping_B_lead_left_calf_at_[0,{t_y},{hit_z}]",
    "slashing_rear_elbow": "A_horizontal_right_elbow_slashing_B_brow_at_[0,{t_y},{hit_z}]",
    "lead_elbow_slash": "A_horizontal_left_elbow_slashing_B_brow_at_[0,{t_y},{hit_z}]",
    "lead_liver_hook": "A_left_shovel_hook_digging_into_B_floating_ribs_at_[0,{t_y},{hit_z}]",
    "single_collar_tie": "A_left_palm_clamping_B_neck_in_collar_tie_at_[0,{t_y},{hit_z}]",
    "clinch_rising_knee": "full_body_view_of_A_grounded_left_pillar_leg_and_rising_right_knee_into_B_solar_plexus_at_[0,{t_y},{hit_z}]",
    "knee_strike": "full_body_view_of_A_grounded_left_pillar_leg_and_rising_right_knee_into_B_solar_plexus_at_[0,{t_y},{hit_z}]",
    "two_hand_clinch_shove": "A_two_open_palms_shoving_B_chest_and_B_heels_skidding_to_z={z_b:.2f}",
    "spinning_back_kick": "A_360deg_spinning_right_heel_buried_into_B_solar_plexus_at_[0,{t_y},{hit_z}]",
    "jab": "{attacker}_straight_left_jab_snapping_into_{defender}_chin_at_[0,{t_y},{hit_z}]",
    "body_jab": "{attacker}_low_left_jab_spearing_{defender}_solar_plexus_at_[0,{t_y},{hit_z}]",
    "cross": "{attacker}_straight_right_cross_slamming_{defender}_jawline_at_[0,{t_y},{hit_z}]",
    "rear_body_straight": "{attacker}_right_body_straight_driving_into_{defender}_midsection_at_[0,{t_y},{hit_z}]",
    "lead_hook": "{attacker}_horizontal_left_hook_whipping_across_{defender}_jaw_at_[0,{t_y},{hit_z}]",
    "rear_hook": "{attacker}_compact_right_hook_slamming_{defender}_temple_at_[0,{t_y},{hit_z}]",
    "lead_uppercut": "{attacker}_rising_left_uppercut_lifting_{defender}_chin_at_[0,{t_y},{hit_z}]",
    "rear_uppercut": "{attacker}_rising_right_uppercut_lifting_{defender}_chin_at_[0,{t_y},{hit_z}]",
    "rear_overhand": "{attacker}_looping_right_overhand_crashing_into_{defender}_temple_at_[0,{t_y},{hit_z}]",
    "roundhouse_kick": "{attacker}_horizontal_right_shin_roundhouse_slamming_{defender}_ribs_at_[0,{t_y},{hit_z}]",
    "low_ankle_sweep": "{attacker}_low_spinning_right_heel_sweeping_{defender}_lead_ankle_at_[0,{t_y},{hit_z}]",
}

SPECIFIC_FX_BY_MOVE: Dict[str, str] = {
    "low_calf_kick": "white_bone_shock_flash_and_rain_spray_on_{defender}_left_calf",
    "slashing_rear_elbow": "sharp_crimson_and_white_elbow_slash_flash_and_sweat_spray_on_{defender}_brow",
    "lead_elbow_slash": "sharp_crimson_and_white_elbow_slash_flash_and_sweat_spray_on_{defender}_brow",
    "lead_liver_hook": "visceral_white_liver_hook_shockwave_and_breath_vapor_burst_from_{defender}_floating_ribs",
    "clinch_rising_knee": "radial_white_standing_knee_shock_flash_on_{defender}_solar_plexus",
    "knee_strike": "radial_white_standing_knee_shock_flash_on_{defender}_solar_plexus",
    "two_hand_clinch_shove": "wet_floor_heel_skid_spray_as_{defender}_slides_back",
    "single_collar_tie": "collar_tie_neck_snap_and_sweat_spray_on_{defender}_neck",
    "spinning_back_kick": "double_concentric_white_shockwave_ring_and_rain_mist_explosion_on_{defender}_solar_plexus",
    "jab": "crisp_white_knuckle_shock_flash_and_sweat_beads_on_{defender}_chin",
    "body_jab": "compact_white_solar_plexus_shock_ring_on_{defender}_midsection",
    "cross": "heavy_white_bone_shock_flash_and_sweat_spray_on_{defender}_jawline",
    "rear_body_straight": "deep_white_rib_compression_shock_ring_on_{defender}_midsection",
    "lead_hook": "whipping_white_jaw_shock_flash_and_sweat_arc_from_{defender}_cheek",
    "rear_hook": "heavy_white_temple_shock_flash_and_sweat_spray_on_{defender}_temple",
    "lead_uppercut": "vertical_white_chin_shock_flash_and_upward_sweat_burst_on_{defender}_chin",
    "rear_uppercut": "vertical_white_chin_shock_flash_and_upward_sweat_burst_on_{defender}_chin",
    "rear_overhand": "explosive_double_white_bone_shock_flash_and_sweat_burst_on_{defender}_temple",
    "roundhouse_kick": "heavy_white_shin_shockwave_and_sweat_spray_on_{defender}_ribs",
    "low_ankle_sweep": "low_white_ankle_chop_shock_flash_and_dust_burst_on_{defender}_lead_ankle",
}


def _format_card_text(template: str, fighter: FighterState) -> str:
    lw = fighter.limb_words()
    return template.format(**lw)


def _resolve_beat_chain(
    beat_action: Optional[Dict[str, Any]],
    card: Dict[str, Any],
    fighter: FighterState,
) -> Tuple[Optional[str], Any]:
    """Kinetic chain for one beat: the per-beat override wins over the card default.

    Returns (formatted_chain_text, chain_frames). chain_frames is internal timing
    metadata — callers read it here, and it is never emitted into prompt text.
    """
    override_chain = beat_action.get(CHAIN_KEY) if isinstance(beat_action, dict) else None
    override_frames = beat_action.get(CHAIN_FRAME_KEY) if isinstance(beat_action, dict) else None
    chain = override_chain if override_chain is not None else card.get(CHAIN_KEY)
    frames = override_frames if override_frames is not None else card.get(CHAIN_FRAME_KEY)
    if not isinstance(chain, str) or not chain.strip():
        return None, frames
    return _format_card_text(chain, fighter), frames


def _split_dual_arm_clause(other_arm: str, primary_words: str) -> Tuple[str, str]:
    """Ensure L_arm and R_arm never duplicate a dual-arm clause or assign leg/head moves to L_arm."""
    lower = other_arm.lower()
    if "left" in lower and "right" in lower and "while" in lower:
        parts = re.split(r"\s+while\s+", other_arm, maxsplit=1)
        if len(parts) == 2:
            left_part = parts[0].strip().rstrip(",")
            right_part = re.sub(r",?\s*both arms separate from the torso.*$", "", parts[1].strip())
            if "right" in left_part.lower() and "left" in right_part.lower():
                return right_part, left_part
            return left_part, right_part
    # When other_arm describes both hands/arms ("both fists held high...", "both arms flaring..."),
    # split cleanly into L_arm and R_arm so L_arm never repeats a leg/head/torso action.
    clean_clause = re.sub(
        r",?\s*(?:with\s+)?both\s+(?:gloved\s+)?(?:arms|hands|fists|forearms|elbows|open\s+palms)\s+(?:clearly\s+)?(?:separate|distinct|visible).*$",
        "",
        other_arm.strip(),
        flags=re.IGNORECASE,
    )
    clean_clause = re.sub(
        r",?\s*(?:clearly\s+)?separate from the torso.*$",
        "",
        clean_clause,
        flags=re.IGNORECASE,
    )
    clean_clause = re.sub(
        r"^(?:both\s+(?:gloved\s+)?(?:fists|hands|arms|forearms|elbows|open\s+palms)\s+)",
        "",
        clean_clause,
        flags=re.IGNORECASE,
    ).strip()
    return f"left arm {clean_clause}", f"right arm {clean_clause}"


def _format_structured_limbs(card: Dict[str, Any], fighter: FighterState) -> str:
    """Build explicit 'L_arm:...; R_arm:... (both arms separate from the torso in silhouette); L_leg:...; R_leg:...' string."""
    act_words = _format_card_text(card["caption_words"], fighter)
    other_arm = _format_card_text(card["off_limbs"]["other_arm"], fighter)
    lead_leg = _format_card_text(card["off_limbs"]["lead_leg"], fighter)
    rear_leg = _format_card_text(card["off_limbs"]["rear_leg"], fighter)

    if fighter.stance == "orthodox":
        l_leg_str = lead_leg
        r_leg_str = rear_leg
        if card["limb"] in {"lead_hand", "lead_elbow"}:
            l_arm_str = act_words
            r_arm_str = other_arm
        elif card["limb"] in {"rear_hand", "rear_elbow"}:
            l_arm_str = other_arm
            r_arm_str = act_words
        elif card["limb"] == "both_hands":
            l_arm_str, r_arm_str = _split_dual_arm_clause(other_arm, act_words)
        else:
            l_arm_str, r_arm_str = _split_dual_arm_clause(other_arm, act_words)
    else:
        l_leg_str = rear_leg
        r_leg_str = lead_leg
        if card["limb"] in {"lead_hand", "lead_elbow"}:
            r_arm_str = act_words
            l_arm_str = other_arm
        elif card["limb"] in {"rear_hand", "rear_elbow"}:
            r_arm_str = other_arm
            l_arm_str = act_words
        elif card["limb"] == "both_hands":
            l_arm_str, r_arm_str = _split_dual_arm_clause(other_arm, act_words)
        else:
            l_arm_str, r_arm_str = _split_dual_arm_clause(other_arm, act_words)

    return (
        f"L_arm:{l_arm_str}; R_arm:{r_arm_str} (both arms separate from the torso in silhouette); "
        f"L_leg:{l_leg_str}; R_leg:{r_leg_str}"
    )


def scan_prompt_v15(
    prompt: str,
    clip_regime: str,
    allowed_styles: Set[str],
    lexicon: Lexicon,
    allow_fluid_stack_numbers: bool = False,
) -> List[Tuple[str, str]]:
    """V15: Scan compiled prompt for forbidden franchise names, forbidden positive-prompt negative move lists,
    and out-of-regime / out-of-style move card aliases.
    """
    errors: List[Tuple[str, str]] = []
    lower = prompt.lower()

    if not allow_fluid_stack_numbers:
        digit_match = re.search(r"\d", prompt)
        if digit_match:
            errors.append(("V15", f"Printed prompt contains a forbidden digit '{digit_match.group(0)}'"))
        metric_match = re.search(r"\b(?:metres|meters|metre|meter|cm|mm|deg|degrees|fps)\b", prompt, re.IGNORECASE)
        if metric_match:
            errors.append(("V15", f"Printed prompt contains a forbidden metric unit '{metric_match.group(0)}'"))

    # Franchise names check
    for term in FORBIDDEN_FRANCHISE_TERMS:
        if term in lower:
            errors.append(("V15", f"Printed prompt contains forbidden franchise term '{term}'"))

    # Rule 0.4: No 'no <move>' negative lists in Layer 1 / Header positive prose
    layer1_part = lower.split("=== layer 2:")[0] if "=== layer 2:" in lower else lower
    neg_list_match = re.search(
        r"\bno\s+(?:sweeps|ankle sweeps|kip-ups|flying knees|wall-runs|cartwheels)\b",
        layer1_part,
    )
    if neg_list_match:
        errors.append(
            ("V15", f"Printed positive prompt contains forbidden negative move list '{neg_list_match.group(0)}'")
        )

    # Out-of-regime / out-of-style move card check
    for card_id, card in lexicon.cards_by_id.items():
        legal_in_regime = clip_regime in card["regimes"] or "transition" in card["regimes"]
        legal_in_style = bool(allowed_styles.intersection(set(card["styles"])))
        if not (legal_in_regime and legal_in_style):
            for alias in card["aliases"]:
                if re.search(rf"\b{re.escape(alias.lower())}\b", lower):
                    errors.append(
                        (
                            "V15",
                            f"Printed prompt mentions out-of-regime/style move alias '{alias}' (from card '{card_id}')",
                        )
                    )
    return errors


def compile_to_sakuga_Fluid_stack(
    clip: Dict[str, Any],
    lexicon: Optional[Lexicon] = None,
) -> Tuple[str, Dict[str, Any], ValidationResult]:
    """Compile a validated beat-sheet into the exact gold_master_6 2-Layer Unrolled Fluid Stack format:
      - Header block
      - === LAYER 1: CONTINUOUS SUPPORT, FORCE-EVENT & PROP TIMELINE (Labanotation-as-Words) ===
      - === LAYER 2: SAKUGA-MLLM-3.1-CAUSAL KINEMATIC & CAMERA SCENE GRAPH ===
    Returns (fluid_stack_text, layer2_json_dict, validation_result).
    """
    lex = lexicon or Lexicon.load_default()
    thresh = load_thresholds()
    val_res = validate_clip(clip, lexicon=lex, thresholds=thresh)
    if not val_res.ok:
        return "", {}, val_res

    fighters_cfg = clip.get("fighters", {})
    a_cfg = fighters_cfg.get("A", {})
    b_cfg = fighters_cfg.get("B", {})

    fighter_a = FighterState(
        id="A",
        style=a_cfg.get("style", "boxing"),
        stance=a_cfg.get("stance", "orthodox"),
        screen_side=a_cfg.get("screen_side", "left"),
        facing=a_cfg.get("facing", "right"),
        support=a_cfg.get("support", "standing"),
        coil=a_cfg.get("coil", "neutral"),
    )
    fighter_b = FighterState(
        id="B",
        style=b_cfg.get("style", "boxing"),
        stance=b_cfg.get("stance", "orthodox"),
        screen_side=b_cfg.get("screen_side", "right"),
        facing=b_cfg.get("facing", "left"),
        support=b_cfg.get("support", "standing"),
        coil=b_cfg.get("coil", "neutral"),
    )
    dyad = DyadState(range_band=clip.get("initial_range", "kick"))

    a_desc = a_cfg.get(
        "label",
        "lean, striated martial artist, shirtless bare torso, white cloth tape on both wrists/knuckles, crimson fight trunks, bare feet",
    )
    b_desc = b_cfg.get(
        "label",
        "towering, massive scarred pit-fighter, shirtless broad muscular torso, charcoal-black fight pants, bare wrists and bare ankles with NO tape, bare feet",
    )
    arena = clip.get(
        "arena",
        "floodlit underground concrete-and-resin martial arts tournament platform, harsh cyan-and-golden overhead stadium floodlights, dark tiered arena crowd in deep shadow, no ring ropes",
    )

    # 1. Build Header (gold_master_6 style)
    header = (
        f"10s anime fight clip, 24fps, {arena}. "
        "STYLE: Pure 2D hand-drawn anime, Baki, Kengan Ashura, and God of High School style detailed anatomical muscle striations, "
        "flat cel shading with hard 2-tone high-contrast shadows, heavy ink outlines on A, broken sketchy ink on active smear limbs only, "
        "clean thick ink on impact holds, hyper-fluid bare-knuckle sakuga animation on twos. Not 3D, not CGI, not live action, not photoreal. "
        f"ENTITY COUNT & OUTFIT LOCK: Exactly TWO shirtless bare-knuckle fighters (ZERO weapons). "
        f"Fighter A (always on screen-{fighter_a.screen_side} facing {fighter_a.facing}): {a_desc}. "
        f"Fighter B (always on screen-{fighter_b.screen_side} facing {fighter_b.facing}): {b_desc}. "
        "Maintain realistic strike spacing at all times: one full arm's length (0.75-0.85m) for punches, "
        "half an arm's length (0.60-0.65m) for pocket hooks/uppercuts/clinch, and one full leg's length (1.05-1.15m) for long range "
        "so the bodies never merge, with both arms separate from the torso in silhouette on every hit. "
        "Execute with dynamic 180-degree-hemisphere Sakuga camera work; no on-screen text, no numbers, no HUD, and no coordinate labels."
    )

    moments = clip.get("moments", [])
    total_moments = max(1, len(moments))

    layer1_lines: List[str] = [
        "MOVEMENT LANGUAGE: <seconds> <performer>: SUPPORT (what bears weight; NO SUPPORT = airborne) | bilateral limb placement & torso rotation (both L_arm and R_arm separate from torso in silhouette) | 5-phase force event & reach distance | path in metres. A is always screen-left (crimson trunks, white wrist tape); B is always screen-right (black pants, bare wrists, no tape)."
    ]

    a_beats: List[Dict[str, Any]] = []
    b_track: List[Dict[str, Any]] = []
    camera_track: List[Dict[str, Any]] = []
    impact_frames: List[float] = []
    smear_frames: List[str] = []
    speed_lines: List[str] = []
    fx_map: Dict[str, str] = {}
    beat_names: List[str] = []
    a_chain_parts: List[str] = []
    b_chain_parts: List[str] = []
    rules_sentences: List[str] = []

    # Asymmetric human rhythm across 0.00s -> 10.00s (Fix 6: vary gaps by beat type & frame weight;
    # non-contact steps/slips snap in tight ~0.40s gaps, pocket combinations fire in ~0.55-0.75s,
    # heavy resets/clinch transitions open ~1.0-1.4s breathing windows)
    raw_weights: List[float] = []
    for i in range(total_moments - 1):
        m = moments[i]
        f_cnt = float(m.get("frames", 8))
        ma_act = m.get("A")
        mb_act = m.get("B")
        ma = lex.get(ma_act["move"]) if ma_act else None
        mb = lex.get(mb_act["move"]) if mb_act else None
        has_contact = any(c and c["contact"] in {"strike", "grapple"} for c in (ma, mb))
        has_release = any(c and c["class"] == "GRAPPLE.RELEASE" for c in (ma, mb))
        if not has_contact:
            # Fast feint / footwork / slip entry: tight gap before the strike lands
            w = f_cnt * 0.52
        elif has_release:
            # Shove-break or reset: slightly wider gap as distance opens
            w = f_cnt * 1.15
        elif i % 2 == 0:
            # First hit of a pair: quick follow-up
            w = f_cnt * 0.85
        else:
            # End of exchange pair: natural recovery pause
            w = f_cnt * 1.25
        raw_weights.append(w)

    total_w = sum(raw_weights) if raw_weights else 1.0
    beat_timestamps: List[float] = [0.0]
    acc_w = 0.0
    for i, w in enumerate(raw_weights):
        acc_w += w
        if i == len(raw_weights) - 1:
            beat_timestamps.append(8.85)
        else:
            beat_timestamps.append(round((acc_w / total_w) * 8.85, 2))

    prev_a_lead: Optional[int] = None
    prev_b_lead: Optional[int] = None
    z_a = 3.20
    for idx, moment in enumerate(moments):
        t_val = moment["t"] if "t" in moment else beat_timestamps[idx]

        frames = moment.get("frames", 8)
        is_hero = bool(moment.get("is_hero", idx == total_moments - 1))

        a_act = moment.get("A")
        b_act = moment.get("B")
        a_card = lex.get(a_act["move"]) if a_act else None
        b_card = lex.get(b_act["move"]) if b_act else None

        # Handle overlap preamble state
        a_ov_card = lex.get(a_act["overlaps_move"]) if (a_act and "overlaps_move" in a_act) else None
        b_ov_card = lex.get(b_act["overlaps_move"]) if (b_act and "overlaps_move" in b_act) else None

        sep_m = RANGE_METRES[dyad.range_band]
        reach_label = RANGE_REACH_LABEL[dyad.range_band]
        z_b = round(z_a + sep_m, 2)

        fe_num = idx + 1
        beat_label = f"exchange_{fe_num}_{a_card['id'] if a_card else 'beat'}_vs_{b_card['id'] if b_card else 'beat'}"
        beat_names.append(beat_label)

        is_contact = any(c and c["contact"] in {"strike", "grapple"} for c in (a_card, b_card))
        # V21: derive impact hold frames from spacing_phases['hold'] window when contact occurs
        primary_contact_card = a_card if (a_card and a_card["contact"] in {"strike", "grapple"}) else b_card
        if is_contact and primary_contact_card:
            hold_win = primary_contact_card.get("spacing_phases", {}).get("hold", [4, 6])
            base_hold = max(2, hold_win[1] - hold_win[0])
            hold_f = max(5, base_hold + 2) if is_hero else max(3, base_hold)
        else:
            hold_f = 0
        if is_contact:
            impact_frames.append(t_val)

        # Build Fighter A Layer 1 + Layer 2 A_beats entry
        if a_card:
            a_ov_prefix = ""
            if a_ov_card:
                a_ov_prefix = _format_card_text(a_ov_card["caption_words"], fighter_a) + " then immediately "
                fighter_a.support = a_ov_card["post"]["support"]
                fighter_a.coil = a_ov_card["post"]["coil"]

            a_move_words = a_ov_prefix + _format_card_text(a_card["caption_words"], fighter_a)
            a_limbs_str = _format_structured_limbs(a_card, fighter_a)
            a_y = SUPPORT_Y_HEIGHT.get(a_card["post"]["support"], 0.84)
            a_ws = list(
                a_act.get("weight_split", a_card.get("weight_split", [50, 50]))
                if a_act
                else a_card.get("weight_split", [50, 50])
            )
            a_com = a_act.get("com_position", a_card.get("com_position", "centered")) if a_act else a_card.get("com_position", "centered")
            if prev_a_lead is not None and (not a_act or "weight_split" not in a_act):
                same_dominant_foot = (a_ws[0] > 55 and prev_a_lead > 55) or (a_ws[0] < 45 and prev_a_lead < 45)
                if a_ws[0] == prev_a_lead or same_dominant_foot:
                    # Enforce beat-to-beat weight transfer so the base shifts every beat
                    a_ws = [a_ws[1], a_ws[0]]
                    if a_com == "over_lead_foot":
                        a_com = "over_rear_foot"
                    elif a_com == "over_rear_foot":
                        a_com = "over_lead_foot"
            prev_a_lead = a_ws[0]
            a_easing = a_act.get("easing_curve", a_card.get("easing_curve", "explosive_snap_hold_recoil")) if a_act else a_card.get("easing_curve", "explosive_snap_hold_recoil")
            a_impulse = int(a_act.get("impulse_tier", a_card.get("impulse_tier", 1))) if a_act else int(a_card.get("impulse_tier", 1))
            if is_hero and a_impulse >= 2:
                a_impulse = 3

            # V18: kinetic chain (card default, per-beat override wins) spliced in as
            # Layer 2 fourth causal segment; chain_frames stays internal timing metadata.
            beat_chain, _beat_chain_frames = _resolve_beat_chain(a_act, a_card, fighter_a)

            a_sup_tag = (
                "NO SUPPORT (airborne)"
                if a_card["post"]["support"] == "airborne"
                else f"SUPPORT both feet planted at z={z_a:.2f} on screen-left ({a_ws[0]}/{a_ws[1]} weight, {reach_label} from B at z={z_b:.2f})"
            )
            hold_tag = f" (hold {hold_f}f, Bound)" if (hold_f and a_card["contact"] in {"strike", "grapple"}) else ""
            l1_a = (
                f"{t_val:.2f} A ({frames}f): {a_sup_tag} | {a_limbs_str} | "
                f"FE{fe_num} {a_card['id'].upper()}{hold_tag}: A {a_move_words} across the {sep_m:.2f}m gap."
            )
            layer1_lines.append(l1_a)

            prev_c_code = f"C{idx:02d}_prev_state" if idx > 0 else "init_stance"
            next_c_code = f"C{idx+1:02d}_{a_card['id']}"
            a_chain_parts.append(f"C{idx+1:02d}_{a_card['id']}_{t_val:.2f}s")

            a_beat_obj: Dict[str, Any] = {
                "t": t_val,
                "beat": beat_label,
                "causal": build_causal_string(
                    f"C{idx+1:02d}",
                    requires=prev_c_code,
                    preserves=f"{a_card['post']['coil']}_momentum",
                    chain=beat_chain or "",
                    causes=next_c_code,
                ),
                "pos": [0, a_y, z_a],
                "vel": [0, 0, 0.3 if a_card["contact"] == "strike" else 0.0],
                "axis": f"head:+Y_up, torso:{a_card['hinge']}_{a_card['path']}, facing:+Z, screen_side:left",
                "arc": f"{a_card['path']}_{a_card['limb']}_at_{sep_m:.2f}m_reach",
                "support": f"{a_card['post']['support']}_on_arena_floor_at_z={z_a:.2f}",
                "weight_split": a_ws,
                "com_position": a_com,
                "easing_curve": a_easing,
                "impulse_tier": a_impulse,
                "limbs": a_limbs_str,
                "pose": (
                    f"At {t_val:.2f}s ({f'hold {hold_f}f' if hold_f else f'{frames}f'}), at {reach_label} "
                    f"with both arms separate from the torso in silhouette, A {a_move_words}."
                ),
            }
            if a_card["contact"] in {"strike", "grapple", "block"} and b_card:
                t_y = LEVEL_TARGET_Y[a_card["level"]]
                t_anat = LEVEL_TARGET_ANATOMY[a_card["level"]]
                hit_z = round(z_b - 0.12, 2)
                if "parry" in a_card["id"] or "tie" in a_card["id"] or "shove" in a_card["id"]:
                    surf = "open_palm_collar_tie"
                elif "calf" in a_card["id"]:
                    surf = "right_shin_calf_kick"
                elif "back_kick" in a_card["id"] or "heel" in a_card["id"] or "sweep" in a_card["id"]:
                    surf = "right_heel_back_kick"
                else:
                    surf = LIMB_SURFACE_TAG.get(a_card["limb"], a_card["limb"])
                a_beat_obj["contact"] = (
                    f"pre:A_{a_card['id']}_windup -> hit:A_{surf}_into_B_{t_anat}_at_[0,{t_y},{hit_z}]_at_{sep_m:.2f}m_reach -> "
                    f"post:white_impact_shock_triggers_B_{b_card['id']}"
                )
                # V21: Compute smear window from spacing_phases['snap'] window at 24fps
                snap_win = a_card.get("spacing_phases", {}).get("snap", [1, 4])
                snap_dur_s = round(max(2, snap_win[1] - snap_win[0]) / 24.0, 2)
                if t_val == 0.0:
                    smear_start = 0.0
                    smear_end = snap_dur_s
                else:
                    smear_start = round(max(0.0, t_val - snap_dur_s), 2)
                    smear_end = t_val
                if a_card["contact"] in {"strike", "grapple"}:
                    fx_template = SPECIFIC_FX_BY_MOVE.get(
                        a_card["id"],
                        f"white_bone_shock_flash_and_sweat_spray_on_{{defender}}_{a_card['level']}_line",
                    )
                    fx_map[str(t_val)] = fx_template.format(attacker="A", defender="B")
                if a_card["contact"] == "strike" and a_card["limb"] not in {"lead_knee", "rear_knee"}:
                    lw = fighter_a.limb_words()
                    smear_limb = lw.get(a_card["limb"], a_card["limb"])
                    smear_frames.append(
                        f"{smear_start}-{smear_end}: A {smear_limb} {a_card['path']} strike arc smear only ({a_easing}); head, torso, and off-hand guard stay solid"
                    )
                    speed_lines.append(f"{smear_start}-{smear_end}")
                elif a_card["contact"] == "strike":
                    speed_lines.append(f"{smear_start}-{smear_end}")

            a_beats.append(a_beat_obj)
            fighter_a.support = a_card["post"]["support"]
            fighter_a.coil = a_card["post"]["coil"]

        # Build Fighter B Layer 1 + Layer 2 B_track entry
        if b_card:
            b_ov_prefix = ""
            if b_ov_card:
                b_ov_prefix = _format_card_text(b_ov_card["caption_words"], fighter_b) + " then immediately "
                fighter_b.support = b_ov_card["post"]["support"]
                fighter_b.coil = b_ov_card["post"]["coil"]

            b_move_words = b_ov_prefix + _format_card_text(b_card["caption_words"], fighter_b)
            b_limbs_str = _format_structured_limbs(b_card, fighter_b)
            b_y = SUPPORT_Y_HEIGHT.get(b_card["post"]["support"], 0.96)
            b_ws = list(
                b_act.get("weight_split", b_card.get("weight_split", [50, 50]))
                if b_act
                else b_card.get("weight_split", [50, 50])
            )
            b_com = b_act.get("com_position", b_card.get("com_position", "centered")) if b_act else b_card.get("com_position", "centered")
            if prev_b_lead is not None and (not b_act or "weight_split" not in b_act):
                same_dominant_b = (b_ws[0] > 55 and prev_b_lead > 55) or (b_ws[0] < 45 and prev_b_lead < 45)
                if b_ws[0] == prev_b_lead or same_dominant_b:
                    b_ws = [b_ws[1], b_ws[0]]
                    if b_com == "over_lead_foot":
                        b_com = "over_rear_foot"
                    elif b_com == "over_rear_foot":
                        b_com = "over_lead_foot"
            prev_b_lead = b_ws[0]
            b_easing = b_act.get("easing_curve", b_card.get("easing_curve", "sudden_jolt_settle")) if b_act else b_card.get("easing_curve", "sudden_jolt_settle")
            b_impulse = int(b_act.get("impulse_tier", b_card.get("impulse_tier", 1))) if b_act else int(b_card.get("impulse_tier", 1))
            if is_hero and b_impulse >= 2:
                b_impulse = 3

            b_sup_tag = (
                "NO SUPPORT (driven backward)"
                if b_card["post"]["support"] == "supine"
                else f"SUPPORT both feet at z={z_b:.2f} on screen-right ({b_ws[0]}/{b_ws[1]} weight, {reach_label} from A at z={z_a:.2f})"
            )
            hold_tag_b = f" (hold {hold_f}f, Bound)" if (hold_f and b_card["contact"] in {"strike", "grapple"}) else ""
            l1_b = (
                f"{t_val:.2f} B ({frames}f): {b_sup_tag} | {b_limbs_str} | "
                f"FE{fe_num} {b_card['id'].upper()}{hold_tag_b}: B {b_move_words}."
            )
            layer1_lines.append(l1_b)
            b_chain_parts.append(f"C{idx+1:02d}_{b_card['id']}_{t_val:.2f}s")

            b_entry: Dict[str, Any] = {
                "t": t_val,
                "pos": [0, b_y, z_b],
                "axis": f"head:+Y_up, torso:{b_card['id']}, facing:-Z, screen_side:right",
                "support": f"{b_card['post']['support']}_on_floor_at_z={z_b:.2f}",
                "weight_split": b_ws,
                "com_position": b_com,
                "easing_curve": b_easing,
                "impulse_tier": b_impulse,
                "action": f"{b_card['id']}_at_{t_val:.2f}s",
                "pose": (
                    f"{'only after contact at ' if b_card['class'] == 'IMPACT.REACTION' else 'at '}{t_val:.2f}s ({frames}f), "
                    f"on screen-right at z={z_b:.2f} ({reach_label}) "
                    f"with both arms separate from the torso in silhouette, B {b_move_words}"
                ),
            }
            if b_card["contact"] in {"strike", "grapple", "block"} and a_card:
                t_y = LEVEL_TARGET_Y[b_card["level"]]
                t_anat = LEVEL_TARGET_ANATOMY[b_card["level"]]
                hit_z_b = round(z_a + 0.12, 2)
                surf_b = "open_palm_parry" if "parry" in b_card["id"] else LIMB_SURFACE_TAG.get(b_card["limb"], b_card["limb"])
                b_entry["contact"] = (
                    f"B_{surf_b} -> into_A_{t_anat}_at_[0,{t_y},{hit_z_b}]_at_{sep_m:.2f}m_reach"
                )
                if b_card["contact"] == "strike":
                    snap_win_b = b_card.get("spacing_phases", {}).get("snap", [1, 4])
                    snap_dur_b = round(max(2, snap_win_b[1] - snap_win_b[0]) / 24.0, 2)
                    smear_start = round(max(0.0, t_val - snap_dur_b), 2)
                    lw_b = fighter_b.limb_words()
                    smear_limb_b = lw_b.get(b_card["limb"], b_card["limb"])
                    smear_frames.append(
                        f"{smear_start}-{t_val}: B {smear_limb_b} {b_card['path']} strike arc smear only ({b_easing}); B head, torso, and off-hand guard stay solid"
                    )
                    speed_lines.append(f"{smear_start}-{t_val}")
                    fx_template_b = SPECIFIC_FX_BY_MOVE.get(
                        b_card["id"],
                        f"heavy_counter_bone_shock_flash_on_{{defender}}_{b_card['level']}_line",
                    )
                    if a_card and a_card["class"] in {"BLOCK.PASSIVE", "BLOCK.ACTIVE"}:
                        if "shell" in a_card["id"]:
                            fx_map[str(t_val)] = "heavy_counter_shock_ring_rippling_off_A_twin_forearm_shell"
                        elif "elbow" in a_card["id"]:
                            fx_map[str(t_val)] = "compact_forearm_block_shock_ring_on_A_left_rib_line"
                        else:
                            fx_map[str(t_val)] = fx_template_b.format(attacker="B", defender="A")
                    else:
                        fx_map[str(t_val)] = fx_template_b.format(attacker="B", defender="A")
            elif a_card and a_card["contact"] in {"strike", "grapple"}:
                t_y = LEVEL_TARGET_Y[a_card["level"]]
                t_anat = LEVEL_TARGET_ANATOMY[a_card["level"]]
                b_entry["contact"] = (
                    f"B_{t_anat} -> struck_by_A_{a_card['id']}_at_[0,{t_y},{round(z_b - 0.12, 2)}]"
                )

            b_track.append(b_entry)
            fighter_b.support = b_card["post"]["support"]
            fighter_b.coil = b_card["post"]["coil"]

        # Camera beat per moment (Decision 21C & Decision 23 compliant + Specific Action Look & Level Height)
        is_knee_beat = any(c and c["limb"] in {"lead_knee", "rear_knee"} for c in (a_card, b_card))
        active_strike_card = a_card if (a_card and a_card["contact"] in {"strike", "grapple"}) else (
            b_card if (b_card and b_card["contact"] in {"strike", "grapple"}) else a_card
        )
        attacker_id = "A" if (a_card and a_card["contact"] in {"strike", "grapple"}) else (
            "B" if (b_card and b_card["contact"] in {"strike", "grapple"}) else "A"
        )
        defender_id = "B" if attacker_id == "A" else "A"
        strike_level = active_strike_card["level"] if active_strike_card else "high"
        t_y_cam = LEVEL_TARGET_Y.get(strike_level, 1.08)
        hit_z_cam = round(z_b - 0.12, 2) if attacker_id == "A" else round(z_a + 0.12, 2)

        if is_knee_beat:
            shot_name = f"medium_wide_side_profile_{beat_label}"
            cam_fov = 38
            cam_pos = [1.75, 0.92, round((z_a + z_b) / 2.0, 2)]
        elif is_hero:
            shot_name = f"telephoto_snap_zoom_3_4_{beat_label}"
            cam_fov = 28
            cam_pos = [1.45, 0.92, round((z_a + z_b) / 2.0, 2)]
        elif is_contact:
            if strike_level == "low":
                shot_name = f"low_3_4_shin_level_tracking_{beat_label}"
                cam_fov = 34
                cam_pos = [1.45, 0.65, round((z_a + z_b) / 2.0, 2)]
            elif strike_level == "mid":
                shot_name = f"low_3_4_upward_rib_angle_{beat_label}"
                cam_fov = 34
                cam_pos = [1.42, 0.78, round((z_a + z_b) / 2.0, 2)]
            else:
                shot_name = f"tight_3_4_front_hemisphere_whip_pan_{beat_label}"
                cam_fov = 34
                cam_pos = [1.40, 1.15, round((z_a + z_b) / 2.0, 2)]
        else:
            shot_name = f"low_3_4_tracking_dolly_{beat_label}"
            cam_fov = 40
            cam_pos = [1.65, 0.95, round((z_a + z_b) / 2.0, 2)]

        if is_contact and active_strike_card:
            look_tmpl = SPECIFIC_CAMERA_LOOK_BY_MOVE.get(
                active_strike_card["id"],
                "{attacker}_{move}_striking_{defender}_at_[0,{t_y},{hit_z}]",
            )
            cam_look = look_tmpl.format(
                attacker=attacker_id,
                defender=defender_id,
                move=active_strike_card["id"],
                t_y=t_y_cam,
                hit_z=hit_z_cam,
                z_a=z_a,
                z_b=z_b,
            )
        else:
            cam_look = f"A_closing_pocket_distance_on_screen_left_z={z_a:.2f}_toward_B_on_screen_right_z={z_b:.2f}"

        cam_entry: Dict[str, Any] = {
            "t": t_val,
            "shot": shot_name,
            "fov": cam_fov,
            "pos": cam_pos,
            "look": cam_look,
            "preserve_axis": True,
        }
        if is_contact and not is_knee_beat:
            cam_entry["dutch_roll_deg"] = -10 if idx % 2 == 0 else 8
        if hold_f:
            cam_entry["hold_frames"] = hold_f
            cam_entry["effect"] = "camera_shake_impact_shock_flash"
            if is_hero:
                cam_entry["time_remap"] = 0.25
        else:
            cam_entry["move"] = "smooth_lateral_dolly_tracking_footwork, no_orbit"
        camera_track.append(cam_entry)

        rules_sentences.append(
            f"At {t_val:.2f}s ({reach_label}), "
            f"A {a_move_words if a_card else 'holds guard'} while B {b_move_words if b_card else 'holds guard'}"
            f"{f' (hold {hold_f}f)' if hold_f else ''}."
        )

        # Update dyad range for next moment
        for card in (a_card, b_card):
            if card and card["post"].get("range_delta", "same") != "same":
                dyad.apply_range_delta(card["post"]["range_delta"])
                break

    # Final t=10.0s hold beat so duration==10.0 is locked
    final_sep = RANGE_METRES[dyad.range_band]
    final_zb = round(z_a + final_sep, 2)
    layer1_lines.append(
        f"10.00 A (10f): SUPPORT wide fighting stance held still at z={z_a:.2f} on screen-left | "
        "L_arm extended forward in high guard, R_arm chambered at cheek, both arms separate from torso in silhouette | "
        "follow-through hold to 10.00s."
    )
    layer1_lines.append(
        f"10.00 B (10f): SUPPORT {fighter_b.support} at z={final_zb:.2f} on screen-right | "
        "both arms separate from torso in silhouette | final state hold to 10.00s."
    )
    a_beats.append(
        {
            "t": 10.0,
            "beat": beat_names[-1],
            "causal": f"C{total_moments+1:02d}_hold: maintains post_finisher_stance_to_10s",
            "pos": [0, SUPPORT_Y_HEIGHT.get(fighter_a.support, 0.84), z_a],
            "vel": [0, 0, 0],
            "axis": "head:+Y_up_level, torso:still_wide_martial_stance, facing:+Z, screen_side:left",
            "arc": "static_follow_through_hold",
            "support": f"{fighter_a.support}_on_floor_at_z={z_a:.2f}",
            "limbs": "L_arm:extended forward in high guard; R_arm:chambered at right cheek (both arms separate from the torso in silhouette); L_leg:planted forward; R_leg:anchored back",
            "pose": f"At 10.00s, A holds his wide fighting stance at z={z_a:.2f} on screen-left with both arms separate from the torso in silhouette.",
        }
    )
    b_track.append(
        {
            "t": 10.0,
            "pos": [0, SUPPORT_Y_HEIGHT.get(fighter_b.support, 0.22), final_zb],
            "axis": f"head:+Y_up, spine:{fighter_b.support}, facing:-Z, screen_side:right",
            "support": f"{fighter_b.support}_on_floor_at_z={final_zb:.2f}",
            "action": f"final_{fighter_b.support}_hold_to_10s",
            "pose": f"At 10.00s, B remains in {fighter_b.support} state at z={final_zb:.2f} on screen-right.",
        }
    )

    style_map = {
        "boxing": "grounded_striker_boxer_baki",
        "baki": "grounded_striker_boxer_baki",
        "mma": "ufc_mma_octagon",
        "muay_thai": "muay_thai_nak_muay",
        "freestyle_sakuga": "acrobatic_multidomain_freestyle",
    }

    spec: Dict[str, Any] = {
        "name": clip.get("clip_id", "fight_move_system_compiled_10s"),
        "schema": "sakuga_Xperiment",
        "fps": 24,
        "duration": 10.0,
        "axes": f"Y_up, metres, arena floor y=0, combat pocket z=2.8 to z=5.0, A stays on screen_{fighter_a.screen_side} facing +Z right for all 10s, B stays on screen_{fighter_b.screen_side} facing -Z left for all 10s",
        "screen_geometry": (
            f"180_degree_camera_hemisphere_locked_for_all_10s: Fighter A remains strictly on screen_{fighter_a.screen_side} facing {fighter_a.facing} (+Z) "
            f"and Fighter B remains strictly on screen_{fighter_b.screen_side} facing {fighter_b.facing} (-Z) for the entire 10.0s clip (zero side swaps)."
        ),
        "negative": (
            "no 3D CGI, no mocap stiffness, no floaty physics, no static flat camera, no weapons, no swords, no knives, "
            "no side swap, no outfit swap, no torso merging, no chest-to-chest clipping, no on-screen text or numbers, "
            "no HUD, no coordinate labels, no extra fighters, no missing limbs, no missing arms, no one-armed fighter, "
            "no extra legs, no deformed legs, no full-body blur during smears, no reaction before contact"
        ),
        "conservation_laws": [
            "CONSERVE_SEMANTICALLY: every strike, evade, block, and counter is chained so the post-coil of Beat N physically loads the pre-coil of Beat N+1",
            "realistic_strike_reach_spacing: punches connect at one full arm's length (0.75-0.85m), pocket hooks/uppercuts at half an arm's length (0.60-0.65m), and kicks at one full leg's length (1.05-1.15m) with both arms separate from the torso in silhouette",
            f"strict_screen_side_and_outfit_lock: A stays on screen_{fighter_a.screen_side} facing {fighter_a.facing} and B stays on screen_{fighter_b.screen_side} facing {fighter_b.facing} for all 10.0 seconds",
            "knockback_and_hit_reaction_require_prior_physical_contact_zero_early_flinch",
        ],
        "laban": {
            "A": {
                "fighting_style": style_map.get(fighter_a.style, "grounded_striker_boxer_baki"),
                "chain": " > ".join(a_chain_parts),
                "effort": {"weight": "heavy_striker_power", "time": "sudden", "space": "direct", "flow": "bound"},
            },
            "B": {
                "fighting_style": style_map.get(fighter_b.style, "grounded_striker_boxer_baki"),
                "chain": " > ".join(b_chain_parts),
                "effort": {"weight": "heavy_brawler_power", "time": "sudden", "space": "direct", "flow": "bound"},
            },
        },
        "beats": beat_names,
        "A_beats": a_beats,
        "B_track": b_track,
        "camera": camera_track,
        "anime": {
            "style": "2D cel-shaded hand-drawn anime, Baki, Kengan Ashura, and God of High School style detailed anatomical muscle striations, hard 2-tone high-contrast shadows, heavy ink outlines on A, broken sketchy ink on active smear limbs only, clean thick ink on impact holds",
            "impact_frames": impact_frames,
            "smear_frames": smear_frames,
            "speed_lines": speed_lines,
            "time_remap": {f"{round(impact_frames[-1]-0.05, 2)}-9.1": 0.25} if impact_frames else {},
            "anticipation_holds": [0.0],
            "fx": fx_map,
            "line_rule": f"heavy anatomical ink outlines on A and B, broken/sketchy outlines ONLY on active smear limbs, ultra-thick clean ink on all held impact frames {impact_frames}",
            "chromatic_aberration": f"impact_frames_only {impact_frames} — keep all transition frames razor-sharp with zero chromatic aberration",
        },
        "rules": (
            "Render as one continuous 10-second 2D hand-drawn bare-knuckle martial arts fight on the tournament platform. "
            f"OUTFIT & SIDE LOCK: Fighter A stays on screen-{fighter_a.screen_side} facing {fighter_a.facing} (+Z) and Fighter B stays on screen-{fighter_b.screen_side} facing {fighter_b.facing} (-Z) for all 10.0 seconds (zero side swaps, zero weapons). "
            "Maintain realistic strike reach at all times with both arms separate from the torso in silhouette on every hit. "
            + " ".join(rules_sentences)
            + " Pure 2D cel-shaded anime, no 3D CGI, no on-screen text or numbers."
        ),
    }

    # Format Layer 2 JSON for sakuga_Xperiment
    lines: List[str] = ["{"]
    lines.append(
        f'"name":{json.dumps(spec["name"])},"schema":"sakuga_Xperiment","fps":24,"duration":10.0,'
    )
    for k in ["axes", "screen_geometry", "negative"]:
        lines.append(f"{json.dumps(k)}:{json.dumps(spec[k])},")
    lines.append('"conservation_laws":[')
    for i, law in enumerate(spec["conservation_laws"]):
        comma = "," if i < len(spec["conservation_laws"]) - 1 else ""
        lines.append(f"{json.dumps(law)}{comma}")
    lines.append("],")
    lines.append('"laban":{')
    lines.append(f'"A":{json.dumps(spec["laban"]["A"], separators=(",", ":"))},')
    lines.append(f'"B":{json.dumps(spec["laban"]["B"], separators=(",", ":"))}' + "},")
    lines.append(f'"beats":{json.dumps(spec["beats"], separators=(",", ":"))},')
    for tk in ["A_beats", "B_track", "camera"]:
        lines.append(f"{json.dumps(tk)}:[")
        items = spec[tk]
        for i, item in enumerate(items):
            comma = "," if i < len(items) - 1 else ""
            lines.append(f"{json.dumps(item, separators=(',', ':'))}{comma}")
        lines.append("],")
    lines.append('"anime":{')
    akeys = list(spec["anime"].keys())
    for i, ak in enumerate(akeys):
        is_last = i == len(akeys) - 1
        if ak == "smear_frames":
            lines.append('"smear_frames":[')
            for j, s_item in enumerate(spec["anime"][ak]):
                scomma = "," if j < len(spec["anime"][ak]) - 1 else ""
                lines.append(f"{json.dumps(s_item)}{scomma}")
            lines.append("]}," if is_last else "],")
        else:
            val_str = json.dumps(spec["anime"][ak], separators=(",", ":"))
            lines.append(f"{json.dumps(ak)}:{val_str}{'},' if is_last else ','}")
    lines.append(f'"rules":{json.dumps(spec["rules"])}')
    lines.append("}")
    layer2_block = "\n".join(lines)

    layer1_block = "\n".join(layer1_lines)
    fluid_stack_prompt = (
        f"{header}\n\n"
        f"=== LAYER 1: CONTINUOUS SUPPORT, FORCE-EVENT & PROP TIMELINE (Labanotation-as-Words) ===\n"
        f"{layer1_block}\n\n"
        f"=== LAYER 2: sakuga_Xperiment KINEMATIC & CAMERA SCENE GRAPH ===\n"
        f"{layer2_block}"
    )

    clip_regime = clip.get("regime", "standup_striking")
    allowed_styles = {fighter_a.style, fighter_b.style}
    v15_errs = scan_prompt_v15(
        fluid_stack_prompt,
        clip_regime,
        allowed_styles,
        lex,
        allow_fluid_stack_numbers=True,
    )
    if v15_errs:
        val_res.errors.extend(v15_errs)
        return "", {}, val_res

    # V18: chain segments stay link-valid, '>' never escapes a chain, and the
    # internal chain_frames offsets never leak into the emitted prompt.
    v18_errs = scan_prompt_v18(fluid_stack_prompt)
    if v18_errs:
        val_res.errors.extend(v18_errs)
        return "", {}, val_res

    return fluid_stack_prompt, spec, val_res


def compile_clip_prompt(
    clip: Dict[str, Any],
    lexicon: Optional[Lexicon] = None,
) -> Tuple[str, ValidationResult]:
    """Default entrypoint: compiles the validated clip into the gold_master_6 2-Layer Unrolled Fluid Stack format."""
    prompt, _, res = compile_to_sakuga_Fluid_stack(clip, lexicon=lexicon)
    return prompt, res
