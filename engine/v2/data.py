"""Data loaders, cached schema validators, and model constants for BLOCK Simulator v2."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import jsonschema

from ..ontology import ROOT

_JSON_CACHE: dict[tuple[str, int], dict[str, Any]] = {}
_VALIDATOR_CACHE: dict[tuple[str, int], Any] = {}


def load_json_cached(path: Path) -> dict[str, Any]:
    resolved = path.resolve()
    mtime = resolved.stat().st_mtime_ns
    key = (str(resolved), mtime)
    cached = _JSON_CACHE.get(key)
    if cached is None:
        cached = json.loads(resolved.read_text(encoding="utf-8"))
        _JSON_CACHE[key] = cached
    return cached


def validate_schema_cached(instance: dict[str, Any], schema_path: Path) -> None:
    resolved = schema_path.resolve()
    mtime = resolved.stat().st_mtime_ns
    key = (str(resolved), mtime)
    validator = _VALIDATOR_CACHE.get(key)
    if validator is None:
        schema = load_json_cached(resolved)
        cls = jsonschema.validators.validator_for(schema)
        validator = cls(schema)
        _VALIDATOR_CACHE[key] = validator
    validator.validate(instance)


def load_model_v2(root: Path = ROOT) -> dict[str, Any]:
    path = root / "data" / "model_v2.json"
    if path.exists():
        return load_json_cached(path)
    return {}


def load_option_behaviors(root: Path = ROOT) -> dict[str, dict[str, Any]]:
    path = root / "data" / "option_behaviors.json"
    if not path.exists():
        return {}
    raw = load_json_cached(path)
    return {opt["id"]: opt for opt in raw.get("options", [])}


def load_techniques_v2(root: Path = ROOT) -> dict[str, dict[str, Any]]:
    path = root / "data" / "techniques_v2.json"
    if not path.exists():
        return {}
    raw = load_json_cached(path)
    return {t["id"]: t for t in raw.get("techniques", [])}


def load_positions_v2(root: Path = ROOT) -> dict[str, Any]:
    path = root / "data" / "positions.json"
    if not path.exists():
        return {}
    return load_json_cached(path)


def load_rulesets_v2(root: Path = ROOT) -> dict[str, Any]:
    path = root / "data" / "rulesets_v2.json"
    if not path.exists():
        return {}
    return load_json_cached(path)


def load_capabilities_v2(root: Path = ROOT) -> dict[str, Any]:
    path = root / "data" / "capabilities_v2.json"
    if not path.exists():
        return {}
    return load_json_cached(path)


def load_combinations_v2(root: Path = ROOT) -> dict[str, Any]:
    path = root / "data" / "combinations_v2.json"
    if not path.exists():
        return {}
    return load_json_cached(path)


def load_debt_registry_v2(root: Path = ROOT) -> dict[str, Any]:
    path = root / "data" / "debt_registry_v2.json"
    if not path.exists():
        return {}
    return load_json_cached(path)


def get_attack_profile(
    option_id: str | None,
    opt_behaviors: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    if not option_id or option_id not in opt_behaviors:
        return {}
    return opt_behaviors[option_id].get("attack_profile", {})


def build_move_base_stats(root: Path = ROOT) -> dict[str, dict[str, Any]]:
    """Build MOVE_BASE_STATS from data/techniques_v2.json and model.readiness.nonlane_lane_map."""
    model = load_model_v2(root)
    nonlane = model.get("readiness", {}).get("nonlane_lane_map", {})
    techs = load_techniques_v2(root)
    out: dict[str, dict[str, Any]] = {}
    for tid, t in techs.items():
        fc = t.get("frame_costs", {})
        raw_lane = str(t.get("attack_lane", "head_straight"))
        if raw_lane in nonlane:
            mapped = nonlane[raw_lane]
            lane = str(mapped) if mapped is not None else raw_lane
        else:
            lane = raw_lane
        entry: dict[str, Any] = {
            "base": float(t.get("base_damage", 0.0)),
            "type": str(t.get("damage_type", "impact")),
            "setup_f": int(fc.get("setup_frames", 4)),
            "exec_f": int(fc.get("execution_frames", 8)),
            "hold_f": int(fc.get("contact_hold_frames", 2)),
            "rec_f": int(fc.get("recovery_frames", 8)),
            "lane": lane,
        }
        vert_min = t.get("vertical_min", "grounded")
        if vert_min and vert_min != "grounded":
            entry["vertical"] = str(vert_min)
        out[tid] = entry
    return out


_MODEL_INIT = load_model_v2(ROOT)
FPS: int = int(_MODEL_INIT.get("fps", 24))
LANES: tuple[str, ...] = tuple(_MODEL_INIT.get("lanes", ()))
MOVE_BASE_STATS: dict[str, dict[str, Any]] = build_move_base_stats(ROOT)
LANDING_QUALITY_MULT: dict[str, float] = {
    k: float(v) for k, v in _MODEL_INIT.get("landing_multipliers", {}).items()
}
ARENA_PRESETS: dict[str, dict[str, Any]] = dict(_MODEL_INIT.get("arena_presets", {}))
KICK_IDS: set[str] = set(
    _MODEL_INIT.get("legacy", {}).get("kick_ids", {}).get("value", [])
)

OFFENSIVE_DIMS: set[str] = {"mentality", "kicking", "target"}
DEFENSIVE_DIMS: set[str] = {"defense", "hands", "tie"}
NEUTRAL_DIMS: set[str] = {"stance"}
