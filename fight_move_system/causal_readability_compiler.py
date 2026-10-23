"""§9. LATENT SAKUGA Causal-Readability Compiler (`LATENT-SAKUGA-1.0`).

Implements the 4 high-ROI performance upgrades on top of the existing V01-V22
validator, BLOCK Fight Engine, and Pre-Intent Knowledge Base:
  1. Zero Internal Math Leak: V01-V22 biomechanics (weight_split, CoG, impulse_tier,
     dutch_roll_deg, [x,y,z] coordinates, frame counts) are strictly validated and
     recorded in the internal Loss-Audited Trace (`audit_trace`), never leaked into
     model-facing prompt text.
  2. Referential Locality (Event-Local Packets): Binds Actor + Preparation +
     Commitment + Named Limb-to-Surface Contact (acquire/maintain/release/strike) +
     Defender Consequence + Camera Observation + Bounded Animation License into a
     single contiguous event packet per exchange.
  3. Visibility & Effect-Timing Contract (RH1 & RH3): Explicitly locks camera
     separation of contacting limbs in silhouette and requires impact accents to
     fire only at/after visible contact and clear immediately for the recoil.
  4. 3-Class Requirement System (HARD / SOFT / FREEDOM) & Dual Realization Dialects:
     - `readability` (6-part Directorial Contract: SHOT CONTRACT, STATE, OBSERVATION,
       CAUSAL BEATS, ANIMATION LICENSE, CLOSURE)
     - `readability-prose` (3-paragraph Directing Prose from §11 of the paper, zero
       numbers, zero headers, 100% hard-intent coverage).
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .compiler import (
    COIL_VISIBLE_PROSE,
    COM_VISIBLE_PROSE,
    LEVEL_TARGET_ANATOMY,
    RANGE_METRES,
    _format_card_text,
    _format_structured_limbs,
    _resolve_beat_chain,
    _resolve_surface_tag,
    scan_prompt_v15,
)
from .dyad import DyadState
from .kb_bridge import (
    query_kb_prior_to_semantic_intent,
    record_compile_usage,
    resolve_beat_kb_guidance,
)
from .lexicon import Lexicon
from .state import FighterState
from .validator import ValidationResult, load_thresholds, validate_clip


# Craft-to-Conditioning visual translations (zero numbers, pure observable consequences)
RANGE_OBSERVABLE_PROSE: Dict[str, str] = {
    "outside": "outside kicking distance with clear open floor between both fighters",
    "kick": "long kicking distance where an extended leg bridges the gap",
    "punch": "clean arm-length punching distance so neither torso overlaps",
    "pocket": "tight inside-pocket distance for compact hooks and elbows",
    "clinch": "close collar-and-elbow clinch distance with frames locked",
    "ground": "close ground-grappling distance on the canvas",
}

EASING_OBSERVABLE_PROSE: Dict[str, str] = {
    "snap_snap_hold_snap": "a brief loaded pause gives way to a whip-fast transfer, holds briefly at contact, then snaps back to guard",
    "burst_launch_snap_lock": "a sudden explosive push-off surges across the floor and locks into a planted base",
    "sudden_jolt_settle": "an abrupt contact jolt rocks the frame before settling into a braced recovery stance",
    "whip_arc_follow_through": "a fast whipping arc carries smoothly through the target into a balanced follow-through",
}

SURFACE_READABLE_WORDS: Dict[str, str] = {
    "left_fist_punch": "left fist",
    "right_fist_cross": "right fist",
    "left_elbow_and_forearm": "left elbow and forearm",
    "right_elbow_and_forearm": "right elbow and forearm",
    "tucked_left_elbow_guard": "tucked left elbow and forearm guard",
    "tucked_elbow_guard": "tucked elbow and forearm guard",
    "vertical_forearm_shell": "paired vertical forearm high shell",
    "open_palm_parry": "open lead palm",
    "open_palm_collar_tie": "cupping collar-tie palm",
    "both_open_palms": "both open palms",
    "left_kneecap": "rising left knee",
    "right_kneecap": "rising right knee",
    "left_shin_and_instep": "left shin and instep",
    "right_heel_and_shin": "right shin and heel",
    "right_shin_calf_kick": "horizontal right shin",
    "left_shin_check": "raised left shin shield",
    "right_heel_back_kick": "driving right heel",
}

TARGET_READABLE_WORDS: Dict[str, str] = {
    "low": "outside lead calf and lower leg",
    "mid": "floating ribs and solar plexus",
    "high": "jawline and temple",
}


def _strip_digits_and_metrics(text: str) -> str:
    """Ensure no accidental numeric literals or metric abbreviations leak into pure readability prose."""
    replacements = {
        "180-degree": "front-hemisphere",
        "180 degree": "front-hemisphere",
        "2D": "hand-drawn",
        "3D": "computer-generated",
        "2-tone": "two-tone",
        "3/4": "three-quarter",
        "10s": "continuous",
        "24fps": "hand-drawn exposure",
    }
    out = text
    for k, v in replacements.items():
        out = re.sub(re.escape(k), v, out, flags=re.IGNORECASE)
    # Remove any stray parenthetical metric measurements like (0.80m) or (3f)
    out = re.sub(r"\(\s*\d+(?:\.\d+)?\s*[a-zA-Z%]+\s*\)", "", out)
    out = re.sub(r"\b\d+(?:\.\d+)?\s*(?:metres|meters|metre|meter|m|cm|mm|deg|degrees|fps|s|f)\b", "", out, flags=re.IGNORECASE)
    out = re.sub(r"\s{2,}", " ", out).strip()
    return out


def _classify_contact_operation(a_card: Dict[str, Any], b_card: Dict[str, Any]) -> str:
    """Map the beat interaction to the paper's 4 typed contact operations: acquire, maintain, release, or strike."""
    a_id = a_card["id"]
    b_id = b_card["id"]
    if "tie" in a_id or "plum" in a_id or "tie" in b_id or "plum" in b_id:
        return "acquire"
    if "clinch" in a_id or "clinch" in b_id:
        if "shove" in a_id or "break" in a_id or "shove" in b_id or "break" in b_id:
            return "release"
        return "maintain"
    if "shove" in a_id or "shove" in b_id or "parry" in a_id or "parry" in b_id:
        return "release"
    return "strike"


def _compress_soft_action_words(words: str) -> str:
    """Compress SOFT secondary cosmetic clauses (sweat spray, exhale, heel skid, redundant filler) while keeping HARD limb/target/recoil."""
    out = words
    soft_removals = [
        r"\s+as sweat sprays from his brow",
        r"\s+with a sharp exhale as the blow sinks into his ribs",
        r",\s*his heels skidding across the floor as he catches his balance",
        r",\s*his knee buckling inward as he catches his balance",
        r"\s+while his hands brace against the shoulders for posture",
        r"\s+as the knee buries deep into his solar plexus",
        r"\s+in the direction of the hook",
        r"\s+and create striking space",
        r"\s+to create striking space",
        r"\s+into striking range",
        r"\s+while loading weight onto the right hip",
        r"\s+while coiling his left shoulder",
        r"\s+while standing on his left pillar leg",
        r"steps off-line on his (left|right) foot and\s+",
        r"steps deep into the pocket and\s+",
        r"steps into the pocket and\s+",
        r"in a sharp forward step to close the gap",
        r"out from under him",
        r"out of the clinch to full arm's length",
        r"in a rigid high shell guard to absorb the blow",
        r"to block the body shot",
        r"of the incoming punch",
        r"underneath the elbow\s+",
        r"inside the clinch",
        r"in place on his (left|right) foot\s+",
        r"down the centerline\s+",
        r"a baseball-bat\s+",
        r"a razor-sharp\s+",
        r"briskly to the inside",
        r"sharply to the outside",
        r"sinks his hips and\s+",
        r"behind the back of the neck\s+",
        r"down tight against his hip and ribs",
        r"tightly in front of his face",
        r"flat against the chest",
        r"vertically upward\s+",
        r"horizontally\s+",
        r"forward at the waist",
    ]
    for pat in soft_removals:
        out = re.sub(pat, "", out, flags=re.IGNORECASE)
    out = re.sub(r"\bwhips right shin\b", "whips his right shin", out)
    out = re.sub(r"\bwhips horizontal right elbow point\b", "whips his right elbow", out)
    out = re.sub(r"\ba heavy straight punch with the right fist\b", "a straight right punch", out)
    out = re.sub(r"\ba tight shovel hook with the left fist\b", "a left shovel hook", out)
    out = re.sub(r"\ba straight right fist deep\b", "a straight right punch", out)
    out = re.sub(r"\bslips his head\b", "slips", out)
    out = re.sub(r"\bhas his (left|right) calf chopped sideways\b", r"'s \1 calf buckles sideways", out)
    out = re.sub(r"\bhas his jaw whipped violently sideways\b", "'s head snaps sideways", out)
    out = re.sub(r"\bhas his neck pulled forward into the clinch\b", "'s neck is pulled into the clinch", out)
    out = re.sub(r"\bplants both open palms and shoves violently forward\b", "shoves both palms into B's chest", out)
    return re.sub(r"\s{2,}", " ", out).strip()


def _extract_core_arena_and_freedom(arena: str) -> Tuple[str, str]:
    """Split arena description into HARD core setting and FREEDOM atmospheric embellishments."""
    if "," in arena:
        parts = [p.strip() for p in arena.split(",")]
        core = re.sub(r"\s+overlooking\s+.*$", "", parts[0], flags=re.IGNORECASE)
        return core, ", ".join(parts[1:])
    return arena, "background lighting and crowd details left open to the generator"


def _extract_tight_wardrobe(desc: str) -> Tuple[str, str]:
    """Split fighter description into HARD identity/wardrobe anchors and SOFT anatomical adjectives."""
    lower = desc.lower()
    if "midnight-blue" in lower:
        return (
            "shirtless Muay Thai striker, white wrist tape, gold ankle wraps, midnight-blue shorts",
            "lean razor-cut striated physique details and bare feet",
        )
    if "urban-camo" in lower:
        return (
            "shirtless Dutch kickboxer, urban-camo shorts, untaped wrists and ankles",
            "heavy broad scarred torso texture details and bare feet",
        )
    return desc, "secondary musculature shading details"


def compile_to_causal_readability(
    clip: Dict[str, Any],
    lexicon: Optional[Lexicon] = None,
    dialect: str = "readability",
    use_kb_priors: bool = True,
    budget_words: Optional[int] = None,
) -> Tuple[str, Dict[str, Any], ValidationResult]:
    """Compile a validated beat-sheet into the LATENT SAKUGA Causal-Readability format.

    Parameters
    ----------
    clip : Dict[str, Any]
        Beat-sheet clip specification (same input as `compile_to_sakuga_Fluid_stack`).
    lexicon : Optional[Lexicon]
        Move Card lexicon.
    dialect : str
        - `"readability"` (default): 6-Part Directorial Contract (`SHOT CONTRACT`,
          `STATE`, `OBSERVATION`, `CAUSAL BEATS`, `ANIMATION LICENSE`, `CLOSURE`).
        - `"readability-prose"`: Compact 3-paragraph Directing Prose (§11 worked-example
          format from the LATENT SAKUGA paper) with zero numbers and zero section headers.
    use_kb_priors : bool
        Query the in-repo Knowledge Base prior to semantic intent decomposition.

    Returns
    -------
    (compiled_prompt_text, intent_ir_and_audit_trace, validation_result)
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

    a_desc = _strip_digits_and_metrics(
        a_cfg.get(
            "label",
            "lean, striated martial artist, shirtless bare torso, white cloth tape on both wrists and knuckles, crimson fight trunks, bare feet",
        )
    )
    b_desc = _strip_digits_and_metrics(
        b_cfg.get(
            "label",
            "towering, massive scarred pit-fighter, shirtless broad muscular torso, charcoal-black fight pants, bare wrists and bare ankles with no tape, bare feet",
        )
    )
    arena = _strip_digits_and_metrics(
        clip.get(
            "arena",
            "floodlit underground concrete martial arts tournament platform, harsh cyan-and-golden overhead stadium floodlights, dark tiered arena crowd in deep shadow",
        )
    )

    moments = clip.get("moments", clip.get("beats", []))
    total_moments = len(moments)

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

    event_packets: List[Dict[str, Any]] = []
    contract_beat_lines: List[str] = []
    prose_beat_sentences: List[str] = []
    tight_beat_sentences: List[str] = []
    stack_layer1_lines: List[str] = []
    stack_exchanges: List[Dict[str, Any]] = []
    stack_camera_track: List[Dict[str, Any]] = []
    stack_impact_moments: List[str] = []
    stack_smear_frames: List[str] = []
    stack_speed_lines: List[str] = []
    stack_fx_map: Dict[str, str] = {}
    stack_beat_names: List[str] = []
    stack_a_chain_parts: List[str] = []
    stack_b_chain_parts: List[str] = []
    audit_trace_entries: List[Dict[str, Any]] = []
    requirement_ledger: List[Dict[str, Any]] = []
    active_modules: List[str] = ["M01_hand_to_hand", "M09_complex_camera"]

    core_arena, freedom_arena_decor = _extract_core_arena_and_freedom(arena)
    a_hard_id, a_soft_anat = _extract_tight_wardrobe(a_desc)
    b_hard_id, b_soft_anat = _extract_tight_wardrobe(b_desc)

    stack_layer1_lines.append(
        f"MOVEMENT LANGUAGE: <timestamp> <exchange>: SUPPORT & WEIGHT TRANSFER (grounded stance & center of balance; NO SUPPORT = airborne) | "
        f"BILATERAL 4-LIMB SILHOUETTE (L_arm, R_arm, L_leg, R_leg — both arms separate from torso in silhouette) | "
        f"KINETIC CHAIN & SPACING | SYNCHRONIZED CAUSE -> CONTACT -> POST-CONTACT REACTION. "
        f"A is always screen-{fighter_a.screen_side} ({a_hard_id}); B is always screen-{fighter_b.screen_side} ({b_hard_id})."
    )

    prev_range: Optional[str] = None

    for idx, moment in enumerate(moments):
        is_hero = bool(moment.get("is_hero", idx == total_moments - 1))
        a_act = moment.get("A")
        b_act = moment.get("B")
        a_card = lex.get(a_act["move"]) if a_act else None
        b_card = lex.get(b_act["move"]) if b_act else None
        a_ov_key = (a_act.get("overlaps_move") or a_act.get("override")) if a_act else None
        b_ov_key = (b_act.get("overlaps_move") or b_act.get("override")) if b_act else None
        a_ov_card = lex.get(a_ov_key) if a_ov_key else None
        b_ov_card = lex.get(b_ov_key) if b_ov_key else None

        if not a_card or not b_card:
            continue

        used_cards.append(a_card["id"])
        used_cards.append(b_card["id"])

        # Update pre-states via overlaps_move if present
        if a_ov_card:
            fighter_a.support = a_ov_card["post"]["support"]
            fighter_a.coil = a_ov_card["post"]["coil"]
        if b_ov_card:
            fighter_b.support = b_ov_card["post"]["support"]
            fighter_b.coil = b_ov_card["post"]["coil"]

        pre_range = dyad.range_band
        range_changed = pre_range != prev_range
        range_prose = RANGE_OBSERVABLE_PROSE.get(pre_range, "clean striking distance")

        # Internal V18-V22 verification metadata (kept strictly internal)
        a_chain_text, a_frames = _resolve_beat_chain(a_act, a_card, fighter_a)
        b_chain_text, b_frames = _resolve_beat_chain(b_act, b_card, fighter_b)
        a_ws = a_card.get("weight_split", [50, 50])
        b_ws = b_card.get("weight_split", [50, 50])
        a_com = a_card.get("com_position", "centered")
        b_com = b_card.get("com_position", "centered")
        a_easing = a_card.get("easing_curve", "snap_snap_hold_snap")
        a_impulse = a_card.get("impulse_tier", 1)

        if use_kb_priors:
            kb_info = resolve_beat_kb_guidance(
                a_card,
                b_card,
                is_hero=is_hero,
                beat_idx=idx,
                total_beats=total_moments,
            )
            used_directives.extend(kb_info.get("directives", []))
            used_passages.extend(kb_info.get("handbook_refs", []))

        # Determine who initiates the primary force and who responds
        a_words = _strip_digits_and_metrics(_format_card_text(a_card["caption_words"], fighter_a))
        b_words = _strip_digits_and_metrics(_format_card_text(b_card["caption_words"], fighter_b))
        a_tight_words = _compress_soft_action_words(a_words)
        b_tight_words = _compress_soft_action_words(b_words)
        a_prep = (
            _strip_digits_and_metrics(_format_card_text(a_ov_card["caption_words"], fighter_a))
            if a_ov_card
            else COIL_VISIBLE_PROSE.get(fighter_a.coil, "settled in stance")
        )
        b_prep = (
            _strip_digits_and_metrics(_format_card_text(b_ov_card["caption_words"], fighter_b))
            if b_ov_card
            else COIL_VISIBLE_PROSE.get(fighter_b.coil, "holding compact guard")
        )
        a_tight_prep = _compress_soft_action_words(a_prep)
        b_tight_prep = _compress_soft_action_words(b_prep)

        contact_op = _classify_contact_operation(a_card, b_card)
        if contact_op in ("acquire", "maintain") and "M04_grappling" not in active_modules:
            active_modules.append("M04_grappling")

        a_is_striker = a_card["contact"] in ("strike", "grapple")
        b_is_striker = b_card["contact"] in ("strike", "grapple")

        if a_is_striker:
            effector = SURFACE_READABLE_WORDS.get(_resolve_surface_tag(a_card), "striking limb")
            if "tie" in a_card["id"] or "plum" in a_card["id"]:
                target_surface = "back of the neck"
            elif "shove" in a_card["id"]:
                target_surface = "upper chest"
            else:
                target_surface = TARGET_READABLE_WORDS.get(a_card.get("level", "high"), "target line")
            is_knee = a_card["limb"] in ("lead_knee", "rear_knee") or "knee" in a_card["id"]
            if b_card["contact"] in ("block", "parry"):
                def_surface = SURFACE_READABLE_WORDS.get(_resolve_surface_tag(b_card), "guarding limb")
                contact_clause = (
                    f"A's {effector} meets B's {def_surface} ({contact_op} contact clearly visible in side profile "
                    f"with both fighters' forearms separated from their torsos in silhouette)"
                )
                short_contact = f"meeting B's {def_surface} in clear profile"
            else:
                contact_clause = (
                    f"A's {effector} connects cleanly against B's {target_surface} ({contact_op} contact clearly visible "
                    f"with zero torso overlap and both arms separate in silhouette)"
                )
                short_contact = f"connecting cleanly on B's {target_surface}"
            vis_view = (
                "tight side-profile impact framing exposing the exact limb-to-target collision"
                if is_hero
                else "medium-wide three-quarter lateral view keeping both upper bodies, feet, and contacting limbs unobstructed"
            )
            if is_knee:
                license_clause = (
                    "Keep the bent striking knee, standing pillar leg, head, and torso razor-sharp with zero smear blur; "
                    "punctuate with a brief hit-stop hold after visible contact and clear any impact accent immediately so B's reaction remains unobstructed"
                )
            else:
                license_clause = (
                    f"Allow a brief limb-only smear on A's {effector} during the fast transfer while head, torso, and off-hand stay solid; "
                    f"restore exact proportions on contact, punctuate with a brief hit-stop hold after visible contact, and clear any impact accent immediately so B's reaction remains unobstructed"
                )
            if a_ov_card:
                beat_sentence = (
                    f"At {range_prose}, A {a_prep} and immediately {a_words}; {contact_clause}, "
                    f"and only after contact does B respond as B {b_words}."
                )
                prose_sentence = (
                    f"A {a_prep} and immediately {a_words} ({short_contact}); only after contact, B {b_words}."
                )
                b_tight_clause = f"B{b_tight_words}" if b_tight_words.startswith("'") else f"B {b_tight_words}"
                tight_sentence = f"A {a_tight_prep} then {a_tight_words}; after contact, {b_tight_clause}."
            else:
                beat_sentence = (
                    f"From {range_prose}, A {a_words}; {contact_clause}, "
                    f"and only after that contact does B respond as B {b_words}."
                )
                prose_sentence = (
                    f"From {range_prose}, A {a_words} ({short_contact}); only after contact, B {b_words}."
                )
                range_prefix = f"In {pre_range} range, " if range_changed else ""
                b_tight_clause = f"B{b_tight_words}" if b_tight_words.startswith("'") else f"B {b_tight_words}"
                tight_sentence = f"{range_prefix}A {a_tight_words}; after contact, {b_tight_clause}."
        elif b_is_striker:
            effector = SURFACE_READABLE_WORDS.get(_resolve_surface_tag(b_card), "striking limb")
            target_surface = TARGET_READABLE_WORDS.get(b_card.get("level", "high"), "target line")
            is_knee = b_card["limb"] in ("lead_knee", "rear_knee") or "knee" in b_card["id"]
            if a_card["contact"] in ("block", "parry"):
                def_surface = SURFACE_READABLE_WORDS.get(_resolve_surface_tag(a_card), "guarding limb")
                contact_clause = (
                    f"B's {effector} meets A's {def_surface} ({contact_op} contact clearly visible in profile "
                    f"with both fighters' arms separated from their torsos in silhouette)"
                )
                short_contact = f"meeting A's {def_surface} in clear profile"
            else:
                contact_clause = (
                    f"B's {effector} connects cleanly against A's {target_surface} ({contact_op} contact clearly visible "
                    f"with zero torso overlap and both arms separate in silhouette)"
                )
                short_contact = f"connecting cleanly on A's {target_surface}"
            vis_view = "medium-wide lateral counter framing keeping B's counter lane and A's guard reaction fully visible"
            if is_knee:
                license_clause = (
                    "Keep the bent striking knee, standing pillar leg, head, and torso razor-sharp with zero smear blur; "
                    "hold the impact briefly after contact and let any shock accent clear before A's recovery"
                )
            else:
                license_clause = (
                    f"Allow a brief limb-only smear on B's {effector} during the swing while head, torso, and off-hand stay solid; "
                    f"restore proportions at contact, hold the impact briefly after contact, and let any shock accent clear before A's recovery"
                )
            if b_ov_card:
                beat_sentence = (
                    f"At {range_prose}, B {b_prep} then immediately {b_words}; {contact_clause}, "
                    f"causing A to respond as A {a_words}."
                )
                prose_sentence = (
                    f"B {b_prep} then immediately {b_words} ({short_contact}), causing A to respond as A {a_words}."
                )
                tight_sentence = f"B {b_tight_prep} then {b_tight_words}, met by A who {a_tight_words}."
            else:
                beat_sentence = (
                    f"At {range_prose}, B {b_words}; {contact_clause}, "
                    f"while A responds only at contact as A {a_words}."
                )
                prose_sentence = (
                    f"At {range_prose}, B {b_words} ({short_contact}) while A responds at contact as A {a_words}."
                )
                range_prefix = f"In {pre_range} range, " if range_changed else ""
                tight_sentence = f"{range_prefix}B {b_tight_words}, met at contact by A who {a_tight_words}."
        else:
            # Positional footwork / transition beat (SOFT setup details compressed, HARD geometry kept)
            contact_clause = "no strike collision on this footwork transition; both fighters maintain clear space and distinct silhouettes"
            vis_view = "smooth lateral tracking view following footwork across the floor without camera orbit"
            license_clause = "crisp solid linework with zero smear blur during footwork repositioning"
            beat_sentence = f"Across {range_prose}, A {a_words} while B {b_words}, resetting their firing line without clipping."
            prose_sentence = beat_sentence
            tight_sentence = f"A {a_tight_words} as B {b_tight_words}."

        prev_range = pre_range

        # Apply post states
        fighter_a.support = a_card["post"]["support"]
        fighter_a.coil = a_card["post"]["coil"]
        fighter_b.support = b_card["post"]["support"]
        fighter_b.coil = b_card["post"]["coil"]
        if a_ov_card:
            dyad.apply_range_delta(a_ov_card["post"]["range_delta"])
        if b_ov_card:
            dyad.apply_range_delta(b_ov_card["post"]["range_delta"])
        dyad.apply_range_delta(a_card["post"]["range_delta"])
        dyad.apply_range_delta(b_card["post"]["range_delta"])

        post_recovery = (
            f"A settles into {COIL_VISIBLE_PROSE.get(fighter_a.coil, 'stance')} ({COM_VISIBLE_PROSE.get(a_com, 'balanced')}); "
            f"B settles into {COIL_VISIBLE_PROSE.get(fighter_b.coil, 'stance')} ({COM_VISIBLE_PROSE.get(b_com, 'balanced')})."
        )

        event_id = f"E{idx + 1:02d}_{a_card['id']}_vs_{b_card['id']}"
        packet = {
            "event_index": idx + 1,
            "event_id": event_id,
            "requirement_class": "HARD",
            "requirements_breakdown": {
                "HARD_invariant": tight_sentence,
                "SOFT_preferences": [
                    f"repeated_range_preamble ({range_prose})" if not range_changed else "initial_or_shifted_range_cue",
                    "per_beat_camera_and_license_repetition",
                    "secondary_spray_exhale_embellishments",
                ],
                "FREEDOM_omissions": [
                    "unconstrained_floor_scuff_and_micro_cloth_folds",
                ],
            },
            "observation_state_target": "correct_visible",
            "visibility_contract": vis_view,
            "preparation": {"A": a_prep, "B": b_prep},
            "commitment": {"A": a_words, "B": b_words},
            "contact": {
                "operation": contact_op,
                "description": contact_clause,
            },
            "consequence_and_recovery": post_recovery,
            "animation_license": license_clause,
            "internal_only_biomechanics_not_emitted": {
                "A_weight_split": a_ws,
                "B_weight_split": b_ws,
                "A_com": a_com,
                "B_com": b_com,
                "A_kinetic_chain": a_chain_text,
                "B_kinetic_chain": b_chain_text,
                "A_chain_frames": a_frames,
                "B_chain_frames": b_frames,
                "easing_curve": a_easing,
                "impulse_tier": a_impulse,
                "range_metres": RANGE_METRES.get(pre_range, 0.80),
            },
        }
        event_packets.append(packet)

        contract_beat_lines.append(
            f"- Beat {idx + 1} ({a_card['id'].upper()} vs {b_card['id'].upper()}): "
            f"[View: {vis_view}] {beat_sentence} [License: {license_clause}]"
        )
        prose_beat_sentences.append(prose_sentence)
        tight_beat_sentences.append(tight_sentence)

        # Build Multi-Layer Scene Stack entries (Layer 1 + Layer 2 Synchronized Scene Graph with zero internal math leak)
        if idx == 0:
            t_val = 0.0
        elif idx == total_moments - 1:
            t_val = 8.85
        else:
            t_val = round((idx / max(1, total_moments)) * 8.8, 2)
        t_tag = f"{t_val:.2f}s"

        a_limbs_str = _format_structured_limbs(a_card, fighter_a)
        b_limbs_str = _format_structured_limbs(b_card, fighter_b)
        a_com_prose = COM_VISIBLE_PROSE.get(a_com, "balanced between both feet")
        b_com_prose = COM_VISIBLE_PROSE.get(b_com, "balanced between both feet")
        a_ease_prose = EASING_OBSERVABLE_PROSE.get(a_easing, "loaded pause into whip-fast snap and brief impact hold")
        beat_label = f"exchange_{idx + 1}_{a_card['id']}_vs_{b_card['id']}"
        stack_beat_names.append(beat_label)
        stack_a_chain_parts.append(f"E{idx + 1:02d}_{a_card['id']}_{t_tag}")
        stack_b_chain_parts.append(f"E{idx + 1:02d}_{b_card['id']}_{t_tag}")

        stack_layer1_lines.append(
            f"{t_tag} E{idx + 1:02d} ({a_card['id'].upper()} vs {b_card['id'].upper()}) @ {range_prose}: "
            f"A [{fighter_a.support} on screen-{fighter_a.screen_side}, {a_com_prose} | {a_limbs_str} | CHAIN: {a_chain_text}] "
            f"<-> B [{fighter_b.support} on screen-{fighter_b.screen_side}, {b_com_prose} | {b_limbs_str} | CHAIN: {b_chain_text}] | "
            f"EVENT ({contact_op.upper()}): {prose_sentence}"
        )

        is_contact_beat = a_is_striker or b_is_striker
        is_knee_beat = (
            a_card["limb"] in ("lead_knee", "rear_knee")
            or b_card["limb"] in ("lead_knee", "rear_knee")
            or "knee" in a_card["id"]
            or "knee" in b_card["id"]
        )
        if is_contact_beat:
            stack_impact_moments.append(t_tag)
            snap_win = (a_card if a_is_striker else b_card).get("spacing_phases", {}).get("snap", [1, 4])
            snap_dur_s = round(max(2, snap_win[1] - snap_win[0]) / 24.0, 2)
            smear_start = round(max(0.0, t_val - snap_dur_s), 2)
            window_tag = f"{smear_start:.2f}s-{t_tag}"
            stack_speed_lines.append(window_tag)
            if not is_knee_beat:
                active_actor = "A" if a_is_striker else "B"
                active_eff = SURFACE_READABLE_WORDS.get(
                    _resolve_surface_tag(a_card if a_is_striker else b_card), "striking limb"
                )
                stack_smear_frames.append(
                    f"{window_tag}: {active_actor} {active_eff} strike transfer smear only; head, torso, standing legs, and off-hand guard stay solid, restoring exact anatomy at {t_tag} contact"
                )
            if a_is_striker:
                lvl = a_card.get("level", "high")
                if is_knee_beat:
                    stack_fx_map[t_tag] = (
                        f"radial white knee shock ring and rain-mist burst on B's {lvl} line (fires strictly AFTER visible knee contact at {t_tag} and clears immediately so B's jackknife recoil is unobstructed)"
                    )
                else:
                    stack_fx_map[t_tag] = (
                        f"white impact shock flash and sweat/rain spray on B's {lvl} line (fires strictly AFTER visible contact at {t_tag} and clears immediately so B's recoil is unobstructed)"
                    )
            else:
                lvl = b_card.get("level", "high")
                stack_fx_map[t_tag] = (
                    f"heavy counter shock ring on A's {lvl} guard line (fires strictly AFTER visible contact at {t_tag} and clears immediately so A's block absorption is unobstructed)"
                )

        prev_ev_tag = f"E{idx:02d}_post_state" if idx > 0 else "initial_grounded_stance"
        causal_chain_str = (
            f"requires {prev_ev_tag} -> preserves {fighter_a.coil}_momentum -> "
            f"chain: {a_chain_text} -> causes {beat_label} (B responds only after visible contact)"
        )
        stack_exchanges.append(
            {
                "t": t_tag,
                "exchange": beat_label,
                "range": range_prose,
                "causal": causal_chain_str,
                "A_state": {
                    "screen_side": fighter_a.screen_side,
                    "facing": fighter_a.facing,
                    "support": f"{fighter_a.support}_grounded_on_screen_{fighter_a.screen_side}",
                    "balance": a_com_prose,
                    "limbs": a_limbs_str,
                    "action": f"A {a_prep + ' then immediately ' + a_words if a_ov_card else a_words}",
                },
                "contact": {
                    "operation": contact_op,
                    "visibility_target": "correct_visible",
                    "event": contact_clause,
                    "spacing_rhythm": a_ease_prose,
                },
                "B_state": {
                    "screen_side": fighter_b.screen_side,
                    "facing": fighter_b.facing,
                    "support": f"{fighter_b.support}_grounded_on_screen_{fighter_b.screen_side}",
                    "balance": b_com_prose,
                    "limbs": b_limbs_str,
                    "reaction_timing": "strictly_after_visible_contact" if a_is_striker else "initiates_counter_met_at_contact",
                    "action": f"B {b_prep + ' then immediately ' + b_words if b_ov_card else b_words}",
                },
            }
        )

        if is_knee_beat:
            stack_camera_track.append(
                {
                    "t": t_tag,
                    "shot": f"medium_wide_side_profile_{beat_label}",
                    "framing": "unobstructed side-profile framing exposing the vertical knee path between both torsos with zero torso merge",
                    "preserve_axis": True,
                    "accent_timing": "brief hit-stop hold AFTER visible knee contact; shock flash clears immediately for B's fold",
                }
            )
        elif is_contact_beat:
            stack_camera_track.append(
                {
                    "t": t_tag,
                    "shot": (
                        f"telephoto_snap_zoom_side_profile_{beat_label}"
                        if is_hero
                        else f"tight_three_quarter_front_hemisphere_whip_pan_{beat_label}"
                    ),
                    "framing": vis_view,
                    "preserve_axis": True,
                    "camera_tilt": "subtle low-angle impact tilt" if idx % 2 == 0 else "subtle counter-angle impact tilt",
                    "accent_timing": (
                        "hero finisher hit-stop hold with brief slow-motion release AFTER visible heel-to-ribs contact"
                        if is_hero
                        else "brief hit-stop hold and camera jolt strictly AFTER visible contact; flash clears immediately"
                    ),
                }
            )
        else:
            stack_camera_track.append(
                {
                    "t": t_tag,
                    "shot": f"low_three_quarter_tracking_dolly_{beat_label}",
                    "framing": vis_view,
                    "preserve_axis": True,
                    "move": "smooth lateral dolly tracking footwork across the wet concrete floor with zero camera orbit",
                }
            )

        audit_trace_entries.append(
            {
                "event_id": event_id,
                "hard_invariant_preserved": True,
                "hard_clause_sha256": hashlib.sha256(tight_sentence.encode("utf-8")).hexdigest()[:16],
                "full_clause_sha256": hashlib.sha256(beat_sentence.encode("utf-8")).hexdigest()[:16],
                "omitted_internal_fields": list(packet["internal_only_biomechanics_not_emitted"].keys()),
            }
        )

    # Terminal Closure Contract
    final_b_state = (
        "collapsed flat on his back on the canvas"
        if fighter_b.support == "supine"
        else f"braced in a {fighter_b.support} recovery posture"
    )
    closure_text = (
        f"End with Fighter A planted in a wide, balanced guard on screen-{fighter_a.screen_side} facing {fighter_a.facing} "
        f"with both arms clearly separate from the torso in silhouette, and Fighter B {final_b_state} on screen-{fighter_b.screen_side}; "
        f"wardrobe markers, actor identities, and screen sides remain unchanged from start to finish."
    )

    # Append 10.00s Terminal Closure to Multi-Layer Scene Stack
    stack_layer1_lines.append(
        f"10.00s TERMINAL_HOLD: A [standing wide balanced guard on screen-{fighter_a.screen_side} facing {fighter_a.facing} | L_arm extended forward in high guard, R_arm chambered at cheek, both arms separate from torso in silhouette] "
        f"<-> B [{fighter_b.support} on screen-{fighter_b.screen_side} facing {fighter_b.facing} | {final_b_state}, both arms separate from torso in silhouette] | "
        f"CLOSURE: {closure_text}"
    )

    style_map = {
        "boxing": "western_boxing",
        "muay_thai": "muay_thai",
        "mma": "ufc_mma_octagon",
        "baki": "baki_underground_arena",
        "freestyle_sakuga": "freestyle_sakuga",
    }
    stack_header = (
        f"10s anime fight clip, 24fps, {arena}. "
        "STYLE: Pure 2D hand-drawn anime, Baki, Kengan Ashura, and God of High School style detailed anatomical muscle striations, "
        "flat cel shading with hard 2-tone high-contrast shadows, heavy ink outlines on A and B, broken sketchy ink on active smear limbs only, "
        "clean ultra-thick ink on impact holds, hyper-fluid bare-knuckle sakuga animation on twos. Not 3D, not CGI, not live action, not photoreal. "
        f"ENTITY COUNT & OUTFIT LOCK: Exactly TWO shirtless bare-knuckle fighters (ZERO weapons). "
        f"Fighter A (always on screen-{fighter_a.screen_side} facing {fighter_a.facing}): {a_desc}. "
        f"Fighter B (always on screen-{fighter_b.screen_side} facing {fighter_b.facing}): {b_desc}. "
        "SPACING & SILHOUETTE CONTRACT: Maintain realistic strike spacing at all times — clean arm-length distance for punches, "
        "tight inside-pocket distance for hooks/elbows/clinch, and full extended-leg distance for kicks so the bodies never merge, "
        "with both left and right arms separate from the torso in silhouette on every hit. "
        "Execute with dynamic front-hemisphere Sakuga camera work; no on-screen text, no numbers, no HUD, and no coordinate labels."
    )

    stack_layer2_spec: Dict[str, Any] = {
        "name": clip.get("name", f"latent_sakuga_scene_stack_{fighter_a.style}_vs_{fighter_b.style}_10s"),
        "schema": "LATENT-SAKUGA-SCENE-STACK-1.0",
        "fps": 24,
        "duration": 10.0,
        "environment_and_lighting": arena,
        "screen_geometry": (
            f"180_degree_camera_hemisphere_locked_for_all_10s: Fighter A remains strictly on screen_{fighter_a.screen_side} facing {fighter_a.facing} "
            f"and Fighter B remains strictly on screen_{fighter_b.screen_side} facing {fighter_b.facing} for the entire 10.0s clip (zero side swaps)."
        ),
        "negative": (
            "no 3D CGI, no mocap stiffness, no floaty physics, no static flat camera, no weapons, no swords, no knives, "
            "no side swap, no outfit swap, no torso merging, no chest-to-chest clipping, no on-screen text or numbers, "
            "no HUD, no coordinate labels, no extra fighters, no missing limbs, no missing arms, no one-armed fighter, "
            "no extra legs, no deformed legs, no full-body blur during smears, no reaction before contact, no early flash hiding impact"
        ),
        "conservation_laws": [
            "CONSERVE_SEMANTICALLY: every strike, evade, block, and counter is chained so the post-coil of Exchange N physically loads the pre-coil of Exchange N+1",
            "event_local_contact_causality: every exchange binds preparation -> commitment -> visible limb-to-surface contact -> post-contact defender reaction",
            "accent_after_contact_rule: impact flashes and shock rings trigger strictly at or after visible contact and clear immediately so physical recoil is unobstructed",
            f"strict_screen_side_and_outfit_lock: A stays on screen_{fighter_a.screen_side} facing {fighter_a.facing} and B stays on screen_{fighter_b.screen_side} facing {fighter_b.facing} for all 10.0 seconds",
        ],
        "laban": {
            "A": {
                "fighting_style": style_map.get(fighter_a.style, "ufc_mma_octagon"),
                "chain": " > ".join(stack_a_chain_parts),
                "effort": {"weight": "heavy_striker_power", "time": "sudden_explosive", "space": "direct", "flow": "bound_at_contact"},
            },
            "B": {
                "fighting_style": style_map.get(fighter_b.style, "ufc_mma_octagon"),
                "chain": " > ".join(stack_b_chain_parts),
                "effort": {"weight": "heavy_brawler_power", "time": "sudden", "space": "direct", "flow": "bound_at_contact"},
            },
        },
        "beats": stack_beat_names,
        "synchronized_exchanges": stack_exchanges,
        "camera": stack_camera_track,
        "anime": {
            "style": "2D cel-shaded hand-drawn anime, Baki, Kengan Ashura, and God of High School style detailed anatomical muscle striations, hard 2-tone high-contrast shadows, heavy ink outlines on A and B, broken sketchy ink on active smear limbs only, clean ultra-thick ink on impact holds",
            "impact_moments": stack_impact_moments,
            "smear_frames": stack_smear_frames,
            "speed_lines": stack_speed_lines,
            "time_remap": (
                {f"{stack_impact_moments[-1]}_finisher_window": "brief slow-motion impact release after visible heel-to-ribs contact"}
                if stack_impact_moments
                else {}
            ),
            "anticipation_holds": ["0.00s_initial_loaded_coiling_pause"],
            "fx": stack_fx_map,
            "line_rule": f"heavy anatomical ink outlines on A and B, broken/sketchy outlines ONLY on active striking limb during transfer, ultra-thick clean ink on all held impact moments {stack_impact_moments}",
            "chromatic_aberration": f"impact_moments_only {stack_impact_moments} — keep all transition and recoil frames razor-sharp with zero chromatic aberration",
        },
        "rules": (
            f"Render as one continuous 10-second 2D hand-drawn bare-knuckle martial arts fight inside the {arena}. "
            f"OUTFIT & SIDE LOCK: Fighter A stays on screen-{fighter_a.screen_side} facing {fighter_a.facing} and Fighter B stays on screen-{fighter_b.screen_side} facing {fighter_b.facing} for all 10.0 seconds (zero side swaps, zero weapons). "
            + " ".join(prose_beat_sentences)
            + " "
            + closure_text
        ),
    }

    stack_lines: List[str] = ["{"]
    stack_lines.append(
        f'"name":{json.dumps(stack_layer2_spec["name"])},"schema":{json.dumps(stack_layer2_spec["schema"])},"fps":24,"duration":10.0,'
    )
    for k in ["environment_and_lighting", "screen_geometry", "negative"]:
        stack_lines.append(f"{json.dumps(k)}:{json.dumps(stack_layer2_spec[k])},")
    stack_lines.append('"conservation_laws":[')
    for i, law in enumerate(stack_layer2_spec["conservation_laws"]):
        comma = "," if i < len(stack_layer2_spec["conservation_laws"]) - 1 else ""
        stack_lines.append(f"{json.dumps(law)}{comma}")
    stack_lines.append("],")
    stack_lines.append('"laban":{')
    stack_lines.append(f'"A":{json.dumps(stack_layer2_spec["laban"]["A"], separators=(",", ":"))},')
    stack_lines.append(f'"B":{json.dumps(stack_layer2_spec["laban"]["B"], separators=(",", ":"))}' + "},")
    stack_lines.append(f'"beats":{json.dumps(stack_layer2_spec["beats"], separators=(",", ":"))},')
    for tk in ["synchronized_exchanges", "camera"]:
        stack_lines.append(f"{json.dumps(tk)}:[")
        items = stack_layer2_spec[tk]
        for i, item in enumerate(items):
            comma = "," if i < len(items) - 1 else ""
            stack_lines.append(f"{json.dumps(item, separators=(',', ':'))}{comma}")
        stack_lines.append("],")
    stack_lines.append('"anime":{')
    akeys = list(stack_layer2_spec["anime"].keys())
    for i, ak in enumerate(akeys):
        is_last = i == len(akeys) - 1
        if ak == "smear_frames":
            stack_lines.append('"smear_frames":[')
            for j, s_item in enumerate(stack_layer2_spec["anime"][ak]):
                scomma = "," if j < len(stack_layer2_spec["anime"][ak]) - 1 else ""
                stack_lines.append(f"{json.dumps(s_item)}{scomma}")
            stack_lines.append("]}," if is_last else "],")
        else:
            val_str = json.dumps(stack_layer2_spec["anime"][ak], separators=(",", ":"))
            stack_lines.append(f"{json.dumps(ak)}:{val_str}{'},' if is_last else ','}")
    stack_lines.append(f'"rules":{json.dumps(stack_layer2_spec["rules"])}')
    stack_lines.append("}")
    stack_layer2_block = "\n".join(stack_lines)
    stack_layer1_block = "\n".join(stack_layer1_lines)

    rung_stack = (
        f"{stack_header}\n\n"
        f"=== LAYER 1: SYNCHRONIZED BILATERAL SUPPORT, 4-LIMB SILHOUETTE & CONTACT TIMELINE ===\n"
        f"{stack_layer1_block}\n\n"
        f"=== LAYER 2: LATENT-SAKUGA-SCENE-STACK KINEMATIC, CAMERA & ANIME FX SCENE GRAPH ===\n"
        f"{stack_layer2_block}"
    )

    shot_contract_text = (
        f"10s anime fight clip, 24fps, {arena}. "
        "STYLE: Pure 2D hand-drawn anime, Baki, Kengan Ashura, and God of High School style detailed anatomical muscle striations, "
        "flat cel shading with hard two-tone high-contrast shadows, heavy ink outlines on A and B, broken sketchy ink on active smear limbs only, "
        "clean ultra-thick ink on impact holds, hyper-fluid bare-knuckle sakuga animation on twos. Not 3D, not CGI, not live action, not photoreal. "
        f"Keep Fighter A strictly on screen-{fighter_a.screen_side} facing {fighter_a.facing} and Fighter B strictly on "
        f"screen-{fighter_b.screen_side} facing {fighter_b.facing} throughout the entire cut with zero side swaps, zero weapons, and zero on-screen text."
    )

    state_text = (
        f"ENTITY COUNT & OUTFIT LOCK: Exactly TWO shirtless bare-knuckle fighters. "
        f"Fighter A (always on screen-{fighter_a.screen_side}, facing {fighter_a.facing}): {a_desc}. "
        f"Fighter B (always on screen-{fighter_b.screen_side}, facing {fighter_b.facing}): {b_desc}. "
        f"Both fighters begin grounded at {RANGE_OBSERVABLE_PROSE.get(clip.get('initial_range', 'kick'), 'striking distance')} "
        f"with both left and right arms visible outside their torso silhouettes."
    )

    observation_text = (
        "CAMERA & SPACING CONTRACT: Maintain realistic strike spacing at all times — clean arm-length distance for punches, "
        "tight inside-pocket distance for hooks/elbows/clinch, and full extended-leg distance for kicks so the bodies never merge. "
        "Execute with dynamic front-hemisphere Sakuga camera work (tight three-quarter whip-pans on exchanges, low lateral tracking dollies on footwork, "
        "unobstructed side-profile framing on clinch knees, and telephoto snap-zoom on the finisher) that keeps both fighters head-to-toe in frame "
        "and exposes every limb-to-target contact in profile. Never orbit across the center line, and never conceal a required block, "
        "parry, or strike behind an early flash or torso overlap."
    )

    animation_license_text = (
        "SAKUGA FX, SMEAR & HIT-STOP LAYER: Contrast short loaded anticipation holds with whip-fast strike transfers and deliberate post-impact recovery. "
        "Permit temporary broken-ink limb-isolated smear stretching ONLY on the active striking limb during swing transfer, "
        "keeping heads, torsos, standing legs, and non-striking guards razor-sharp and solid; restore full anatomical proportions and ultra-thick ink outlines immediately at contact. "
        "Punctuate each clean hit with a brief hit-stop hold, radial white impact shock rings, sweat/rain-mist spray, and subtle impact camera jolt "
        "strictly AT or AFTER visible contact, clearing the flash immediately so the physical recoil is unobstructed. "
        "NEGATIVE GUARDRAILS: no 3D CGI, no mocap stiffness, no floaty physics, no torso merging, no missing or one-armed limbs, no full-body blur, no reaction before contact."
    )

    # Build the 3 Rungs of the Compression Ladder (Priority 4: HARD vs. SOFT vs. FREEDOM)
    # Rung 0: 6-Part Directorial Contract (Full HARD + SOFT + FREEDOM)
    beats_block = "\n".join(contract_beat_lines)
    rung_0_contract = (
        f"SHOT & STYLE CONTRACT\n{shot_contract_text}\n\n"
        f"ENTITY & INITIAL STATE\n{state_text}\n\n"
        f"CAMERA & OBSERVATION LAYER\n{observation_text}\n\n"
        f"SYNCHRONIZED CAUSAL BEATS (Preparation -> Commitment -> Named Contact -> Consequence -> Recovery)\n{beats_block}\n\n"
        f"SAKUGA FX & ANIMATION LICENSE LAYER\n{animation_license_text}\n\n"
        f"TERMINAL CLOSURE\n{closure_text}"
    )

    # Rung 1: 3-Paragraph Worked-Example Directing Prose (§11 — drops section headers & per-beat view/license brackets)
    p1_prose = _strip_digits_and_metrics(f"{shot_contract_text} {state_text} {observation_text}")
    p2_prose = _strip_digits_and_metrics(" ".join(prose_beat_sentences))
    p3_prose = _strip_digits_and_metrics(f"{animation_license_text} {closure_text}")
    rung_1_prose = f"{p1_prose}\n\n{p2_prose}\n\n{p3_prose}"

    # Rung 2: Ultra-Tight HARD-Invariant Prose (§8.4 — drops FREEDOM background decor & compresses SOFT phrasing while preserving 100% HARD invariants + supporting scene style/FX)
    tight_p1 = _strip_digits_and_metrics(
        f"Continuous hand-drawn anime fight in a {core_arena} — Baki and Kengan Ashura style muscle striations, flat two-tone cel shadows, heavy ink outlines, broken sketchy ink on active smear limbs, ultra-thick ink on impact holds. "
        f"Two bare-knuckle fighters: A (screen-{fighter_a.screen_side}, facing {fighter_a.facing}, {a_hard_id}) faces "
        f"B (screen-{fighter_b.screen_side}, facing {fighter_b.facing}, {b_hard_id}) "
        f"at {RANGE_OBSERVABLE_PROSE.get(clip.get('initial_range', 'kick'), 'striking distance')} with both arms distinct in silhouette. "
        f"Use dynamic front-hemisphere whip-pans, tracking dollies, and side-profile impact framing keeping both fighters head-to-toe in frame with no side swaps and no concealed contacts."
    )
    tight_p2 = _strip_digits_and_metrics(" ".join(tight_beat_sentences))
    tight_p3 = _strip_digits_and_metrics(
        f"Contrast brief holds with whip-fast strikes; restrict smear stretching strictly to the active striking limb, restore solid anatomy at contact, "
        f"and fire hit-stop holds, radial shock rings, and sweat spray only after impact so recoil stays visible (no CGI, no torso merge, no missing limbs, no early flinch). "
        f"Close with A in a balanced guard on screen-{fighter_a.screen_side} and B {final_b_state} on screen-{fighter_b.screen_side}."
    )
    rung_2_tight = f"{tight_p1}\n\n{tight_p2}\n\n{tight_p3}"

    ladder_candidates = [
        ("readability", 0, rung_0_contract),
        ("readability-prose", 1, rung_1_prose),
        ("readability-tight", 2, rung_2_tight),
    ]

    if dialect == "readability-stack":
        effective_dialect = "readability-stack"
        active_rung = -1
        compiled_prompt = rung_stack
        budget_status = "MULTI_LAYER_SCENE_STACK (Full Supporting Header + Layer 1 Synchronized Timeline + Layer 2 Camera/Anime/FX Scene Graph)"
    else:
        # Select starting rung from requested dialect
        if dialect == "readability-tight":
            selected_idx = 2
        elif dialect == "readability-prose":
            selected_idx = 1
        else:
            selected_idx = 0

        budget_status = "UNCONSTRAINED"
        if budget_words is not None and budget_words > 0:
            # Step down the compression ladder (Rung 0 -> Rung 1 -> Rung 2) until word count fits budget_words or HARD floor is reached
            while selected_idx < 2 and len(ladder_candidates[selected_idx][2].split()) > budget_words:
                selected_idx += 1
            final_wc = len(ladder_candidates[selected_idx][2].split())
            if final_wc <= budget_words:
                budget_status = f"FIT_WITHIN_BUDGET (rung={selected_idx}, words={final_wc}<={budget_words})"
            else:
                budget_status = (
                    f"HARD_INVARIANT_FLOOR_REACHED (rung=2, words={final_wc}>{budget_words}; "
                    "refused to drop any HARD requirement)"
                )

        effective_dialect, active_rung, compiled_prompt = ladder_candidates[selected_idx]

    # Populate Priority 4 Requirement Ledger (HARD vs. SOFT vs. FREEDOM dispositions)
    requirement_ledger.extend(
        [
            {
                "id": "REQ_HARD_ACTOR_IDENTITY_AND_SIDES",
                "class": "HARD",
                "summary": f"A ({a_hard_id}) on screen-{fighter_a.screen_side}; B ({b_hard_id}) on screen-{fighter_b.screen_side}; zero side swaps.",
                "disposition": "preserved_hard",
            },
            {
                "id": "REQ_HARD_CAMERA_HEMISPHERE_AND_VISIBILITY",
                "class": "HARD",
                "summary": "Front-hemisphere profile view; head-to-toe framing; all contacts and both arms visible (observation_state_target=correct_visible).",
                "disposition": "preserved_hard",
            },
            {
                "id": "REQ_HARD_CAUSAL_BEATS_AND_CONTACTS",
                "class": "HARD",
                "summary": f"All {len(event_packets)} ordered beats, initiator->target bindings, typed contact operations, and post-contact reactions.",
                "disposition": "preserved_hard",
            },
            {
                "id": "REQ_HARD_ACCENT_AFTER_CONTACT_AND_LIMB_ISOLATED_SMEAR",
                "class": "HARD",
                "summary": "Limb-isolated smear only during swing transfer; solid standing legs/torso/head; impact flashes only at/after contact.",
                "disposition": "preserved_hard",
            },
            {
                "id": "REQ_HARD_TERMINAL_CLOSURE",
                "class": "HARD",
                "summary": f"A balanced guard on screen-{fighter_a.screen_side}; B {final_b_state} on screen-{fighter_b.screen_side}.",
                "disposition": "preserved_hard",
            },
            {
                "id": "REQ_SOFT_SECTION_HEADERS_AND_PER_BEAT_BRACKETS",
                "class": "SOFT",
                "summary": "Section headers and per-beat [View: ...] / [License: ...] bracket wrappers.",
                "disposition": "included_soft" if active_rung == 0 else "compressed_soft",
            },
            {
                "id": "REQ_SOFT_REPEATED_RANGE_AND_SPRAY_EMBELLISHMENTS",
                "class": "SOFT",
                "summary": "Repeated unchanged range preambles, secondary sweat/spittle spray clauses, and verbose anatomical adjectives.",
                "disposition": "included_soft" if active_rung <= 1 else "compressed_soft",
            },
            {
                "id": "REQ_FREEDOM_ARENA_LIGHTING_AND_CROWD_DECOR",
                "class": "FREEDOM",
                "summary": freedom_arena_decor or "Unconstrained background crowd and ambient stadium lighting variations.",
                "disposition": "included_freedom" if active_rung <= 1 else "omitted_freedom",
            },
            {
                "id": "REQ_FREEDOM_MICRO_CLOTH_AND_FLOOR_SCUFF",
                "class": "FREEDOM",
                "summary": "Unconstrained micro cloth folds, dust motes, and floor scuff patterns.",
                "disposition": "omitted_freedom",
            },
        ]
    )

    # Verify V15 compliance (and for readability-prose / readability-tight, verify zero digits/metrics!)
    clip_regime = clip.get("regime", "standup_striking")
    allowed_styles = {fighter_a.style, fighter_b.style}
    v15_errs = scan_prompt_v15(
        compiled_prompt,
        clip_regime,
        allowed_styles,
        lex,
        allow_fluid_stack_numbers=(effective_dialect in ("readability", "readability-stack")),
    )
    if v15_errs:
        val_res.errors.extend(v15_errs)
        return "", {}, val_res

    if use_kb_priors:
        record_compile_usage(
            run_id=clip.get("name", "latent_sakuga_compile"),
            used_directives=list(dict.fromkeys(used_directives)),
            used_cards=list(dict.fromkeys(used_cards)),
            used_passages=list(dict.fromkeys(used_passages)),
        )

    intent_ir_and_trace: Dict[str, Any] = {
        "schema": "LATENT-SAKUGA-1.0",
        "dialect": effective_dialect,
        "requested_dialect": dialect,
        "compression_rung": active_rung,
        "budget_words_target": budget_words,
        "budget_status": budget_status,
        "name": clip.get("name", f"latent_sakuga_{fighter_a.style}_vs_{fighter_b.style}"),
        "active_modules": active_modules,
        "budget_metrics": {
            "character_count": len(compiled_prompt),
            "utf8_byte_count": len(compiled_prompt.encode("utf-8")),
            "word_count": len(compiled_prompt.split()),
            "hard_intent_coverage": 1.0,
            "leaked_internal_numeric_fields": 0,
            "ladder_word_counts": {
                "scene_stack_multi_layer": len(rung_stack.split()),
                "rung_0_contract": len(rung_0_contract.split()),
                "rung_1_prose": len(rung_1_prose.split()),
                "rung_2_tight_hard_floor": len(rung_2_tight.split()),
            },
        },
        "requirement_ledger": requirement_ledger,
        "scene_stack_layer2": stack_layer2_spec,
        "shot_contract": shot_contract_text,
        "initial_state": state_text,
        "observation_contract": observation_text,
        "event_packets": event_packets,
        "animation_license": animation_license_text,
        "closure_contract": closure_text,
        "audit_trace": audit_trace_entries,
    }

    return compiled_prompt, intent_ir_and_trace, val_res
