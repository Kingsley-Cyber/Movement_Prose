"""Grappling position and grip state transitions for BLOCK Simulator v2."""

from __future__ import annotations

from typing import Any

from .data import load_model_v2


def update_grappling_position(
    actor_state: dict[str, Any],
    defender_state: dict[str, Any],
    tid: str,
    outcome: str,
    actor_card: dict[str, Any],
) -> str:
    """Update grappling positions, grips, and control marks following an exchange."""
    model_cfg = load_model_v2()
    gt_cfg = model_cfg.get("legacy", {}).get("grappling_transitions", {})
    ride_id = gt_cfg.get("ride_id")
    collar_tie_id = gt_cfg.get("collar_tie_id")
    thai_plum_opt = gt_cfg.get("thai_plum_option")
    body_lock_id = gt_cfg.get("body_lock_id")
    wall_tie_id = gt_cfg.get("wall_tie_id")
    pummel_id = gt_cfg.get("pummel_id")
    takedown_ids = set(gt_cfg.get("takedown_ids", []))
    side_control_td_ids = set(gt_cfg.get("side_control_takedown_ids", []))
    guard_pull_id = gt_cfg.get("guard_pull_id")
    armbar_id = gt_cfg.get("armbar_id")
    ground_escape_ids = set(gt_cfg.get("ground_escape_ids", []))

    if outcome not in ("clean", "flush", "counter_hit", "partial"):
        if outcome == "jammed":
            actor_state["grappling_position"] = "over_under"
            defender_state["grappling_position"] = "over_under"
        elif tid == ride_id and actor_state.get("posture_mode") == "ground":
            actor_state["posture_mode"] = defender_state["posture_mode"] = "standing"
            actor_state["grappling_position"] = defender_state["grappling_position"] = "standing_neutral"
            actor_state["grip"] = defender_state["grip"] = None
            actor_state["submission_stage"] = defender_state["submission_stage"] = 0
        return str(actor_state.get("grappling_position", "standing_neutral"))

    tie_opt = actor_card["dimensions"].get("tie")
    if tid == collar_tie_id:
        pos = "thai_plum" if tie_opt == thai_plum_opt else str(collar_tie_id)
        actor_state["grappling_position"] = pos
        defender_state["grappling_position"] = str(collar_tie_id)
        actor_state["sub_grips"]["head_position"] = "inside_control"
        actor_state["grip"], defender_state["grip"] = "collar", "controlled"
    elif tid == body_lock_id:
        actor_state["grappling_position"] = "front_body_lock"
        defender_state["grappling_position"] = "over_under"
        actor_state["sub_grips"]["underhooks"] = 2
        actor_state["grip"], defender_state["grip"] = str(body_lock_id), "controlled"
    elif tid == wall_tie_id:
        actor_state["grappling_position"] = "wall_pinned"
        defender_state["grappling_position"] = "wall_pinned"
        actor_state["sub_grips"]["underhooks"] = 1
        actor_state["grip"], defender_state["grip"] = "single_tie", "controlled"
    elif tid == pummel_id:
        actor_state["grappling_position"] = "double_underhooks"
        defender_state["grappling_position"] = "over_under"
        actor_state["sub_grips"]["underhooks"] = min(2, actor_state["sub_grips"].get("underhooks", 0) + 1)
    elif tid in takedown_ids:
        actor_state["posture_mode"] = defender_state["posture_mode"] = "ground"
        actor_state["grappling_position"] = "side_control" if tid in side_control_td_ids else "half_guard_top"
        defender_state["grappling_position"] = "closed_guard_bottom"
        actor_state["grip"], defender_state["grip"] = "top", "bottom"
        actor_state["control_marks"] += 1
    elif tid == guard_pull_id:
        actor_state["posture_mode"] = defender_state["posture_mode"] = "ground"
        actor_state["grappling_position"] = "closed_guard_bottom"
        defender_state["grappling_position"] = "half_guard_top"
        actor_state["grip"], defender_state["grip"] = "bottom", "top"
        actor_state["control_marks"] += 1
    elif tid == ride_id:
        actor_state["grappling_position"] = "mount_or_back_ride"
        defender_state["grappling_position"] = "closed_guard_bottom"
        actor_state["control_marks"] += 1
    elif tid == armbar_id:
        stage = int(actor_state.get("submission_stage", 0)) + 1
        actor_state["submission_stage"] = stage
        actor_state["sub_grips"]["wrist_control"] = True
        actor_state["grappling_position"] = "side_control"
        actor_state["control_marks"] += 1
    elif tid in ground_escape_ids and actor_state.get("posture_mode") == "ground":
        actor_state["posture_mode"] = defender_state["posture_mode"] = "standing"
        actor_state["grappling_position"] = defender_state["grappling_position"] = "standing_neutral"
        actor_state["grip"] = defender_state["grip"] = None
        actor_state["submission_stage"] = defender_state["submission_stage"] = 0

    return str(actor_state["grappling_position"])
