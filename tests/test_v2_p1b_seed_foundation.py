"""Phase P1b tests: seed schemas, 160 techniques, capabilities/rulesets/combos/debts, availability parity, style templates."""

from __future__ import annotations

import copy
import json
from pathlib import Path

from engine.ontology import Knowledge
from engine.v2 import MOVE_BASE_STATS, available_v2, load_card_v2, simulate_fight_v2
from scripts.validate_v2_data import validate_all, validate_card_slots

ROOT = Path(__file__).resolve().parent.parent


def test_p1b_data_and_schema_validation_passes() -> None:
    res = validate_all(ROOT, verbose=False)
    assert res["status"] == "PASS"
    assert res["validated_files"] == 8
    assert len(MOVE_BASE_STATS) == 160


def test_p1b_availability_parity_and_karate_core() -> None:
    k = Knowledge()
    v1 = {t["id"]: t for t in json.loads((ROOT / "data" / "techniques.json").read_text())["techniques"]}
    tech_v2 = k.techniques_v2

    for cpath in sorted((ROOT / "cards" / "v2").glob("*.json")):
        card = load_card_v2(k, cpath)
        trained = set(card["baseline_capabilities"]) | {
            c for s in card["synchronized_capabilities"] for c in s["capabilities"]
        }
        legacy_av = {
            t
            for t in card["active_techniques"]
            if t in v1 and "mma" in v1[t]["ruleset_legality"] and (set(tech_v2[t]["required_capabilities"]) & trained)
        }
        if "karate" in trained and card["dimensions"].get("kicking") == "kicking.karate":
            legacy_av |= {"side_kick", "teep", "body_kick", "spinning_back_kick"}

        new_av = available_v2(k, card, "mma")
        att_legacy = {t for t in legacy_av if tech_v2[t]["kind"] != "defense" and tech_v2[t].get("usage") != "defense"}
        att_new = {t for t in new_av if tech_v2[t]["kind"] != "defense" and tech_v2[t].get("usage") != "defense"}
        att_new_existing = {t for t in att_new if tech_v2[t].get("status") == "existing"}
        assert att_legacy - att_new == set(), f"{card['fighter_id']} lost attacks: {att_legacy - att_new}"
        assert att_new_existing - att_legacy <= {"clinch_break", "stand_up", "head_kick", "switch_kick"}

    aya = load_card_v2(k, "karate")
    assert {"side_kick", "teep", "body_kick", "spinning_back_kick"} <= available_v2(k, aya, "mma")


def test_p1b_all_11_style_templates_load_and_simulate() -> None:
    k = Knowledge()
    tpl_paths = sorted((ROOT / "handoff_seed" / "style_templates").glob("*.json"))
    assert len(tpl_paths) == 11
    loaded_cards = []
    for tpath in tpl_paths:
        c = k.card(tpath)
        assert c["version"] == "block-2"
        assert validate_card_slots(c, ROOT) == []
        loaded_cards.append(c)

    # Verify two templates can simulate a quick fight cleanly
    res = simulate_fight_v2(loaded_cards[0], loaded_cards[1], ruleset="mma", duration_s=15.0, seed=11, knowledge=k)
    assert res["winner_id"] in (loaded_cards[0]["fighter_id"], loaded_cards[1]["fighter_id"])
    assert res["exchange_count"] >= 1


def test_p1b_rank_and_school_mastery_ceiling_validation() -> None:
    k = Knowledge()
    donnell = copy.deepcopy(load_card_v2(k, "donnell"))
    # Baseline donnell has slot warnings on current card, so filter for school_mastery problems
    donnell["rank"] = "master"
    donnell["school_mastery"] = {"boxing": "master", "inside_combinations": "expert"}
    k.schema("fighter_card_v2", donnell)
    sm_probs = [p for p in validate_card_slots(donnell, ROOT) if p.startswith("school_mastery")]
    assert sm_probs == []

    bad = copy.deepcopy(donnell)
    bad["school_mastery"] = {"boxing": "grandmaster", "judo": "trained"}
    bad_probs = [p for p in validate_card_slots(bad, ROOT) if p.startswith("school_mastery")]
    assert len(bad_probs) == 2
