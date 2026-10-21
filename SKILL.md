---
name: sakuga-fight-director
description: >-
  Use this skill whenever the user wants to design, write, lint, compile, or
  chain 2D Sakuga anime fight choreography video prompts (for Seedance 2.0 Mini,
  Seedance 2.5, Kling, Wan, or AI Video YouTube channel episodes) using the
  empirically verified SAKUGA-MLLM-3.1-CAUSAL schema and 2-Layer Unrolled Fluid Stack.
---

# Sakuga Fight Director & Compiler (`SAKUGA-MLLM-3.1-CAUSAL` & 2-Layer Fluid Stack)

This skill turns creative fight ideas or multi-clip YouTube episode concepts into empirically verified, non-regressing **`SAKUGA-MLLM-3.1-CAUSAL`** video prompts (in either **Single-Layer JSON** or **2-Layer Unrolled Fluid Stack `--stack`** format) and validates/compiles them using [sakuga_compiler.py](./scripts/sakuga_compiler.py).

## Directory Contents (STRICT TEMPLATE & VARIATION BOUNDARY RULE)
* **AGENT ONBOARDING & 25-DECISION INDEX (READ FIRST):** [AGENTS.md](./AGENTS.md)
* **ORIGINAL CANONICAL GOLDEN BASELINE TEMPLATES (`examples/`):**
  * **Verified Gold-Master #1 (Single-Layer JSON — Kunai vs. Blade Exchange):** [gold_master_1_blade_exchange.json](./examples/gold_master_1_blade_exchange.json)
  * **Verified Gold-Master #2 (Single-Layer JSON — Multi-Prop Disarm, Mid-Air Catch & Dual-Blade X-Lock):** [gold_master_2_disarm_dual_blade.json](./examples/gold_master_2_disarm_dual_blade.json)
  * **Verified Gold-Master #3 (2-Layer Fluid Stack — Courtyard Sky-Cartwheel, Rising Uppercut, Wall-Run & Kunai Dive):** [gold_master_3_courtyard_sky_cartwheel.json](./examples/gold_master_3_courtyard_sky_cartwheel.json) & [gold_master_3_courtyard_fluid_stack.txt](./examples/gold_master_3_courtyard_fluid_stack.txt)
  * **Verified Gold-Master #4 (2-Layer Fluid Stack Determinism Benchmark — Rain Shrine Bo-Staff vs. Iron Gauntlets):** [gold_master_4_shrine_bo_staff_determinism_test.json](./examples/gold_master_4_shrine_bo_staff_determinism_test.json) & [gold_master_4_shrine_bo_staff_fluid_stack.txt](./examples/gold_master_4_shrine_bo_staff_fluid_stack.txt)
* **COMBAT-STYLE & BIOMECHANICAL VARIATIONS (`examples/variations/` — Distinct from Golden #1–#4):**
  * **Variation #1 (`grounded_striker_boxer_baki` — 100% Grounded Baki / Kengan Stand-Up War):** [variation_1_baki_grounded_standup_war.json](./examples/variations/variation_1_baki_grounded_standup_war.json) & [variation_1_baki_grounded_standup_war_fluid_stack.txt](./examples/variations/variation_1_baki_grounded_standup_war_fluid_stack.txt)
  * **Variation #2 (`acrobatic_multidomain_freestyle` — 4-Domain Multi-Limb Martial Arts Showcase):** [variation_2_multidomain_combative_showcase.json](./examples/variations/variation_2_multidomain_combative_showcase.json) & [variation_2_multidomain_combative_showcase_fluid_stack.txt](./examples/variations/variation_2_multidomain_combative_showcase_fluid_stack.txt)
* **Architecture & Fighting-Style Documentation:**
  * [TWO_LAYER_FLUID_STACK_ARCHITECTURE.md](./docs/TWO_LAYER_FLUID_STACK_ARCHITECTURE.md)
  * [VARIATIONS_AND_FIGHTING_STYLES.md](./docs/VARIATIONS_AND_FIGHTING_STYLES.md)
* **Compiler & 25-Rule Physics/Diversity/Style Linter CLI:** [sakuga_compiler.py](./scripts/sakuga_compiler.py)
* **TwelveLabs Video-to-Sakuga Bridge (Mode A & Mode B):** [twelvelabs_bridge.py](./scripts/twelvelabs_bridge.py)
* **Full Master SOP:** [sakuga_prompt_schema_sop.md](./references/sakuga_prompt_schema_sop.md)
* ⚠️ **CRITICAL RULE FOR AGENTS:** NEVER copy schemas or prompt structures from `_archive_rd_history_do_not_copy/`. Those files contain deprecated early baselines (`LBN-2.3-ADV` Euler dicts, Quaternion A/B tests, `v3.2` metadata bloat tests) kept strictly for historical benchmarking. Always use `examples/gold_master_1..4*.json` (`SAKUGA-MLLM-3.1-CAUSAL`).

---

## 1. Non-Negotiable Core Rules (Tier 1 Structural Backbone — Drives 95%+ of Quality)

When authoring any clip JSON, you **MUST** obey all 10 laws discovered across 20 empirical decisions on Seedance 2.0 Mini and Seedance 2.5:

1. **Decoder-Only MLLM Causal Key Ordering:**
   Keys must be ordered strictly left-to-right so defender reactions (`B_track`), props, camera, and `rules` causally attend back to `A_beats` in the MLLM KV-cache:
   `name` $\rightarrow$ `schema` $\rightarrow$ `fps` $\rightarrow$ `duration` $\rightarrow$ `axes` $\rightarrow$ `screen_geometry` $\rightarrow$ `negative` $\rightarrow$ `conservation_laws` $\rightarrow$ `laban` $\rightarrow$ `beats` $\rightarrow$ `A_beats` $\rightarrow$ `B_track` $\rightarrow$ `<prop_tracks>` $\rightarrow$ `camera` $\rightarrow$ `anime` $\rightarrow$ `rules`.
2. **Strictly Kinematic & Causal `A_beats` (Zero Bloat):**
   Every beat in `A_beats` uses **only** these 11 keys in order:
   `t`, `beat`, `causal`, `pos`, `vel`, `axis`, `arc`, `support`, `contact` (optional on pure holds), `limbs`, `pose`.
   * **NEVER** include 10-bone Euler dicts, Quaternions (`q_root`, `q_rig`, `slerp`), or per-beat non-kinematic metadata keys (`style`, `fx_preset`, `camera_tempo`, `expression`).
3. **Zero Negation Leakage & Zero `<verb>` Markup Pollution (Decisions 03 & 19):**
   * **NEVER** write `"NOT a kick"`, `"NOT a punch"`, `"not a flip"`, or `"should not float"` inside `A_beats` or `B_track`. Distilled models activate the negated noun.
   * **NEVER** wrap motion verbs or events in `<punch>` or `<impact>` angle-bracket tags; they trigger the HTML/XML markup prior and weaken motion generation.
4. **4-Phase Sub-Beat Unrolling (`Entry/Windup -> Drive/Apex -> Contact -> Landing/Recovery` — Decision 18):**
   * Never collapse a complex rotation, cartwheel, aerial kick, wall-run, or dive into a single keyframe or jump directly from mid-air (`4.3s`) to a wall-run (`5.5s`) without an intermediate floor landing (`4.8s`).
   * Unroll every key move into **3–4 sequential sub-beats** (`0.3s–0.6s` apart) so the model interpolates short, unambiguous linear segments instead of guessing missing phases.
5. **Bilateral Two-Arm Silhouette Locking (Preventing One-Arm Occlusion — Decision 20):**
   * On every single beat in Layer 1 and Layer 2 (`limbs` and `pose`), **explicitly specify the spatial position of BOTH `L_arm` and `R_arm` (`or both_arms`) outside the torso silhouette**.
   * During single-handed punch/strike windups (e.g., `2.75s` left uppercut coil), never leave the non-striking arm vague (`"R_arm:high guard"`). Extend the non-striking arm clearly into view (e.g., `"R_arm extended forward toward B's chest with open right palm as a range-finding lead guard while L_arm is cocked low at left hip with clenched left fist so both left and right arms are 100% visible outside the torso silhouette"`), and include `"no missing arms, no one-armed fighter, both left and right arms and hands always visible"` in `"negative"`.
6. **2-Layer Unrolled Fluid Stack (`compile --stack` — Decision 19):**
   * For acrobatic, vertical, or multi-phase martial arts choreographies, compile with `--stack` to emit **Layer 1 (Continuous Support, 5-Phase Force-Event & Prop Timeline in Labanotation-as-Words)** directly above **Layer 2 (`SAKUGA-MLLM-3.1-CAUSAL` JSON)** from the same single source.
7. **Explicit Causal Dependency Graph (`C01 -> C16`):**
   * Every beat's `"causal"` string must link `requires: <precursor_torque_or_state>` $\rightarrow$ `causes: <next_state>`, with `timing: BEFORE_<THREAT>_INTERSECTION` on parries/dodges.
8. **3-Phase Contact Contract (`pre -> hit -> post`):**
   * Format `"contact"` as `"pre:<approach> -> hit:<Actor_Limb_strikes_Target_Part_at_[x,y,z]_zero_gap> -> post:<follow_through_and_impulse>"`.
9. **Close-Quarters Pocket + Midpoint Physical Screen-Cross (`t=4.8s–5.4s`):**
   * Keep combat within $\Delta z \le 1.6\text{m}$ (`fov 28–40` with explicit `"look"` anchors) and include at least one physical screen-side cross (`left -> right`).
10. **Parabolic Gravity on Airborne Props:**
    * Never describe an airborne weapon as `"hovering"`. Use a true upward apex (`y=2.1m–5.8m`) and a falling mid-air catch.

---

## 2. Compilation Modes, Taste Layer & Animation Style Presets

Use [sakuga_compiler.py](./scripts/sakuga_compiler.py) to lint and compile any choreography spec:
* **Compilation Modes:**
  * `compile <file.json>` (Default): Outputs **Single-Layer `SAKUGA-MLLM-3.1-CAUSAL` JSON** (used in Gold-Masters #1 & #2).
  * `compile <file.json> --stack`: Outputs the **2-Layer Unrolled Fluid Stack** (`Layer 1 Labanotation-as-Words Timeline` + `Layer 2 Causal JSON`, used in Gold-Masters #3 & #4).
* **Taste Presets (`--taste`):**
  * `--taste clean` (Default): Pure verified output.
  * `--taste nakamura`: Injects `hard_2_tone_cel` shadow rules, `chromatic_aberration: impact_frames_only`, and camera `preserve_axis: true` + `no_orbit`.
* **Animation Style Presets (`--style`):**
  * `cel_default`, `genga`, `sumi_ink`, `trigger_neon`, `retro_90s`, `ufotable`.

---

## 3. Step-by-Step Workflow for YouTube Episodes & Single Clips

```bash
# 1. Lint one or more JSON or Fluid Stack files against all 20 SOP Decisions:
python3 scripts/sakuga_compiler.py lint examples/gold_master_3_courtyard_sky_cartwheel.json examples/gold_master_4_shrine_bo_staff_determinism_test.json

# 2. Compile into a 2-Layer Unrolled Fluid Stack prompt (--stack):
python3 scripts/sakuga_compiler.py compile examples/gold_master_3_courtyard_sky_cartwheel.json --stack --out courtyard_stack.txt

# 3. Stitch & compile a multi-clip YouTube sequence in 2-Layer Fluid Stack format:
python3 scripts/sakuga_compiler.py stitch clip1.json clip2.json --stack --out episode_prompts.md
```

---

## 4. Conversational TwelveLabs Video Intelligence & 3-Tier Extraction (`twelvelabs_bridge.py`)

Use [twelvelabs_bridge.py](./scripts/twelvelabs_bridge.py) for Mode A reference extraction (`extract --tier fast|medium|full`), conversational video Q&A (`ask`), moment search (`search`), and Mode B render auditing (`audit-render`).
