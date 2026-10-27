"""Data loaders, cached schema validators, and model constants for BLOCK Simulator v2."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import jsonschema

from ..ontology import ROOT

_JSON_CACHE: dict[str, dict[str, Any]] = {}
_VALIDATOR_CACHE: dict[str, Any] = {}


def load_json_cached(path: Path) -> dict[str, Any]:
    key = str(path)
    cached = _JSON_CACHE.get(key)
    if cached is None:
        resolved = path.resolve()
        cached = json.loads(resolved.read_text(encoding="utf-8"))
        _JSON_CACHE[key] = cached
        _JSON_CACHE[str(resolved)] = cached
    return cached


def validate_schema_cached(instance: dict[str, Any], schema_path: Path) -> None:
    key = str(schema_path)
    validator = _VALIDATOR_CACHE.get(key)
    if validator is None:
        resolved = schema_path.resolve()
        schema = load_json_cached(resolved)
        cls = jsonschema.validators.validator_for(schema)
        validator = cls(schema)
        _VALIDATOR_CACHE[key] = validator
        _VALIDATOR_CACHE[str(resolved)] = validator
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


def build_kick_ids(root: Path = ROOT) -> set[str]:
    model = load_model_v2(root)
    legacy_ids = set(model.get("legacy", {}).get("kick_ids", {}).get("value", []))
    techs = load_techniques_v2(root)
    return legacy_ids | {tid for tid, t in techs.items() if t.get("kind") in ("kick", "knee")}


_MODEL_INIT = load_model_v2(ROOT)
FPS: int = int(_MODEL_INIT.get("fps", 24))
LANES: tuple[str, ...] = tuple(_MODEL_INIT.get("lanes", ()))
MOVE_BASE_STATS: dict[str, dict[str, Any]] = build_move_base_stats(ROOT)
LANDING_QUALITY_MULT: dict[str, float] = {
    k: float(v) for k, v in _MODEL_INIT.get("landing_multipliers", {}).items()
}
ARENA_PRESETS: dict[str, dict[str, Any]] = dict(_MODEL_INIT.get("arena_presets", {}))
KICK_IDS: set[str] = build_kick_ids(ROOT)

OFFENSIVE_DIMS: set[str] = {"mentality", "kicking", "target"}
DEFENSIVE_DIMS: set[str] = {"defense", "hands", "tie"}
NEUTRAL_DIMS: set[str] = {"stance"}
KIND_ESCAPE: str = "escape"
KIND_DEFENSE: str = "defense"
KIND_MOVEMENT: str = "movement"
KIND_FEINT: str = "feint"
KIND_GROUND_STRIKE: str = "ground_strike"
TECH_RETREAT: str = "retreat"
TECH_STEP: str = "step"
TECH_SHOVE: str = "shove"
TECH_STAND_UP: str = "stand_up"
TECH_CLINCH_BREAK: str = "clinch_break"
TECH_FEINT: str = "feint"
TECH_GUARD_PULL: str = "guard_pull"
TECH_CUT_OFF_STEP: str = "cut_off_step"
TECH_KICK_CATCH: str = "kick_catch"
TECH_PUMMEL: str = "pummel"
TECH_SANDA_SWEEP: str = "sanda_sweep"
TECH_CAUGHT_KICK_DUMP: str = "caught_kick_dump"
TECH_COLLAR_TIE: str = "collar_tie"
TECH_UNDERHOOK: str = "underhook"
TECH_BODY_LOCK: str = "body_lock"
TECH_SUBMISSION_ESCAPE: str = "submission_escape"
TECH_SWITCH_STEP: str = "switch_step"
TECH_SWITCH_KICK: str = "switch_kick"
OPT_DEFAULT_DEFENSE: str = "defense.block_absorb"
