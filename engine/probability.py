import math
from .capabilities import admitted_slots, available, compatibility, null_seams, reachable, resolved_dimensions
from .matchups import evaluate
from .ontology import Knowledge, write


def predict(a, b, ruleset="mma", knowledge=None):
    k = knowledge or Knowledge()
    a, b = k.card(a), k.card(b)
    if a["fighter_id"] == b["fighter_id"]:
        raise ValueError("two distinct fighter IDs are required")
    if ruleset not in k.model["rulesets"]:
        raise ValueError("unknown ruleset")
    slot_coeff = k.model["slot_logit_per_net_slot"]
    null_coeff = k.model["null_logit_per_reachable_seam"]
    if not (isinstance(slot_coeff, (int, float)) and math.isfinite(slot_coeff) and isinstance(null_coeff, (int, float)) and math.isfinite(null_coeff)):
        raise ValueError("non-finite model coefficient")
    for w in k.model["weights"].values():
        if not (isinstance(w, (int, float)) and math.isfinite(w) and w > 0):
            raise ValueError("invalid model weight")
    traces = evaluate(k, a, b, ruleset)
    seams = null_seams(k, b, a, ruleset) + null_seams(k, a, b, ruleset)
    pa = sum(s["reachable"] for s in seams if s["victim_id"] == a["fighter_id"])
    pb = sum(s["reachable"] for s in seams if s["victim_id"] == b["fighter_id"])
    slots_a = len(admitted_slots(a, k))
    slots_b = len(admitted_slots(b, k))
    slot = slot_coeff * (slots_a - slots_b)
    null = null_coeff * (pb - pa)
    logit = math.fsum(t["weighted_contribution"] for t in traces) + slot + null
    if not math.isfinite(logit):
        raise ValueError("non-finite logit")
    p = 1 / (1 + math.exp(-logit)) if logit >= 0 else math.exp(logit) / (1 + math.exp(logit))
    weaknesses = reachable(k, a, b, ruleset) + reachable(k, b, a, ruleset)
    influences = [{"source": t["matrix_id"], "logit": t["weighted_contribution"],
                   "why": [d.get("how", d.get("reason")) for d in t["directions"]]} for t in traces]
    influences += [{"source": "slots", "logit": slot, "why": "Net synchronized slots, counted once."},
                   {"source": "NULL", "logit": null, "why": "One penalty per legal reachable uncovered dimension."}]
    paths = []
    for c, opponent in [(a, b), (b, a)]:
        accessible = [w for w in weaknesses if w["attacker_id"] == c["fighter_id"] and w["reachable"]]
        paths.append({"fighter_id": c["fighter_id"], "establish": c["preferred_ranges"],
                      "first_weakness_candidates": accessible,
                      "mechanism": c["debt_sentence"],
                      "reversal_risk": [w["debt_id"] for w in weaknesses if w["victim_id"] == c["fighter_id"] and w["reachable"]]})
    return {"model_version": k.model["version"], "knowledge_sha256": k.fingerprint(), "ruleset": ruleset,
            "fighter_a": a["fighter_id"], "fighter_b": b["fighter_id"],
            "probability_a": p, "probability_b": 1 - p, "logit_a": logit,
            "probability_classification": k.model["probability_label"],
            "matrix_edges": traces, "top_tactical_influences": sorted(influences, key=lambda x: abs(x["logit"]), reverse=True)[:3],
            "accessible_weaknesses": [w for w in weaknesses if w["reachable"]],
            "inaccessible_weaknesses": [w for w in weaknesses if not w["reachable"]],
            "null_seams": seams,
            "compatibility_effects": compatibility(k, a) + compatibility(k, b),
            "slot_effect": {"net_slots_a": slots_a - slots_b, "logit": slot},
            "null_effect": {"a_count": pa, "b_count": pb, "logit": null},
            "resolved_configurations": {c["fighter_id"]: {"adaptation": c["adaptation"], "orientation": c["orientation"],
                   "options": {dim: k.options[ident]["mma_adaptation" if c["adaptation"] == "mma" and ruleset == "mma" else "boxing_form"] if ident else None for dim, ident in resolved_dimensions(k, c).items()},
                   "available_techniques": sorted(available(k, c, ruleset))} for c in [a, b]},
            "range_control": {"early_initiator": max([a, b], key=lambda c: (c["tempo"], c["fighter_id"]))["fighter_id"],
                              "preferred_fight_favorite": a["fighter_id"] if p > .5 else b["fighter_id"] if p < .5 else None,
                              "contest": {c["fighter_id"]: c["preferred_ranges"] for c in [a, b]},
                              "explanation": "Early initiative follows authored tempo. Long-run preference follows the complete conditional model, not tempo alone."},
            "tactical_win_paths": paths,
            "confidence": {"classification": "uncalibrated", "uncertainty": ["Authored equal-lane scores and weights", "Range access can be denied", "No athlete measurements or empirical calibration"]},
            "provenance": {"classification": "CANON", "sources": sorted(k.sources), "formula": k.model["formula"]}}
