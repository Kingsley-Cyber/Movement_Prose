"""§8. 2-Layer Unrolled Fluid Stack Wording Compiler (gold_master_6 / SAKUGA-MLLM-3.1-CAUSAL format) & V15/V18 Scanners."""

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


def _format_structured_limbs(card: Dict[str, Any], fighter: FighterState) -> str:
    """Build explicit 'L_arm:...; R_arm:... (both arms separate from the torso in silhouette); L_leg:...; R_leg:...' string."""
    lw = fighter.limb_words()
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
        else:
            l_arm_str = other_arm
            r_arm_str = "held wide-right in active guard, clearly separate from the torso"
    else:
        l_leg_str = rear_leg
        r_leg_str = lead_leg
        if card["limb"] in {"lead_hand", "lead_elbow"}:
            r_arm_str = act_words
            l_arm_str = other_arm
        elif card["limb"] in {"rear_hand", "rear_elbow"}:
            r_arm_str = other_arm
            l_arm_str = act_words
        else:
            l_arm_str = other_arm
            r_arm_str = "held wide-right in active guard, clearly separate from the torso"

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

    # Time distribution across 0.00s -> 10.00s
    z_a = 3.20
    for idx, moment in enumerate(moments):
        if idx == 0:
            t_val = 0.0
        elif idx == total_moments - 1:
            t_val = 8.85
        else:
            t_val = round((idx / total_moments) * 8.8, 2)

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
        hold_f = 5 if (is_hero and is_contact) else (3 if is_contact else 0)
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
            a_sup_tag = (
                "NO SUPPORT (airborne)"
                if a_card["post"]["support"] == "airborne"
                else f"SUPPORT both feet planted at z={z_a:.2f} on screen-left ({reach_label} from B at z={z_b:.2f})"
            )
            hold_tag = f" (hold {hold_f}f, Bound)" if (hold_f and a_card["contact"] in {"strike", "grapple"}) else ""
            l1_a = (
                f"{t_val:.2f} A ({frames}f): {a_sup_tag} | {a_limbs_str} | "
                f"FE{fe_num} {a_card['id'].upper()}{hold_tag}: A {a_move_words} across the {sep_m:.2f}m gap."
            )
            layer1_lines.append(l1_a)

            prev_c = f"C{idx:02d}_prev_state" if idx > 0 else "init_stance"
            next_c = f"C{idx+1:02d}_{a_card['id']}"
            a_chain_parts.append(f"C{idx+1:02d}_{a_card['id']}_{t_val:.2f}s")

            # V18: kinetic chain (card default, per-beat override wins) spliced in as
            # the fourth causal segment; chain_frames stays internal timing metadata.
            beat_chain, _beat_chain_frames = _resolve_beat_chain(a_act, a_card, fighter_a)

            a_beat_obj: Dict[str, Any] = {
                "t": t_val,
                "beat": beat_label,
                "causal": build_causal_string(
                    f"C{idx+1:02d}",
                    requires=prev_c,
                    preserves=f"{a_card['post']['coil']}_momentum",
                    chain=beat_chain or "",
                    causes=next_c,
                ),
                "pos": [0, a_y, z_a],
                "vel": [0, 0, 0.3 if a_card["contact"] == "strike" else 0.0],
                "axis": f"head:+Y_up, torso:{a_card['hinge']}_{a_card['path']}, facing:+Z, screen_side:left",
                "arc": f"{a_card['path']}_{a_card['limb']}_at_{sep_m:.2f}m_reach",
                "support": f"{a_card['post']['support']}_on_arena_floor_at_z={z_a:.2f}",
                "limbs": a_limbs_str,
                "pose": (
                    f"At {t_val:.2f}s ({f'hold {hold_f}f' if hold_f else f'{frames}f'}), at {reach_label} "
                    f"with both arms separate from the torso in silhouette, A {a_move_words}."
                ),
            }
            if a_card["contact"] in {"strike", "grapple", "block"} and b_card:
                t_y = LEVEL_TARGET_Y[a_card["level"]]
                t_anat = LEVEL_TARGET_ANATOMY[a_card["level"]]
                if "parry" in a_card["id"] or "tie" in a_card["id"] or "shove" in a_card["id"]:
                    surf = "open_palm_collar_tie"
                elif "calf" in a_card["id"] or "shin" in a_card["id"]:
                    surf = "right_shin_calf_kick"
                elif "back_kick" in a_card["id"] or "heel" in a_card["id"] or "sweep" in a_card["id"]:
                    surf = "right_heel_back_kick"
                else:
                    surf = LIMB_SURFACE_TAG.get(a_card["limb"], a_card["limb"])
                a_beat_obj["contact"] = (
                    f"pre:A_{a_card['id']}_windup -> hit:A_{surf}_into_B_{t_anat}_at_[0,{t_y},{round(z_b - 0.12, 2)}]_at_{sep_m:.2f}m_reach -> "
                    f"post:white_impact_shock_triggers_B_{b_card['id']}"
                )
                if a_card["contact"] == "strike" and a_card["limb"] not in {"lead_knee", "rear_knee"}:
                    smear_start = round(max(0.0, t_val - 0.20), 2)
                    lw = fighter_a.limb_words()
                    smear_limb = lw.get(a_card["limb"], a_card["limb"])
                    smear_frames.append(
                        f"{smear_start}-{t_val}: A {smear_limb} {a_card['path']} strike arc smear only; head, torso, and off-hand guard stay solid"
                    )
                    speed_lines.append(f"{smear_start}-{t_val}")
                    fx_map[str(t_val)] = f"white_impact_shock_flash_and_sweat_spray_on_B_{a_card['level']}_line"
                elif a_card["contact"] == "strike":
                    speed_lines.append(f"{round(max(0.0, t_val - 0.20), 2)}-{t_val}")
                    fx_map[str(t_val)] = f"radial_white_knee_shock_flash_on_B_{a_card['level']}_line"

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
            b_sup_tag = (
                "NO SUPPORT (driven backward)"
                if b_card["post"]["support"] == "supine"
                else f"SUPPORT both feet at z={z_b:.2f} on screen-right ({reach_label} from A at z={z_a:.2f})"
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
                "action": f"{b_card['id']}_at_{t_val:.2f}s",
                "pose": (
                    f"{'only after contact at ' if b_card['class'] == 'IMPACT.REACTION' else 'at '}{t_val:.2f}s ({frames}f), "
                    f"on screen-right at z={z_b:.2f} ({reach_label}) with both arms separate from the torso in silhouette, B {b_move_words}"
                ),
            }
            if b_card["contact"] in {"strike", "grapple", "block"} and a_card:
                t_y = LEVEL_TARGET_Y[b_card["level"]]
                t_anat = LEVEL_TARGET_ANATOMY[b_card["level"]]
                surf_b = "open_palm_parry" if "parry" in b_card["id"] else LIMB_SURFACE_TAG.get(b_card["limb"], b_card["limb"])
                b_entry["contact"] = (
                    f"B_{surf_b} -> into_A_{t_anat}_at_[0,{t_y},{round(z_a + 0.12, 2)}]_at_{sep_m:.2f}m_reach"
                )
                if b_card["contact"] == "strike":
                    smear_start = round(max(0.0, t_val - 0.20), 2)
                    lw_b = fighter_b.limb_words()
                    smear_limb_b = lw_b.get(b_card["limb"], b_card["limb"])
                    smear_frames.append(
                        f"{smear_start}-{t_val}: B {smear_limb_b} {b_card['path']} strike arc smear only; B head, torso, and off-hand guard stay solid"
                    )
                    speed_lines.append(f"{smear_start}-{t_val}")
                    fx_map[str(t_val)] = f"heavy_counter_shock_flash_on_A_{b_card['level']}_line"
            elif a_card and a_card["contact"] in {"strike", "grapple"}:
                t_y = LEVEL_TARGET_Y[a_card["level"]]
                t_anat = LEVEL_TARGET_ANATOMY[a_card["level"]]
                b_entry["contact"] = (
                    f"B_{t_anat} -> struck_by_A_{a_card['id']}_at_[0,{t_y},{round(z_b - 0.12, 2)}]"
                )

            b_track.append(b_entry)
            fighter_b.support = b_card["post"]["support"]
            fighter_b.coil = b_card["post"]["coil"]

        # Camera beat per moment (Decision 21C & Decision 23 compliant)
        is_knee_beat = any(c and c["limb"] in {"lead_knee", "rear_knee"} for c in (a_card, b_card))
        if is_knee_beat:
            shot_name = f"medium_wide_side_profile_{beat_label}"
            cam_fov = 38
        elif is_hero:
            shot_name = f"telephoto_snap_zoom_3_4_{beat_label}"
            cam_fov = 28
        elif is_contact:
            shot_name = f"tight_3_4_front_hemisphere_whip_pan_{beat_label}"
            cam_fov = 32
        else:
            shot_name = f"low_3_4_tracking_dolly_{beat_label}"
            cam_fov = 40

        cam_entry: Dict[str, Any] = {
            "t": t_val,
            "shot": shot_name,
            "fov": cam_fov,
            "pos": [1.55, 0.92, round((z_a + z_b) / 2.0, 2)],
            "look": f"A_on_screen_left_z={z_a:.2f}_and_B_on_screen_right_z={z_b:.2f}_at_{sep_m:.2f}m_separation",
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
