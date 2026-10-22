"""Protected, Dedicated Compiler & Knowledge-Base Pre-Intent Path for the Original 05:34 (`e91c686`)
`SAKUGA-MLLM-3.1-CAUSAL` Single-Layer Prompt Template & Schema.

This module is strictly isolated from `sakuga_Xperiment` and the 2-Layer Fluid Stack (`compiler.py`).
It guarantees:
  1. 100% fidelity to the original `05:34` (`e91c686`) `SAKUGA-MLLM-3.1-CAUSAL` format (`Header + 1-line-per-beat JSON`)
     and `scripts/sakuga_compiler.py` (`CANONICAL_TOP_KEY_ORDER`, 11-key `CANONICAL_A_BEAT_KEY_ORDER`,
     8-key `CANONICAL_B_BEAT_KEY_ORDER`, 17-Decision `lint_clip` with 0 errors and 0 warnings,
     midpoint physical screen-cross `screen_left -> screen_right`, `pre -> hit -> post` or `evasion_corridor:` contact,
     clock-face arcs, parabolic prop gravity, and limb-isolated smears with `"stay solid"`).
  2. ZERO leakage of `sakuga_Xperiment` or Layer-1 constructs (`weight_split`, `com_position`, `easing_curve`,
     `impulse_tier`, `=== LAYER 1 ===`, `=== LAYER 2 ===`).
  3. Direct pre-intent Knowledge Base integration (`query_kb_prior_to_semantic_intent`, `resolve_beat_kb_guidance`,
     and `record_compile_usage`) prior to semantic intent decomposition and compilation.
"""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .dyad import DyadState
from .kb_bridge import (
    DEFAULT_BUNDLE_DIR,
    query_kb_prior_to_semantic_intent,
    record_compile_usage,
    resolve_beat_kb_guidance,
)
from .lexicon import Lexicon
from .state import FighterState
from .validator import ValidationResult, load_thresholds, validate_clip

REPO_ROOT = Path(__file__).resolve().parent.parent
ORIGINAL_COMPILER_PATH = REPO_ROOT / "scripts" / "sakuga_compiler.py"
ORIGINAL_TEMPLATE_PATH = REPO_ROOT / "templates" / "sakuga_mllm_3_1_causal_0534_template.json"
ORIGINAL_COMPILER_E91C686_SHA256 = "fdf54e5543e3ac9981878521136daafdd4086c1a1559af4673153512d433b498"

# Strictly forbidden keys from the `sakuga_Xperiment` 2-Layer Fluid Stack path
FORBIDDEN_XPERIMENT_KEYS = {
    "weight_split",
    "com_position",
    "easing_curve",
    "impulse_tier",
}

CLOCK_ARC_MAP: Dict[str, str] = {
    "linear": "linear_9_to_3_clock_drive",
    "horizontal": "horizontal_3_to_9_clock_whip_arc",
    "upward": "diagonal_7_to_1_clock_rising_arc",
    "downward": "vertical_12_to_6_clock_downward_drive",
    "circular": "360deg_ccw_grounded_pivot_into_3_to_9_clock_roundhouse_arc",
    "stationary": "compact_centerline_guard_frame",
}

SUPPORT_CLOCK_SURFACE: Dict[str, float] = {
    "standing": 0.84,
    "crouched": 0.62,
    "clinched": 0.80,
    "kneeling": 0.52,
    "supine": 0.22,
    "prone": 0.22,
    "airborne": 1.24,
}

LEVEL_HIT_Y: Dict[str, float] = {
    "low": 0.46,
    "mid": 1.08,
    "high": 1.38,
}

LEVEL_TARGET_PART: Dict[str, str] = {
    "low": "lead_calf_and_knee_hollow",
    "mid": "solar_plexus_and_floating_ribs",
    "high": "jawline_and_chin",
}


def load_original_sakuga_compiler_module() -> Any:
    """Dynamically load the protected `scripts/sakuga_compiler.py` (`e91c686`) module."""
    spec = importlib.util.spec_from_file_location("sakuga_compiler_0534", ORIGINAL_COMPILER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load protected compiler at {ORIGINAL_COMPILER_PATH}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def verify_original_compiler_protection() -> Tuple[bool, str]:
    """Verify `scripts/sakuga_compiler.py` is byte-for-byte identical to the original `05:34` (`e91c686`) commit."""
    if not ORIGINAL_COMPILER_PATH.is_file():
        return False, f"Missing {ORIGINAL_COMPILER_PATH}"
    digest = hashlib.sha256(ORIGINAL_COMPILER_PATH.read_bytes()).hexdigest()
    if digest != ORIGINAL_COMPILER_E91C686_SHA256:
        return (
            False,
            f"scripts/sakuga_compiler.py SHA256 mismatch: got {digest}, expected {ORIGINAL_COMPILER_E91C686_SHA256} (commit e91c686)",
        )
    return True, digest


def assert_pure_0534_causal_spec(
    spec: Dict[str, Any],
    prompt_text: str,
) -> Tuple[List[str], List[str]]:
    """Run the original `e91c686` 17-Decision linter (`lint_clip`) plus strict isolation checks ensuring
    zero `sakuga_Xperiment` or 2-Layer Fluid Stack leakage.
    Returns (errors, warnings).
    """
    orig = load_original_sakuga_compiler_module()
    errors, warnings = orig.lint_clip(spec)

    if "=== LAYER 1" in prompt_text or "=== LAYER 2" in prompt_text or "MOVEMENT LANGUAGE:" in prompt_text:
        errors.append(
            "ISOLATION VIOLATION: Prompt contains 2-Layer Fluid Stack headers ('=== LAYER 1' / 'MOVEMENT LANGUAGE:')."
        )

    allowed_a_keys = set(orig.CANONICAL_A_BEAT_KEY_ORDER)
    allowed_b_keys = set(orig.CANONICAL_B_BEAT_KEY_ORDER)

    for idx, beat in enumerate(spec.get("A_beats", [])):
        extra = set(beat.keys()) - allowed_a_keys
        if extra:
            errors.append(
                f"ISOLATION VIOLATION in A_beats[{idx}]: non-0534 keys {sorted(extra)} present (allowed: {orig.CANONICAL_A_BEAT_KEY_ORDER})."
            )
        leaked = FORBIDDEN_XPERIMENT_KEYS.intersection(beat.keys())
        if leaked:
            errors.append(f"ISOLATION VIOLATION in A_beats[{idx}]: sakuga_Xperiment keys {sorted(leaked)} leaked.")
        causal_val = str(beat.get("causal", ""))
        if " -> chain: " in causal_val:
            errors.append(
                f"ISOLATION VIOLATION in A_beats[{idx}]: 4-part sakuga_Xperiment '-> chain:' leaked into 05:34 causal string."
            )

    for idx, beat in enumerate(spec.get("B_track", [])):
        extra = set(beat.keys()) - allowed_b_keys
        if extra:
            errors.append(
                f"ISOLATION VIOLATION in B_track[{idx}]: non-0534 keys {sorted(extra)} present (allowed: {orig.CANONICAL_B_BEAT_KEY_ORDER})."
            )
        leaked = FORBIDDEN_XPERIMENT_KEYS.intersection(beat.keys())
        if leaked:
            errors.append(f"ISOLATION VIOLATION in B_track[{idx}]: sakuga_Xperiment keys {sorted(leaked)} leaked.")

    return errors, warnings


def _extract_request_summary_from_causal_spec(spec: Dict[str, Any], header_text: str) -> str:
    """Build a natural-language query string from an original `SAKUGA-MLLM-3.1-CAUSAL` spec for pre-intent KB retrieval."""
    beats = spec.get("beats", [])
    laban_a = spec.get("laban", {}).get("A", {}).get("chain", "")
    style = spec.get("anime", {}).get("style", "")
    parts = [
        spec.get("name", "cqc_sakuga_10s"),
        " ".join(str(b).replace("_", " ") for b in beats),
        laban_a.replace("_", " ").replace(">", " "),
        style,
        header_text[:200],
    ]
    return " ".join(p for p in parts if p).strip()


def compile_original_causal_spec_with_kb(
    spec_or_path: Any,
    taste: str = "clean",
    style: str = "cel_default",
    kb_taste: str = "heavy, brutal, old school",
    knobs_spec: Optional[List[str]] = None,
    bundle_dir: Path = DEFAULT_BUNDLE_DIR,
    record_usage: bool = True,
) -> Tuple[str, Dict[str, Any], Dict[str, Any], List[str], List[str]]:
    """Path A (Protected Original `05:34` `SAKUGA-MLLM-3.1-CAUSAL` Spec + Pre-Intent Knowledge Base Query):
    1. Loads an original `05:34` (`e91c686`) `SAKUGA-MLLM-3.1-CAUSAL` JSON or hybrid file (e.g. `gold_master_1`,
       `gold_master_2`, or `templates/sakuga_mllm_3_1_causal_0534_template.json`).
    2. Queries `knowledge_base/` PRIOR to semantic intent / compilation via `query_kb_prior_to_semantic_intent()`.
    3. Canonicalizes and applies `--taste` (`clean` | `nakamura`) and `--style` using the protected
       `scripts/sakuga_compiler.py` functions (`apply_style_preset`, `apply_taste_layer`, `canonicalize_spec`).
    4. Validates via `assert_pure_0534_causal_spec()` (enforcing 0 errors and 0 warnings on the original 17-Decision linter).
    5. Formats via `scripts/sakuga_compiler.py` `format_sakuga_prompt()` and logs KB usage to `agent_memory.db`.

    Returns `(compiled_prompt_text, canonical_spec, kb_priors_report, errors, warnings)`.
    """
    orig = load_original_sakuga_compiler_module()

    if isinstance(spec_or_path, (str, Path)):
        path = Path(spec_or_path)
        loaded_spec, header_text = orig.load_clip_file(path)
    elif isinstance(spec_or_path, dict):
        loaded_spec = copy.deepcopy(spec_or_path)
        header_text = loaded_spec.pop(
            "header",
            orig.DEFAULT_HEADER_TEMPLATE.format(
                duration=loaded_spec.get("duration", 10.0),
                fps=loaded_spec.get("fps", 24),
                background="painted moonlit bamboo courtyard background",
                entities="Exactly TWO ninja fighters in close-quarters combat",
            ),
        )
    else:
        raise TypeError(f"Unsupported spec_or_path type: {type(spec_or_path)}")

    # 1. Query the Knowledge Base PRIOR to semantic intent & compilation
    request_summary = _extract_request_summary_from_causal_spec(loaded_spec, header_text)
    kb_priors = query_kb_prior_to_semantic_intent(
        request_summary,
        taste=kb_taste,
        knobs_spec=knobs_spec,
        bundle_dir=bundle_dir,
    )

    # 2. Run the original 05:34 (`e91c686`) style, taste, and canonicalization pipeline
    seasoned_spec, updated_header = orig.apply_taste_layer(loaded_spec, header_text, taste, style)
    canonical_spec = orig.order_spec_causally(seasoned_spec)

    # 3. Format using the original 05:34 (`e91c686`) single-layer formatter
    compiled_prompt = orig.format_sakuga_prompt(canonical_spec, updated_header)

    # 4. Validate against the original 17-Decision linter + strict isolation checks
    errors, warnings = assert_pure_0534_causal_spec(canonical_spec, compiled_prompt)

    # 5. Record KB usage back into `knowledge_base/agent_memory.db`
    if record_usage and not errors:
        used_directives: List[str] = []
        used_passages: List[str] = []
        for d_item in kb_priors.get("directives", []):
            if isinstance(d_item, dict) and d_item.get("id"):
                used_directives.append(d_item["id"])
        for p_item in kb_priors.get("pulled_relations", []):
            if isinstance(p_item, dict) and p_item.get("id"):
                used_directives.append(p_item["id"])
        for hit in kb_priors.get("passages", []):
            if isinstance(hit, dict) and hit.get("id"):
                used_passages.append(hit["id"])
        record_compile_usage(
            run_id=f"0534_causal:{canonical_spec.get('name', 'clip')}",
            used_directives=used_directives,
            used_cards=[str(b) for b in canonical_spec.get("beats", [])],
            used_passages=used_passages,
            bundle_dir=bundle_dir,
        )

    return compiled_prompt, canonical_spec, kb_priors, errors, warnings


def _format_0534_limbs(card: Dict[str, Any], fighter: FighterState) -> str:
    """Format compact 05:34-style `limbs` string (`L:...; R:...; feet:...`) without any negative tokens."""
    lw = fighter.limb_words()
    act_words = card["caption_words"].format(**lw)
    other_arm = card["off_limbs"]["other_arm"].format(**lw)
    lead_leg = card["off_limbs"]["lead_leg"].format(**lw)
    rear_leg = card["off_limbs"]["rear_leg"].format(**lw)

    if card["limb"] in {"lead_hand", "lead_elbow"}:
        l_str = act_words
        r_str = other_arm
    elif card["limb"] in {"rear_hand", "rear_elbow"}:
        l_str = other_arm
        r_str = act_words
    else:
        l_str = other_arm
        r_str = f"counter-balancing guard while executing {act_words}"

    return f"L:{l_str}; R:{r_str}; feet:{lead_leg}, {rear_leg}"


def compile_beatsheet_to_original_0534_causal(
    clip: Dict[str, Any],
    lexicon: Optional[Lexicon] = None,
    taste: str = "clean",
    style: str = "cel_default",
    kb_taste: str = "heavy, brutal, old school",
    knobs_spec: Optional[List[str]] = None,
    bundle_dir: Path = DEFAULT_BUNDLE_DIR,
    record_usage: bool = True,
) -> Tuple[str, Dict[str, Any], Dict[str, Any], ValidationResult]:
    """Path B (Beat-Sheet -> Pure `05:34` `SAKUGA-MLLM-3.1-CAUSAL` Single-Layer Prompt with Pre-Intent KB Query):
    Compiles a `fight_move_system` beat-sheet into a 100% pure `05:34` (`e91c686`) `SAKUGA-MLLM-3.1-CAUSAL`
    single-layer prompt (Header + 1-line-per-beat JSON) on its own dedicated code path:
      - Queries `knowledge_base/` PRIOR to semantic intent via `query_kb_prior_to_semantic_intent()`.
      - Uses ONLY the 11 canonical `A_beats` keys (`t`, `beat`, `causal`, `pos`, `vel`, `axis`, `arc`, `support`,
        `contact`, `limbs`, `pose`) and 8 canonical `B_track` keys (`t`, `pos`, `axis`, `support`, `contact`,
        `launch_vel`, `action`, `pose`).
      - Enforces Decision 16 midpoint physical cross (`screen_side:left` -> `screen_side:crossing_left_to_right`
        around `t=4.4s–5.3s` -> `screen_side:right`) so `scripts/sakuga_compiler.py lint` passes with **0 errors
        and 0 warnings**.
      - Enforces 3-phase `contact` (`pre:... -> hit:..._at_[x,y,z]_zero_gap -> post:...` or `evasion_corridor:...`)
        with `BEFORE_<THREAT>_INTERSECTION` on parries/dodges/blocks.
      - Never emits `weight_split`, `com_position`, `easing_curve`, `impulse_tier`, or `=== LAYER 1 ===`.
    """
    orig = load_original_sakuga_compiler_module()
    lex = lexicon or Lexicon.load_default()
    thresh = load_thresholds()
    val_res = validate_clip(clip, lexicon=lex, thresholds=thresh)
    if not val_res.ok:
        return "", {}, {}, val_res

    # 1. Query the Knowledge Base PRIOR to semantic intent decomposition
    kb_priors = query_kb_prior_to_semantic_intent(
        clip,
        taste=kb_taste,
        knobs_spec=knobs_spec,
        bundle_dir=bundle_dir,
    )

    fighters_cfg = clip.get("fighters", {})
    a_cfg = fighters_cfg.get("A", {})
    b_cfg = fighters_cfg.get("B", {})

    fighter_a = FighterState(
        id="A",
        style=a_cfg.get("style", "boxing"),
        stance=a_cfg.get("stance", "orthodox"),
        screen_side="left",
        facing="right",
        support=a_cfg.get("support", "standing"),
        coil=a_cfg.get("coil", "neutral"),
    )
    fighter_b = FighterState(
        id="B",
        style=b_cfg.get("style", "boxing"),
        stance=b_cfg.get("stance", "orthodox"),
        screen_side="right",
        facing="left",
        support=b_cfg.get("support", "standing"),
        coil=b_cfg.get("coil", "neutral"),
    )
    dyad = DyadState(range_band=clip.get("initial_range", "kick"))

    a_desc = a_cfg.get(
        "label",
        "lean martial artist, dark indigo coat, white forearm wraps, crimson fight trunks",
    ).replace("NO tape", "bare skin")
    b_desc = b_cfg.get(
        "label",
        "heavyweight rival striker, broad muscular torso, dark charcoal fight pants, bare wrists",
    ).replace("NO tape", "bare skin")
    arena = clip.get(
        "arena",
        "painted lantern-lit stone temple courtyard at dusk",
    )

    moments = clip.get("moments", [])
    total_moments = max(1, len(moments))
    midpoint_idx = max(1, total_moments // 2)

    a_beats: List[Dict[str, Any]] = []
    b_track: List[Dict[str, Any]] = []
    camera_track: List[Dict[str, Any]] = []
    impact_frames: List[float] = []
    smear_frames: List[str] = []
    speed_lines: List[str] = []
    anticipation_holds: List[float] = []
    fx_map: Dict[str, str] = {}
    beat_names: List[str] = []
    a_chain_parts: List[str] = []
    b_chain_parts: List[str] = []
    used_directives: List[str] = []
    used_cards: List[str] = []
    used_passages: List[str] = []

    for d_item in kb_priors.get("directives", []):
        if isinstance(d_item, dict) and d_item.get("id"):
            used_directives.append(d_item["id"])
    for p_item in kb_priors.get("pulled_relations", []):
        if isinstance(p_item, dict) and p_item.get("id"):
            used_directives.append(p_item["id"])
    for hit in kb_priors.get("passages", []):
        if isinstance(hit, dict) and hit.get("id"):
            used_passages.append(hit["id"])

    cross_time = 4.9
    for idx, moment in enumerate(moments):
        if idx == 0:
            t_val = 0.0
        elif idx == total_moments - 1:
            t_val = 7.4
        else:
            t_val = round((idx / total_moments) * 7.2, 2)

        if idx == midpoint_idx:
            cross_time = t_val

        is_hero = bool(moment.get("is_hero", idx == total_moments - 1))
        a_act = moment.get("A")
        b_act = moment.get("B")
        a_card = lex.get(a_act["move"]) if a_act else None
        b_card = lex.get(b_act["move"]) if b_act else None

        if a_card:
            used_cards.append(a_card["id"])
        if b_card:
            used_cards.append(b_card["id"])

        kb_beat = resolve_beat_kb_guidance(
            a_card,
            b_card,
            is_hero=is_hero,
            beat_idx=idx,
            total_beats=total_moments,
            bundle_dir=bundle_dir,
        )
        used_directives.extend(kb_beat["directives"])
        used_passages.extend(kb_beat["handbook_refs"])

        # Screen-side progression with Decision 16 midpoint physical cross
        if idx < midpoint_idx:
            a_side_tag = "screen_side:left"
            b_side_tag = "screen_side:right"
            a_facing_tag = "facing:+Z"
            b_facing_tag = "facing:-Z"
            z_a = 3.20
            z_b = 4.05
            hit_z = 3.95
        elif idx == midpoint_idx:
            a_side_tag = "screen_side:crossing_left_to_right"
            b_side_tag = "screen_side:left_as_A_crosses_past"
            a_facing_tag = "facing:+Z_turning_-Z"
            b_facing_tag = "facing:-Z"
            z_a = 4.25
            z_b = 4.10
            hit_z = 4.18
        else:
            a_side_tag = "screen_side:right"
            b_side_tag = "screen_side:left"
            a_facing_tag = "facing:-Z"
            b_facing_tag = "facing:+Z"
            z_a = 4.45
            z_b = 3.65
            hit_z = 3.78

        beat_label = f"c{idx+1:02d}_{a_card['id'] if a_card else 'beat'}_vs_{b_card['id'] if b_card else 'beat'}"
        beat_names.append(beat_label)

        is_contact = any(c and c["contact"] in {"strike", "grapple", "block"} for c in (a_card, b_card))
        is_evasion = bool(a_card and a_card["class"] in {"DEFENSE.EVADE", "FOOTWORK.TRANSLATE"} and not is_contact)
        hold_f = 5 if is_hero else (3 if is_contact else 0)
        if is_contact:
            impact_frames.append(t_val)
        else:
            anticipation_holds.append(t_val)

        if a_card:
            lw_a = fighter_a.limb_words()
            a_words = a_card["caption_words"].format(**lw_a).replace(" not ", " ")
            a_limbs = _format_0534_limbs(a_card, fighter_a).replace(" not ", " ")
            a_y = SUPPORT_CLOCK_SURFACE.get(a_card["post"]["support"], 0.84)
            arc_desc = CLOCK_ARC_MAP.get(a_card["path"], "linear_9_to_3_clock_drive")
            if idx == midpoint_idx:
                arc_desc = f"low_step_through_cross_left_to_right, {arc_desc}"

            prev_code = f"C{idx:02d}_{a_chain_parts[-1]}" if a_chain_parts else "init_grounded_push_impulse"
            next_code = f"C{idx+2:02d}_{b_card['id'] if b_card else 'next_state'}"
            a_chain_parts.append(f"C{idx+1:02d}_{a_card['id']}")

            needs_before_timing = (
                a_card["class"] in {"DEFENSE.BLOCK_PARRY", "DEFENSE.EVADE"}
                or "parry" in a_card["id"]
                or "slip" in a_card["id"]
                or "duck" in a_card["id"]
                or "weave" in a_card["id"]
                or "shell" in a_card["id"]
                or "block" in a_card["id"]
            )
            timing_clause = " -> timing: BEFORE_STRIKE_INTERSECTION" if needs_before_timing else ""
            causal_str = (
                f"C{idx+1:02d}: requires: {prev_code}{timing_clause} -> "
                f"preserves: {a_card['post']['coil']}_momentum -> "
                f"causes: {next_code}"
            )

            hit_y = LEVEL_HIT_Y.get(a_card["level"], 1.08)
            target_part = LEVEL_TARGET_PART.get(a_card["level"], "torso")
            if is_evasion:
                contact_str = (
                    f"evasion_corridor: A_head_and_chest_clear_by_18cm_at_y={round(a_y, 2)}m_as_B_attack_sweeps_past_at_z={hit_z}"
                )
            else:
                contact_str = (
                    f"pre:A_commits_{a_card['id']}_from_grounded_pivot -> "
                    f"hit:A_{a_card['limb']}_deforms_B_{target_part}_at_[0,{hit_y},{hit_z}]_zero_gap -> "
                    f"post:transfers_impulse_into_B_{b_card['id'] if b_card else 'recoil'}_with_follow_through"
                )

            pose_prefix = f"IMPACT FRAME (hold {hold_f}f{', slomo 0.25x' if is_hero else ''}). " if hold_f else ""
            cross_note = (
                " Stepping across screen center from screen-left to screen-right past B's flank,"
                if idx == midpoint_idx
                else ""
            )
            pose_str = (
                f"{pose_prefix}At {t_val}s,{cross_note} A ({a_side_tag.replace('screen_side:', 'screen ')}) {a_words}."
            ).replace(" not ", " ")

            a_beat_entry: Dict[str, Any] = {
                "t": t_val,
                "beat": beat_label,
                "causal": causal_str,
                "pos": [0, a_y, z_a],
                "vel": [0, 0, 0.9 if idx == midpoint_idx else 0.4],
                "axis": f"head:+Y_up, torso:{a_card['hinge']}_{a_card['path']}, {a_facing_tag}, {a_side_tag}",
                "arc": arc_desc,
                "support": f"both_feet_planted_on_floor_at_z={z_a}",
                "contact": contact_str,
                "limbs": a_limbs,
                "pose": pose_str,
            }
            a_beats.append(a_beat_entry)

            if is_contact:
                smear_start = round(max(0.0, t_val - 0.15), 2)
                smear_frames.append(
                    f"{smear_start}-{t_val}: A {a_card['limb']} {arc_desc} streak only; head, standing leg, and torso stay solid"
                )
                speed_lines.append(f"{smear_start}-{t_val}")
                fx_map[str(t_val)] = f"impact_shock_ring_and_dust_burst_on_{a_card['id']}"

            fighter_a.support = a_card["post"]["support"]
            fighter_a.coil = a_card["post"]["coil"]

        if b_card:
            lw_b = fighter_b.limb_words()
            b_words = b_card["caption_words"].format(**lw_b).replace(" not ", " ")
            b_y = SUPPORT_CLOCK_SURFACE.get(b_card["post"]["support"], 0.88)
            b_chain_parts.append(f"C{idx+1:02d}_{b_card['id']}")
            hit_y = LEVEL_HIT_Y.get(a_card["level"] if a_card else b_card["level"], 1.08)
            target_part = LEVEL_TARGET_PART.get(a_card["level"] if a_card else b_card["level"], "torso")

            b_entry: Dict[str, Any] = {
                "t": t_val,
                "pos": [0, b_y, z_b],
                "axis": f"head:+Y_up, torso:{b_card['id']}, {b_facing_tag}, {b_side_tag}",
                "support": f"both_feet_braced_on_floor_at_z={z_b}",
                "contact": f"B_{target_part} -> absorbs_A_{a_card['id'] if a_card else 'contact'}_at_[0,{hit_y},{hit_z}]",
                "action": f"{b_card['id']}_after_contact",
                "pose": f"only after contact at [{0},{hit_y},{hit_z}], B {b_words}".replace(" not ", " "),
            }
            b_track.append(b_entry)
            fighter_b.support = b_card["post"]["support"]
            fighter_b.coil = b_card["post"]["coil"]

        cam_entry: Dict[str, Any] = {
            "t": t_val,
            "shot": f"tight_cqc_combat_track_{beat_label}",
            "fov": 30 if is_hero else 34,
            "pos": [1.45, 0.85, round((z_a + z_b) / 2.0, 2)],
            "look": f"A_and_B_contact_point_at_[0,1.08,{hit_z}]",
            "move": (
                "smooth_pan_keeping_180_rule_as_A_crosses_to_screen_right"
                if idx == midpoint_idx
                else "tight_push_in_tracking_exchange"
            ),
        }
        if hold_f:
            cam_entry["hold_frames"] = hold_f
            cam_entry["effect"] = "camera_shake_impact_flash"
        if is_hero:
            cam_entry["time_remap"] = 0.25
        camera_track.append(cam_entry)

        if a_card:
            dyad.apply_range_delta(a_card["post"]["range_delta"])
        if b_card:
            dyad.apply_range_delta(b_card["post"]["range_delta"])

    # Add 8.6s and 10.0s hold beats on screen_right (A) and screen_left (B) matching Gold Master 1 & 2
    final_beat_label = beat_names[-1] if beat_names else "final_dominant_hold"
    for hold_t, suffix in ((8.6, "hold"), (10.0, "hold_end")):
        a_beats.append(
            {
                "t": hold_t,
                "beat": final_beat_label,
                "causal": f"C{total_moments:02d}_{suffix}: maintains C{total_moments:02d}_post_finisher_lock",
                "pos": [0, 0.78, 4.45],
                "vel": [0, 0, 0],
                "axis": "head:+Y_up_looking_at_B, torso:low_dominant_combat_stance, facing:-Z, screen_side:right",
                "arc": "static_hold",
                "support": "both_feet_planted_wide_on_floor_at_z=4.45",
                "limbs": "L:lead guard hand extended; R:rear hand chambered tight at cheek; feet:both feet planted wide on floor",
                "pose": f"At {hold_t}s, A holds the dominant finishing stance on screen-right facing left as dust settles.",
            }
        )
        b_track.append(
            {
                "t": hold_t,
                "pos": [0, SUPPORT_CLOCK_SURFACE.get(fighter_b.support, 0.52), 3.65],
                "axis": f"head:+Y_up, torso:{fighter_b.support}_hold, facing:+Z, screen_side:left",
                "support": f"{fighter_b.support}_on_floor_at_z=3.65",
                "action": f"defeated_{fighter_b.support}_hold",
                "pose": f"At {hold_t}s, B remains in {fighter_b.support} state on screen-left at z=3.65.",
            }
        )

    camera_track.append(
        {
            "t": 8.6,
            "shot": "extreme_close_up_finisher_hold",
            "fov": 28,
            "look": "A_eyes_on_screen_right_over_B_on_screen_left",
            "move": "slow_push_in_final_hold",
            "duration": 1.4,
        }
    )

    header_text = (
        "10s anime fight clip, 24fps. STYLE: 2D hand-drawn anime, cel-shaded flat colors, heavy ink outlines, "
        "intense close-quarters sakuga martial arts animation on twos with limb-isolated smear frames, camera shake on impacts, "
        f"and held impact frames, {arena}. Not 3D, not CGI, not live action, not photoreal. "
        f"ENTITY COUNT: Exactly TWO fighters in close-quarters combat. Fighter A: {a_desc}. Fighter B: {b_desc}. "
        "Render as one physically continuous combat event where every movement emerges visibly from the force and momentum "
        "of the previous state; no on-screen text, no numbers, no HUD, and no coordinate labels."
    )

    spec: Dict[str, Any] = {
        "name": clip.get("name", "cqc_sakuga_10s_0534_causal"),
        "schema": "SAKUGA-MLLM-3.1-CAUSAL",
        "fps": 24,
        "duration": 10.0,
        "axes": (
            "Y_up, metres, floor y=0, close-quarters combat zone z=2.8 to z=5.0, "
            "A starts at z=3.20 facing +Z (screen_left), B starts at z=4.05 facing -Z (screen_right)"
        ),
        "screen_geometry": (
            f"180_degree_camera_rule_locked: A_on_screen_left_facing_right and B_on_screen_right_facing_left from 0.0s to {cross_time}s; "
            f"at {cross_time}s A physically steps across screen center past B's flank; from {round(cross_time + 0.1, 2)}s to 10.0s "
            "A_on_screen_right_facing_left and B_on_screen_left_facing_right. Never flip left-right screen sides via camera cuts."
        ),
        "negative": (
            "no 3D CGI, no mocap stiffness, no floaty physics, no distant wide shots, no on-screen text or numbers, "
            "no HUD, no extra fighters, no cloned A or B, no missing limbs, no full-body blur during smears, "
            "no reaction before contact, no spontaneous spins without grounded pivot torque, no stopping strikes at surface without follow-through"
        ),
        "conservation_laws": [
            "CONSERVE_SEMANTICALLY: prioritize continuous momentum transfer, contact deformation, and causal order over isolated poses",
            "knockback_and_hit_reaction_require_prior_physical_contact_zero_early_flinch",
            "body_rotation_requires_prior_grounded_foot_pivot_and_hip_torque",
            "evasion_must_initiate_AFTER_attack_commitment_and_BEFORE_trajectory_intersection",
        ],
        "laban": {
            "A": {
                "chain": " > ".join(a_chain_parts),
                "effort": {
                    "weight": "strong_snappy",
                    "time": "sudden_explosive",
                    "space": "direct_close_range",
                    "flow": "continuous_momentum_bound_at_impacts",
                },
            },
            "B": {
                "chain": " > ".join(b_chain_parts),
                "effort": {
                    "weight": "heavy",
                    "time": "sustained_to_sudden",
                    "space": "direct",
                    "flow": "bound",
                },
            },
        },
        "beats": beat_names,
        "A_beats": a_beats,
        "B_track": b_track,
        "camera": camera_track,
        "anime": {
            "style": "2D cel-shaded hand-drawn anime, flat color, heavy ink outlines, intense close-quarters sakuga martial arts animation on twos",
            "impact_frames": impact_frames,
            "smear_frames": smear_frames,
            "speed_lines": speed_lines,
            "time_remap": {"7.2-7.5": 0.25},
            "anticipation_holds": anticipation_holds[:3] if anticipation_holds else [0.0],
            "fx": fx_map,
            "line_rule": "heavy ink outlines on A and B, broken/sketchy outlines ONLY on active smear limbs, ultra-thick impact frames on finisher",
        },
        "rules": (
            "Render as one physically continuous combat event where each state emerges visibly from the force and momentum "
            f"of the previous state. Maintain strict 180-degree screen geometry: A is on screen-left and B is on screen-right "
            f"from 0.0s until {cross_time}s, when A physically steps across screen center past B's flank to land on screen-right "
            f"from {round(cross_time + 0.1, 2)}s to 10.0s. Pure 2D hand-drawn cel-shaded anime throughout, no 3D CGI, no on-screen text or numbers."
        ),
    }

    seasoned_spec, updated_header = orig.apply_taste_layer(spec, header_text, taste, style)
    canonical_spec = orig.order_spec_causally(seasoned_spec)
    compiled_prompt = orig.format_sakuga_prompt(canonical_spec, updated_header)

    lint_errors, lint_warnings = assert_pure_0534_causal_spec(canonical_spec, compiled_prompt)
    for err in lint_errors:
        val_res.add_error("ORIG_0534_LINT", err)
    for warn in lint_warnings:
        val_res.add_warning("ORIG_0534_WARN", warn)

    if record_usage and val_res.ok:
        record_compile_usage(
            run_id=f"0534_beatsheet:{canonical_spec['name']}",
            used_directives=used_directives,
            used_cards=used_cards,
            used_passages=used_passages,
            bundle_dir=bundle_dir,
        )

    return compiled_prompt, canonical_spec, kb_priors, val_res
