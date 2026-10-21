"""CLI & Render Packet Generator for Fight Move System (v2)."""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from .compiler import compile_clip_prompt
from .composer import compose_clips
from .lexicon import Lexicon
from .validator import validate_clip


def generate_m4_packets(out_dir: Path) -> Dict[str, Any]:
    """Generate M4 render packets (H1, H5, H6 + single-move boxing word probes) without making live API calls."""
    out_dir.mkdir(parents=True, exist_ok=True)
    lex = Lexicon.load_default()

    # 1. Word probe packet for all boxing moves in boxing_v1.json
    boxing_probes: List[Dict[str, Any]] = []
    for move_id, card in sorted(lex.cards_by_id.items()):
        if "boxing" not in card["styles"]:
            continue
        boxing_probes.append(
            {
                "probe_id": f"probe_boxing_{move_id}",
                "move_id": move_id,
                "class": card["class"],
                "caption_prompt": (
                    "Hand-drawn anime martial arts animation with bold black ink linework. "
                    "In a side-profile medium-wide shot, a lean boxer in crimson trunks on the left faces a heavy boxer in black pants on the right at arm's length. "
                    f"The crimson-trunks boxer on the left {card['caption_words'].format(lead_hand='left', rear_hand='right', lead_leg='left', rear_leg='right', lead_side='left', rear_side='right')} "
                    f"with his {card['off_limbs']['other_arm'].format(lead_hand='left', rear_hand='right', lead_leg='left', rear_leg='right', lead_side='left', rear_side='right')}, "
                    f"{card['off_limbs']['lead_leg'].format(lead_hand='left', rear_hand='right', lead_leg='left', rear_leg='right', lead_side='left', rear_side='right')}, "
                    f"and {card['off_limbs']['rear_leg'].format(lead_hand='left', rear_hand='right', lead_leg='left', rear_leg='right', lead_side='left', rear_side='right')}."
                ),
                "owner_instruction": f"Render once on target model; mark 'works' if the fighter cleanly executes '{move_id}' with both arms distinct, 'partial' if sluggish, or 'fails' if wrong limb/pose.",
            }
        )

    # 2. Hypothesis A/B test packets (H1, H5, H6)
    fixture_path = Path(__file__).parent / "fixtures" / "pass" / "10_beat_boxing_exchange.json"
    with open(fixture_path, "r", encoding="utf-8") as f:
        exchange_clip = json.load(f)
    compiled_exchange, _ = compile_clip_prompt(exchange_clip, lexicon=lex)

    hypothesis_packets = {
        "H1_plain_caption_vs_expert_names": {
            "hypothesis_id": "H1",
            "hypothesis": "Plain body-shape caption words beat martial-arts / franchise names.",
            "arm_A_caption_words": (
                "Hand-drawn anime martial arts animation. On the left, a lean fighter in crimson trunks steps in at arm's length "
                "and drops into a deep lunge with his rear knee low to the floor, driving his right fist straight forward at chin height "
                "while his left fist guards his left cheek, snapping the right-side fighter's head backward."
            ),
            "arm_B_expert_franchise_names": (
                "Hand-drawn anime martial arts animation. On the left, a lean fighter in crimson trunks executes a Baki Triceratops Fist "
                "Cockroach Dash Mach Straight into the right-side fighter's chin."
            ),
            "owner_instruction": "Render Arm A and Arm B (three times each if budget allows). Pass if Arm A executes the low-lunge straight punch more often without freezing into a static raised-fist pose.",
        },
        "H5_four_limb_occupancy_vs_single_limb": {
            "hypothesis_id": "H5",
            "hypothesis": "4-limb occupancy text on strike beats fixes the missing/merged off-arm bug.",
            "arm_A_four_limb_text": (
                "Hand-drawn anime martial arts animation. At arm's length in side profile, the crimson-trunks fighter on the left "
                "drives a heavy straight punch with the right fist down the centerline toward the jaw with his left fist retracted tight "
                "against the left cheekbone in a high guard, both arms clearly separate from the torso, left leg braced firm at the front "
                "of the stance, and right hip and heel pivoting hard."
            ),
            "arm_B_single_limb_only": (
                "Hand-drawn anime martial arts animation. At arm's length in side profile, the crimson-trunks fighter on the left "
                "throws a heavy right straight punch to the jaw."
            ),
            "owner_instruction": "Compare off-hand visibility during the punch apex. Pass if Arm A shows fewer missing or torso-merged left arms than Arm B.",
        },
        "H6_fluid_coil_chained_vs_neutral_reset": {
            "hypothesis_id": "H6",
            "hypothesis": "Coil-chained beats read more fluidly than reset-to-neutral beats.",
            "arm_A_coil_chained_10_beat_exchange": compiled_exchange,
            "arm_B_reset_between_hits": (
                "Hand-drawn anime martial arts animation. The crimson-trunks boxer on the left throws a left jab, then returns to a neutral standing guard and pauses. "
                "Next he throws a right cross, then returns to a neutral standing guard and pauses. "
                "Next he throws a left hook, then returns to a neutral standing guard."
            ),
            "owner_instruction": "Compare motion continuity across the exchange. Pass if Arm A reads as a continuous fluid fight and Arm B reads stiffer/stop-and-go.",
        },
    }

    packet_bundle = {
        "meta": {
            "milestone": "M4",
            "status": "ready_for_owner_render",
            "paid_calls_made_by_agent": 0,
        },
        "hypothesis_packets": hypothesis_packets,
        "boxing_word_probes": boxing_probes,
    }

    packet_file = out_dir / "m4_render_packet.json"
    with open(packet_file, "w", encoding="utf-8") as f:
        json.dump(packet_bundle, f, indent=2)

    return packet_bundle


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="fight_move_system", description="Fight Move System v2 CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_val = sub.add_parser("validate", help="Validate a beat-sheet JSON file")
    p_val.add_argument("input", type=Path, help="Path to beat-sheet JSON")

    p_comp = sub.add_parser("compile", help="Validate, compose clips, and compile caption prompts")
    p_comp.add_argument("input", type=Path, help="Path to beat-sheet JSON")
    p_comp.add_argument("-o", "--output", type=Path, default=None, help="Optional output file path")

    p_pkt = sub.add_parser("packet", help="Generate M4 hypothesis and word-probe render packets")
    p_pkt.add_argument(
        "--out-dir",
        type=Path,
        default=Path(__file__).parent / "packets",
        help="Directory to write render packet JSON",
    )

    args = parser.parse_args(argv)

    if args.cmd == "validate":
        with open(args.input, "r", encoding="utf-8") as f:
            data = json.load(f)
        clips, notes = compose_clips(data)
        all_ok = True
        for idx, clip in enumerate(clips):
            res = validate_clip(clip)
            print(f"=== Clip {idx + 1} ({clip.get('regime', 'standup_striking')}) ===")
            for note in notes:
                print(f"  [NOTE]  {note}")
            for code, msg in res.warnings:
                print(f"  [WARN]  [{code}] {msg}")
            for code, msg in res.errors:
                print(f"  [ERROR] [{code}] {msg}")
            if not res.ok:
                all_ok = False
            else:
                print(f"  [PASSED] {len(res.errors)} errors, {len(res.warnings)} warnings")
        return 0 if all_ok else 1

    if args.cmd == "compile":
        with open(args.input, "r", encoding="utf-8") as f:
            data = json.load(f)
        clips, notes = compose_clips(data)
        prompts: List[str] = []
        for idx, clip in enumerate(clips):
            prompt, res = compile_clip_prompt(clip)
            if not res.ok:
                for code, msg in res.errors:
                    print(f"[ERROR] [{code}] {msg}", file=sys.stderr)
                return 1
            prompts.append(prompt)
        full_output = "\n\n---\n\n".join(prompts)
        if args.output:
            args.output.write_text(full_output + "\n", encoding="utf-8")
        else:
            print(full_output)
        return 0

    if args.cmd == "packet":
        bundle = generate_m4_packets(args.out_dir)
        print(
            f"[OK] Generated {len(bundle['boxing_word_probes'])} word probes and {len(bundle['hypothesis_packets'])} hypothesis packets in {args.out_dir / 'm4_render_packet.json'}"
        )
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
