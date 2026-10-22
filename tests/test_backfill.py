import hashlib
from engine.audit import audit
from engine.ontology import read, write
from scripts.backfill import backfill


def contents(root):
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob("*") if p.is_file() and "reports" not in p.parts and "__pycache__" not in p.parts}


def test_dry_run_restoration_and_second_apply_are_idempotent(project_copy):
    idx = project_copy / "data/engine_index.json"
    data = read(idx)
    original_name = data["options"][0]["name"]
    del data["options"][0]["name"]
    data["options"].pop()
    write(idx, data)
    matrix = project_copy / "data/matchups.json"
    data = read(matrix)
    data["matrices"][0]["cells"].pop()
    write(matrix, data)
    mapping = project_copy / "data/pipeline.json"
    data = read(mapping)
    data["event_types"].pop()
    write(mapping, data)
    (project_copy / "schemas/fight_state.schema.json").unlink()
    before = contents(project_copy)
    dry = backfill(project_copy)
    assert dry["change_count"] and contents(project_copy) == before
    fixed = backfill(project_copy, apply=True)
    assert fixed["validation"] == "PASS"
    assert read(idx)["options"][0]["name"] == original_name
    assert audit(project_copy)["status"] == "PASS"
    first = contents(project_copy)
    second = backfill(project_copy, apply=True)
    assert second["change_count"] == 0 and contents(project_copy) == first


def test_authored_values_and_invalid_references_are_preserved_and_reported(project_copy):
    idx = project_copy / "data/engine_index.json"
    data = read(idx)
    data["options"][0]["description"] = "A deliberate authored revision retains provenance."
    write(idx, data)
    result = backfill(project_copy, apply=True)
    assert read(idx)["options"][0]["description"] == data["options"][0]["description"]
    assert any(c.get("pointer", "").endswith("/description") for c in result["conflicts"])
    card = project_copy / "cards/maleek.json"
    data = read(card)
    data["dimensions"]["hands"] = "hands.unverifiable"
    write(card, data)
    result = backfill(project_copy, apply=True)
    assert result["validation"] == "FAIL"
    assert read(card)["dimensions"]["hands"] == "hands.unverifiable"


def test_release_version_conflict_does_not_overwrite_live_canon(project_copy):
    path = project_copy / "data/model.json"
    data = read(path)
    data["version"] = "new_authored_version"
    write(path, data)
    result = backfill(project_copy, apply=True)
    assert read(path) == data
    assert any(c["resolution"].startswith("blocked:") for c in result["conflicts"])
