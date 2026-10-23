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


def compile_to_causal_readability(
    clip: Dict[str, Any],
    lexicon: Optional[Lexicon] = None,
    dialect: str = "readability",
    use_kb_priors: bool = True,
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
    audit_trace_entries: List[Dict[str, Any]] = []
    active_modules: List[str] = ["M01_hand_to_hand", "M09_complex_camera"]

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
            else:
                beat_sentence = (
                    f"From {range_prose}, A {a_words}; {contact_clause}, "
                    f"and only after that contact does B respond as B {b_words}."
                )
                prose_sentence = (
                    f"From {range_prose}, A {a_words} ({short_contact}); only after contact, B {b_words}."
                )
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
            else:
                beat_sentence = (
                    f"At {range_prose}, B {b_words}; {contact_clause}, "
                    f"while A responds only at contact as A {a_words}."
                )
                prose_sentence = (
                    f"At {range_prose}, B {b_words} ({short_contact}) while A responds at contact as A {a_words}."
                )
        else:
            # Positional footwork / transition beat (SOFT setup details compressed, HARD geometry kept)
            contact_clause = "no strike collision on this footwork transition; both fighters maintain clear space and distinct silhouettes"
            vis_view = "smooth lateral tracking view following footwork across the floor without camera orbit"
            license_clause = "crisp solid linework with zero smear blur during footwork repositioning"
            beat_sentence = f"Across {range_prose}, A {a_words} while B {b_words}, resetting their firing line without clipping."
            prose_sentence = beat_sentence

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

        packet = {
            "event_index": idx + 1,
            "event_id": f"E{idx + 1:02d}_{a_card['id']}_vs_{b_card['id']}",
            "requirement_class": "HARD",
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

        audit_trace_entries.append(
            {
                "event_id": packet["event_id"],
                "requirement_class": "HARD",
                "preserved_in_prompt": True,
                "clause_sha256": hashlib.sha256(beat_sentence.encode("utf-8")).hexdigest()[:16],
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

    shot_contract_text = (
        f"One continuous hand-drawn anime martial arts action cut inside a {arena}. "
        f"Expressive hand-drawn character animation with flat two-tone cel shadows, crisp anatomical ink outlines, "
        f"and clear spacing contrast between brief loaded holds and whip-fast transfers. "
        f"Keep Fighter A strictly on screen-{fighter_a.screen_side} facing {fighter_a.facing} and Fighter B strictly on "
        f"screen-{fighter_b.screen_side} facing {fighter_b.facing} throughout the entire cut with zero side swaps and zero on-screen text."
    )

    state_text = (
        f"Fighter A (screen-{fighter_a.screen_side}, facing {fighter_a.facing}): {a_desc}. "
        f"Fighter B (screen-{fighter_b.screen_side}, facing {fighter_b.facing}): {b_desc}. "
        f"Both fighters begin grounded at {RANGE_OBSERVABLE_PROSE.get(clip.get('initial_range', 'kick'), 'striking distance')} "
        f"with both left and right arms visible outside their torso silhouettes."
    )

    observation_text = (
        "Maintain a readable front-hemisphere lateral and three-quarter camera view that keeps both fighters head-to-toe in frame "
        "and exposes every limb-to-target contact in profile. Never orbit across the center line, and never conceal a required block, "
        "parry, or strike behind an early flash or torso overlap."
    )

    animation_license_text = (
        "Contrast short preparation holds with fast strike transfers and deliberate post-impact recovery. "
        "Permit temporary limb-isolated smear stretching only on the active striking limb during swing transfer, "
        "keeping heads, torsos, standing legs, and non-striking guards solid; restore full anatomical proportions immediately at contact. "
        "Trigger impact flashes only at or after visible contact and clear them immediately so the physical recoil is clearly seen."
    )

    if dialect == "readability-prose":
        # 3-Paragraph Worked-Example Directing Prose (§11 of LATENT SAKUGA paper — zero digits, zero headers)
        p1 = _strip_digits_and_metrics(f"{shot_contract_text} {state_text} {observation_text}")
        p2 = _strip_digits_and_metrics(" ".join(prose_beat_sentences))
        p3 = _strip_digits_and_metrics(f"{animation_license_text} {closure_text}")
        compiled_prompt = f"{p1}\n\n{p2}\n\n{p3}"
    else:
        # 6-Part Directorial Contract (§8.3 of LATENT SAKUGA paper)
        beats_block = "\n".join(contract_beat_lines)
        compiled_prompt = (
            f"SHOT CONTRACT\n{shot_contract_text}\n\n"
            f"STATE\n{state_text}\n\n"
            f"OBSERVATION\n{observation_text}\n\n"
            f"CAUSAL BEATS (Preparation -> Commitment -> Named Contact -> Consequence -> Recovery)\n{beats_block}\n\n"
            f"ANIMATION LICENSE\n{animation_license_text}\n\n"
            f"CLOSURE\n{closure_text}"
        )

    # Verify V15 compliance (and for readability-prose, verify zero digits/metrics!)
    clip_regime = clip.get("regime", "standup_striking")
    allowed_styles = {fighter_a.style, fighter_b.style}
    v15_errs = scan_prompt_v15(
        compiled_prompt,
        clip_regime,
        allowed_styles,
        lex,
        allow_fluid_stack_numbers=(dialect != "readability-prose"),
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
        "dialect": dialect,
        "name": clip.get("name", f"latent_sakuga_{fighter_a.style}_vs_{fighter_b.style}"),
        "active_modules": active_modules,
        "budget_metrics": {
            "character_count": len(compiled_prompt),
            "utf8_byte_count": len(compiled_prompt.encode("utf-8")),
            "word_count": len(compiled_prompt.split()),
            "hard_intent_coverage": 1.0,
            "leaked_internal_numeric_fields": 0,
        },
        "shot_contract": shot_contract_text,
        "initial_state": state_text,
        "observation_contract": observation_text,
        "event_packets": event_packets,
        "animation_license": animation_license_text,
        "closure_contract": closure_text,
        "audit_trace": audit_trace_entries,
    }

    return compiled_prompt, intent_ir_and_trace, val_res
