#!/usr/bin/env python3
"""
TwelveLabs Full Account & Multi-Tier Video Intelligence Bridge (`twelvelabs_bridge.py`)
For `Movement_Prose` / `sakuga-fight-director` (`SAKUGA-MLLM-3.1-CAUSAL`).

Capabilities:
1. Full Conversational TwelveLabs Account Control:
   - `auth`: Save or verify your `TWELVELABS_API_KEY` persistently (`~/.config/sakuga/twelvelabs.json` or `.env`).
   - `account`: Inspect indexes, video counts, and active engines (`pegasus1.2` + `marengo2.7`).
   - `videos`: List all indexed videos in your TwelveLabs account with durations, FPS, and IDs.
   - `upload`: Upload local `.mp4`/`.mov` files (or URLs) and index them with BOTH Pegasus 1.2 & Marengo 2.7.
   - `search`: Run Marengo 2.7 semantic visual + audio moment search across your entire video library.
   - `ask`: Conversational Q&A with Pegasus 1.2 about any specific video or timestamp window.

2. Three-Tier Video Extraction Engine (`extract --tier fast | medium | full`):
   - `--tier fast`   (1 API call, ~5s): Rapid storyboard, fighter silhouettes, 180° cross timestamp, macro C01->C10 beat list.
   - `--tier medium` (2 API calls, ~12s): Gist + Full `SAKUGA-MLLM-3.1-CAUSAL` kinematic/causal/contact/prop extraction.
   - `--tier full`   (6-Pass Complete Extraction): Extracts 100% of TwelveLabs' capabilities for the LLM:
       Pass 1: System Video Metadata (exact FPS, resolution, duration, audio tracks).
       Pass 2: Semantic Gist (`POST /gist` -> Title, Topics, Hashtags).
       Pass 3: Summaries, Timestamped Chapters & Highlights (`POST /summarize` x3).
       Pass 4: Deep Pegasus Pass A -> Biomechanics, Causal Graph (`C01->C12`), 6D `axis`, Laban `arc`, `support`, 3-phase `contact`.
       Pass 5: Deep Pegasus Pass B -> Camera FOV/Cuts/Overshoot, Sakuga Smear X-Sheet, Prop Parabolas & Cross-Modal Audio Impulse Track.
       Pass 6: Marengo 2.7 Temporal Action Search (`POST /search` for impacts, evasions, spins, and finishers with sub-second confidence windows).

3. Closed-Loop Render QA (`audit-render`):
   - Compares a rendered Seedance/Kling video against a `SAKUGA-MLLM-3.1-CAUSAL` JSON spec beat-by-beat and extracts the true `t=10.0s` handoff state for Clip N+1.
"""

import argparse
import json
import mimetypes
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

TWELVELABS_API_BASE = "https://api.twelvelabs.io/v1.3"
CONFIG_FILE = Path.home() / ".config" / "sakuga" / "twelvelabs.json"
DEFAULT_INDEX_NAME = "movement-prose-sakuga-dual-engine"

# ============================================================================
# EXTRACTION PROMPTS (FAST, MEDIUM, AND FULL 2-PART DEEP PASSES)
# ============================================================================

FAST_PASS_PROMPT = """You are a Sakuga fight choreographer doing a FAST PASS storyboard scout of this video.
Output a valid JSON object (and nothing else) with:
{
  "pass_tier": "fast",
  "clip_summary": "1-sentence overview of the fight exchange and style",
  "duration_sec": 10.0,
  "fighters": {
    "A": "Primary fighter appearance, build, and weapon",
    "B": "Opponent appearance, build, and weapon"
  },
  "screen_geometry_and_cross": "Who starts on screen_left vs screen_right, and the exact timestamp + move where they cross sides",
  "macro_beats": [
    {"t": 0.0, "id": "C01", "action": "concise description of move and contact/dodge"}
  ]
}"""

MEDIUM_PASS_PROMPT = """You are an expert 2D Sakuga martial arts fight choreographer and biomechanical motion analyst.
Analyze this fight video clip second-by-second (at 24fps precision) and extract a structured Causal Choreography Breakdown so it can be converted into a SAKUGA-MLLM-3.1-CAUSAL specification.

Output a valid JSON object (and nothing else) following this exact structure:
{
  "pass_tier": "medium",
  "clip_summary": "1-sentence summary of the martial arts exchange and tempo",
  "duration_sec": 10.0,
  "screen_geometry": "Describe who starts on screen_left vs screen_right, and the EXACT timestamp (e.g. t=4.9s) and move (vault/duck/step-through) where they physically cross sides. Note if camera ever flips the 180-degree line.",
  "fighters": {
    "A": "Primary driver/attacker build, stance, and starting weapon/hand (e.g. right_hand reverse_grip)",
    "B": "Opponent build, stance, and starting weapon/hand"
  },
  "causal_beats": [
    {
      "t": 0.0,
      "node_id": "C01",
      "beat_name": "short_slug",
      "causal_chain": "requires: [prior torque/recoil/opening] -> timing: [BEFORE_ATTACK_INTERSECTION if dodge/parry] -> preserves: [momentum type] -> causes: [next state]",
      "A_kinematics": {
        "pos_estimate_m": [0.0, 0.78, 2.8],
        "vel_estimate": [0.0, 0.0, 3.5],
        "axis": "head:+Y_up, torso/hips:[state], facing:[+Z or -Z], screen_side:[left or right]",
        "arc": "[Laban Effort: PUNCH/SLASH/DAB/FLICK/PRESS/WRING/GLIDE] + [clock-face arc e.g. 7_to_1_clock or 360deg_cw_spin]",
        "support": "[Positive-only ground/surface lock, e.g. both_boots_planted_flat_on_floor or left_boot_planted_pivot]",
        "contact": "pre:[approach/commitment] -> hit:[A_limb_deforms_B_part_at_[x,y,z]_zero_gap] -> post:[follow_through_and_B_reaction] (OR evasion_corridor:[clearance in cm under/past B attack])",
        "limbs": "L:[left arm state]; R:[right arm + weapon state]; feet:[stance/kick state]",
        "pose": "[IMPACT FRAME (hold Xf) or ANTICIPATION HOLD] + vivid description of the physical weight transfer"
      },
      "B_reaction": {
        "pos_estimate_m": [0.0, 1.0, 4.2],
        "axis": "head:+Y_up, torso:[state], facing:[-Z or +Z], screen_side:[right or left]",
        "support": "[Positive support state, e.g. both_boots_skidding_backward]",
        "contact": "[How B's body/guard/weapon receives or whiffs the contact]",
        "action": "short_action_slug",
        "pose": "What B is doing and how B's posture breaks/recoils AFTER contact"
      },
      "props": {
        "weapon_A": "owner:[A_right_hand/A_left_hand/airborne], state/event",
        "weapon_B": "owner:[B_both_hands/none_airborne_disarmed/A_left_hand], state/event"
      },
      "camera_and_sakuga": {
        "shot": "shot type (e.g. tight_profile_impact, low_angle_weave)",
        "fov_estimate": 34,
        "look_anchor": "exact contact point camera is centered on",
        "hold_frames": 3,
        "smear_isolation": "Which single limb smears on what clock-face arc while head and torso stay solid"
      }
    }
  ]
}"""

FULL_PASS_PART_A_BIOMECHANICS_PROMPT = """You are conducting PASS A (Deep Biomechanical, Causal Graph & Laban Kinematics) of a FULL PASS video extraction.
Analyze every sub-second combat beat in this video with maximum anatomical and physical detail.
Output a valid JSON object (and nothing else) with:
{
  "fighters_detailed": {
    "A": {"silhouette": "...", "costume_and_colors": "...", "proportions": "...", "starting_weapon_and_grip": "...", "martial_arts_style": "..."},
    "B": {"silhouette": "...", "costume_and_colors": "...", "proportions": "...", "starting_weapon_and_grip": "...", "martial_arts_style": "..."}
  },
  "screen_geometry_timeline": [
    {"t_range": "0.0-4.9", "A_screen_side": "left", "B_screen_side": "right", "cross_event_at_end": "describe exact vault/duck/pass"}
  ],
  "causal_beats": [
    {
      "t": 0.0,
      "node_id": "C01",
      "beat": "beat_slug",
      "causal": "C01: requires: [...] -> timing: [BEFORE_..._INTERSECTION] -> preserves: [...] -> causes: [...]",
      "laban_effort": {"action": "PUNCH|SLASH|DAB|FLICK|PRESS|WRING|GLIDE", "weight": "heavy|light", "time": "sudden|sustained", "space": "direct|indirect", "flow": "bound|free"},
      "A_beat": {
        "pos": [0.0, 0.78, 2.8],
        "vel": [0.0, 0.0, 3.6],
        "axis": "head:..., torso:..., hips:..., facing:..., screen_side:...",
        "arc": "rotation degrees + clock-face trajectory arc",
        "support": "positive-only foot/hand ground or surface lock",
        "contact": "pre:... -> hit:..._zero_gap -> post:... (or evasion_corridor:...)",
        "limbs": "L:...; R:...; feet:...",
        "pose": "full biomechanical narrative including anticipation/impact hold"
      },
      "B_beat": {
        "pos": [0.0, 1.0, 4.2],
        "axis": "head:..., torso:..., facing:..., screen_side:...",
        "support": "positive ground/guard/skid state",
        "contact": "how B initiates or absorbs the force",
        "launch_vel": [0.0, 0.0, 0.0],
        "action": "action_slug",
        "pose": "full defender reaction narrative"
      }
    }
  ]
}"""

FULL_PASS_PART_B_CINEMATOGRAPHY_SAKUGA_AUDIO_PROMPT = """You are conducting PASS B (Cinematography, Sakuga Exposure Sheet, Prop Physics, Environment & Cross-Modal Audio Impulse Analysis) of a FULL PASS video extraction.
Analyze the visual animation techniques, camera mechanics, props, environment, and audio track of this video at sub-second precision.
Output a valid JSON object (and nothing else) with:
{
  "visual_style_and_medium": {
    "animation_medium": "e.g. 2D cel-shaded / genga sketch / sumi-e ink / 3D CGI / live action",
    "line_art_weight_and_rule": "outline thickness, broken lines on smears, impact frame ink weight",
    "shading_and_palette": "flat cel vs 2-tone vs soft gradient, dominant colors, rim lighting",
    "framerate_modulation": "on ones (24fps) vs on twos (12fps) vs on threes (8fps) and where it shifts"
  },
  "prop_state_machines": {
    "<prop_name>": [
      {"t": 0.0, "state": "...", "owner": "A_right_hand|B_both_hands|none_airborne_disarmed", "grip": "...", "pos_if_airborne": [0, 2.1, 4.2], "event": "..."}
    ]
  },
  "environment_and_surface_physics": {
    "setting_description": "detailed background and lighting layout",
    "floor_and_support_surfaces": "stone, wood, water, pillars, tables",
    "environmental_destruction_events": [
      {"t": 0.0, "surface": "...", "deformation_or_debris": "...", "persists_until_end": true}
    ]
  },
  "camera_track": [
    {
      "t": 0.0,
      "shot": "shot scale and angle",
      "fov_estimate": 34,
      "pos_estimate": [1.4, 0.75, 3.2],
      "look": "exact focal target in frame",
      "move": "TRACK / TILT_UP / SNAP_ZOOM / OVERSHOOT / DOLLY",
      "preserve_axis": true,
      "hold_frames": 0,
      "time_remap": 1.0,
      "effect": "camera_shake / chromatic_aberration / flash"
    }
  ],
  "sakuga_exposure_sheet": {
    "impact_frames": [0.8, 1.5],
    "anticipation_holds": [4.4],
    "time_remap_windows": {"3.3-3.5": 0.25},
    "smear_frames": [
      "t_start-t_end: exact limb and clock-face smear arc; explicitly state which body parts stay solid"
    ],
    "speed_lines": ["0.0-0.8"],
    "fx_by_timestamp": {"0.8": "sparks / dust ring / shockwave / contrast inversion"}
  },
  "audio_impulse_track": [
    {"t": 0.8, "type": "metallic_clash|body_impact|whoosh|foot_skid|vocal|music_accent", "description": "exact sound and intensity"}
  ]
}"""


def build_mode_b_audit_prompt(spec_json: Dict[str, Any]) -> str:
    compact_beats = [
        {
            "t": b.get("t"),
            "causal": b.get("causal"),
            "support": b.get("support"),
            "contact": b.get("contact"),
            "pose": b.get("pose"),
        }
        for b in spec_json.get("A_beats", [])
    ]
    return f"""You are a Sakuga Animation Technical Director auditing an AI-generated fight render against its target SAKUGA-MLLM-3.1-CAUSAL choreography specification.

Target Beat Specification:
{json.dumps(compact_beats, indent=2)}

Inspect the video carefully and output a valid JSON object (and nothing else) with:
1. "overall_score_out_of_10": number,
2. "beat_audit": For each timestamp `t` in the spec, report:
   - "t": timestamp,
   - "status": "PASS" | "DRIFT" | "AIR_HIT" | "EARLY_FLINCH" | "PROP_GLITCH",
   - "observed": what actually happened on screen at this timestamp,
   - "fix_recommendation": if not PASS, what kinematic/support/contact change will fix it.
3. "final_frame_handoff_state" (at t=8.5s to 10.0s, for stitching Clip N+1 at t=0.0s):
   - "A_pos_estimate": [x, y, z],
   - "A_axis_and_screen_side": "head:..., facing:..., screen_side:left|right",
   - "A_support": "exact grounded stance in final frame",
   - "B_pos_estimate": [x, y, z],
   - "B_axis_and_screen_side": "head:..., facing:..., screen_side:left|right",
   - "B_support": "exact stance/pinned state in final frame",
   - "prop_ownership": "exact hand holding each weapon at t=10.0s"
"""


# ============================================================================
# AUTHENTICATION & HTTP CLIENT
# ============================================================================

def get_api_key(explicit_key: Optional[str] = None) -> str:
    if explicit_key:
        return explicit_key.strip()
    env_key = os.environ.get("TWELVELABS_API_KEY", "").strip()
    if env_key:
        return env_key
    # Check local .env file
    for env_path in [Path(".env"), Path(__file__).resolve().parent.parent / ".env"]:
        if env_path.exists():
            for line in env_path.read_text(encoding="utf-8").splitlines():
                if line.strip().startswith("TWELVELABS_API_KEY="):
                    val = line.split("=", 1)[1].strip().strip("'\"")
                    if val:
                        return val
    # Check persistent config file
    if CONFIG_FILE.exists():
        try:
            cfg = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            if cfg.get("api_key"):
                return cfg["api_key"].strip()
        except Exception:
            pass
    raise RuntimeError(
        "No TwelveLabs API key found.\n"
        "Set it once with:\n"
        "  python3 scripts/twelvelabs_bridge.py auth --set-key 'tlk_YOUR_KEY'\n"
        "Or export TWELVELABS_API_KEY='tlk_YOUR_KEY'"
    )


def save_api_key(api_key: str, default_index_id: Optional[str] = None) -> None:
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    cfg: Dict[str, Any] = {}
    if CONFIG_FILE.exists():
        try:
            cfg = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception:
            cfg = {}
    cfg["api_key"] = api_key.strip()
    if default_index_id:
        cfg["default_index_id"] = default_index_id
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
    os.chmod(CONFIG_FILE, 0o600)


def api_request(
    method: str,
    endpoint: str,
    api_key: str,
    json_body: Optional[Dict[str, Any]] = None,
    raw_body: Optional[bytes] = None,
    content_type: str = "application/json",
) -> Dict[str, Any]:
    url = f"{TWELVELABS_API_BASE}{endpoint}"
    headers = {"x-api-key": api_key}
    data = None
    if json_body is not None:
        data = json.dumps(json_body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    elif raw_body is not None:
        data = raw_body
        headers["Content-Type"] = content_type

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            body_text = resp.read().decode("utf-8")
            try:
                return json.loads(body_text)
            except json.JSONDecodeError:
                combined_text = []
                for line in body_text.splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        ev = json.loads(line)
                        if "text" in ev:
                            combined_text.append(ev["text"])
                        elif "data" in ev and isinstance(ev["data"], str):
                            combined_text.append(ev["data"])
                    except json.JSONDecodeError:
                        pass
                return {"data": "".join(combined_text) or body_text}
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"TwelveLabs API HTTP {e.code} on {endpoint}: {err_body}") from e


def try_parse_json_str(text: str) -> Any:
    """Extract and parse JSON block from Pegasus text output if wrapped in markdown fences."""
    if not isinstance(text, str):
        return text
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
    brace_start = cleaned.find("{")
    brace_end = cleaned.rfind("}")
    if brace_start != -1 and brace_end != -1 and brace_end > brace_start:
        try:
            return json.loads(cleaned[brace_start : brace_end + 1])
        except json.JSONDecodeError:
            pass
    return text


# ============================================================================
# ACCOUNT, INDEX & VIDEO MANAGEMENT
# ============================================================================

def list_indexes(api_key: str) -> List[Dict[str, Any]]:
    resp = api_request("GET", "/indexes?page=1&page_limit=50", api_key)
    return resp.get("data", [])


def get_or_create_dual_engine_index(
    api_key: str, index_name: str = DEFAULT_INDEX_NAME
) -> str:
    """Get or create an index with BOTH Pegasus 1.2 (generative analysis) and Marengo 2.7 (temporal search/embeddings)."""
    for idx in list_indexes(api_key):
        if idx.get("index_name") == index_name:
            return idx["_id"]

    print(
        f"[TwelveLabs] Creating dual-engine index '{index_name}' (pegasus1.2 + marengo2.7)...",
        file=sys.stderr,
    )
    create_body = {
        "index_name": index_name,
        "models": [
            {"model_name": "pegasus1.2", "model_options": ["visual", "audio"]},
            {"model_name": "marengo2.7", "model_options": ["visual", "audio"]},
        ],
        "addons": ["thumbnail"],
    }
    created = api_request("POST", "/indexes", api_key, json_body=create_body)
    return created["_id"]


def list_videos_in_index(api_key: str, index_id: str) -> List[Dict[str, Any]]:
    resp = api_request("GET", f"/indexes/{index_id}/videos?page=1&page_limit=50", api_key)
    return resp.get("data", [])


def find_video_index_id(api_key: str, video_id: str, explicit_index_id: Optional[str] = None) -> Optional[str]:
    if explicit_index_id:
        return explicit_index_id
    for idx in list_indexes(api_key):
        idx_id = idx["_id"]
        try:
            vids = list_videos_in_index(api_key, idx_id)
            for v in vids:
                if v.get("_id") == video_id:
                    return idx_id
        except Exception:
            continue
    return None


def upload_video_to_index(api_key: str, index_id: str, video_path: Path) -> str:
    boundary = f"----SakugaBoundary{uuid.uuid4().hex}"
    mime_type = mimetypes.guess_type(str(video_path))[0] or "video/mp4"
    file_bytes = video_path.read_bytes()

    parts = [
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="index_id"\r\n\r\n'
        f"{index_id}\r\n".encode("utf-8"),
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="video_file"; filename="{video_path.name}"\r\n'
        f"Content-Type: {mime_type}\r\n\r\n".encode("utf-8")
        + file_bytes
        + b"\r\n",
        f"--{boundary}--\r\n".encode("utf-8"),
    ]
    raw_body = b"".join(parts)
    content_type = f"multipart/form-data; boundary={boundary}"

    print(f"[TwelveLabs] Uploading '{video_path.name}' to index {index_id}...", file=sys.stderr)
    task = api_request("POST", "/tasks", api_key, raw_body=raw_body, content_type=content_type)
    task_id = task["_id"]

    while True:
        status_resp = api_request("GET", f"/tasks/{task_id}", api_key)
        status = status_resp.get("status")
        print(f"[TwelveLabs] Indexing status: {status}...", file=sys.stderr)
        if status == "ready":
            return status_resp["video_id"]
        if status in ("failed", "error"):
            raise RuntimeError(f"TwelveLabs video indexing failed: {status_resp}")
        time.sleep(3)


def resolve_video_and_index(
    api_key: str, video_arg: str, explicit_index_id: Optional[str] = None
) -> Tuple[str, Optional[str]]:
    path = Path(video_arg)
    if path.exists() and path.is_file():
        idx_id = explicit_index_id or get_or_create_dual_engine_index(api_key)
        vid_id = upload_video_to_index(api_key, idx_id, path)
        return vid_id, idx_id
    idx_id = find_video_index_id(api_key, video_arg, explicit_index_id)
    return video_arg, idx_id


# ============================================================================
# TWELVELABS EXTRACTION ENDPOINTS (METADATA, GIST, SUMMARIZE, ANALYZE, SEARCH)
# ============================================================================

def get_video_metadata(
    api_key: str, index_id: str, video_id: str, include_embeddings: bool = False
) -> Dict[str, Any]:
    q = "?embed=true" if include_embeddings else ""
    return api_request("GET", f"/indexes/{index_id}/videos/{video_id}{q}", api_key)


def get_video_gist(api_key: str, video_id: str) -> Dict[str, Any]:
    body = {"video_id": video_id, "types": ["title", "topic", "hashtag"]}
    return api_request("POST", "/gist", api_key, json_body=body)


def get_video_summaries_chapters_highlights(api_key: str, video_id: str) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for stype in ["summary", "chapter", "highlight"]:
        try:
            resp = api_request(
                "POST",
                "/summarize",
                api_key,
                json_body={"video_id": video_id, "type": stype},
            )
            out[stype] = resp.get(stype + "s", resp.get("summary", resp))
        except Exception as e:
            out[stype] = f"unavailable: {e}"
    return out


def analyze_video_with_pegasus(
    api_key: str, video_id: str, prompt: str, temperature: float = 0.1
) -> Any:
    body = {
        "video_id": video_id,
        "prompt": prompt,
        "temperature": temperature,
        "stream": False,
    }
    resp = api_request("POST", "/analyze", api_key, json_body=body)
    raw_text = resp.get("data", resp)
    return try_parse_json_str(raw_text)


def search_moments_in_index(
    api_key: str,
    index_id: str,
    query_text: str,
    video_id_filter: Optional[str] = None,
    page_limit: int = 10,
) -> List[Dict[str, Any]]:
    """Run Marengo 2.7 visual+audio temporal search to locate exact sub-second action windows."""
    boundary = f"----SakugaSearch{uuid.uuid4().hex}"
    fields: List[Tuple[str, str]] = [
        ("index_id", index_id),
        ("query_text", query_text),
        ("search_options", "visual"),
        ("search_options", "audio"),
        ("page_limit", str(page_limit)),
    ]
    if video_id_filter:
        fields.append(("filter", json.dumps({"id": [video_id_filter]})))

    parts = []
    for k, v in fields:
        parts.append(
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="{k}"\r\n\r\n'
            f"{v}\r\n".encode("utf-8")
        )
    parts.append(f"--{boundary}--\r\n".encode("utf-8"))
    raw_body = b"".join(parts)
    content_type = f"multipart/form-data; boundary={boundary}"

    resp = api_request("POST", "/search", api_key, raw_body=raw_body, content_type=content_type)
    return resp.get("data", [])


# ============================================================================
# MULTI-TIER EXTRACTION ORCHESTRATOR (FAST | MEDIUM | FULL)
# ============================================================================

def run_tiered_extraction(
    api_key: str,
    video_arg: str,
    tier: str,
    explicit_index_id: Optional[str] = None,
    include_embeddings: bool = False,
) -> Dict[str, Any]:
    video_id, index_id = resolve_video_and_index(api_key, video_arg, explicit_index_id)

    if tier == "fast":
        print(f"[TwelveLabs FAST PASS] Running 1-call Pegasus scout on video_id={video_id}...", file=sys.stderr)
        analysis = analyze_video_with_pegasus(api_key, video_id, FAST_PASS_PROMPT)
        return {
            "extraction_tier": "fast",
            "video_id": video_id,
            "index_id": index_id,
            "fast_storyboard": analysis,
        }

    elif tier == "medium":
        print(f"[TwelveLabs MEDIUM PASS] Step 1/2: Extracting semantic gist for video_id={video_id}...", file=sys.stderr)
        gist = {}
        try:
            gist = get_video_gist(api_key, video_id)
        except Exception as e:
            gist = {"warning": str(e)}

        print(f"[TwelveLabs MEDIUM PASS] Step 2/2: Extracting SAKUGA-MLLM-3.1-CAUSAL kinematics...", file=sys.stderr)
        choreo = analyze_video_with_pegasus(api_key, video_id, MEDIUM_PASS_PROMPT)
        return {
            "extraction_tier": "medium",
            "video_id": video_id,
            "index_id": index_id,
            "gist": gist,
            "sakuga_causal_extraction": choreo,
        }

    elif tier == "full":
        dossier: Dict[str, Any] = {
            "extraction_tier": "full",
            "video_id": video_id,
            "index_id": index_id,
        }

        # Pass 1: System Video Metadata & Optional Marengo Embeddings
        print(f"[TwelveLabs FULL PASS 1/6] Fetching system metadata & telemetry...", file=sys.stderr)
        if index_id:
            try:
                meta = get_video_metadata(api_key, index_id, video_id, include_embeddings=include_embeddings)
                dossier["system_metadata"] = meta.get("system_metadata", meta)
                if include_embeddings and "embedding" in meta:
                    dossier["marengo_embeddings"] = meta["embedding"]
            except Exception as e:
                dossier["system_metadata"] = {"warning": str(e)}

        # Pass 2: Gist (Title, Topics, Hashtags)
        print(f"[TwelveLabs FULL PASS 2/6] Extracting Gist (title, topics, hashtags)...", file=sys.stderr)
        try:
            dossier["gist"] = get_video_gist(api_key, video_id)
        except Exception as e:
            dossier["gist"] = {"warning": str(e)}

        # Pass 3: Summarize + Timestamped Chapters + Highlights
        print(f"[TwelveLabs FULL PASS 3/6] Extracting Summary, Timestamped Chapters & Highlights...", file=sys.stderr)
        dossier["temporal_segmentation"] = get_video_summaries_chapters_highlights(api_key, video_id)

        # Pass 4: Deep Pegasus Pass A (Biomechanics, Causal Graph C01->C12, Laban, 3-Phase Contact)
        print(f"[TwelveLabs FULL PASS 4/6] Running Deep Pegasus Pass A (Biomechanics, Causal Graph & Laban)...", file=sys.stderr)
        dossier["pass_a_biomechanics_and_causal_graph"] = analyze_video_with_pegasus(
            api_key, video_id, FULL_PASS_PART_A_BIOMECHANICS_PROMPT
        )

        # Pass 5: Deep Pegasus Pass B (Cinematography, Sakuga X-Sheet, Props, Environment & Audio Impulses)
        print(f"[TwelveLabs FULL PASS 5/6] Running Deep Pegasus Pass B (Camera, Sakuga Smears, Props & Audio Track)...", file=sys.stderr)
        dossier["pass_b_cinematography_sakuga_and_audio"] = analyze_video_with_pegasus(
            api_key, video_id, FULL_PASS_PART_B_CINEMATOGRAPHY_SAKUGA_AUDIO_PROMPT
        )

        # Pass 6: Marengo 2.7 Temporal Action Search Verification
        print(f"[TwelveLabs FULL PASS 6/6] Running Marengo 2.7 sub-second temporal action grounding...", file=sys.stderr)
        if index_id:
            marengo_moments: Dict[str, Any] = {}
            for q_label, q_text in [
                ("impacts_and_clashes", "weapon clash sparks or heavy strike impact"),
                ("evasions_and_vaults", "dodge weave duck or acrobatic shoulder vault"),
                ("spins_and_sweeps", "spinning kick or low leg sweep"),
                ("finisher_and_lock", "final knockdown chest pin or blade lock at throat"),
            ]:
                try:
                    hits = search_moments_in_index(
                        api_key, index_id, q_text, video_id_filter=video_id, page_limit=5
                    )
                    marengo_moments[q_label] = [
                        {
                            "start_sec": h.get("start"),
                            "end_sec": h.get("end"),
                            "confidence": h.get("confidence"),
                            "score": h.get("score"),
                        }
                        for h in hits
                    ]
                except Exception as e:
                    marengo_moments[q_label] = f"search unavailable on this index: {e}"
            dossier["pass_c_marengo_temporal_grounding"] = marengo_moments

        return dossier

    raise ValueError(f"Unknown tier: {tier}")


# ============================================================================
# CLI ENTRYPOINT
# ============================================================================

def main() -> int:
    parser = argparse.ArgumentParser(
        description="TwelveLabs Full Account & Multi-Tier Video Intelligence Bridge (fast | medium | full)"
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    # 1. auth
    p_auth = sub.add_parser("auth", help="Save or verify your TwelveLabs API key persistently")
    p_auth.add_argument("--set-key", default=None, help="Save your TWELVELABS_API_KEY to ~/.config/sakuga/twelvelabs.json")
    p_auth.add_argument("--status", action="store_true", help="Check if API key is configured and valid")

    # 2. account
    sub.add_parser("account", help="Inspect your TwelveLabs account indexes, engines, and video counts")

    # 3. videos
    p_vids = sub.add_parser("videos", help="List all indexed videos in your TwelveLabs account")
    p_vids.add_argument("--index-id", default=None, help="Optional specific index_id")

    # 4. upload
    p_up = sub.add_parser("upload", help="Upload and index a local video with both Pegasus 1.2 & Marengo 2.7")
    p_up.add_argument("video_path", type=Path, help="Path to local .mp4/.mov video file")
    p_up.add_argument("--index-id", default=None, help="Optional target index_id")

    # 5. extract (Supports --tier fast | medium | full)
    p_ext = sub.add_parser(
        "extract",
        aliases=["extract-ref"],
        help="Run a Fast, Medium, or Full Pass extraction on a video (file path or video_id)",
    )
    p_ext.add_argument(
        "video",
        nargs="?",
        default=None,
        help="Local video path (.mp4/.mov) OR existing TwelveLabs video_id",
    )
    p_ext.add_argument(
        "--tier",
        choices=["fast", "medium", "full"],
        default="full",
        help="Extraction depth: 'fast' (1 call storyboard), 'medium' (2 calls causal spec), 'full' (6-pass complete TwelveLabs intelligence dossier)",
    )
    p_ext.add_argument("--index-id", default=None, help="Optional TwelveLabs index_id")
    p_ext.add_argument(
        "--embed",
        action="store_true",
        help="Include raw Marengo 2.7 multimodal vector embeddings in --tier full output",
    )
    p_ext.add_argument("--out", type=Path, default=None, help="Output file path for extracted JSON dossier")
    p_ext.add_argument(
        "--print-prompt",
        action="store_true",
        help="Print the extraction prompt(s) for the selected --tier to paste into TwelveLabs Web Playground",
    )

    # 6. ask (Conversational Q&A with Pegasus about any video)
    p_ask = sub.add_parser("ask", help="Ask Pegasus 1.2 any custom conversational question about a video")
    p_ask.add_argument("video", help="Local video path OR existing TwelveLabs video_id")
    p_ask.add_argument("question", help="Custom question or instruction for Pegasus 1.2")
    p_ask.add_argument("--index-id", default=None, help="Optional TwelveLabs index_id")

    # 7. search (Marengo 2.7 semantic search across video library)
    p_search = sub.add_parser("search", help="Search across your TwelveLabs videos for specific visual/audio combat moments")
    p_search.add_argument("query", help="Natural language search query (e.g. 'spinning hook kick', 'sword disarm')")
    p_search.add_argument("--index-id", default=None, help="Optional index_id (searches all indexes if omitted)")
    p_search.add_argument("--video-id", default=None, help="Optional filter to search inside a single video_id")

    # 8. audit-render (Mode B Render QA)
    p_audit = sub.add_parser(
        "audit-render",
        help="Mode B: Audit a Seedance rendered video against a SAKUGA-MLLM-3.1-CAUSAL spec & extract t=10s handoff state",
    )
    p_audit.add_argument("spec", type=Path, help="Path to your SAKUGA-MLLM-3.1-CAUSAL clip JSON file")
    p_audit.add_argument("video", nargs="?", default=None, help="Local rendered video path (.mp4) OR TwelveLabs video_id")
    p_audit.add_argument("--index-id", default=None, help="Optional TwelveLabs index_id")
    p_audit.add_argument("--out", type=Path, default=None, help="Output file path for audit report")
    p_audit.add_argument("--print-prompt", action="store_true", help="Print the Mode B audit prompt")

    args = parser.parse_args()

    # Handle auth
    if args.cmd == "auth":
        if args.set_key:
            save_api_key(args.set_key)
            print(f"[TwelveLabs Auth] Saved API key to {CONFIG_FILE}")
        try:
            key = get_api_key()
            idxs = list_indexes(key)
            print(f"[TwelveLabs Auth] CONNECTED — API key is valid ({len(idxs)} index(es) found in account).")
            return 0
        except Exception as e:
            print(f"[TwelveLabs Auth] ERROR: {e}", file=sys.stderr)
            return 1

    # Handle --print-prompt before requiring API key
    if args.cmd in ("extract", "extract-ref") and args.print_prompt:
        if args.tier == "fast":
            print(FAST_PASS_PROMPT)
        elif args.tier == "medium":
            print(MEDIUM_PASS_PROMPT)
        else:
            print("=== FULL PASS PART A (BIOMECHANICS, CAUSAL GRAPH & LABAN) ===\n")
            print(FULL_PASS_PART_A_BIOMECHANICS_PROMPT)
            print("\n=== FULL PASS PART B (CINEMATOGRAPHY, SAKUGA X-SHEET, PROPS & AUDIO) ===\n")
            print(FULL_PASS_PART_B_CINEMATOGRAPHY_SAKUGA_AUDIO_PROMPT)
        return 0

    if args.cmd == "audit-render" and args.print_prompt:
        raw_spec = args.spec.read_text(encoding="utf-8").strip()
        spec_json = json.loads(raw_spec[raw_spec.find("{") :])
        print(build_mode_b_audit_prompt(spec_json))
        return 0

    # All remaining commands use the live TwelveLabs API
    api_key = get_api_key()

    if args.cmd == "account":
        idxs = list_indexes(api_key)
        summary = []
        for idx in idxs:
            idx_id = idx.get("_id")
            vids = list_videos_in_index(api_key, idx_id)
            summary.append(
                {
                    "index_id": idx_id,
                    "index_name": idx.get("index_name"),
                    "models": [m.get("model_name") for m in idx.get("models", [])],
                    "video_count": len(vids),
                }
            )
        print(json.dumps({"account_indexes": summary}, indent=2))
        return 0

    elif args.cmd == "videos":
        idxs = [{"_id": args.index_id, "index_name": "specified"}] if args.index_id else list_indexes(api_key)
        all_vids = []
        for idx in idxs:
            idx_id = idx["_id"]
            for v in list_videos_in_index(api_key, idx_id):
                sys_meta = v.get("system_metadata", {})
                all_vids.append(
                    {
                        "video_id": v.get("_id"),
                        "index_id": idx_id,
                        "index_name": idx.get("index_name"),
                        "filename": sys_meta.get("filename") or sys_meta.get("video_title"),
                        "duration_sec": sys_meta.get("duration"),
                        "fps": sys_meta.get("fps"),
                        "resolution": f"{sys_meta.get('width')}x{sys_meta.get('height')}",
                        "created_at": v.get("created_at"),
                    }
                )
        print(json.dumps({"videos": all_vids}, indent=2))
        return 0

    elif args.cmd == "upload":
        idx_id = args.index_id or get_or_create_dual_engine_index(api_key)
        vid_id = upload_video_to_index(api_key, idx_id, args.video_path)
        print(json.dumps({"status": "ready", "video_id": vid_id, "index_id": idx_id}, indent=2))
        return 0

    elif args.cmd in ("extract", "extract-ref"):
        if not args.video:
            print("[ERROR] Provide a video file path or TwelveLabs video_id (or use --print-prompt).", file=sys.stderr)
            return 1
        dossier = run_tiered_extraction(
            api_key=api_key,
            video_arg=args.video,
            tier=args.tier,
            explicit_index_id=args.index_id,
            include_embeddings=args.embed,
        )
        out_str = json.dumps(dossier, indent=2)
        if args.out:
            args.out.write_text(out_str + "\n", encoding="utf-8")
            print(f"[TwelveLabs {args.tier.upper()} PASS] Saved extraction dossier to {args.out}")
        else:
            print(out_str)
        return 0

    elif args.cmd == "ask":
        vid_id, _ = resolve_video_and_index(api_key, args.video, args.index_id)
        answer = analyze_video_with_pegasus(api_key, vid_id, args.question)
        if isinstance(answer, (dict, list)):
            print(json.dumps(answer, indent=2))
        else:
            print(answer)
        return 0

    elif args.cmd == "search":
        idxs = [{"_id": args.index_id, "index_name": "specified"}] if args.index_id else list_indexes(api_key)
        results = []
        for idx in idxs:
            try:
                hits = search_moments_in_index(api_key, idx["_id"], args.query, video_id_filter=args.video_id)
                for h in hits:
                    h["index_id"] = idx["_id"]
                    results.append(h)
            except Exception:
                continue
        print(json.dumps({"query": args.query, "matches": results}, indent=2))
        return 0

    elif args.cmd == "audit-render":
        if not args.video:
            print("[ERROR] Provide a rendered video path or TwelveLabs video_id.", file=sys.stderr)
            return 1
        raw_spec = args.spec.read_text(encoding="utf-8").strip()
        spec_json = json.loads(raw_spec[raw_spec.find("{") :])
        audit_prompt = build_mode_b_audit_prompt(spec_json)
        vid_id, _ = resolve_video_and_index(api_key, args.video, args.index_id)
        report = analyze_video_with_pegasus(api_key, vid_id, audit_prompt)
        out_str = json.dumps(report, indent=2) if isinstance(report, (dict, list)) else str(report)
        if args.out:
            args.out.write_text(out_str + "\n", encoding="utf-8")
            print(f"[TwelveLabs Mode B] Saved render QA & handoff report to {args.out}")
        else:
            print(out_str)
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
