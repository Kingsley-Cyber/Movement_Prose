"""Read-only Knowledge Base Bridge to `/Users/king/Downloads/anime_action_research_bundle`.

Connects `fight_move_system` (`sakuga_Xperiment`) to:
  1. `handbook_index.db` (20-chapter CPCS Domain Handbook FTS5 index, passages, blocks, concepts) — READ-ONLY
  2. `ai_video_compiler.db` (64-row `semantic_directives` catalog across 6 moments x 8 slots) — READ-ONLY
  3. `agent_memory.db` (growing memory: tags, usage_events, used_with, agent_concepts, agent_links) — READ/WRITE

Never modifies any file listed in `SHA256SUMS.bundle`.
"""

import hashlib
import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .lexicon import Lexicon

DEFAULT_BUNDLE_DIR = Path(
    os.environ.get(
        "ANIME_KB_BUNDLE_DIR",
        "/Users/king/Downloads/anime_action_research_bundle",
    )
)

# Mapping from fight_move_system move classes/ids to the 64 `aa_*` directives in `ai_video_compiler.db`
# and canonical handbook citations in `handbook_index.db`.
PHASE_DIRECTIVE_MAP: Dict[str, List[str]] = {
    "anticipation": [
        "aa_subject_loaded_silhouette",
        "aa_action_weight_load",
        "aa_env_preimpact_quiet",
        "aa_time_hold_then_burst",
        "aa_light_hard_shadow",
        "aa_material_two_tone_cel",
    ],
    "execution": [
        "aa_action_hip_led_punch",
        "aa_subject_angular_pose",
        "aa_subject_multiple_limb_smear",
        "aa_time_mixed_exposures",
        "aa_time_pose_snapping",
        "aa_camera_lateral_track",
    ],
    "impact_strike": [
        "aa_subject_elastic_contact",
        "aa_time_contact_hitstop",
        "aa_camera_contact_lock",
        "aa_secondary_angular_impact_star",
        "aa_secondary_contact_ring",
    ],
    "impact_block": [
        "aa_action_forearm_block",
        "aa_camera_contact_lock",
        "aa_time_contact_hitstop",
        "aa_env_skid_gouge",
    ],
    "impact_finisher": [
        "aa_material_charcoal_impact",
        "aa_material_monochrome_impact",
        "aa_env_radial_fracture",
        "aa_env_yutapon_cubes",
        "aa_time_contact_hitstop",
    ],
    "recoil": [
        "aa_action_absorb_recoil",
        "aa_time_recoil_spacing",
        "aa_subject_recoil_identity",
        "aa_material_expressive_rough",
        "aa_env_skid_gouge",
    ],
    "follow_through": [
        "aa_action_followthrough_arc",
        "aa_time_overlap_offsets",
        "aa_subject_costume_attachment",
    ],
    "recovery": [
        "aa_action_guard_recovery",
        "aa_subject_recovery_model",
        "aa_env_debris_settle",
        "aa_camera_recovery_settle",
        "aa_light_restore_key",
        "aa_material_restore_palette",
        "aa_time_moving_hold",
    ],
}

# The 9 martial-arts lexical gaps and 5 taste gaps surfaced by `agent propose` in `gaps.jsonl`
# bridged into `agent_memory.db` (`agent_concepts` & `agent_links`).
BRIDGED_LEXICAL_CONCEPTS: List[Dict[str, Any]] = [
    {
        "concept_id": "low_calf_kick_strike",
        "label": "Low calf kick / shin chop",
        "kind": "technique",
        "aliases": ["kick", "calf kick", "low kick", "outside calf kick", "shin kick", "spinning back kick"],
        "description": "Off-line lead step and horizontal shin whip into opponent's lead calf or spinning heel drive into solar plexus/jaw.",
        "linked_directives": ["aa_action_weight_load", "aa_subject_multiple_limb_smear", "aa_time_contact_hitstop"],
    },
    {
        "concept_id": "slip_counter_exchange",
        "label": "Slip-and-counter exchange",
        "kind": "technique",
        "aliases": ["counter", "slip counter", "slip inside", "slip outside", "counter cross"],
        "description": "Coarticulated evasion that loads the lead or rear hip so defense and counter-strike execute without a neutral reset.",
        "linked_directives": ["aa_action_weight_load", "aa_action_hip_led_punch", "aa_time_pose_snapping"],
    },
    {
        "concept_id": "liver_shovel_hook",
        "label": "Lead liver shovel hook",
        "kind": "technique",
        "aliases": ["liver", "hook", "liver hook", "shovel hook", "body hook"],
        "description": "Level-dipped upward/horizontal left fist arc into the right floating ribs, compressing the opponent's ribcage into a short graphic curve.",
        "linked_directives": ["aa_subject_angular_pose", "aa_subject_elastic_contact", "aa_material_expressive_rough"],
    },
    {
        "concept_id": "muay_thai_clinch_knee",
        "label": "Collar-tie clinch & rising pillar knee",
        "kind": "technique",
        "aliases": ["clinch", "grab", "collar tie", "double collar plum", "rising clinch knee", "clinch shove"],
        "description": "Symmetrical chest-to-chest tie-up (0.58m) with straight grounded support pillar leg and vertical knee drive into sternum.",
        "linked_directives": ["aa_camera_contact_lock", "aa_secondary_contact_ring", "aa_action_absorb_recoil"],
    },
    {
        "concept_id": "spinning_back_kick_finisher",
        "label": "Spinning back kick finisher",
        "kind": "technique",
        "aliases": ["spinning", "knockout", "back kick", "spinning back kick", "heel kick"],
        "description": "1-frame coiled back-turn hold followed by full-rotation heel piston into solar plexus/jaw with charcoal-monochrome impact flash and radial floor fracture.",
        "linked_directives": [
            "aa_time_hold_then_burst",
            "aa_material_charcoal_impact",
            "aa_env_radial_fracture",
            "aa_env_yutapon_cubes",
        ],
    },
    {
        "concept_id": "bare_knuckle_intensity",
        "label": "Bare-knuckle gritty OVA intensity",
        "kind": "style",
        "aliases": [
            "intense",
            "bare",
            "bare-knuckle",
            "heavy ink line weight",
            "blood / sweat",
            "dark saturated palette",
            "film grain / cel dust",
        ],
        "description": "High-contrast 2-tone cel shading, bold wedge muscle striations, sweat spray on impact holds, and broken ink contours on peak recoil frames.",
        "linked_directives": [
            "aa_material_two_tone_cel",
            "aa_light_hard_shadow",
            "aa_material_expressive_rough",
            "aa_material_charcoal_impact",
        ],
    },
]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def bundle_available(bundle_dir: Path = DEFAULT_BUNDLE_DIR) -> bool:
    """Return True if the research bundle databases exist on disk."""
    return (
        bundle_dir.is_dir()
        and (bundle_dir / "ai_video_compiler.db").is_file()
        and (bundle_dir / "handbook_index.db").is_file()
    )


def verify_bundle_integrity(bundle_dir: Path = DEFAULT_BUNDLE_DIR) -> Tuple[bool, List[str]]:
    """Verify `SHA256SUMS.bundle` in the research bundle directory so frozen files are never mutated."""
    manifest = bundle_dir / "SHA256SUMS.bundle"
    if not manifest.is_file():
        return False, [f"Missing SHA256SUMS.bundle in {bundle_dir}"]
    errors: List[str] = []
    for line in manifest.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        expected_sha, rel_name = parts[0], parts[1].lstrip("*")
        fpath = bundle_dir / rel_name
        if not fpath.is_file():
            errors.append(f"Missing bundle file: {rel_name}")
            continue
        actual_sha = hashlib.sha256(fpath.read_bytes()).hexdigest()
        if actual_sha != expected_sha:
            errors.append(f"SHA256 mismatch for {rel_name}: expected {expected_sha}, got {actual_sha}")
    return len(errors) == 0, errors


def _connect_ro(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _connect_memory(bundle_dir: Path = DEFAULT_BUNDLE_DIR) -> sqlite3.Connection:
    mem_path = bundle_dir / "agent_memory.db"
    conn = sqlite3.connect(str(mem_path))
    conn.row_factory = sqlite3.Row
    return conn


def load_semantic_directives(bundle_dir: Path = DEFAULT_BUNDLE_DIR) -> Dict[str, Dict[str, Any]]:
    """Load all 64 rows from `ai_video_compiler.db` read-only."""
    if not bundle_available(bundle_dir):
        return {}
    conn = _connect_ro(bundle_dir / "ai_video_compiler.db")
    try:
        rows = conn.execute(
            "SELECT directive_id, archetype, sub_genre, slot_id, moment_type, prompt_snippet, negative_snippet, mechanical_guidance "
            "FROM semantic_directives"
        ).fetchall()
        out: Dict[str, Dict[str, Any]] = {}
        for r in rows:
            mg = r["mechanical_guidance"]
            try:
                mg_parsed = json.loads(mg) if isinstance(mg, str) and mg.startswith("{") else mg
            except Exception:
                mg_parsed = mg
            out[r["directive_id"]] = {
                "directive_id": r["directive_id"],
                "archetype": r["archetype"],
                "sub_genre": r["sub_genre"],
                "slot_id": r["slot_id"],
                "moment_type": r["moment_type"],
                "prompt_snippet": r["prompt_snippet"],
                "negative_snippet": r["negative_snippet"],
                "mechanical_guidance": mg_parsed,
            }
        return out
    finally:
        conn.close()


def sync_lexicon_gaps_to_memory(
    lexicon: Optional[Lexicon] = None,
    bundle_dir: Path = DEFAULT_BUNDLE_DIR,
) -> Dict[str, int]:
    """Bridge the 9 martial-arts lexical gaps, 5 taste gaps, and 38 Move Cards into `agent_memory.db`
    without modifying `ai_video_compiler.db` or `handbook_index.db`.
    """
    if not bundle_available(bundle_dir):
        return {"concepts_synced": 0, "links_synced": 0, "tags_synced": 0}

    lex = lexicon or Lexicon.load_default()
    conn = _connect_memory(bundle_dir)
    ts = _utc_now()
    concepts_count = 0
    links_count = 0
    tags_count = 0
    try:
        # 1. Insert bridged lexical & taste concepts
        for item in BRIDGED_LEXICAL_CONCEPTS:
            conn.execute(
                "INSERT OR REPLACE INTO agent_concepts (concept_id, label, kind, aliases, description, created_at, created_by) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    item["concept_id"],
                    item["label"],
                    item["kind"],
                    json.dumps(item["aliases"]),
                    item["description"],
                    ts,
                    "fight_move_system",
                ),
            )
            concepts_count += 1
            for d_id in item.get("linked_directives", []):
                conn.execute(
                    "INSERT OR REPLACE INTO agent_links (from_kind, from_id, to_kind, to_id, relation, note, created_at, created_by) "
                    "VALUES ('concept', ?, 'directive', ?, 'implemented_by', 'bridged from fight_move_system lexicon', ?, 'fight_move_system')",
                    (item["concept_id"], d_id, ts),
                )
                links_count += 1

        # 2. Register each Move Card from `fight_move_system` in `agent_concepts` so `agent concept` sees all 38 moves
        for move_id, card in sorted(lex.cards_by_id.items()):
            cid = f"move:{move_id}"
            aliases = [move_id.replace("_", " ")] + list(card.get("aliases", []))
            desc = f"{card['class']} ({card['limb']}, {card['level']}): {card['caption_words']}"
            conn.execute(
                "INSERT OR REPLACE INTO agent_concepts (concept_id, label, kind, aliases, description, created_at, created_by) "
                "VALUES (?, ?, 'move_card', ?, ?, ?, 'fight_move_system')",
                (cid, move_id.replace("_", " ").title(), json.dumps(aliases), desc, ts),
            )
            concepts_count += 1

        # 3. Tag key handbook passages for combat state, contact contract, and localized repair
        key_tags = [
            ("combat_persistence", "src-additional-continous-combat-state-md#0152", "10. Persistence invariants (no pose reset, no phantom force)"),
            ("contact_taxonomy", "src-additional-continous-combat-state-md#0215", "19. Contact failure taxonomy (flicker, dead contact, support swap)"),
            ("minimal_projection", "src-additional-02-facs-laban-bartenieff-gap-closure-completed-md#0786", "Salience ranking -> attention budget -> minimal sufficient projection"),
            ("localized_repair", "src-cpcs-mx-repair_strategy#0001", "target -> compile -> generate -> observe -> verify -> smallest localized repair"),
        ]
        for tag_name, pid, note in key_tags:
            conn.execute(
                "INSERT OR IGNORE INTO tags (tag, description, created_at, created_by) VALUES (?, ?, ?, 'fight_move_system')",
                (tag_name, note, ts),
            )
            conn.execute(
                "INSERT OR REPLACE INTO node_tags (node_kind, node_id, tag, weight, note, created_at, created_by) "
                "VALUES ('passage', ?, ?, 1.0, ?, ?, 'fight_move_system')",
                (pid, tag_name, note, ts),
            )
            tags_count += 1

        conn.commit()
    finally:
        conn.close()

    return {
        "concepts_synced": concepts_count,
        "links_synced": links_count,
        "tags_synced": tags_count,
    }


def resolve_beat_kb_guidance(
    a_card: Optional[Dict[str, Any]],
    b_card: Optional[Dict[str, Any]],
    is_hero: bool = False,
    beat_idx: int = 0,
    total_beats: int = 10,
) -> Dict[str, Any]:
    """Return structured KB directive IDs and phrasing enhancements for a single combat beat."""
    directives: List[str] = []
    if beat_idx == 0:
        directives.extend(["aa_env_preimpact_quiet", "aa_time_hold_then_burst", "aa_subject_loaded_silhouette"])

    if a_card:
        if a_card["contact"] == "strike":
            directives.extend(["aa_action_weight_load", "aa_action_hip_led_punch", "aa_subject_angular_pose"])
            if a_card["limb"] not in {"lead_knee", "rear_knee"}:
                directives.append("aa_subject_multiple_limb_smear")
            directives.extend(["aa_time_contact_hitstop", "aa_camera_contact_lock"])
            if "elbow" in a_card["id"]:
                directives.append("aa_secondary_angular_impact_star")
            elif "knee" in a_card["id"]:
                directives.append("aa_secondary_contact_ring")
            if is_hero:
                directives.extend(
                    [
                        "aa_material_charcoal_impact",
                        "aa_material_monochrome_impact",
                        "aa_env_radial_fracture",
                        "aa_env_yutapon_cubes",
                    ]
                )
        elif a_card["contact"] == "block":
            directives.extend(["aa_action_forearm_block", "aa_camera_contact_lock", "aa_env_skid_gouge"])
        elif a_card["contact"] == "grapple":
            if "shove" in a_card["id"]:
                directives.extend(["aa_action_absorb_recoil", "aa_env_skid_gouge", "aa_env_layered_dust"])
            else:
                directives.append("aa_camera_contact_lock")

    if b_card:
        if b_card["class"] == "IMPACT.REACTION":
            directives.extend(
                [
                    "aa_action_absorb_recoil",
                    "aa_time_recoil_spacing",
                    "aa_subject_recoil_identity",
                ]
            )
            if b_card["level"] == "mid":
                directives.extend(["aa_subject_elastic_contact", "aa_material_expressive_rough"])
            if "shoved" in b_card["id"]:
                directives.append("aa_env_skid_gouge")
        elif b_card["contact"] == "strike":
            directives.extend(["aa_action_weight_load", "aa_action_hip_led_punch", "aa_subject_multiple_limb_smear"])

    if beat_idx == total_beats - 1:
        directives.extend(
            [
                "aa_action_guard_recovery",
                "aa_subject_recovery_model",
                "aa_env_debris_settle",
                "aa_camera_recovery_settle",
                "aa_light_restore_key",
                "aa_material_restore_palette",
            ]
        )

    # Deduplicate preserving order
    seen = set()
    deduped = []
    for d in directives:
        if d not in seen:
            seen.add(d)
            deduped.append(d)

    return {
        "directives": deduped,
        "handbook_refs": [
            "src-additional-continous-combat-state-md#0315",
            "src-additional-continous-combat-state-md#0152",
            "src-additional-02-facs-laban-bartenieff-gap-closure-completed-md#0786",
        ],
    }


def record_compile_usage(
    run_id: str,
    used_directives: List[str],
    used_cards: List[str],
    used_passages: Optional[List[str]] = None,
    bundle_dir: Path = DEFAULT_BUNDLE_DIR,
) -> None:
    """Record emitted directives, Move Cards, and handbook citations into `agent_memory.db` (`usage_events` & `used_with`)."""
    if not bundle_available(bundle_dir):
        return
    conn = _connect_memory(bundle_dir)
    ts = _utc_now()
    nodes: List[Tuple[str, str]] = (
        [("directive", d) for d in sorted(set(used_directives))]
        + [("concept", f"move:{m}") for m in sorted(set(used_cards))]
        + [("passage", p) for p in sorted(set(used_passages or []))]
    )
    try:
        ctx = json.dumps({"compiler": "sakuga_Xperiment", "timestamp": ts})
        for kind, nid in nodes:
            conn.execute(
                "INSERT INTO usage_events (at, run_id, action, node_kind, node_id, context) VALUES (?, ?, 'compiled', ?, ?, ?)",
                (ts, run_id, kind, nid, ctx),
            )
        for i, (ak, aid) in enumerate(nodes):
            for bk, bid in nodes[i + 1 :]:
                a, b = sorted([(ak, aid), (bk, bid)])
                conn.execute(
                    "INSERT INTO used_with (a_kind, a_id, b_kind, b_id, count, last_at) VALUES (?, ?, ?, ?, 1, ?) "
                    "ON CONFLICT(a_kind, a_id, b_kind, b_id) DO UPDATE SET count = count + 1, last_at = excluded.last_at",
                    (a[0], a[1], b[0], b[1], ts),
                )
        conn.commit()
    finally:
        conn.close()


def kb_find(query_text: str, limit: int = 8, bundle_dir: Path = DEFAULT_BUNDLE_DIR) -> Dict[str, Any]:
    """Search across `handbook_index.db`, `agent_memory.db`, and `fight_move_system` Move Cards."""
    out: Dict[str, Any] = {"concepts": [], "move_cards": [], "tags": [], "passages": []}
    lex = Lexicon.load_default()
    q_lower = query_text.lower().strip()
    for cid, card in sorted(lex.cards_by_id.items()):
        hay = " ".join([cid.replace("_", " "), card["caption_words"]] + list(card.get("aliases", []))).lower()
        if any(tok in hay for tok in q_lower.split() if len(tok) >= 3):
            out["move_cards"].append(
                {
                    "id": cid,
                    "class": card["class"],
                    "limb": card["limb"],
                    "level": card["level"],
                    "caption_words": card["caption_words"],
                }
            )

    if not bundle_available(bundle_dir):
        return out

    conn = _connect_ro(bundle_dir / "handbook_index.db")
    mem_path = bundle_dir / "agent_memory.db"
    try:
        if mem_path.is_file():
            conn.execute("ATTACH DATABASE ? AS mem", (f"file:{mem_path}?mode=ro",))
        phrase = query_text if any(ch in query_text for ch in '"*') else " ".join(query_text.split())
        try:
            c_rows = conn.execute(
                "SELECT c.concept_id, c.label, c.kind FROM concept_fts JOIN concepts c ON c.concept_id = concept_fts.concept_id "
                "WHERE concept_fts MATCH ? ORDER BY bm25(concept_fts) LIMIT 5",
                (phrase,),
            ).fetchall()
            for r in c_rows:
                out["concepts"].append({"id": r["concept_id"], "label": r["label"], "kind": r["kind"]})
        except sqlite3.OperationalError:
            pass

        try:
            m_rows = conn.execute(
                "SELECT concept_id, label, kind, description FROM mem.agent_concepts WHERE lower(label) LIKE ? OR lower(aliases) LIKE ? LIMIT 5",
                (f"%{q_lower}%", f"%{q_lower}%"),
            ).fetchall()
            for r in m_rows:
                out["concepts"].append({"id": r["concept_id"], "label": r["label"], "kind": r["kind"]})
        except sqlite3.OperationalError:
            pass

        try:
            p_rows = conn.execute(
                "SELECT p.passage_id, p.moment_type, p.slot_id, p.intent_tier, p.heading_path, substr(p.text, 1, 180) AS excerpt "
                "FROM handbook_fts JOIN handbook_passages p ON p.passage_id = handbook_fts.passage_id "
                "WHERE handbook_fts MATCH ? ORDER BY bm25(handbook_fts) LIMIT ?",
                (phrase, limit),
            ).fetchall()
            for r in p_rows:
                out["passages"].append(
                    {
                        "passage_id": r["passage_id"],
                        "moment": r["moment_type"],
                        "slot": r["slot_id"],
                        "tier": r["intent_tier"],
                        "heading": r["heading_path"],
                        "excerpt": r["excerpt"],
                    }
                )
        except sqlite3.OperationalError:
            pass
    finally:
        conn.close()

    return out


def kb_lookup(
    moment: Optional[str] = None,
    slot: Optional[str] = None,
    limit: int = 8,
    bundle_dir: Path = DEFAULT_BUNDLE_DIR,
) -> Dict[str, Any]:
    """Lookup directives from `ai_video_compiler.db` and passages from `handbook_index.db` by moment and slot."""
    directives = load_semantic_directives(bundle_dir)
    matched_directives = [
        d
        for d in directives.values()
        if (moment is None or d["moment_type"] == moment) and (slot is None or d["slot_id"] == slot)
    ]

    passages: List[Dict[str, Any]] = []
    if bundle_available(bundle_dir):
        conn = _connect_ro(bundle_dir / "handbook_index.db")
        try:
            clauses = ["1=1"]
            params: List[Any] = []
            if moment:
                clauses.append("moment_type = ?")
                params.append(moment)
            if slot:
                clauses.append("slot_id = ?")
                params.append(slot)
            sql = (
                "SELECT passage_id, moment_type, moment_score, slot_id, slot_score, heading_path, substr(text, 1, 180) AS excerpt "
                f"FROM handbook_passages WHERE {' AND '.join(clauses)} "
                "ORDER BY (COALESCE(moment_score, 0) + COALESCE(slot_score, 0)) DESC LIMIT ?"
            )
            params.append(limit)
            for r in conn.execute(sql, tuple(params)).fetchall():
                passages.append(
                    {
                        "passage_id": r["passage_id"],
                        "moment": r["moment_type"],
                        "slot": r["slot_id"],
                        "score": (r["moment_score"] or 0) + (r["slot_score"] or 0),
                        "heading": r["heading_path"],
                        "excerpt": r["excerpt"],
                    }
                )
        finally:
            conn.close()

    return {
        "moment": moment,
        "slot": slot,
        "directives": matched_directives,
        "passages": passages,
    }
