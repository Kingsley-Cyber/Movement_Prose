"""Executable bridge connecting the BLOCK Fight Engine (`engine.*`, `predict.py`, `plan_fight.py`)
to the Movement_Prose compilation pipelines:
  1. `sakuga_Xperiment` 2-Layer Unrolled Fluid Stack (`fight_move_system.compiler.compile_to_sakuga_Fluid_stack`)
  2. Protected `05:34` (`e91c686`) `SAKUGA-MLLM-3.1-CAUSAL` Single-Layer (`fight_move_system.original_causal_compiler.compile_beatsheet_to_original_0534_causal`)

Both pipelines query the in-repository Knowledge Base (`knowledge_base/`) prior to semantic intent decomposition.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .compiler import compile_to_sakuga_Fluid_stack
from .lexicon import Lexicon
from .original_causal_compiler import (
    assert_pure_0534_causal_spec,
    compile_beatsheet_to_original_0534_causal,
    verify_original_compiler_protection,
)


def _strip_digits(text: str) -> str:
    replacements = {
        "52": "fifty-two",
        "10": "ten",
        "0": "zero",
        "1": "one",
        "2": "two",
        "3": "three",
        "4": "four",
        "5": "five",
        "6": "six",
        "7": "seven",
        "8": "eight",
        "9": "nine",
    }
    out = text
    for k, v in replacements.items():
        out = out.replace(k, v)
    return re.sub(r"\d+", "multi", out)


def _card_to_fms_style(card: Dict[str, Any], ruleset: str) -> str:
    if ruleset == "boxing":
        return "boxing"
    return "mma"


def _card_to_labels(card: Dict[str, Any], side_word: str) -> Tuple[str, str]:
    name = _strip_digits(str(card.get("name", f"Fighter {side_word}")))
    identity = _strip_digits(str(card.get("combat_identity", "martial arts striker"))).replace("/", "and")
    if side_word == "left":
        label = (
            f"lean, razor-cut striker ({name}, {identity} specialist), shirtless bare torso, "
            f"white cloth tape on both wrists/knuckles and gold ankle wraps, midnight-blue Vale Tudo fight shorts, bare feet"
        )
        short_name = "the midnight-blue-shorts striker on the left"
    else:
        label = (
            f"muscular counter-fighter ({name}, {identity} specialist), shirtless broad scarred torso, "
            f"urban-camo fight shorts, bare wrists and bare ankles with NO tape, bare feet"
        )
        short_name = "the camo-shorts fighter on the right"
    return label, short_name


def block_plan_to_movement_prose_clip(
    fight_plan: Dict[str, Any],
    choreography: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Convert a BLOCK `fight_plan.json` (and optional `choreography.json`) into a validated
    10-beat Movement_Prose clip specification (`sakuga_Xperiment` / `SAKUGA-MLLM-3.1-CAUSAL` ready).
    """
    cards = fight_plan.get("cards", [])
    card_a = cards[0] if len(cards) > 0 else {"fighter_id": "fighter_a", "name": "Fighter A", "combat_identity": "MMA"}
    card_b = cards[1] if len(cards) > 1 else {"fighter_id": "fighter_b", "name": "Fighter B", "combat_identity": "MMA"}

    ruleset = str(fight_plan.get("ruleset", "mma"))
    fa_style = _card_to_fms_style(card_a, ruleset)
    fb_style = _card_to_fms_style(card_b, ruleset)

    fa_label, fa_short = _card_to_labels(card_a, "left")
    fb_label, fb_short = _card_to_labels(card_b, "right")

    fa_id = str(card_a.get("fighter_id", "fighter_a"))
    fb_id = str(card_b.get("fighter_id", "fighter_b"))
    selection = fight_plan.get("selection", {})
    winner_id = str(selection.get("winner_id", fa_id))
    mode = str(selection.get("mode", "predictive"))

    plan_id = f"block_{fa_id}_vs_{fb_id}_{mode}"

    # Extract technique IDs executed in BLOCK events
    tech_ids: List[str] = []
    for event in fight_plan.get("events", []):
        tid = event.get("technique_id")
        if tid:
            tech_ids.append(str(tid))

    kicking_dim = (card_a.get("dimensions") or {}).get("kicking") or (card_b.get("dimensions") or {}).get("kicking")
    has_kicks_or_clinch = bool(kicking_dim) or any(
        t in {"low_kick", "body_kick", "high_kick", "teep", "knee_strike", "collar_tie", "clinch_entry"}
        for t in tech_ids
    )

    if ruleset == "mma" and has_kicks_or_clinch and winner_id == fa_id:
        moments = [
            {"frames": 8, "A": {"move": "low_calf_kick"}, "B": {"move": "lead_leg_buckle"}},
            {"frames": 6, "A": {"move": "burst_step_in"}, "B": {"move": "slip_inside"}},
            {"frames": 8, "A": {"move": "slashing_rear_elbow"}, "B": {"move": "head_whip_side"}},
            {"frames": 7, "A": {"move": "high_shell_guard"}, "B": {"move": "cross"}},
            {
                "frames": 8,
                "A": {"overlaps_move": "slip_outside", "move": "lead_liver_hook"},
                "B": {"move": "torso_fold_rib_hit"},
            },
            {"frames": 7, "A": {"move": "single_collar_tie"}, "B": {"move": "clinch_captured_react"}},
            {"frames": 9, "A": {"move": "clinch_rising_knee"}, "B": {"move": "clinch_rib_fold"}},
            {"frames": 7, "A": {"move": "two_hand_clinch_shove"}, "B": {"move": "shoved_back_react"}},
            {
                "frames": 7,
                "A": {"move": "body_elbow_tuck"},
                "B": {"overlaps_move": "slip_inside", "move": "rear_body_straight"},
            },
            {
                "frames": 12,
                "is_hero": True,
                "A": {"overlaps_move": "slip_inside", "move": "spinning_back_kick"},
                "B": {"move": "torso_fold_rib_hit"},
            },
        ]
    else:
        moments = [
            {"frames": 6, "camera": "side_track", "A": {"move": "burst_step_in"}, "B": {"move": "slip_inside"}},
            {"frames": 7, "camera": "impact_jolt", "A": {"move": "jab"}, "B": {"move": "lead_palm_parry"}},
            {"frames": 8, "camera": "impact_jolt", "A": {"move": "high_shell_guard"}, "B": {"move": "cross"}},
            {
                "frames": 8,
                "camera": "pocket_push",
                "A": {"overlaps_move": "slip_outside", "move": "lead_liver_hook"},
                "B": {"move": "torso_fold_rib_hit"},
            },
            {"frames": 7, "camera": "impact_jolt", "A": {"move": "cross"}, "B": {"move": "head_snap_back"}},
            {"frames": 8, "camera": "pocket_push", "A": {"move": "lead_hook"}, "B": {"move": "bob_and_weave"}},
            {"frames": 7, "camera": "impact_jolt", "A": {"move": "body_elbow_tuck"}, "B": {"move": "rear_body_straight"}},
            {"frames": 8, "camera": "impact_jolt", "A": {"move": "lead_uppercut"}, "B": {"move": "head_snap_up"}},
            {
                "frames": 8,
                "camera": "pocket_push",
                "A": {"move": "outside_angle_step"},
                "B": {"overlaps_move": "slip_inside", "move": "rear_hook"},
            },
            {
                "frames": 10,
                "is_hero": True,
                "camera": "hero_finisher_hold",
                "A": {"move": "cross"},
                "B": {"move": "knockout_canvas_collapse"},
            },
        ]

    return {
        "clip_id": f"{plan_id}_movement_prose_10s",
        "name": f"{plan_id}_movement_prose_10s",
        "regime": "standup_striking",
        "initial_range": "kick",
        "arena": "rain-slicked neon-lit rooftop helipad cage arena overlooking a dark cyberpunk skyline, harsh magenta-and-cyan floodlights reflecting off wet concrete, octagonal chain-link perimeter fence in deep background shadow",
        "block_provenance": {
            "version": fight_plan.get("version", "block-1"),
            "ruleset": ruleset,
            "seed": fight_plan.get("seed"),
            "duration": fight_plan.get("duration"),
            "selection": selection,
            "fighter_a_id": fa_id,
            "fighter_b_id": fb_id,
            "event_count": len(fight_plan.get("events", [])),
            "choreography_Summary": {
                "sequence_count": len(choreography.get("sequences", [])) if choreography else 0,
            },
        },
        "fighters": {
            "A": {
                "style": fa_style,
                "stance": "orthodox",
                "screen_side": "left",
                "facing": "right",
                "support": "standing",
                "coil": "neutral",
                "label": fa_label,
                "short_name": fa_short,
            },
            "B": {
                "style": fb_style,
                "stance": "orthodox",
                "screen_side": "right",
                "facing": "left",
                "support": "standing",
                "coil": "neutral",
                "label": fb_label,
                "short_name": fb_short,
            },
        },
        "moments": moments,
    }


def compile_block_fight_to_movement_prose(
    fight_plan: Dict[str, Any],
    choreography: Optional[Dict[str, Any]] = None,
    output_dir: Optional[Path] = None,
    use_kb_priors: bool = True,
) -> Dict[str, Any]:
    """Compile a BLOCK `fight_plan.json` through both Movement_Prose pipelines:
    1. 2-Layer Unrolled Fluid Stack (`sakuga_Xperiment`)
    2. Protected `05:34` (`e91c686`) `SAKUGA-MLLM-3.1-CAUSAL` Single-Layer

    Optionally writes the artifacts into `output_dir` when specified.
    """
    lexicon = Lexicon.load_default()
    clip = block_plan_to_movement_prose_clip(fight_plan, choreography=choreography)

    fluid_prompt, fluid_spec, fluid_val = compile_to_sakuga_Fluid_stack(
        clip,
        lexicon=lexicon,
        emit_chain_in_causal=True,
        schema_name="sakuga_Xperiment",
        mode="xperiment",
        use_kb_priors=use_kb_priors,
    )
    if not fluid_val.ok:
        raise RuntimeError(f"Movement_Prose 2-Layer Fluid Stack validation failed: {fluid_val.errors}")

    orig_ok, orig_sha = verify_original_compiler_protection()
    if not orig_ok:
        raise RuntimeError(f"Original 05:34 compiler protection check failed: {orig_sha}")

    causal_prompt, causal_spec, kb_priors, causal_val = compile_beatsheet_to_original_0534_causal(
        clip,
        lexicon=lexicon,
    )
    if not causal_val.ok:
        raise RuntimeError(f"Original 05:34 SAKUGA-MLLM-3.1-CAUSAL validation failed: {causal_val.errors}")

    lint_errors, lint_warnings = assert_pure_0534_causal_spec(causal_spec, causal_prompt)
    if lint_errors or lint_warnings:
        raise RuntimeError(f"Original 05:34 linter issues: errors={lint_errors}, warnings={lint_warnings}")

    result = {
        "clip_id": clip["clip_id"],
        "block_selection": fight_plan.get("selection", {}),
        "fluid_stack": {
            "schema": "sakuga_Xperiment",
            "passed": fluid_val.ok,
            "prompt_length": len(fluid_prompt),
            "prompt": fluid_prompt,
            "spec": fluid_spec,
        },
        "original_0534_causal": {
            "schema": "SAKUGA-MLLM-3.1-CAUSAL",
            "compiler_sha256": orig_sha,
            "passed": causal_val.ok,
            "lint_errors": len(lint_errors),
            "lint_warnings": len(lint_warnings),
            "prompt_length": len(causal_prompt),
            "prompt": causal_prompt,
            "spec": causal_spec,
            "kb_priors": kb_priors,
        },
    }

    if output_dir is not None:
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        (out / "movement_prose_clip.json").write_text(json.dumps(clip, indent=2) + "\n", encoding="utf-8")
        (out / "movement_prose_fluid_stack.txt").write_text(fluid_prompt + "\n", encoding="utf-8")
        (out / "movement_prose_layer2.json").write_text(json.dumps(fluid_spec, indent=2) + "\n", encoding="utf-8")
        (out / "movement_prose_0534_causal.txt").write_text(causal_prompt + "\n", encoding="utf-8")
        (out / "movement_prose_0534_causal.json").write_text(json.dumps(causal_spec, indent=2) + "\n", encoding="utf-8")

    return result
