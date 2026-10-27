"""Phase P3 verification tests: weighted seeded selection, diversity floor, combos, and contested defenses."""

from __future__ import annotations

from engine.ontology import Knowledge
from engine.v2.cards import list_archetypes_v2, load_card_v2
from engine.v2.defense import compute_kick_defense_window
from engine.v2.exchange import simulate_fight_v2


def test_p3_kick_defense_window_additive():
    # sanda (+0.08) + parry_catch (+0.08) + base (0.08) = 0.24
    c_sanda_parry = {"dimensions": {"kicking": "kicking.sanda", "defense": "defense.parry_catch"}}
    assert round(compute_kick_defense_window(c_sanda_parry), 4) == 0.24

    # sanda alone = 0.16, check_frame alone = 0.16, parry_catch alone = 0.16
    assert round(compute_kick_defense_window({"dimensions": {"kicking": "kicking.sanda"}}), 4) == 0.16
    assert round(compute_kick_defense_window({"dimensions": {"defense": "defense.check_frame"}}), 4) == 0.16
    assert round(compute_kick_defense_window({"dimensions": {"defense": "defense.parry_catch"}}), 4) == 0.16

    # Niran: check_frame (+0.08) + muay_thai (+0.04) + base (0.08) = 0.20
    c_niran = {"dimensions": {"defense": "defense.check_frame", "kicking": "kicking.muay_thai"}}
    assert round(compute_kick_defense_window(c_niran), 4) == 0.20

    # outfight: 0.16 far from wall, 0.08 near wall
    c_out = {"dimensions": {"defense": "defense.outfight"}}
    assert round(compute_kick_defense_window(c_out, wall_proximity="far"), 4) == 0.16
    assert round(compute_kick_defense_window(c_out, wall_proximity="near"), 4) == 0.08


def test_p3_diversity_floor_60_seeds():
    """§10.7 Diversity: distinct 5-move openings over 60 seeds >= 12 (brawler) / 25 (others)."""
    k = Knowledge()
    ids = [a["fighter_id"] for a in list_archetypes_v2(k)]
    cards = {fid: load_card_v2(k, fid) for fid in ids}

    for fid in ids:
        opp_list = [o for o in ids if o != fid]
        openings: set[tuple[str, ...]] = set()
        for s in range(1, 61):
            opp_id = opp_list[(s - 1) % len(opp_list)]
            res = simulate_fight_v2(cards[fid], cards[opp_id], seed=s, duration_s=120.0, knowledge=k)
            own_moves = tuple(
                ex["technique_id"] for ex in res["exchanges"] if ex["attacker_id"] == fid
            )[:5]
            openings.add(own_moves)
        threshold = 12 if fid == "street" else 25
        assert len(openings) >= threshold, (
            f"Archetype {fid} produced only {len(openings)} distinct 5-move openings over 60 seeds "
            f"(required >= {threshold})"
        )


def test_p3_contested_defenses_combos_and_counters():
    """Verify every defense outcome has a recorded roll/p_success, combos fire, and counter-only moves are counter-exclusive."""
    k = Knowledge()
    ids = [a["fighter_id"] for a in list_archetypes_v2(k)]
    cards = {fid: load_card_v2(k, fid) for fid in ids}

    counter_only_ids = {"check_hook", "pull_counter", "shield_counter_hook"}
    defense_outcomes = {"evaded", "blocked", "checked", "caught", "jammed"}

    total_defenses = 0
    combos_fired = 0
    counters_fired = 0
    counter_only_fired = 0

    for i, a in enumerate(ids):
        for b in ids[i + 1 :]:
            for s in (1, 2):
                res = simulate_fight_v2(cards[a], cards[b], seed=s, knowledge=k)
                for ex in res["exchanges"]:
                    # Counter-only moves must never be chosen as primary attacks
                    assert ex["technique_id"] not in counter_only_ids
                    assert ex.get("selection") is not None
                    assert ex["selection"]["chosen"] == ex["technique_id"]
                    assert ex["selection"]["granting_capability"]

                    if ex.get("combo_id"):
                        combos_fired += 1

                    if ex["outcome"] in defense_outcomes:
                        total_defenses += 1
                        def_rec = ex.get("defense")
                        assert def_rec is not None, f"Missing defense record on {ex['outcome']} in {a} vs {b}"
                        assert 0.0 <= float(def_rec["roll"]) <= 1.0
                        assert 0.05 <= float(def_rec["p_success"]) <= 0.95
                        assert def_rec["granting_capability"]

                    cf = ex.get("counter_followup")
                    if cf:
                        counters_fired += 1
                        if cf["technique_id"] in counter_only_ids:
                            counter_only_fired += 1

    assert total_defenses > 200
    assert combos_fired > 20
    assert counters_fired > 20
    assert counter_only_fired > 0
