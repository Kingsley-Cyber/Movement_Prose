"""Closed-Loop Render Verification, Ledger Calibration, Localized RFC 6902 Repair, and Clip Handoff Engine.

Implements the CPCS Handbook operational loop (`src-cpcs-mx-repair_strategy` & `ch-14 Localized Repair Playbook`):
  target -> compile -> generate -> observe (SCORECARD.md / TwelveLabs audit-render) ->
  verify -> failure signature -> responsible layer -> smallest localized repair -> regenerate
"""

import copy
import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .dyad import DyadState
from .kb_bridge import DEFAULT_BUNDLE_DIR, bundle_available
from .lexicon import Lexicon
from .state import FighterState

LEDGERS_DIR = Path(__file__).parent / "ledgers"
CONFIG_DIR = Path(__file__).parent / "config"
WORD_PROBES_PATH = LEDGERS_DIR / "word_probes.json"
QUARANTINED_PAIRS_PATH = LEDGERS_DIR / "quarantined_pairs.json"
THRESHOLDS_PATH = CONFIG_DIR / "thresholds.json"

# Handbook Contact & Persistence Failure Taxonomy (`b026`, `b037`, `src-cpcs-mx-repair_strategy`)
FAILURE_TAXONOMY: Dict[str, Dict[str, Any]] = {
    "contact_flicker": {
        "symptom": "Hands or limbs touch for alternating single frames without readable contact hold",
        "responsible_layer": "temporal_cadence",
        "validator_id": "V21",
        "directive_fix": "aa_time_contact_hitstop",
        "preferred_repairs": ["extend_contact_hold_window", "lock_contact_camera"],
    },
    "phantom_force": {
        "symptom": "Defender reacts before or without visible contact onset",
        "responsible_layer": "dyad_causality",
        "validator_id": "V09",
        "directive_fix": "aa_time_recoil_spacing",
        "preferred_repairs": ["enforce_only_after_contact_recoil", "set_sudden_jolt_settle_easing"],
    },
    "dead_contact": {
        "symptom": "Limbs touch but bodies remain independent without force transfer",
        "responsible_layer": "kinetic_chain_and_impulse",
        "validator_id": "V18/V22",
        "directive_fix": "aa_action_absorb_recoil",
        "preferred_repairs": ["splice_ground_up_kinetic_chain", "align_defender_impulse_tier"],
    },
    "pose_reset": {
        "symptom": "Next action begins from a stiff neutral stance incompatible with previous endpoint",
        "responsible_layer": "fighter_state_machine",
        "validator_id": "V10/V11",
        "directive_fix": "aa_action_followthrough_arc",
        "preferred_repairs": ["insert_coarticulated_overlap_move", "carry_post_coil_into_pre_coil"],
    },
    "support_swap": {
        "symptom": "Weight-bearing foot changes or CoG falls outside support base without transfer/catch step",
        "responsible_layer": "support_and_balance",
        "validator_id": "V19",
        "directive_fix": "aa_action_weight_load",
        "preferred_repairs": ["stabilize_weight_split_and_com", "add_recovery_catch_step"],
    },
    "camera_occlusion": {
        "symptom": "Camera angle hides the acting limb or contact point behind a torso/shoulder",
        "responsible_layer": "camera_optics",
        "validator_id": "V20",
        "directive_fix": "aa_camera_contact_lock",
        "preferred_repairs": ["switch_to_medium_wide_side_profile"],
    },
    "mismatched_hands": {
        "symptom": "Missing off-arm, torso-merged arm, or extra hallucinated limb during strike",
        "responsible_layer": "subject_anchor",
        "validator_id": "V15/V16",
        "directive_fix": "aa_subject_loaded_silhouette",
        "preferred_repairs": ["enforce_four_limb_silhouette_separation"],
    },
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_scorecard_markdown(md_text: str) -> List[Dict[str, str]]:
    """Parse a markdown scorecard table (like `runs/001_strike_block/SCORECARD.md`) into structured rows."""
    lines = [ln.strip() for ln in md_text.splitlines() if ln.strip().startswith("|")]
    if len(lines) < 3:
        return []
    headers = [c.strip().lower() for c in lines[0].strip("|").split("|")]
    rows: List[Dict[str, str]] = []
    for ln in lines[2:]:
        cols = [c.strip() for c in ln.strip("|").split("|")]
        if len(cols) != len(headers):
            continue
        row = dict(zip(headers, cols))
        # Only include rows where at least a verdict or model id was filled in
        if any(row.get(k, "") for k in ("verdict", "engine / model id", "notes")):
            rows.append(row)
    return rows


def ingest_render_verdict(
    render_id: str,
    model_id: str,
    verdict: str,
    move_id: Optional[str] = None,
    bleed_pair: Optional[Tuple[str, str]] = None,
    calibrate_threshold_key: Optional[str] = None,
    notes: str = "",
    word_probes_path: Path = WORD_PROBES_PATH,
    quarantined_pairs_path: Path = QUARANTINED_PAIRS_PATH,
    thresholds_path: Path = THRESHOLDS_PATH,
    bundle_dir: Path = DEFAULT_BUNDLE_DIR,
) -> Dict[str, Any]:
    """Ingest an owner render verdict into `ledgers/word_probes.json`, `ledgers/quarantined_pairs.json`,
    `config/thresholds.json`, and `agent_memory.db`.
    """
    if verdict not in {"works", "partial", "fails"}:
        raise ValueError(f"verdict must be one of 'works', 'partial', 'fails' (got '{verdict}')")

    ts = _utc_now()
    summary: Dict[str, Any] = {
        "render_id": render_id,
        "model_id": model_id,
        "verdict": verdict,
        "updated_word_probes": False,
        "updated_quarantined_pairs": False,
        "updated_thresholds": False,
        "updated_agent_memory": False,
    }

    # 1. Update word_probes.json
    if move_id:
        probes_data = json.loads(word_probes_path.read_text(encoding="utf-8"))
        probes_dict = probes_data.setdefault("probes", {})
        move_entry = probes_dict.setdefault(move_id, {})
        model_entry = move_entry.setdefault(model_id, {"verdict": verdict, "render_ids": [], "notes": []})
        model_entry["verdict"] = verdict
        if render_id not in model_entry["render_ids"]:
            model_entry["render_ids"].append(render_id)
        if notes:
            model_entry["notes"].append(f"[{ts}] {notes}")
        word_probes_path.write_text(json.dumps(probes_data, indent=2) + "\n", encoding="utf-8")
        summary["updated_word_probes"] = True

    # 2. Update quarantined_pairs.json if attention bleed occurred
    if bleed_pair and len(bleed_pair) == 2:
        q_data = json.loads(quarantined_pairs_path.read_text(encoding="utf-8"))
        pairs_list = q_data.setdefault("pairs", [])
        c_a, c_b = bleed_pair
        existing = next(
            (p for p in pairs_list if {p.get("class_a"), p.get("class_b")} == {c_a, c_b}),
            None,
        )
        if existing:
            ev_ids = existing.setdefault("evidence_render_ids", [])
            if render_id not in ev_ids:
                ev_ids.append(render_id)
            existing["status"] = "calibrated"
        else:
            pairs_list.append(
                {
                    "id": f"Q_{len(pairs_list) + 1:02d}_{c_a.lower().replace('.', '_')}_{c_b.lower().replace('.', '_')}",
                    "class_a": c_a,
                    "class_b": c_b,
                    "status": "calibrated",
                    "evidence_render_ids": [render_id],
                    "reason": notes or f"Empirically observed cross-attention bleed in render {render_id} on {model_id}.",
                }
            )
        quarantined_pairs_path.write_text(json.dumps(q_data, indent=2) + "\n", encoding="utf-8")
        summary["updated_quarantined_pairs"] = True

    # 3. Calibrate threshold in config/thresholds.json
    if calibrate_threshold_key and thresholds_path.is_file():
        t_data = json.loads(thresholds_path.read_text(encoding="utf-8"))
        thresholds_map = t_data.get("thresholds", {})
        if calibrate_threshold_key in thresholds_map:
            t_entry = thresholds_map[calibrate_threshold_key]
            t_entry["status"] = "calibrated"
            ev = t_entry.setdefault("evidence_render_ids", [])
            if render_id not in ev:
                ev.append(render_id)
            thresholds_path.write_text(json.dumps(t_data, indent=2) + "\n", encoding="utf-8")
            summary["updated_thresholds"] = True

    # 4. Log verdict into `agent_memory.db` if available
    if bundle_available(bundle_dir):
        mem_path = bundle_dir / "agent_memory.db"
        conn = sqlite3.connect(str(mem_path))
        try:
            tag_name = f"verdict_{verdict}"
            conn.execute(
                "INSERT OR IGNORE INTO tags (tag, description, created_at, created_by) VALUES (?, ?, ?, 'closed_loop')",
                (tag_name, f"Render verdict: {verdict}", ts),
            )
            target_id = f"move:{move_id}" if move_id else render_id
            conn.execute(
                "INSERT OR REPLACE INTO node_tags (node_kind, node_id, tag, weight, note, created_at, created_by) "
                "VALUES ('concept', ?, ?, ?, ?, ?, 'closed_loop')",
                (
                    target_id,
                    tag_name,
                    1.0 if verdict == "works" else (0.5 if verdict == "partial" else -1.0),
                    f"model={model_id} render={render_id} {notes}".strip(),
                    ts,
                ),
            )
            conn.execute(
                "INSERT INTO usage_events (at, run_id, action, node_kind, node_id, context) VALUES (?, ?, ?, 'concept', ?, ?)",
                (
                    ts,
                    render_id,
                    f"verdict:{verdict}",
                    target_id,
                    json.dumps({"model": model_id, "notes": notes}),
                ),
            )
            conn.commit()
            summary["updated_agent_memory"] = True
        finally:
            conn.close()

    return summary


def plan_localized_repair(
    clip: Dict[str, Any],
    beat_index: int,
    failure_type: str,
    actor: str = "A",
    lexicon: Optional[Lexicon] = None,
) -> Dict[str, Any]:
    """Create a localized RFC 6902 repair plan for a single failed beat without rewriting the rest of the clip
    (Handbook `src-cpcs-mx-repair_strategy` & `ch-14 Localized Repair Playbook`).
    """
    if failure_type not in FAILURE_TAXONOMY:
        raise ValueError(
            f"Unknown failure_type '{failure_type}'. Legal types: {sorted(FAILURE_TAXONOMY.keys())}"
        )
    moments = clip.get("moments", [])
    if not (0 <= beat_index < len(moments)):
        raise ValueError(f"beat_index {beat_index} out of range (clip has {len(moments)} moments)")

    lex = lexicon or Lexicon.load_default()
    tax = FAILURE_TAXONOMY[failure_type]
    moment = moments[beat_index]
    act_slot = moment.get(actor) or {}
    move_id = act_slot.get("move", "")
    card = lex.get(move_id) if move_id else None

    canonical_bytes = json.dumps(clip, sort_keys=True).encode("utf-8")
    base_digest = "sha256:" + hashlib.sha256(canonical_bytes).hexdigest()

    patches: List[Dict[str, Any]] = []
    # RFC 6902 `test` operation to protect the expected base before mutation
    if move_id:
        patches.append(
            {
                "op": "test",
                "path": f"/moments/{beat_index}/{actor}/move",
                "value": move_id,
            }
        )

    if failure_type == "contact_flicker":
        cur_frames = int(moment.get("frames", 8))
        new_frames = max(cur_frames, 9)
        patches.append({"op": "replace", "path": f"/moments/{beat_index}/frames", "value": new_frames})
        patches.append(
            {
                "op": "add",
                "path": f"/moments/{beat_index}/camera",
                "value": "medium_wide_side_profile",
            }
        )
    elif failure_type == "phantom_force":
        target_actor = "B" if actor == "B" else "B"
        patches.append(
            {
                "op": "add",
                "path": f"/moments/{beat_index}/{target_actor}/easing_curve",
                "value": "sudden_jolt_settle",
            }
        )
    elif failure_type == "dead_contact":
        if card and card.get("chain"):
            patches.append(
                {
                    "op": "add",
                    "path": f"/moments/{beat_index}/{actor}/chain",
                    "value": card["chain"],
                }
            )
            patches.append(
                {
                    "op": "add",
                    "path": f"/moments/{beat_index}/{actor}/chain_frames",
                    "value": card.get("chain_frames", [0, 2, 4, 6]),
                }
            )
        if "B" in moment and card:
            atk_tier = int(card.get("impulse_tier", 2))
            patches.append(
                {
                    "op": "add",
                    "path": f"/moments/{beat_index}/B/impulse_tier",
                    "value": atk_tier,
                }
            )
    elif failure_type == "pose_reset":
        patches.append(
            {
                "op": "add",
                "path": f"/moments/{beat_index}/{actor}/overlaps_move",
                "value": "slip_outside",
            }
        )
    elif failure_type == "support_swap":
        patches.append(
            {
                "op": "add",
                "path": f"/moments/{beat_index}/{actor}/weight_split",
                "value": [70, 30],
            }
        )
        patches.append(
            {
                "op": "add",
                "path": f"/moments/{beat_index}/{actor}/com_position",
                "value": "over_lead_foot",
            }
        )
        patches.append(
            {
                "op": "add",
                "path": f"/moments/{beat_index}/{actor}/catch_step",
                "value": True,
            }
        )
    elif failure_type == "camera_occlusion":
        patches.append(
            {
                "op": "add",
                "path": f"/moments/{beat_index}/camera",
                "value": "medium_wide_side_profile",
            }
        )
    elif failure_type == "mismatched_hands":
        patches.append(
            {
                "op": "add",
                "path": f"/moments/{beat_index}/{actor}/easing_curve",
                "value": "explosive_snap_hold_recoil",
            }
        )
        patches.append(
            {
                "op": "add",
                "path": f"/moments/{beat_index}/camera",
                "value": "medium_wide_side_profile",
            }
        )

    return {
        "repair_id": f"repair.beat_{beat_index + 1:02d}.{failure_type}",
        "failure_id": f"failure.{tax['responsible_layer']}.{failure_type}",
        "validator_id": tax["validator_id"],
        "base_digest": base_digest,
        "responsible_layer": tax["responsible_layer"],
        "directive_fix": tax["directive_fix"],
        "regeneration_scope": f"moments[{beat_index}]",
        "affected_paths": [p["path"] for p in patches if p["op"] != "test"],
        "protected_invariants": [
            "action_identity",
            "duration",
            "subject_identity",
            "screen_side_lock",
        ],
        "patch": patches,
        "status": "proposed",
    }


def apply_localized_repair(clip: Dict[str, Any], repair_obj: Dict[str, Any]) -> Dict[str, Any]:
    """Apply a localized RFC 6902 repair object to a copy of `clip`, mutating only the target beat."""
    canonical_bytes = json.dumps(clip, sort_keys=True).encode("utf-8")
    actual_digest = "sha256:" + hashlib.sha256(canonical_bytes).hexdigest()
    expected_digest = repair_obj.get("base_digest")
    if expected_digest and actual_digest != expected_digest:
        raise ValueError(f"Base digest mismatch: expected {expected_digest}, got {actual_digest}")

    repaired = copy.deepcopy(clip)
    for op_item in repair_obj.get("patch", []):
        op = op_item["op"]
        parts = [p for p in op_item["path"].strip("/").split("/") if p]
        target: Any = repaired
        for seg in parts[:-1]:
            if isinstance(target, list):
                target = target[int(seg)]
            else:
                target = target.setdefault(seg, {})
        last_key = parts[-1]
        if op == "test":
            actual_val = target[int(last_key)] if isinstance(target, list) else target.get(last_key)
            if actual_val != op_item["value"]:
                raise ValueError(
                    f"RFC 6902 test failed at {op_item['path']}: expected {op_item['value']}, got {actual_val}"
                )
        elif op in {"add", "replace"}:
            if isinstance(target, list):
                target[int(last_key)] = op_item["value"]
            else:
                target[last_key] = op_item["value"]
    return repaired


def build_next_clip_handoff(
    clip: Dict[str, Any],
    lexicon: Optional[Lexicon] = None,
) -> Dict[str, Any]:
    """Extract the terminal `t=10.0s` fighter postures, coil states, range_band, and persistent floor damage
    from Clip N to seed Clip N+1 seamlessly.
    """
    lex = lexicon or Lexicon.load_default()
    fighters_cfg = copy.deepcopy(clip.get("fighters", {}))
    a_cfg = fighters_cfg.get("A", {})
    b_cfg = fighters_cfg.get("B", {})

    fighter_a = FighterState(
        id="A",
        style=a_cfg.get("style", "boxing"),
        stance=a_cfg.get("stance", "orthodox"),
        screen_side=a_cfg.get("screen_side", "left"),
        facing=a_cfg.get("facing", "right"),
        support=a_cfg.get("support", "standing"),
        coil=a_cfg.get("coil", "neutral"),
    )
    fighter_b = FighterState(
        id="B",
        style=b_cfg.get("style", "boxing"),
        stance=b_cfg.get("stance", "orthodox"),
        screen_side=b_cfg.get("screen_side", "right"),
        facing=b_cfg.get("facing", "left"),
        support=b_cfg.get("support", "standing"),
        coil=b_cfg.get("coil", "neutral"),
    )
    dyad = DyadState(range_band=clip.get("initial_range", "punch"))

    for moment in clip.get("moments", []):
        for fid, fstate in (("A", fighter_a), ("B", fighter_b)):
            act = moment.get(fid)
            if not act:
                continue
            if "overlaps_move" in act:
                ov = lex.get(act["overlaps_move"])
                if ov:
                    fstate.support = ov["post"]["support"]
                    fstate.coil = ov["post"]["coil"]
                    dyad.apply_range_delta(ov["post"]["range_delta"])
            card = lex.get(act["move"])
            if card:
                fstate.support = card["post"]["support"]
                fstate.coil = card["post"]["coil"]
                dyad.apply_range_delta(card["post"]["range_delta"])

    a_cfg["support"] = fighter_a.support
    a_cfg["coil"] = fighter_a.coil
    b_cfg["support"] = fighter_b.support
    b_cfg["coil"] = fighter_b.coil

    next_regime = "ground" if "supine" in {fighter_a.support, fighter_b.support} else (
        "clinch" if dyad.range_band == "clinch" else "standup_striking"
    )

    return {
        "name": f"{clip.get('name', 'clip')}_next_handoff",
        "handoff_from": clip.get("name", "clip_N"),
        "regime": next_regime,
        "initial_range": dyad.range_band,
        "arena": clip.get("arena", ""),
        "persistent_environment_state": [
            "aa_env_debris_settle: preserve radial concrete cracks, heel skid gouges, and cuboid stone chips from prior clip"
        ],
        "fighters": {
            "A": a_cfg,
            "B": b_cfg,
        },
        "moments": [],
    }
