#!/usr/bin/env python3
"""Validate the adjacent anime seed and optional compiled examples, without generation.

Example selection intervals use [start_frame, end_frame): end_frame is exclusive.
The optional --db file is opened read-only. SQL execution tests use memory only.
"""

import argparse
import hashlib
import itertools
import json
import re
import sqlite3
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


COLUMNS = (
    "directive_id", "archetype", "sub_genre", "slot_id", "moment_type",
    "prompt_snippet", "negative_snippet", "mechanical_guidance",
)
SLOTS = {
    "subject_anchor", "environment", "primary_action", "secondary_motion",
    "temporal_cadence", "camera_optics", "lighting", "material_shading",
}
MOMENTS = {"anticipation", "execution", "impact", "recoil", "follow_through", "recovery"}
GENRES = {
    "shonen_impact", "cyberpunk_cqc", "mecha_aerobatics",
    "supernatural_speed", "grounded_martial_arts",
}
GLOBAL_SLOTS = {"camera_optics", "environment"}
ID_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")
PLACEHOLDER = re.compile(r"\{\s*[A-Za-z_][A-Za-z0-9_]*\s*\}")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def fingerprint(rows):
    ordered = sorted(rows, key=lambda row: row[0])
    return hashlib.sha256(json.dumps(ordered, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


def pass_test(report, name, details=None):
    report["tests"].append({"name": name, "result": "pass", "details": details})


def inspect_table(connection, expected_rows):
    columns = [row[1] for row in connection.execute("PRAGMA table_info(semantic_directives)")]
    require(columns == list(COLUMNS), f"Expected exactly these eight columns in order: {COLUMNS}; found {columns}")
    rows = connection.execute(
        "SELECT " + ", ".join(COLUMNS) + " FROM semantic_directives WHERE archetype='anime_action' ORDER BY directive_id"
    ).fetchall()
    expected = sorted(expected_rows, key=lambda row: row[0])
    require(len(rows) == len(expected), f"Database has {len(rows)} anime_action rows; expected {len(expected)}")
    for actual, wanted in zip(rows, expected):
        differences = [name for name, a, b in zip(COLUMNS, actual, wanted) if a != b]
        require(not differences, f"Database mismatch for {wanted[0]} in fields: {differences}")
    require(connection.execute("PRAGMA integrity_check").fetchall() == [("ok",)], "SQLite integrity_check failed")
    return fingerprint(rows)


def validate_catalog(base, report):
    document = read_json(base / "anime_directives.json")
    records = document["directives"] if isinstance(document, dict) else document
    require(isinstance(records, list) and len(records) == 64, "Expected exactly 64 directive records")
    sources_doc = read_json(base / "sources.json")
    sources = sources_doc["sources"]
    require(isinstance(sources, list), "sources.json must contain a sources array")
    source_ids = [item["source_id"] for item in sources]
    require(all(isinstance(value, str) and value.strip() for value in source_ids), "Empty or nontext source_id")
    require(len(source_ids) == len(set(source_ids)), "Duplicate source_id")
    source_ids = set(source_ids)
    by_id, guidance, expected_rows = {}, {}, []
    for row in records:
        require(isinstance(row, dict), "A directive must be an object")
        missing = set(COLUMNS) - row.keys()
        require(not missing, f"Missing directive fields: {sorted(missing)}")
        identifier = row["directive_id"]
        require(isinstance(identifier, str) and ID_PATTERN.fullmatch(identifier) and len(identifier) <= 64,
                f"Invalid snake_case identifier or length: {identifier!r}")
        require(identifier not in by_id, f"Duplicate directive_id: {identifier}")
        for key in COLUMNS:
            require(isinstance(row[key], str) and row[key].strip(), f"{identifier}: {key} must be nonempty text")
        for key in ("archetype", "sub_genre", "slot_id", "moment_type"):
            require(len(row[key]) <= 32, f"{identifier}: {key} exceeds 32 characters")
        require(row["archetype"] == "anime_action", f"{identifier}: unexpected archetype")
        require(row["sub_genre"] in GENRES, f"{identifier}: invalid sub_genre")
        require(row["slot_id"] in SLOTS, f"{identifier}: invalid slot_id")
        require(row["moment_type"] in MOMENTS, f"{identifier}: invalid moment_type")
        mechanics = json.loads(row["mechanical_guidance"])
        require(isinstance(mechanics, dict), f"{identifier}: mechanical_guidance must encode an object")
        references = mechanics.get("sources")
        require(isinstance(references, list) and references, f"{identifier}: missing source references")
        require(all(isinstance(value, str) and value in source_ids for value in references),
                f"{identifier}: unresolved source reference")
        conflicts = mechanics.get("conflicts_with", [])
        require(isinstance(conflicts, list) and all(isinstance(value, str) for value in conflicts),
                f"{identifier}: conflicts_with must be an array of IDs")
        by_id[identifier], guidance[identifier] = row, mechanics
        expected_rows.append(tuple(row[key] for key in COLUMNS))
    require(len(expected_rows) == len(set(expected_rows)), "Duplicate full directive rows")
    require(len({row[1:] for row in expected_rows}) == len(expected_rows), "Duplicate directive content under different IDs")
    for identifier, mechanics in guidance.items():
        for conflict in mechanics.get("conflicts_with", []):
            require(conflict in by_id and conflict != identifier, f"{identifier}: invalid conflict reference {conflict}")
    counts = Counter(row["slot_id"] for row in records)
    require(counts == Counter({slot: 8 for slot in SLOTS}), f"Expected 8 records per slot; found {dict(counts)}")
    matrix = {slot: Counter(row["moment_type"] for row in records if row["slot_id"] == slot) for slot in sorted(SLOTS)}
    for slot, moments in matrix.items():
        require(set(moments) == MOMENTS, f"{slot}: one or more moment types missing")
    report["coverage"] = {
        "records": len(records), "slots": dict(sorted(counts.items())),
        "moments": dict(sorted(Counter(row["moment_type"] for row in records).items())),
        "slot_moment_counts": {slot: dict(sorted(values.items())) for slot, values in matrix.items()},
    }
    report["canonical_content_sha256"] = fingerprint(expected_rows)
    pass_test(report, "catalog_contract", "64 unique rows; eight allowed slots with eight rows each; every slot covers all six moments; field types, lengths, enums, JSON, sources and declared conflict IDs checked")
    return by_id, guidance, expected_rows


def validate_sql(base, rows, report):
    script = (base / "seed_anime_directives.sql").read_text(encoding="utf-8")
    with sqlite3.connect(":memory:") as connection:
        connection.executescript(script)
        first = inspect_table(connection, rows)
        pass_test(report, "sql_first_ingestion", "Exact eight-column schema, every field matches canonical JSON, and integrity_check=ok")
        connection.executescript(script)
        second = inspect_table(connection, rows)
        require(first == second, "Content fingerprint changed on repeated ingestion")
        pass_test(report, "sql_repeat_ingestion", "All 64 rows and the complete content fingerprint remain identical")
        sentinel = (
            "validator_sentinel_other_archetype", "validator_other", "shonen_impact",
            "subject_anchor", "anticipation", "Sentinel positive text", "Sentinel negative text", '{"sentinel":true}',
        )
        connection.execute("INSERT INTO semantic_directives VALUES (?,?,?,?,?,?,?,?)", sentinel)
        connection.commit()
        connection.executescript(script)
        found = connection.execute(
            "SELECT " + ", ".join(COLUMNS) + " FROM semantic_directives WHERE directive_id=?", (sentinel[0],)
        ).fetchone()
        require(found == sentinel, "Seed changed or deleted the unrelated sentinel row")
        require(inspect_table(connection, rows) == first, "Anime content changed during sentinel preservation test")
        pass_test(report, "unrelated_row_preserved", "A preexisting row from another archetype survives seed ingestion byte-for-byte")


def validate_examples(base, by_id, guidance, report):
    path = base / "example_payloads.json"
    if not path.exists():
        report["tests"].append({"name": "compiled_examples", "result": "not_run", "details": "Optional example_payloads.json is absent"})
        return
    examples = read_json(path)["examples"]
    require(isinstance(examples, list) and examples, "examples must be a nonempty array")
    example_ids = set()
    selection_count = 0
    for example in examples:
        name = example["example_id"]
        require(isinstance(name, str) and name.strip() and name not in example_ids, "Missing or duplicate example_id")
        example_ids.add(name)
        require(example["moment_type"] in MOMENTS, f"{name}: invalid example moment_type")
        require(isinstance(example.get("require_all_slots"), bool), f"{name}: require_all_slots must be boolean")
        for field in ("compiled_positive_prompt", "compiled_negative_candidate"):
            text = example[field]
            require(isinstance(text, str), f"{name}: {field} must be text")
            require(not PLACEHOLDER.search(text), f"{name}: unresolved placeholder in {field}")
        require(example["compiled_positive_prompt"].strip(), f"{name}: compiled positive prompt is empty")
        selections = example["selections"]
        require(isinstance(selections, list) and selections, f"{name}: selections must be nonempty")
        for item in selections:
            identifier = item["directive_id"]
            require(identifier in by_id, f"{name}: unknown directive {identifier}")
            row = by_id[identifier]
            require(row["moment_type"] == example["moment_type"], f"{name}: moment mismatch for {identifier}")
            start, end = item["start_frame"], item["end_frame"]
            require(type(start) is int and type(end) is int and 0 <= start < end,
                    f"{name}: intervals must be integer [start_frame,end_frame) with 0 <= start < end")
            for key in ("actor_id", "target_id"):
                value = item.get(key)
                require(value is None or (isinstance(value, str) and value.strip() and not PLACEHOLDER.search(value)),
                        f"{name}: invalid {key}")
            for placeholder, binding in (("{actor}", "actor_id"), ("{target}", "target_id")):
                require(placeholder not in row["prompt_snippet"] or bool(item.get(binding)),
                        f"{name}: {identifier} requires {binding}")
        selected_slots = {by_id[item["directive_id"]]["slot_id"] for item in selections}
        if example["require_all_slots"]:
            require(selected_slots == SLOTS, f"{name}: expected all eight distinct slots")
        for left, right in itertools.combinations(selections, 2):
            if max(left["start_frame"], right["start_frame"]) >= min(left["end_frame"], right["end_frame"]):
                continue
            lid, rid = left["directive_id"], right["directive_id"]
            lslot, rslot = by_id[lid]["slot_id"], by_id[rid]["slot_id"]
            global_scope = lslot in GLOBAL_SLOTS or rslot in GLOBAL_SLOTS
            if lslot == rslot:
                require(not (global_scope or left.get("actor_id") == right.get("actor_id")),
                        f"{name}: simultaneous duplicate slot {lslot} for the same actor or global scope")
            declared_conflict = rid in guidance[lid].get("conflicts_with", []) or lid in guidance[rid].get("conflicts_with", [])
            left_entities = {left.get("actor_id"), left.get("target_id")} - {None, ""}
            right_entities = {right.get("actor_id"), right.get("target_id")} - {None, ""}
            if declared_conflict and (global_scope or left_entities.intersection(right_entities)):
                raise ValueError(f"{name}: declared conflict {lid} / {rid} overlaps in time and scope")
        selection_count += len(selections)
    pass_test(report, "compiled_examples", {
        "examples": len(examples), "selections": selection_count,
        "checks": "IDs, moment binding, required actor/target bindings, half-open frame intervals, required slot coverage, same-actor/global duplicate slots, unresolved named placeholders, and declared overlapping conflicts",
    })


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, help="Optional existing database to inspect read-only")
    parser.add_argument("--report", type=Path, help="Write the JSON report here; otherwise print it")
    args = parser.parse_args()
    base = Path(__file__).resolve().parent
    report = {
        "validator": "validate_anime_seed.py", "checked_at": datetime.now(timezone.utc).isoformat(),
        "sqlite_runtime_version": sqlite3.sqlite_version, "status": "running", "tests": [],
        "generation_tests_performed": False,
        "limits": [
            "These checks validate data, SQL behavior, declared composition rules, and optional database integrity. They do not prove anatomy, motion, rendering quality, or source truth.",
            "Conflict checks use authored conflict IDs, overlapping half-open frame intervals, and actor/target identities; camera and environment slots are treated as global within each example.",
            "The checker does not infer undeclared semantic conflicts or prove that compiled prose perfectly preserves every selected directive."
        ],
    }
    try:
        by_id, guidance, rows = validate_catalog(base, report)
        validate_sql(base, rows, report)
        validate_examples(base, by_id, guidance, report)
        if args.db:
            db = args.db.resolve()
            require(db.is_file(), f"Database does not exist: {db}")
            with sqlite3.connect(db.as_uri() + "?mode=ro", uri=True) as connection:
                connection.execute("PRAGMA query_only=ON")
                report["database_content_sha256"] = inspect_table(connection, rows)
            pass_test(report, "readonly_database", "Eight-column schema, complete canonical content, and integrity_check=ok; no database writes")
        report["status"] = "pass"
    except (KeyError, TypeError, ValueError, OSError, sqlite3.Error) as error:
        report["status"] = "fail"
        report["error"] = f"{type(error).__name__}: {error}"
    output = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(output, encoding="utf-8")
        print(json.dumps({"status": report["status"], "report": str(args.report.resolve()), "tests": len(report["tests"])}))
    else:
        sys.stdout.write(output)
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
