"""Monte Carlo many-runs simulator, director mode, and atomic causal beat bridge for BLOCK Simulator v2."""

from __future__ import annotations

from typing import Any

from ..ontology import Knowledge
from .cards import load_card_v2
from .data import validate_schema_cached
from .exchange import simulate_fight_v2
from .vertical import normalize_vertical_mode


def simulate_many_v2(
    a: Any,
    b: Any,
    runs: int = 50,
    ruleset: str = "mma",
    duration_s: float = 60.0,
    arena: str = "cage",
    vertical_mode: str = "grounded",
    directed_winner: str | None = None,
    knowledge: Knowledge | None = None,
) -> dict[str, Any]:
    """Run N seeded v2 fights to compute empirical win rates, method breakdown, deciding slots/lanes,
    and realistic directed runs validated against simulation_result_v2.schema.json.
    """
    k = knowledge or Knowledge()
    card_a, card_b = load_card_v2(k, a), load_card_v2(k, b)
    id_a, id_b = card_a["fighter_id"], card_b["fighter_id"]
    vertical_mode = normalize_vertical_mode(vertical_mode)

    wins = {id_a: 0, id_b: 0}
    methods: dict[str, int] = {}
    deciding_slots: dict[str, int] = {}
    deciding_lanes: dict[str, int] = {}
    matching_runs: list[dict[str, Any]] = []
    all_runs: list[dict[str, Any]] = []
    total_dur = 0.0

    for s in range(1, runs + 1):
        sim = simulate_fight_v2(
            card_a,
            card_b,
            ruleset=ruleset,
            duration_s=duration_s,
            seed=s,
            arena=arena,
            vertical_mode=vertical_mode,
            knowledge=k,
        )
        w = str(sim["winner_id"])
        wins[w] += 1
        total_dur += float(sim["duration_actual_s"])
        m_key = str(sim["finish_reason"]).split(" (")[0]
        methods[m_key] = methods.get(m_key, 0) + 1
        if sim["exchanges"]:
            last_ex = sim["exchanges"][-1]
            s_id = str(last_ex["active_slot_id"])
            l_id = str(last_ex["attack_lane"])
            deciding_slots[s_id] = deciding_slots.get(s_id, 0) + 1
            deciding_lanes[l_id] = deciding_lanes.get(l_id, 0) + 1
        all_runs.append(sim)
        if directed_winner and w == directed_winner:
            matching_runs.append(sim)

    selected_run = matching_runs[0] if matching_runs else all_runs[0]
    result = {
        "version": "block-2",
        "fighter_a": id_a,
        "fighter_b": id_b,
        "runs": runs,
        "ruleset": ruleset,
        "arena": arena,
        "vertical_mode": vertical_mode,
        "win_counts": wins,
        "empirical_win_rate_a": round(wins[id_a] / runs, 3),
        "empirical_win_rate_b": round(wins[id_b] / runs, 3),
        "method_breakdown": methods,
        "average_duration_s": round(total_dur / runs, 2),
        "deciding_slots": deciding_slots,
        "deciding_weakness_lanes": deciding_lanes,
        "directed_winner": directed_winner,
        "representative_fight": selected_run,
    }
    validate_schema_cached(result, k.root / "schemas" / "simulation_result_v2.schema.json")
    return result


def compile_simulated_fight_to_atomic_beats(
    sim_result: dict[str, Any],
    max_beats: int = 6,
) -> dict[str, Any]:
    """Translate the key exchanges of a `simulate_fight_v2` result into 1-Contact-Per-Beat
    `AtomicCausalBeat` blocks (`Prep -> Commit -> Contact -> Consequence -> Recovery`)
    plus single-sentence unlabeled natural-language prose.
    """
    from fight_move_system.atomic_causal_compiler import AtomicCausalBeat

    exchanges = list(sim_result.get("exchanges", []))
    actors_final = sim_result.get("actors_final", {})
    names = {fid: str(info.get("name", fid)) for fid, info in actors_final.items()}

    if len(exchanges) <= max_beats:
        selected = exchanges
    else:
        scored = sorted(
            exchanges[1:-1],
            key=lambda e: (
                1 if e.get("counter_followup") else 0,
                1 if e.get("outcome") in ("flush", "clean", "caught", "checked") else 0,
                float(e.get("damage", {}).get("final_damage", 0.0)),
            ),
            reverse=True,
        )[: max(0, max_beats - 2)]
        chosen_indices = {exchanges[0]["exchange_index"], exchanges[-1]["exchange_index"]} | {
            e["exchange_index"] for e in scored
        }
        selected = [e for e in exchanges if e["exchange_index"] in chosen_indices][:max_beats]

    beats: list[AtomicCausalBeat] = []
    for idx, ex in enumerate(selected, start=1):
        att_id = str(ex["attacker_id"])
        def_id = str(ex["defender_id"])
        att_name = names.get(att_id, att_id)
        def_name = names.get(def_id, def_id)
        tid = str(ex["technique_id"])
        outcome = str(ex["outcome"])
        posture = ex["defender_posture_before"]
        kick = ex.get("kick_anatomy")
        dmg = ex["damage"]
        counter = ex.get("counter_followup")
        pos_after = str(ex["grappling_position"])

        prep = (
            f"At {ex['range']} range ({ex['lead_foot_matchup']}), {def_name} holds {posture['guard_id']} "
            f"with {posture['weight_split']} weight and {posture['head_position']} head alignment "
            f"(lane {ex['attack_lane']} readiness {ex['lane_readiness_score']:.2f})"
        )
        if kick:
            commit = (
                f"{att_name} executes `{tid}` from `{ex['active_slot_id']}` using `{kick['kicking_leg']}` "
                f"({kick['chamber']} chamber, {kick['support_foot']} support pivot, {kick['path']} path)"
            )
            surface = kick["striking_surface"]
        else:
            commit = f"{att_name} initiates `{tid}` from `{ex['active_slot_id']}` along the `{ex['attack_lane']}` lane"
            surface = "striking limb"

        if outcome in ("clean", "flush", "partial"):
            contact = (
                f"{att_name}'s {surface} lands `{outcome}` on {def_name}'s {dmg['target_region']} "
                f"(card-derived damage {dmg['final_damage']:.2f})"
            )
            consequence = (
                f"From that impact, {def_name}'s balance shifts to `{ex['state_changes']['defender_balance']}` "
                f"in `{pos_after}` position"
            )
        elif outcome == "checked":
            contact = (
                f"{def_name} raises a hard shin block (`{ex['defense_used']}`) that meets {att_name}'s kicking shin on contact"
            )
            consequence = (
                f"From the shin-on-shin collision, {att_name} absorbs {dmg['recoil_leg_damage_to_attacker']:.2f} "
                f"recoil leg damage and stumbles onto compromised support"
            )
        elif outcome == "caught" and counter:
            contact = (
                f"{def_name} traps {att_name}'s kicking leg with `{ex['defense_used']}` and immediately sweeps the standing support "
                f"with `{counter['technique_id']}`"
            )
            consequence = (
                f"From the caught-kick dump, {att_name} crashes to the mat for {counter['damage']['final_damage']:.2f} "
                f"counter damage into `{pos_after}`"
            )
        elif counter:
            contact = (
                f"{def_name} uses `{ex['defense_used']}` to clear `{tid}` and fires an immediate counter `{counter['technique_id']}` "
                f"to {att_name}'s {counter['damage']['target_region']}"
            )
            consequence = (
                f"From the counter strike, {att_name} takes {counter['damage']['final_damage']:.2f} damage "
                f"while {def_name} takes the angle"
            )
        else:
            contact = f"{def_name} neutralizes `{tid}` with `{ex['defense_used'] or outcome}` across the `{ex['attack_lane']}` lane"
            consequence = f"With the attack denied, {def_name} preserves `{ex['state_changes']['defender_balance']}` balance"

        rec_win = ex["state_changes"]["attacker_recovery_window"]
        slot_note = f" and switches gameplan to `{ex['slot_switched_to']}`" if ex.get("slot_switched_to") else ""
        recovery = (
            f"{att_name} retracts through `{rec_win}` recovery{slot_note} while {def_name} resets guard in `{pos_after}`"
        )

        beats.append(
            AtomicCausalBeat(
                beat_id=f"BEAT_{idx:02d}",
                title=f"{ex['t_start']:.2f}s-{ex['t_end']:.2f}s | {att_name} `{tid}` -> {outcome.upper()}",
                named_contact_id=f"ex_{ex['exchange_index']}_{tid}_{outcome}",
                view="locked 180-degree full-body profile framing",
                prep=prep,
                commit=commit,
                contact=contact,
                consequence=consequence,
                recovery=recovery,
                license="1-frame contact accent on primary collision only",
                a_support_after="mat" if pos_after in ("side_control", "half_guard_top", "closed_guard_bottom", "mount_or_back_ride") else "two_feet",
                b_support_after="mat" if pos_after in ("side_control", "half_guard_top", "closed_guard_bottom", "mount_or_back_ride") else "two_feet",
            )
        )

    return {
        "beat_count": len(beats),
        "labeled_ir": "\n\n".join(b.render_labeled_block() for b in beats),
        "unlabeled_prose": "\n\n".join(b.render_unlabeled_seedance_sentence() for b in beats),
        "beats": [
            {
                "beat_id": b.beat_id,
                "title": b.title,
                "labeled_ir": b.render_labeled_block(),
                "unlabeled_prose": b.render_unlabeled_seedance_sentence(),
            }
            for b in beats
        ],
    }
