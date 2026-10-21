"""§8. Natural Caption Wording Compiler & V15 Purity Scanner."""

import re
from typing import Any, Dict, List, Optional, Set, Tuple

from .dyad import DyadState
from .enums import RANGE_CAPTION_WORDS
from .lexicon import Lexicon
from .state import FighterState
from .validator import ValidationResult, load_thresholds, validate_clip

# Forbidden franchise / anime trope names and metric units (V15)
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

METRIC_UNIT_REGEX = re.compile(r"\b(?:metres|meters|metre|meter|cm|mm|deg|degrees|fps)\b", re.IGNORECASE)
DIGIT_REGEX = re.compile(r"\d")

CAMERA_VOCABULARY: Dict[str, str] = {
    "locked_side_medium": "The camera holds a steady side-profile medium-wide framing across the center of the arena",
    "side_track": "The side-profile camera glides laterally with the footwork to keep both fighters framed head-to-toe",
    "pocket_push": "The camera pushes in slightly to a tight medium-full framing as they trade in the pocket",
    "low_angle_clinch": "The camera drops to a low side-on angle looking up through the clinch",
    "impact_jolt": "The frame jolts sharply on impact as a crisp motion smear trails only the striking limb while both fighters' ink outlines stay razor-sharp",
    "hero_finisher_hold": "The camera locks firmly on the side-profile exchange, holding briefly on the moment of impact as a clean shockwave ring ripples outward and sweat sprays from the jaw",
}

TIME_CONNECTORS = [
    "A heartbeat later,",
    "Riding that momentum without resetting his stance,",
    "In the next instant,",
    "Flowing directly out of the recoil,",
    "Without a pause,",
    "Uncoiling immediately from the hip,",
    "Pressing the exchange,",
    "Pivoting into the counter,",
    "In the decisive moment,",
]


def _format_card_text(template: str, fighter: FighterState) -> str:
    lw = fighter.limb_words()
    return template.format(**lw)


def scan_prompt_v15(
    prompt: str,
    clip_regime: str,
    allowed_styles: Set[str],
    lexicon: Lexicon,
) -> List[Tuple[str, str]]:
    """V15: Scan compiled positive prompt for digits, metric units, forbidden franchise names,
    negative 'no <move>' lists, or out-of-regime move card phrases.
    """
    errors: List[Tuple[str, str]] = []
    lower = prompt.lower()

    # 1. Digits check
    digit_match = DIGIT_REGEX.search(prompt)
    if digit_match:
        errors.append(("V15", f"Printed prompt contains a forbidden digit '{digit_match.group(0)}'"))

    # 2. Metric units check
    metric_match = METRIC_UNIT_REGEX.search(prompt)
    if metric_match:
        errors.append(("V15", f"Printed prompt contains a forbidden metric unit '{metric_match.group(0)}'"))

    # 3. Franchise names check
    for term in FORBIDDEN_FRANCHISE_TERMS:
        if term in lower:
            errors.append(("V15", f"Printed prompt contains forbidden franchise term '{term}'"))

    # 4. Rule 0.4: No 'no <move>' negative lists in positive prompt
    neg_list_match = re.search(r"\bno\s+(?:sweeps|ankle sweeps|kip-ups|flying knees|wall-runs|cartwheels)\b", lower)
    if neg_list_match:
        errors.append(
            ("V15", f"Printed positive prompt contains forbidden negative move list '{neg_list_match.group(0)}'")
        )

    # 5. Out-of-regime / out-of-style move card check
    for card_id, card in lexicon.cards_by_id.items():
        legal_in_regime = clip_regime in card["regimes"] or "transition" in card["regimes"]
        legal_in_style = bool(allowed_styles.intersection(set(card["styles"])))
        if not (legal_in_regime and legal_in_style):
            # Check if any alias of this illegal move leaked into the prompt
            for alias in card["aliases"]:
                if re.search(rf"\b{re.escape(alias.lower())}\b", lower):
                    errors.append(
                        (
                            "V15",
                            f"Printed prompt mentions out-of-regime/style move alias '{alias}' (from card '{card_id}')",
                        )
                    )
    return errors


def compile_clip_prompt(
    clip: Dict[str, Any],
    lexicon: Optional[Lexicon] = None,
) -> Tuple[str, ValidationResult]:
    """Validate and compile a clip beat-sheet into a deterministic, render-ready caption prompt.
    If validation fails, returns ("", validation_result).
    """
    lex = lexicon or Lexicon.load_default()
    thresh = load_thresholds()
    val_res = validate_clip(clip, lexicon=lex, thresholds=thresh)
    if not val_res.ok:
        return "", val_res

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
    dyad = DyadState(range_band=clip.get("initial_range", "punch"))

    a_name = a_cfg.get("label", " the lean fighter in crimson trunks and white wrist tape")
    b_name = b_cfg.get("label", " the heavy bare-knuckle fighter in black pants with bare wrists")
    a_short = a_cfg.get("short_name", "the crimson-trunks fighter on the left")
    b_short = b_cfg.get("short_name", "the black-pants fighter on the right")

    style_header = clip.get(
        "style_header",
        "Hand-drawn anime martial arts animation with bold black ink linework, crisp anatomical proportions, and high-contrast cel shading.",
    )
    arena_desc = clip.get("arena", "inside a dimly lit underground sand arena")

    sentences: List[str] = []
    # 1. Opening Identity, Style & Screen-Side Lock Sentence (§8.1)
    opening = (
        f"{style_header} "
        f"Staged {arena_desc}, {a_name.strip()} stands on the {fighter_a.screen_side} side of the frame facing {fighter_a.facing}, "
        f"while {b_name.strip()} stands on the {fighter_b.screen_side} side of the frame facing {fighter_b.facing}, "
        f"both fighters keeping their left-right screen positions locked throughout the exchange."
    )
    sentences.append(opening)

    moments = clip.get("moments", [])
    camera_h4_switch = thresh.get("camera_slow_lock_on_tier_3", {}).get("value", False)

    for idx, moment in enumerate(moments):
        connector = TIME_CONNECTORS[(idx - 1) % len(TIME_CONNECTORS)] if idx > 0 else "In the opening beat,"
        is_hero = bool(moment.get("is_hero", idx == len(moments) - 1))

        a_act = moment.get("A")
        b_act = moment.get("B")
        a_card = lex.get(a_act["move"]) if a_act else None
        b_card = lex.get(b_act["move"]) if b_act else None

        # Determine if this is a key beat (§8.3: contact, transition, or hero moment)
        is_key_beat = is_hero or any(
            c and (c["contact"] in {"strike", "grapple"} or "transition" in c["regimes"])
            for c in (a_card, b_card)
        )

        # Build overlap preamble if present
        overlap_parts: List[str] = []
        for f_st, f_short, f_a in [(fighter_a, a_short, a_act), (fighter_b, b_short, b_act)]:
            if f_a and "overlaps_move" in f_a:
                ov_card = lex.get(f_a["overlaps_move"])
                if ov_card:
                    ov_words = _format_card_text(ov_card["caption_words"], f_st)
                    overlap_parts.append(f"{f_short} {ov_words} and in the same continuous motion")
                    f_st.support = ov_card["post"]["support"]
                    f_st.coil = ov_card["post"]["coil"]

        range_phrase = RANGE_CAPTION_WORDS[dyad.range_band]
        beat_clauses: List[str] = []

        # Primary actor first (attacker if contact, else A then B)
        ordered_pairs = [(fighter_a, a_short, a_card), (fighter_b, b_short, b_card)]
        if b_card and b_card["contact"] in {"strike", "grapple"} and (not a_card or a_card["contact"] not in {"strike", "grapple"}):
            ordered_pairs = [(fighter_b, b_short, b_card), (fighter_a, a_short, a_card)]

        for p_idx, (f_st, f_short, card) in enumerate(ordered_pairs):
            if not card:
                continue
            move_text = _format_card_text(card["caption_words"], f_st)
            if is_key_beat and p_idx == 0:
                # Key beat: full 4-limb occupancy on acting fighter (§8.3)
                off_arm = _format_card_text(card["off_limbs"]["other_arm"], f_st)
                lead_l = _format_card_text(card["off_limbs"]["lead_leg"], f_st)
                rear_l = _format_card_text(card["off_limbs"]["rear_leg"], f_st)
                clause = (
                    f"{f_short} {move_text} with his {off_arm}, {lead_l}, and {rear_l}"
                )
            elif is_key_beat and p_idx == 1:
                # Partner reaction on key beat
                off_arm = _format_card_text(card["off_limbs"]["other_arm"], f_st)
                clause = f"as {f_short} {move_text} with {off_arm}"
            else:
                # Connective beat: acting limb + feet only (§7.2 / §8.3)
                lead_l = _format_card_text(card["off_limbs"]["lead_leg"], f_st)
                prefix = "while " if p_idx == 1 else ""
                clause = f"{prefix}{f_short} {move_text} with his {lead_l}"

            beat_clauses.append(clause)
            f_st.support = card["post"]["support"]
            f_st.coil = card["post"]["coil"]

        # Update dyad range
        for card in (a_card, b_card):
            if card and card["post"].get("range_delta", "same") != "same":
                dyad.apply_range_delta(card["post"]["range_delta"])
                break

        # Camera & Sakuga impact phrasing
        has_tier_3 = any(c and c["bleed_tier"] == 3 for c in (a_card, b_card))
        cam_key = moment.get("camera", "impact_jolt" if is_key_beat else "side_track")
        if camera_h4_switch and has_tier_3:
            cam_key = "locked_side_medium"
        if is_hero:
            cam_key = "hero_finisher_hold"
        cam_phrase = CAMERA_VOCABULARY.get(cam_key, CAMERA_VOCABULARY["side_track"])

        ov_prefix = (" ".join(overlap_parts) + ", ") if overlap_parts else ""
        body_joined = " ".join(beat_clauses)
        sentence = f"{connector} {range_phrase}, {ov_prefix}{body_joined}. {cam_phrase}."
        sentences.append(sentence)

    prompt = " ".join(sentences)

    # V15 Final Gate Scan
    clip_regime = clip.get("regime", "standup_striking")
    allowed_styles = {fighter_a.style, fighter_b.style}
    v15_errs = scan_prompt_v15(prompt, clip_regime, allowed_styles, lex)
    if v15_errs:
        val_res.errors.extend(v15_errs)
        return "", val_res

    return prompt, val_res
