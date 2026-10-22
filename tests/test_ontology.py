import copy
import pytest
from engine.audit import REQUIRED, TYPES, audit
from engine.ontology import ROOT, read, write


def test_required_options_content_and_executable_wiring(knowledge):
    report = audit()
    assert report["status"] == "PASS", report["errors"]
    assert set(knowledge.options) == {d + "." + i for d, ids in REQUIRED.items() for i in ids}
    assert report["counts"]["ontology_options"] == 57
    assert report["counts"]["fighter_cards"] >= 11
    assert {r["type"] for r in knowledge.relationships.values()} == TYPES


def test_each_debt_has_real_opening_and_exploitation_path(knowledge):
    for debt in knowledge.debts.values():
        source = knowledge.options[debt["option_id"]]
        assert debt["opening"] in source["tactical_conditions"]["exposes"]
        assert debt["mechanical_tradeoff"]
        assert debt["exploiters"] and debt["technique_ids"]
        for exploiter in debt["exploiters"]:
            assert debt["opening"] in knowledge.options[exploiter]["tactical_conditions"]["answers"]
        assert any(r["source_id"] == debt["id"] and r["type"] == "EXPLOITED_BY" for r in knowledge.relationships.values())


def test_conditional_counter_cycle_and_no_universal_graph_dominance(knowledge):
    edges = {(r["source_id"], r["destination_id"]) for r in knowledge.relationships.values() if r["type"] == "BEATS"}
    assert {("mentality.outboxer", "mentality.slugger"), ("mentality.slugger", "mentality.swarmer"), ("mentality.swarmer", "mentality.outboxer")} <= edges
    counters = [r for r in knowledge.relationships.values() if r["type"] == "COUNTERS"]
    for ident in knowledge.options:
        assert sum(r["source_id"] == ident for r in counters) >= 2
        assert any(r["destination_id"] == ident for r in counters)
        assert all(r["preconditions"] and r["mechanism"] for r in counters if r["source_id"] == ident)


def test_cultural_evidence_is_separate_from_authored_52_mechanics(knowledge, cards):
    shield = knowledge.options["hands.shield52"]
    assert shield["provenance"]["classification"] == "CANON"
    assert knowledge.claims["claim_green_52"]["source_ids"] == ["green_52"]
    assert {c["id"] for c in cards["maleek"]["composites"]} == {"canon.52_dutch", "canon.uno"}
    assert all(c["classification"] == "CANON" for c in cards["maleek"]["composites"])


@pytest.mark.parametrize("defect", ["blank", "source", "counter", "debt", "mapping"])
def test_audit_rejects_broken_knowledge(project_copy, defect):
    if defect in ["blank", "source"]:
        path = project_copy / "data/engine_index.json"
        data = read(path)
        option = data["options"][0]
        if defect == "blank":
            option["description"] = ""
        else:
            option["provenance"] = {"classification": "VERIFIED", "source_ids": ["imaginary_source"]}
    elif defect == "counter":
        path = project_copy / "data/counter_graph.json"
        data = read(path)
        data["relationships"][0]["destination_id"] = "invented.option"
    elif defect == "debt":
        path = project_copy / "data/debt_registry.json"
        data = read(path)
        data["debts"][0]["exploiters"] = []
    else:
        path = project_copy / "data/pipeline.json"
        data = read(path)
        data["event_types"].pop()
    write(path, data)
    assert audit(project_copy)["status"] == "FAIL"


def test_every_card_has_plain_language_comprehension(cards):
    for card in cards.values():
        assert all(card["fighting_description"][k].strip() for k in ["does", "wins", "avoids", "beaten_by"])
        assert card["debt_sentence"] and card["combat_limitations"]
