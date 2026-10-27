"""2-D arena geometry, facing, boundary/corner detection, and movement displacement helpers (§7.3)."""

from __future__ import annotations

import math
from typing import Any

from .data import (
    ARENA_PRESETS,
    TECH_CUT_OFF_STEP,
    TECH_PIVOT,
    TECH_RETREAT,
    TECH_SHOVE,
    TECH_STEP,
    load_model_v2,
)
from .defense import contest_roll


def get_arena_preset(arena: str, model_cfg: dict[str, Any] | None = None) -> dict[str, Any]:
    m_cfg = model_cfg if model_cfg is not None else load_model_v2()
    presets = m_cfg.get("arena_presets", ARENA_PRESETS)
    return presets.get(arena, presets.get("cage", {}))


def get_arena_shape_cfg(arena: str, model_cfg: dict[str, Any] | None = None) -> dict[str, Any]:
    m_cfg = model_cfg if model_cfg is not None else load_model_v2()
    arenas = m_cfg.get("geometry", {}).get("arenas", {})
    return arenas.get(arena, arenas.get("cage", {"shape": "octagon", "radius_m": 3.5}))


def compute_distance_m(pos_a: list[float], pos_b: list[float]) -> float:
    return math.hypot(float(pos_a[0]) - float(pos_b[0]), float(pos_a[1]) - float(pos_b[1]))


def band_from_distance(
    dist_m: float,
    posture_mode: str = "standing",
    model_cfg: dict[str, Any] | None = None,
) -> str:
    """Return the nearest range band from distance in meters; ground posture overrides to 'ground' (§7.3)."""
    if posture_mode == "ground":
        return "ground"
    m_cfg = model_cfg if model_cfg is not None else load_model_v2()
    dists = m_cfg.get("geometry", {}).get(
        "distances_m",
        {"clinch": 0.45, "close": 0.70, "punch": 1.05, "kick": 1.65, "outside": 2.40},
    )
    return min(dists.keys(), key=lambda b: abs(float(dists[b]) - float(dist_m)))


def update_facing(pos_self: list[float], pos_opp: list[float]) -> list[float]:
    dx = float(pos_opp[0]) - float(pos_self[0])
    dy = float(pos_opp[1]) - float(pos_self[1])
    norm = math.hypot(dx, dy)
    if norm <= 1e-6:
        return [1.0, 0.0]
    return [round(dx / norm, 4), round(dy / norm, 4)]


def compute_wall_and_corner(
    pos: list[float],
    arena: str,
    model_cfg: dict[str, Any] | None = None,
) -> tuple[str, bool, float]:
    """Compute (wall_proximity, in_corner, min_wall_dist_m) for a 2-D point in the arena (§7.3)."""
    m_cfg = model_cfg if model_cfg is not None else load_model_v2()
    preset = get_arena_preset(arena, m_cfg)
    shape_cfg = get_arena_shape_cfg(arena, m_cfg)
    wall_near_m = float(preset.get("wall_near_m", 0.60))
    half_w = float(preset.get("half_width_m", 3.5))
    shape = str(shape_cfg.get("shape", "octagon"))
    x, y = float(pos[0]), float(pos[1])

    if not preset.get("has_walls", False) and not preset.get("has_drop_hazard", False):
        return "far", False, max(0.0, half_w - math.hypot(x, y))

    if shape == "square" or shape == "platform":
        dx = max(0.0, half_w - abs(x))
        dy = max(0.0, half_w - abs(y))
        d_min = min(dx, dy)
        in_corner = bool(preset.get("has_corners", False) and dx <= wall_near_m and dy <= wall_near_m)
        prox = "near" if d_min <= wall_near_m else "far"
        return prox, in_corner, d_min

    if shape == "corridor":
        half_len = float(shape_cfg.get("half_length_m", 15.0))
        dx = max(0.0, half_w - abs(x))
        dy = max(0.0, half_len - abs(y))
        d_min = min(dx, dy)
        in_corner = bool(preset.get("has_corners", False) and dx <= wall_near_m and dy <= wall_near_m)
        prox = "near" if d_min <= wall_near_m else "far"
        return prox, in_corner, d_min

    # octagon / circle
    r = math.hypot(x, y)
    d_min = max(0.0, half_w - r)
    prox = "near" if d_min <= wall_near_m else "far"
    return prox, False, d_min


def clamp_or_fall_at_boundary(
    actor_state: dict[str, Any],
    raw_x: float,
    raw_y: float,
    arena: str,
    model_cfg: dict[str, Any] | None = None,
    rng: Any = None,
) -> None:
    """Apply arena boundary clamping or rooftop_edge drop-hazard roll (§7.3) and update wall_proximity / in_corner."""
    m_cfg = model_cfg if model_cfg is not None else load_model_v2()
    preset = get_arena_preset(arena, m_cfg)
    shape_cfg = get_arena_shape_cfg(arena, m_cfg)
    half_w = float(preset.get("half_width_m", 3.5))
    shape = str(shape_cfg.get("shape", "octagon"))

    if preset.get("has_drop_hazard", False):
        over_edge = abs(raw_x) > half_w or abs(raw_y) > half_w
        if over_edge:
            ef_cfg = m_cfg.get("geometry", {}).get("edge_fall", {})
            p_fall = float(ef_cfg.get("probability", 0.35))
            if actor_state.get("balance") in ("off_base", "compromised"):
                p_fall = min(0.95, p_fall * float(ef_cfg.get("off_base_multiplier", 1.5)))
            if contest_roll(p_fall, band_name="edge_fall", rng=rng, model_cfg=m_cfg)[0]:
                actor_state["fell_from_edge"] = True
                actor_state["position"] = [round(raw_x, 3), round(raw_y, 3)]
                actor_state["wall_proximity"] = "near"
                return
            clamped_x = max(-half_w, min(half_w, raw_x))
            clamped_y = max(-half_w, min(half_w, raw_y))
            actor_state["position"] = [round(clamped_x, 3), round(clamped_y, 3)]
            actor_state["balance"] = "off_base"
            actor_state["wall_proximity"] = "near"
            actor_state["in_corner"] = False
            return

    if preset.get("has_walls", False):
        if shape == "square":
            clamped_x = max(-half_w, min(half_w, raw_x))
            clamped_y = max(-half_w, min(half_w, raw_y))
        elif shape == "corridor":
            half_len = float(shape_cfg.get("half_length_m", 15.0))
            clamped_x = max(-half_w, min(half_w, raw_x))
            clamped_y = max(-half_len, min(half_len, raw_y))
        else:
            r = math.hypot(raw_x, raw_y)
            if r > half_w and r > 1e-6:
                scale = half_w / r
                clamped_x = raw_x * scale
                clamped_y = raw_y * scale
            else:
                clamped_x, clamped_y = raw_x, raw_y
    else:
        clamped_x, clamped_y = raw_x, raw_y

    actor_state["position"] = [round(clamped_x, 3), round(clamped_y, 3)]
    prox, in_corner, _ = compute_wall_and_corner(actor_state["position"], arena, m_cfg)
    actor_state["wall_proximity"] = prox
    actor_state["in_corner"] = in_corner


def apply_movement_displacement(
    tid: str,
    att_state: dict[str, Any],
    def_state: dict[str, Any],
    arena: str,
    model_cfg: dict[str, Any] | None = None,
    rng: Any = None,
) -> None:
    """Update 2-D positions and facings when a movement or push technique executes (§7.3)."""
    m_cfg = model_cfg if model_cfg is not None else load_model_v2()
    moves_m = m_cfg.get("geometry", {}).get("moves_m", {})
    preset = get_arena_preset(arena, m_cfg)
    lat_free = float(preset.get("lateral_freedom", 1.0))

    ax, ay = float(att_state["position"][0]), float(att_state["position"][1])
    dx, dy = float(def_state["position"][0]), float(def_state["position"][1])
    ux, uy = update_facing([ax, ay], [dx, dy])

    if tid == TECH_STEP:
        step_d = float(moves_m.get(TECH_STEP, 0.35))
        clamp_or_fall_at_boundary(att_state, ax + ux * step_d, ay + uy * step_d, arena, m_cfg, rng=rng)
    elif tid == TECH_RETREAT:
        ret_d = float(moves_m.get(TECH_RETREAT, 0.40))
        clamp_or_fall_at_boundary(att_state, ax - ux * ret_d, ay - uy * ret_d, arena, m_cfg, rng=rng)
    elif tid == TECH_CUT_OFF_STEP:
        cut_d = float(moves_m.get(TECH_CUT_OFF_STEP, 0.25))
        # Move toward opponent's lateral escape side (and slightly inward)
        lat_sign = 1.0 if dy >= ay else -1.0
        nx = ax + ux * (0.7 * cut_d) - uy * lat_sign * (0.7 * cut_d)
        ny = ay + uy * (0.7 * cut_d) + ux * lat_sign * (0.7 * cut_d)
        clamp_or_fall_at_boundary(att_state, nx, ny, arena, m_cfg, rng=rng)
    elif tid == TECH_SHOVE:
        shove_d = float(moves_m.get(TECH_SHOVE, 0.60))
        clamp_or_fall_at_boundary(def_state, dx + ux * shove_d, dy + uy * shove_d, arena, m_cfg, rng=rng)
    elif tid == TECH_PIVOT:
        deg = float(moves_m.get("pivot_angle_deg", 35.0)) * lat_free
        rad = math.radians(deg)
        vx, vy = dx - ax, dy - ay
        rx = ax + vx * math.cos(rad) - vy * math.sin(rad)
        ry = ay + vx * math.sin(rad) + vy * math.cos(rad)
        clamp_or_fall_at_boundary(def_state, rx, ry, arena, m_cfg, rng=rng)

    att_state["facing"] = update_facing(att_state["position"], def_state["position"])
    def_state["facing"] = update_facing(def_state["position"], att_state["position"])
