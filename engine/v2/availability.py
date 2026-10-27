"""Technique availability, slot pools (§6.0.3), and conditional abilities for BLOCK Simulator v2."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

from ..capabilities import training
from ..ontology import Knowledge
from .data import KIND_ESCAPE, load_capabilities_v2, load_rulesets_v2, load_techniques_v2

_CAP_INDEX_CACHE: dict[str, tuple[dict[str, set[str]], dict[str, set[str]], dict[str, set[str]]]] = {}


def _get_cap_indexes(root: Path) -> tuple[dict[str, set[str]], dict[str, set[str]], dict[str, set[str]]]:
    key = str(root.resolve())
    cached = _CAP_INDEX_CACHE.get(key)
    if cached is not None:
        return cached
    techs = load_techniques_v2(root)
    caps_v2 = load_capabilities_v2(root).get("capabilities", {})
    grants_by_cap: dict[str, set[str]] = {}
    def_grants_by_cap: dict[str, set[str]] = {}
    core_by_cap: dict[str, set[str]] = {}
    all_tids = set(techs.keys())
    for cid, cinfo in caps_v2.items():
        core_by_cap[cid] = set(cinfo.get("core", [])) & all_tids
        grants_by_cap[cid] = set()
        def_grants_by_cap[cid] = set()
    for tid, t in techs.items():
        is_def = t["kind"] == "defense" or t.get("usage") == "defense"
        for cap in t.get("required_capabilities", []):
            grants_by_cap.setdefault(cap, set()).add(tid)
            if is_def:
                def_grants_by_cap.setdefault(cap, set()).add(tid)
    res = (grants_by_cap, def_grants_by_cap, core_by_cap)
    _CAP_INDEX_CACHE[key] = res
    return res


def available_v2(
    k: Knowledge,
    card: dict[str, Any],
    ruleset: str = "mma",
    activated: Iterable[str] = (),
) -> set[str]:
    """Return the fighter's legal v2 technique set under §6.0 (cores + trained active attacks + trained defenses)."""
    techs = load_techniques_v2(k.root)
    rulesets_v2 = load_rulesets_v2(k.root).get("rulesets", {})
    grants_by_cap, def_grants_by_cap, core_by_cap = _get_cap_indexes(k.root)

    activated_set = set(activated)
    trained = training(card, activated_set)
    active = set(card.get("active_techniques", []))
    if activated_set:
        active.update(
            t
            for a in card.get("conditional_abilities", [])
            if a.get("id") in activated_set
            for t in a.get("techniques", [])
        )

    out: set[str] = set()
    for cap in trained:
        g = grants_by_cap.get(cap, set())
        out |= core_by_cap.get(cap, set()) | (g & active) | def_grants_by_cap.get(cap, set())

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


def slot_pool_v2(
    k: Knowledge,
    card: dict[str, Any],
    slot_caps: Iterable[str],
    ruleset: str = "mma",
    activated: Iterable[str] = (),
) -> set[str]:
    """Return the active slot's legal attacking/movement pool (§6.0.3, D19)."""
    techs = load_techniques_v2(k.root)
    grants_by_cap, _, core_by_cap = _get_cap_indexes(k.root)
    avail = available_v2(k, card, ruleset, activated)

    activated_set = set(activated)
    active = set(card.get("active_techniques", []))
    unlocked_caps: set[str] = set()
    if activated_set:
        for a in card.get("conditional_abilities", []):
            if a.get("id") in activated_set:
                active.update(a.get("techniques", []))
                if a.get("grants_capability"):
                    unlocked_caps.add(str(a["grants_capability"]))

    eff_caps = set(slot_caps) | unlocked_caps
    pool: set[str] = set(core_by_cap.get("basic_movement", set()))
    for cap in eff_caps:
        g = grants_by_cap.get(cap, set())
        pool |= core_by_cap.get(cap, set()) | (g & active)

    return {
        tid
        for tid in (pool & avail)
        if techs[tid]["kind"] != "defense" and techs[tid].get("usage") != "defense"
    }


def slot_defense_pool_v2(
    k: Knowledge,
    card: dict[str, Any],
    slot_caps: Iterable[str],
    ruleset: str = "mma",
    activated: Iterable[str] = (),
) -> set[str]:
    """Return the legal defense/escape techniques granted by slot_caps (used by reset_to_home_range slots)."""
    techs = load_techniques_v2(k.root)
    grants_by_cap, _, _ = _get_cap_indexes(k.root)
    avail = available_v2(k, card, ruleset, activated)
    out: set[str] = set()
    for cap in set(slot_caps):
        for tid in grants_by_cap.get(cap, set()) & avail:
            t = techs[tid]
            if t["kind"] in ("defense", KIND_ESCAPE) or t.get("usage") == "defense":
                out.add(tid)
    return out


def evaluate_conditional_abilities(
    card: dict[str, Any],
    actor_state: dict[str, Any],
    opp_state: dict[str, Any],
    range_band: str,
) -> list[str]:
    """Check conditional_abilities gates against current fight state and unlock any newly satisfied abilities (§7.5)."""
    conds = card.get("conditional_abilities")
    if not conds:
        return []
    unlocked: list[str] = list(actor_state.get("unlocked_abilities", []))
    newly_unlocked: list[str] = []
    setups = set(actor_state.get("setups", []))

    for ab in conds:
        ab_id = str(ab.get("id", ""))
        if not ab_id or ab_id in unlocked or not ab.get("trained", False):
            continue
        gates = ab.get("gates") or {}
        if "range" in gates and range_band != gates["range"]:
            continue
        if "wall" in gates:
            req_wall = gates["wall"]
            if actor_state.get("wall_proximity") != req_wall and opp_state.get("wall_proximity") != req_wall:
                continue
        if "previous_setup" in gates and gates["previous_setup"] not in setups:
            continue
        unlocked.append(ab_id)
        newly_unlocked.append(ab_id)

    if newly_unlocked:
        actor_state["unlocked_abilities"] = unlocked
    return newly_unlocked
