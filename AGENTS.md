# AGENTS.md — Agent-Led Operating Protocol, Non-Technical User BLUF Guide & Deterministic Onboarding

Welcome to **Movement_Prose** (`SAKUGA-MLLM-3.1-CAUSAL`, 2-Layer Unrolled Fluid Stack, & **BLOCK Fight Engine**).
Read this file **first** before interacting with the user, reading, editing, linting, planning, or generating any fight plan or prompt in this repository.

---

## 0. AGENT-LED OPERATING MODEL & NON-TECHNICAL USER BLUF PROTOCOL (MANDATORY)

> **CRITICAL DIRECTIVE FOR ALL AI AGENTS:**
> This repository is **100% Agent-Led, Agent-Managed, Agent-Updated, and Agent-Executed**.
> Your human user may **not** be technical or comfortable with terminals, CLI flags, Python virtual environments, or JSON schemas.
> **Your job is to:**
> 1. **Onboard the user in plain English with a BLUF (Bottom Line Up Front) overview** of what this repository does and its 3 Core Flows whenever they ask what this repo is or how to use it.
> 2. **Execute everything in the background based on the user's plain-English intent** (auto-creating `.venv` if needed, querying the Knowledge Base, simulating matchups, planning fights, compiling prompts, or repairing renders) and return ready-to-use results and plain-English explanations—**never dump raw terminal commands on a non-technical user and ask them to run them manually.**
> 3. **Maintain and update the repository yourself** (running tests, audits, Knowledge Base updates, and Git operations) while keeping the user informed in clear, jargon-free language.

### What to Tell the User: Plain-English BLUF (Bottom Line Up Front)

When introducing this system to a user, explain it using this **BLUF Summary**:

* **BLUF (Bottom Line Up Front):** **Movement_Prose** is an AI-operated fight director, tactical combat simulator, and anime action ("Sakuga") video prompt studio. You simply tell the agent **who is fighting**, **what style or outcome you want**, or **what went wrong in a video render**, and the agent automatically handles all the math, martial arts research, choreography planning, and prompt engineering behind the scenes.

### The 3 Core Flows (Explain These Clearly to Users & Execute Automatically)

#### Flow 1: The Knowledge Base Flow (`knowledge_base/` — Queried *Before* Any Fight Is Written)
* **What It Does (Plain English):** Before the agent writes a single punch or camera move, it automatically looks up real martial arts biomechanics and 2D anime animation principles from an built-in library of **30,275 indexed combat & animation passages** (`handbook_index.db`, auto-extracted on first use), **64 empirical Sakuga physics rules** (`ai_video_compiler.db`), and **Agent Memory** (`agent_memory.db` — which remembers past fixes that worked).
* **Why It Matters to the User:** Every fight beat uses authentic weight transfer, impact freeze-frames ("hit-stop"), smear rules, and camera framing instead of generic AI guesswork—and the system gets smarter after every video you judge.

#### Flow 2: The Fighting Simulator & Matchup Engine (`BLOCK Fight Engine` — `predict.py`, `plan_fight.py`, `cards/`, `data/`, `engine/`)
* **What It Does (Plain English):** Acts as a tactical martial-arts simulator across **11 pre-built fighters** (or custom fighters the agent creates for you), **7 combat dimensions** (`hands`, `defense`, `stance`, `tie/clinch`, `target`, `kicking`, `mentality`), and **511 style-vs-style matchup interactions**.
  * **Mode A — Matchup Predictor:** Tells you each fighter's tactical win probability (e.g., `54.5% vs 45.5%`), what openings/weaknesses exist (like a missing clinch game or a 2-piece combo advantage), and how they match up under Boxing, Muay Thai, Kickboxing, MMA, or Street rules.
  * **Mode B — 10-Phase Fight Simulator & Director:** Simulates a complete 30-to-60-second fight step-by-step (`Read -> Setup -> Exchange -> Clinch/Counter -> Finish/Decision`)—either letting the simulation decide the winner or locking in **your chosen winner** (`Director Mode`)—and outputs a full move-by-move fight plan, camera shot list, and video prompts.

#### Flow 3: The Dual-Path Sakuga Video Prompt Compiler & Render Repair Loop (`Movement_Prose` — `fight_move_system/`, `scripts/`)
* **What It Does (Plain English):** Turns either a **simulated BLOCK fight** or your **custom fight idea** into copy-paste-ready prompts for AI video generators (Seedance 2.0 Mini, Seedance 2.5, Kling, Wan, etc.) using **TWO CO-EQUAL PROMPT SCHEMAS** (both are first-class, supported, and maintained):
  1. **Schema 1: The Original Baseline Schema (`SAKUGA-MLLM-3.1-CAUSAL`):**
     * Formal schema: [`schemas/sakuga_mllm_3_1_causal.schema.json`](schemas/sakuga_mllm_3_1_causal.schema.json)
     * Template: [`templates/sakuga_mllm_3_1_causal_0534_template.json`](templates/sakuga_mllm_3_1_causal_0534_template.json)
     * Our original compact single-layer format (natural language header + 1-line-per-beat causal JSON with 11-key `A_beats`, 8-key `B_track`, explicit `C01..C16` causal graph, and 17-Rule physics linter). Cryptographically locked to `05:34` (`e91c686`).
  2. **Schema 2: The Extreme / Advanced 2-Layer Schema (`sakuga_Xperiment`):**
     * Formal schema: [`schemas/sakuga_xperiment.schema.json`](schemas/sakuga_xperiment.schema.json)
     * Templates: [`templates/sakuga_xperiment_template.json`](templates/sakuga_xperiment_template.json) (input JSON) & [`templates/sakuga_xperiment_2layer_template.txt`](templates/sakuga_xperiment_2layer_template.txt) (compiled 2-layer prompt)
     * The extreme 2-Layer Unrolled Fluid Stack format: pairs Layer 1 (*Labanotation-as-Words* continuous support, force-event & prop timeline with weight split `%`, Center of Gravity `CoG`, and easing curves) directly above Layer 2 (Kinematic Scene Graph with V01–V22 biomechanical attributes: bilateral two-arm silhouette lock, standing-pillar leg separation, realistic reach spacing, 180° camera hemisphere lock, and fighting-style archetype gating).
  3. **Shot-by-Shot Cinematic Prose (`video_prompts.jsonl`):** Clean, model-agnostic shot-by-shot camera and movement descriptions generated by the BLOCK engine.
* **Closed-Loop Video Fixer:** If a rendered video clip has a glitch (e.g., *"at 3 seconds his left arm disappears"* or *"the kick looked floaty"*), just tell the agent in plain English—the agent automatically patches only that specific beat and records the lesson in Agent Memory.

### Agent Intent-to-Action Routing Table (How Agents Must Execute User Intent Automatically)

| When the User Says (Plain-English Intent)... | What the Agent Automatically Runs in the Background | What the Agent Presents Back to the User |
| :--- | :--- | :--- |
| *"What does this repo do?"* / *"How do I use this?"* | Nothing needed (or quick health check) | The **BLUF summary** above + the **3 Core Flows** + 3 simple examples of what they can ask for right now. |
| *"Who wins between Maleek and Donnell?"* / *"Compare a Philly Shell boxer vs a Muay Thai kickboxer"* | `.venv/bin/python predict.py --fighter-a cards/<A>.json --fighter-b cards/<B>.json --ruleset <ruleset>` | A plain-English breakdown of the matchup probabilities, each fighter's key tactical advantages, and exploitable openings. |
| *"Simulate a 60-second fight between [A] and [B] (or make [A] win) and give me the video prompts"* | `.venv/bin/python plan_fight.py --fighter-a cards/<A>.json --fighter-b cards/<B>.json --duration 60 --seed 42 [--winner a\|b] --movement-prose --output-dir outputs/<run>` | A clear summary of the 10-phase fight story, key exchanges, and the ready-to-paste video prompts (`2-Layer Fluid Stack`, `05:34 Single-Layer`, and `Shot-by-Shot Prose`). |
| *"Write me a 10-second anime fight prompt (grounded Baki brawl / ninja blade duel / Muay Thai rooftop war)"* | Queries KB (`kb-query`) $\to$ builds/selects spec $\to$ compiles via `fight_move_system.cli compile` (`--mode sakuga_Xperiment`) **or** `compile-original` (`05:34` path) $\to$ runs 25-rule linter | The verified, copy-paste-ready prompt file + a short explanation of the choreography beats and camera cuts. |
| *"Use the original 05:34 prompt format with the knowledge base"* | `.venv/bin/python scripts/sakuga_original_kb.py compile-spec <spec.json> --out <out.txt>` | The protected `05:34` (`e91c686`) Single-Layer `SAKUGA-MLLM-3.1-CAUSAL` prompt enriched by the Knowledge Base, plus verification that all 17 physics rules passed. |
| *"In my rendered video, the fighter lost an arm / merged bodies / floated at 3.5 seconds—fix it"* | `.venv/bin/python -m fight_move_system.cli repair --spec <spec.json> ...` (and logs verdict in `agent_memory.db`) | The updated, repaired prompt with only the broken beat fixed, explaining what changed and confirming the lesson was saved to Agent Memory. |
| *"Make sure everything in the repo is working / installed"* | Creates `.venv` if missing, installs `requirements.txt`, and runs `.venv/bin/python scripts/regress.py` | A simple green-light confirmation that all databases, 105 automated tests, and example pipelines passed. |

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
2. **Pre-Indexed `handbook_index.db.gz` Automatic Extraction (Mac Studio, Windows, Linux):**
   - `knowledge_base/ai_video_compiler.db` (frozen 64-row lexicon), `knowledge_base/agent_memory.db` (growing memory), and `knowledge_base/handbook_index.db.gz` (`9.8 MB` compressed FTS5 index) are all tracked directly in Git.
   - On any fresh `git clone` (Mac Studio, Windows, or Linux), `knowledge_base/agent/__init__.py` and `fight_move_system/kb_bridge.py` automatically decompress `handbook_index.db.gz` into `knowledge_base/handbook_index.db` on first import (~0.8s), so all 25 Knowledge Base checks and 105 tests pass out of the box with zero manual setup.
3. **Python Executable Invocation (`python3` vs `python` / `py -3`):**
   - On **macOS (Mac Studio) & Linux**, use `.venv/bin/python` or `python3`.
   - On **Windows**, use `.venv\Scripts\python.exe`, `python`, or `py -3`.

---

## 6. Semantic Verification & Claim-Checked Renderer Backlog (Deferred to Future Compiler Session)

> **Current Session Focus vs. Future Compiler Session:**  
> Right now, our active focus on `exp/latent-sakuga-causal-readability` is **Pure Natural-Language (NL) Prompt Engineering A/B Testing** (sticking to NL contracts/prose rather than JSON schemas that can violate causal-readability rules).  
> However, during our `LBN-2.3-ADV v3` Pillar Fight recompilation, we identified **6 semantic contradictions** in the source score/rendered prose that JSON Schema and our current validators did **not** catch. The full ADR and implementation blueprint are captured in **[`docs/ADR_CLAIM_CHECKED_RENDERER_AND_SEMANTIC_VERIFIER.md`](docs/ADR_CLAIM_CHECKED_RENDERER_AND_SEMANTIC_VERIFIER.md)** for our next dedicated compiler session.

### 6.1 The 10 Annotated Semantic & Readability Issues (`SEM-BUG-01` – `SEM-BUG-10`)
*(Categorized by whether our native repo already prevents them vs. what came from translating a flawed external score vs. new scan rules needed — see full table in [`docs/ADR_CLAIM_CHECKED_RENDERER_AND_SEMANTIC_VERIFIER.md`](docs/ADR_CLAIM_CHECKED_RENDERER_AND_SEMANTIC_VERIFIER.md)):*
1. **`SEM-BUG-01` (Ungoverned Franchise/Style Literal):** Hand-typed franchise string (`"Naruto Shippuden and Sword of the Stranger style"`) instead of a governed style token from the IR (`SCAN-01`).
2. **`SEM-BUG-02` (Count vs. List Drift):** Prose header states `"SIX tracked props"`, while the numbered ledger lists only `5` entries (merging `smoke_pellet` and `substitution_log` into item `(3)` instead of rendering from `len(ir.props)`) (`SCAN-02`).
3. **`SEM-BUG-03` (Stale Guardrail vs. State Replay Contradiction):** Negative guardrail says `"no B standing up after 5.00s knockdown"`, yet B throws shuriken (`5.5s`), lands (`6.3s`), grapples A (`6.6s–6.8s`), and throws A (`7.0s`). Real knockdown is `8.75s–8.77s` (`9.00s` prone). *(Already prevented in native `validator.py` V04/V05; leaked here from copying raw external XML rule)* (`SCAN-03`).
4. **`SEM-BUG-04` (Pillar & Screen-Space Geometry Contradiction):** Global lock `"A stays on screen-left"` + `"pillar on right"` conflicts with A starting on the pillar, B's shuriken flying past A into the pillar behind A (`Pillar <-- A <-- B`), A reappearing *behind B's spine* at `4.4s`, and B throwing A into the pillar at `7.0s` (`SCAN-04`).
5. **`SEM-BUG-05` (Interval Containment & Dead-Air Gaps):** `Beat 1` labeled `0.00s–0.60s` while its pillar sprint runs to `1.60s`, plus unaccounted dead-air gaps (`3.00s–3.70s`, `5.10s–5.50s`, `7.05s–7.50s`). *(Already prevented in native `compiler.py` frame-contiguous windows; leaked here from grouping sparse external keyframes)* (`SCAN-05`).
6. **`SEM-BUG-06` (2.0s Slow-Motion Floating Projectile):** Kunai thrown at `0.50s` not reaching A's foot until `2.50s` (`2.0s` flight across a few meters) (`SCAN-06`).
7. **`SEM-BUG-07` (4.1s "Orbiting Kunai" Gravity & Object-Permanence Paradox):** Kunai deflected upward at `2.50s`, disappears for `4.1s` across Beats 3–5, and is caught falling out of mid-air at `6.60s` (would require a $20.6\text{m}$ / 6-story apex; fix by embedding deflected kunai into the stone pillar at `2.70s` so A snatches it from the pillar face during his `7.00s` wall-plant!). *(Native `05:34` template kept kunai toss to `1.2s`; external `LBN-2.3` stretched it to `4.1s`)* (`SCAN-07`).
8. **`SEM-BUG-08` (Bilateral Hand-Occupancy & Target-Slot Collision):** A draws `rope_dart` into `L_hand` at `3.00s`, then plants `L_hand` flat on the floor for a cartwheel at `6.30s`; then at `7.60s–8.50s` both the `rope_dart` wrap and the `kunai` stab target the exact same joint (`B's right shoulder`) simultaneously (`SCAN-08`).
9. **`SEM-BUG-09` (Action-Density & Sub-Frame Timestamp Overload):** `33` decimal timestamps (including half-frame ticks like `4.70s` vs `4.72s`, `8.75s` vs `8.77s`) and `11` exchanges in 10s overload text-encoder attention. *(Already prevented in native `causal_readability_compiler.py` via `_strip_digits_and_metrics()`; bypassed in ad-hoc script)* (`SCAN-09`).
10. **`SEM-BUG-10` (Triple-Duplicated Camera & FX Instructions):** Camera shots and FX sparks written 3 times (`CAMERA LAYER` + per-beat `[View]/[License]` + `SAKUGA FX LAYER`), bloating prompt length (`SCAN-10`).

### 6.2 Proven Compiler & Planner Methods to Wire In
- [ ] **Single Source of Truth (`IR -> Prose`):** Never author a fact twice; counts (`len(props)`), interval labels (`[min_t, max_t]`), and prop ledgers are computed from `IntentIR`.
- [ ] **State Replay / Event Sourcing (Petri-Net Conservation):** Replay every event chronologically against a single world state (`WorldStateAtTime[t]`) so each fighter and prop has exactly one state per moment.
- [ ] **Precondition & Effect Checking (PDDL / VAL Validation):** Every action checks preconditions (`grapple` requires `B.support == standing`) and applies effects (`FE4_ground_slam` sets `B.support = prone` at `8.77s`).
- [ ] **Temporal Constraint Networks (Allen's Interval Algebra & Dechter's STN):** Enforce beat interval containment (`Beat` interval $=$ convex hull of sub-events) and realistic projectile flight-time bounds ($\Delta t \in [d/v_{\max}, d/v_{\min}]$).
- [ ] **Qualitative Spatial Reasoning & SAT/SMT Unsat Cores (Z3-Style):** Catch `"A stays screen-left"` vs. `"A behind B / at right-side pillar"` and return the **minimal unsat core** of conflicting clauses.

### 6.3 The 5-Part "Claim-Checked Renderer" To-Do List (See [`docs/ADR_CLAIM_CHECKED_RENDERER_AND_SEMANTIC_VERIFIER.md`](docs/ADR_CLAIM_CHECKED_RENDERER_AND_SEMANTIC_VERIFIER.md))
- [ ] **1. Fact-Linked Sentence IDs (`ClaimProvenance`):** Every emitted sentence carries an ID linking it to replayed world-state facts; unlinked sentences are flagged as decoration; false claims fail compilation.
- [ ] **2. Round-Trip Prose Parse & Diff (`ProseClaimExtractor`):** Parse rendered prose back into structured facts (`who, what, which hand/prop, when, screen side, count`) and diff against the replayed graph to catch renderer/template leaks (like `"5.00s knockdown"`).
- [ ] **3. State-Generated Guardrails (Never Hand-Written):** Synthesize negative lines (`"no B standing after 8.77s knockdown"`) directly from state changes in the replay graph.
- [ ] **4. 2D Screen-Space Projection Check (`ScreenSpaceProjector`):** Project each beat into 2D for its camera phase to test the 180-degree rule, screen-left/right ordering, and occlusion.
- [ ] **5. Human-in-the-Loop Conflict Resolution (Never Auto-Fixed):** When claims conflict, surface the minimal conflict set with 2–3 explicit repair options to the user so nothing is silently cut or trimmed.

---

## 7. BLOCK Fight Simulator v2 Architecture & Agent Operating Rules (See [`docs/BLOCK_SIMULATOR_V2_DESIGN_SPEC.md`](docs/BLOCK_SIMULATOR_V2_DESIGN_SPEC.md))

The BLOCK Fight Simulator v2 (`engine/simulator_v2.py`, `scripts/build_v2_data.py`, `data/option_behaviors.json`, `data/techniques_v2.json`, `data/positions.json`, `data/model_v2.json`, and the 9 v2 JSON schemas in `schemas/`) runs **100% off card and ontology data** without physical height/weight/speed stats:

- [x] **1. Dynamic Defensive Posture & 8-Lane Readiness Calculator (`compute_posture_state`, `compute_readiness_profile`):** Defense is not a static label — it is a live defensive posture built from **Guard (`hands`) + Stance (`weight_split`, `height`, `hip_angle`, `base_width`) + Head Position + Defense Method (`defense`)**, recomputed every exchange across all 8 lanes (`head_straight`, `head_hook`, `head_uppercut`, `body`, `leg`, `entry`, `clinch`, `single_support`) and modified by 11 live fight states:
  1. Fighter's own prior attack (`recovery_window`: `single_leg_recovery`, `extended_arm_recovery`, `wide_swing_recovery`, `sprawled_shot_recovery`, `airborne_landing_recovery`),
  2. Balance state (`stable`, `compromised`, `off_base`),
  3. Range & outside angle (`clinch`/`ground` shifts defense from guard to `tie` + `sub_grips`),
  4. Lead-foot matchup (`open_stance` vs. `closed_stance`),
  5. Space (`wall_proximity == "near"` breaks down `defense.outfight`),
  6. Attention (`feinted` pulls guard/eyes),
  7. Reads (`read_memory`: bonus against repeated moves, novelty penalty on first sight),
  8. Fatigue (guard drops, reactions slow),
  9. Regional damage (`head` slows reactions; `body` drops elbows and decays `guard_integrity`; `leg` disables `check_frame` and mobility),
  10. Mentality (`risk_appetite`),
  11. Grips (`underhooks`, `wrist_control`, `head_position`).
- [x] **2. All 9 v2 Data Contracts (`schemas/`) & Authored Catalogs (`data/`):**
  - `schemas/fighter_card_v2.schema.json` (accepts both `block-1` and `block-2` cards, validated on all 11 canonical cards + `cards/v2/sanda_judo.json` `Mio Tsukihara`)
  - `schemas/option_behavior.schema.json` $\to$ `data/option_behaviors.json` (all 57 style options)
  - `schemas/technique_v2.schema.json` $\to$ `data/techniques_v2.json` (38 techniques with 24fps frame costs, biomechanics, recovery windows, base damage)
  - `schemas/position_map.schema.json` $\to$ `data/positions.json` (15 positions + 14 transitions)
  - `schemas/fight_settings.schema.json`, `schemas/model_config_v2.schema.json` ($\to$ `data/model_v2.json`), `schemas/fight_state_v2.schema.json`, `schemas/exchange_event_v2.schema.json`, `schemas/simulation_result_v2.schema.json`.
- [x] **3. First-Class Kicking Subsystem, Grappling Position Map, Slot Gameplans & Card-Derived Damage:** Implemented and verified in `engine/simulator_v2.py` and `tests/test_simulator_v2_and_atomic_compiler.py`.

### 7.1 Mandatory Agent Rules for Authoring Cards & Running Simulations
1. **How to Build a `block-2` Card from a Plain-English Character Description:**
   - Map the fighter's habits onto the 7 dimensions in `data/engine_index.json` (`hands`, `defense`, `stance`, `tie`, `target`, `kicking`, `mentality`) + `tempo (1..5)` + `orientation (orthodox/southpaw/switching)`.
   - Define `1..4` `synchronized_capabilities` slots (`Brawler=1`, `Two-piece=2`, `Triad=3`, `Anomaly=4`), giving each slot its `capabilities`, `trigger`, `sequence`, `home_range`, `goal`, `abandon_rule`, and `links` (see `cards/v2/sanda_judo.json` as the canonical worked example).
   - Populate `exploitable_seams` with the union of `exploitable_debt_ids` from all chosen options in `data/engine_index.json` (never omit an option's required debts).
   - Validate the card with `Knowledge().card(card_dict)` and `schemas/fighter_card_v2.schema.json`.
2. **When to Run Many-Runs (`simulate_many_v2`) vs. Single-Run (`simulate_fight_v2`) vs. Director Mode (`directed_winner`):**
   - Use **`simulate_many_v2(a, b, runs=50..200)`** when evaluating a matchup's empirical win rate, method-of-victory distribution (`KO/TKO`, `Submission`, `Decision`), and deciding slots/weakness lanes.
   - Use **`simulate_many_v2(a, b, runs=50, directed_winner="fighter_id")`** when the user or story requires a specific winner: Director Mode selects a realistic seeded run where that fighter naturally won through their card's trained gameplan, rather than forcing artificial moves.
   - Use **`simulate_fight_v2(a, b, seed=S)`** for deterministic single-fight inspection and exchange-by-exchange replay.
3. **Strict Trained-Moves-Only Rule (Zero Untrained Moves):**
   - Never add or emit any technique in a slot sequence, exchange, or counter that is not in `available(k, card, ruleset)` (gated by the card's `active_techniques` and trained `capabilities`).
