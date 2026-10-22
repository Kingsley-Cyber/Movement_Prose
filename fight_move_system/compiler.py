"""§8. 2-Layer Unrolled Fluid Stack Wording Compiler (`sakuga_Xperiment` & `lean` modes), KB-Prior Integration & V15/V18 Scanners."""

import json
import re
from typing import Any, Dict, List, Optional, Set, Tuple

from .chain import CHAIN_FRAME_KEY, CHAIN_KEY, build_causal_string, scan_prompt_v18
from .dyad import DyadState
from .kb_bridge import (
    query_kb_prior_to_semantic_intent,
    record_compile_usage,
    resolve_beat_kb_guidance,
)
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
    "outside_support_falling": "center of mass knocked outside the support base into a fall",
    "airborne_trajectory": "center of mass rising along airborne trajectory",
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
            right_part = re.sub(r",?\s*both arms.*$", "", parts[1].strip())
            if "right" in left_part.lower() and "left" in right_part.lower():
                return right_part, left_part
            return left_part, right_part

    # Strip leading "both hands/arms/fists..." BEFORE stripping trailing ", both arms separate..."
    clean_clause = re.sub(r",?\s*clearly separate from the torso.*$", "", other_arm.strip())
    clean_clause = re.sub(
        r"^(?:both\s+(?:gloved\s+)?(?:fists|hands|arms|forearms|elbows|open\s+palms)\s+)",
        "",
        clean_clause,
        flags=re.IGNORECASE,
    )
    clean_clause = re.sub(r",?\s*both arms.*$", "", clean_clause).strip()
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
        else:
            l_arm_str, r_arm_str = _split_dual_arm_clause(other_arm, act_words)

    return (
        f"L_arm:{l_arm_str}; R_arm:{r_arm_str} (both arms separate from the torso in silhouette); "
        f"L_leg:{l_leg_str}; R_leg:{r_leg_str}"
    )


def _resolve_surface_tag(card: Dict[str, Any]) -> str:
    """Resolve anatomical contact surface for a Move Card without substring collisions (e.g. 'sla-shin-g')."""
    cid = card["id"]
    if "elbow" in cid or card["limb"] in {"lead_elbow", "rear_elbow"}:
        if "tuck" in cid or card["contact"] == "block":
            return "tucked_left_elbow_guard" if card["limb"] == "lead_elbow" else "tucked_elbow_guard"
        return "right_elbow_and_forearm" if card["limb"] == "rear_elbow" else "left_elbow_and_forearm"
    if "shell" in cid or "frame_absorb" in cid:
        return "vertical_forearm_shell"
    if "parry" in cid:
        return "open_palm_parry"
    if "tie" in cid or "plum" in cid:
        return "open_palm_collar_tie"
    if "shove" in cid:
        return "both_open_palms"
    if "calf" in cid or cid == "shin_check":
        return "right_shin_calf_kick" if card["limb"] == "rear_leg" else "left_shin_check"
    if "back_kick" in cid or "heel" in cid or "sweep" in cid:
        return "right_heel_back_kick"
    return LIMB_SURFACE_TAG.get(card["limb"], card["limb"])


def _extract_short_wardrobe(desc: str, default_str: str) -> str:
    """Extract a concise wardrobe anchor from a fighter label for the Layer 1 legend."""
    lower = desc.lower()
    if "midnight-blue" in lower and "white cloth tape" in lower:
        return "midnight-blue shorts, white wrist tape, gold ankle wraps"
    if "urban-camo" in lower and "bare wrists" in lower:
        return "urban-camo shorts, bare wrists, no tape"
    return default_str


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
    emit_chain_in_causal: bool = True,
    schema_name: str = "sakuga_Xperiment",
    mode: str = "xperiment",
    use_kb_priors: bool = True,
) -> Tuple[str, Dict[str, Any], ValidationResult]:
    """Compile a validated beat-sheet into the 2-Layer Unrolled Fluid Stack format:
      - `mode="xperiment"` (default): Full `sakuga_Xperiment` schema (`e041b6b` + KB priors + bug fixes) with
        Layer 1 `SUPPORT (% weight split, CoG) | limbs | CHAIN | Easing | FE<N>` and Layer 2 `weight_split`,
        `com_position`, `easing_curve`, `impulse_tier`, 4-part `causal` (`requires -> preserves -> chain -> causes`),
        per-timestamp `anime.fx` dictionary, and full `rules` summary.
      - `mode="lean"`: Stripped `e1eb131` output without extra Layer 2 metadata keys.
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

    # 1. Build Header
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

    a_short_outfit = _extract_short_wardrobe(a_desc, "crimson trunks, white wrist tape")
    b_short_outfit = _extract_short_wardrobe(b_desc, "black pants, bare wrists, no tape")

    if mode == "lean":
        layer1_lines: List[str] = [
            f"MOVEMENT LANGUAGE: <seconds> <performer>: SUPPORT (what bears weight; NO SUPPORT = airborne) | bilateral limb placement & torso rotation (both L_arm and R_arm separate from torso in silhouette) | 5-phase force event & reach distance | path in metres. A is always screen-left ({a_short_outfit}); B is always screen-right ({b_short_outfit})."
        ]
    else:
        layer1_lines = [
            f"MOVEMENT LANGUAGE: <seconds> <performer>: SUPPORT (what bears weight, lead/rear weight split %, and Center of Gravity CoG; NO SUPPORT = airborne) | bilateral limb placement & torso rotation (both L_arm and R_arm separate from torso in silhouette) | CHAIN (ground-up kinetic link sequence) & Easing Curve | 5-phase force event & reach distance | path in metres. A is always screen-left ({a_short_outfit}); B is always screen-right ({b_short_outfit})."
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
    used_directives: List[str] = []
    used_cards: List[str] = []
    used_passages: List[str] = []

    if use_kb_priors:
        pre_intent_kb = query_kb_prior_to_semantic_intent(clip)
        for d_item in pre_intent_kb.get("directives", []):
            if isinstance(d_item, dict) and d_item.get("id"):
                used_directives.append(d_item["id"])
        for p_item in pre_intent_kb.get("pulled_relations", []):
            if isinstance(p_item, dict) and p_item.get("id"):
                used_directives.append(p_item["id"])
        for hit in pre_intent_kb.get("passages", []):
            if isinstance(hit, dict) and hit.get("id"):
                used_passages.append(hit["id"])

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

        if a_card:
            used_cards.append(a_card["id"])
        if b_card:
            used_cards.append(b_card["id"])

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
        primary_contact_card = a_card if (a_card and a_card["contact"] in {"strike", "grapple"}) else b_card
        if is_contact and primary_contact_card:
            hold_win = primary_contact_card.get("spacing_phases", {}).get("hold", [4, 6])
            base_hold = max(2, hold_win[1] - hold_win[0])
            hold_f = max(5, base_hold + 2) if is_hero else max(3, base_hold)
        else:
            hold_f = 0
        if is_contact:
            impact_frames.append(t_val)

        if use_kb_priors:
            kb_info = resolve_beat_kb_guidance(
                a_card, b_card, is_hero=is_hero, beat_idx=idx, total_beats=total_moments
            )
            used_directives.extend(kb_info["directives"])
            used_passages.extend(kb_info["handbook_refs"])

        a_pre_coil = fighter_a.coil

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
            a_ws = (
                a_act.get("weight_split", a_card.get("weight_split", [50, 50]))
                if a_act
                else a_card.get("weight_split", [50, 50])
            )
            a_com = (
                a_act.get("com_position", a_card.get("com_position", "centered"))
                if a_act
                else a_card.get("com_position", "centered")
            )
            a_easing = (
                a_act.get("easing_curve", a_card.get("easing_curve", "explosive_snap_hold_recoil"))
                if a_act
                else a_card.get("easing_curve", "explosive_snap_hold_recoil")
            )
            a_impulse = (
                int(a_act.get("impulse_tier", a_card.get("impulse_tier", 1)))
                if a_act
                else int(a_card.get("impulse_tier", 1))
            )
            if is_hero and a_impulse >= 2:
                a_impulse = 3

            beat_chain, _beat_chain_frames = _resolve_beat_chain(a_act, a_card, fighter_a)

            hold_tag = f" (hold {hold_f}f, Bound)" if (hold_f and a_card["contact"] in {"strike", "grapple"}) else ""
            if mode == "lean":
                a_sup_tag = (
                    "NO SUPPORT (airborne)"
                    if a_card["post"]["support"] == "airborne"
                    else f"SUPPORT both feet planted at z={z_a:.2f} on screen-left ({reach_label} from B at z={z_b:.2f})"
                )
                l1_a = (
                    f"{t_val:.2f} A ({frames}f): {a_sup_tag} | {a_limbs_str} | "
                    f"FE{fe_num} {a_card['id'].upper()}{hold_tag}: A {a_move_words} across the {sep_m:.2f}m gap."
                )
            else:
                a_sup_tag = (
                    f"NO SUPPORT (airborne, CoG {a_com})"
                    if a_card["post"]["support"] == "airborne"
                    else f"SUPPORT both feet planted at z={z_a:.2f} on screen-left ({a_ws[0]}/{a_ws[1]} lead/rear weight split, CoG {a_com}, {reach_label} from B at z={z_b:.2f})"
                )
                l1_a = (
                    f"{t_val:.2f} A ({frames}f): {a_sup_tag} | {a_limbs_str} | "
                    f"CHAIN: {beat_chain} | Easing: {a_easing} | "
                    f"FE{fe_num} {a_card['id'].upper()}{hold_tag}: A {a_move_words} across the {sep_m:.2f}m gap."
                )
            layer1_lines.append(l1_a)

            prev_c_code = f"C{idx:02d}_prev_state" if idx > 0 else "init_stance"
            prev_visible = COIL_VISIBLE_PROSE.get(a_pre_coil, "balanced stance")
            next_c_code = f"C{idx+1:02d}_{a_card['id']}"
            next_visible = (
                f"B {b_card['id'].replace('_', ' ')}, A {COM_VISIBLE_PROSE.get(a_com, a_com)}"
                if (b_card and a_card["contact"] in {"strike", "grapple"})
                else f"A {COM_VISIBLE_PROSE.get(a_com, a_com)}"
            )
            a_chain_parts.append(f"C{idx+1:02d}_{a_card['id']}_{t_val:.2f}s")

            if emit_chain_in_causal and mode != "lean":
                causal_str = build_causal_string(
                    f"C{idx+1:02d}",
                    requires=prev_c_code,
                    preserves=f"{a_card['post']['coil']}_momentum",
                    chain=beat_chain or "",
                    causes=next_c_code,
                )
            elif emit_chain_in_causal:
                causal_str = build_causal_string(
                    f"C{idx+1:02d}",
                    requires=prev_c_code,
                    preserves=f"{a_card['post']['coil']}_momentum",
                    chain=beat_chain or "",
                    causes=next_c_code,
                )
            else:
                causal_str = (
                    f"C{idx+1:02d}: requires: {prev_c_code} -> "
                    f"preserves: {a_card['post']['coil']}_momentum -> "
                    f"causes: {next_c_code}"
                )

            a_beat_obj: Dict[str, Any] = {
                "t": t_val,
                "beat": beat_label,
                "causal": causal_str,
                "pos": [0, a_y, z_a],
                "vel": [0, 0, 0.3 if a_card["contact"] == "strike" else 0.0],
                "axis": f"head:+Y_up, torso:{a_card['hinge']}_{a_card['path']}, facing:+Z, screen_side:left",
                "arc": f"{a_card['path']}_{a_card['limb']}_at_{sep_m:.2f}m_reach",
                "support": f"{a_card['post']['support']}_on_arena_floor_at_z={z_a:.2f}",
            }
            if mode != "lean":
                a_beat_obj["weight_split"] = a_ws
                a_beat_obj["com_position"] = a_com
                a_beat_obj["easing_curve"] = a_easing
                a_beat_obj["impulse_tier"] = a_impulse

            a_beat_obj["limbs"] = a_limbs_str
            if mode == "lean":
                a_beat_obj["pose"] = (
                    f"At {t_val:.2f}s ({f'hold {hold_f}f' if hold_f else f'{frames}f'}), at {reach_label} "
                    f"with both arms separate from the torso in silhouette, A {a_move_words}."
                )
            else:
                a_beat_obj["pose"] = (
                    f"At {t_val:.2f}s ({f'hold {hold_f}f' if hold_f else f'{frames}f'}), at {reach_label} "
                    f"with {a_ws[0]}/{a_ws[1]} lead/rear weight split ({COM_VISIBLE_PROSE.get(a_com, a_com)}) "
                    f"and both arms separate from the torso in silhouette, A {a_move_words}."
                )

            if a_card["contact"] in {"strike", "grapple", "block"} and b_card:
                t_y = LEVEL_TARGET_Y[a_card["level"]]
                t_anat = LEVEL_TARGET_ANATOMY[a_card["level"]]
                surf = _resolve_surface_tag(a_card)
                # Fix passive-block contact direction when A blocks B's incoming strike
                if a_card["contact"] == "block" and b_card["contact"] == "strike":
                    b_surf = _resolve_surface_tag(b_card)
                    a_beat_obj["contact"] = (
                        f"pre:A_{a_card['id']}_set -> "
                        f"hit:B_{b_surf}_meets_A_{surf}_at_[0,{t_y},{round(z_a + 0.12, 2)}]_at_{sep_m:.2f}m_reach -> "
                        f"post:heavy_counter_shock_absorbed_on_A_{a_card['id']}"
                    )
                else:
                    a_beat_obj["contact"] = (
                        f"pre:A_{a_card['id']}_windup -> "
                        f"hit:A_{surf}_into_B_{t_anat}_at_[0,{t_y},{round(z_b - 0.12, 2)}]_at_{sep_m:.2f}m_reach -> "
                        f"post:white_impact_shock_triggers_B_{b_card['id']}"
                    )
                snap_win = a_card.get("spacing_phases", {}).get("snap", [1, 4])
                snap_dur_s = round(max(2, snap_win[1] - snap_win[0]) / 24.0, 2)
                smear_start = round(max(0.0, t_val - snap_dur_s), 2)
                if a_card["contact"] == "strike" and a_card["limb"] not in {"lead_knee", "rear_knee"}:
                    lw = fighter_a.limb_words()
                    smear_limb = lw.get(a_card["limb"], a_card["limb"])
                    smear_frames.append(
                        f"{smear_start}-{t_val}: A {smear_limb} {a_card['path']} strike arc smear only ({a_easing}); head, torso, and off-hand guard stay solid"
                    )
                    speed_lines.append(f"{smear_start}-{t_val}")
                    fx_map[str(t_val)] = f"white_impact_shock_flash_and_sweat_spray_on_B_{a_card['level']}_line"
                elif a_card["contact"] == "strike":
                    speed_lines.append(f"{smear_start}-{t_val}")
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
            b_ws = (
                b_act.get("weight_split", b_card.get("weight_split", [50, 50]))
                if b_act
                else b_card.get("weight_split", [50, 50])
            )
            b_com = (
                b_act.get("com_position", b_card.get("com_position", "centered"))
                if b_act
                else b_card.get("com_position", "centered")
            )
            b_easing = (
                b_act.get("easing_curve", b_card.get("easing_curve", "sudden_jolt_settle"))
                if b_act
                else b_card.get("easing_curve", "sudden_jolt_settle")
            )
            b_impulse = (
                int(b_act.get("impulse_tier", b_card.get("impulse_tier", 1)))
                if b_act
                else int(b_card.get("impulse_tier", 1))
            )
            if is_hero and b_impulse >= 2:
                b_impulse = 3

            b_beat_chain, _b_chain_frames = _resolve_beat_chain(b_act, b_card, fighter_b)

            hold_tag_b = f" (hold {hold_f}f, Bound)" if (hold_f and b_card["contact"] in {"strike", "grapple"}) else ""
            if mode == "lean":
                b_sup_tag = (
                    "NO SUPPORT (driven backward)"
                    if b_card["post"]["support"] == "supine"
                    else f"SUPPORT both feet at z={z_b:.2f} on screen-right ({reach_label} from A at z={z_a:.2f})"
                )
                l1_b = (
                    f"{t_val:.2f} B ({frames}f): {b_sup_tag} | {b_limbs_str} | "
                    f"FE{fe_num} {b_card['id'].upper()}{hold_tag_b}: B {b_move_words}."
                )
            else:
                b_sup_tag = (
                    f"NO SUPPORT (driven backward, CoG {b_com})"
                    if b_card["post"]["support"] == "supine"
                    else f"SUPPORT both feet at z={z_b:.2f} on screen-right ({b_ws[0]}/{b_ws[1]} lead/rear weight split, CoG {b_com}, {reach_label} from A at z={z_a:.2f})"
                )
                l1_b = (
                    f"{t_val:.2f} B ({frames}f): {b_sup_tag} | {b_limbs_str} | "
                    f"CHAIN: {b_beat_chain} | Easing: {b_easing} | "
                    f"FE{fe_num} {b_card['id'].upper()}{hold_tag_b}: B {b_move_words}."
                )
            layer1_lines.append(l1_b)
            b_chain_parts.append(f"C{idx+1:02d}_{b_card['id']}_{t_val:.2f}s")

            b_entry: Dict[str, Any] = {
                "t": t_val,
                "pos": [0, b_y, z_b],
                "axis": f"head:+Y_up, torso:{b_card['id']}, facing:-Z, screen_side:right",
                "support": f"{b_card['post']['support']}_on_floor_at_z={z_b:.2f}",
            }
            if mode != "lean":
                b_entry["weight_split"] = b_ws
                b_entry["com_position"] = b_com
                b_entry["easing_curve"] = b_easing
                b_entry["impulse_tier"] = b_impulse

            b_entry["action"] = f"{b_card['id']}_at_{t_val:.2f}s"
            if mode == "lean":
                b_entry["pose"] = (
                    f"{'only after contact at ' if b_card['class'] == 'IMPACT.REACTION' else 'at '}{t_val:.2f}s ({frames}f), "
                    f"on screen-right at z={z_b:.2f} ({reach_label}) "
                    f"with both arms separate from the torso in silhouette, B {b_move_words}"
                )
            else:
                b_entry["pose"] = (
                    f"{'only after contact at ' if b_card['class'] == 'IMPACT.REACTION' else 'at '}{t_val:.2f}s ({frames}f), "
                    f"on screen-right at z={z_b:.2f} ({reach_label}, {b_ws[0]}/{b_ws[1]} lead/rear weight split, {COM_VISIBLE_PROSE.get(b_com, b_com)}) "
                    f"with both arms separate from the torso in silhouette, B {b_move_words}"
                )

            if b_card["contact"] in {"strike", "grapple", "block"} and a_card:
                t_y = LEVEL_TARGET_Y[b_card["level"]]
                t_anat = LEVEL_TARGET_ANATOMY[b_card["level"]]
                surf_b = _resolve_surface_tag(b_card)
                if a_card["contact"] == "block":
                    surf_a = _resolve_surface_tag(a_card)
                    b_entry["contact"] = (
                        f"B_{surf_b} -> into_A_{surf_a}_at_[0,{t_y},{round(z_a + 0.12, 2)}]_at_{sep_m:.2f}m_reach"
                    )
                else:
                    b_entry["contact"] = (
                        f"B_{surf_b} -> into_A_{t_anat}_at_[0,{t_y},{round(z_a + 0.12, 2)}]_at_{sep_m:.2f}m_reach"
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

        # Camera entry
        is_knee_beat = any(c and c["limb"] in {"lead_knee", "rear_knee"} for c in (a_card, b_card))
        if is_knee_beat:
            cam_obj: Dict[str, Any] = {
                "t": t_val,
                "shot": f"medium_wide_side_profile_{beat_label}",
                "fov": 38,
                "pos": [1.55, 0.92, round((z_a + z_b) / 2.0, 2)],
                "look": f"A_on_screen_left_z={z_a:.2f}_and_B_on_screen_right_z={z_b:.2f}_at_{sep_m:.2f}m_separation",
                "preserve_axis": True,
                "hold_frames": hold_f or 3,
                "effect": "camera_shake_impact_shock_flash",
            }
        elif is_contact:
            cam_obj = {
                "t": t_val,
                "shot": (
                    f"telephoto_snap_zoom_3_4_{beat_label}"
                    if is_hero
                    else f"tight_3_4_front_hemisphere_whip_pan_{beat_label}"
                ),
                "fov": 28 if is_hero else 32,
                "pos": [1.55, 0.92, round((z_a + z_b) / 2.0, 2)],
                "look": f"A_on_screen_left_z={z_a:.2f}_and_B_on_screen_right_z={z_b:.2f}_at_{sep_m:.2f}m_separation",
                "preserve_axis": True,
                "dutch_roll_deg": -10 if idx % 2 == 0 else 8,
                "hold_frames": hold_f,
                "effect": "camera_shake_impact_shock_flash",
            }
            if is_hero:
                cam_obj["time_remap"] = 0.25
        else:
            cam_obj = {
                "t": t_val,
                "shot": f"low_3_4_tracking_dolly_{beat_label}",
                "fov": 40,
                "pos": [1.55, 0.92, round((z_a + z_b) / 2.0, 2)],
                "look": f"A_on_screen_left_z={z_a:.2f}_and_B_on_screen_right_z={z_b:.2f}_at_{sep_m:.2f}m_separation",
                "preserve_axis": True,
                "move": "smooth_lateral_dolly_tracking_footwork, no_orbit",
            }
        camera_track.append(cam_obj)

        if a_card and b_card:
            a_Summary = _format_card_text(a_card["caption_words"], fighter_a)
            if a_ov_card:
                a_Summary = _format_card_text(a_ov_card["caption_words"], fighter_a) + " then immediately " + a_Summary
            b_Summary = _format_card_text(b_card["caption_words"], fighter_b)
            if b_ov_card:
                b_Summary = _format_card_text(b_ov_card["caption_words"], fighter_b) + " then immediately " + b_Summary
            rules_sentences.append(
                f"At {t_val:.2f}s ({reach_label}), A {a_Summary} while B {b_Summary}"
                + (f" (hold {hold_f}f)." if hold_f else ".")
            )

        if a_ov_card:
            dyad.apply_range_delta(a_ov_card["post"]["range_delta"])
        if b_ov_card:
            dyad.apply_range_delta(b_ov_card["post"]["range_delta"])
        if a_card:
            dyad.apply_range_delta(a_card["post"]["range_delta"])
        if b_card:
            dyad.apply_range_delta(b_card["post"]["range_delta"])

    # Add 10.00s final state hold
    layer1_lines.append(
        f"10.00 A (10f): SUPPORT wide fighting stance held still at z={z_a:.2f} on screen-left | L_arm extended forward in high guard, R_arm chambered at cheek, both arms separate from torso in silhouette | follow-through hold to 10.00s."
    )
    layer1_lines.append(
        f"10.00 B (10f): SUPPORT {fighter_b.support} at z=4.30 on screen-right | both arms separate from torso in silhouette | final state hold to 10.00s."
    )
    a_beats.append(
        {
            "t": 10.0,
            "beat": beat_names[-1] if beat_names else "final_hold",
            "causal": "C11_hold: maintains post_finisher_stance_to_10s",
            "pos": [0, 0.84, z_a],
            "vel": [0, 0, 0],
            "axis": "head:+Y_up_level, torso:still_wide_martial_stance, facing:+Z, screen_side:left",
            "arc": "static_follow_through_hold",
            "support": f"standing_on_floor_at_z={z_a:.2f}",
            "limbs": "L_arm:extended forward in high guard; R_arm:chambered at right cheek (both arms separate from the torso in silhouette); L_leg:planted forward; R_leg:anchored back",
            "pose": f"At 10.00s, A holds his wide fighting stance at z={z_a:.2f} on screen-left with both arms separate from the torso in silhouette.",
        }
    )
    b_track.append(
        {
            "t": 10.0,
            "pos": [0, SUPPORT_Y_HEIGHT.get(fighter_b.support, 0.22), 4.30],
            "axis": f"head:+Y_up, spine:{fighter_b.support}, facing:-Z, screen_side:right",
            "support": f"{fighter_b.support}_on_floor_at_z=4.30",
            "action": f"final_{fighter_b.support}_hold_to_10s",
            "pose": f"At 10.00s, B remains in {fighter_b.support} state at z=4.30 on screen-right.",
        }
    )

    style_map = {
        "boxing": "western_boxing",
        "muay_thai": "muay_thai",
        "mma": "ufc_mma_octagon",
        "baki": "baki_underground_arena",
        "freestyle_sakuga": "freestyle_sakuga",
    }

    spec: Dict[str, Any] = {
        "name": clip.get("name", f"fight_move_system_{fighter_a.style}_vs_{fighter_b.style}_10s"),
        "schema": schema_name,
        "fps": 24,
        "duration": 10.0,
        "axes": "Y_up, metres, arena floor y=0, combat pocket z=2.8 to z=5.0, A stays on screen_left facing +Z right for all 10s, B stays on screen_right facing -Z left for all 10s",
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
                "fighting_style": style_map.get(fighter_a.style, "ufc_mma_octagon"),
                "chain": " > ".join(a_chain_parts),
                "effort": {"weight": "heavy_striker_power", "time": "sudden", "space": "direct", "flow": "bound"},
            },
            "B": {
                "fighting_style": style_map.get(fighter_b.style, "ufc_mma_octagon"),
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

    lines: List[str] = ["{"]
    lines.append(
        f'"name":{json.dumps(spec["name"])},"schema":{json.dumps(schema_name)},"fps":24,"duration":10.0,'
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
        f"=== LAYER 2: {schema_name} KINEMATIC & CAMERA SCENE GRAPH ===\n"
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

    if emit_chain_in_causal:
        v18_errs = scan_prompt_v18(fluid_stack_prompt)
        if v18_errs:
            val_res.errors.extend(v18_errs)
            return "", {}, val_res

    if use_kb_priors:
        record_compile_usage(
            run_id=spec["name"],
            used_directives=used_directives,
            used_cards=used_cards,
            used_passages=used_passages,
        )

    return fluid_stack_prompt, spec, val_res


def compile_clip_prompt(
    clip: Dict[str, Any],
    lexicon: Optional[Lexicon] = None,
    emit_chain_in_causal: bool = True,
    schema_name: str = "sakuga_Xperiment",
    mode: str = "xperiment",
    use_kb_priors: bool = True,
) -> Tuple[str, ValidationResult]:
    """Default entrypoint: compiles the validated clip into the 2-Layer Unrolled Fluid Stack (`sakuga_Xperiment`) format."""
    prompt, _, res = compile_to_sakuga_Fluid_stack(
        clip,
        lexicon=lexicon,
        emit_chain_in_causal=emit_chain_in_causal,
        schema_name=schema_name,
        mode=mode,
        use_kb_priors=use_kb_priors,
    )
    return prompt, res
