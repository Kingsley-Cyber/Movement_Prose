# AGENTS.md — Deterministic Onboarding & Standard Operating Procedure

Welcome to **Movement_Prose** (`SAKUGA-MLLM-3.1-CAUSAL` & 2-Layer Unrolled Fluid Stack).
Read this file **first** before reading, editing, linting, or generating any prompt in this repository.

---

## 1. Repository Map & Strict Directory Boundaries

```text
Movement_Prose/
├── AGENTS.md                                                  # 👈 START HERE: Deterministic agent onboarding & 25-Decision index
├── README.md                                                  # Project overview & CLI quick-start
├── SKILL.md                                                   # Antigravity / Claude Skill instructions (mirrored to ~/.gemini/config/skills/sakuga-fight-director)
├── docs/
│   ├── FIGHT_MOVE_SYSTEM_PLAN.md                              # 🚀 v2 Master Architecture & Execution Plan (Move Lexicon, State Machine, Dyad Coupling, Wording Compiler)
│   ├── TWO_LAYER_FLUID_STACK_ARCHITECTURE.md                  # Deep-dive: Mode 1 (Single-Layer JSON) vs Mode 2 (--stack 2-Layer Fluid Stack)
│   └── VARIATIONS_AND_FIGHTING_STYLES.md                      # Deep-dive: Decisions 21-25, Entity Fighting Styles & Variations vs Golden Baseline
├── scripts/
│   ├── sakuga_compiler.py                                     # Deterministic CLI Compiler, 25-Rule Physics/Diversity/Style Linter & Stitcher
│   └── twelvelabs_bridge.py                                   # TwelveLabs Pegasus 1.2 Bridge (Mode A: Reference Extractor, Mode B: Render QA)
├── examples/                                                  # ✅ ORIGINAL CANONICAL GOLDEN BASELINE PROMPTS (DO NOT OVERWRITE)
│   ├── gold_master_1_blade_exchange.json                      # Golden #1 (Mode 1 Single-Layer JSON): Kunai vs. Blade Exchange
│   ├── gold_master_2_disarm_dual_blade.json                   # Golden #2 (Mode 1 Single-Layer JSON): Wakizashi Disarm, Aerial Catch & X-Lock
│   ├── gold_master_3_courtyard_sky_cartwheel.json             # Golden #3 (Mode 2 --stack): Courtyard Sky-Cartwheel, Uppercut, Wall-Run & Dive
│   ├── gold_master_3_courtyard_fluid_stack.txt                # Golden #3 Compiled 2-Layer Fluid Stack Output
│   ├── gold_master_4_shrine_bo_staff_determinism_test.json    # Golden #4 (Mode 2 --stack): Rain Shrine Bo-Staff vs. Iron Gauntlets
│   ├── gold_master_4_shrine_bo_staff_fluid_stack.txt          # Golden #4 Compiled 2-Layer Fluid Stack Output
│   └── variations/                                            # 🔥 COMBAT-STYLE & BIOMECHANICAL VARIATIONS (Distinct from Golden #1-#4)
│       ├── variation_1_baki_grounded_standup_war.json         # Variation #1 (style: grounded_striker_boxer_baki): 100% Grounded Baki Stand-Up War
│       ├── variation_1_baki_grounded_standup_war_fluid_stack.txt
│       ├── variation_2_multidomain_combative_showcase.json    # Variation #2 (style: acrobatic_multidomain_freestyle): 4-Domain Acrobatic Showcase
│       ├── variation_2_multidomain_combative_showcase_fluid_stack.txt
│       ├── variation_3_eight_limbs_muay_thai_mma_war.json     # Variation #3 (style: ufc_mma_octagon): Compiled via Fight Move System v2 (6 Weapons, Rooftop Helipad Cage War)
│       └── variation_3_eight_limbs_muay_thai_mma_war_fluid_stack.txt
├── references/
│   └── sakuga_prompt_schema_sop.md                            # Complete Master SOP (Decisions 01-25)
└── _archive_rd_history_do_not_copy/                           # ⛔ DEPRECATED R&D ARCHIVE (Euler/Quaternion/Bloat tests — NEVER COPY FROM HERE)
```

### Critical Boundary Rules for Agents:
1. **NEVER copy from `_archive_rd_history_do_not_copy/`**: Those files contain deprecated early experiments (`Euler dicts`, `Quaternions`, `v3.2 metadata bloat`) kept strictly for historical A/B logs.
2. **Keep `examples/gold_master_1..4` Distinct from `examples/variations/`**:
   - `examples/gold_master_1..4` are the **Original Canonical Golden Prompts** (ninja blade/kunai exchanges, courtyard sky-cartwheel/wall-run, and shrine bo-staff).
   - `examples/variations/` holds **Combat-Style & Biomechanical Variations** (such as `variation_1_baki_grounded_standup_war` and `variation_2_multidomain_combative_showcase`). All new fighting-style variations belong in `examples/variations/`.

---

## 2. Where to Go Based on Your Task

| If the User Wants To... | Read This File First | Template / Tool to Use |
| :--- | :--- | :--- |
| Implement or extend the **v2 Fight Move System** (closed Move Card lexicon, Fighter/Dyad state machines, `V01–V17` validator, no-numbers/no-forbidden-names Wording Compiler, `H1–H7` render packets) | [`docs/FIGHT_MOVE_SYSTEM_PLAN.md`](docs/FIGHT_MOVE_SYSTEM_PLAN.md) | Follow Milestones `M1` $\to$ `M6` in [`docs/FIGHT_MOVE_SYSTEM_PLAN.md`](docs/FIGHT_MOVE_SYSTEM_PLAN.md) |
| Generate a **grounded bare-knuckle / Baki / Kengan / UFC / boxing / kickboxing** fight (ZERO wall-runs, ZERO ground punches, ZERO aerial flip bleed) | [`docs/VARIATIONS_AND_FIGHTING_STYLES.md`](docs/VARIATIONS_AND_FIGHTING_STYLES.md) | [`examples/variations/variation_1_baki_grounded_standup_war.json`](examples/variations/variation_1_baki_grounded_standup_war.json) (`fighting_style: "grounded_striker_boxer_baki"` or `"ufc_mma_octagon"`) |
| Generate an **acrobatic multi-domain martial arts showcase** (floor sweeps, ground up-kicks, kip-ups, jumping knees, aerial axe kicks) | [`docs/VARIATIONS_AND_FIGHTING_STYLES.md`](docs/VARIATIONS_AND_FIGHTING_STYLES.md) | [`examples/variations/variation_2_multidomain_combative_showcase.json`](examples/variations/variation_2_multidomain_combative_showcase.json) (`fighting_style: "acrobatic_multidomain_freestyle"`) |
| Generate a **weapon / ninja / blade / bo-staff / acrobatic wall-dive** fight | [`docs/TWO_LAYER_FLUID_STACK_ARCHITECTURE.md`](docs/TWO_LAYER_FLUID_STACK_ARCHITECTURE.md) | [`examples/gold_master_2_disarm_dual_blade.json`](examples/gold_master_2_disarm_dual_blade.json), [`examples/gold_master_3_courtyard_sky_cartwheel.json`](examples/gold_master_3_courtyard_sky_cartwheel.json), or [`examples/gold_master_4_shrine_bo_staff_determinism_test.json`](examples/gold_master_4_shrine_bo_staff_determinism_test.json) |
| Understand **why a render had anatomical issues** (1 arm, merged torsos, deformed legs on knees, aerial sweeps bleeding into punch combos, static camera) | [`docs/VARIATIONS_AND_FIGHTING_STYLES.md`](docs/VARIATIONS_AND_FIGHTING_STYLES.md) & [`docs/TWO_LAYER_FLUID_STACK_ARCHITECTURE.md`](docs/TWO_LAYER_FLUID_STACK_ARCHITECTURE.md) | Run `python3 scripts/sakuga_compiler.py lint <file.json>` |

---

## 3. Master Index of All 25 Empirical Decisions (`Decisions 01–25`)

Every rule below is enforced or audited by [`scripts/sakuga_compiler.py`](scripts/sakuga_compiler.py):

### Tier 1: Core Schema & Causal Physics (`Decisions 01–17` — [`references/sakuga_prompt_schema_sop.md`](references/sakuga_prompt_schema_sop.md))
- **Decision 01 (No 10-Bone Euler Dicts):** Never put per-joint Euler angle dictionaries inside beats; use `pos`, `vel`, `axis`, `arc`, `support`, `limbs`, `pose`.
- **Decision 02 (Anti-HUD / Anti-Text Header & Negative):** Always include `"no on-screen text or numbers, no HUD, no coordinate labels"`.
- **Decision 03 (Positive-Only Support Locks — Zero Negation Leakage):** Never write `"NOT a kick"` or `"NOT a flip"` inside `A_beats` or `B_track`.
- **Decision 04 (No Per-Beat Style/FX Metadata Bloat):** Keep `A_beats` strictly to the 11 kinematic/causal keys; put all smears/FX in `"anime"`.
- **Decision 05 (6D Orientation Basis `axis` + Clock-Face `arc`):** Express orientation via `"axis"` and trajectories via clock-face vectors (`"8_to_2_clock"`).
- **Decision 06 (3-Phase Contact Contract):** Every impact uses `"pre:... -> hit:... -> post:..."`.
- **Decision 07 (Limb-Isolated Smear Frames):** Smear ONLY the active striking limb while explicitly stating `"head, torso, and non-striking limbs stay solid"`.
- **Decision 08 (No Quaternions / Slerp):** Never use `q_root`, `q_rig`, or `slerp`.
- **Decision 09 (Decoder-Only MLLM Causal Key Order):** Top-level keys must follow `name -> schema -> fps -> duration -> axes -> screen_geometry -> negative -> conservation_laws -> laban -> beats -> A_beats -> B_track -> <props> -> camera -> anime -> rules`.
- **Decision 10 (Close-Quarters Pocket & Camera FOV 28–40):** Keep fighters within realistic strike reach and camera `fov` between `28` and `40`.
- **Decision 11 (Zero-Early-Flinch Defender Causality):** `B_track` reactions happen ONLY at or after the exact contact timestamp.
- **Decision 12 (Mandatory Camera `look` Anchors):** Every camera shot must specify an explicit `"look"` target.
- **Decision 13 (Clean Impact Holds):** State `(hold 3f)` / `(hold 4f)` / `(hold 5f)` once per impact line (never duplicate hold tags on the same line).
- **Decision 14 (`SAKUGA-MLLM-3.1-CAUSAL` Explicit Causal Graph):** Every beat in `A_beats` starts `"causal"` with `"C01: requires: ... -> preserves: ... -> causes: ..."`.
- **Decision 15 (Explicit Prop State Machine):** Every weapon/prop has its own top-level track with continuous ownership and state.
- **Decision 16 (Parabolic Prop Gravity):** Airborne weapons follow a parabolic arc (`apex -> falling catch`), never `"hovering"`.
- **Decision 17 (Tier 2 Taste Layer `--taste nakamura`):** Optional Yutaka Nakamura seasoning (`hard 2-tone cel`, `chromatic_aberration: impact_frames_only`).

### Tier 2: 2-Layer Fluid Stack & Anatomical Integrity (`Decisions 18–21` — [`docs/TWO_LAYER_FLUID_STACK_ARCHITECTURE.md`](docs/TWO_LAYER_FLUID_STACK_ARCHITECTURE.md))
- **Decision 18 (4-Phase Sub-Beat Unrolling):** Unroll every strike/maneuver into `Entry/Windup -> Drive/Turnover -> Contact -> Landing/Recovery` (`0.3s–0.6s` per sub-beat).
- **Decision 19 (Single-Source 2-Layer Fluid Stack `--stack` & Zero `<verb>` Markup):** Compile Layer 1 (`Labanotation-as-Words`) and Layer 2 (`Causal JSON`) from the same JSON source; never wrap verbs in `<punch>` XML/HTML tags.
- **Decision 20 (Bilateral Two-Arm Silhouette Lock — The `:03` One-Arm Fix):** Explicitly place BOTH `L_arm` and `R_arm` (`"both arms separate from the torso in silhouette"`) on every single beat.
- **Decision 21 (Standing-Pillar Leg Separation, Bent-Knee Smear Ban & Full-Body Side Profile — The `:04–:05` Knee Fix):** Anchor one leg straight down (`6 o'clock` pillar) or extend it straight back (`5 o'clock` scissor) during knee strikes; never smear bent knees; frame knees in head-to-toe `medium_wide_side_profile` (`fov 38`), never `worm_eye`.

### Tier 3: Combat-Style Variations, Cinematography & Anti-Bleed Gating (`Decisions 22–25` — [`docs/VARIATIONS_AND_FIGHTING_STYLES.md`](docs/VARIATIONS_AND_FIGHTING_STYLES.md))
- **Decision 22 (Realistic Strike-Reach Spacing, 10s Screen-Side Lock & Biomechanical Poses over Franchise Names):** Stage punches at **one full arm's length (`0.75–0.85m`)**, elbows/clinches at **half an arm's length (`0.60–0.65m`)**, and kicks at **one full leg's length (`1.05–1.15m`)**. Lock `A` on `screen_left` and `B` on `screen_right` for all 10s (zero side swaps), lock outfit/tape identity (`no wrist tape on B`), and describe physical poses instead of franchise move names.
- **Decision 23 (Elite 180-Degree Hemisphere Sakuga Cinematography & Multi-Axis Rotations):** Within the $+X$ front hemisphere, vary camera angles (`3/4 low ankle track`, `crane plunge`, `3/4 whip-pan`, `vertical pedestal drop`, `fov 40 -> 28 snap-zoom`, `Dutch roll -12° to +12°`), drive $90^\circ–360^\circ$ torso rotations, and enforce opposite head-snap directions for opposite-side strikes.
- **Decision 24 (6-Weapon Anatomical Diversity & "Recoil-is-Windup" Chaining):** Cycle across distinct body weapons (`shin/calf`, `ankle/heel`, `knee`, `elbow/forearm`, `fist/backfist`, `palm/collar-tie`) and elevations so the recoil of Move $N$ physically loads Move $N+1$.
- **Decision 25 (Entity `fighting_style` Archetype Gating & Anti-Bleed Isolation):** Declare `laban.<entity>.fighting_style` (`grounded_striker_boxer_baki`, `ufc_mma_octagon`, `muay_thai_nak_muay`, `acrobatic_multidomain_freestyle`, `shinobi_weapon_acrobat`, `heavy_weapon_master`) so grounded boxing/kickboxing combos are never contaminated by temporal self-attention bleed from aerial leg sweeps or flips.

---

## 4. Standard CLI Verification Workflow

Always run the linter and compiler before committing or returning any prompt:

```bash
# 1. Lint Canonical Golden Prompts #1 & #2 with the locked 05:34 (e91c686) compiler:
python3 scripts/sakuga_compiler.py lint examples/gold_master_1_blade_exchange.json examples/gold_master_2_disarm_dual_blade.json

# 2. Lint 25-Decision Scene Graphs (Golden #3, #4 & Variations) with the Fluid Stack Scene Graph Linter:
python3 -m fight_move_system.scene_graph_linter lint examples/*.json examples/variations/*.json

# 3. Validate, Compile, Query KB, and Run Closed-Loop Repair via Fight Move System v2 CLI:
python3 -m fight_move_system.cli kb-sync
python3 -m fight_move_system.cli compile fight_move_system/fixtures/pass/variation_3_eight_limbs_muay_thai_mma_war_sheet.json \
  --mode xperiment --schema sakuga_Xperiment \
  -o examples/variations/variation_3_eight_limbs_muay_thai_mma_war_sakuga_Xperiment.txt
python3 -m unittest discover -s tests -v
```
