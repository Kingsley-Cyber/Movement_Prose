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

## Directory Contents
* **Compiler & Linter CLI:** [sakuga_compiler.py](./scripts/sakuga_compiler.py)
* **TwelveLabs Video-to-Sakuga Bridge (Mode A & Mode B):** [twelvelabs_bridge.py](./scripts/twelvelabs_bridge.py)
* **Full 17-Decision Master SOP:** [sakuga_prompt_schema_sop.md](./references/sakuga_prompt_schema_sop.md)
* **Verified Gold-Master #1 (Single-Prop Kunai vs. Blade Exchange):** [gold_master_1_blade_exchange.json](./examples/gold_master_1_blade_exchange.json)
* **Verified Gold-Master #2 (Multi-Prop Disarm, Mid-Air Catch & Dual-Blade X-Lock):** [gold_master_2_disarm_dual_blade.json](./examples/gold_master_2_disarm_dual_blade.json)

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

## 4. TwelveLabs Video-to-Sakuga Bridge (`twelvelabs_bridge.py`)

When the user has a reference fight video (Mode A) or wants to audit a rendered clip / extract its true `t=10.0s` final frame for the next clip (Mode B), use [twelvelabs_bridge.py](./scripts/twelvelabs_bridge.py):

```bash
# MODE A (Primary): Extract timestamped C01->C10 choreography & kinematics from a reference fight video:
export TWELVELABS_API_KEY="tlk_..."
python3 scripts/twelvelabs_bridge.py extract-ref reference_fight.mp4 --out extracted_ref.json

# Or print the Mode A extraction prompt to paste directly into the TwelveLabs Web Playground (no API key needed):
python3 scripts/twelvelabs_bridge.py extract-ref --print-prompt

# MODE B: Audit a rendered Seedance video against a spec & extract the true t=10.0s state for Clip N+1:
python3 scripts/twelvelabs_bridge.py audit-render clip1.json rendered_clip1.mp4 --out audit_report.json
```
