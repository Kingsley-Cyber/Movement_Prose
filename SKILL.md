---
name: sakuga-fight-director
description: >-
  Use this skill whenever the user wants to design, write, lint, compile, or
  chain 2D Sakuga anime fight choreography video prompts (for Seedance 2.0 Mini,
  Seedance 2.5, Kling, Wan, or AI Video YouTube channel episodes) using the
  empirically verified SAKUGA-MLLM-3.1-CAUSAL schema.
---

# Sakuga Fight Director & Compiler (`SAKUGA-MLLM-3.1-CAUSAL`)

This skill turns creative fight ideas or multi-clip YouTube episode concepts into empirically verified, non-regressing **`SAKUGA-MLLM-3.1-CAUSAL`** video prompts and validates/compiles them using [sakuga_compiler.py](./scripts/sakuga_compiler.py).

## Directory Contents (STRICT TEMPLATE RULE)
* **CANONICAL TEMPLATES (USE ONLY THESE):**
  * **Verified Gold-Master #1 (Single-Prop Kunai vs. Blade Exchange):** [gold_master_1_blade_exchange.json](./examples/gold_master_1_blade_exchange.json)
  * **Verified Gold-Master #2 (Multi-Prop Disarm, Mid-Air Catch & Dual-Blade X-Lock):** [gold_master_2_disarm_dual_blade.json](./examples/gold_master_2_disarm_dual_blade.json)
* **Compiler & Linter CLI:** [sakuga_compiler.py](./scripts/sakuga_compiler.py)
* **TwelveLabs Video-to-Sakuga Bridge (Mode A & Mode B):** [twelvelabs_bridge.py](./scripts/twelvelabs_bridge.py)
* **Full 17-Decision Master SOP:** [sakuga_prompt_schema_sop.md](./references/sakuga_prompt_schema_sop.md)
* ⚠️ **CRITICAL RULE FOR AGENTS:** NEVER copy schemas or prompt structures from `_archive_rd_history_do_not_copy/`. Those files contain deprecated early baselines (`LBN-2.3-ADV` Euler dicts, Quaternion A/B tests, `v3.2` metadata bloat tests) kept strictly for historical benchmarking. Always use `examples/gold_master_1_blade_exchange.json` or `examples/gold_master_2_disarm_dual_blade.json` (`SAKUGA-MLLM-3.1-CAUSAL`).

---

## 1. Non-Negotiable Core Rules (Tier 1 Structural Backbone — Drives 95% of Quality)

When authoring any clip JSON, you **MUST** obey all 7 laws discovered through A/B testing on Seedance 2.0 Mini and Seedance 2.5:

1. **Decoder-Only MLLM Causal Key Ordering:**
   Keys must be ordered strictly left-to-right so defender reactions (`B_track`), props, camera, and `rules` causally attend back to `A_beats` in the MLLM KV-cache:
   `name` $\rightarrow$ `schema` $\rightarrow$ `fps` $\rightarrow$ `duration` $\rightarrow$ `axes` $\rightarrow$ `screen_geometry` $\rightarrow$ `negative` $\rightarrow$ `conservation_laws` $\rightarrow$ `laban` $\rightarrow$ `beats` $\rightarrow$ `A_beats` $\rightarrow$ `B_track` $\rightarrow$ `<prop_tracks>` $\rightarrow$ `camera` $\rightarrow$ `anime` $\rightarrow$ `rules`.
2. **Strictly Kinematic & Causal `A_beats` (Zero Bloat):**
   Every beat in `A_beats` uses **only** these 11 keys in order:
   `t`, `beat`, `causal`, `pos`, `vel`, `axis`, `arc`, `support`, `contact` (optional on pure holds), `limbs`, `pose`.
   * **NEVER** include 10-bone Euler dicts, Quaternions (`q_root`, `q_rig`, `slerp`), or per-beat non-kinematic metadata keys (`style`, `fx_preset`, `camera_tempo`, `expression`). They dilute kinematic attention and cause air-hitting and motion lag.
3. **Zero Negation Leakage Inside Beats:**
   * **NEVER** write `"NOT a kick"`, `"NOT a punch"`, or `"not thrown"` inside `A_beats` or `B_track`. Distilled models activate the negated noun.
   * Always immobilize non-active limbs **positively** in `"support"` (e.g., `"both_boots_planted_flat_on_floor"`, `"left_boot_planted_pivot_on_floor"`).
4. **Explicit Causal Dependency Graph (`C01 -> C10`):**
   * Every beat's `"causal"` string must link `requires: <precursor_torque_or_state>` $\rightarrow$ `causes: <next_state>`.
   * On any parry, dodge, weave, or substitution beat, include `timing: BEFORE_<THREAT>_INTERSECTION` so evasions initiate *after* attack commitment and *before* weapon intersection.
   * Chain elastic kung-fu recoil into uncoil (e.g., `C04_arched_spine_tension` $\rightarrow$ `requires: C04_arched_spine_whiplash_uncoil`).
5. **3-Phase Contact Contract (`pre -> hit -> post`):**
   * Every strike, parry, vault, or grab must format `"contact"` as:
     `"pre:<approach_commitment> -> hit:<Actor_Limb_deforms_Target_Part_at_[x,y,z]_zero_gap> -> post:<attacker_follow_through_and_target_impulse>"`.
   * On pure dodges/weaves, format `"contact"` as `"evasion_corridor: <exact clearance in cm/m below or beside weapon sweep>"`.
6. **Close-Quarters Pocket + Midpoint Physical Screen-Cross (`t=4.8s–5.4s`):**
   * Keep fighters within $\Delta z \le 1.5\text{m}$ (`fov 28–38` tight combat lenses with explicit `"look"` target anchors on every camera cut).
   * Always include **one dynamic physical cross (`screen_left -> screen_right`)** around `t=4.8s–5.4s` (via a shoulder vault, ducking step-through, or spinning flank pass) so the fight has sweeping 3D momentum instead of a static standoff.
7. **Parabolic Gravity on Airborne Props:**
   * Never describe an airborne or disarmed weapon as `"hovering"`. Launch it to a true upward apex (`y=2.0m–2.2m`) and catch it on the move as it falls through `y=1.35m–1.45m`.

---

## 2. Optional Tier 2 "Taste / Seasoning Layer" & Animation Style Presets (Via Compiler Flags)

Keep the base choreography JSON clean and apply stylistic seasoning or animation medium swaps via [sakuga_compiler.py](./scripts/sakuga_compiler.py):
* **Taste Presets (`--taste`):**
  * `--taste clean` (Default): Pure `SAKUGA-MLLM-3.1-CAUSAL` Gold-Master output.
  * `--taste nakamura`: Injects `hard_2_tone_cel` shadow rules, `chromatic_aberration: impact_frames_only`, and camera `preserve_axis: true` + `no_orbit`.
* **Animation Style Presets (`--style` — R&D Queue in [sakuga_prompt_schema_sop.md](./references/sakuga_prompt_schema_sop.md) Section 5):**
  * `--style cel_default` (Default): Standard 2D cel-shaded anime.
  * `--style genga`: Raw pencil key-animation sketch on cream paper with red/blue layout lines (`[TO BE TESTED]`).
  * `--style sumi_ink`: Traditional Japanese sumi-e calligraphy brush ink wash (`[TO BE TESTED]`).
  * `--style trigger_neon`: Studio Trigger hyper-pop angular shadows & neon rim light (`[TO BE TESTED]`).
  * `--style retro_90s`: 1990s hand-painted acetate cel with 35mm film grain & halation (`[TO BE TESTED]`).
  * `--style ufotable`: Dark-fantasy 2D cel with hand-drawn ukiyo-e elemental trails on weapon arcs (`[TO BE TESTED]`).

---

## 3. Step-by-Step Workflow for YouTube Episodes & Single Clips

### Step 1: Design the Choreography Spec
* For a **single 10s clip**, start from [gold_master_1_blade_exchange.json](./examples/gold_master_1_blade_exchange.json) or [gold_master_2_disarm_dual_blade.json](./examples/gold_master_2_disarm_dual_blade.json) and write the scene spec JSON.
* For a **multi-clip YouTube episode (e.g. 30s = 3 clips)**, design a JSON array of clips or separate clip files (`clip1.json`, `clip2.json`, `clip3.json`).

### Step 2: Run the Compiler & Pre-Flight Linter
Always run [sakuga_compiler.py](./scripts/sakuga_compiler.py) to validate all 17 SOP rules, check contact distances, stitch multi-clip continuity (`Clip N [t=10.0s]` $\rightarrow$ `Clip N+1 [t=0.0s]`), and generate the copy-pasteable prompt block:

```bash
# Validate and compile a single clip into a ready-to-paste Seedance prompt:
python3 scripts/sakuga_compiler.py compile path/to/clip.json --taste clean

# Validate and compile with Nakamura taste layer (hard 2-tone cel, impact chromatic aberration, camera overshoot):
python3 scripts/sakuga_compiler.py compile path/to/clip.json --taste nakamura

# Stitch & compile a multi-clip YouTube sequence (auto-locks Clip N+1 t=0.0s to Clip N t=10.0s):
python3 scripts/sakuga_compiler.py stitch clip1.json clip2.json clip3.json --out episode_prompts.md
```

### Step 3: Verify Zero Linter Warnings
If `sakuga_compiler.py` reports any `[ERROR]` or `[WARN]` (such as negation leakage, missing `pre -> hit -> post` phases, contact distance $> 0.45\text{m}$, or camera `fov > 40`), fix the JSON and re-run until the compiler reports `PASSED (0 errors, 0 warnings)`.

---

## 4. Conversational TwelveLabs Video Intelligence & 3-Tier Extraction (`twelvelabs_bridge.py`)

This skill gives you **full conversational control** over the user's TwelveLabs API account via [twelvelabs_bridge.py](./scripts/twelvelabs_bridge.py). Whenever the user asks about their TwelveLabs account, indexes, uploaded videos, or asks to extract/analyze/search a fight video, run the appropriate command automatically and converse naturally with the results.

### A. Account, Library, Upload & Conversational Q&A Commands
```bash
# 1. Save API key once (persists to ~/.config/sakuga/twelvelabs.json) or check auth status:
python3 scripts/twelvelabs_bridge.py auth --set-key "tlk_..."
python3 scripts/twelvelabs_bridge.py auth --status

# 2. Inspect TwelveLabs account indexes & enabled engines (pegasus1.2, marengo2.7):
python3 scripts/twelvelabs_bridge.py account

# 3. List all videos in the user's TwelveLabs library (supports partial name or video_id matching):
python3 scripts/twelvelabs_bridge.py videos

# 4. Upload & index a new local video (auto-creates a dual Pegasus 1.2 + Marengo 2.7 index if needed):
python3 scripts/twelvelabs_bridge.py upload path/to/video.mp4

# 5. Ask ANY conversational follow-up question to Pegasus 1.2 about an indexed/local video:
python3 scripts/twelvelabs_bridge.py ask <video_id_or_name_or_path> "At what exact timestamp does the blade disarm happen, and which foot is planted?"

# 6. Search across the entire TwelveLabs index for specific visual/audio combat moments (Marengo 2.7):
python3 scripts/twelvelabs_bridge.py search "mid-air blade catch" "high-velocity shoulder vault"
```

### B. 3-Tier Extraction Engine (`extract --tier fast | medium | full`)
Choose the extraction depth based on what the user needs (accepts a local `.mp4`, an existing TwelveLabs `video_id`, or a partial filename already in their TwelveLabs account):

| Tier | Command | API Calls | What It Extracts & When to Use |
| :--- | :--- | :--- | :--- |
| **`fast`** | `extract <target> --tier fast` | **1 call** (`/analyze`) | **Rapid Storyboard Pass (~10s):** High-level premise, fighter silhouettes, midpoint screen-cross timestamp, and macro `C01->C10` beat list. Best for quick brainstorming. |
| **`medium`** | `extract <target> --tier medium` | **2 calls** (`/gist` + `/analyze`) | **Standard Choreographer Pass (~25s):** Video Gist + single-pass `SAKUGA-MLLM-3.1-CAUSAL` JSON draft (`A_beats`, `B_track`, props, camera, anime). Best for standard Mode A prompt creation. |
| **`full`** | `extract <target> --tier full` | **6 passes** (All TwelveLabs endpoints) | **100% Complete Video Intelligence Dossier (~60s):** Extracts **everything TwelveLabs supports** about the video and merges it into a unified dossier + compiled `SAKUGA-MLLM-3.1-CAUSAL` JSON:<br>1. **System Metadata (`/videos/{id}`):** Exact FPS, resolution, duration, audio tracks (+ optional `--embed` Marengo 2.7 vector embeddings)<br>2. **Gist (`/gist`):** Auto-generated Title, Topics & Hashtags<br>3. **Summaries (`/summarize` x3):** Full Summary, Timestamped Chapters & Key Highlights<br>4. **Pegasus Deep Pass A (`/analyze`):** Full Biomechanics, `C01->C12` Causal Graph, 8-Effort Laban Table, 6D `axis`, `support`, and 3-phase `pre->hit->post` contacts<br>5. **Pegasus Deep Pass B (`/analyze`):** Cinematography/FOV/cuts, Sakuga Smear Exposure Sheet (`on_1s`/`on_2s`), Parabolic Prop State Machines, Destructible Environment & Cross-Modal Audio Impulse Track<br>6. **Marengo 2.7 Temporal Grounding (`/search`):** Sub-second visual + audio confidence timestamps for impacts/clashes, evasions/vaults, spins/sweeps, and finishers |

```bash
# Run a Full Pass (100% TwelveLabs extraction) on an indexed video or local file:
python3 scripts/twelvelabs_bridge.py extract reference_fight.mp4 --tier full --out full_dossier.json

# Include raw Marengo 2.7 1024-D visual/audio vector embeddings in the Full Pass:
python3 scripts/twelvelabs_bridge.py extract reference_fight.mp4 --tier full --embed --out full_dossier_with_vectors.json

# Print the raw prompts for any tier (fast, medium, full) to use in the TwelveLabs Web Playground without an API key:
python3 scripts/twelvelabs_bridge.py extract --tier full --print-prompt
```

### C. Mode B Render QA & `t=10.0s` Handoff State Extractor (`audit-render`)
```bash
# Audit a rendered Seedance clip against your JSON spec & extract the true t=10.0s state for Clip N+1:
python3 scripts/twelvelabs_bridge.py audit-render clip1.json rendered_clip1.mp4 --out audit_report.json
```
