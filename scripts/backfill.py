"""Restore only missing BLOCK release content; preserve and report authored conflicts."""
import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from engine.ontology import ROOT, read, write
from engine.audit import audit

BLOCK_OWNED_PREFIXES = (
    "cards/",
    "data/",
    "schemas/",
    "engine/",
    "docs/model.md",
    "docs/llm_reasoning_guide.md",
    "tests/conftest.py",
    "tests/test_",
)
BLOCK_OWNED_EXACT = {
    "predict.py",
    "plan_fight.py",
    "pyproject.toml",
    "requirements.txt",
    "scripts/__init__.py",
    "scripts/audit_coverage.py",
    "scripts/backfill.py",
    "scripts/regress.py",
    "scripts/validate_data.py",
}


def is_block_owned(relative: str) -> bool:
    rel = relative.replace("\\", "/")
    return rel in BLOCK_OWNED_EXACT or rel.startswith(BLOCK_OWNED_PREFIXES)


def backfill(root=ROOT, apply=False):
    root = Path(root)
    bundle = read(root / "resources/recovery.json")
    changes, conflicts = [], []

    def fill(live, source, pointer, file):
        if isinstance(source, dict) and isinstance(live, dict):
            result = copy.deepcopy(live)
            if "version" in source and live.get("version", source["version"]) != source["version"]:
                conflicts.append({"file": file, "pointer": pointer + "/version", "live": live["version"], "release": source["version"], "resolution": "blocked: incompatible release version"})
                return live
            for key, value in source.items():
                ptr = pointer + "/" + key
                if key not in live or live[key] == "" or (live[key] is None and not pointer.endswith("/dimensions") and value is not None):
                    result[key] = copy.deepcopy(value)
                    changes.append({"file": file, "pointer": ptr, "operation": "restore missing field", "provenance": bundle["version"]})
                else:
                    result[key] = fill(live[key], value, ptr, file)
            return result
        if isinstance(source, list) and isinstance(live, list):
            if source and all(isinstance(v, dict) and "id" in v for v in source):
                result = copy.deepcopy(live)
                source_by_id = {x["id"]: x for x in source}
                positions = {x.get("id"): i for i, x in enumerate(result) if isinstance(x, dict)}
                for ident, value in source_by_id.items():
                    if ident not in positions:
                        result.append(copy.deepcopy(value))
                        changes.append({"file": file, "pointer": pointer + "/" + ident, "operation": "restore missing record", "provenance": bundle["version"]})
                    else:
                        result[positions[ident]] = fill(result[positions[ident]], value, pointer + "/" + ident, file)
                # Release order is used for canonical IDs; new authored records retain order afterward.
                return sorted(result, key=lambda x: list(source_by_id).index(x["id"]) if isinstance(x, dict) and x.get("id") in source_by_id else len(source_by_id))
            if not live and source:
                changes.append({"file": file, "pointer": pointer, "operation": "restore empty required list", "provenance": bundle["version"]})
                return copy.deepcopy(source)
        if live != source:
            conflicts.append({"file": file, "pointer": pointer, "live": live, "release": source, "resolution": "preserve authored value; validate live content"})
        return live

    for relative, record in bundle["files"].items():
        if not is_block_owned(relative):
            continue
        path = root / relative
        if path.resolve().is_relative_to(root.resolve()) is False:
            raise ValueError("recovery path escapes project")
        source = record["content"]
        encoded = json.dumps(source, sort_keys=True, ensure_ascii=False).encode()
        if hashlib.sha256(encoded).hexdigest() != record["sha256"]:
            raise ValueError("recovery content digest mismatch: " + relative)
        if not path.exists():
            changes.append({"file": relative, "operation": "restore missing release file", "provenance": bundle["version"]})
            if apply:
                path.parent.mkdir(parents=True, exist_ok=True)
                if record["format"] == "json":
                    write(path, source)
                else:
                    atomic_text(path, source)
            continue
        # Existing executable code, docs and tests are never rewritten. Recovery
        # supplies absent files only. JSON merges fill holes without replacing canon.
        if record["format"] != "json":
            if path.read_text() != source:
                conflicts.append({"file": relative, "resolution": "preserve existing file", "release_sha256": record["sha256"]})
            continue
        try:
            live = read(path)
        except (ValueError, OSError) as exc:
            conflicts.append({"file": relative, "resolution": "blocked: invalid JSON preserved", "error": str(exc)})
            continue
        merged = fill(live, source, "", relative)
        if apply and merged != live:
            write(path, merged)
    result = {"mode": "apply" if apply else "dry-run", "release": bundle["version"], "change_count": len(changes), "changes": changes,
              "conflicts": conflicts, "procedure": ["INVENTORY", "DETECT GAPS", "CLASSIFY", "RESEARCH/DERIVE", "BACKFILL", "VALIDATE", "RECHECK"]}
    if apply:
        integrity = audit(root)
        result["validation"] = integrity["status"]
        write(root / "reports/backfill_changes.json", result)
        write(root / "reports/unresolved_conflicts.json", {"conflicts": conflicts, "mandatory_errors": integrity["errors"]})
        save_reports(root, integrity)
    return result


def atomic_text(path, text):
    import os
    import tempfile
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".block-")
    try:
        with os.fdopen(fd, "w") as stream:
            stream.write(text)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def save_reports(root, integrity):
    write(root / "reports/backfill_coverage.json", integrity)
    write(root / "reports/final_integrity_report.json", integrity)
    write(root / "reports/provenance_audit.json", {"status": integrity["status"], "classification_policy": integrity.get("provenance"), "errors": [e for e in integrity["errors"] if any(w in e for w in ["source", "claim", "provenance", "verified"])]})


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=ROOT)
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--verify", action="store_true")
    args = p.parse_args()
    if args.verify:
        result = audit(args.root)
        save_reports(args.root, result)
        code = 0 if result["status"] == "PASS" else 1
    else:
        result = backfill(args.root, args.apply)
        code = 1 if result.get("validation") == "FAIL" or any(c.get("resolution", "").startswith("blocked:") for c in result["conflicts"]) else 0
    print(json.dumps(result, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
