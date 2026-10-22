"""CLI & Render Packet Generator for Fight Move System (v2)."""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from .closed_loop import (
    apply_localized_repair,
    build_next_clip_handoff,
    ingest_render_verdict,
    parse_scorecard_markdown,
    plan_localized_repair,
)
from .compiler import compile_clip_prompt, compile_to_sakuga_Fluid_stack
from .composer import compose_clips
from .kb_bridge import (
    kb_find,
    kb_lookup,
    kb_verify,
    query_kb_prior_to_semantic_intent,
    sync_lexicon_gaps_to_memory,
    verify_bundle_integrity,
)
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
    p_comp.add_argument(
        "--mode",
        choices=["xperiment", "lean"],
        default="xperiment",
        help="Compilation profile: 'xperiment' (full sakuga_Xperiment) or 'lean'",
    )
    p_comp.add_argument(
        "--schema",
        type=str,
        default="sakuga_Xperiment",
        help="Layer 2 schema tag (default: sakuga_Xperiment)",
    )
    p_comp.add_argument(
        "--json-out",
        type=Path,
        default=None,
        help="Optional path to write the compiled Layer 2 JSON spec",
    )

    p_pkt = sub.add_parser("packet", help="Generate M4 hypothesis and word-probe render packets")
    p_pkt.add_argument(
        "--out-dir",
        type=Path,
        default=Path(__file__).parent / "packets",
        help="Directory to write render packet JSON",
    )

    p_kbsync = sub.add_parser("kb-sync", help="Verify KB bundle SHA256 and sync lexical/taste gaps to agent_memory.db")
    p_kbsync.add_argument("--bundle-dir", type=Path, default=None, help="Optional path to anime_action_research_bundle")

    p_kbfind = sub.add_parser("kb-find", help="Search the Handbook FTS5 index, semantic directives, and agent_memory")
    p_kbfind.add_argument("query", type=str, help="Query string")
    p_kbfind.add_argument("--limit", type=int, default=8, help="Max results")

    p_kblook = sub.add_parser("kb-lookup", help="Look up aa_* semantic directives by moment/slot")
    p_kblook.add_argument("--moment", type=str, default=None, help="Moment type (e.g. strike, reaction, camera)")
    p_kblook.add_argument("--slot", type=str, default=None, help="Grammar slot (e.g. verb, manner, camera_motion)")

    p_kbask = sub.add_parser(
        "kb-ask",
        help="Query the Knowledge Base PRIOR to semantic intent (surfaces moments, slots, concepts, directives, relations, causal triples, knobs, and animation_grammar)",
    )
    p_kbask.add_argument("input_or_request", type=str, help="Natural language fight request OR path to beat-sheet JSON")
    p_kbask.add_argument("--taste", type=str, default="heavy, brutal, old school", help="Taste profile vibe words")
    p_kbask.add_argument("--follow", type=int, default=2, help="Module relation follow depth (1 or 2)")
    p_kbask.add_argument("--discover", type=int, default=2, help="Swanson A->B<-C bridge hypotheses count")
    p_kbask.add_argument("--knob", action="append", default=None, help="axis=option, repeatable")

    p_kbver = sub.add_parser("kb-verify", help="Run SHA256SUMS.bundle + 25-check agent.verify integrity suite")
    p_kbver.add_argument("--bundle-dir", type=Path, default=None, help="Optional path to knowledge_base")

    p_ing = sub.add_parser("ingest-verdict", help="Ingest a render verdict or markdown scorecard into priors + agent_memory")
    p_ing.add_argument("--run-id", type=str, default="manual_render_run", help="Render run identifier")
    p_ing.add_argument("--scorecard", type=Path, default=None, help="Path to markdown scorecard")
    p_ing.add_argument("--move-id", type=str, default=None, help="Single move_id to update in word_probes.json")
    p_ing.add_argument("--status", choices=["works", "partial", "fails"], default=None, help="Probe status")
    p_ing.add_argument("--quarantine-pair", nargs=2, metavar=("PREV_MOVE", "NEXT_MOVE"), default=None)
    p_ing.add_argument("--quarantine-reason", type=str, default="Empirical transition failure")

    p_rep = sub.add_parser("repair", help="Generate and optionally apply a localized RFC 6902 JSON Patch repair for a beat")
    p_rep.add_argument("input", type=Path, help="Path to beat-sheet JSON")
    p_rep.add_argument("--beat", type=int, required=True, help="0-based beat index to repair")
    p_rep.add_argument(
        "--failure",
        choices=[
            "contact_flicker",
            "phantom_force",
            "dead_contact",
            "pose_reset",
            "support_swap",
            "camera_occlusion",
            "mismatched_hands",
        ],
        required=True,
        help="Observed failure class from Handbook src-cpcs-mx-repair_strategy",
    )
    p_rep.add_argument("--apply-out", type=Path, default=None, help="Write patched beat-sheet JSON to this path")

    p_next = sub.add_parser("next-clip", help="Extract t=10.0s terminal fighter & dyad state to seed Clip N+1")
    p_next.add_argument("input", type=Path, help="Path to Clip N beat-sheet JSON")
    p_next.add_argument("-o", "--output", type=Path, default=None, help="Optional path to write Clip N+1 seed JSON")

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
        specs: List[Dict[str, Any]] = []
        for idx, clip in enumerate(clips):
            prompt, spec, res = compile_to_sakuga_Fluid_stack(
                clip,
                emit_chain_in_causal=(args.mode != "lean"),
                schema_name=args.schema,
                mode=args.mode,
            )
            if not res.ok:
                for code, msg in res.errors:
                    print(f"[ERROR] [{code}] {msg}", file=sys.stderr)
                return 1
            prompts.append(prompt)
            specs.append(spec)
        full_output = "\n\n---\n\n".join(prompts)
        if args.output:
            args.output.write_text(full_output + "\n", encoding="utf-8")
        else:
            print(full_output)
        if args.json_out and specs:
            args.json_out.write_text(json.dumps(specs[0] if len(specs) == 1 else specs, indent=2) + "\n", encoding="utf-8")
        return 0

    if args.cmd == "packet":
        bundle = generate_m4_packets(args.out_dir)
        print(
            f"[OK] Generated {len(bundle['boxing_word_probes'])} word probes and {len(bundle['hypothesis_packets'])} hypothesis packets in {args.out_dir / 'm4_render_packet.json'}"
        )
        return 0

    if args.cmd == "kb-sync":
        ok, errs = verify_bundle_integrity(args.bundle_dir) if args.bundle_dir else verify_bundle_integrity()
        sync_res = sync_lexicon_gaps_to_memory(args.bundle_dir) if args.bundle_dir else sync_lexicon_gaps_to_memory()
        print(json.dumps({"integrity": {"ok": ok, "errors": errs}, "sync": sync_res}, indent=2))
        return 0 if ok else 1

    if args.cmd == "kb-find":
        print(json.dumps(kb_find(args.query, limit=args.limit), indent=2))
        return 0

    if args.cmd == "kb-lookup":
        print(json.dumps(kb_lookup(moment=args.moment, slot=args.slot), indent=2))
        return 0

    if args.cmd == "kb-ask":
        p = Path(args.input_or_request)
        if p.is_file():
            target_input = json.loads(p.read_text(encoding="utf-8"))
        else:
            target_input = args.input_or_request
        res = query_kb_prior_to_semantic_intent(
            target_input,
            taste=args.taste,
            follow_depth=args.follow,
            discover_count=args.discover,
            knobs_spec=args.knob,
        )
        print(json.dumps(res, indent=2))
        return 0

    if args.cmd == "kb-verify":
        ver = kb_verify(args.bundle_dir) if args.bundle_dir else kb_verify()
        print(json.dumps(ver, indent=2))
        return 0 if ver.get("ok") else 1

    if args.cmd == "ingest-verdict":
        bleed_pair = tuple(args.quarantine_pair) if args.quarantine_pair else None
        verdict = args.status or "works"
        scorecard_notes = ""
        if args.scorecard and args.scorecard.exists():
            sc_text = args.scorecard.read_text(encoding="utf-8")
            rows = parse_scorecard_markdown(sc_text)
            scorecard_notes = f"Parsed scorecard {args.scorecard.name}: {len(rows)} rows"
        summary = ingest_render_verdict(
            render_id=args.run_id,
            model_id="seedance-2.0",
            verdict=verdict,
            move_id=args.move_id,
            bleed_pair=bleed_pair,
            notes=scorecard_notes or args.quarantine_reason,
        )
        print(json.dumps(summary, indent=2))
        return 0

    if args.cmd == "repair":
        with open(args.input, "r", encoding="utf-8") as f:
            clip = json.load(f)
        plan = plan_localized_repair(clip, beat_index=args.beat, failure_type=args.failure)
        if args.apply_out:
            repaired = apply_localized_repair(clip, plan)
            args.apply_out.write_text(json.dumps(repaired, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(plan, indent=2))
        return 0

    if args.cmd == "next-clip":
        with open(args.input, "r", encoding="utf-8") as f:
            clip = json.load(f)
        handoff = build_next_clip_handoff(clip)
        if args.output:
            args.output.write_text(json.dumps(handoff, indent=2) + "\n", encoding="utf-8")
        else:
            print(json.dumps(handoff, indent=2))
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
