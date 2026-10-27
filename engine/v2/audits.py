"""Round-robin balance auditor and 57-option coverage auditor for BLOCK Simulator v2."""

from __future__ import annotations

import copy
from typing import Any

from ..capabilities import KNOWN_CAPABILITIES
from ..ontology import Knowledge
from .cards import load_card_v2
from .data import load_model_v2
from .exchange import simulate_fight_v2
from .montecarlo import simulate_many_v2


def explain_matchup_top_causes_v2(
    many_result: dict[str, Any],
    card_a: dict[str, Any],
    card_b: dict[str, Any],
) -> list[str]:
    """Extract the top 3 concrete mechanical causes explaining a pairwise matchup outcome."""
    wa = float(many_result["empirical_win_rate_a"])
    wb = float(many_result["empirical_win_rate_b"])
    fav_card, dog_card = (card_a, card_b) if wa >= wb else (card_b, card_a)
    fav_id, dog_id = str(fav_card["fighter_id"]), str(dog_card["fighter_id"])

    rep = many_result["representative_fight"]
    exchanges = list(rep.get("exchanges", []))
    total_ex = max(1, len(exchanges))

    range_counts: dict[str, int] = {}
    fav_rdy_list: list[float] = []
    dog_rdy_list: list[float] = []
    counter_count = 0
    catch_or_check_count = 0

    for ex in exchanges:
        r = str(ex["range"])
        range_counts[r] = range_counts.get(r, 0) + 1
        if ex["defender_id"] == fav_id:
            fav_rdy_list.append(float(ex["lane_readiness_score"]))
        else:
            dog_rdy_list.append(float(ex["lane_readiness_score"]))
        if ex.get("counter_followup") and ex["counter_followup"].get("counter_actor_id") == fav_id:
            counter_count += 1
        if ex["defender_id"] == fav_id and ex["outcome"] in ("caught", "checked"):
            catch_or_check_count += 1

    top_range, top_range_n = max(range_counts.items(), key=lambda kv: kv[1]) if range_counts else ("punch", 0)
    top_lane = (
        max(many_result["deciding_weakness_lanes"].items(), key=lambda kv: kv[1])[0]
        if many_result.get("deciding_weakness_lanes")
        else "head_straight"
    )
    top_method = (
        max(many_result["method_breakdown"].items(), key=lambda kv: kv[1])[0]
        if many_result.get("method_breakdown")
        else "Decision"
    )
    fav_avg_rdy = sum(fav_rdy_list) / max(1, len(fav_rdy_list))
    dog_avg_rdy = sum(dog_rdy_list) / max(1, len(dog_rdy_list))
    fav_ctrl = int(rep["actors_final"][fav_id].get("control_marks", 0))

    return [
        (
            f"Range & Footwork Control: {top_range_n}/{total_ex} exchanges ({top_range_n / total_ex * 100:.0f}%) "
            f"took place at `{top_range}` range (favoring {fav_id}'s {fav_card['dimensions'].get('stance')} / {fav_card['dimensions'].get('mentality')})"
        ),
        (
            f"Posture & Seam Readiness Delta: {fav_id} maintained {fav_avg_rdy:.2f} avg lane readiness vs "
            f"{dog_id}'s {dog_avg_rdy:.2f}, exploiting the `{top_lane}` seam toward `{top_method}` finishes"
        ),
        (
            f"Tactical Counters & Control: {fav_id} generated {counter_count} contested counters, "
            f"{catch_or_check_count} kick catches/checks, and {fav_ctrl} grappling control marks"
        ),
    ]


def audit_round_robin_balance_v2(
    runs_per_pair: int = 200,
    ruleset: str = "mma",
    duration_s: float = 60.0,
    arena: str = "cage",
    verify_order_invariance_seeds: int = 5,
    knowledge: Knowledge | None = None,
) -> dict[str, Any]:
    """Run an all-pairs round-robin balance audit across all 12 predefined block-2 archetypes."""
    k = knowledge or Knowledge()
    model_cfg = load_model_v2(k.root)
    aud_cfg = model_cfg.get("audits", {})
    band_lo, band_hi = aud_cfg.get("overall_band", [0.35, 0.65])
    pair_max = float(aud_cfg.get("pair_max", 0.85))

    v2_dir = k.root / "cards" / "v2"
    ids = sorted([p.stem for p in v2_dir.glob("*.json")]) if v2_dir.exists() else sorted(list(k.cards.keys()))
    cards_map = {fid: load_card_v2(k, fid) for fid in ids}

    wins = {fid: 0.0 for fid in ids}
    matches = {fid: 0 for fid in ids}
    pairwise_records: list[dict[str, Any]] = []
    order_invariance_ok = True

    for i, a in enumerate(ids):
        for b in ids[i + 1 :]:
            res = simulate_many_v2(
                cards_map[a],
                cards_map[b],
                runs=runs_per_pair,
                ruleset=ruleset,
                duration_s=duration_s,
                arena=arena,
                knowledge=k,
            )
            wa = float(res["empirical_win_rate_a"])
            wb = float(res["empirical_win_rate_b"])
            wins[a] += wa
            wins[b] += wb
            matches[a] += 1
            matches[b] += 1

            for s in range(1, verify_order_invariance_seeds + 1):
                f_ab = simulate_fight_v2(cards_map[a], cards_map[b], ruleset=ruleset, duration_s=duration_s, seed=s, arena=arena, knowledge=k)
                f_ba = simulate_fight_v2(cards_map[b], cards_map[a], ruleset=ruleset, duration_s=duration_s, seed=s, arena=arena, knowledge=k)
                if f_ab["winner_id"] != f_ba["winner_id"] or f_ab["exchange_count"] != f_ba["exchange_count"]:
                    order_invariance_ok = False

            causes = explain_matchup_top_causes_v2(res, cards_map[a], cards_map[b])
            pairwise_records.append(
                {
                    "fighter_a": a,
                    "fighter_b": b,
                    "win_rate_a": wa,
                    "win_rate_b": wb,
                    "max_win_rate": round(max(wa, wb), 3),
                    "method_breakdown": res["method_breakdown"],
                    "top_3_causes": causes,
                }
            )

    overall_rates = {
        fid: round(wins[fid] / max(1, matches[fid]), 3)
        for fid in sorted(ids, key=lambda x: wins[x] / max(1, matches[x]), reverse=True)
    }
    pairwise_records.sort(key=lambda r: float(r["max_win_rate"]), reverse=True)
    max_pair_rate = max((float(r["max_win_rate"]) for r in pairwise_records), default=0.5)
    outliers_overall = {
        fid: rate for fid, rate in overall_rates.items() if rate < float(band_lo) or rate > float(band_hi)
    }
    outliers_pairwise = [r for r in pairwise_records if float(r["max_win_rate"]) > pair_max]

    return {
        "runs_per_pair": runs_per_pair,
        "ruleset": ruleset,
        "duration_s": duration_s,
        "arena": arena,
        "archetype_count": len(ids),
        "pair_count": len(pairwise_records),
        "order_invariance_verified": order_invariance_ok,
        "archetype_overall_win_rates": overall_rates,
        "all_within_target_band_35_65": len(outliers_overall) == 0,
        "overall_outliers": outliers_overall,
        "max_pairwise_win_rate": max_pair_rate,
        "no_sweep_above_85": len(outliers_pairwise) == 0,
        "pairwise_outliers_above_85": outliers_pairwise,
        "top_skewed_pairs": pairwise_records[:10],
        "pairwise_matrix": pairwise_records,
    }


def audit_option_coverage_v2(
    runs_per_matchup: int = 20,
    ruleset: str = "mma",
    duration_s: float = 60.0,
    arena: str = "cage",
    knowledge: Knowledge | None = None,
) -> dict[str, Any]:
    """Swap each of the 57 options one at a time into a neutral 2-slot baseline card,
    run it against all 12 predefined archetypes, and flag any option that is dominant or useless/dead.
    """
    k = knowledge or Knowledge()
    model_cfg = load_model_v2(k.root)
    probe_cfg = model_cfg.get("legacy", {}).get("option_audit_probe", {})
    v2_dir = k.root / "cards" / "v2"
    roster_ids = sorted([p.stem for p in v2_dir.glob("*.json")]) if v2_dir.exists() else sorted(list(k.cards.keys()))
    roster_cards = {fid: load_card_v2(k, fid) for fid in roster_ids}
    all_techs = sorted(list(k.techniques.keys()))

    canonical_used_options = {
        opt_id
        for c in roster_cards.values()
        for opt_id in c["dimensions"].values()
        if opt_id is not None
    }

    baseline_dims = dict(probe_cfg.get("baseline_dims", {}))
    no_kick_opt = probe_cfg.get("no_kicking_option")
    s1_no_kick = list(probe_cfg.get("slot_1_seq_no_kick", []))
    s1_default = list(probe_cfg.get("slot_1_seq_default", []))
    slot_2_seq = list(probe_cfg.get("slot_2_seq", []))
    switching_opts = set(probe_cfg.get("switching_options", []))
    tpl_fid = str(probe_cfg.get("template_fighter_id", roster_ids[0]))

    by_dimension: dict[str, list[dict[str, Any]]] = {}
    all_option_records: list[dict[str, Any]] = []

    for opt_id, opt_meta in sorted(k.options.items()):
        dim = str(opt_meta["dimension"])
        dims = dict(baseline_dims)
        dims[dim] = opt_id

        slot_1_seq = s1_no_kick if opt_id == no_kick_opt else s1_default

        probe_card = copy.deepcopy(roster_cards[tpl_fid])
        probe_card["fighter_id"] = f"probe_{opt_id.replace('.', '_')}"
        probe_card["name"] = f"Probe ({opt_id})"
        probe_card["combat_identity"] = f"Neutral 2-slot probe card testing {opt_id}"
        probe_card["slot_count"] = 2
        probe_card["slot_label"] = "Two-piece"
        probe_card["tempo"] = 3
        probe_card["orientation"] = "switching" if opt_id in switching_opts else "orthodox"
        probe_card["preferred_ranges"] = ["punch", "kick"]
        probe_card["dimensions"] = dims
        probe_card["exploitable_seams"] = sorted(
            {d for oid in dims.values() if oid for d in k.options[oid]["exploitable_debt_ids"]}
        )
        probe_card["baseline_capabilities"] = sorted(list(KNOWN_CAPABILITIES))
        probe_card["synchronized_capabilities"] = [
            {
                "id": "slot_1_striking",
                "capabilities": ["boxing", "kickboxing"],
                "description": "Probe striking sequence",
                "sequence": slot_1_seq,
                "trigger": "fight_start",
                "home_range": "punch",
                "goal": "head_damage",
                "abandon_rule": {"max_consecutive_stalls": 2, "condition": "2 consecutive stalls"},
                "links": ["slot_2_clinch"],
            },
            {
                "id": "slot_2_clinch",
                "capabilities": ["wrestling", "clinch"],
                "description": "Probe clinch sequence",
                "sequence": slot_2_seq,
                "trigger": "slot_stalled_or_countered",
                "home_range": "clinch",
                "goal": "clinch_control",
                "abandon_rule": {"max_consecutive_stalls": 2, "condition": "2 consecutive stalls"},
                "links": ["slot_1_striking"],
            },
        ]
        probe_card["active_techniques"] = all_techs
        probe_card["signature_moves"] = slot_1_seq[:3]
        probe_card["conditional_abilities"] = []

        total_wins = 0.0
        for opp_id in roster_ids:
            res = simulate_many_v2(
                probe_card,
                roster_cards[opp_id],
                runs=runs_per_matchup,
                ruleset=ruleset,
                duration_s=duration_s,
                arena=arena,
                knowledge=k,
            )
            total_wins += float(res["empirical_win_rate_a"])

        avg_wr = round(total_wins / len(roster_ids), 3)
        rec: dict[str, Any] = {
            "option_id": opt_id,
            "dimension": dim,
            "used_on_canonical_12": opt_id in canonical_used_options,
            "win_rate": avg_wr,
        }
        by_dimension.setdefault(dim, []).append(rec)
        all_option_records.append(rec)

    dim_summaries: dict[str, dict[str, Any]] = {}
    dominant_options: list[dict[str, Any]] = []
    dead_options: list[dict[str, Any]] = []

    for dim, recs in by_dimension.items():
        mean_wr = sum(float(r["win_rate"]) for r in recs) / max(1, len(recs))
        for r in recs:
            delta = round(float(r["win_rate"]) - mean_wr, 3)
            r["delta_vs_dimension_mean"] = delta
            if float(r["win_rate"]) > 0.68 or delta > 0.14:
                r["status"] = "DOMINANT"
                dominant_options.append(r)
            elif float(r["win_rate"]) < 0.32 or delta < -0.14:
                r["status"] = "DEAD_OR_WEAK"
                dead_options.append(r)
            else:
                r["status"] = "VIABLE"
        recs.sort(key=lambda x: float(x["win_rate"]), reverse=True)
        dim_summaries[dim] = {
            "dimension_mean_win_rate": round(mean_wr, 3),
            "min_win_rate": min(float(r["win_rate"]) for r in recs),
            "max_win_rate": max(float(r["win_rate"]) for r in recs),
            "spread": round(max(float(r["win_rate"]) for r in recs) - min(float(r["win_rate"]) for r in recs), 3),
            "options": recs,
        }

    return {
        "total_options_tested": len(all_option_records),
        "canonical_used_count": sum(1 for r in all_option_records if r["used_on_canonical_12"]),
        "custom_only_tested_count": sum(1 for r in all_option_records if not r["used_on_canonical_12"]),
        "runs_per_matchup": runs_per_matchup,
        "all_57_viable": len(dominant_options) == 0 and len(dead_options) == 0,
        "dominant_options": dominant_options,
        "dead_options": dead_options,
        "by_dimension": dim_summaries,
    }
