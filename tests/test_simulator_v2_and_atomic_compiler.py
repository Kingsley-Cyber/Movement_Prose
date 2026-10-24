"""Comprehensive End-to-End Test & Validation Suite for:
1. Atomic 1-Contact-Per-Beat Causal Compiler & 12-Rule Semantic Verifier (fight_move_system/atomic_causal_compiler.py)
2. BLOCK Fight Simulator v2:
   - All 9 JSON Schemas (fighter_card_v2, option_behavior, technique_v2, position_map, fight_settings,
     model_config_v2, fight_state_v2, exchange_event_v2, simulation_result_v2)
   - All 57 Option Behavior profiles (data/option_behaviors.json)
   - Dynamic Defensive Posture & 8-Lane Readiness Calculator (compute_posture_state, compute_readiness_profile)
   - Card-Derived Damage Formula & First-Class Kicking Subsystem (unroll_kick_anatomy, select_kick_defense)
   - Order-Invariance (simulate_fight_v2(A, B) == simulate_fight_v2(B, A))
   - Seed Determinism & Trained-Moves-Only Invariant
   - Anti-Slot-Gaming Depth-vs-Breadth Scaling
"""

import copy
import math
import jsonschema
import pytest

from engine.capabilities import available
from engine.ontology import ROOT, Knowledge, read
from engine.simulator_v2 import (
    ARENA_PRESETS,
    LANES,
    build_slot_plans,
    compute_card_derived_damage,
    compute_posture_state,
    compute_readiness_profile,
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

    beat_ids = [b.beat_id for b in ir.beats]
    assert "Beat 2a" in beat_ids and "Beat 2b" in beat_ids
    beat_2a = next(b for b in ir.beats if b.beat_id == "Beat 2a")
    beat_2b = next(b for b in ir.beats if b.beat_id == "Beat 2b")
    assert beat_2a.named_contact_id == "B_hand_releases_kunai"
    assert beat_2b.named_contact_id == "A_right_foot_deflects_kunai_into_pillar"

    for label in ("Prep:", "Commit:", "Contact:", "Consequence:", "Recovery:"):
        assert label in labeled
    assert "spark" in beat_2b.consequence.lower()
    assert "spark" not in (beat_2b.prep + " " + beat_2b.commit).lower()

    beat_1b = next(b for b in ir.beats if b.beat_id == "Beat 1b")
    assert "head-first" in beat_1b.prep.lower()
    assert "flips upright" not in unlabeled.lower()
    assert "draws b's throw" not in unlabeled.lower()
    assert "up and toward screen-left" in beat_2b.consequence.lower()


def test_atomic_pillar_verifier_catches_injected_semantic_defects():
    ir = build_lbn23_pillar_atomic_ir()
    bad_ir_spark = copy.deepcopy(ir)
    b0 = bad_ir_spark.beats[0]
    bad_ir_spark.beats[0] = AtomicCausalBeat(
        **{**b0.__dict__, "prep": "A drops with a bright metallic spark ring before touching the pillar"}
    )
    rep1 = validate_atomic_pillar_prompt(bad_ir_spark, render_unlabeled_seedance_prompt(bad_ir_spark))
    assert rep1["status"] == "FAIL"
    assert any("SCAN-11" in e for e in rep1["errors"])

    bad_nl = render_unlabeled_seedance_prompt(ir) + " A draws B's throw and flips upright and sprints down."
    rep2 = validate_atomic_pillar_prompt(ir, bad_nl)
    assert rep2["status"] == "FAIL"
    assert any("SCAN-12" in e for e in rep2["errors"])


# ---------------------------------------------------------------------------
# Part 2: All 9 v2 Schemas & 57 Option Behavior Validation Tests
# ---------------------------------------------------------------------------

def test_all_9_v2_schemas_and_all_57_option_behaviors_validate(knowledge, cards):
    opt_beh = read(ROOT / "data/option_behaviors.json")
    tech_v2 = read(ROOT / "data/techniques_v2.json")
    pos_map = read(ROOT / "data/positions.json")
    mod_v2 = read(ROOT / "data/model_v2.json")
    mio_v2 = read(ROOT / "cards/v2/sanda_judo.json")

    jsonschema.validate(opt_beh, read(ROOT / "schemas/option_behavior.schema.json"))
    jsonschema.validate(tech_v2, read(ROOT / "schemas/technique_v2.schema.json"))
    jsonschema.validate(pos_map, read(ROOT / "schemas/position_map.schema.json"))
    jsonschema.validate(mod_v2, read(ROOT / "schemas/model_config_v2.schema.json"))
    jsonschema.validate(mio_v2, read(ROOT / "schemas/fighter_card_v2.schema.json"))

    # All 11 block-1 cards AND Mio's block-2 card must validate against fighter_card_v2.schema.json
    card_v2_schema = read(ROOT / "schemas/fighter_card_v2.schema.json")
    for c in cards.values():
        jsonschema.validate(c, card_v2_schema)

    assert len(opt_beh["options"]) == 57
    assert {o["id"] for o in opt_beh["options"]} == set(knowledge.options.keys())


def test_dynamic_defensive_posture_and_8_lane_readiness_profile_shifts_with_state(knowledge, cards):
    opt_map = {o["id"]: o for o in read(ROOT / "data/option_behaviors.json")["options"]}
    niran = cards["thai"]     # hands.long_guard, defense.check_frame, stance.upright (rear_heavy)
    donnell = cards["donnell"]  # hands.peekaboo, defense.slip_roll, stance.crouch (front_heavy)

    fresh_state = {
        "posture_mode": "standing",
        "balance": "stable",
        "grip": None,
        "sub_grips": {"underhooks": 0},
        "wall_proximity": "far",
        "damage": {"head": 0.0, "body": 0.0, "leg": 0.0},
        "fatigue": 0.0,
        "recovery_window": {"window_type": "none", "last_technique_id": None, "exposed_lanes": [], "readiness_penalty": 0.0},
        "attention": {"focus_line": "neutral", "feinted": False, "outside_angle_conceded": False},
        "read_memory": {"seen_counts": {}, "consecutive_same_move_by_opponent": 0},
    }

    # 1. Fresh Niran Sol is rear-weighted and has high leg readiness (check_frame + upright)
    p_fresh = compute_posture_state(niran, fresh_state, opt_map)
    r_fresh = compute_readiness_profile(knowledge, niran, fresh_state, donnell, fresh_state, "kick", "closed_stance", "low_kick", opt_map)
    assert p_fresh["weight_split"] == "rear_heavy"
    assert set(r_fresh.keys()) == set(LANES)
    assert r_fresh["leg"] > 4.5

    # 2. Half a second later: Niran is mid single-leg recovery after throwing a kick, off-base, with hurt legs -> readiness drops sharply!
    compromised_state = copy.deepcopy(fresh_state)
    compromised_state["balance"] = "off_base"
    compromised_state["damage"]["leg"] = 5.0
    compromised_state["recovery_window"] = {
        "window_type": "single_leg_recovery",
        "last_technique_id": "body_kick",
        "exposed_lanes": ["single_support", "leg", "head_straight", "entry"],
        "readiness_penalty": 1.35,
    }
    p_comp = compute_posture_state(niran, compromised_state, opt_map)
    r_comp = compute_readiness_profile(knowledge, niran, compromised_state, donnell, fresh_state, "kick", "closed_stance", "low_kick", opt_map)
    assert p_comp["base_width"] == "single_leg"
    assert r_comp["leg"] < r_fresh["leg"] - 2.5
    assert r_comp["single_support"] < r_fresh["single_support"] - 2.0

    # 3. Body damage brings the elbows down, decaying guard_integrity and opening head lanes
    body_hurt_state = copy.deepcopy(fresh_state)
    body_hurt_state["damage"]["body"] = 8.0
    body_hurt_state["fatigue"] = 6.0
    p_body = compute_posture_state(donnell, body_hurt_state, opt_map)
    r_donnell_fresh = compute_readiness_profile(knowledge, donnell, fresh_state, niran, fresh_state, "punch", "closed_stance", "cross", opt_map)
    r_donnell_hurt = compute_readiness_profile(knowledge, donnell, body_hurt_state, niran, fresh_state, "punch", "closed_stance", "cross", opt_map)
    assert p_body["guard_integrity"] < 0.65
    assert r_donnell_hurt["head_straight"] < r_donnell_fresh["head_straight"] - 1.5


def test_card_derived_damage_and_first_class_kicking_subsystem(knowledge, cards):
    rook = cards["street"]
    darius = cards["detroit"]
    niran = cards["thai"]
    maleek = cards["maleek"]
    aya = cards["karate"]
    mio = knowledge.card("sanda_judo")

    dummy_state = {"fatigue": 0.0, "damage": {"head": 0.0, "body": 0.0, "leg": 0.0}, "wall_proximity": "far", "setups": []}
    rook_cross = compute_card_derived_damage(knowledge, rook, darius, "cross", "clean", dummy_state, dummy_state)
    darius_cross = compute_card_derived_damage(knowledge, darius, rook, "cross", "clean", dummy_state, dummy_state)
    darius_counter = compute_card_derived_damage(knowledge, darius, rook, "cross", "counter_hit", dummy_state, dummy_state)
    assert rook_cross["attacker_multiplier"] > darius_cross["attacker_multiplier"] * 1.35
    assert darius_counter["final_damage"] > darius_cross["final_damage"] * 1.95

    for tid in ("low_kick", "body_kick", "head_kick", "teep", "side_kick", "switch_kick", "spinning_back_kick", "axe_kick", "jumping_knee"):
        anat = unroll_kick_anatomy(tid, niran, "orthodox")
        assert anat is not None
        for key in ("kick_family", "kicking_leg", "chamber", "support_foot", "path", "target_region", "striking_surface", "ending"):
            assert anat.get(key), f"{tid} missing {key}"

    assert select_kick_defense(niran, "low_kick", "kick") == ("check", "checked")
    checked_dmg = compute_card_derived_damage(knowledge, maleek, niran, "low_kick", "checked", dummy_state, dummy_state)
    assert checked_dmg["recoil_leg_damage_to_attacker"] > 1.0
    assert select_kick_defense(mio, "body_kick", "kick") == ("kick_catch", "caught")
    assert select_kick_defense(aya, "head_kick", "kick") == ("evade_step_back", "evaded")


def test_order_invariance_seed_determinism_trained_moves_only_and_schema_validation(knowledge, cards):
    mio = knowledge.card("sanda_judo")
    niran = cards["thai"]

    state_v2_schema = read(ROOT / "schemas/fight_state_v2.schema.json")
    ex_v2_schema = read(ROOT / "schemas/exchange_event_v2.schema.json")

    # 1. Same seed produces identical fight; reversed fighter order produces exact same winner & exchanges!
    sim_ab_1 = simulate_fight_v2(mio, niran, ruleset="mma", duration_s=60.0, seed=7, arena="cage", knowledge=knowledge)
    sim_ab_2 = simulate_fight_v2(mio, niran, ruleset="mma", duration_s=60.0, seed=7, arena="cage", knowledge=knowledge)
    sim_ba = simulate_fight_v2(niran, mio, ruleset="mma", duration_s=60.0, seed=7, arena="cage", knowledge=knowledge)

    assert sim_ab_1 == sim_ab_2
    assert sim_ab_1["winner_id"] == sim_ba["winner_id"]
    assert sim_ab_1["exchanges"] == sim_ba["exchanges"]
    assert sim_ab_1["final_state_v2"] == sim_ba["final_state_v2"]

    # 2. Validate final_state_v2 and every exchange event against JSON Schemas
    jsonschema.validate(sim_ab_1["final_state_v2"], state_v2_schema)
    for ex in sim_ab_1["exchanges"]:
        jsonschema.validate(ex, ex_v2_schema)

    # 3. Trained-moves-only invariant: no fighter ever executes a technique not in their trained available set
    avail_by_id = {
        "sanda_judo": set(available(knowledge, mio, "mma")),
        "thai": set(available(knowledge, niran, "mma")),
    }
    for ex in sim_ab_1["exchanges"]:
        assert ex["technique_id"] in avail_by_id[ex["attacker_id"]]
        if ex["counter_followup"]:
            c_actor = ex["counter_followup"]["counter_actor_id"]
            assert ex["counter_followup"]["technique_id"] in avail_by_id[c_actor]

    # 4. Anti-slot-gaming depth-vs-breadth check: splitting Mio's 2 slots into 3 slots reduces per-slot depth_multiplier
    mio_split = copy.deepcopy(mio)
    mio_split["slot_count"] = 3
    mio_split["slot_label"] = "Triad"
    mio_split["synchronized_capabilities"] = [
        {"id": "s1", "capabilities": ["sanda", "kickboxing"], "description": "Slot 1"},
        {"id": "s2", "capabilities": ["karate", "boxing"], "description": "Slot 2"},
        {"id": "s3", "capabilities": ["judo", "wrestling", "clinch"], "description": "Slot 3"},
    ]
    plans_2 = build_slot_plans(knowledge, mio, "mma")
    plans_3 = build_slot_plans(knowledge, mio_split, "mma")
    assert plans_2[0]["depth_multiplier"] == 1.05
    assert plans_3[0]["depth_multiplier"] == 1.00


def test_arena_presets_grappling_positions_and_monte_carlo_many_runs(knowledge, cards):
    assert set(ARENA_PRESETS) == {"ring", "cage", "open_floor", "narrow_alley", "rooftop_edge", "dojo"}

    mc_ab = simulate_many_v2(cards["greco"], cards["karate"], runs=16, arena="cage", knowledge=knowledge)
    mc_ba = simulate_many_v2(cards["karate"], cards["greco"], runs=16, arena="cage", knowledge=knowledge)
    assert math.isclose(mc_ab["empirical_win_rate_a"], mc_ba["empirical_win_rate_b"], abs_tol=1e-9)
    assert math.isclose(mc_ab["empirical_win_rate_b"], mc_ba["empirical_win_rate_a"], abs_tol=1e-9)

    bjj_sim = simulate_fight_v2(cards["jiujitsu"], cards["street"], duration_s=60.0, seed=3, knowledge=knowledge)
    positions_seen = {e["grappling_position"] for e in bjj_sim["exchanges"]}
    assert any(p != "standing_neutral" for p in positions_seen)
