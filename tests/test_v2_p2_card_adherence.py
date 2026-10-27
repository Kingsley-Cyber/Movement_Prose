"""Phase P2 tests: slot pools, 2,000-fight active-slot traceability, leaky card rejection, triggers/abandon, conditional abilities."""

from __future__ import annotations

import copy
import itertools
from pathlib import Path

from engine.ontology import Knowledge
from engine.v2 import (
    list_archetypes_v2,
    load_card_v2,
    simulate_fight_v2,
    slot_pool_v2,
)
from engine.v2.availability import evaluate_conditional_abilities
from scripts.validate_v2_data import validate_card_slots

ROOT = Path(__file__).resolve().parent.parent


def test_p2_all_12_cards_pass_strict_slot_validation_and_leaky_card_rejected() -> None:
    k = Knowledge()
    for a in list_archetypes_v2(k):
        card = load_card_v2(k, a["fighter_id"])
        assert validate_card_slots(card, ROOT) == []

    # Deliberately leaky card: boxing slot trying to throw haymaker (untrained_striking) or outside_trip (judo)
    leaky = copy.deepcopy(load_card_v2(k, "detroit"))
    leaky["synchronized_capabilities"][0]["sequence"].append("haymaker")
    probs = validate_card_slots(leaky, ROOT)
    assert any("haymaker" in p and "not granted by the slot's capabilities" in p for p in probs)


def test_p2_2000_sampled_fights_100_percent_trace_to_active_slot_pool() -> None:
    k = Knowledge()
    arch_ids = sorted(a["fighter_id"] for a in list_archetypes_v2(k))
    cards = {fid: load_card_v2(k, fid) for fid in arch_ids}
    slot_caps_by_id: dict[str, dict[str, list[str]]] = {
        fid: {s["id"]: list(s["capabilities"]) for s in cards[fid]["synchronized_capabilities"]}
        for fid in arch_ids
    }

    # 66 pairs x 30 seeds + 20 boxing seeds = 2,000 fights
    pairs = list(itertools.combinations(arch_ids, 2))
    fight_count = 0
    total_exchanges = 0

    for a_id, b_id in pairs:
        for seed in range(1, 31):
            sim = simulate_fight_v2(cards[a_id], cards[b_id], ruleset="mma", duration_s=60.0, seed=seed, knowledge=k)
            fight_count += 1
            unlocked_map = {
                fid: tuple(sim["final_state_v2"]["actors"][fid].get("unlocked_abilities", ()))
                for fid in (a_id, b_id)
            }
            for ex in sim["exchanges"]:
                total_exchanges += 1
                att_id = ex["attacker_id"]
                slot_id = ex["active_slot_id"]
                tid = ex["technique_id"]
                s_caps = slot_caps_by_id[att_id][slot_id]
                pool = slot_pool_v2(k, cards[att_id], s_caps, "mma", unlocked_map[att_id])
                assert tid in pool, f"Fight {a_id} vs {b_id} seed {seed}: {att_id} in {slot_id} threw {tid} not in {pool}"

    for i in range(20):
        a_id, b_id = pairs[i % len(pairs)]
        sim = simulate_fight_v2(cards[a_id], cards[b_id], ruleset="boxing", duration_s=60.0, seed=100 + i, knowledge=k)
        fight_count += 1
        for ex in sim["exchanges"]:
            total_exchanges += 1
            att_id = ex["attacker_id"]
            slot_id = ex["active_slot_id"]
            tid = ex["technique_id"]
            s_caps = slot_caps_by_id[att_id][slot_id]
            pool = slot_pool_v2(k, cards[att_id], s_caps, "boxing")
            assert tid in pool

    assert fight_count == 2000
    assert total_exchanges > 10000


def test_p2_maleek_cage_plum_conditional_ability_unlocks_from_real_state() -> None:
    k = Knowledge()
    maleek = load_card_v2(k, "maleek")
    base_pool = slot_pool_v2(k, maleek, ["boxing", "shield"], "mma")
    assert "cage_plum" not in base_pool

    actor_st = {"wall_proximity": "near", "setups": ["shield_frame"], "unlocked_abilities": []}
    opp_st = {"wall_proximity": "near"}
    newly = evaluate_conditional_abilities(maleek, actor_st, opp_st, "clinch")
    assert newly == ["maleek.cage_plum"]
    unlocked_pool = slot_pool_v2(k, maleek, ["boxing", "shield"], "mma", actor_st["unlocked_abilities"])
    assert "cage_plum" in unlocked_pool
    assert "knee_body" in unlocked_pool
