"""Knowledge Base Bridge to `knowledge_base/` (vendored in-repo `anime_action_research_bundle`).

Connects `fight_move_system` (`sakuga_Xperiment`) to:
  1. `knowledge_base/agent/` (bundle-local prompt agent: `query.ask`, `propose`, `relations.follow`, `causal`, `knobs`, `discover`, `verify`)
  2. `knowledge_base/handbook_index.db` (21-chapter CPCS Domain Handbook FTS5 index, 18,120 passages, 3,302 blocks, 149 concepts) — READ-ONLY
  3. `knowledge_base/ai_video_compiler.db` (64-row `semantic_directives` catalog across 6 moments x 8 slots) — READ-ONLY
  4. `knowledge_base/agent_memory.db` (growing memory: tags, usage_events, used_with, agent_concepts, agent_links, causal_triples, module_relations) — READ/WRITE

Provides `query_kb_prior_to_semantic_intent(clip_or_request, ...)` so the Knowledge Base is queried *before* semantic intent / beat-by-beat compilation.
Never modifies any file listed in `SHA256SUMS.bundle`.
"""

import hashlib
import json
import os
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .lexicon import Lexicon

REPO_ROOT = Path(__file__).resolve().parent.parent
IN_REPO_KB_DIR = REPO_ROOT / "knowledge_base"
EXTERNAL_KB_DIR = Path("/Users/king/Downloads/anime_action_research_bundle")


def _resolve_default_bundle_dir() -> Path:
    env_dir = os.environ.get("ANIME_KB_BUNDLE_DIR")
    if env_dir:
        return Path(env_dir)
    if (IN_REPO_KB_DIR / "ai_video_compiler.db").is_file():
        return IN_REPO_KB_DIR
    return EXTERNAL_KB_DIR


DEFAULT_BUNDLE_DIR = _resolve_default_bundle_dir()

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


def _ensure_agent_importable(bundle_dir: Path = DEFAULT_BUNDLE_DIR) -> bool:
    """Ensure `knowledge_base/agent` can be imported as `agent`."""
    if not (bundle_dir / "agent" / "__init__.py").is_file():
        return False
    b_str = str(bundle_dir)
    if b_str not in sys.path:
        sys.path.insert(0, b_str)
    return True


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
    if not (bundle_dir / "ai_video_compiler.db").is_file():
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
    write_unindexed_concepts: bool = False,
) -> Dict[str, int]:
    """Bridge key handbook tags and links into `agent_memory.db` without breaking `agent verify`
    (which checks that every row in `agent_concepts` has been backfilled into `handbook_index.db`).
    """
    if not (bundle_dir / "agent_memory.db").is_file():
        return {"concepts_synced": 0, "links_synced": 0, "tags_synced": 0}

    lex = lexicon or Lexicon.load_default()
    conn = _connect_memory(bundle_dir)
    ts = _utc_now()
    concepts_count = len(BRIDGED_LEXICAL_CONCEPTS) + len(lex.cards_by_id)
    links_count = 0
    tags_count = 0
    try:
        if write_unindexed_concepts:
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
            for move_id, card in sorted(lex.cards_by_id.items()):
                cid = f"move:{move_id}"
                aliases = [move_id.replace("_", " ")] + list(card.get("aliases", []))
                desc = f"{card['class']} ({card['limb']}, {card['level']}): {card['caption_words']}"
                conn.execute(
                    "INSERT OR REPLACE INTO agent_concepts (concept_id, label, kind, aliases, description, created_at, created_by) "
                    "VALUES (?, ?, 'move_card', ?, ?, ?, 'fight_move_system')",
                    (cid, move_id.replace("_", " ").title(), json.dumps(aliases), desc, ts),
                )

        # Link existing indexed concepts to directives in agent_links
        indexed_links = [
            ("weight_load", "aa_action_weight_load"),
            ("hip_led_punch", "aa_action_hip_led_punch"),
            ("forearm_block", "aa_action_forearm_block"),
            ("hit_stop", "aa_time_contact_hitstop"),
            ("camera_lock", "aa_camera_contact_lock"),
            ("smear", "aa_subject_multiple_limb_smear"),
            ("shock_ring", "aa_secondary_contact_ring"),
            ("impact_star", "aa_secondary_angular_impact_star"),
            ("skid_gouge", "aa_env_skid_gouge"),
            ("ground_fracture", "aa_env_radial_fracture"),
            ("yutapon_cubes", "aa_env_yutapon_cubes"),
            ("guard_recovery", "aa_action_guard_recovery"),
        ]
        for cid, did in indexed_links:
            conn.execute(
                "INSERT OR REPLACE INTO agent_links (from_kind, from_id, to_kind, to_id, relation, note, created_at, created_by) "
                "VALUES ('concept', ?, 'directive', ?, 'implemented_by', 'bridged from fight_move_system lexicon', ?, 'fight_move_system')",
                (cid, did, ts),
            )
            links_count += 1

        # Tag key handbook passages for combat state, contact contract, and localized repair
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


def query_kb_prior_to_semantic_intent(
    clip_or_request: Any,
    taste: str = "heavy, brutal, old school",
    follow_depth: int = 2,
    discover_count: int = 2,
    knobs_spec: Optional[List[str]] = None,
    bundle_dir: Path = DEFAULT_BUNDLE_DIR,
) -> Dict[str, Any]:
    """Query the updated Knowledge Base (`agent.query.ask`, `agent.propose`, `agent.relations.follow`,
    `agent.causal.closure`, `agent.knobs`, and `runs/002_rooftop_cage_fight/provenance.json`)
    PRIOR to semantic intent decomposition and prompt compilation.
    """
    if isinstance(clip_or_request, dict):
        moves = []
        for m in clip_or_request.get("moments", []):
            for side in ("A", "B"):
                if m.get(side) and m[side].get("move"):
                    moves.append(m[side]["move"].replace("_", " "))
        arena = clip_or_request.get("arena", "bare-knuckle martial arts arena")
        request_text = (
            f"bare-knuckle anime fight in {arena}: " + ", ".join(moves[:12])
            if moves
            else f"bare-knuckle anime fight in {arena}"
        )
    else:
        request_text = str(clip_or_request)

    result: Dict[str, Any] = {
        "request": request_text,
        "taste": taste,
        "bundle_dir": str(bundle_dir),
        "moments": [],
        "slots": [],
        "concepts": [],
        "directives": [],
        "pulled_relations": [],
        "causal_chains": [],
        "knobs": {},
        "animation_grammar_rules": {},
        "rule_sources": {},
        "passages": [],
        "bridges": [],
        "gaps": {"handbook": [], "catalog": []},
    }

    # 1. Load Run 002 animation_grammar & provenance rules surfaced from the KB
    run002_prompt = bundle_dir / "runs" / "002_rooftop_cage_fight" / "prompt.json"
    run002_prov = bundle_dir / "runs" / "002_rooftop_cage_fight" / "provenance.json"
    if run002_prompt.is_file():
        try:
            p_doc = json.loads(run002_prompt.read_text(encoding="utf-8"))
            result["animation_grammar_rules"] = p_doc.get("animation_grammar", {})
        except Exception:
            pass
    if run002_prov.is_file():
        try:
            prov_doc = json.loads(run002_prov.read_text(encoding="utf-8"))
            result["rule_sources"] = prov_doc.get("rule_sources", {})
        except Exception:
            pass

    # 2. Load Diversity Knobs (`agent/data/knobs.json`)
    knobs_path = bundle_dir / "agent" / "data" / "knobs.json"
    if knobs_path.is_file():
        try:
            k_doc = json.loads(knobs_path.read_text(encoding="utf-8"))
            selected_knobs = knobs_spec or [
                "laban_profile=grounded_martial_arts",
                "exposure_cadence=twos_with_impact_hold",
                "smear_policy=limb_smear",
                "impact_accent=inverse_flash_and_ring",
                "camera_behavior=lateral_countertrack",
            ]
            for spec in selected_knobs:
                axis, _, opt_name = spec.partition("=")
                opt_obj = k_doc.get("axes", {}).get(axis, {}).get("options", {}).get(opt_name)
                if opt_obj:
                    result["knobs"][axis] = {
                        "option": opt_name,
                        "prose": opt_obj.get("prose", ""),
                        "from": opt_obj.get("from", []),
                        "prefers": opt_obj.get("prefers", []),
                    }
        except Exception:
            pass

    # 3. Query `agent` modules directly if `handbook_index.db` and `agent` package are available
    if _ensure_agent_importable(bundle_dir) and bundle_available(bundle_dir):
        try:
            from agent import catalog as ag_cat
            from agent import causal as ag_causal
            from agent import handbook as ag_hb
            from agent import knowledge as ag_kn
            from agent import policy as ag_pol
            from agent import query as ag_q
            from agent import relations as ag_rel
            from agent import taste as ag_taste

            conn = ag_hb.connect(bundle_dir / "handbook_index.db")
            ag_kn.attach_memory(conn, bundle_dir / "agent_memory.db")
            mem_conn = ag_kn.open_memory(bundle_dir / "agent_memory.db")
            try:
                cat = ag_cat.load_catalog(bundle_dir)
                pol = ag_pol.Policy(bundle_dir / "agent" / "data")
                tastes = ag_taste.load_profiles(bundle_dir / "agent" / "data" / "taste_profiles.json")

                ask_res = ag_q.ask(
                    conn,
                    request_text,
                    catalog=cat,
                    policy=pol,
                    tastes=tastes,
                    taste_text=taste,
                    limit_per=3,
                    max_concepts=4,
                    discover=discover_count,
                )
                result["moments"] = list(ask_res.get("moments", []))
                result["slots"] = list(ask_res.get("slots", []))
                result["concepts"] = list(ask_res.get("concepts", []))
                result["directives"] = list(ask_res.get("directives", []))
                result["gaps"] = dict(ask_res.get("gaps", {"handbook": [], "catalog": []}))

                for grp in ask_res.get("groups", []):
                    if grp.get("name") == "bridges":
                        result["bridges"].extend(grp.get("hits", []))
                    else:
                        result["passages"].extend(grp.get("hits", []))

                # Follow module_relations from primary actions
                seed_dirs = [
                    "aa_action_hip_led_punch",
                    "aa_action_forearm_block",
                    "aa_action_weight_load",
                ]
                pulled = ag_rel.follow(mem_conn, seed_dirs, depth=follow_depth)
                result["pulled_relations"] = [dict(p) for p in pulled]

                # Causal closure from seeded directive triples (`directive:aa_env_yutapon_cubes`, `directive:aa_action_hip_led_punch`, `hit_stop`)
                for c_seed in (
                    "directive:aa_env_yutapon_cubes",
                    "directive:aa_action_hip_led_punch",
                    "directive:aa_env_skid_gouge",
                    "hit_stop",
                ):
                    closure_rows = ag_causal.closure(mem_conn, c_seed, depth=2)
                    if closure_rows:
                        result["causal_chains"].extend([dict(r, seed=c_seed) for r in closure_rows])
            finally:
                mem_conn.close()
                conn.close()
        except Exception:
            pass

    return result


def resolve_beat_kb_guidance(
    a_card: Optional[Dict[str, Any]],
    b_card: Optional[Dict[str, Any]],
    is_hero: bool = False,
    beat_idx: int = 0,
    total_beats: int = 10,
    bundle_dir: Path = DEFAULT_BUNDLE_DIR,
) -> Dict[str, Any]:
    """Return structured KB directive IDs, module-relation pulled directives, and handbook citations for a single combat beat."""
    directives: List[str] = []
    handbook_refs: List[str] = [
        "src-additional-continous-combat-state-md#0315",
        "src-additional-continous-combat-state-md#0152",
        "src-additional-02-facs-laban-bartenieff-gap-closure-completed-md#0786",
    ]
    applied_rules: List[str] = []

    if beat_idx == 0:
        directives.extend(["aa_env_preimpact_quiet", "aa_time_hold_then_burst", "aa_subject_loaded_silhouette"])

    if a_card:
        if a_card["contact"] == "strike":
            directives.extend(["aa_action_weight_load", "aa_action_hip_led_punch", "aa_subject_angular_pose"])
            applied_rules.extend(["kinetic_chain", "hit_stop", "cause_before_effect", "camera_on_contact"])
            if a_card["limb"] not in {"lead_knee", "rear_knee"}:
                directives.append("aa_subject_multiple_limb_smear")
                applied_rules.append("smear")
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
                applied_rules.extend(["time_remap", "effects_after_contact"])
        elif a_card["contact"] == "block":
            directives.extend(["aa_action_forearm_block", "aa_camera_contact_lock", "aa_env_skid_gouge"])
            applied_rules.extend(["hit_stop", "camera_on_contact", "effects_after_contact"])
        elif a_card["contact"] == "grapple":
            if "shove" in a_card["id"]:
                directives.extend(["aa_action_absorb_recoil", "aa_env_skid_gouge", "aa_env_layered_dust", "aa_camera_whip_reacquire"])
                applied_rules.extend(["camera_between_contacts", "effects_after_contact", "cause_before_effect"])
            else:
                directives.append("aa_camera_contact_lock")
                applied_rules.extend(["camera_on_contact", "cause_before_effect"])
        else:
            directives.extend(["aa_camera_lateral_track", "aa_time_mixed_exposures"])
            applied_rules.extend(["camera_between_contacts", "exposure"])

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

    # Pull supporting rows via `module_relations` in `agent_memory.db` if available
    mem_path = bundle_dir / "agent_memory.db"
    if mem_path.is_file():
        try:
            conn = _connect_ro(mem_path)
            try:
                placeholders = ",".join("?" for _ in directives)
                if placeholders:
                    rows = conn.execute(
                        f"SELECT source, relation, target, passage_id FROM module_relations "
                        f"WHERE source IN ({placeholders}) OR target IN ({placeholders})",
                        tuple(directives) + tuple(directives),
                    ).fetchall()
                    for r in rows:
                        for cand in (r["source"], r["target"]):
                            if isinstance(cand, str) and cand.startswith("aa_"):
                                directives.append(cand)
            finally:
                conn.close()
        except Exception:
            pass

    # Deduplicate preserving order
    seen = set()
    deduped = []
    for d in directives:
        if d not in seen:
            seen.add(d)
            deduped.append(d)

    seen_rules = set()
    deduped_rules = []
    for r in applied_rules:
        if r not in seen_rules:
            seen_rules.add(r)
            deduped_rules.append(r)

    return {
        "directives": deduped,
        "handbook_refs": handbook_refs,
        "applied_rules": deduped_rules,
    }


def record_compile_usage(
    run_id: str,
    used_directives: List[str],
    used_cards: List[str],
    used_passages: Optional[List[str]] = None,
    bundle_dir: Path = DEFAULT_BUNDLE_DIR,
) -> None:
    """Record emitted directives and valid handbook citations into `agent_memory.db` (`usage_events` & `used_with`),
    preserving `agent verify` invariants (`memory_directive_refs_known` and `memory_passage_refs_resolve`).
    """
    if not bundle_available(bundle_dir):
        return
    conn = _connect_memory(bundle_dir)
    idx_conn = _connect_ro(bundle_dir / "handbook_index.db")
    ts = _utc_now()
    try:
        valid_directives = [
            d
            for d in sorted(set(used_directives))
            if idx_conn.execute(
                "SELECT 1 FROM directive_requires WHERE directive_id = ? UNION SELECT 1 FROM directive_passages WHERE directive_id = ?",
                (d, d),
            ).fetchone()
            is not None
        ]
        valid_passages = [
            p
            for p in sorted(set(used_passages or []))
            if idx_conn.execute("SELECT 1 FROM handbook_passages WHERE passage_id = ?", (p,)).fetchone() is not None
        ]
        nodes: List[Tuple[str, str]] = (
            [("directive", d) for d in valid_directives]
            + [("passage", p) for p in valid_passages]
        )
        ctx = json.dumps({"compiler": "sakuga_Xperiment", "cards": sorted(set(used_cards)), "timestamp": ts})
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
        idx_conn.close()
        conn.close()


def kb_find(query_text: str, limit: int = 8, bundle_dir: Path = DEFAULT_BUNDLE_DIR) -> Dict[str, Any]:
    """Search across `handbook_index.db` (using Slice 3c `find2` alias expansion + diversity rerank when available),
    `agent_memory.db`, and `fight_move_system` Move Cards.
    """
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

    if _ensure_agent_importable(bundle_dir):
        try:
            from agent import handbook as ag_hb
            from agent import knowledge as ag_kn
            from agent import query as ag_q

            conn = ag_hb.connect(bundle_dir / "handbook_index.db")
            ag_kn.attach_memory(conn, bundle_dir / "agent_memory.db")
            try:
                res = ag_q.find2(conn, query_text, limit=limit)
                out["concepts"] = list(res.get("concepts", []))
                out["tags"] = list(res.get("tags", []))
                out["passages"] = list(res.get("passages", []))
                return out
            finally:
                conn.close()
        except Exception:
            pass

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
        if _ensure_agent_importable(bundle_dir):
            try:
                from agent import handbook as ag_hb
                from agent import knowledge as ag_kn
                from agent import query as ag_q

                conn = ag_hb.connect(bundle_dir / "handbook_index.db")
                ag_kn.attach_memory(conn, bundle_dir / "agent_memory.db")
                try:
                    hits, _ = ag_q.lookup2(conn, moment=moment, slot=slot, min_score=1, limit=limit)
                    passages = list(hits)
                    return {
                        "moment": moment,
                        "slot": slot,
                        "directives": matched_directives,
                        "passages": passages,
                    }
                finally:
                    conn.close()
            except Exception:
                pass

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


def kb_verify(bundle_dir: Path = DEFAULT_BUNDLE_DIR) -> Dict[str, Any]:
    """Run both SHA256SUMS.bundle integrity and the 25-check `agent.verify.run()` suite."""
    sha_ok, sha_errs = verify_bundle_integrity(bundle_dir)
    agent_verify_res: Dict[str, Any] = {"ok": sha_ok, "checks": []}
    if _ensure_agent_importable(bundle_dir) and bundle_available(bundle_dir):
        try:
            from agent import verify as ag_vf

            agent_verify_res = dict(
                ag_vf.run(
                    index_path=bundle_dir / "handbook_index.db",
                    memory_path=bundle_dir / "agent_memory.db",
                )
            )
        except Exception as e:
            agent_verify_res = {"ok": False, "error": str(e)}
    return {
        "sha256_bundle_ok": sha_ok,
        "sha256_errors": sha_errs,
        "agent_verify": agent_verify_res,
        "ok": bool(sha_ok and agent_verify_res.get("ok", True)),
    }
