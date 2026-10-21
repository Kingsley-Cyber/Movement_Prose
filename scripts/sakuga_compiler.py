#!/usr/bin/env python3
"""
SAKUGA-MLLM-3.1-CAUSAL Deterministic Compiler, 20-Rule Physics Linter,
2-Layer Unrolled Fluid Stack Generator & Multi-Clip Stitcher
For Seedance 2.0 Mini, Seedance 2.5, and Kling AI Video YouTube Workflows.
"""

import argparse
import copy
import json
import math
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

CANONICAL_TOP_KEY_ORDER = [
    "name",
    "schema",
    "fps",
    "duration",
    "axes",
    "screen_geometry",
    "negative",
    "conservation_laws",
    "laban",
    "beats",
    "A_beats",
    "B_track",
    # Prop tracks are inserted dynamically right here (after B_track, before camera)
    "camera",
    "anime",
    "rules",
]

CANONICAL_A_BEAT_KEY_ORDER = [
    "t",
    "beat",
    "causal",
    "pos",
    "vel",
    "axis",
    "arc",
    "support",
    "contact",
    "limbs",
    "pose",
]

CANONICAL_B_BEAT_KEY_ORDER = [
    "t",
    "pos",
    "axis",
    "support",
    "contact",
    "launch_vel",
    "action",
    "pose",
]

FORBIDDEN_BEAT_KEYS = {
    "q_root",
    "q_rig",
    "slerp",
    "style",
    "fx_preset",
    "camera_tempo",
    "duration_frames",
    "expression",
    "contrast",
    "Sp",
    "LUL",
    "RUL",
    "LL",
    "RL",
    "LA",
    "RA",
    "LFA",
    "RFA",
}

DEFAULT_HEADER_TEMPLATE = (
    "{duration:.0f}s anime fight clip, {fps}fps. STYLE: 2D hand-drawn anime, "
    "cel-shaded flat colors, heavy ink outlines, intense close-quarters sakuga "
    "martial arts animation on twos with limb-isolated smear frames, camera shake "
    "on impacts, and held impact frames, {background}. Not 3D, not CGI, not live "
    "action, not photoreal. ENTITY COUNT: {entities}. Render as one physically "
    "continuous combat event where every movement emerges visibly from the force "
    "and momentum of the previous state; no on-screen text, no numbers, no HUD, "
    "and no coordinate labels."
)


def extract_prop_tracks(spec: Dict[str, Any]) -> List[str]:
    """Identify prop state-machine tracks (e.g., kunai, wakizashi, katana, bo_staff)."""
    reserved = set(CANONICAL_TOP_KEY_ORDER) | {"header", "meta", "layer_1_timeline"}
    prop_keys = []
    for k, v in spec.items():
        if k not in reserved and isinstance(v, list):
            prop_keys.append(k)
    return prop_keys


def order_beat_dict(beat: Dict[str, Any], key_order: List[str]) -> Dict[str, Any]:
    ordered = {}
    for k in key_order:
        if k in beat:
            ordered[k] = beat[k]
    for k, v in beat.items():
        if k not in ordered:
            ordered[k] = v
    return ordered


def order_spec_causally(spec: Dict[str, Any]) -> Dict[str, Any]:
    """Enforce Decoder-Only MLLM Causal KV-Cache Track Ordering (Decision 09 & 14)."""
    prop_keys = extract_prop_tracks(spec)
    ordered: Dict[str, Any] = {}

    pre_prop_keys = [
        "name",
        "schema",
        "fps",
        "duration",
        "axes",
        "screen_geometry",
        "negative",
        "conservation_laws",
        "laban",
        "beats",
        "A_beats",
        "B_track",
    ]
    post_prop_keys = ["camera", "anime", "rules"]

    for k in pre_prop_keys:
        if k in spec:
            if k == "A_beats":
                ordered[k] = [
                    order_beat_dict(b, CANONICAL_A_BEAT_KEY_ORDER) for b in spec[k]
                ]
            elif k == "B_track":
                ordered[k] = [
                    order_beat_dict(b, CANONICAL_B_BEAT_KEY_ORDER) for b in spec[k]
                ]
            else:
                ordered[k] = spec[k]

    for pk in prop_keys:
        ordered[pk] = spec[pk]

    for k in post_prop_keys:
        if k in spec:
            ordered[k] = spec[k]

    return ordered


def build_layer1_timeline(spec: Dict[str, Any]) -> List[str]:
    """
    Generate Layer 1 (Continuous Support, 5-Phase Force-Event & Prop Timeline in
    Labanotation-as-Words) from a SAKUGA-MLLM-3.1-CAUSAL spec (Decision 18, 19, 20).
    If the spec defines an explicit 'layer_1_timeline' list of strings, use that directly.
    Otherwise, synthesize it deterministically from prop tracks, A_beats, and B_track.
    """
    if "layer_1_timeline" in spec and isinstance(spec["layer_1_timeline"], list):
        return [str(line) for line in spec["layer_1_timeline"]]

    lines: List[str] = [
        "MOVEMENT LANGUAGE: Each line states <seconds> <performer>: SUPPORT (what bears weight; NO SUPPORT = airborne) | bilateral limb gestures & orientation (both L_arm and R_arm explicitly placed) | 5-phase force events (windup -> drive -> CONTACT -> reaction -> follow-through) | path (continuous translation in metres). Every key action is unrolled into separate timestamps for windup/entry, drive/apex, contact, and landing/recovery so nothing is left to inference."
    ]

    # Summarize prop tracks first
    for pk in extract_prop_tracks(spec):
        p_items = spec.get(pk, [])
        if p_items:
            chain_parts = []
            for p in p_items:
                t_val = float(p.get("t", 0.0))
                owner = p.get("owner", "")
                state = p.get("state", "")
                event = p.get("event", p.get("grip", ""))
                detail = f"{state} ({owner}" + (f", {event})" if event else ")")
                chain_parts.append(f"{t_val:.2f}s {detail}")
            lines.append(f"{pk.upper()} CONTINUITY: " + " -> ".join(chain_parts) + ".")

    # Merge A_beats and B_track chronologically
    events: List[Tuple[float, int, str]] = []
    for ab in spec.get("A_beats", []):
        t_val = float(ab.get("t", 0.0))
        sup = ab.get("support", "")
        sup_label = (
            f"NO SUPPORT ({sup})"
            if "none_airborne" in sup
            else f"SUPPORT {sup.replace('_', ' ')}"
        )
        limbs = ab.get("limbs", "")
        contact = ab.get("contact", "")
        pose = ab.get("pose", "")
        parts = [f"{t_val:0.2f} A: {sup_label}", limbs]
        if contact:
            parts.append(f"FE ({contact})")
        parts.append(pose)
        events.append((t_val, 0, " | ".join(parts)))

    for bb in spec.get("B_track", []):
        t_val = float(bb.get("t", 0.0))
        sup = bb.get("support", "")
        sup_label = (
            f"NO SUPPORT ({sup})"
            if "none_airborne" in sup
            else f"SUPPORT {sup.replace('_', ' ')}"
        )
        contact = bb.get("contact", "")
        pose = bb.get("pose", "")
        parts = [f"{t_val:0.2f} B: {sup_label}"]
        if contact:
            parts.append(f"FE reaction ({contact})")
        parts.append(pose)
        events.append((t_val, 1, " | ".join(parts)))

    events.sort(key=lambda x: (x[0], x[1]))
    for _, _, line_text in events:
        lines.append(line_text)

    return lines


def lint_clip(spec: Dict[str, Any]) -> Tuple[List[str], List[str]]:
    """
    Validate a clip specification against all 20 Empirical Decisions in the SOP.
    Returns (errors, warnings).
    """
    errors: List[str] = []
    warnings: List[str] = []

    # 1. Schema version check
    schema = spec.get("schema", "")
    if schema != "SAKUGA-MLLM-3.1-CAUSAL":
        errors.append(
            f"[Decision 14] Invalid or missing schema '{schema}'. Expected 'SAKUGA-MLLM-3.1-CAUSAL'."
        )

    # 2. Required top-level tracks
    for req_key in [
        "name",
        "axes",
        "screen_geometry",
        "negative",
        "conservation_laws",
        "laban",
        "beats",
        "A_beats",
        "B_track",
        "camera",
        "anime",
        "rules",
    ]:
        if req_key not in spec:
            errors.append(f"[Decision 09] Missing mandatory top-level track: '{req_key}'.")

    # 3. Anti-HUD & Bilateral Arm negative check (Decision 02 & Decision 20)
    neg = spec.get("negative", "").lower()
    if "no on-screen text" not in neg or "no hud" not in neg:
        warnings.append(
            "[Decision 02] 'negative' should explicitly include 'no on-screen text or numbers, no HUD'."
        )
    if "no missing arms" not in neg and "no one-armed" not in neg:
        warnings.append(
            "[Decision 20] 'negative' should explicitly include 'no missing arms, no one-armed fighter, both left and right arms and hands always visible'."
        )

    # 4. Validate A_beats (Decisions 01, 03, 04, 13, 14, 16, 18, 19, 20)
    a_beats = spec.get("A_beats", [])
    b_track = spec.get("B_track", [])
    b_by_t = {round(float(b.get("t", -1)), 2): b for b in b_track}

    seen_screen_sides = set()
    prev_t = -1.0
    prev_support = ""

    for idx, beat in enumerate(a_beats):
        t = float(beat.get("t", -1))
        if t <= prev_t:
            errors.append(f"[A_beats[{idx}]] Non-monotonic timestamp t={t} after t={prev_t}.")

        # Check forbidden bloat keys (Decisions 01, 04, 13)
        bad_keys = set(beat.keys()) & FORBIDDEN_BEAT_KEYS
        if bad_keys:
            errors.append(
                f"[Decision 01/04/13] A_beats t={t} contains forbidden bloat keys: {sorted(bad_keys)}. "
                "Keep A_beats strictly kinematic + causal."
            )

        # Check required per-beat keys
        for rk in ["t", "beat", "causal", "pos", "vel", "axis", "arc", "support", "limbs", "pose"]:
            if rk not in beat:
                errors.append(f"[Decision 14] A_beats t={t} is missing required key '{rk}'.")

        # Check negation leakage & meta-negation inside beat (Decision 03 & Decision 19)
        beat_text = json.dumps(beat)
        if re.search(r"\bNOT\b", beat_text) or re.search(
            r"\bnot a (kick|punch|throw|slash|flip)\b", beat_text, re.IGNORECASE
        ):
            errors.append(
                f"[Decision 03] Negation leakage detected in A_beats t={t}. "
                "Never write 'NOT' inside beats; use positive-only support locks."
            )
        if re.search(r"should not (float|drift|hover)", beat_text, re.IGNORECASE):
            errors.append(
                f"[Decision 19] Meta-negation leakage ('should not float/drift') in A_beats t={t}. "
                "State positive downward velocity/gravity instead."
            )

        # Check XML/HTML markup tag pollution inside beat (Decision 19)
        if re.search(r"<[a-zA-Z_][a-zA-Z0-9_-]*>", beat_text):
            errors.append(
                f"[Decision 19] Markup tag '<...>' detected inside A_beats t={t}. "
                "Never wrap motions or events in '<>' tags; they activate the HTML/XML label prior."
            )

        # Decision 18: Check airborne-to-wall jump without intermediate ground landing
        curr_support = beat.get("support", "").lower()
        if (
            "none_airborne" in prev_support
            and ("wall" in curr_support or "pillar" in curr_support)
            and (t - prev_t) > 0.65
        ):
            warnings.append(
                f"[Decision 18] A_beats t={t} transitions directly from airborne (t={prev_t}) to wall/pillar support "
                f"across {t - prev_t:.2f}s without an intermediate floor-landing keyframe. Unroll the floor landing!"
            )
        prev_support = curr_support
        prev_t = t

        # Decision 20: Bilateral Two-Arm Silhouette Check
        limbs_str = beat.get("limbs", "")
        has_both_arms = bool(
            re.search(r"\b(both_arms|both_hands|arms)\s*:", limbs_str)
            or (
                re.search(r"\b(L_arm|L_hand|L)\s*:", limbs_str)
                and re.search(r"\b(R_arm|R_hand|R)\s*:", limbs_str)
            )
        )
        if not has_both_arms:
            warnings.append(
                f"[Decision 20] A_beats t={t} 'limbs' does not explicitly lock both left and right arms "
                f"('L_arm'/'R_arm' or 'both_arms'). Explicit bilateral arm placement prevents one-arm silhouette occlusion."
            )

        # Check causal edge format (Decision 14)
        causal_str = beat.get("causal", "")
        if not re.match(r"^C\d+", causal_str):
            errors.append(
                f"[Decision 14] A_beats t={t} 'causal' must start with a node ID (e.g. 'C01: ...'). Got: '{causal_str}'."
            )

        # Track screen_side for Decision 16 (Dynamic Midpoint Screen Cross)
        axis_str = beat.get("axis", "")
        if "screen_side:left" in axis_str or "crossing_left_to_right" in axis_str:
            seen_screen_sides.add("left")
        if "screen_side:right" in axis_str or "crossing_left_to_right" in axis_str:
            seen_screen_sides.add("right")

        # Check 3-Phase Contact Contract (Decision 14)
        if "contact" in beat:
            c_str = beat["contact"]
            is_evasion = c_str.startswith("evasion_corridor:")
            is_hold = "hold" in beat.get("causal", "")
            if not is_evasion and not is_hold:
                if not ("pre:" in c_str and "hit:" in c_str and "post:" in c_str):
                    errors.append(
                        f"[Decision 14] A_beats t={t} 'contact' must use 3-phase contract "
                        "'pre:... -> hit:... -> post:...' (or 'evasion_corridor:...')."
                    )

        # Check Close-Quarters distance against B_track (Decision 10)
        t_key = round(t, 2)
        if t_key in b_by_t and "pos" in beat and "pos" in b_by_t[t_key]:
            apos = beat["pos"]
            bpos = b_by_t[t_key]["pos"]
            dz = abs(float(apos[2]) - float(bpos[2]))
            if dz > 1.65:
                warnings.append(
                    f"[Decision 10] A_beats t={t} z-separation is {dz:.2f}m (> 1.65m close-quarters pocket)."
                )

    if len(seen_screen_sides) < 2:
        warnings.append(
            "[Decision 16] Fighter A stays on a single screen_side for the entire clip. "
            "Include a physical midpoint cross (screen_left -> screen_right around t=4.8s-5.4s) to prevent a static standoff."
        )

    # 5. Validate B_track (Decision 03 & Decision 11)
    for idx, bbeat in enumerate(b_track):
        t = bbeat.get("t", idx)
        for rk in ["t", "pos", "axis", "support", "action", "pose"]:
            if rk not in bbeat:
                errors.append(f"[Decision 11] B_track t={t} is missing required key '{rk}'.")
        b_text = json.dumps(bbeat)
        if re.search(r"\bNOT\b", b_text):
            errors.append(f"[Decision 03] Negation leakage ('NOT') detected in B_track t={t}.")

    # 6. Validate Prop Tracks (Decision 15 & Decision 16: No Hovering Props)
    for pk in extract_prop_tracks(spec):
        for pbeat in spec[pk]:
            p_text = json.dumps(pbeat).lower()
            if "hover" in p_text:
                errors.append(
                    f"[Decision 16] Prop track '{pk}' at t={pbeat.get('t')} uses 'hover/hovering'. "
                    "Use a true parabolic upward launch apex (y=2.0m-2.2m) and falling catch."
                )

    # 7. Validate Camera (Decision 10 & Decision 12)
    for cbeat in spec.get("camera", []):
        t = cbeat.get("t", "?")
        fov = cbeat.get("fov", 35)
        if fov > 40 or fov < 24:
            warnings.append(
                f"[Decision 10] Camera t={t} has fov={fov} (recommended close-quarters range: 28-38)."
            )
        if "look" not in cbeat:
            errors.append(f"[Decision 12] Camera t={t} is missing mandatory 'look' target anchor.")

    # 8. Validate Smear Isolation (Decision 04/07)
    anime = spec.get("anime", {})
    for sm in anime.get("smear_frames", []):
        if "solid" not in sm.lower():
            warnings.append(
                f"[Decision 04] Smear frame '{sm}' should explicitly state that head/torso 'stay solid'."
            )

    return errors, warnings


STYLE_PRESETS: Dict[str, Dict[str, str]] = {
    "cel_default": {},
    "genga": {
        "header_style": "2D hand-drawn rough anime key-animation (genga) on cream animation paper, graphite pencil construction lines, red and blue animator shadow layout markings, uncolored raw sakuga",
        "anime_style": "2D hand-drawn rough anime key-animation (genga) on cream paper, visible graphite pencil lines, red/blue/yellow layout shading lines, intense close-quarters sakuga on twos",
        "line_rule": "rough sketchy graphite pencil outlines on A and B, red and blue layout construction lines on active smear limbs, heavy pencil impact frames",
    },
    "sumi_ink": {
        "header_style": "Traditional Japanese sumi-e ink wash painting in motion, heavy black calligraphy brush strokes on textured rice paper, stark black-and-white monochrome with crimson accents",
        "anime_style": "2D traditional sumi-e ink wash martial arts animation on twos, dry-brush textures, stark black ink on rice paper with crimson accents",
        "line_rule": "variable-width wet sumi calligraphy brush outlines on A and B, dry-brush bristle streaks on active smear limbs, heavy ink-splatter impact frames",
    },
    "trigger_neon": {
        "header_style": "Studio Trigger style hyper-stylized 2D anime, neon cyan and magenta rim lighting, razor-sharp angular shadows, exaggerated foreshortening, four-point star impact flashes",
        "anime_style": "Hyper-stylized 2D cel anime, hard angular black shadows, neon cyan and magenta rim lights, explosive sakuga on twos",
        "line_rule": "ultra-bold black ink outlines, neon chromatic split on impact frames, sharp geometric smear streaks ONLY on active smear limbs",
    },
    "retro_90s": {
        "header_style": "1990s hand-painted acetate cel anime, 35mm film grain, deep muted shadow palette, halation glow on steel highlights, hand-painted watercolor background",
        "anime_style": "1990s OVA hand-painted acetate cel anime, subtle 35mm film grain, high-contrast retro cel shadows, gritty martial arts sakuga on twos",
        "line_rule": "crisp dark-ink acetate cel outlines, classic 90s white frame-flash on impacts, broken cel outlines ONLY on active smear limbs",
    },
    "ufotable": {
        "header_style": "High-contrast dark-fantasy 2D cel anime with hand-drawn ukiyo-e elemental water and fire slashes trailing the blade arcs",
        "anime_style": "2D dark-fantasy cel-shaded anime with hand-drawn ukiyo-e elemental ribbons trailing weapon arcs, intense sakuga on twos",
        "line_rule": "crisp heavy ink outlines on A and B, stylized ukiyo-e elemental wave/flame trails ONLY on active weapon and smear arcs",
    },
}


def apply_taste_layer(
    spec: Dict[str, Any], header_text: str, taste: str, style_preset: str = "cel_default"
) -> Tuple[Dict[str, Any], str]:
    """
    Apply optional Tier 2 Taste / Seasoning Layer (Decision 17) and Experimental Style Presets
    (Section 5.1) without bloating A_beats keys.
    """
    spec = copy.deepcopy(spec)

    if style_preset in STYLE_PRESETS and style_preset != "cel_default":
        preset = STYLE_PRESETS[style_preset]
        header_text = re.sub(
            r"STYLE:\s*2D hand-drawn anime,\s*cel-shaded flat colors,\s*heavy ink outlines",
            f"STYLE: {preset['header_style']}",
            header_text,
        )
        anime = spec.setdefault("anime", {})
        anime["style"] = preset["anime_style"]
        anime["line_rule"] = preset["line_rule"]

    if taste == "clean":
        return spec, header_text

    if taste == "nakamura":
        # Upgrade header for hard 2-tone cel & camera overshoot
        header_text = header_text.replace(
            "cel-shaded flat colors",
            "flat cel shading with hard 2-tone shadow boundaries, no soft airbrush gradients",
        )
        # Lock preserve_axis and no_orbit in camera
        for cbeat in spec.get("camera", []):
            cbeat["preserve_axis"] = True
            if "move" in cbeat and "no_orbit" not in cbeat["move"]:
                cbeat["move"] = f"{cbeat['move']}, no_orbit"
        # Add localized chromatic aberration in anime track
        anime = spec.setdefault("anime", {})
        impacts = anime.get("impact_frames", [0.8, 1.5, 3.4, 7.6])
        anime["chromatic_aberration"] = (
            f"impact_frames_only {impacts} — keep all spinning and transition frames razor-sharp with zero chromatic aberration"
        )
        if "hard 2-tone" not in anime.get("style", ""):
            anime["style"] = (
                "2D hand-drawn anime, flat cel shading, hard 2-tone shadow boundaries, strong heavy ink line, no soft shading gradients, "
                + anime.get("style", "")
            )
    return spec, header_text


def format_sakuga_prompt(
    spec: Dict[str, Any], header_text: str, stack: bool = False
) -> str:
    """
    Format the causally ordered JSON spec into either:
      - Mode 1 (stack=False): Single-Layer Compact SAKUGA-MLLM-3.1-CAUSAL JSON (Gold-Masters #1 & #2)
      - Mode 2 (stack=True):  2-Layer Unrolled Fluid Stack (Layer 1 Continuous Support/Force-Event/Prop
                              Labanotation-as-Words Timeline + Layer 2 SAKUGA-MLLM-3.1-CAUSAL JSON, Gold-Master #3+)
    """
    ordered = order_spec_causally(spec)
    lines: List[str] = ["{"]

    # Line 1: name, schema, fps, duration
    head_keys = ["name", "schema", "fps", "duration"]
    head_parts = [
        f"{json.dumps(k)}:{json.dumps(ordered[k], separators=(',', ':'))}"
        for k in head_keys
        if k in ordered
    ]
    lines.append(",".join(head_parts) + ",")

    # Simple scalar/list keys before laban
    for k in ["axes", "screen_geometry", "negative"]:
        if k in ordered:
            lines.append(f"{json.dumps(k)}:{json.dumps(ordered[k])},")

    if "conservation_laws" in ordered:
        lines.append('"conservation_laws":[')
        laws = ordered["conservation_laws"]
        for i, law in enumerate(laws):
            comma = "," if i < len(laws) - 1 else ""
            lines.append(f"{json.dumps(law)}{comma}")
        lines.append("],")

    if "laban" in ordered:
        lines.append('"laban":{')
        laban = ordered["laban"]
        l_keys = list(laban.keys())
        for i, lk in enumerate(l_keys):
            comma = "}," if i == len(l_keys) - 1 else ","
            val_str = json.dumps(laban[lk], separators=(",", ":"))
            lines.append(f"{json.dumps(lk)}:{val_str}{comma}")

    if "beats" in ordered:
        lines.append(f'"beats":{json.dumps(ordered["beats"], separators=(",", ":"))},')

    # List-of-dict tracks: A_beats, B_track, props, camera
    prop_keys = extract_prop_tracks(ordered)
    track_keys = ["A_beats", "B_track"] + prop_keys + ["camera"]
    for tk in track_keys:
        if tk in ordered:
            lines.append(f"{json.dumps(tk)}:[")
            items = ordered[tk]
            for i, item in enumerate(items):
                comma = "," if i < len(items) - 1 else ""
                lines.append(f"{json.dumps(item, separators=(',', ':'))}{comma}")
            lines.append("],")

    # anime block
    if "anime" in ordered:
        anime = ordered["anime"]
        lines.append('"anime":{')
        akeys = list(anime.keys())
        for i, ak in enumerate(akeys):
            is_last = i == len(akeys) - 1
            if ak == "smear_frames" and isinstance(anime[ak], list):
                lines.append('"smear_frames":[')
                slist = anime[ak]
                for j, s_item in enumerate(slist):
                    scomma = "," if j < len(slist) - 1 else ""
                    lines.append(f"{json.dumps(s_item)}{scomma}")
                end_tok = "]}," if is_last else "],"
                lines.append(end_tok)
            else:
                val_str = json.dumps(anime[ak], separators=(",", ":"))
                end_tok = "}," if is_last else ","
                lines.append(f"{json.dumps(ak)}:{val_str}{end_tok}")

    # rules (final key)
    if "rules" in ordered:
        lines.append(f'"rules":{json.dumps(ordered["rules"])}')

    lines.append("}")
    json_block = "\n".join(lines)

    if not stack:
        return f"{header_text.strip()}\n\n{json_block}"

    layer1_lines = build_layer1_timeline(spec)
    layer1_block = "\n".join(layer1_lines)
    return (
        f"{header_text.strip()}\n\n"
        f"=== LAYER 1: CONTINUOUS SUPPORT, FORCE-EVENT & PROP TIMELINE (Labanotation-as-Words) ===\n"
        f"{layer1_block}\n\n"
        f"=== LAYER 2: SAKUGA-MLLM-3.1-CAUSAL KINEMATIC & CAMERA SCENE GRAPH ===\n"
        f"{json_block}"
    )


def stitch_multi_clip_continuity(clips: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    For multi-clip YouTube fight sequences (Clip 1 -> Clip 2 -> Clip N):
    Extracts the t=10.0 ending state of Clip k and verifies/locks Clip k+1's t=0.0 starting state,
    returning the stitched clips and a Continuity Handoff Report.
    """
    stitched = copy.deepcopy(clips)
    handoff_notes: List[str] = []

    for i in range(len(stitched) - 1):
        curr_clip = stitched[i]
        next_clip = stitched[i + 1]

        curr_a_end = curr_clip["A_beats"][-1]
        curr_b_end = curr_clip["B_track"][-1]
        next_a_start = next_clip["A_beats"][0]
        next_b_start = next_clip["B_track"][0]

        # Extract end positions and screen sides
        a_end_pos = curr_a_end.get("pos")
        b_end_pos = curr_b_end.get("pos")
        a_end_axis = curr_a_end.get("axis", "")
        b_end_axis = curr_b_end.get("axis", "")

        # Extract prop ownership at end of Clip i
        prop_end_states = {}
        for pk in extract_prop_tracks(curr_clip):
            if curr_clip[pk]:
                last_p = curr_clip[pk][-1]
                prop_end_states[pk] = {
                    "owner": last_p.get("owner"),
                    "state": last_p.get("state"),
                    "grip": last_p.get("grip", ""),
                }

        handoff_notes.append(
            f"### Handoff: Clip {i+1} (`{curr_clip.get('name')}` t=10.0s) -> Clip {i+2} (`{next_clip.get('name')}` t=0.0s)\n"
            f"- **Fighter A End -> Start:** `pos={a_end_pos}`, `axis=\"{a_end_axis}\"`\n"
            f"- **Fighter B End -> Start:** `pos={b_end_pos}`, `axis=\"{b_end_axis}\"`\n"
            f"- **Props Carried Over:** `{json.dumps(prop_end_states)}`"
        )

        # Auto-align next clip t=0.0 positions if flagged with auto_stitch or if mismatched
        if next_clip.get("meta", {}).get("auto_stitch_from_prev", True):
            next_a_start["pos"] = a_end_pos
            next_b_start["pos"] = b_end_pos

    return stitched, handoff_notes


def load_clip_file(path: Path) -> Tuple[Dict[str, Any], str]:
    """Load a pure JSON file, a Single-Layer hybrid text+JSON file, or a 2-Layer Fluid Stack text+JSON file."""
    raw = path.read_text(encoding="utf-8").strip()
    if raw.startswith("{"):
        data = json.loads(raw)
        header = data.pop("header", None)
        if not header:
            header = DEFAULT_HEADER_TEMPLATE.format(
                duration=data.get("duration", 10.0),
                fps=data.get("fps", 24),
                background="painted moonlit bamboo courtyard background",
                entities="Exactly TWO ninja fighters in close-quarters combat",
            )
        return data, header
    else:
        # Check if it's a 2-Layer Fluid Stack file with === LAYER 1 ... === and === LAYER 2 ... ===
        layer2_marker = "=== LAYER 2:"
        if layer2_marker in raw:
            l2_idx = raw.find(layer2_marker)
            brace_idx = raw.find("{", l2_idx)
        else:
            brace_idx = raw.find("{")
        if brace_idx == -1:
            raise ValueError(f"No JSON object found in {path}")
        preamble = raw[:brace_idx].strip()
        if "=== LAYER 1:" in preamble:
            l1_idx = preamble.find("=== LAYER 1:")
            header = preamble[:l1_idx].strip()
        else:
            header = preamble
        data = json.loads(raw[brace_idx:])
        return data, header


def main() -> int:
    parser = argparse.ArgumentParser(
        description="SAKUGA-MLLM-3.1-CAUSAL Compiler, 20-Rule Linter, 2-Layer Fluid Stack & Multi-Clip Stitcher"
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    # lint command
    p_lint = sub.add_parser("lint", help="Validate one or more clip JSON/Stack files against the 20 SOP Decisions")
    p_lint.add_argument("files", nargs="+", type=Path, help="Clip JSON or text file(s) to validate")

    # compile command
    p_compile = sub.add_parser("compile", help="Lint, causally order, apply taste/style layer, and output prompt")
    p_compile.add_argument("file", type=Path, help="Clip JSON file to compile")
    p_compile.add_argument(
        "--stack",
        action="store_true",
        help="Emit the 2-Layer Unrolled Fluid Stack (Layer 1 Labanotation-as-Words Timeline + Layer 2 Causal JSON)",
    )
    p_compile.add_argument(
        "--taste",
        choices=["clean", "nakamura"],
        default="clean",
        help="Optional Tier 2 Taste Layer preset (default: clean)",
    )
    p_compile.add_argument(
        "--style",
        choices=list(STYLE_PRESETS.keys()),
        default="cel_default",
        help="Optional Animation Style swap from R&D Queue (cel_default, genga, sumi_ink, trigger_neon, retro_90s, ufotable)",
    )
    p_compile.add_argument("--out", type=Path, default=None, help="Optional output file path")

    # stitch command
    p_stitch = sub.add_parser(
        "stitch", help="Validate and stitch multiple 10s clips into a continuous YouTube episode pack"
    )
    p_stitch.add_argument("files", nargs="+", type=Path, help="Ordered clip JSON files (Clip 1, Clip 2, ...)")
    p_stitch.add_argument(
        "--stack",
        action="store_true",
        help="Emit each clip in the 2-Layer Unrolled Fluid Stack format",
    )
    p_stitch.add_argument(
        "--taste",
        choices=["clean", "nakamura"],
        default="clean",
        help="Optional Tier 2 Taste Layer preset (default: clean)",
    )
    p_stitch.add_argument(
        "--style",
        choices=list(STYLE_PRESETS.keys()),
        default="cel_default",
        help="Optional Animation Style swap from R&D Queue (cel_default, genga, sumi_ink, trigger_neon, retro_90s, ufotable)",
    )
    p_stitch.add_argument("--out", type=Path, required=True, help="Output Markdown episode prompt pack")

    args = parser.parse_args()

    if args.cmd == "lint":
        any_err = False
        for f in args.files:
            spec, _ = load_clip_file(f)
            errs, warns = lint_clip(spec)
            print(f"=== Linting {f.name} ({spec.get('name', 'unnamed')}) ===")
            for w in warns:
                print(f"  [WARN]  {w}")
            for e in errs:
                print(f"  [ERROR] {e}")
            if not errs and not warns:
                print("  [PASSED] 0 errors, 0 warnings (100% SAKUGA-MLLM-3.1-CAUSAL compliant)")
            elif not errs:
                print(f"  [PASSED WITH WARNINGS] 0 errors, {len(warns)} warning(s)")
            else:
                print(f"  [FAILED] {len(errs)} error(s), {len(warns)} warning(s)")
                any_err = True
        return 1 if any_err else 0

    elif args.cmd == "compile":
        spec, header = load_clip_file(args.file)
        errs, warns = lint_clip(spec)
        if errs:
            for e in errs:
                print(f"[ERROR] {e}", file=sys.stderr)
            return 1
        for w in warns:
            print(f"[WARN] {w}", file=sys.stderr)

        spec, header = apply_taste_layer(spec, header, args.taste, args.style)
        prompt_text = format_sakuga_prompt(spec, header, stack=args.stack)

        if args.out:
            args.out.write_text(prompt_text + "\n", encoding="utf-8")
            mode_str = "2-Layer Fluid Stack" if args.stack else "Single-Layer Causal JSON"
            print(f"[COMPILED: {mode_str}] Wrote verified prompt to {args.out}")
        else:
            print(prompt_text)
        return 0

    elif args.cmd == "stitch":
        loaded = [load_clip_file(f) for f in args.files]
        specs = [item[0] for item in loaded]
        headers = [item[1] for item in loaded]

        for idx, s in enumerate(specs):
            errs, warns = lint_clip(s)
            if errs:
                print(f"[ERROR] Clip {idx+1} ({args.files[idx].name}) failed lint:", file=sys.stderr)
                for e in errs:
                    print(f"  {e}", file=sys.stderr)
                return 1

        stitched_specs, handoff_notes = stitch_multi_clip_continuity(specs)

        md_sections = [
            "# YouTube Episode Sakuga Prompt Pack (`SAKUGA-MLLM-3.1-CAUSAL`)",
            f"- **Total Clips:** {len(stitched_specs)} ({len(stitched_specs) * 10}s total duration @ 24fps)",
            f"- **Mode:** `{'2-Layer Unrolled Fluid Stack (--stack)' if args.stack else 'Single-Layer Causal JSON'}` | **Taste Preset:** `{args.taste}` | **Style Preset:** `{args.style}`",
            "",
            "## Cross-Clip Continuity Handoff Sheet",
            "\n\n".join(handoff_notes) if handoff_notes else "*Single clip — no cross-clip handoffs.*",
            "",
            "---",
        ]

        for idx, (s, h) in enumerate(zip(stitched_specs, headers)):
            s_tasted, h_tasted = apply_taste_layer(s, h, args.taste, args.style)
            compiled_prompt = format_sakuga_prompt(s_tasted, h_tasted, stack=args.stack)
            md_sections.append(f"## Clip {idx+1}: `{s.get('name')}` (`{idx*10}s - {(idx+1)*10}s`)")
            md_sections.append("```text\n" + compiled_prompt + "\n```\n")

        args.out.write_text("\n".join(md_sections), encoding="utf-8")
        print(f"[STITCHED & COMPILED] Wrote {len(stitched_specs)}-clip episode pack to {args.out}")
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
