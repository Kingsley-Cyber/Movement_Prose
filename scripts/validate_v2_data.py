#!/usr/bin/env python3
"""Read-only validator for BLOCK Simulator v2 data files, schemas, cross-references, and cards (§6.10, D15)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import jsonschema

ROOT = Path(__file__).resolve().parent.parent


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_all(root: Path = ROOT, verbose: bool = True) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []

    core_pairs = [
        ("data/option_behaviors.json", "schemas/option_behavior.schema.json"),
        ("data/techniques_v2.json", "schemas/technique_v2.schema.json"),
        ("data/positions.json", "schemas/position_map.schema.json"),
        ("data/model_v2.json", "schemas/model_config_v2.schema.json"),
    ]
    v21_pairs = [
        ("data/rulesets_v2.json", "schemas/rulesets_v2.schema.json"),
        ("data/combinations_v2.json", "schemas/combinations_v2.schema.json"),
        ("data/debt_registry_v2.json", "schemas/debt_registry_v2.schema.json"),
        ("data/capabilities_v2.json", "schemas/capabilities_v2.schema.json"),
    ]

    validated_files = 0
    for d_rel, s_rel in core_pairs:
        d_path, s_path = root / d_rel, root / s_rel
        if not d_path.exists() or not s_path.exists():
            errors.append(f"Missing required core file or schema: {d_rel} / {s_rel}")
            continue
        jsonschema.validate(_load(d_path), _load(s_path))
        validated_files += 1

    has_v21_seed = all((root / d_rel).exists() and (root / s_rel).exists() for d_rel, s_rel in v21_pairs)
    for d_rel, s_rel in v21_pairs:
        d_path, s_path = root / d_rel, root / s_rel
        if d_path.exists() and s_path.exists():
            jsonschema.validate(_load(d_path), _load(s_path))
            validated_files += 1

    # Validate v2 and v1 cards against fighter_card_v2.schema.json
    card_schema = _load(root / "schemas" / "fighter_card_v2.schema.json")
    v2_cards = sorted((root / "cards" / "v2").glob("*.json"))
    v1_cards = sorted((root / "cards").glob("*.json"))
    if len(v2_cards) != 12:
        errors.append(f"Expected 12 v2 cards in cards/v2/, found {len(v2_cards)}")
    if len(v1_cards) != 11:
        errors.append(f"Expected 11 v1 cards in cards/, found {len(v1_cards)}")
    for cpath in v2_cards + v1_cards:
        jsonschema.validate(_load(cpath), card_schema)

    # Validate style templates when v2.1 seed schemas are active
    tpl_dir = root / "handoff_seed" / "style_templates"
    if has_v21_seed and tpl_dir.exists():
        for tpath in sorted(tpl_dir.glob("*.json")):
            jsonschema.validate(_load(tpath), card_schema)

    opt_data = _load(root / "data" / "option_behaviors.json")
    if len(opt_data.get("options", [])) != 57:
        errors.append(f"Expected 57 options in option_behaviors.json, found {len(opt_data.get('options', []))}")

    tech_data = _load(root / "data" / "techniques_v2.json")
    tech_map = {t["id"]: t for t in tech_data.get("techniques", [])}
    pos_data = _load(root / "data" / "positions.json")
    pos_map = {p["id"]: p for p in pos_data.get("positions", [])}

    # Cross-reference checks when v2.1 seed files are present (P1b+)
    if has_v21_seed:
        cap_data = _load(root / "data" / "capabilities_v2.json")
        caps_map = cap_data.get("capabilities", {})
        rulesets_data = _load(root / "data" / "rulesets_v2.json").get("rulesets", {})
        combos_data = _load(root / "data" / "combinations_v2.json").get("chains", [])
        debts_v2 = _load(root / "data" / "debt_registry_v2.json").get("debts", {})

        # 1. Every technique required_capabilities in capabilities_v2
        for tid, t in tech_map.items():
            for req_cap in t.get("required_capabilities", []):
                if req_cap not in caps_map:
                    errors.append(f"Technique {tid} references unknown capability {req_cap}")
            res_pos = t.get("result_position")
            if res_pos and res_pos not in pos_map:
                errors.append(f"Technique {tid} references unknown result_position {res_pos}")
            for req_pos in t.get("required_position", []):
                if req_pos not in pos_map:
                    errors.append(f"Technique {tid} references unknown required_position {req_pos}")

            # 2. Check legal_in matches rulesets_v2 derivation
            derived_legal = []
            for r_id, r_cfg in rulesets_data.items():
                if tid in r_cfg.get("illegal_techniques", []):
                    continue
                if t["kind"] in r_cfg.get("allowed_kinds", []):
                    derived_legal.append(r_id)
            if set(t.get("legal_in", [])) != set(derived_legal):
                errors.append(
                    f"Technique {tid} legal_in {t.get('legal_in')} != derived {derived_legal}"
                )

        # 3. Every capability core/grant technique exists in techniques_v2
        all_cap_techs: set[str] = set()
        for cid, cinfo in caps_map.items():
            for tid in cinfo.get("core_techniques", []) + cinfo.get("granted_techniques", []):
                all_cap_techs.add(tid)
                if tid not in tech_map:
                    errors.append(f"Capability {cid} references unknown technique {tid}")

        for tid in tech_map:
            if tid not in all_cap_techs:
                errors.append(f"Technique {tid} is not in any capability's core_techniques or granted_techniques")

        # 4. Option defense lists and supported_by_v2 reference valid techniques
        for opt in opt_data.get("options", []):
            oid = opt["id"]
            for tid in opt.get("supported_by_v2", []):
                if tid not in tech_map:
                    errors.append(f"Option {oid} supported_by_v2 references unknown technique {tid}")
            nd = opt.get("native_defense", {})
            for section in ("by_class", "at_wall"):
                for cls_name, entries in nd.get(section, {}).items():
                    for entry in entries:
                        t_ref = entry["technique"] if isinstance(entry, dict) else entry
                        if t_ref not in tech_map:
                            errors.append(f"Option {oid} native_defense.{section}.{cls_name} unknown technique {t_ref}")
                        elif tech_map[t_ref]["kind"] not in ("defense", "movement"):
                            errors.append(
                                f"Option {oid} native_defense.{section}.{cls_name} technique {t_ref} has kind {tech_map[t_ref]['kind']}"
                            )
            for prep_key in ("defense_prepend", "kick_defense_prepend"):
                for cls_name, entries in opt.get(prep_key, {}).items():
                    for t_ref in entries:
                        if t_ref not in tech_map:
                            errors.append(f"Option {oid} {prep_key}.{cls_name} unknown technique {t_ref}")

        # 5. Combinations reference valid capabilities and techniques
        for ch in combos_data:
            cid = ch["id"]
            if ch["school"] not in caps_map:
                errors.append(f"Combination {cid} references unknown school {ch['school']}")
            for tid in ch.get("sequence", []):
                if tid not in tech_map:
                    errors.append(f"Combination {cid} references unknown technique {tid}")

        # 6. Debt registry v2 references valid techniques
        base_debts = {d["id"] for d in _load(root / "data" / "debt_registry.json").get("debts", [])}
        for did, dinfo in debts_v2.items():
            if did not in base_debts:
                errors.append(f"debt_registry_v2 {did} not found in data/debt_registry.json")
            for tid in dinfo.get("v2_Recommended_technique_ids", []):
                if tid not in tech_map:
                    errors.append(f"debt_registry_v2 {did} references unknown technique {tid}")

        # 7. Positions transitions reference valid positions and techniques
        for pid, pinfo in pos_map.items():
            for tr in pinfo.get("transitions", []):
                for target_key in ("to", "on_fail", "via_outcome"):
                    t_pos = tr.get(target_key)
                    if t_pos and t_pos not in pos_map:
                        errors.append(f"Position {pid} transition {target_key} references unknown position {t_pos}")
                for tid in tr.get("by_techniques", []):
                    if tid not in tech_map:
                        errors.append(f"Position {pid} transition references unknown technique {tid}")

        # 8. Card slot validator warnings (§7.1.1)
        for cpath in v2_cards:
            c = _load(cpath)
            fid = c["fighter_id"]
            card_caps = set(c.get("baseline_capabilities", []))
            for s in c.get("synchronized_capabilities", []):
                card_caps.update(s.get("capabilities", []))
            card_grants: set[str] = set()
            for cap_id in card_caps | {"basic_movement"}:
                cinfo = caps_map.get(cap_id, {})
                card_grants.update(cinfo.get("core_techniques", []))
                card_grants.update(cinfo.get("granted_techniques", []))
            for tid in c.get("active_techniques", []):
                if tid not in tech_map:
                    errors.append(f"Card {fid} active_technique {tid} not in techniques_v2.json")
                elif tid not in card_grants:
                    warnings.append(f"Card {fid} active_technique {tid} not granted by any card capability")
            for s in c.get("synchronized_capabilities", []):
                sid = s["id"]
                s_caps = set(s.get("capabilities", [])) | {"basic_movement"}
                s_grants: set[str] = set()
                for cap_id in s_caps:
                    cinfo = caps_map.get(cap_id, {})
                    s_grants.update(cinfo.get("core_techniques", []))
                    s_grants.update(cinfo.get("granted_techniques", []))
                for tid in s.get("sequence", []):
                    if tid not in s_grants:
                        warnings.append(f"Card {fid} slot {sid} sequence item '{tid}' is off-school for {sorted(s_caps)}")

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
    args = parser.parse_args(argv)
    res = validate_all(ROOT, verbose=not args.quiet)
    if args.show_warnings:
        for w in res["warnings"]:
            print(f"WARN: {w}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
