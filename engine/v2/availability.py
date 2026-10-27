"""Technique availability calculation for BLOCK Simulator v2 (§6.0)."""

from __future__ import annotations

from typing import Any, Iterable

from ..capabilities import training
from ..ontology import Knowledge
from .data import load_capabilities_v2, load_rulesets_v2, load_techniques_v2


def available_v2(
    k: Knowledge,
    card: dict[str, Any],
    ruleset: str = "mma",
    activated: Iterable[str] = (),
) -> set[str]:
    """Return the fighter's legal v2 technique set under §6.0 (cores + trained active attacks + trained defenses)."""
    techs = load_techniques_v2(k.root)
    caps_v2 = load_capabilities_v2(k.root).get("capabilities", {})
    rulesets_v2 = load_rulesets_v2(k.root).get("rulesets", {})

    activated_set = set(activated)
    trained = training(card, activated_set)
    active = set(card.get("active_techniques", []))
    active.update(
        t
        for a in card.get("conditional_abilities", [])
        if a.get("id") in activated_set
        for t in a.get("techniques", [])
    )

    out: set[str] = set()
    for cap in trained:
        grants = {tid for tid, t in techs.items() if cap in t.get("required_capabilities", [])}
        core = set(caps_v2.get(cap, {}).get("core", [])) & set(techs.keys())
        out |= core | (grants & active)
        out |= {
            tid
            for tid in grants
            if techs[tid]["kind"] == "defense" or techs[tid].get("usage") == "defense"
        }

    if ruleset in rulesets_v2:
        r_cfg = rulesets_v2[ruleset]
        legal_kinds = set(r_cfg.get("legal_kinds", []))
        allowed_tids = set(r_cfg.get("allowed_techniques", []))
        banned_tids = set(r_cfg.get("banned_techniques", []))
        return {
            tid
            for tid in out
            if tid in techs
            and tid not in banned_tids
            and (techs[tid]["kind"] in legal_kinds or tid in allowed_tids)
            and ruleset in techs[tid].get("legal_in", [])
        }
    return {tid for tid in out if tid in techs and ruleset in techs[tid].get("legal_in", [])}
