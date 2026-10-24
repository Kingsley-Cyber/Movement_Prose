"""Tests and validation suite for:
1. Atomic 1-Contact-Per-Beat Causal Compiler & 12-Rule Semantic Verifier (fight_move_system/atomic_causal_compiler.py)
2. BLOCK Fight Simulator v2: Card-Derived Damage, First-Class Kicking, Grappling Positions, Slot Gameplans,
   Fight Clock, Arena Presets, and Mio Tsukihara Sanda/Judo card (engine/simulator_v2.py, cards/v2/sanda_judo.json).
"""

import copy
import math
import pytest

from engine.ontology import Knowledge
from engine.simulator_v2 import (
    ARENA_PRESETS,
    build_slot_plans,
    compute_card_derived_damage,
    select_kick_defense,
    simulate_fight_v2,
    simulate_many_v2,
    unroll_kick_anatomy,
)
from fight_move_system.atomic_causal_compiler import (
    AtomicCausalBeat,
    build_lbn23_pillar_atomic_ir,
    compile_and_write_pillar_prompts,
    render_labeled_atomic_prompt,
    render_unlabeled_seedance_prompt,
    validate_atomic_pillar_prompt,
)


# ---------------------------------------------------------------------------
# Part 1: Atomic 1-Contact-Per-Beat Pillar Fight Compiler & Verifier Tests
# ---------------------------------------------------------------------------

def test_atomic_pillar_compiler_passes_all_12_scan_rules_and_fixes_all_5_user_critiques():
    result = compile_and_write_pillar_prompts()
    report = result["report"]
    assert report["status"] == "PASS", report["errors"]
    assert report["atomic_beat_count"] == 14
    assert report["tracked_prop_count"] == 6

    ir = build_lbn23_pillar_atomic_ir()
    labeled = render_labeled_atomic_prompt(ir)
    unlabeled = render_unlabeled_seedance_prompt(ir)

    # Critique 1: Beat 2 is split into single-contact atomic beats (Beat 2a: THROW, Beat 2b: FOOT DEFLECTION)
    beat_ids = [b.beat_id for b in ir.beats]
    assert "Beat 2a" in beat_ids and "Beat 2b" in beat_ids
    beat_2a = next(b for b in ir.beats if b.beat_id == "Beat 2a")
    beat_2b = next(b for b in ir.beats if b.beat_id == "Beat 2b")
    assert beat_2a.named_contact_id == "B_hand_releases_kunai"
    assert beat_2b.named_contact_id == "A_right_foot_deflects_kunai_into_pillar"

    # Critique 2: Steps are explicitly labeled in the IR & labeled prompt so checker verifies spark-after-contact
    for label in ("Prep:", "Commit:", "Contact:", "Consequence:", "Recovery:"):
        assert label in labeled
    assert "spark" in beat_2b.consequence.lower()
    assert "spark" not in (beat_2b.prep + " " + beat_2b.commit).lower()

    # Critique 3: Beat 1 orientation physics (head-first pitch when sprinting down vertical pillar)
    beat_1b = next(b for b in ir.beats if b.beat_id == "Beat 1b")
    assert "head-first" in beat_1b.prep.lower()
    assert "flips upright" not in unlabeled.lower()

    # Critique 4: No ambiguous "A draws B's throw"
    assert "draws b's throw" not in unlabeled.lower()
    assert "seeing a dive downward and rightward from the stone pillar" in beat_2a.prep.lower()

    # Critique 5: Deflection direction defined in explicit screen terms ("up and toward screen-left")
    assert "up and toward screen-left" in beat_2b.consequence.lower()


def test_atomic_pillar_verifier_catches_injected_semantic_defects():
    ir = build_lbn23_pillar_atomic_ir()

    # 1. Inject spark into Prep before Contact -> must fail SCAN-11
    bad_ir_spark = copy.deepcopy(ir)
    b0 = bad_ir_spark.beats[0]
    bad_ir_spark.beats[0] = AtomicCausalBeat(
        **{**b0.__dict__, "prep": "A drops with a bright metallic spark ring before touching the pillar"}
    )
    rep1 = validate_atomic_pillar_prompt(bad_ir_spark, render_unlabeled_seedance_prompt(bad_ir_spark))
    assert rep1["status"] == "FAIL"
    assert any("SCAN-11" in e for e in rep1["errors"])

    # 2. Inject "draws B's throw" or "flips upright... and sprints straight down" -> must fail SCAN-12
    bad_nl = render_unlabeled_seedance_prompt(ir) + " A draws B's throw and flips upright and sprints down."
    rep2 = validate_atomic_pillar_prompt(ir, bad_nl)
    assert rep2["status"] == "FAIL"
    assert any("SCAN-12" in e for e in rep2["errors"])


# ---------------------------------------------------------------------------
# Part 2: BLOCK Fight Simulator v2 Tests & Validation
# ---------------------------------------------------------------------------

def test_card_derived_damage_differentiates_slugger_vs_counter_puncher(knowledge, cards):
    rook = cards["street"]     # 1-slot Brawler, mentality.slugger, stance.planted, target.head_hunter
    darius = cards["detroit"]  # 2-slot Two-piece, mentality.counter, stance.bladed, hands.kronk

    dummy_state = {"fatigue": 0.0, "damage": {"head": 0.0, "body": 0.0, "leg": 0.0}, "wall_proximity": "far", "setups": []}

    # Clean rear cross/haymaker: Rook Mercer hits much harder on base clean strikes than Darius Reed
    rook_cross = compute_card_derived_damage(knowledge, rook, darius, "cross", "clean", dummy_state, dummy_state)
    darius_cross = compute_card_derived_damage(knowledge, darius, rook, "cross", "clean", dummy_state, dummy_state)
    assert rook_cross["attacker_multiplier"] > darius_cross["attacker_multiplier"] * 1.35
    assert rook_cross["final_damage"] > darius_cross["final_damage"]

    # Counter-hit: Darius Reed gets a massive counter surge (1.45x mentality * 1.40x counter_hit landing)
    darius_counter = compute_card_derived_damage(knowledge, darius, rook, "cross", "counter_hit", dummy_state, dummy_state)
    assert darius_counter["final_damage"] > darius_cross["final_damage"] * 1.95


def test_first_class_kicking_subsystem_anatomy_checks_and_sanda_kick_catch(knowledge, cards):
    niran = cards["thai"]                  # kicking.muay_thai, defense.check_frame
    maleek = cards["maleek"]               # kicking.dutch, defense.check_frame
    aya = cards["karate"]                  # kicking.karate, defense.outfight
    mio = knowledge.card("sanda_judo")     # kicking.sanda, defense.parry_catch, tie.judo_sambo

    # 1. Every kick unrolls all 6 anatomical dimensions
    for tid in ("low_kick", "body_kick", "head_kick", "teep", "side_kick", "switch_kick", "spinning_back_kick", "axe_kick", "jumping_knee"):
        anat = unroll_kick_anatomy(tid, niran, "orthodox")
        assert anat is not None
        for key in ("kick_family", "kicking_leg", "chamber", "support_foot", "path", "target_region", "striking_surface", "ending"):
            assert anat.get(key), f"{tid} missing {key}"

    # 2. Shin check reflects recoil leg damage back onto the kicker!
    st_att = {"fatigue": 0.0, "damage": {"head": 0.0, "body": 0.0, "leg": 0.0}, "wall_proximity": "far", "setups": []}
    st_def = {"fatigue": 0.0, "damage": {"head": 0.0, "body": 0.0, "leg": 0.0}, "wall_proximity": "far", "setups": []}
    def_act, def_out = select_kick_defense(niran, "low_kick", "kick")
    assert (def_act, def_out) == ("check", "checked")
    checked_dmg = compute_card_derived_damage(knowledge, maleek, niran, "low_kick", "checked", st_att, st_def)
    assert checked_dmg["recoil_leg_damage_to_attacker"] > 1.0
    assert checked_dmg["final_damage"] < checked_dmg["recoil_leg_damage_to_attacker"]

    # 3. Mio Tsukihara (kicking.sanda) catches body/low kicks and triggers a Sanda sweep dump!
    catch_act, catch_out = select_kick_defense(mio, "body_kick", "kick")
    assert (catch_act, catch_out) == ("kick_catch", "caught")

    # 4. Outfight (Aya Quinn) steps back to evade round kicks
    assert select_kick_defense(aya, "head_kick", "kick") == ("evade_step_back", "evaded")


def test_v2_simulation_adheres_to_cards_prevents_move_spam_and_switches_slots(knowledge, cards):
    mio = knowledge.card("sanda_judo")
    niran = cards["thai"]

    sim = simulate_fight_v2(mio, niran, ruleset="mma", duration_s=60.0, seed=7, arena="cage", knowledge=knowledge)
    assert sim["version"] == "block-v2"
    assert sim["exchange_count"] >= 6

    # Verify no fighter ever repeats the same move 4+ times consecutively (fixes the "12 body hooks" bug)
    for fid in ("sanda_judo", "thai"):
        fighter_moves = [e["technique_id"] for e in sim["exchanges"] if e["attacker_id"] == fid]
        assert len(set(fighter_moves)) >= 2
        max_streak = 1
        cur_streak = 1
        for prev_m, curr_m in zip(fighter_moves, fighter_moves[1:]):
            if curr_m == prev_m:
                cur_streak += 1
                max_streak = max(max_streak, cur_streak)
            else:
                cur_streak = 1
        assert max_streak <= 3, f"{fid} spammed move {max_streak} times in a row"

    # Verify kick anatomy and kick defenses appear in the exchange log
    kick_exchanges = [e for e in sim["exchanges"] if e["kick_anatomy"] is not None]
    assert len(kick_exchanges) >= 1
    assert any(e["outcome"] in ("caught", "checked") for e in kick_exchanges)


def test_arena_presets_grappling_positions_and_monte_carlo_many_runs(knowledge, cards):
    assert set(ARENA_PRESETS) == {"ring", "cage", "open_floor", "narrow_alley", "rooftop_edge", "dojo"}

    # Greco swarmer (Oren Pike) vs Outboxer (Aya Quinn) in cage vs open_floor
    mc_cage = simulate_many_v2(cards["greco"], cards["karate"], runs=20, arena="cage", knowledge=knowledge)
    mc_open = simulate_many_v2(cards["greco"], cards["karate"], runs=20, arena="open_floor", knowledge=knowledge)
    assert mc_cage["runs"] == 20
    assert math.isclose(mc_cage["empirical_win_rate_a"] + mc_cage["empirical_win_rate_b"], 1.0, abs_tol=1e-6)
    assert mc_open["representative_fight"]["arena"] == "open_floor"

    # BJJ specialist (Jo Costa) establishes ground / submission positions
    bjj_sim = simulate_fight_v2(cards["jiujitsu"], cards["street"], duration_s=60.0, seed=3, knowledge=knowledge)
    positions_seen = {e["grappling_position"] for e in bjj_sim["exchanges"]}
    assert any(p != "standing_neutral" for p in positions_seen)
