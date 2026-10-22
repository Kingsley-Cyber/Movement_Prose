"""Content, reference and runtime wiring checks independent of recovery data."""
import importlib
import itertools
import math
import ast
from collections import Counter
from .ontology import Knowledge, read


REQUIRED = {
    "hands": "high_guard philly_shell peekaboo cross_arm long_guard helmet shield52 hands_down kronk dutch_guard".split(),
    "defense": "slip_roll parry_catch block_absorb outfight shoulder_roll smother check_frame sprawl_pummel".split(),
    "stance": "upright bladed crouch balanced planted switch shuffle".split(),
    "tie": "thai_plum greco folk_ride freestyle judo_sambo bjj wall_boxing anti_grappling".split(),
    "target": "head_hunter body_puncher leg_chopper liver_ribs knee_clincher mixer".split(),
    "kicking": "none muay_thai dutch karate sanda wrestler_teep".split(),
    "mentality": "outboxer swarmer counter slugger boxer_puncher switch_hitter defensive pressure spoiler slickster showman technician".split()}
MATRICES = {"mentality_mentality": ("mentality", "mentality"), "stance_stance": ("stance", "stance"),
            "hands_target": ("hands", "target"), "defense_target": ("defense", "target"),
            "defense_kicking": ("defense", "kicking"), "stance_kicking": ("stance", "kicking"),
            "tie_tie": ("tie", "tie"), "tie_stance": ("tie", "stance")}
TYPES = {"BEATS", "LOSES_TO", "COMPATIBLE_WITH", "INCOMPATIBLE_WITH", "EXPOSES", "EXPLOITED_BY", "REQUIRES", "ENABLES", "COUNTERS", "TRANSITIONS_TO", "ADAPTS_TO", "CAUSES"}


def audit(root=None):
    errors, warnings = [], []
    try:
        k = Knowledge(root) if root else Knowledge()
    except (OSError, ValueError, KeyError) as exc:
        return {"status": "FAIL", "errors": ["knowledge load: " + str(exc)], "warnings": [], "counts": {}}

    def need(condition, message):
        if not condition:
            errors.append(message)

    def fields(record, required, context):
        for field in required.split():
            need(field in record and record[field] not in [None, "", [], {}], context + " missing " + field)

    def provenance(prov, context):
        need(prov.get("classification") in ["CANON", "VERIFIED"], context + " classification")
        for claim in prov.get("basis_claims", []):
            need(claim in k.claims, context + " unknown claim " + claim)
        if prov.get("classification") == "VERIFIED":
            need(bool(prov.get("source_ids")), context + " unsupported verified label")
            for src in prov.get("source_ids", []):
                need(src in k.sources, context + " unknown source " + src)

    expected = {d + "." + i for d, ids in REQUIRED.items() for i in ids}
    need(set(k.options) == expected, "mandatory ontology ID coverage")
    need(set(k.index["dimensions"]) == set(REQUIRED), "dimension index coverage")
    for dim, ids in REQUIRED.items():
        need(set(k.index["dimensions"].get(dim, [])) == {dim + "." + i for i in ids}, "dimension index " + dim)
    out, incoming = Counter(), Counter()
    for r in k.relationships.values():
        if r["type"] == "COUNTERS":
            out[r["source_id"]] += 1
            incoming[r["destination_id"]] += 1
    for ident, option in k.options.items():
        fields(option, "id name dimension description reference_anchor boxing_form mma_adaptation mechanical_advantages derived_liabilities counter_relationships compatible_options incompatible_options ratings preferred_ranges tactical_conditions technique_refs exploitable_debt_ids provenance", ident)
        provenance(option.get("provenance", {}), ident)
        need(all(isinstance(v, int) and 1 <= v <= 5 for v in option["ratings"].values()), ident + " ratings outside 1–5")
        for adaptation in ["boxing_form", "mma_adaptation"]:
            fields(option[adaptation], "description ratings covers", ident + " " + adaptation)
            need(all(1 <= v <= 5 for v in option[adaptation]["ratings"].values()), ident + " adaptation ratings")
        need(out[ident] >= 2 and incoming[ident] >= 1, ident + " lacks incoming/outgoing counters")
        for tid in option["technique_refs"]:
            need(tid in k.techniques, ident + " unknown technique " + tid)
        for did in option["exploitable_debt_ids"]:
            need(did in k.debts and k.debts[did]["option_id"] == ident, ident + " invalid debt " + did)
        for r in option["counter_relationships"]:
            need(r in k.relationships and k.relationships[r]["source_id"] == ident and k.relationships[r]["type"] == "COUNTERS", ident + " invalid counter pointer")
        for field in ["compatible_options", "incompatible_options"]:
            need(all(x in k.options for x in option[field]), ident + " invalid option relationship")
        if option["dimension"] == "stance":
            fields(option, "carryover", ident)
        if option["dimension"] == "mentality":
            fields(option, "strengths weaknesses natural_tempo stamina_drain_tendency on_screen_behavior", ident)
        if option["dimension"] == "target":
            fields(option, "exploits shut_down_by", ident)
    for did, debt in k.debts.items():
        fields(debt, "id option_id opening mechanical_tradeoff exploiters technique_ids required_range ruleset classification", did)
        need(debt["option_id"] in k.options, did + " missing source")
        need(all(x in k.options for x in debt["exploiters"]), did + " missing exploiter")
        need(all(x in k.techniques for x in debt["technique_ids"]), did + " missing exploit technique")
        for x in debt["exploiters"]:
            need(debt["opening"] in k.options[x]["tactical_conditions"]["answers"], did + " unsupported exploit")
    caps = {"cap." + c for t in k.techniques.values() for c in t["required_capabilities"]}
    known = set(k.options) | set(k.debts) | set(k.techniques) | caps
    seen = set()
    for r in k.relationships.values():
        fields(r, "id source_id destination_id type mechanism preconditions ruleset classification", r["id"])
        need(r["type"] in TYPES, "unknown relationship type")
        need(r["source_id"] in known and r["destination_id"] in known, "dangling graph reference " + r["id"])
        key = (r["source_id"], r["destination_id"], r["type"])
        need(key not in seen, "duplicate graph relationship")
        seen.add(key)
        need(r["classification"] == "CANON", "tactical relationship may not claim empirical verification")
        if r["type"] == "COUNTERS" and r["source_id"] in k.options and r["destination_id"] in k.options:
            a, b = k.options[r["source_id"]], k.options[r["destination_id"]]
            need(bool(set(a["tactical_conditions"]["answers"]) & set(b["tactical_conditions"]["exposes"])), "unsupported counter mechanism " + r["id"])
            need((r["destination_id"], r["source_id"], "LOSES_TO") in {(x["source_id"], x["destination_id"], x["type"]) for x in k.relationships.values()}, "missing reciprocal counter")
    need({r["type"] for r in k.relationships.values()} == TYPES, "relationship type coverage")
    for a, b in [("outboxer", "slugger"), ("slugger", "swarmer"), ("swarmer", "outboxer")]:
        need(("mentality." + a, "mentality." + b, "BEATS") in seen, "missing conditional triangle")
    need(set(k.matrices) == set(MATRICES), "required matrix coverage")
    cell_count = 0
    for mid, (rd, cd) in MATRICES.items():
        if mid not in k.matrices:
            continue
        matrix = k.matrices[mid]
        keys = [(c["row_id"], c["column_id"]) for c in matrix["cells"]]
        expected_pairs = set(itertools.product([rd + "." + i for i in REQUIRED[rd]], [cd + "." + i for i in REQUIRED[cd]]))
        need(len(keys) == len(set(keys)) and set(keys) == expected_pairs, mid + " duplicate/missing cells")
        cell_count += len(keys)
        for cell in matrix["cells"]:
            fields(cell, "id row_id column_id mechanism preconditions defended_openings how classification numeric_basis", cell["id"])
            edge = cell["edge"]
            need(isinstance(edge, (float, int)) and math.isfinite(edge) and -1 <= edge <= 1, cell["id"] + " invalid edge")
            need(cell["favored_side"] == ("row" if edge > 0 else "column" if edge < 0 else "neutral"), cell["id"] + " inverted favored side")
            need(all(x in k.debts for x in cell["exploited_debt_ids"]), cell["id"] + " unknown cell debt")
            if rd == cd:
                reverse = k.cells[mid].get((cell["column_id"], cell["row_id"]))
                need(reverse is not None and edge == -reverse["edge"], cell["id"] + " reciprocity")
                if cell["row_id"] == cell["column_id"]:
                    need(edge == 0, "self matchup nonzero")
        if rd == cd:
            for row in REQUIRED[rd]:
                values = [c["edge"] for c in matrix["cells"] if c["row_id"] == rd + "." + row and c["row_id"] != c["column_id"]]
                need(not values or not all(v > 0 for v in values), "universally dominant matrix option " + row)
                if values and all(v >= 0 for v in values) and any(v > 0 for v in values):
                    warnings.append({"option": rd + "." + row, "finding": "Weakly non-losing base row; ties and cross-dimensional liabilities remain. Not universal dominance.", "incoming_counters": incoming[rd + "." + row]})
    need(cell_count == 511, "511-cell requirement")
    weights = k.model["weights"]
    need(set(weights) == set(MATRICES) and math.isclose(sum(weights.values()), 1), "matrix weights not normalized")
    need(all(v > 0 for v in weights.values()) and weights["mentality_mentality"] > weights["stance_stance"] >= weights["tie_stance"] and weights["mentality_mentality"] > weights["tie_tie"] >= weights["tie_stance"], "dimension priority")
    for tid, t in k.techniques.items():
        fields(t, "id name description combat_schools ruleset_legality starting_stance required_range required_body_configuration setup_actions execution_phases attacking_limb target_region direction_trajectory contact_conditions defensive_counters recovery_requirements balance_support expected_state_changes potential_failure_conditions visual_readability provenance kind required_capabilities", tid)
        need(all(x in k.techniques for x in t["defensive_counters"] + t["follow_up_opportunities"]), tid + " invalid follow-up/counter")
        need(all(x == "observe" or x == "grip" or x in k.techniques for x in t["setup_actions"]), tid + " invalid setup")
        provenance(t["provenance"], tid)
    combos = read(k.root / "data/combinations.json")["combinations"]
    for combo in combos:
        need(combo["from"] in k.techniques and combo["to"] in k.techniques and combo["success"] == "possible, never guaranteed", "invalid technique combination")
    for claim in k.claims.values():
        fields(claim, "id classification source_ids claim limits", claim["id"])
        need(all(src in k.sources for src in claim["source_ids"]), "unsupported verified source label " + claim["id"])
    for source in k.sources.values():
        fields(source, "id title publisher url access_date applicable_claim evidence_limitations access_method", source["id"])
        need(source["url"].startswith("https://"), "source URL")
    card_ids = set()
    for path in sorted((k.root / "cards").glob("*.json")):
        try:
            card = k.card(path)
            need(card["fighter_id"] not in card_ids, "duplicate fighter ID")
            card_ids.add(card["fighter_id"])
        except Exception as exc:
            errors.append(path.name + ": " + str(exc))
    need(len(card_ids) >= 11 and {"maleek", "donnell", "macklin", "detroit", "philly"} <= card_ids, "mandatory fighter coverage")
    eventids = set()
    for mapping in k.pipeline["event_types"]:
        eventids.add(mapping["id"])
        for key in ["state_handler", "choreography_handler", "prompt_handler"]:
            module, symbol = mapping[key].rsplit(".", 1)
            try:
                module_path = k.root / (module.replace(".", "/") + ".py")
                declared = {n.name for n in ast.parse(module_path.read_text()).body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
                need(symbol in declared, "missing handler declaration " + mapping[key])
                need(callable(getattr(importlib.import_module(module), symbol)), "unreachable " + mapping[key])
            except (ImportError, AttributeError, OSError, SyntaxError):
                errors.append("unreachable " + mapping[key])
        fields(mapping, "technique_kinds", "event mapping " + mapping["id"])
    from .fight_state import HANDLERS
    need(eventids == set(HANDLERS), "missing/unhandled event types")
    for doc in k.pipeline["required_docs"]:
        need((k.root / doc).is_file() and bool((k.root / doc).read_text().strip()), "missing documentation " + doc)
    return {"status": "PASS" if not errors else "FAIL", "errors": errors, "warnings": warnings,
            "counts": {"ontology_options": len(k.options), "matchup_cells": cell_count, "fighter_cards": len(card_ids),
                       "techniques": len(k.techniques), "relationships": len(k.relationships),
                       "counter_relationships": sum(r["type"] == "COUNTERS" for r in k.relationships.values()),
                       "debts": len(k.debts), "debt_exploit_relationships": sum(r["type"] == "EXPLOITED_BY" for r in k.relationships.values()),
                       "event_types": len(eventids), "sources": len(k.sources), "verified_claims": len(k.claims)},
            "knowledge_sha256": k.fingerprint(), "provenance": "Verified claims resolve to accessed sources. All matchup values and tactical interpretations are CANON; factual verification is not inferred from pointer validity."}
