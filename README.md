# Movement_Prose (`SAKUGA-MLLM-3.1-CAUSAL`, 2-Layer Fluid Stack & BLOCK Fight Engine)

> **🤖 100% AGENT-LED, AGENT-MANAGED, AGENT-UPDATED & AGENT-EXECUTED REPOSITORY**
> **You do not need to know terminal commands, Python, or code to use this project.**
> Open this repository in your AI coding agent (Antigravity, Codex, Claude Code, Cursor, etc.) and simply tell the agent what kind of fight you want to simulate or generate in plain English. The agent will read [`AGENTS.md`](AGENTS.md), explain your options using the **BLUF Guide** below, and run every tool automatically in the background for you.

---

## BLUF (Bottom Line Up Front) — What This Repo Does in Plain English

**Movement_Prose** is an all-in-one **AI Fight Director, Martial Arts Matchup Simulator, and Anime Action ("Sakuga") Video Prompt Studio**. Instead of writing complex video prompts by hand or guessing how two fighting styles interact, you just tell your AI agent your idea—and the agent runs **3 Connected Flows** behind the scenes:

### 1. 📚 The Knowledge Base Flow (`knowledge_base/` — Consulted *Before* Every Fight)
Before your agent writes any choreography, it automatically searches a built-in martial arts and animation library containing:
- **30,275 Passages from a 21-Chapter Action & Biomechanics Handbook** (`handbook_index.db`, automatically unpacked on first run) covering real strike mechanics, footwork, camera angles, and impact framing.
- **64 Verified Sakuga Physics Directives** (`ai_video_compiler.db`) that prevent common AI video glitches (like floating jumps, missing arms, or early flinches).
- **Growing Agent Memory** (`agent_memory.db`) that remembers which prompt fixes solved video glitches in earlier renders so the system gets smarter over time.

### 2. 🥋 The Fighting Simulator & Matchup Engine (`BLOCK Fight Engine v1 & v2` — `simulate_fight.py`, `predict.py`, `plan_fight.py`, `cards/`, `cards/v2/`, `data/`, `engine/`)
Want to know how two fighters match up—or want a realistic, exchange-by-exchange fight simulation generated automatically?
- **BLOCK Fight Simulator v2 (`simulate_fight.py` & `engine/simulator_v2.py`):** Order-invariant, card-driven exchange simulator across **12 pre-built `block-2` fighter archetypes** (`cards/v2/*.json`: `detroit`, `donnell`, `greco`, `jiujitsu`, `karate`, `macklin`, `maleek`, `philly`, `sanda_judo`, `street`, `thai`, `wrestler`) and **all 57 style options**:
  - **Strict Attack vs. Defense Option Split:** Defensive dimensions (`hands`, `defense`, `stance`, `tie`) set `lane_readiness_bonus` across 8 defensive lanes (`head_straight`, `head_hook`, `head_uppercut`, `body`, `leg`, `entry`, `clinch`, `single_support`), while offensive dimensions (`target`, `kicking`, `mentality`) set `attack_profile` (`lane_accuracy_bonus`, `lane_damage_mult`, `preferred_lanes`) and only contribute defensive vulnerabilities (`lane_vulnerability`).
  - **Smooth Diminishing-Returns Posture Readiness (`asymptote = 2.40`):** Replaces hard caps so stacking complementary guard + defense + stance layers always matters without creating an unhittable wall.
  - **Contested Rolls & Dynamic Breakdown:** Every range change, strike, kick catch, caught-kick sweep, and counter is a contested roll (`[10%, 85%]`) modified by 11 live fight states (recovery windows, balance, stance alignment, wall proximity, feints, read memory, fatigue, regional head/body/leg damage, and clinch grips).
  - **200-Seed Round-Robin Balance Audit (`--balance-audit`) & 57-Option Viability Audit (`--option-audit`):** Verifies order invariance, confirms all 12 archetypes sit within the `[35%, 65%]` fair competitive band (`39.4%`–`61.1%`, zero `>85%` matchups), and validates all `57/57` options via single-option perturbation testing.
- **Tactical Matchup Predictor & 10-Phase Planner (`predict.py` & `plan_fight.py`):** Compares **11 canonical `block-1` fighter cards** across **7 combat dimensions** and **511 style-vs-style interactions**, calculating uncalibrated win probabilities or simulating a 10-phase bout with optional `Director Mode` (`--winner`).

### 3. 🎬 The Dual-Path Sakuga Video Prompt Compiler, Atomic 1-Contact-Per-Beat Compiler & Glitch Repair Loop (`Movement_Prose` — `fight_move_system/`, `scripts/`)
Takes either a **simulated BLOCK fight** or your **custom fight concept** and compiles it into ready-to-paste AI video prompts (for Seedance 2.0 Mini, Seedance 2.5, Kling, Wan, etc.) using **TWO OFFICIAL CO-EQUAL PROMPT SCHEMAS** plus the **Atomic 1-Contact-Per-Beat Causal Compiler**:
1. **Schema 1: The Original Baseline Schema (`SAKUGA-MLLM-3.1-CAUSAL`):**
   - **Schema & Template:** [`schemas/sakuga_mllm_3_1_causal.schema.json`](schemas/sakuga_mllm_3_1_causal.schema.json) | [`templates/sakuga_mllm_3_1_causal_0534_template.json`](templates/sakuga_mllm_3_1_causal_0534_template.json)
   - **Format:** Single-Layer causal JSON structure (header + 1-line-per-beat causal JSON with 11-key `A_beats`, 8-key `B_track`, explicit `C01..C16` causal graph, and 17-Rule physics linter). Cryptographically locked (`SHA256`) to the `05:34` (`e91c686`) baseline.
2. **Schema 2: The Extreme / Advanced 2-Layer Schema (`sakuga_Xperiment`):**
   - **Schema & Templates:** [`schemas/sakuga_xperiment.schema.json`](schemas/sakuga_xperiment.schema.json) | [`templates/sakuga_xperiment_template.json`](templates/sakuga_xperiment_template.json) | [`templates/sakuga_xperiment_2layer_template.txt`](templates/sakuga_xperiment_2layer_template.txt)
   - **Format:** The extreme 2-Layer Unrolled Fluid Stack format: pairs Layer 1 (*Labanotation-as-Words* continuous support, force-event & prop timeline with weight split `%`, Center of Gravity `CoG`, and easing curves) directly above Layer 2 (Kinematic Scene Graph with V01–V22 biomechanical attributes: bilateral two-arm silhouette lock, standing-pillar leg separation, realistic reach spacing, 180° camera hemisphere lock, and fighting-style archetype gating).
3. **Atomic 1-Contact-Per-Beat Causal Compiler (`fight_move_system/atomic_causal_compiler.py` & `simulate_fight.py --emit-prompt`):**
   - Unrolls simulated v2 exchanges into strict 1-Contact-Per-Beat (`Prep -> Commit -> Contact -> Consequence -> Recovery`) natural-language Seedance prompts verified by a 5-part claim-checked semantic verifier (`SEM-BUG-01..10`).
4. **BLOCK Shot-by-Shot Cinematic Prose (`video_prompts.jsonl`):** Clean, model-agnostic shot-by-shot camera and movement descriptions.
- **Instant Video Glitch Repair:** If a rendered video has a flaw (e.g., *"his arm vanished at 3 seconds"* or *"they stood too far apart"*), just tell your agent. The agent automatically repairs only that specific beat and saves the lesson into Agent Memory.

### 💬 What You Can Ask Your Agent Right Now (Zero Terminal Required)
- *"Simulate a fight between Mio Tsukihara (`sanda_judo`) and Niran Sol (`thai`) in the cage and emit the 1-contact-per-beat video prompt."*
- *"Run a 200-seed series between Rook Mercer (`street`) and Niran Sol (`thai`) and break down why each wins."*
- *"Run the 200-seed Round-Robin balance audit and the 57-option viability audit."*
- *"Give me the BLUF on this repo, explain both the Original and Extreme prompt schemas, and show me the fighters available."*
- *"Who wins between Maleek and Donnell under MMA rules, and what is Donnell's biggest opening?"*
- *"Simulate a 60-second fight between Imani Vale (wrestler) and Donnell where Imani exploits his missing clinch game, and generate the video prompts in both Original and Extreme formats."*
- *"Create a 10-second grounded Baki-style bare-knuckle brawl prompt using the Extreme sakuga_Xperiment schema and the Knowledge Base."*
- *"Compile my fight using the original 05:34 SAKUGA-MLLM-3.1-CAUSAL single-layer prompt format."*
- *"In my video render, the kick at 4 seconds looked floaty—fix that beat."*

---

## Technical Overview (For Agents & Developers)

**Movement_Prose** (`movement-prose-e2e` / `sakuga-fight-director`) is an integrated, offline-first combat reasoning, semantic fight direction, and biomechanical Sakuga prompt compilation system combining:
1. **BLOCK Fight Simulator v2 (`simulate_fight.py`, `engine/simulator_v2.py`, `scripts/build_v2_data.py`, `cards/v2/`, `data/option_behaviors.json`, `data/model_v2.json`, `data/techniques_v2.json`, `data/positions.json`, `schemas/*_v2.schema.json`):** Order-invariant, card-driven exchange simulator across 12 predefined `block-2` fighter archetypes and 57 mechanical style options (`attack_profile` vs. `lane_readiness_bonus`), featuring dynamic posture state, smooth diminishing-returns 8-lane readiness (`asymptote = 2.40`), first-class kicking anatomy, 15-node grappling position map, 24fps fight clock, 6 arena presets, 200-seed Round-Robin balance auditing (`--balance-audit`), and 57-option viability auditing (`--option-audit`).
2. **BLOCK Fight Engine v1 (`engine/`, `cards/`, `data/`, `schemas/`, `predict.py`, `plan_fight.py`):** Loads fictional fighter cards, calculates deterministic uncalibrated matchup probabilities across 7 dimensions and 511 canonical cells, constructs seeded or director-controlled causal fight event graphs, and compiles traceable model-agnostic cinematic shotlists and prompts (`shotlist.json`, `video_prompts.jsonl`).
3. **Fight Move System v2 & Atomic Causal Compiler (`fight_move_system/`):** Deterministic 2-Layer Unrolled Fluid Stack (`sakuga_Xperiment` & `lean`) compiler, Atomic 1-Contact-Per-Beat Causal Compiler (`atomic_causal_compiler.py`) with 5-part claim-checked semantic verification, V01–V22 biomechanical & kinetic-chain validator, closed-loop render verdict ingestion, RFC 6902 localized beat repair, and `block_bridge.py` (which compiles planned BLOCK v1 and simulated BLOCK v2 fights into Movement_Prose prompt pipelines).
4. **Protected Original `05:34` (`e91c686`) Single-Layer Path (`scripts/sakuga_compiler.py`, `scripts/sakuga_original_kb.py`, `templates/sakuga_mllm_3_1_causal_0534_template.json`):** Cryptographically SHA256-locked (`fdf54e55...`) original `SAKUGA-MLLM-3.1-CAUSAL` single-layer compiler and 17-Rule physics linter with its own dedicated pre-intent Knowledge Base path.
5. **In-Repository Knowledge Base & Graphify Knowledge Graph (`knowledge_base/`, `graphify-out/`):** Frozen 64-row `ai_video_compiler.db` (`semantic_directives`), growing `agent_memory.db` (tags, judged labels, causal triples, module relations, usage events), FTS5 `handbook_index.db` (auto-extracted from `handbook_index.db.gz`), and persistent `graphify-out/` AST + semantic knowledge graph (`graph.json`, `GRAPH_REPORT.md`, `graph.html`).

---

## Single Acceptance Command & Setup

From the repository root, use Python 3.9 or later (with `jsonschema==4.25.1` and `pytest==8.4.2` pinned in `requirements.txt`):

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/regress.py
```

Or invoke directly via `.venv/bin/python` without activating the virtual environment:

```sh
.venv/bin/python scripts/regress.py
```

The single acceptance command (`python scripts/regress.py`) runs from the destination root, audits all BLOCK knowledge and schemas (`scripts/audit_coverage.py`), verifies backfill dry-run/apply/verify idempotence (`scripts/backfill.py`), executes all **117 automated tests** (`58` original BLOCK tests + `59` Movement_Prose, Simulator v2, and Atomic Compiler unit and integration tests via `pytest -q`), runs the 25-check Knowledge Base verification (`kb-verify`) and `05:34` (`e91c686`) SHA256 lock check, and generates both 60-second `seed=42` fight demonstrations (`maleek` vs `donnell` and `wrestler` vs `donnell`) across both BLOCK and Movement_Prose outputs. Actual stdout, stderr, and exit codes are written to [`reports/execution_evidence.json`](reports/execution_evidence.json).

---

## Repository Structure & File Ownership

```text
Movement_Prose/
├── AGENTS.md                                                   # 👈 Deterministic Agent Onboarding, Directory Map, BLOCK & 25-Decision Index
├── README.md                                                   # Unified Setup, Architecture, BLOCK v1/v2 Model & CLI Reference
├── SKILL.md                                                    # Antigravity Skill instructions & YouTube Episode workflow
├── pyproject.toml / requirements.txt                           # Python package metadata (`engine`, `fight_move_system`, `scripts`) & pinned deps
├── simulate_fight.py                                           # 🥋 BLOCK v2 CLI: Standalone archetype fight simulator, Monte Carlo, prompts & audits
├── predict.py                                                  # 🥋 BLOCK v1 CLI: Deterministic, uncalibrated matchup probability prediction
├── plan_fight.py                                               # 🥋 BLOCK v1 CLI: Seeded/director-controlled fight planning, shotlist, prompts & `--movement-prose` bridge
├── cards/                                                      # 🥋 11 Canonical `block-1` Fighter Cards + `cards/v2/` (12 `block-2` Archetypes incl. `sanda_judo`)
├── data/                                                       # 📊 Authoritative BLOCK v1 & v2 Canon & Provenance Registries
│   ├── engine_index.json                                       # All 7 dimensions and 57 authored option interpretations
│   ├── option_behaviors.json / model_v2.json                   # v2 57-option attack/defense mechanical profiles, diminishing returns & posture math
│   ├── techniques_v2.json / positions.json                     # v2 38 frame-costed techniques (with kick anatomy) & 15-node grappling position map
│   ├── matchups.json / model.json                              # All 511 canonical matchup cells, weights, rulesets, staging distances & logistic formula
│   ├── counter_graph.json / debt_registry.json                 # Conditional counter mechanisms (168 edges) and operational debts (114 debts)
│   ├── techniques.json / combinations.json                     # 44 defined v1 motions, prerequisites, and possible transitions
│   ├── pipeline.json                                           # Event-type state, choreography, and prompt handler registry
│   └── sources.json / claims.json                              # 15 accessed primary sources and 15 narrowly scoped verified claims
├── schemas/                                                    # 📐 Versioned JSON Schemas (6 v1 schemas + 9 `*_v2.schema.json` contracts + Sakuga schemas)
├── engine/                                                     # ⚙️ BLOCK Fight Engine Core Modules (v1 & v2)
│   ├── simulator_v2.py                                         # v2 Exchange Simulator: posture, 8-lane diminishing-returns readiness, kicking, grappling & audits
│   ├── ontology.py / audit.py                                  # Knowledge loader, JSON Schema validator, SHA256 fingerprinting & 511-cell coverage audit
│   ├── capabilities.py / matchups.py / probability.py          # Gated capabilities, directional cell evaluation, slots, reachable NULLs & logistic probability
│   ├── fight_director.py / fight_state.py / event_graph.py     # 10-phase tactical planner, semantic state reducer & causal replay validator
│   └── choreography.py / prompt_compiler.py                    # 6-phase biomechanical movement expansion, camera shotlist & model-agnostic prose compiler
├── resources/
│   └── recovery.json                                           # Frozen BLOCK recovery release with content digests (targets only BLOCK-owned content)
├── reports/                                                    # BLOCK audit, backfill, provenance, implementation decisions & `execution_evidence.json`
├── outputs/example_fights/                                     # Generated BLOCK + Movement_Prose fight packages (`maleek_vs_donnell`, `two_slot_upset`, `prediction.json`)
├── docs/
│   ├── BLOCK_SIMULATOR_V2_DESIGN_SPEC.md                       # Complete BLOCK Fight Simulator v2 Architecture, Math, 57-Option Split & Audit Spec
│   ├── ADR_CLAIM_CHECKED_RENDERER_AND_SEMANTIC_VERIFIER.md     # Claim-Checked Renderer & 10-Rule Semantic Verifier (`SEM-BUG-01..10`)
│   ├── model.md                                                # Exact BLOCK matchup calculation, logistic formula, state contract & research boundary
│   ├── llm_reasoning_guide.md                                  # Manual LLM retrieval/calculation sequence & worked trace tables
│   ├── FIGHT_MOVE_SYSTEM_PLAN.md                               # v2 Fight Move System Architecture (Move Lexicon, State Machine, Dyad Coupling, Wording Compiler)
│   ├── TWO_LAYER_FLUID_STACK_ARCHITECTURE.md                   # Mode 1 (Single-Layer) vs Mode 2 (2-Layer Fluid Stack) Architecture
│   └── VARIATIONS_AND_FIGHTING_STYLES.md                       # Decisions 21-25, Entity Fighting Styles & Variations vs Golden Baseline
├── scripts/
│   ├── build_v2_data.py                                        # Deterministic generator for `data/option_behaviors.json`, `model_v2.json`, `techniques_v2.json`, `cards/v2/`
│   ├── audit_coverage.py / validate_data.py                    # Independent BLOCK ontology, matrix, card, handler & provenance coverage audit
│   ├── backfill.py                                             # Deterministic, idempotent BLOCK missing-record recovery & conflict reporter
│   ├── regress.py                                              # Single end-to-end acceptance workflow runner (`reports/execution_evidence.json`)
│   ├── sakuga_compiler.py                                      # 🔒 Original 05:34 (e91c686) Deterministic CLI Compiler & 17-Rule Physics Linter (SHA256 Locked)
│   ├── sakuga_original_kb.py                                   # 🔒 Dedicated 05:34 SAKUGA-MLLM-3.1-CAUSAL + Pre-Intent Knowledge Base Compiler Path
│   └── twelvelabs_bridge.py                                    # TwelveLabs Pegasus 1.2 Bridge (Mode A: Reference Extractor, Mode B: Render QA & Handoff)
├── templates/
│   └── sakuga_mllm_3_1_causal_0534_template.json               # 🔒 Canonical Protected 05:34 (e91c686) Single-Layer SAKUGA-MLLM-3.1-CAUSAL Template
├── knowledge_base/                                             # 📚 In-Repo Knowledge Base (`ai_video_compiler.db`, `agent_memory.db`, `agent/`, `runs/`)
├── fight_move_system/                                          # 🚀 v2 Fight Move System + Atomic Compiler + KB Bridge + BLOCK Bridge + Closed-Loop Repair
│   ├── cli.py                                                  # Unified CLI (`validate`, `compile`, `compile-original`, `block-predict`, `block-plan`, `kb-*`, `repair`, `next-clip`)
│   ├── atomic_causal_compiler.py                               # 1-Contact-Per-Beat (`Prep -> Commit -> Contact -> Consequence -> Recovery`) Compiler & Semantic Verifier
│   ├── block_bridge.py                                         # Bridges BLOCK v1 `fight_plan.json` & v2 `simulation_result_v2` into Movement_Prose & Atomic prompts
│   ├── original_causal_compiler.py                             # 🔒 Protected 05:34 `SAKUGA-MLLM-3.1-CAUSAL` Single-Layer Compiler + Pre-Intent KB Bridge
│   ├── compiler.py                                             # 2-Layer Fluid Stack (`sakuga_Xperiment` / `lean`) Compiler (queries KB prior to semantic intent)
│   ├── kb_bridge.py / closed_loop.py                           # Pre-intent KB query engine, verdict ingestion & RFC 6902 localized beat repair
│   └── scene_graph_linter.py / validator.py                    # 25-Decision Scene Graph Linter & V01-V22 Biomechanical Validator
├── graphify-out/                                               # 🕸️ Graphify Persistent Knowledge Graph (`graph.json`, `GRAPH_REPORT.md`, `graph.html`)
├── examples/                                                   # ✅ Canonical Golden Baseline Prompts (`gold_master_1..4`) & `variations/variation_1..3`
└── tests/                                                      # 🧪 117 Automated Tests (58 original BLOCK tests + 59 Movement_Prose, Simulator v2 & Atomic Compiler tests)
```

| Location | Ownership & Purpose |
|---|---|
| `data/engine_index.json` | All seven BLOCK dimensions (`hands`, `defense`, `stance`, `tie`, `target`, `kicking`, `mentality`) and 57 authored option interpretations |
| `data/matchups.json` | All 511 canonical cells and their derivations |
| `data/model.json` | Weights, adaptation policy, rulesets, staging distances, and logistic formula |
| `data/counter_graph.json`, `data/debt_registry.json` | Conditional counter mechanisms and operational debts |
| `data/techniques.json`, `data/combinations.json` | Defined motions, prerequisites, and possible transitions |
| `data/sources.json`, `data/claims.json` | Accessed primary sources and narrowly scoped `[VERIFIED]` claims |
| `cards/`, `schemas/` | Fighter identities and versioned JSON Schema validation contracts |
| `engine/probability.py`, `engine/matchups.py`, `engine/capabilities.py` | Probability calculation, directional cells, slots, NULL penalties, and reachability |
| `engine/fight_director.py`, `engine/fight_state.py`, `engine/event_graph.py` | Tactical phases, semantic reducer, and causal replay validation |
| `engine/choreography.py`, `engine/prompt_compiler.py` | Six-phase movement expansion, camera shots, and model-agnostic prose compilation |
| `fight_move_system/block_bridge.py`, `fight_move_system/atomic_causal_compiler.py` | Executable bridge translating BLOCK v1 fight plans & v2 exchange logs into `sakuga_Xperiment` 2-Layer Fluid Stack, protected `05:34` `SAKUGA-MLLM-3.1-CAUSAL`, and Atomic 1-Contact-Per-Beat prompts |
| `simulate_fight.py`, `engine/simulator_v2.py`, `scripts/build_v2_data.py` | BLOCK Fight Simulator v2: 12 `block-2` archetypes (`cards/v2/*.json`), 57 mechanical option behaviors (`data/option_behaviors.json`), smooth diminishing-returns readiness (`data/model_v2.json`), 200-seed Round-Robin balance audit, and 57-option viability audit |
| `scripts/backfill.py`, `engine/audit.py`, `resources/recovery.json` | BLOCK-scoped missing-record recovery, conflict reporting, and independent coverage checks |
| `docs/BLOCK_SIMULATOR_V2_DESIGN_SPEC.md`, `docs/model.md`, `docs/llm_reasoning_guide.md` | Complete BLOCK v2 & v1 model semantics, option math, and step-by-step LLM calculation/retrieval instructions |

JSON under `data/` and `cards/` is authoritative for BLOCK. Generated fights embed their original cards, model version, and knowledge SHA256 digest. The frozen recovery release (`resources/recovery.json`) targets only BLOCK-owned content: it restores missing known BLOCK fields/files, preserves competing live values and reports them as conflicts, never converts an unverifiable claim into verified research, and never touches or overwrites unrelated repository files.

---

## BLOCK Fight Engine: Model Meaning, Fidelity & Demonstrations

> **Full Model Specification & Manual LLM Guide:** See [`docs/model.md`](docs/model.md) and [`docs/llm_reasoning_guide.md`](docs/llm_reasoning_guide.md).

### What the BLOCK Model Means
- **Conditional Lanes, Not Power Levels:** Every advantage has a reachable liability. Scores compare specific conditional lanes (`answers` vs `exposes`), never overall martial-art power.
- **Dimensions vs. Synchronized Slots:** Dimension choices (`hands`, `defense`, `stance`, `tie`, `target`, `kicking`, `mentality`) describe how a fighter behaves; synchronized slots (`1 = Brawler`, `2 = Two-piece`, `3 = Triad`, `4 = Anomaly`) are trained bundles that coordinate actions (`0.15` logit per net slot difference).
- **Reachable NULL Ties vs. Gated Capabilities:** A `null` tie means missing offensive attachment training (`0.20` logit penalty per missing dimension when the opponent has a legal, trained, reachable entry). Trained anti-grappling is a separate capability. Maleek (`cards/maleek.json`) begins with `tie: null`; his pretrained `maleek.cage_plum` is gated until three runtime conditions are simultaneously satisfied (`in_clinch_range`, `against_cage`, `forearm_frame_established`). The state reducer rejects activation before those gates are met.
- **Provenance Boundary (`[VERIFIED]` vs. `[CANON]`):** Verified claims are strictly restricted to [`data/claims.json`](data/claims.json) and resolved against [`data/sources.json`](data/sources.json). Numerical edges, ratings, weights, tactical implications, fictional identities, 52-Dutch, and Uno are `[CANON]`. Primary sources establish mechanics or cultural context, never win percentages.

### Fidelity and Limits
- **Semantic Motion Validation vs. Physics Simulation:** The BLOCK event ledger enforces trained techniques, setups, contact causality, adjacent ranges, earned grips, and persistent consequences. Choreography uses meters, anatomical limb names (`left`/`right` resolved from live stance orientation), and a fixed camera side. It is semantically validated staging—no skeleton, IK/FK solver, collision engine, or empirical biomechanical calibration dataset exists in this repository.
- **Condensed CANON Exhibition:** Short fights (30–60s) are condensed `[CANON]` exhibitions whose decisions follow contact and control marks demonstrated along the sampled or director-selected path; these marks are narrative accounting units, not medical injury estimates or official commission judging.
- **Director-Controlled Mode (`--winner`):** Passing `--winner <fighter_id>` explicitly labels `selection.mode = "director-controlled"` and dramatizes a conditional path for that winner while preserving `selection.original_probabilities` unchanged.
- **Fairness Admission & Consumer-Boundary Enforcement (`F-001`, `F-002`, `F-003`):**
  - `F-001` (Duplicate Slot Claims): `Knowledge.card` and `capabilities.admitted_slots` enforce distinct semantic coordination signatures `(frozenset(capabilities), tuple(coordination_sequence))` per slot; copied capability bundles under new IDs/descriptions are rejected at admission and earn zero duplicate `0.15` logit credit.
  - `F-002` (Unsupported Style Selection): `Knowledge.card` and `capabilities.resolved_dimensions` bind every selected option in `dimensions` to actual trained capabilities and active techniques; unsupported labels (such as setting `tie: "tie.anti_grappling"` on an untrained tie card) are rejected at admission and resolve to `None` in `null_seams` and `matchups.evaluate`.
  - `F-003` (Conditional Narrative vs. Empirical Ranking Boundary): `capabilities.admit_ranked_result` rejects narrative fight plans, sampled seed draws, director-controlled outcomes, and contact/control mark tallies from being ingested as empirical ranked results.
  - Run `.venv/bin/python scripts/verify_findings.py --root . --output-dir reports/fairness_after_repair` (and `tests/test_fairness_plan.py`) to verify all admission, NULL truth-table ($2^4=16$), 220-pair symmetry, state-sequence, and mutation-probe checks.

### BLOCK Simulator v2 CLI (`simulate_fight.py`) — Archetype Simulations, Prompts & Audits

```sh
# 1. List all 12 predefined block-2 fighter archetypes (human-readable or --json)
.venv/bin/python simulate_fight.py --list-archetypes
.venv/bin/python simulate_fight.py --list-archetypes --json

# 2. Simulate a single deterministic fight with play-by-play exchange breakdown + 1-Contact-Per-Beat causal prompt
.venv/bin/python simulate_fight.py sanda_judo thai --seed 7 --arena cage --emit-prompt

# 3. Run a Monte Carlo multi-run series (with optional Director Mode --winner)
.venv/bin/python simulate_fight.py street thai --runs 200
.venv/bin/python simulate_fight.py wrestler thai --runs 50 --winner wrestler --json

# 4. Run the 12-Archetype 200-Seed Round-Robin Balance Audit (verifies order invariance & [35%, 65%] target band)
.venv/bin/python simulate_fight.py --balance-audit --runs 200

# 5. Run the 57-Option Coverage & Single-Option Perturbation Viability Audit
.venv/bin/python simulate_fight.py --option-audit --runs 20
```

### BLOCK v1 CLI Commands & Seed-42 Demonstrations (`predict.py` & `plan_fight.py`)

```sh
# 1. Coverage Audit & Deterministic Backfill
.venv/bin/python scripts/audit_coverage.py
.venv/bin/python scripts/backfill.py --dry-run
.venv/bin/python scripts/backfill.py --apply
.venv/bin/python scripts/backfill.py --verify

# 2. Deterministic Uncalibrated Matchup Prediction
.venv/bin/python predict.py cards/maleek.json cards/donnell.json --ruleset mma --output outputs/example_fights/prediction.json

# 3. Demonstration 1: Maleek vs Donnell (60s, seed=42, MMA) + Movement_Prose Bridge
.venv/bin/python plan_fight.py cards/maleek.json cards/donnell.json --ruleset mma --duration 60 --seed 42 --output-dir outputs/example_fights/maleek_vs_donnell --movement-prose

# 4. Demonstration 2: Imani Vale (2-slot wrestler) vs Donnell (3-slot, NULL tie) — Reachable NULL-Tie Exploit
.venv/bin/python plan_fight.py cards/wrestler.json cards/donnell.json --ruleset mma --duration 60 --seed 42 --output-dir outputs/example_fights/two_slot_upset --movement-prose

# 5. Director-Controlled Mode (preserves original prediction; dramatizes selected winner)
.venv/bin/python plan_fight.py cards/maleek.json cards/donnell.json --ruleset mma --duration 60 --seed 42 --winner donnell --output-dir outputs/example_fights/maleek_vs_donnell_director

# 6. Equivalent Entry via Unified Fight Move System CLI
.venv/bin/python -m fight_move_system.cli block-predict cards/maleek.json cards/donnell.json --ruleset mma
.venv/bin/python -m fight_move_system.cli block-plan cards/maleek.json cards/donnell.json --ruleset mma --duration 60 --seed 42 --output-dir outputs/example_fights/maleek_vs_donnell
```

---

## Sakuga Prompt Architecture: Single-Layer `05:34` (`SAKUGA-MLLM-3.1-CAUSAL`) vs. 2-Layer Unrolled Fluid Stack (`sakuga_Xperiment`)

> **Full Deep-Dive Documentation:** See [`AGENTS.md`](AGENTS.md), [`docs/TWO_LAYER_FLUID_STACK_ARCHITECTURE.md`](docs/TWO_LAYER_FLUID_STACK_ARCHITECTURE.md), and [`docs/VARIATIONS_AND_FIGHTING_STYLES.md`](docs/VARIATIONS_AND_FIGHTING_STYLES.md).

| Feature | Protected `05:34` Single-Layer (`SAKUGA-MLLM-3.1-CAUSAL`) | 2-Layer Unrolled Fluid Stack (`sakuga_Xperiment` / `--stack`) | BLOCK Native Shot Compiler (`model-agnostic-prose`) |
| :--- | :--- | :--- | :--- |
| **Entrypoints** | `scripts/sakuga_compiler.py`<br>`scripts/sakuga_original_kb.py`<br>`fight_move_system.cli compile-original` | `fight_move_system.cli compile`<br>`scripts/sakuga_compiler.py compile --stack` | `plan_fight.py`<br>`fight_move_system.cli block-plan` |
| **Canonical Examples** | `templates/sakuga_mllm_3_1_causal_0534_template.json`<br>`examples/gold_master_1_blade_exchange.json`<br>`examples/gold_master_2_disarm_dual_blade.json` | `examples/gold_master_3_courtyard_sky_cartwheel.json`<br>`examples/gold_master_4_shrine_bo_staff_determinism_test.json`<br>`examples/variations/variation_1..3` | `outputs/example_fights/maleek_vs_donnell/`<br>`outputs/example_fights/two_slot_upset/` |
| **Prompt Structure** | `Header` + `1-Line-Per-Beat SAKUGA-MLLM-3.1-CAUSAL JSON` | `Header` + `LAYER 1 (Labanotation-as-Words Timeline)` + `LAYER 2 (Kinematic & Camera Scene Graph JSON)` | `shotlist.json` + `video_prompts.jsonl` (per-shot self-contained staging prose) |
| **Key Invariants** | 11-key `A_beats`, 8-key `B_track`, zero `sakuga_Xperiment` keys (`weight_split`, `com_position`, `easing_curve`, `impulse_tier`), 17-Rule physics linter | 4-Phase sub-beat unrolling (`Entry -> Drive -> Contact -> Recovery`), bilateral two-arm silhouette lock, V01–V22 validator | 6-phase movement expansion (`preparation -> initiation -> execution -> contact -> reaction -> recovery`), causal event IDs |

### Quick Start: Sakuga & Fight Move System Commands

```sh
# 1. Protected Original 05:34 (e91c686) SAKUGA-MLLM-3.1-CAUSAL Single-Layer Path + Pre-Intent KB Query
.venv/bin/python scripts/sakuga_original_kb.py verify-protection
.venv/bin/python scripts/sakuga_original_kb.py compile-spec templates/sakuga_mllm_3_1_causal_0534_template.json --taste clean
.venv/bin/python scripts/sakuga_original_kb.py compile-beatsheet fight_move_system/fixtures/pass/10_beat_boxing_exchange.json --taste nakamura
.venv/bin/python -m fight_move_system.cli compile-original templates/sakuga_mllm_3_1_causal_0534_template.json --taste clean

# 2. Fight Move System v2 (2-Layer Fluid Stack `sakuga_Xperiment` & Pre-Intent KB Query)
.venv/bin/python -m fight_move_system.cli validate fight_move_system/fixtures/pass/variation_3_eight_limbs_muay_thai_mma_war_sheet.json
.venv/bin/python -m fight_move_system.cli compile fight_move_system/fixtures/pass/variation_3_eight_limbs_muay_thai_mma_war_sheet.json --mode xperiment --schema sakuga_Xperiment
.venv/bin/python -m fight_move_system.cli kb-verify
.venv/bin/python -m fight_move_system.cli kb-ask fight_move_system/fixtures/pass/variation_3_eight_limbs_muay_thai_mma_war_sheet.json --taste "heavy, brutal, old school" --follow 2 --discover 2

# 3. Closed-Loop Verdict Ingestion, Localized RFC 6902 Beat Repair, and Clip N+1 Handoff
.venv/bin/python -m fight_move_system.cli ingest-verdict --run-id run_001 --move-id low_calf_kick --status works
.venv/bin/python -m fight_move_system.cli repair fight_move_system/fixtures/pass/variation_3_eight_limbs_muay_thai_mma_war_sheet.json --beat 2 --failure contact_flicker
.venv/bin/python -m fight_move_system.cli next-clip fight_move_system/fixtures/pass/variation_3_eight_limbs_muay_thai_mma_war_sheet.json
```

---

## Cross-Platform Usage (macOS / Mac Studio, Windows, & Linux)

All tools in this repository use Python 3.9+ (`pathlib.Path`, `sqlite3`, `json`, `hashlib`, `jsonschema`, `pytest`, `unittest`) with **zero OS-specific hardcoded paths** and run independently of the current working directory:
- **macOS (Mac Studio) & Linux (`zsh` / `bash`):**
  ```sh
  .venv/bin/python scripts/regress.py
  ```
- **Windows (`PowerShell` / `CMD`):**
  ```powershell
  .venv\Scripts\python.exe scripts\regress.py
  ```
- **Knowledge Base Index (`knowledge_base/handbook_index.db.gz`):**
  - `knowledge_base/ai_video_compiler.db`, `knowledge_base/agent_memory.db`, and the compressed FTS5 index `knowledge_base/handbook_index.db.gz` (`9.8 MB`) all ship directly in Git. On a fresh clone, [`fight_move_system/kb_bridge.py`](fight_move_system/kb_bridge.py) and [`knowledge_base/agent/__init__.py`](knowledge_base/agent/__init__.py) automatically extract `knowledge_base/handbook_index.db` on first run with zero manual steps required.
