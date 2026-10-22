from .capabilities import available, resolved_dimensions


def _edge(k, matrix, row, col, row_card, col_card, ruleset):
    if row is None or col is None:
        return 0.0, {"cell_id": None, "edge": 0.0, "reason": "Uncovered selection; only reachable NULL rules can penalize it."}
    cell = k.cells[matrix][row, col]
    edge = cell["edge"]
    a, b = k.options[row], k.options[col]
    # Recompute exactly the same coverage formula with the card's documented
    # adaptation. Keeping a boxing base in MMA retains its stated exposures.
    am = a["mma_adaptation" if row_card["adaptation"] == "mma" and ruleset == "mma" else "boxing_form"]
    bm = b["mma_adaptation" if col_card["adaptation"] == "mma" and ruleset == "mma" else "boxing_form"]
    ac, bc = set(am["covers"]), set(bm["covers"])
    ae = set(a["tactical_conditions"]["exposes"])
    be = set(b["tactical_conditions"]["exposes"])
    asymmetric_attack = k.matrices[matrix]["column_dimension"] in ["target", "kicking"]
    gate = True
    if asymmetric_attack:
        # Only attack lanes that this card can execute count. A target tendency
        # does not grant a low kick, knee, or submission.
        targets = {k.techniques[t]["target_region"] for t in available(k, col_card, ruleset)
                   if k.techniques[t]["kind"] in ["punch", "kick", "knee"]}
        lane_target = {"head_straight": "head", "head_hook": "head", "head_uppercut": "head",
                       "vision": "head", "body": "body", "leg": "leg"}
        bc = {lane for lane in bc if lane_target.get(lane, "body") in targets}
        gate = bool(bc)
        edge = (len(ac & bc) - sum(am["exposure_weights"][lane] for lane in ae & bc)) / len(bc) if bc else 0.0
    else:
        edge = (sum(bm["exposure_weights"][lane] for lane in ac & be) / len(be)
                - sum(am["exposure_weights"][lane] for lane in bc & ae) / len(ae)) / 2
    return edge, {"cell_id": cell["id"], "authored_edge": cell["edge"], "edge": edge,
                  "mechanism": cell["mechanism"], "how": cell["how"],
                  "adaptations": [row_card["adaptation"], col_card["adaptation"]],
                  "attack_capability_gate": gate,
                  "active_forward_lanes": sorted(ac & (bc if asymmetric_attack else be)),
                  "active_reverse_lanes": sorted(ae & bc), "classification": "CANON"}


def evaluate(k, a, b, ruleset):
    dimensions = k.model["rulesets"][ruleset]["dimensions"]
    applicable = {key: m for key, m in k.matrices.items()
                  if m["row_dimension"] in dimensions and m["column_dimension"] in dimensions}
    total = sum(k.model["weights"][key] for key in applicable)
    if not isinstance(total, (int, float)) or total <= 0:
        raise ValueError("invalid matrix weight total")
    da = resolved_dimensions(k, a)
    db = resolved_dimensions(k, b)
    traces = []
    for key, matrix in applicable.items():
        rd, cd = matrix["row_dimension"], matrix["column_dimension"]
        fwd, ft = _edge(k, key, da[rd], db[cd], a, b, ruleset)
        if rd == cd:
            edge, directions = fwd, [ft]
        else:
            reverse, rt = _edge(k, key, db[rd], da[cd], b, a, ruleset)
            edge, directions = (fwd - reverse) / 2, [ft, rt]
        weight = k.model["weights"][key] / total
        traces.append({"matrix_id": key, "raw_weight": k.model["weights"][key], "normalized_weight": weight,
                       "signed_edge_for_a": edge, "weighted_contribution": weight * edge,
                       "directions": directions})
    return traces
