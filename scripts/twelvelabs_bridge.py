#!/usr/bin/env python3
"""
TwelveLabs Video-to-Sakuga Bridge (Mode A: Reference Extractor & Mode B: Render QA Audit)
Works with zero external dependencies (uses Python built-in urllib to call TwelveLabs API v1.3,
or uses the `twelvelabs` Python SDK if installed).

Also supports `--print-prompt` so you can copy-paste the extraction prompt directly into the
TwelveLabs Web Playground without needing code!
"""

import argparse
import json
import mimetypes
import os
import sys
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

TWELVELABS_API_BASE = "https://api.twelvelabs.io/v1.3"

MODE_A_REFERENCE_EXTRACTION_PROMPT = """You are an expert 2D Sakuga martial arts fight choreographer and biomechanical motion analyst.
Analyze this fight video clip second-by-second (at 24fps precision) and extract a structured Causal Choreography Breakdown so it can be converted into a SAKUGA-MLLM-3.1-CAUSAL specification.

Output a valid JSON object (and nothing else) following this exact structure:
{
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


def build_mode_b_audit_prompt(spec_json: Dict[str, Any]) -> str:
    """Build a Mode B Render QA + Handoff extraction prompt comparing video vs SAKUGA-MLLM-3.1-CAUSAL spec."""
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
2. "beat_audit":For each timestamp `t` in the spec, report:
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
        with urllib.request.urlopen(req, timeout=120) as resp:
            body_text = resp.read().decode("utf-8")
            try:
                return json.loads(body_text)
            except json.JSONDecodeError:
                # Handle streaming NDJSON responses from /analyze or /generate
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


def get_or_create_index(api_key: str, index_name: str = "sakuga-fight-director-index") -> str:
    resp = api_request("GET", "/indexes?page=1&page_limit=20", api_key)
    for idx in resp.get("data", []):
        if idx.get("index_name") == index_name:
            return idx["_id"]

    print(f"[TwelveLabs] Creating index '{index_name}' with Pegasus 1.2...", file=sys.stderr)
    create_body = {
        "index_name": index_name,
        "models": [
            {
                "model_name": "pegasus1.2",
                "model_options": ["visual", "audio"],
            }
        ],
    }
    created = api_request("POST", "/indexes", api_key, json_body=create_body)
    return created["_id"]


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


def analyze_video_with_pegasus(api_key: str, video_id: str, prompt: str) -> str:
    print(f"[TwelveLabs] Analyzing video_id={video_id} with Pegasus 1.2...", file=sys.stderr)
    body = {
        "video_id": video_id,
        "prompt": prompt,
        "temperature": 0.1,
        "stream": False,
    }
    resp = api_request("POST", "/analyze", api_key, json_body=body)
    return resp.get("data", json.dumps(resp, indent=2))


def resolve_video_id(api_key: str, video_arg: str, index_id: Optional[str]) -> str:
    path = Path(video_arg)
    if path.exists() and path.is_file():
        idx_id = index_id or get_or_create_index(api_key)
        return upload_video_to_index(api_key, idx_id, path)
    # Otherwise treat video_arg directly as an already-indexed TwelveLabs video_id
    return video_arg


def main() -> int:
    parser = argparse.ArgumentParser(
        description="TwelveLabs Video-to-Sakuga Bridge (Mode A: Reference Choreography Extractor, Mode B: Render QA)"
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    # Mode A: extract-ref
    p_ref = sub.add_parser(
        "extract-ref",
        help="Mode A: Extract timestamped C01->C10 choreography & kinematics from a reference fight video",
    )
    p_ref.add_argument(
        "video",
        nargs="?",
        default=None,
        help="Local video path (.mp4/.mov) OR existing TwelveLabs video_id",
    )
    p_ref.add_argument("--index-id", default=None, help="Optional TwelveLabs index_id")
    p_ref.add_argument("--out", type=Path, default=None, help="Output file path for extracted JSON")
    p_ref.add_argument(
        "--print-prompt",
        action="store_true",
        help="Print the exact Mode A prompt to paste into the TwelveLabs Web Playground (no API key needed)",
    )

    # Mode B: audit-render
    p_audit = sub.add_parser(
        "audit-render",
        help="Mode B: Audit a Seedance rendered video against a SAKUGA-MLLM-3.1-CAUSAL spec & extract t=10s handoff state",
    )
    p_audit.add_argument("spec", type=Path, help="Path to your SAKUGA-MLLM-3.1-CAUSAL clip JSON file")
    p_audit.add_argument(
        "video",
        nargs="?",
        default=None,
        help="Local rendered video path (.mp4) OR existing TwelveLabs video_id",
    )
    p_audit.add_argument("--index-id", default=None, help="Optional TwelveLabs index_id")
    p_audit.add_argument("--out", type=Path, default=None, help="Output file path for audit report")
    p_audit.add_argument(
        "--print-prompt",
        action="store_true",
        help="Print the exact Mode B audit prompt to paste into the TwelveLabs Web Playground",
    )

    args = parser.parse_args()

    if args.cmd == "extract-ref":
        if args.print_prompt:
            print(MODE_A_REFERENCE_EXTRACTION_PROMPT)
            return 0

        if not args.video:
            print("[ERROR] Please provide a video file path or TwelveLabs video_id (or use --print-prompt).", file=sys.stderr)
            return 1

        api_key = os.environ.get("TWELVELABS_API_KEY", "").strip()
        if not api_key:
            print(
                "[ERROR] TWELVELABS_API_KEY environment variable is not set.\n"
                "Run: export TWELVELABS_API_KEY='tlk_your_key_here'\n"
                "Or use `--print-prompt` to copy the prompt for the TwelveLabs Web Playground.",
                file=sys.stderr,
            )
            return 1

        vid_id = resolve_video_id(api_key, args.video, args.index_id)
        result_text = analyze_video_with_pegasus(api_key, vid_id, MODE_A_REFERENCE_EXTRACTION_PROMPT)
        if args.out:
            args.out.write_text(result_text + "\n", encoding="utf-8")
            print(f"[TwelveLabs Mode A] Saved extracted choreography skeleton to {args.out}")
        else:
            print(result_text)
        return 0

    elif args.cmd == "audit-render":
        raw_spec = args.spec.read_text(encoding="utf-8").strip()
        brace_idx = raw_spec.find("{")
        spec_json = json.loads(raw_spec[brace_idx:])
        audit_prompt = build_mode_b_audit_prompt(spec_json)

        if args.print_prompt:
            print(audit_prompt)
            return 0

        if not args.video:
            print("[ERROR] Please provide a rendered video path or TwelveLabs video_id (or use --print-prompt).", file=sys.stderr)
            return 1

        api_key = os.environ.get("TWELVELABS_API_KEY", "").strip()
        if not api_key:
            print(
                "[ERROR] TWELVELABS_API_KEY environment variable is not set.\n"
                "Run: export TWELVELABS_API_KEY='tlk_your_key_here'\n"
                "Or use `--print-prompt` to copy the audit prompt for the TwelveLabs Web Playground.",
                file=sys.stderr,
            )
            return 1

        vid_id = resolve_video_id(api_key, args.video, args.index_id)
        result_text = analyze_video_with_pegasus(api_key, vid_id, audit_prompt)
        if args.out:
            args.out.write_text(result_text + "\n", encoding="utf-8")
            print(f"[TwelveLabs Mode B] Saved render QA & handoff report to {args.out}")
        else:
            print(result_text)
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
