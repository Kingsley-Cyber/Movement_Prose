#!/usr/bin/env python3
"""Standalone CLI & LLM Runner for the BLOCK Fight Simulator v2.

Allows an LLM or human user to discover all 12 predefined fighter archetypes and
simulate single fights, Monte Carlo multi-run series, or 1-Contact-Per-Beat
causal prose directly without manual prompting.

Examples:
  python3 simulate_fight.py --list-archetypes
  python3 simulate_fight.py sanda_judo thai --seed 7 --arena cage
  python3 simulate_fight.py sanda_judo thai --seed 7 --emit-prompt
  python3 simulate_fight.py maleek detroit --ruleset boxing --arena ring --runs 50
  python3 simulate_fight.py wrestler thai --runs 30 --winner wrestler --json
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Dict

from engine.ontology import Knowledge
from engine.simulator_v2 import (
    ARENA_PRESETS,
    compile_simulated_fight_to_atomic_beats,
    list_archetypes_v2,
    simulate_fight_v2,
    simulate_many_v2,
)


def _format_archetypes_text(archetypes) -> str:
    lines = [
        f"BLOCK Fight Simulator v2 — {len(archetypes)} Predefined Archetypes (cards/v2/*.json)",
        "=" * 84,
    ]
    for a in archetypes:
        dims = ", ".join(f"{k}={v.split('.')[-1]}" for k, v in a["dimensions"].items() if v)
        slots_str = " | ".join(
            f"{s['id']} ({s['home_range']} -> {s['goal']}: {','.join(s['sequence'])})"
            for s in a["slots"]
        )
        lines.append(
            f"- {a['fighter_id']:<12} | {a['name']:<16} | {a['slot_label']} ({a['slot_count']} slot) | "
            f"tempo={a['tempo']} | {a['orientation']} | {a['combat_identity']}"
        )
        lines.append(f"    Dimensions : {dims}")
        lines.append(f"    Signatures : {', '.join(a['signature_moves'])} | Ranges: {', '.join(a['preferred_ranges'])}")
        lines.append(f"    Gameplans  : {slots_str}")
    return "\n".join(lines)


def _format_single_fight_text(sim: Dict[str, object], emit_prompt: bool = False) -> str:
    actors = sim["actors_final"]
    fa, fb = str(sim["fighter_a"]), str(sim["fighter_b"])
    na, nb = actors[fa]["name"], actors[fb]["name"]
    lines = [
        f"BLOCK Fight Simulator v2 — {na} ({fa}) vs. {nb} ({fb})",
        f"Ruleset: {sim['ruleset']} | Arena: {sim['arena']} | Vertical: {sim['vertical_mode']} | Seed: {sim['seed']}",
        f"Winner : {sim['winner_name']} ({sim['winner_id']}) via {sim['finish_reason']} at {sim['duration_actual_s']:.2f}s ({sim['exchange_count']} exchanges)",
        "-" * 92,
    ]
    for ex in sim["exchanges"]:
        att_name = actors[ex["attacker_id"]]["name"]
        def_name = actors[ex["defender_id"]]["name"]
        dmg = ex["damage"]["final_damage"]
        recoil = ex["damage"]["recoil_leg_damage_to_attacker"]
        kick = ex.get("kick_anatomy")
        kick_tag = (
            f" [{kick['kicking_leg']} {kick['striking_surface']}, {kick['path']}]"
            if kick
            else ""
        )
        def_tag = f" vs {ex['defense_used']}" if ex.get("defense_used") else ""
        recoil_tag = f" (recoil_leg={recoil:.2f})" if recoil > 0 else ""
        counter = ex.get("counter_followup")
        counter_tag = (
            f" -> COUNTER {counter['technique_id']} ({counter['damage']['final_damage']:.2f} dmg)"
            if counter
            else ""
        )
        slot_tag = f" [SWITCH -> {ex['slot_switched_to']}]" if ex.get("slot_switched_to") else ""
        lines.append(
            f"[{ex['exchange_index']:02d}] {ex['t_start']:5.2f}s-{ex['t_end']:5.2f}s | {ex['range']:<6} | "
            f"{att_name} ({ex['active_slot_id']}) -> {ex['technique_id']}{kick_tag}{def_tag} "
            f"on {def_name} (lane={ex['attack_lane']} rdy={ex['lane_readiness_score']:.2f}, p={ex['hit_probability']:.2f}) "
            f"=> {ex['outcome'].upper()} (dmg={dmg:.2f}{recoil_tag}){counter_tag}{slot_tag}"
        )

    lines.append("-" * 92)
    for fid in (fa, fb):
        st = actors[fid]
        d = st["damage"]
        lines.append(
            f"Final {st['name']} ({fid}): head={d['head']:.2f}, body={d['body']:.2f}, leg={d['leg']:.2f} | "
            f"fatigue={st['fatigue']:.2f} | pos={st['grappling_position']} | slot_switches={st['slot_switches']}"
        )

    if emit_prompt:
        compiled = compile_simulated_fight_to_atomic_beats(sim)
        lines.append("\n" + "=" * 92)
        lines.append("ATOMIC 1-CONTACT-PER-BEAT CAUSAL IR (Prep -> Commit -> Contact -> Consequence -> Recovery)")
        lines.append("=" * 92)
        lines.append(str(compiled["labeled_ir"]))
        lines.append("\n" + "=" * 92)
        lines.append("SINGLE-SENTENCE UNLABELED PROSE")
        lines.append("=" * 92)
        lines.append(str(compiled["unlabeled_prose"]))

    return "\n".join(lines)


def _format_many_runs_text(res: Dict[str, object]) -> str:
    fa, fb = str(res["fighter_a"]), str(res["fighter_b"])
    rep = res["representative_fight"]
    lines = [
        f"BLOCK Fight Simulator v2 — Monte Carlo Series ({res['runs']} seeded runs)",
        f"Matchup: {fa} vs. {fb} | Ruleset: {res['ruleset']} | Arena: {res['arena']} | Avg Duration: {res['average_duration_s']:.2f}s",
        f"Win Rates: {fa}={res['empirical_win_rate_a']*100:.1f}% ({res['win_counts'][fa]}) | "
        f"{fb}={res['empirical_win_rate_b']*100:.1f}% ({res['win_counts'][fb]})",
        f"Methods  : {res['method_breakdown']}",
        f"Deciding Slots : {res['deciding_slots']}",
        f"Deciding Lanes : {res['deciding_weakness_lanes']}",
        "=" * 92,
        "Representative Fight:",
        _format_single_fight_text(rep, emit_prompt=False),
    ]
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Simulate fights between predefined BLOCK v2 fighter archetypes."
    )
    parser.add_argument("fighter_a", nargs="?", help="First fighter archetype ID or card path (e.g., sanda_judo, thai, maleek)")
    parser.add_argument("fighter_b", nargs="?", help="Second fighter archetype ID or card path (e.g., wrestler, detroit, karate)")
    parser.add_argument("--list-archetypes", action="store_true", help="List all 12 predefined block-2 fighter archetypes and exit")
    parser.add_argument("--ruleset", default="mma", choices=["mma", "boxing"], help="Combat ruleset (default: mma)")
    parser.add_argument("--arena", default="cage", choices=sorted(ARENA_PRESETS.keys()), help="2D arena preset (default: cage)")
    parser.add_argument("--vertical-mode", default="grounded", choices=["grounded", "athletic", "wall_assisted"], help="Vertical mode (default: grounded)")
    parser.add_argument("--duration", type=float, default=60.0, help="Fight clock duration in seconds (default: 60.0)")
    parser.add_argument("--seed", type=int, default=42, help="Deterministic RNG seed for single-fight mode (default: 42)")
    parser.add_argument("--runs", type=int, default=0, help="If > 0, run N Monte Carlo simulations via simulate_many_v2")
    parser.add_argument("--winner", default=None, help="Optional Director Mode winner fighter_id for --runs")
    parser.add_argument("--emit-prompt", action="store_true", help="Compile simulated exchanges into Atomic 1-Contact-Per-Beat Causal IR and prose")
    parser.add_argument("--json", action="store_true", help="Emit structured JSON output for LLM/programmatic consumption")

    args = parser.parse_args(argv)
    k = Knowledge()

    if args.list_archetypes:
        archetypes = list_archetypes_v2(k)
        if args.json:
            print(json.dumps({"version": "block-2", "archetypes": archetypes}, indent=2))
        else:
            print(_format_archetypes_text(archetypes))
        return 0

    if not args.fighter_a or not args.fighter_b:
        parser.error("Provide two fighter archetype IDs (e.g. `sanda_judo thai`) or use `--list-archetypes`.")

    if args.runs > 0:
        res = simulate_many_v2(
            args.fighter_a,
            args.fighter_b,
            runs=args.runs,
            ruleset=args.ruleset,
            duration_s=args.duration,
            arena=args.arena,
            vertical_mode=args.vertical_mode,
            directed_winner=args.winner,
            knowledge=k,
        )
        if args.json:
            print(json.dumps(res, indent=2))
        else:
            print(_format_many_runs_text(res))
        return 0

    sim = simulate_fight_v2(
        args.fighter_a,
        args.fighter_b,
        ruleset=args.ruleset,
        duration_s=args.duration,
        seed=args.seed,
        arena=args.arena,
        vertical_mode=args.vertical_mode,
        knowledge=k,
    )
    if args.emit_prompt:
        sim["atomic_causal_beats"] = compile_simulated_fight_to_atomic_beats(sim)

    if args.json:
        print(json.dumps(sim, indent=2))
    else:
        print(_format_single_fight_text(sim, emit_prompt=args.emit_prompt))
    return 0


if __name__ == "__main__":
    sys.exit(main())
