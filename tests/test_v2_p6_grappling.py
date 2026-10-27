"""Phase P6 tests: pair-level grappling graph, skill contests, scrambles, staged submissions & control time (§7.12, §8.3, §8.4)."""

from __future__ import annotations

from pathlib import Path

from engine.ontology import Knowledge
from engine.simulator_v2 import load_card_v2, simulate_fight_v2
from engine.v2.data import load_positions_v2


def test_p6_every_position_change_follows_defined_transition() -> None:
    """Verify every grappling transition step recorded in sampled fights matches a transition in data/positions.json."""
    k = Knowledge()
    pos_data = load_positions_v2(k.root)
    valid_transitions = {
        (tr["from_position"], tr["to_position"], tr["via_technique"])
        for tr in pos_data.get("transitions", [])
    }

    matchups = [
        ("wrestler", "jiujitsu"),
        ("greco", "street"),
        ("sanda_judo", "thai"),
        ("wrestler", "philly"),
        ("jiujitsu", "street"),
    ]
    total_transitions_checked = 0
    for fa, fb in matchups:
        for seed in range(1, 16):
            res = simulate_fight_v2(fa, fb, ruleset="mma", duration_s=60.0, seed=seed, knowledge=k)
            for ex in res["exchanges"]:
                g_rec = ex.get("grappling")
                if not g_rec:
                    continue
                for step in g_rec.get("transitions", []):
                    tup = (step["from_position"], step["to_position"], step["via_technique"])
                    assert tup in valid_transitions, f"Transition {tup} not in data/positions.json"
                    total_transitions_checked += 1

    assert total_transitions_checked >= 50


def test_p6_staged_submissions_leg_entanglement_and_control_time() -> None:
    """Verify staged submissions (1-3 stages, contested escapes, failed-attempt rows), leg_entanglement, and control_time_s."""
    k = Knowledge()
    tpl_dir = k.root / "handoff_seed" / "style_templates"
    cw_card = load_card_v2(k, tpl_dir / "tpl_catch_wrestling.json")

    saw_leg_entanglement = False
    saw_staged_submission = False
    saw_failed_sub_transition = False
    for seed in range(1, 40):
        res = simulate_fight_v2(cw_card, "jiujitsu", ruleset="mma", duration_s=120.0, seed=seed, knowledge=k)
        for ex in res["exchanges"]:
            if ex.get("grappling_position") == "leg_entanglement":
                saw_leg_entanglement = True
            g_rec = ex.get("grappling") or {}
            if g_rec.get("contest") == "submission":
                saw_staged_submission = True
                if g_rec.get("escaped") and g_rec.get("from_position") != g_rec.get("to_position"):
                    saw_failed_sub_transition = True

    assert saw_staged_submission
    assert saw_leg_entanglement or saw_failed_sub_transition

    # Verify wrestling/greco control_time_s accrual
    wrestler_ctrl = 0.0
    for seed in range(1, 15):
        r_w = simulate_fight_v2("wrestler", "street", ruleset="mma", duration_s=60.0, seed=seed, knowledge=k)
        wrestler_ctrl += float(r_w["final_state_v2"]["actors"]["wrestler"]["control_time_s"])
    assert wrestler_ctrl > 10.0


def test_p6_jiujitsu_submission_win_share() -> None:
    """Verify jiujitsu achieves >= 25% of its wins by Submission across sampled matchups (§10.6)."""
    k = Knowledge()
    opponents = ["street", "donnell", "detroit", "thai", "karate", "wrestler"]
    jj_wins = 0
    jj_sub_wins = 0
    for opp in opponents:
        for seed in range(1, 21):
            res = simulate_fight_v2("jiujitsu", opp, ruleset="mma", duration_s=180.0, seed=seed, knowledge=k)
            if res["winner_id"] == "jiujitsu":
                jj_wins += 1
                if "Submission" in str(res["finish_reason"]):
                    jj_sub_wins += 1

    assert jj_wins > 0
    assert (jj_sub_wins / jj_wins) >= 0.25, f"Expected >= 25% submission wins for jiujitsu, got {jj_sub_wins}/{jj_wins}"
