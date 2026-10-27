#!/usr/bin/env python3
"""Read-only validator for BLOCK Simulator v2 data files, schemas, cross-references, and cards (§6.1, §6.10, D15)."""

from __future__ import annotations

import argparse
import json
import sys
from collections import deque
from pathlib import Path
from typing import Any

import jsonschema

ROOT = Path(__file__).resolve().parent.parent


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def card_available_v2(
    card: dict[str, Any],
    tech_map: dict[str, dict[str, Any]],
    caps_map: dict[str, dict[str, Any]],
) -> tuple[set[str], set[str]]:
    trained = set(card.get("baseline_capabilities", [])) | {
        c for s in card.get("synchronized_capabilities", []) for c in s.get("capabilities", [])
    }
    active = set(card.get("active_techniques", []))
    out: set[str] = set()
    for cap in trained:
        grants = {tid for tid, t in tech_map.items() if cap in t.get("required_capabilities", [])}
        core = set(caps_map.get(cap, {}).get("core", [])) & set(tech_map.keys())
        out |= core | (grants & active)
        out |= {
            tid
            for tid in grants
            if tech_map[tid]["kind"] == "defense" or tech_map[tid].get("usage") == "defense"
        }
    return out, trained


def validate_card_slots(card: dict[str, Any], root: Path = ROOT) -> list[str]:
    """Validate a v2 fighter card's slots, sequences, triggers, links, and school_mastery (§6.1)."""
    tech_map = {t["id"]: t for t in _load(root / "data" / "techniques_v2.json").get("techniques", [])}
    caps_map = _load(root / "data" / "capabilities_v2.json").get("capabilities", {})
    model_cfg = _load(root / "data" / "model_v2.json")
    st_cfg = model_cfg.get("slot_triggers", {})
    predicates = set(st_cfg.get("predicates", []))
    stall_conditions = set(st_cfg.get("stall_conditions", []))
    modifiers = {cid for cid, cinfo in caps_map.items() if cinfo.get("modifier")}
    basic_grants = {tid for tid, t in tech_map.items() if "basic_movement" in t.get("required_capabilities", [])}

    problems: list[str] = []
    avail, trained = card_available_v2(card, tech_map, caps_map)
    slots = card.get("synchronized_capabilities", [])
    slot_ids = [s["id"] for s in slots]
    starts = [s["id"] for s in slots if s.get("trigger") == "fight_start"]
    if len(starts) != 1:
        problems.append(f"expected exactly one fight_start slot, found {starts}")

    pools: dict[str, frozenset[str]] = {}
    for s in slots:
        sid = s["id"]
        caps_ = set(s.get("capabilities", []))
        granted: set[str] = set()
        for cap in caps_ | {"basic_movement"}:
            granted |= {tid for tid, t in tech_map.items() if cap in t.get("required_capabilities", [])}
        attack_pool = {
            t
            for t in granted
            if t in avail
            and tech_map[t].get("usage") in ("attack", "both", "counter")
            and tech_map[t]["kind"] not in ("movement", "feint")
        }
        nonbasic = attack_pool - basic_grants
        reset = s.get("goal") == "reset_to_home_range"
        if reset:
            tools = {t for t in granted - basic_grants if tech_map[t]["kind"] in ("defense", "escape")}
            if len(tools) < 2:
                problems.append(f"{sid}: reset slot grants fewer than 2 defense/escape tools")
        elif len(nonbasic) < 2:
            problems.append(
                f"{sid}: slot grants fewer than 2 usable non-basic attacking techniques ({sorted(nonbasic)})"
            )
        if caps_ and caps_ <= modifiers:
            problems.append(f"{sid}: modifier capability without a school")
        for tid in s.get("sequence", []):
            if tid not in granted:
                problems.append(
                    f"{sid}: sequence item '{tid}' is not granted by the slot's capabilities {sorted(caps_)}"
                )
            elif tid not in avail:
                problems.append(
                    f"{sid}: sequence item '{tid}' is granted but not trained (not in active_techniques or a core)"
                )
        if s.get("trigger") and predicates and s["trigger"] not in predicates:
            problems.append(f"{sid}: unknown trigger '{s['trigger']}'")
        cond = (s.get("abandon_rule") or {}).get("condition")
        if cond and stall_conditions and cond not in stall_conditions:
            problems.append(f"{sid}: unknown abandon condition '{cond}'")
        for ln in s.get("links", []):
            if ln not in slot_ids:
                problems.append(f"{sid}: link '{ln}' is not a slot of this card")
        pools[sid] = frozenset(t for t in granted - basic_grants if t in avail and tech_map[t]["kind"] != "defense")

    level = {"novice": -1, "trained": 0, "expert": 1, "master": 2, "grandmaster": 3}
    cap_rank = level[card.get("rank", "trained")]
    for school, r in (card.get("school_mastery") or {}).items():
        if school not in trained:
            problems.append(f"school_mastery: '{school}' is not a capability this card trains")
        if level[r] > cap_rank:
            problems.append(
                f"school_mastery: '{school}' at {r} exceeds the card's rank {card.get('rank', 'trained')} (rank is a ceiling)"
            )

    seen: dict[frozenset[str], str] = {}
    for sid, pool in pools.items():
        if pool and pool in seen:
            problems.append(f"{sid}: identical non-basic technique pool (attacks + movement) to {seen[pool]}")
        seen.setdefault(pool, sid)
    return problems


def validate_all(root: Path = ROOT, verbose: bool = True, strict_slots: bool = False) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []

    pairs = [
        ("data/option_behaviors.json", "schemas/option_behavior.schema.json"),
        ("data/techniques_v2.json", "schemas/technique_v2.schema.json"),
        ("data/positions.json", "schemas/position_map.schema.json"),
        ("data/model_v2.json", "schemas/model_config_v2.schema.json"),
        ("data/rulesets_v2.json", "schemas/rulesets_v2.schema.json"),
        ("data/combinations_v2.json", "schemas/combinations_v2.schema.json"),
        ("data/debt_registry_v2.json", "schemas/debt_registry_v2.schema.json"),
        ("data/capabilities_v2.json", "schemas/capabilities_v2.schema.json"),
    ]

    validated_files = 0
    for d_rel, s_rel in pairs:
        d_path, s_path = root / d_rel, root / s_rel
        if not d_path.exists() or not s_path.exists():
            errors.append(f"Missing required file or schema: {d_rel} / {s_rel}")
            continue
        jsonschema.validate(_load(d_path), _load(s_path))
        validated_files += 1

    card_schema = _load(root / "schemas" / "fighter_card_v2.schema.json")
    v2_cards = sorted((root / "cards" / "v2").glob("*.json"))
    v1_cards = sorted((root / "cards").glob("*.json"))
    if len(v2_cards) != 12:
        errors.append(f"Expected 12 v2 cards in cards/v2/, found {len(v2_cards)}")
    if len(v1_cards) != 11:
        errors.append(f"Expected 11 v1 cards in cards/, found {len(v1_cards)}")
    for cpath in v2_cards + v1_cards:
        jsonschema.validate(_load(cpath), card_schema)

    tpl_dir = root / "handoff_seed" / "style_templates"
    if tpl_dir.exists():
        for tpath in sorted(tpl_dir.glob("*.json")):
            tcard = _load(tpath)
            jsonschema.validate(tcard, card_schema)
            t_probs = validate_card_slots(tcard, root)
            if t_probs:
                for p in t_probs:
                    errors.append(f"Style template {tpath.name}: {p}")

    opt_data = _load(root / "data" / "option_behaviors.json")
    if len(opt_data.get("options", [])) != 57:
        errors.append(f"Expected 57 options in option_behaviors.json, found {len(opt_data.get('options', []))}")

    tech_data = _load(root / "data" / "techniques_v2.json")
    tech_map = {t["id"]: t for t in tech_data.get("techniques", [])}
    pos_data = _load(root / "data" / "positions.json")
    pos_map = {p["id"]: p for p in pos_data.get("positions", [])}
    cap_data = _load(root / "data" / "capabilities_v2.json")
    caps_map = cap_data.get("capabilities", {})
    rulesets_data = _load(root / "data" / "rulesets_v2.json").get("rulesets", {})
    combos_data = _load(root / "data" / "combinations_v2.json").get("chains", [])
    debts_v2 = _load(root / "data" / "debt_registry_v2.json").get("debts", {})

    # 1. Technique cross-references & legal_in derivation
    for tid, t in tech_map.items():
        for req_cap in t.get("required_capabilities", []):
            if req_cap not in caps_map:
                errors.append(f"Technique {tid} references unknown capability {req_cap}")
        res_pos = t.get("result_position")
        if res_pos and res_pos not in pos_map:
            errors.append(f"Technique {tid} references unknown result_position {res_pos}")
        req_pos = t.get("requires_position")
        if req_pos:
            req_list = req_pos if isinstance(req_pos, list) else [req_pos]
            for rp in req_list:
                base_pos = str(rp).split(":", 1)[0]
                if base_pos not in pos_map and not base_pos.startswith("any_"):
                    errors.append(f"Technique {tid} references unknown requires_position {rp}")
        for c_tid in t.get("counters", []):
            if c_tid not in tech_map:
                errors.append(f"Technique {tid} counter references unknown technique {c_tid}")

        derived_legal = []
        for r_id, r_cfg in rulesets_data.items():
            if tid in r_cfg.get("banned_techniques", []):
                continue
            if t["kind"] in r_cfg.get("legal_kinds", []) or tid in r_cfg.get("allowed_techniques", []):
                derived_legal.append(r_id)
        if set(t.get("legal_in", [])) != set(derived_legal):
            errors.append(f"Technique {tid} legal_in {t.get('legal_in')} != derived {derived_legal}")

    # 2. Capabilities core & grants
    basic_set = {tid for tid, t in tech_map.items() if "basic_movement" in t.get("required_capabilities", [])}
    for cid, cinfo in caps_map.items():
        for tid in cinfo.get("core", []):
            if tid not in tech_map:
                errors.append(f"Capability {cid} core references unknown technique {tid}")
        grants = {tid for tid, t in tech_map.items() if cid in t.get("required_capabilities", [])}
        if not cinfo.get("modifier", False) and cid != "basic_movement":
            if len(grants - basic_set) < 2:
                errors.append(f"Capability {cid} grants fewer than 2 non-basic techniques: {sorted(grants - basic_set)}")
        for cls_name, entries in (cinfo.get("defense_prepend") or {}).items():
            for t_ref in entries:
                if t_ref not in tech_map:
                    errors.append(f"Capability {cid} defense_prepend.{cls_name} unknown technique {t_ref}")

    # 3. Option defense lists and supported_by_v2
    for opt in opt_data.get("options", []):
        oid = opt["id"]
        for tid in opt.get("supported_by_v2", []):
            if tid not in tech_map:
                errors.append(f"Option {oid} supported_by_v2 references unknown technique {tid}")
        nd = opt.get("native_defense") or {}
        for section in ("by_class", "at_wall"):
            for cls_name, entries in (nd.get(section) or {}).items():
                for entry in entries:
                    t_ref = entry["technique"] if isinstance(entry, dict) else entry
                    if t_ref not in tech_map:
                        errors.append(f"Option {oid} native_defense.{section}.{cls_name} unknown technique {t_ref}")
                    elif tech_map[t_ref]["kind"] not in ("defense", "movement", "escape"):
                        errors.append(
                            f"Option {oid} native_defense.{section}.{cls_name} technique {t_ref} has kind {tech_map[t_ref]['kind']}"
                        )
        for prep_key in ("defense_prepend", "kick_defense_prepend"):
            for cls_name, entries in (opt.get(prep_key) or {}).items():
                for t_ref in entries:
                    if t_ref not in tech_map:
                        errors.append(f"Option {oid} {prep_key}.{cls_name} unknown technique {t_ref}")

    # 4. Combinations
    for ch in combos_data:
        cid = ch["id"]
        if ch["school"] not in caps_map:
            errors.append(f"Combination {cid} references unknown school {ch['school']}")
        for tid in ch.get("sequence", []):
            if tid not in tech_map:
                errors.append(f"Combination {cid} references unknown technique {tid}")

    # 5. Debt registry v2
    base_debts = {d["id"] for d in _load(root / "data" / "debt_registry.json").get("debts", [])}
    debts_iter = (
        debts_v2.items()
        if isinstance(debts_v2, dict)
        else ((d.get("debt_id") or d.get("id"), d) for d in debts_v2)
    )
    for did, dinfo in debts_iter:
        if did not in base_debts:
            errors.append(f"debt_registry_v2 {did} not found in data/debt_registry.json")
        for tid in dinfo.get("add_technique_ids", []):
            if tid not in tech_map:
                errors.append(f"debt_registry_v2 {did} references unknown technique {tid}")

    # 6. Positions transitions & reachability from standing_neutral
    adj: dict[str, set[str]] = {pid: set() for pid in pos_map}
    for tr in pos_data.get("transitions", []):
        fp, tp, vt = tr.get("from_position"), tr.get("to_position"), tr.get("via_technique")
        if fp not in pos_map:
            errors.append(f"Position transition from_position unknown: {fp}")
        if tp not in pos_map:
            errors.append(f"Position transition to_position unknown: {tp}")
        if fp in pos_map and tp in pos_map:
            adj[fp].add(tp)
        if vt and vt not in tech_map:
            errors.append(f"Position transition {fp}->{tp} via_technique unknown: {vt}")
        for c_tid in tr.get("counters", []):
            if c_tid not in tech_map:
                errors.append(f"Position transition {fp}->{tp} counter unknown: {c_tid}")

    visited: set[str] = {"standing_neutral"}
    queue: deque[str] = deque(["standing_neutral"])
    while queue:
        cur = queue.popleft()
        for nxt in adj.get(cur, ()):
            if nxt not in visited:
                visited.add(nxt)
                queue.append(nxt)
    for pid, pinfo in pos_map.items():
        if pinfo.get("status") != "deprecated" and pid not in visited:
            errors.append(f"Position {pid} is not reachable from standing_neutral")

    # 7. Card slot validator (§6.1)
    for cpath in v2_cards:
        c = _load(cpath)
        fid = c["fighter_id"]
        probs = validate_card_slots(c, root)
        for p in probs:
            msg = f"{fid}: {p}"
            if strict_slots:
                errors.append(msg)
            else:
                warnings.append(msg)

    if errors:
        for e in errors:
            print(f"ERROR: {e}", file=sys.stderr)
        raise SystemExit(1)

    if verbose:
        print(
            f"validate_v2_data: PASS ({validated_files} data files, {len(v2_cards)} v2 cards, "
            f"{len(v1_cards)} v1 cards, {len(tech_map)} techniques, {len(pos_map)} positions, "
            f"{len(warnings)} slot/card warnings)."
        )
    return {"status": "PASS", "validated_files": validated_files, "warnings": warnings}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate BLOCK Simulator v2 data and schemas.")
    parser.add_argument("--quiet", action="store_true", help="Suppress summary line on success")
    parser.add_argument("--show-warnings", action="store_true", help="Print card/slot warnings")
    parser.add_argument("--strict-slots", action="store_true", help="Treat slot warnings on cards/v2 as errors")
    args = parser.parse_args(argv)
    res = validate_all(ROOT, verbose=not args.quiet, strict_slots=args.strict_slots)
    if args.show_warnings:
        for w in res["warnings"]:
            print(f"WARN: {w}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
