"""Phase P5 tests: ruleset legality (§10.9), clinch/ground rules, equipment, stop_hit, on_success_effects (§7.17), and edge falls."""

from __future__ import annotations

import copy
import random
from pathlib import Path

from engine.ontology import Knowledge
from engine.v2 import available_v2, compute_card_derived_damage, load_card_v2, simulate_fight_v2
from engine.v2.data import load_model_v2, load_option_behaviors, load_rulesets_v2, load_techniques_v2
from engine.v2.finishes import check_finish_conditions, resolve_standing_count_or_knockdown
from engine.v2.readiness import compute_readiness_profile
from engine.v2.state import apply_technique_effects, compute_posture_state, tick_active_effects

ROOT = Path(__file__).resolve().parent.parent


def test_p5_ruleset_legality_matrix_and_simulation_invariants() -> None:
    """Verify §10.9 legality rules across boxing, kickboxing, muay_thai, mma, street, and lethwei."""
    k = Knowledge()
    techs = load_techniques_v2(ROOT)
    cards = [load_card_v2(k, p) for p in sorted((ROOT / "cards" / "v2").glob("*.json"))]
    templates = [k.card(p) for p in sorted((ROOT / "handoff_seed" / "style_templates").glob("*.json"))]
    all_cards = cards + templates

    headbutt_ids = {"headbutt", "clinch_headbutt", "lunging_headbutt"}
    foul_strike_ids = {"finger_jab", "tiger_claw", "piercing_palm"}

    for c in all_cards:
        # Boxing: zero kicks, knees, elbows, grips, takedowns, sweeps, submissions, ground_strikes
        av_box = available_v2(k, c, "boxing")
        for tid in av_box:
            if tid == "clinch_break":
                continue
            assert techs[tid]["kind"] in ("movement", "feint", "punch", "defense"), f"Illegal in boxing: {tid}"

        # Kickboxing: zero elbows, takedowns, sweeps, clinch knees, submissions, ground_strikes
        av_kb = available_v2(k, c, "kickboxing")
        assert "knee_head_clinch" not in av_kb
        for tid in av_kb:
            if tid == "clinch_break":
                continue
            assert techs[tid]["kind"] in ("movement", "feint", "punch", "kick", "knee", "defense", "grip"), (
                f"Illegal in kickboxing: {tid}"
            )

        # Muay Thai & Lethwei: zero ground strikes or submissions
        for rs in ("muay_thai", "lethwei"):
            av_rs = available_v2(k, c, rs)
            for tid in av_rs:
                assert techs[tid]["kind"] not in ("ground_strike", "submission", "control"), (
                    f"Illegal ground technique in {rs}: {tid}"
                )

        # MMA: zero headbutts, eye jabs, claws, throat strikes
        av_mma = available_v2(k, c, "mma")
        assert not (av_mma & headbutt_ids), f"Headbutts must be banned in MMA: {av_mma & headbutt_ids}"
        assert not (av_mma & foul_strike_ids), f"Foul strikes must be banned in MMA: {av_mma & foul_strike_ids}"

        # Headbutts only in lethwei and street; foul strikes only in street
        for rs in ("boxing", "kickboxing", "muay_thai", "mma"):
            assert not (available_v2(k, c, rs) & headbutt_ids)
        for rs in ("boxing", "kickboxing", "muay_thai", "mma", "lethwei"):
            assert not (available_v2(k, c, rs) & foul_strike_ids)

    # Simulate fights under boxing, kickboxing, muay_thai, lethwei, street and check runtime invariants
    mio = load_card_v2(k, "sanda_judo")
    niran = load_card_v2(k, "thai")
    bjj = load_card_v2(k, "jiujitsu")
    lethwei_tpl = k.card(ROOT / "handoff_seed" / "style_templates" / "tpl_lethwei.json")

    box_res = simulate_fight_v2(mio, niran, ruleset="boxing", duration_s=60.0, seed=11, arena="ring", knowledge=k)
    for ex in box_res["exchanges"]:
        tid = ex["technique_id"]
        assert techs[tid]["kind"] in ("movement", "feint", "punch", "defense") or tid == "clinch_break"
        assert ex["grappling_position"] == "standing_neutral"

    kb_res = simulate_fight_v2(mio, niran, ruleset="kickboxing", duration_s=60.0, seed=11, arena="ring", knowledge=k)
    for ex in kb_res["exchanges"]:
        tid = ex["technique_id"]
        assert tid != "knee_head_clinch"
        assert techs[tid]["kind"] not in ("elbow", "takedown", "sweep", "submission", "ground_strike")

    mt_res = simulate_fight_v2(mio, bjj, ruleset="muay_thai", duration_s=60.0, seed=11, arena="ring", knowledge=k)
    for ex in mt_res["exchanges"]:
        assert ex["range"] != "ground"
        assert ex["grappling_position"] not in ("closed_guard_bottom", "half_guard_top", "side_control", "mount_or_back_ride")

    lw_res = simulate_fight_v2(lethwei_tpl, niran, ruleset="lethwei", duration_s=60.0, seed=11, arena="ring", knowledge=k)
    for ex in lw_res["exchanges"]:
        assert ex["range"] != "ground"


def test_p5_bare_knuckle_equipment_and_on_success_effects() -> None:
    """Verify bare-knuckle punch multiplier (street/lethwei) and §7.17 on_success_effects interpreter."""
    k = Knowledge()
    rulesets = load_rulesets_v2(ROOT)["rulesets"]
    model_cfg = load_model_v2(ROOT)
    beh = load_option_behaviors(ROOT)
    techs = load_techniques_v2(ROOT)

    darius = load_card_v2(k, "detroit")
    rook = load_card_v2(k, "street")
    att_state = {"fatigue": 0.0, "damage": {"head": 0.0, "body": 0.0, "leg": 0.0}, "setups": [], "orientation": "orthodox"}
    def_state = {"fatigue": 0.0, "damage": {"head": 0.0, "body": 0.0, "leg": 0.0}, "wall_proximity": "far", "orientation": "orthodox"}

    dmg_mma = compute_card_derived_damage(
        k, darius, rook, "cross", "clean", att_state, def_state, equipment=rulesets["mma"]["equipment"]
    )
    dmg_street = compute_card_derived_damage(
        k, darius, rook, "cross", "clean", att_state, def_state, equipment=rulesets["street"]["equipment"]
    )
    assert round(dmg_street["final_damage"] / dmg_mma["final_damage"], 2) == 1.10

    # Test on_success_effects interpreter (§7.17): pak_sao (lane_penalty), finger_jab (vision), shove (push_back), negativa (low_posture)
    actors = {
        "detroit": copy.deepcopy(att_state),
        "street": copy.deepcopy(def_state),
    }
    cards = {"detroit": darius, "street": rook}
    rdy_before = compute_readiness_profile(
        k, rook, actors["street"], darius, actors["detroit"], "punch", "closed_stance", opt_behaviors=beh, model_cfg=model_cfg
    )

    applied_pak, r_after = apply_technique_effects(
        "pak_sao", techs["pak_sao"]["on_success_effects"], "detroit", "street", actors, cards, "punch", ["kick", "punch", "clinch"], rng=random.Random(7)
    )
    assert len(applied_pak) == 1
    assert applied_pak[0]["effect"] == "lane_penalty"
    tick_active_effects(actors)
    rdy_pak = compute_readiness_profile(
        k, rook, actors["street"], darius, actors["detroit"], "punch", "closed_stance", opt_behaviors=beh, model_cfg=model_cfg
    )
    assert rdy_pak["head_straight"] < rdy_before["head_straight"]
    assert rdy_pak["head_hook"] < rdy_before["head_hook"]

    # After one more tick, the 1-exchange pak_sao effect expires
    tick_active_effects(actors)
    rdy_expired = compute_readiness_profile(
        k, rook, actors["street"], darius, actors["detroit"], "punch", "closed_stance", opt_behaviors=beh, model_cfg=model_cfg
    )
    assert rdy_expired["head_straight"] == rdy_before["head_straight"]

    # Test low_posture (negativa) and vision (finger_jab)
    post_street_before = compute_posture_state(rook, actors["street"], beh)
    apply_technique_effects(
        "negativa", techs["negativa"]["on_success_effects"], "detroit", "street", actors, cards, "punch", ["kick", "punch", "clinch"], rng=random.Random(7)
    )
    apply_technique_effects(
        "finger_jab", techs["finger_jab"]["on_success_effects"], "detroit", "street", actors, cards, "punch", ["kick", "punch", "clinch"], rng=random.Random(7)
    )
    tick_active_effects(actors)
    post_detroit = compute_posture_state(darius, actors["detroit"], beh)
    post_street = compute_posture_state(rook, actors["street"], beh)
    assert post_detroit["height"] == "low_crouch"
    assert post_street["vision_effective"] == round(post_street_before["vision_effective"] - 0.8, 2)


def test_p5_knockdown_rules_standing_count_and_rooftop_edge_fall() -> None:
    """Verify standing count hooks, 3-knockdown / 4-knockdown rules, and rooftop_edge Fall (ring-out)."""
    k = Knowledge()
    rulesets = load_rulesets_v2(ROOT)["rulesets"]
    model_cfg = load_model_v2(ROOT)

    actors = {
        "a": {"damage": {"head": 5.0, "body": 0.0, "leg": 0.0}, "knockdowns_round": 0, "knockdowns_total": 0},
        "b": {"damage": {"head": 5.0, "body": 0.0, "leg": 0.0}, "knockdowns_round": 0, "knockdowns_total": 0},
    }
    rng = random.Random(42)
    for _ in range(3):
        sc = resolve_standing_count_or_knockdown(actors["b"], rulesets["boxing"], model_cfg, rng)
        assert sc is not None and "p_recover" in sc

    winner, reason = check_finish_conditions(["a", "b"], actors, model_cfg, ruleset_cfg=rulesets["boxing"])
    assert winner == "a"
    assert reason is not None and ("knockdown rule" in reason or "standing count" in reason)

    # Rooftop edge fall check
    donnell = load_card_v2(k, "donnell")
    darius = load_card_v2(k, "detroit")
    fell_fights = 0
    for s in range(1, 35):
        res = simulate_fight_v2(donnell, darius, ruleset="street", duration_s=60.0, seed=s, arena="rooftop_edge", knowledge=k)
        if res["finish_reason"] == "Fall (ring-out)":
            fell_fights += 1
    assert fell_fights >= 1
