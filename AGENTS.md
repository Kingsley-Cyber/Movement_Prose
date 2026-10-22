# AGENTS.md — Deterministic Onboarding & Standard Operating Procedure

Welcome to **Movement_Prose** (`SAKUGA-MLLM-3.1-CAUSAL`, 2-Layer Unrolled Fluid Stack, & **BLOCK Fight Engine**).
Read this file **first** before reading, editing, linting, planning, or generating any fight plan or prompt in this repository.

---

## 1. Repository Map & Strict Directory Boundaries

```text
Movement_Prose/
├── AGENTS.md                                                  # 👈 START HERE: Deterministic agent onboarding, BLOCK & 25-Decision index
├── README.md                                                  # Unified setup, architecture, BLOCK model & CLI quick-start
├── SKILL.md                                                   # Antigravity / Claude Skill instructions (mirrored to ~/.gemini/config/skills/sakuga-fight-director)
├── pyproject.toml / requirements.txt                          # Package definition (`engine`, `fight_move_system`, `scripts`) & pinned deps
├── predict.py                                                 # 🥋 BLOCK CLI: Deterministic, uncalibrated matchup probability prediction
├── plan_fight.py                                              # 🥋 BLOCK CLI: Seeded/director-controlled fight planning, shotlist, prompts & `--movement-prose`
├── cards/                                                     # 🥋 11 BLOCK Fighter Identity Cards (`maleek`, `donnell`, `wrestler`, `macklin`, `detroit`, `philly`, etc.)
├── data/                                                      # 📊 Authoritative BLOCK Canon (`engine_index`, `matchups`, `model`, `counter_graph`, `debt_registry`, `techniques`, `combinations`, `pipeline`, `sources`, `claims`)
├── schemas/                                                   # 📐 Versioned BLOCK JSON Schemas (`fighter_card`, `fight_plan`, `fight_state`, `event`, `event_graph`, `shot`)
├── engine/                                                    # ⚙️ BLOCK Fight Engine Core (`ontology`, `audit`, `capabilities`, `matchups`, `probability`, `fight_director`, `fight_state`, `event_graph`, `choreography`, `prompt_compiler`)
├── resources/recovery.json                                    # Frozen BLOCK recovery bundle (restores only BLOCK-owned content; preserves authored values)
├── reports/                                                   # BLOCK audit, backfill, provenance, implementation decisions & `execution_evidence.json`
├── outputs/example_fights/                                    # Generated BLOCK + Movement_Prose fight packages (`maleek_vs_donnell`, `two_slot_upset`, `prediction.json`)
├── docs/
│   ├── model.md                                               # Exact BLOCK matchup calculation, logistic formula, state contract & research boundary
│   ├── llm_reasoning_guide.md                                 # Manual LLM retrieval/calculation sequence & worked trace tables
│   ├── FIGHT_MOVE_SYSTEM_PLAN.md                              # 🚀 v2 Master Architecture & Execution Plan (Move Lexicon, State Machine, Dyad Coupling, Wording Compiler)
│   ├── TWO_LAYER_FLUID_STACK_ARCHITECTURE.md                  # Deep-dive: Mode 1 (Single-Layer JSON) vs Mode 2 (--stack 2-Layer Fluid Stack)
│   └── VARIATIONS_AND_FIGHTING_STYLES.md                      # Deep-dive: Decisions 21-25, Entity Fighting Styles & Variations vs Golden Baseline
├── scripts/
│   ├── regress.py                                             # ✅ Single end-to-end acceptance workflow runner (`reports/execution_evidence.json`)
│   ├── audit_coverage.py / validate_data.py                   # Independent BLOCK 511-cell ontology, card, handler & provenance coverage audit
│   ├── backfill.py                                            # Deterministic, idempotent BLOCK missing-record recovery & conflict reporter
│   ├── sakuga_compiler.py                                     # 🔒 Original 05:34 (e91c686) Deterministic CLI Compiler & 17-Rule Physics Linter (SHA256 Locked)
│   ├── sakuga_original_kb.py                                  # 🔒 Dedicated 05:34 SAKUGA-MLLM-3.1-CAUSAL + Pre-Intent Knowledge Base Compiler Path
│   └── twelvelabs_bridge.py                                   # TwelveLabs Pegasus 1.2 Bridge (Mode A: Reference Extractor, Mode B: Render QA)
├── templates/
│   └── sakuga_mllm_3_1_causal_0534_template.json              # 🔒 Canonical Protected 05:34 (e91c686) Single-Layer SAKUGA-MLLM-3.1-CAUSAL Template
├── knowledge_base/                                            # 📚 IN-REPO KNOWLEDGE BASE (`anime_action_research_bundle` + `agent/` + `runs/002_rooftop_cage_fight`)
├── fight_move_system/                                         # 🚀 v2 Fight Move System + `block_bridge.py` + Protected 05:34 Compiler (`original_causal_compiler.py`) + Pre-Intent KB Query Engine (`kb_bridge.py`) + Closed-Loop Repair (`closed_loop.py`)
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
├── tests/                                                     # 🧪 98 Automated Tests (58 original BLOCK pytest tests + 40 Movement_Prose tests)
└── _archive_rd_history_do_not_copy/                           # ⛔ DEPRECATED R&D ARCHIVE (Euler/Quaternion/Bloat tests — NEVER COPY FROM HERE)
```

### Critical Boundary Rules for Agents:
1. **NEVER copy from `_archive_rd_history_do_not_copy/`**: Those files contain deprecated early experiments (`Euler dicts`, `Quaternions`, `v3.2 metadata bloat`) kept strictly for historical A/B logs.
2. **Keep `examples/gold_master_1..4` Distinct from `examples/variations/`**:
   - `examples/gold_master_1..4` are the **Original Canonical Golden Prompts** (ninja blade/kunai exchanges, courtyard sky-cartwheel/wall-run, and shrine bo-staff).
   - `examples/variations/` holds **Combat-Style & Biomechanical Variations** (such as `variation_1_baki_grounded_standup_war` and `variation_2_multidomain_combative_showcase`). All new fighting-style variations belong in `examples/variations/`.
3. **Preserve Protected `05:34` (`e91c686`) Single-Layer Compiler & BLOCK Provenance Boundaries**:
   - Never modify `scripts/sakuga_compiler.py` (`SHA256 = fdf54e5543e3ac9981878521136daafdd4086c1a1559af4673153512d433b498`).
   - Preserve the strict distinction in BLOCK between `[VERIFIED]` source claims (`data/claims.json` + `data/sources.json`), `[CANON]` tactical/numerical rules (`data/engine_index.json`, `data/matchups.json`), uncalibrated probabilities (`engine/probability.py`), and semantic motion validation (`engine/event_graph.py`, `engine/prompt_compiler.py`).

---

## 2. Where to Go Based on Your Task

| If the User Wants To... | Read This File First | Template / Tool to Use |
| :--- | :--- | :--- |
| Run the **BLOCK Fight Engine** (fighter cards $\to$ uncalibrated matchup prediction $\to$ 10-phase fight plan $\to$ event graph $\to$ choreography $\to$ shotlist $\to$ prompts $\to$ Movement_Prose bridge) | [`docs/model.md`](docs/model.md) & [`docs/llm_reasoning_guide.md`](docs/llm_reasoning_guide.md) | `.venv/bin/python predict.py ...`, `.venv/bin/python plan_fight.py ... --movement-prose`, or `.venv/bin/python scripts/regress.py` |
| Implement or extend the **v2 Fight Move System** (closed Move Card lexicon, Fighter/Dyad state machines, `V01–V22` validator, Wording Compiler, `block_bridge.py`) | [`docs/FIGHT_MOVE_SYSTEM_PLAN.md`](docs/FIGHT_MOVE_SYSTEM_PLAN.md) | Follow Milestones `M1` $\to$ `M6` in [`docs/FIGHT_MOVE_SYSTEM_PLAN.md`](docs/FIGHT_MOVE_SYSTEM_PLAN.md) |
| Compile via the **Protected Original `05:34` (`e91c686`) `SAKUGA-MLLM-3.1-CAUSAL` Single-Layer Path** with pre-intent Knowledge Base queries | [`fight_move_system/original_causal_compiler.py`](fight_move_system/original_causal_compiler.py) | `python3 scripts/sakuga_original_kb.py compile-spec ...` or `python3 -m fight_move_system.cli compile-original ...` |
| Generate a **grounded bare-knuckle / Baki / Kengan / UFC / boxing / kickboxing** fight (ZERO wall-runs, ZERO ground punches, ZERO aerial flip bleed) | [`docs/VARIATIONS_AND_FIGHTING_STYLES.md`](docs/VARIATIONS_AND_FIGHTING_STYLES.md) | [`examples/variations/variation_1_baki_grounded_standup_war.json`](examples/variations/variation_1_baki_grounded_standup_war.json) (`fighting_style: "grounded_striker_boxer_baki"` or `"ufc_mma_octagon"`) |
| Generate an **acrobatic multi-domain martial arts showcase** (floor sweeps, ground up-kicks, kip-ups, jumping knees, aerial axe kicks) | [`docs/VARIATIONS_AND_FIGHTING_STYLES.md`](docs/VARIATIONS_AND_FIGHTING_STYLES.md) | [`examples/variations/variation_2_multidomain_combative_showcase.json`](examples/variations/variation_2_multidomain_combative_showcase.json) (`fighting_style: "acrobatic_multidomain_freestyle"`) |
| Generate a **weapon / ninja / blade / bo-staff / acrobatic wall-dive** fight | [`docs/TWO_LAYER_FLUID_STACK_ARCHITECTURE.md`](docs/TWO_LAYER_FLUID_STACK_ARCHITECTURE.md) | [`examples/gold_master_2_disarm_dual_blade.json`](examples/gold_master_2_disarm_dual_blade.json), [`examples/gold_master_3_courtyard_sky_cartwheel.json`](examples/gold_master_3_courtyard_sky_cartwheel.json), or [`examples/gold_master_4_shrine_bo_staff_determinism_test.json`](examples/gold_master_4_shrine_bo_staff_determinism_test.json) |
| Understand **why a render had anatomical issues** (1 arm, merged torsos, deformed legs on knees, aerial sweeps bleeding into punch combos, static camera) | [`docs/VARIATIONS_AND_FIGHTING_STYLES.md`](docs/VARIATIONS_AND_FIGHTING_STYLES.md) & [`docs/TWO_LAYER_FLUID_STACK_ARCHITECTURE.md`](docs/TWO_LAYER_FLUID_STACK_ARCHITECTURE.md) | Run `python3 scripts/sakuga_compiler.py lint <file.json>` |

---

## 3. Master Index of All 25 Empirical Decisions (`Decisions 01–25`)

Every rule below is enforced or audited by [`scripts/sakuga_compiler.py`](scripts/sakuga_compiler.py) and [`fight_move_system/scene_graph_linter.py`](fight_move_system/scene_graph_linter.py):

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

Run the single end-to-end acceptance command or individual subsystem commands before committing:

```bash
# 0. Single End-to-End Acceptance Command (audits BLOCK, verifies backfill, runs all 98 pytest tests, verifies KB & 05:34 lock, and builds both example fights):
.venv/bin/python scripts/regress.py

# 1. Verify Protected 05:34 (e91c686) SAKUGA-MLLM-3.1-CAUSAL Compiler Lock & Compile via Pre-Intent KB Path:
.venv/bin/python scripts/sakuga_original_kb.py verify-protection
.venv/bin/python scripts/sakuga_original_kb.py compile-spec templates/sakuga_mllm_3_1_causal_0534_template.json --taste clean
.venv/bin/python scripts/sakuga_original_kb.py compile-beatsheet fight_move_system/fixtures/pass/10_beat_boxing_exchange.json --taste nakamura
.venv/bin/python scripts/sakuga_compiler.py lint examples/gold_master_1_blade_exchange.json examples/gold_master_2_disarm_dual_blade.json

# 2. Lint 25-Decision Scene Graphs (Golden #3, #4 & Variations) with the Fluid Stack Scene Graph Linter:
.venv/bin/python -m fight_move_system.scene_graph_linter lint examples/*.json examples/variations/*.json

# 3. Query the in-repo Knowledge Base PRIOR to semantic intent, verify KB invariants, and compile 2-Layer `sakuga_Xperiment`:
.venv/bin/python -m fight_move_system.cli kb-verify
.venv/bin/python -m fight_move_system.cli kb-ask fight_move_system/fixtures/pass/variation_3_eight_limbs_muay_thai_mma_war_sheet.json --taste "heavy, brutal, old school" --follow 2 --discover 2
.venv/bin/python -m fight_move_system.cli compile fight_move_system/fixtures/pass/variation_3_eight_limbs_muay_thai_mma_war_sheet.json \
  --mode xperiment --schema sakuga_Xperiment \
  -o examples/variations/variation_3_eight_limbs_muay_thai_mma_war_sakuga_Xperiment.txt

# 4. Run BLOCK Fight Engine Prediction, Fight Planning, & Movement_Prose Bridge:
.venv/bin/python predict.py cards/maleek.json cards/donnell.json --ruleset mma --output outputs/example_fights/prediction.json
.venv/bin/python plan_fight.py cards/maleek.json cards/donnell.json --ruleset mma --duration 60 --seed 42 --output-dir outputs/example_fights/maleek_vs_donnell --movement-prose
.venv/bin/python plan_fight.py cards/wrestler.json cards/donnell.json --ruleset mma --duration 60 --seed 42 --output-dir outputs/example_fights/two_slot_upset --movement-prose
```

---

## 5. Cross-Platform Compatibility (macOS / Mac Studio, Windows, & Linux)

This repository is engineered to run identically across **macOS (Mac Studio / Apple Silicon)**, **Windows (PowerShell / CMD / WSL2)**, and **Linux** using Python 3.9+ (`pathlib.Path`, `sqlite3`, `json`, `hashlib`, `jsonschema`, `pytest`, `unittest`):

1. **Zero Hardcoded Machine Paths (`pathlib.Path` & URI Resolution):**
   - All repository modules (`engine/`, `fight_move_system/`, `scripts/`, `knowledge_base/agent/`) resolve paths dynamically relative to `__file__` and use `Path.resolve().as_uri()` for read-only SQLite URI connections so Windows drive letters (`C:\...`) and POSIX paths (`/Users/...`, `/home/...`) both work out of the box.
   - To override the Knowledge Base location on any OS, set the `ANIME_KB_BUNDLE_DIR` environment variable:
     - **macOS / Linux (`zsh` / `bash`):** `export ANIME_KB_BUNDLE_DIR="/path/to/knowledge_base"`
     - **Windows (`PowerShell`):** `$env:ANIME_KB_BUNDLE_DIR = "C:\path\to\knowledge_base"`
     - **Windows (`CMD`):** `set ANIME_KB_BUNDLE_DIR=C:\path\to\knowledge_base`
2. **Pre-Indexed `handbook_index.db` Setup (Mac Studio, Windows, Linux):**
   - `knowledge_base/ai_video_compiler.db` (frozen 64-row lexicon) and `knowledge_base/agent_memory.db` (growing memory) are tracked directly in Git.
   - `knowledge_base/handbook_index.db` (~131 MB FTS5 index) is ignored by Git (`.gitignore`) to stay under GitHub's 100 MB file limit. On a new clone (Mac Studio, Windows, or Linux), either copy `handbook_index.db` into `knowledge_base/` or rebuild it locally in ~13 seconds from `handbook.html`:
     ```bash
     # macOS / Linux:
     cd knowledge_base && python3 -m agent index-handbook /path/to/handbook.html && python3 -m agent verify
     # Windows (PowerShell):
     cd knowledge_base; python -m agent index-handbook C:\path\to\handbook.html; python -m agent verify
     ```
3. **Python Executable Invocation (`python3` vs `python` / `py -3`):**
   - On **macOS (Mac Studio) & Linux**, use `.venv/bin/python` or `python3`.
   - On **Windows**, use `.venv\Scripts\python.exe`, `python`, or `py -3`.
