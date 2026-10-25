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
    audit_option_coverage_v2,
    audit_round_robin_balance_v2,
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


def _format_balance_audit_text(audit: Dict[str, object]) -> str:
    lines = [
        f"BLOCK Fight Simulator v2 — Round-Robin Balance Audit ({audit['runs_per_pair']} seeds/pair across {audit['pair_count']} pairs)",
        f"Ruleset: {audit['ruleset']} | Arena: {audit['arena']} | Duration: {audit['duration_s']}s | Order Invariance: {audit['order_invariance_verified']}",
        f"Target Band [35%-65%] All Pass: {audit['all_within_target_band_35_65']} | No Pair > 85%: {audit['no_sweep_above_85']} (Max Pairwise: {float(audit['max_pairwise_win_rate'])*100:.1f}%)",
        "=" * 92,
        "1. Overall Archetype Win Rates (Target Band: 35.0% - 65.0%):",
    ]
    for fid, rate in audit["archetype_overall_win_rates"].items():
        status = "PASS" if 0.35 <= float(rate) <= 0.65 else "OUTLIER"
        lines.append(f"  - {fid:<14}: {float(rate)*100:5.1f}%  [{status}]")
    lines.append("\n2. Top Most Skewed Matchups & Top-3 Mechanical Causes:")
    for pair in audit["top_skewed_pairs"][:6]:
        lines.append(
            f"  * {pair['fighter_a']} vs {pair['fighter_b']}: "
            f"{float(pair['win_rate_a'])*100:.1f}% - {float(pair['win_rate_b'])*100:.1f}% | Methods: {pair['method_breakdown']}"
        )
        for idx, c in enumerate(pair["top_3_causes"], start=1):
            lines.append(f"      Cause {idx}: {c}")
    return "\n".join(lines)


def _format_option_audit_text(rep: Dict[str, object]) -> str:
    lines = [
        f"BLOCK Fight Simulator v2 — 57-Option Coverage & Viability Audit ({rep['runs_per_matchup']} seeds/matchup vs 12 archetypes)",
        f"Total Options Tested: {rep['total_options_tested']} | Used on 12 Canonical Cards: {rep['canonical_used_count']} | Custom-Only Options Exercised: {rep['custom_only_tested_count']}",
        f"All 57 Viable (No Dominant/Dead): {rep['all_57_viable']} | Dominant: {len(rep['dominant_options'])} | Dead/Weak: {len(rep['dead_options'])}",
        "=" * 92,
    ]
    for dim, dinfo in rep["by_dimension"].items():
        lines.append(
            f"[{dim.upper()}] Mean={float(dinfo['dimension_mean_win_rate'])*100:.1f}% | "
            f"Range=[{float(dinfo['min_win_rate'])*100:.1f}%, {float(dinfo['max_win_rate'])*100:.1f}%] | "
            f"Spread={float(dinfo['spread'])*100:.1f}%"
        )
        for o in dinfo["options"]:
            tag = "canonical-12" if o["used_on_canonical_12"] else "CUSTOM-TESTED"
            lines.append(
                f"  - {o['option_id']:<26} | win_rate={float(o['win_rate'])*100:5.1f}% | "
                f"delta={float(o['delta_vs_dimension_mean'])*100:+5.1f}% | {tag:<13} | [{o['status']}]"
            )
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Simulate fights between predefined BLOCK v2 fighter archetypes."
    )
    parser.add_argument("fighter_a", nargs="?", help="First fighter archetype ID or card path (e.g., sanda_judo, thai, maleek)")
    parser.add_argument("fighter_b", nargs="?", help="Second fighter archetype ID or card path (e.g., wrestler, detroit, karate)")
    parser.add_argument("--list-archetypes", action="store_true", help="List all 12 predefined block-2 fighter archetypes and exit")
    parser.add_argument("--balance-audit", action="store_true", help="Run round-robin balance audit across all 12 archetypes and report Top-3 causes")
    parser.add_argument("--option-audit", action="store_true", help="Swap each of the 57 options into a neutral probe card and audit viability across the roster")
    parser.add_argument("--ruleset", default="mma", choices=["mma", "boxing"], help="Combat ruleset (default: mma)")
    parser.add_argument("--arena", default="cage", choices=sorted(ARENA_PRESETS.keys()), help="2D arena preset (default: cage)")
    parser.add_argument("--vertical-mode", default="grounded", choices=["grounded", "athletic", "wall_assisted"], help="Vertical mode (default: grounded)")
    parser.add_argument("--duration", type=float, default=60.0, help="Fight clock duration in seconds (default: 60.0)")
    parser.add_argument("--seed", type=int, default=42, help="Deterministic RNG seed for single-fight mode (default: 42)")
    parser.add_argument("--runs", type=int, default=0, help="If > 0, run N Monte Carlo simulations via simulate_many_v2 (or seeds/pair for --balance-audit)")
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

    if args.balance_audit:
        audit_runs = args.runs if args.runs > 0 else 200
        audit = audit_round_robin_balance_v2(
            runs_per_pair=audit_runs,
            ruleset=args.ruleset,
            duration_s=args.duration,
            arena=args.arena,
            knowledge=k,
        )
        if args.json:
            print(json.dumps(audit, indent=2))
        else:
            print(_format_balance_audit_text(audit))
        return 0

    if args.option_audit:
        opt_runs = args.runs if args.runs > 0 else 20
        rep = audit_option_coverage_v2(
            runs_per_matchup=opt_runs,
            ruleset=args.ruleset,
            duration_s=args.duration,
            arena=args.arena,
            knowledge=k,
        )
        if args.json:
            print(json.dumps(rep, indent=2))
        else:
            print(_format_option_audit_text(rep))
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
