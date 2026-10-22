"""Comprehensive fairness, admission, NULL reachability, 220-pair invariant, state-sequence,
consumer-boundary, and mutation-verification test suite implementing `docs/fairness_test_plan.md`.
"""

import copy
import itertools
import json
import math
import subprocess
import sys
import jsonschema
import pytest

from engine.capabilities import (
    admit_ranked_result,
    admitted_slots,
    available,
    null_seams,
    option_supported,
    reachable,
    resolved_dimensions,
    training,
)
from engine.event_graph import graph, validate
from engine.fight_director import Builder, plan
from engine.fight_state import apply
from engine.matchups import evaluate
from engine.ontology import Knowledge, ROOT
from engine.probability import predict


def test_slot_copy_set_order_and_duplicate_members_rejected_or_invariant(cards, knowledge, tmp_path):
    # SLOT-COPY (F-001): exact copied bundle with new ID/description rejected by card admission & CLI
    clone = copy.deepcopy(cards["wrestler"])
    copied_slot = copy.deepcopy(clone["synchronized_capabilities"][0])
    copied_slot["id"] = "audit_duplicate_slot"
    copied_slot["description"] = "Copied training, no new synchronized mechanism."
    clone["synchronized_capabilities"].append(copied_slot)
    clone["slot_count"] += 1
    clone["slot_label"] = "Triad"

    with pytest.raises(ValueError, match="duplicate synchronized capability bundle"):
        knowledge.card(clone)

    # Even if raw dict is passed to admitted_slots, duplicate semantic bundle is not counted
    assert len(admitted_slots(clone, knowledge)) == cards["wrestler"]["slot_count"]

    ap = tmp_path / "clone.json"
    bp = tmp_path / "donnell.json"
    ap.write_text(json.dumps(clone))
    bp.write_text(json.dumps(cards["donnell"]))
    run = subprocess.run(
        [sys.executable, str(ROOT / "predict.py"), str(ap), str(bp), "--ruleset", "mma"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert run.returncode != 0

    # SLOT-SET-ORDER: reordering unordered capabilities or slot presentation preserves probability & count
    reordered = copy.deepcopy(cards["wrestler"])
    reordered["synchronized_capabilities"][1]["capabilities"] = list(
        reversed(reordered["synchronized_capabilities"][1]["capabilities"])
    )
    reordered["synchronized_capabilities"] = list(reversed(reordered["synchronized_capabilities"]))
    p_orig = predict(cards["wrestler"], cards["donnell"], "mma", knowledge)
    p_reord = predict(reordered, cards["donnell"], "mma", knowledge)
    assert len(admitted_slots(reordered, knowledge)) == 2
    assert math.isclose(p_orig["probability_a"], p_reord["probability_a"], rel_tol=0, abs_tol=1e-12)

    # SLOT-DUPLICATE-MEMBERS: repeating a capability inside a single bundle is rejected
    dup_member = copy.deepcopy(cards["wrestler"])
    dup_member["synchronized_capabilities"][0]["capabilities"] = ["wrestling", "wrestling"]
    with pytest.raises((ValueError, jsonschema.ValidationError)):
        knowledge.card(dup_member)

    # SLOT-COUNT: declared count differing from admitted entries or outside 1..4 is rejected
    bad_count = copy.deepcopy(cards["wrestler"])
    bad_count["slot_count"] = 3
    bad_count["slot_label"] = "Triad"
    with pytest.raises(ValueError, match="slot count"):
        knowledge.card(bad_count)


def test_slot_valid_coordination_coefficient_and_swap(cards, knowledge):
    # SLOT-VALID-COORDINATION + SLOT-COEFFICIENT + SLOT-SWAP
    base_ab = predict(cards["wrestler"], cards["donnell"], "mma", knowledge)
    valid = copy.deepcopy(cards["wrestler"])
    valid["slot_count"] += 1
    valid["slot_label"] = "Triad"
    valid["synchronized_capabilities"].append(
        {
            "id": "wrestler.slot.3",
            "capabilities": ["basic_movement"],
            "description": "Distinct footwork-entry coordination using existing movement training.",
        }
    )
    changed_ab = predict(valid, cards["donnell"], "mma", knowledge)
    changed_ba = predict(cards["donnell"], valid, "mma", knowledge)
    assert math.isclose(changed_ab["logit_a"] - base_ab["logit_a"], 0.15, rel_tol=0, abs_tol=1e-12)
    assert math.isclose(changed_ab["slot_effect"]["logit"], -changed_ba["slot_effect"]["logit"], rel_tol=0, abs_tol=1e-12)


def test_style_unsupported_roster_and_claim_authority(cards, knowledge, tmp_path):
    # STYLE-UNSUPPORTED (F-002): Donnell claiming tie.anti_grappling without training/techniques
    unearned = copy.deepcopy(cards["donnell"])
    unearned["dimensions"]["tie"] = "tie.anti_grappling"
    with pytest.raises(ValueError, match="unsupported dimension option"):
        knowledge.card(unearned)

    ap = tmp_path / "unearned.json"
    bp = tmp_path / "wrestler.json"
    ap.write_text(json.dumps(unearned))
    bp.write_text(json.dumps(cards["wrestler"]))
    run = subprocess.run(
        [sys.executable, str(ROOT / "predict.py"), str(ap), str(bp), "--ruleset", "mma"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert run.returncode != 0

    # Even if raw dict is passed directly to resolved_dimensions / null_seams / evaluate,
    # the unsupported tie label resolves to None and grants zero NULL erasure or matrix credit.
    assert resolved_dimensions(knowledge, unearned)["tie"] is None
    seams_orig = null_seams(knowledge, cards["wrestler"], cards["donnell"], "mma")
    seams_unearned = null_seams(knowledge, cards["wrestler"], unearned, "mma")
    assert seams_orig == seams_unearned
    assert evaluate(knowledge, cards["donnell"], cards["wrestler"], "mma") == evaluate(
        knowledge, unearned, cards["wrestler"], "mma"
    )

    # STYLE-ROSTER: all 11 shipped cards have supported options across all 7 dimensions
    for card in cards.values():
        for dim, opt_id in card["dimensions"].items():
            assert option_supported(knowledge, card, opt_id), f"{card['fighter_id']} {dim}={opt_id}"

    # CLAIM-AUTHORITY: self-declared VERIFIED provenance on a fighter card is rejected
    forged_prov = copy.deepcopy(cards["maleek"])
    forged_prov["provenance"]["classification"] = "VERIFIED"
    with pytest.raises(ValueError, match="CANON"):
        knowledge.card(forged_prov)


def test_null_and_truth_table_and_reachability_oracles(cards, knowledge):
    # NULL-AND: 2^4 = 16 truth table over (ruleset_includes_tie, tie_is_null, attacker_has_entry_tech, attacker_has_capability)
    for ruleset_mma, tie_is_null, has_entry_tech, has_cap in itertools.product([True, False], repeat=4):
        ruleset = "mma" if ruleset_mma else "boxing"
        victim = copy.deepcopy(cards["donnell"])
        if not tie_is_null:
            victim = copy.deepcopy(cards["wrestler"])  # has supported tie.freestyle
        attacker = copy.deepcopy(cards["wrestler"])
        if not has_entry_tech:
            attacker["active_techniques"] = [
                t for t in attacker["active_techniques"] if knowledge.techniques[t]["kind"] not in ["takedown", "grip"]
            ]
        if not has_cap:
            attacker["synchronized_capabilities"] = [
                {"id": "wrestler.slot.1", "capabilities": ["boxing"], "description": "Boxing only"},
                {"id": "wrestler.slot.2", "capabilities": ["kickboxing"], "description": "Kickboxing only"},
            ]
        seams = null_seams(knowledge, attacker, victim, ruleset)
        tie_seams = [s for s in seams if s["dimension"] == "tie"]
        expected_present = tie_is_null
        expected_reachable = ruleset_mma and tie_is_null and has_entry_tech and has_cap
        assert bool(tie_seams) == expected_present
        if tie_seams:
            assert tie_seams[0]["reachable"] == expected_reachable

    # NULL-NONE: kicking.none is an explicit punch-only option, not NULL
    assert cards["donnell"]["dimensions"]["kicking"] == "kicking.none"
    assert all(s["dimension"] != "kicking" for s in null_seams(knowledge, cards["maleek"], cards["donnell"], "mma"))

    # NULL-PRECONDITION: BJJ card with guard_pull removed cannot reach ground-only debts
    bjj_no_entry = copy.deepcopy(cards["jiujitsu"])
    bjj_no_entry["active_techniques"] = [t for t in bjj_no_entry["active_techniques"] if t != "guard_pull"]
    for w in reachable(knowledge, bjj_no_entry, cards["donnell"], "mma"):
        if w["required_range"] == "ground":
            assert w["reachable"] is False

    # NULL-FORGERY: removing a debt ID from exploitable_seams is rejected by admission and restored by reachable()
    forged_debt = copy.deepcopy(cards["donnell"])
    removed_debt = forged_debt["exploitable_seams"].pop(0)
    with pytest.raises(ValueError, match="missing required option debt"):
        knowledge.card(forged_debt)
    restored_ids = {w["debt_id"] for w in reachable(knowledge, cards["maleek"], forged_debt, "mma")}
    assert removed_debt in restored_ids


def test_all_220_ordered_pair_ruleset_invariants_and_numerics(cards, knowledge):
    # Enumerate all 11 * 10 / 2 = 55 unordered pairs x 2 rulesets = 110 contexts (220 ordered evaluations)
    ordered_count = 0
    for a, b in itertools.combinations(cards.values(), 2):
        for ruleset in ["mma", "boxing"]:
            ab = predict(a, b, ruleset, knowledge)
            ba = predict(b, a, ruleset, knowledge)
            ordered_count += 2
            assert math.isclose(ab["probability_a"] + ba["probability_a"], 1.0, rel_tol=0, abs_tol=1e-12)
            assert math.isclose(ab["logit_a"], -ba["logit_a"], rel_tol=0, abs_tol=1e-12)
            trace_sum = (
                math.fsum(t["weighted_contribution"] for t in ab["matrix_edges"])
                + ab["slot_effect"]["logit"]
                + ab["null_effect"]["logit"]
            )
            assert math.isclose(ab["logit_a"], trace_sum, rel_tol=0, abs_tol=1e-12)
    assert ordered_count == 220

    # PROB-IDENTICAL: identical modeled configurations with distinct fighter IDs yield 0.5 probability
    twin_a = copy.deepcopy(cards["maleek"])
    twin_b = copy.deepcopy(cards["maleek"])
    twin_b["fighter_id"] = "maleek_twin"
    twin_b["name"] = "Maleek Twin"
    p_twin = predict(twin_a, twin_b, "mma", knowledge)
    assert math.isclose(p_twin["probability_a"], 0.5, rel_tol=0, abs_tol=1e-12)
    assert math.isclose(p_twin["logit_a"], 0.0, rel_tol=0, abs_tol=1e-12)

    # PROB-NUMERICS: NaN/Infinity model parameters fail closed
    bad_k = copy.deepcopy(knowledge)
    bad_k.model["slot_logit_per_net_slot"] = float("nan")
    with pytest.raises(ValueError, match="non-finite"):
        predict(cards["maleek"], cards["donnell"], "mma", bad_k)


def test_outcome_modes_consumer_boundary_and_state_sequences(cards, knowledge):
    # MODE-ANALYSIS, MODE-SAMPLED, MODE-DIRECTED, MODE-CONSUMER
    pred = predict(cards["maleek"], cards["donnell"], "mma", knowledge)
    sampled = plan(cards["maleek"], cards["donnell"], seed=42, knowledge=knowledge)
    directed = plan(cards["maleek"], cards["donnell"], winner="donnell", seed=42, knowledge=knowledge)

    assert sampled["selection"]["mode"] == "predictive"
    assert directed["selection"]["mode"] == "director-controlled"
    assert directed["prediction"] == sampled["prediction"]

    # Consumer boundary rejects predictions, sampled fight plans, and director-controlled plans
    for invalid_record in [pred, sampled, directed, {"mode": "predictive", "winner_id": "maleek"}]:
        with pytest.raises(ValueError):
            admit_ranked_result(invalid_record)

    assert (
        admit_ranked_result(
            {
                "origin": "independent_adjudicated_match",
                "result_id": "match-001",
                "ruleset": "mma",
                "winner_id": "maleek",
            }
        )
        is True
    )

    # STATE-SETUP, STATE-CONTACT, STATE-PERSISTENCE across generated legal/illegal sequences
    b_bad = Builder(knowledge, [cards["maleek"], cards["donnell"]], "mma")
    for actor in b_bad.cards:
        b_bad.emit("assessment", actor)
    # Illegal non-adjacent jump from outside -> clinch must fail
    b_bad.emit("setup", "maleek", "step")
    with pytest.raises(ValueError, match="nonadjacent"):
        b_bad.emit("movement", "maleek", "step", {"to_range": "clinch"})

    # Legal step into kick range -> low_kick -> damage persists
    b = Builder(knowledge, [cards["maleek"], cards["donnell"]], "mma")
    for actor in b.cards:
        b.emit("assessment", actor)
    b.stage("maleek", "kick")
    b.action("maleek", "low_kick")
    leg_damage_after_kick = b.state["actors"]["donnell"]["damage"]["leg"]
    assert leg_damage_after_kick > 0
    b.stage("donnell", "punch")
    assert b.state["actors"]["donnell"]["damage"]["leg"] == leg_damage_after_kick


def test_removing_admission_gates_in_disposable_copy_causes_fairness_probe_to_fail(project_copy, tmp_path):
    # "Test the tests": remove the new admission & resolution gates in a disposable copy and verify verify_findings.py fails (exit 1)
    ontology_path = project_copy / "engine/ontology.py"
    text = ontology_path.read_text()
    weakened = (
        text.replace(
            'if ident is not None and not option_supported(self, card, ident):\n                raise ValueError("unsupported dimension option for card training: " + str(ident))',
            "pass",
        )
        .replace(
            'if len(admitted_slots(card, self)) != card["slot_count"]:\n            raise ValueError("duplicate synchronized capability bundle")',
            "pass",
        )
        .replace(
            'if not expected_debts <= set(card["exploitable_seams"]):\n            raise ValueError("missing required option debt in exploitable_seams")',
            "pass",
        )
    )
    assert weakened != text
    ontology_path.write_text(weakened)

    cap_path = project_copy / "engine/capabilities.py"
    cap_text = cap_path.read_text()
    cap_weakened = cap_text.replace(
        "if sig in seen:\n            continue",
        "pass",
    ).replace(
        "dim: (opt_id if option_supported(k, card, opt_id) else None)",
        "dim: opt_id",
    )
    assert cap_weakened != cap_text
    cap_path.write_text(cap_weakened)

    out_dir = tmp_path / "mutated_probe_out"
    run = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/verify_findings.py"),
            "--root",
            str(project_copy),
            "--output-dir",
            str(out_dir),
        ],
        capture_output=True,
        text=True,
    )
    assert run.returncode == 1
    payload = json.loads(run.stdout)
    assert payload["fairness_gate_status"] == "FAIL"
    assert any(f["id"] == "F-001" and f["classification"] == "CONFIRMED_DEFECT" for f in payload["findings"])
    assert any(f["id"] == "F-002" and f["classification"] == "CONFIRMED_DEFECT" for f in payload["findings"])
