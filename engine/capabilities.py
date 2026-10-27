KNOWN_CAPABILITIES = {
    "acrobatics",
    "anti_grappling",
    "baguazhang",
    "bajiquan",
    "basic_movement",
    "bjj",
    "boxing",
    "cage_plum",
    "capoeira",
    "catch_wrestling",
    "clinch",
    "counter_boxing",
    "hung_gar",
    "inside_combinations",
    "jeet_kune_do",
    "judo",
    "karate",
    "kickboxing",
    "lethwei",
    "muay_thai",
    "pressure_footwork",
    "sanda",
    "shield",
    "shuai_jiao",
    "switch_step",
    "taekwondo",
    "tai_chi",
    "untrained_striking",
    "wall_boxing",
    "wing_chun",
    "wrestling",
}

OPTION_REQUIRED_TECHS = {
    "hands.shield52": {"shield_frame"},
    "hands.dutch_guard": {"low_kick"},
    "defense.smother": {"pummel"},
    "defense.check_frame": {"check", "shield_frame"},
    "defense.sprawl_pummel": {"sprawl", "pummel"},
    "stance.switch": {"switch_step"},
    "mentality.switch_hitter": {"switch_step"},
    "target.leg_chopper": {"low_kick"},
    "target.knee_clincher": {"knee_body", "collar_tie"},
}

UNTRAINED_PUNCH_OPTIONS = {
    "hands.hands_down",
    "defense.block_absorb",
    "stance.planted",
    "target.head_hunter",
    "kicking.none",
    "mentality.slugger",
    "mentality.showman",
}


def training(card, activated=()):
    caps = set(card["baseline_capabilities"])
    caps.update(c for slot in card["synchronized_capabilities"] for c in slot["capabilities"])
    caps.update(a["grants_capability"] for a in card["conditional_abilities"] if a["id"] in activated)
    return caps


def slot_signature(slot):
    """Semantic identity of a synchronized bundle: unordered capability set plus optional ordered sequence."""
    caps = frozenset(slot.get("capabilities") or ())
    seq = tuple(slot.get("coordination_sequence") or ())
    return caps, seq


def admitted_slots(card, k=None):
    """Return distinct admitted synchronized capability bundles; duplicate semantic bundles earn no extra credit."""
    admitted = []
    seen = set()
    active_techs = set(card.get("active_techniques") or ())
    for slot in card.get("synchronized_capabilities") or ():
        caps = slot.get("capabilities") or []
        if not caps or len(caps) != len(set(caps)):
            continue
        if any(c not in KNOWN_CAPABILITIES for c in caps):
            continue
        seq = slot.get("coordination_sequence")
        if seq is not None:
            if not isinstance(seq, (list, tuple)) or len(seq) < 2:
                continue
            if any(t not in active_techs for t in seq):
                continue
        sig = slot_signature(slot)
        if sig in seen:
            continue
        seen.add(sig)
        admitted.append(slot)
    return admitted


def option_supported(k, card, opt_id):
    """Verify that a selected dimension option is backed by the card's trained capabilities and active techniques."""
    if opt_id is None:
        return True
    if opt_id not in k.options:
        return False
    opt = k.options[opt_id]
    dim = opt["dimension"]
    tr = training(card)
    is_v2 = card.get("version") == "block-2"
    tech_table = (getattr(k, "techniques_v2", None) or k.techniques) if is_v2 else k.techniques
    active = {
        tid
        for tid in card.get("active_techniques", [])
        if tid in tech_table and (set(tech_table[tid]["required_capabilities"]) & tr)
    }
    trefs = opt["technique_refs"]
    v1_ok = False
    if dim == "tie":
        tie_trefs = [tid for tid in trefs if tid != "body_hook"]
        v1_ok = any(tid in active for tid in tie_trefs)
    elif dim == "kicking":
        if opt_id == "kicking.none":
            v1_ok = bool(active)
        elif opt_id == "kicking.sanda" and "sanda_sweep" in active:
            v1_ok = True
        else:
            kick_trefs = [tid for tid in trefs if tid in tech_table and tech_table[tid]["kind"] == "kick"]
            v1_ok = any(tid in active for tid in kick_trefs)
    elif opt_id in OPTION_REQUIRED_TECHS:
        v1_ok = bool(OPTION_REQUIRED_TECHS[opt_id] & active)
    elif any(tid in active for tid in trefs):
        v1_ok = True
    elif opt_id in UNTRAINED_PUNCH_OPTIONS and "untrained_striking" in tr and "haymaker" in active:
        v1_ok = True
    if v1_ok:
        return True
    if is_v2:
        sup = getattr(k, "option_supported_by_v2", {}).get(opt_id, set())
        return bool(sup & active)
    return False


def resolved_dimensions(k, card):
    """Resolve supported dimension options; unsupported labels downgrade to None."""
    return {
        dim: (opt_id if option_supported(k, card, opt_id) else None)
        for dim, opt_id in card["dimensions"].items()
    }


def available(k, card, ruleset, activated=()):
    tids = set(card["active_techniques"])
    tids.update(t for a in card["conditional_abilities"] if a["id"] in activated for t in a["techniques"])
    caps = training(card, activated)
    return {tid for tid in tids if ruleset in k.techniques[tid]["ruleset_legality"]
            and set(k.techniques[tid]["required_capabilities"]) & caps}


def reachable(k, attacker, victim, ruleset):
    """Return evidence for potential access, never a claim that the attack has landed.

    Standing adjacent range steps are basic movement. Ground access needs a trained
    entry; an unattached bottom submission alone cannot create ground access.
    """
    tids = available(k, attacker, ruleset)
    has_ground_entry = any(k.techniques[t]["kind"] == "takedown" for t in tids)
    dims = resolved_dimensions(k, victim)
    canonical_debts = [
        d for opt_id in dims.values() if opt_id for d in k.options[opt_id]["exploitable_debt_ids"]
    ]
    seams = list(dict.fromkeys([d for d in victim.get("exploitable_seams", []) if d in k.debts] + canonical_debts))
    reports = []
    for did in seams:
        debt = k.debts[did]
        usable = [t for t in debt["technique_ids"] if t in tids]
        in_rules = ruleset in debt["ruleset"]
        ground_ok = debt["required_range"] != "ground" or has_ground_entry
        ok = bool(usable) and in_rules and ground_ok
        reports.append({"debt_id": did, "victim_id": victim["fighter_id"], "attacker_id": attacker["fighter_id"],
                        "opening": debt["opening"], "reachable": ok, "technique_ids": usable,
                        "required_range": debt["required_range"],
                        "path": ["adjacent standing steps", "trained ground entry"] if debt["required_range"] == "ground" else ["adjacent standing steps"],
                        "mechanism": debt["mechanical_tradeoff"],
                        "reason": "Trained technique and a legal access path exist; opponent can still deny access." if ok else
                        "Illegal under ruleset." if not in_rules else "No ground entry." if not ground_ok else "Required technique is not active."})
    return reports


def null_seams(k, attacker, victim, ruleset):
    """A single penalty per missing dimension, regardless of number of attacks."""
    legal_dims = k.model["rulesets"][ruleset]["dimensions"]
    tids = available(k, attacker, ruleset)
    dims = resolved_dimensions(k, victim)
    result = []
    for dim, selected in dims.items():
        if selected is not None:
            continue
        candidates = []
        for tid in sorted(tids):
            t = k.techniques[tid]
            if dim == "tie" and t["kind"] in ["takedown", "grip"]:
                if t["required_body_configuration"]["grip"] is None:
                    candidates.append(tid)
            elif dim in ["hands", "defense"] and t["kind"] == "punch":
                candidates.append(tid)
            elif dim == "stance" and t["kind"] in ["kick", "takedown"]:
                candidates.append(tid)
        relevant = dim in legal_dims
        result.append({"victim_id": victim["fighter_id"], "attacker_id": attacker["fighter_id"],
                       "dimension": dim, "reachable": relevant and bool(candidates),
                       "technique_ids": candidates if relevant else [],
                       "required_range": k.techniques[candidates[0]]["required_range"][0] if candidates else None,
                       "reason": "Legal trained entry can reach an initially uncovered capability." if relevant and candidates else
                       "Dimension unavailable in this ruleset." if not relevant else "Opponent has no legal trained entry.",
                       "conditional_mitigations": [a["id"] for a in victim["conditional_abilities"]]})
    return result


def compatibility(k, card):
    dims = resolved_dimensions(k, card)
    selected = [k.options[i] for i in dims.values() if i]
    result = []
    for n, a in enumerate(selected):
        for b in selected[n + 1:]:
            shared = sorted(set(a["preferred_ranges"]) & set(b["preferred_ranges"]))
            result.append({"fighter_id": card["fighter_id"], "options": [a["id"], b["id"]],
                           "shared_ranges": shared, "status": "shared range" if shared else "transition required",
                           "effect": "Sequence the two trained expressions after recovery." if shared else
                           "Move through adjacent ranges; no simultaneous range bonus.", "additional_logit": 0})
    return result


def admit_ranked_result(record):
    """Consumer-boundary guard: reject conditional narrative outputs and uncalibrated predictions as empirical ranked outcomes."""
    if not isinstance(record, dict):
        raise ValueError("ranked result must be a structured record")
    if "events" in record or "selection" in record or "final_state" in record:
        raise ValueError("conditional fight plan / narrative choreography cannot be ingested as an empirical ranked result")
    if "probability_a" in record or "matrix_edges" in record:
        raise ValueError("uncalibrated matchup prediction cannot be ingested as an empirical ranked result")
    mode = record.get("mode") or record.get("origin")
    if mode in {"predictive", "director-controlled", "director", "narrative", "simulated"}:
        raise ValueError("narrative or director-selected outcomes are ineligible for empirical ranking")
    if record.get("origin") != "independent_adjudicated_match" or not record.get("result_id") or not record.get("ruleset"):
        raise ValueError("empirical ranking requires an independently adjudicated match record with result_id and ruleset")
    return True
