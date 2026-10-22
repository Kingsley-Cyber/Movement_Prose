# Movement_Prose (`SAKUGA-MLLM-3.1-CAUSAL`, 2-Layer Fluid Stack & BLOCK Fight Engine)

**Movement_Prose** (`movement-prose-e2e` / `sakuga-fight-director`) is an integrated, offline-first combat reasoning, semantic fight direction, and biomechanical Sakuga prompt compilation system combining:
1. **BLOCK Fight Engine (`engine/`, `cards/`, `data/`, `schemas/`, `predict.py`, `plan_fight.py`):** Loads fictional fighter cards, calculates deterministic uncalibrated matchup probabilities across 7 dimensions and 511 canonical cells, constructs seeded or director-controlled causal fight event graphs, and compiles traceable model-agnostic cinematic shotlists and prompts (`shotlist.json`, `video_prompts.jsonl`).
2. **Fight Move System v2 (`fight_move_system/`):** Deterministic 2-Layer Unrolled Fluid Stack (`sakuga_Xperiment` & `lean`) compiler, V01–V22 biomechanical & kinetic-chain validator, closed-loop render verdict ingestion, RFC 6902 localized beat repair, and `block_bridge.py` (which compiles planned BLOCK fights into both Movement_Prose prompt pipelines).
3. **Protected Original `05:34` (`e91c686`) Single-Layer Path (`scripts/sakuga_compiler.py`, `scripts/sakuga_original_kb.py`, `templates/sakuga_mllm_3_1_causal_0534_template.json`):** Cryptographically SHA256-locked (`fdf54e55...`) original `SAKUGA-MLLM-3.1-CAUSAL` single-layer compiler and 17-Rule physics linter with its own dedicated pre-intent Knowledge Base path.
4. **In-Repository Knowledge Base (`knowledge_base/`):** Frozen 64-row `ai_video_compiler.db` (`semantic_directives`), growing `agent_memory.db` (tags, judged labels, causal triples, module relations, usage events), and FTS5 `handbook_index.db` queried prior to semantic intent decomposition.

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

The single acceptance command (`python scripts/regress.py`) runs from the destination root, audits all BLOCK knowledge and schemas (`scripts/audit_coverage.py`), verifies backfill dry-run/apply/verify idempotence (`scripts/backfill.py`), executes all 98 tests (`58` original BLOCK tests + `40` Movement_Prose unit and integration tests via `pytest -q`), runs the 25-check Knowledge Base verification (`kb-verify`) and `05:34` (`e91c686`) SHA256 lock check, and generates both 60-second `seed=42` fight demonstrations (`maleek` vs `donnell` and `wrestler` vs `donnell`) across both BLOCK and Movement_Prose outputs. Actual stdout, stderr, and exit codes are written to [`reports/execution_evidence.json`](reports/execution_evidence.json).

---

## Repository Structure & File Ownership

```text
Movement_Prose/
├── AGENTS.md                                                   # 👈 Deterministic Agent Onboarding, Directory Map, BLOCK & 25-Decision Index
├── README.md                                                   # Unified Setup, Architecture, BLOCK Model & CLI Reference
├── SKILL.md                                                    # Antigravity Skill instructions & YouTube Episode workflow
├── pyproject.toml / requirements.txt                           # Python package metadata (`engine`, `fight_move_system`, `scripts`) & pinned deps
├── predict.py                                                  # BLOCK CLI: Deterministic, uncalibrated matchup probability prediction
├── plan_fight.py                                               # BLOCK CLI: Seeded/director-controlled fight planning, shotlist, prompts & `--movement-prose` bridge
├── cards/                                                      # 🥋 11 BLOCK Fighter Identity Cards (`maleek`, `donnell`, `wrestler`, `macklin`, `detroit`, `philly`, `thai`, `karate`, `greco`, `jiujitsu`, `street`)
├── data/                                                       # 📊 Authoritative BLOCK Canon & Provenance Registries
│   ├── engine_index.json                                       # All 7 dimensions and 57 authored option interpretations
│   ├── matchups.json                                           # All 511 canonical matchup cells and derivations
│   ├── model.json                                              # Weights, adaptation policy, rulesets, staging distances, and logistic formula
│   ├── counter_graph.json / debt_registry.json                 # Conditional counter mechanisms (168 edges) and operational debts (114 debts)
│   ├── techniques.json / combinations.json                     # 44 defined motions, prerequisites, and possible transitions
│   ├── pipeline.json                                           # Event-type state, choreography, and prompt handler registry
│   └── sources.json / claims.json                              # 15 accessed primary sources and 15 narrowly scoped verified claims
├── schemas/                                                    # 📐 Versioned JSON Schemas (`fighter_card`, `fight_plan`, `fight_state`, `event`, `event_graph`, `shot`)
├── engine/                                                     # ⚙️ BLOCK Fight Engine Core Modules
│   ├── ontology.py / audit.py                                  # Knowledge loader, JSON Schema validator, SHA256 fingerprinting & 511-cell coverage audit
│   ├── capabilities.py / matchups.py / probability.py          # Gated capabilities, directional cell evaluation, slots, reachable NULLs & logistic probability
│   ├── fight_director.py / fight_state.py / event_graph.py     # 10-phase tactical planner, semantic state reducer & causal replay validator
│   └── choreography.py / prompt_compiler.py                    # 6-phase biomechanical movement expansion, camera shotlist & model-agnostic prose compiler
├── resources/
│   └── recovery.json                                           # Frozen BLOCK recovery release with content digests (targets only BLOCK-owned content)
├── reports/                                                    # BLOCK audit, backfill, provenance, implementation decisions & `execution_evidence.json`
├── outputs/example_fights/                                     # Generated BLOCK + Movement_Prose fight packages (`maleek_vs_donnell`, `two_slot_upset`, `prediction.json`)
├── docs/
│   ├── model.md                                                # Exact BLOCK matchup calculation, logistic formula, state contract & research boundary
│   ├── llm_reasoning_guide.md                                  # Manual LLM retrieval/calculation sequence & worked trace tables
│   ├── FIGHT_MOVE_SYSTEM_PLAN.md                               # v2 Fight Move System Architecture (Move Lexicon, State Machine, Dyad Coupling, Wording Compiler)
│   ├── TWO_LAYER_FLUID_STACK_ARCHITECTURE.md                   # Mode 1 (Single-Layer) vs Mode 2 (2-Layer Fluid Stack) Architecture
│   └── VARIATIONS_AND_FIGHTING_STYLES.md                       # Decisions 21-25, Entity Fighting Styles & Variations vs Golden Baseline
├── scripts/
│   ├── audit_coverage.py / validate_data.py                    # Independent BLOCK ontology, matrix, card, handler & provenance coverage audit
│   ├── backfill.py                                             # Deterministic, idempotent BLOCK missing-record recovery & conflict reporter
│   ├── regress.py                                              # Single end-to-end acceptance workflow runner (`reports/execution_evidence.json`)
│   ├── sakuga_compiler.py                                      # 🔒 Original 05:34 (e91c686) Deterministic CLI Compiler & 17-Rule Physics Linter (SHA256 Locked)
│   ├── sakuga_original_kb.py                                   # 🔒 Dedicated 05:34 SAKUGA-MLLM-3.1-CAUSAL + Pre-Intent Knowledge Base Compiler Path
│   └── twelvelabs_bridge.py                                    # TwelveLabs Pegasus 1.2 Bridge (Mode A: Reference Extractor, Mode B: Render QA & Handoff)
├── templates/
│   └── sakuga_mllm_3_1_causal_0534_template.json               # 🔒 Canonical Protected 05:34 (e91c686) Single-Layer SAKUGA-MLLM-3.1-CAUSAL Template
├── knowledge_base/                                             # 📚 In-Repo Knowledge Base (`ai_video_compiler.db`, `agent_memory.db`, `agent/`, `runs/`)
├── fight_move_system/                                          # 🚀 v2 Fight Move System + KB Bridge + BLOCK Bridge + Closed-Loop Repair
│   ├── cli.py                                                  # Unified CLI (`validate`, `compile`, `compile-original`, `block-predict`, `block-plan`, `kb-*`, `repair`, `next-clip`)
│   ├── block_bridge.py                                         # Bridges BLOCK `fight_plan.json` into both Movement_Prose 2-Layer Fluid Stack & 05:34 Causal prompts
│   ├── original_causal_compiler.py                             # 🔒 Protected 05:34 `SAKUGA-MLLM-3.1-CAUSAL` Single-Layer Compiler + Pre-Intent KB Bridge
│   ├── compiler.py                                             # 2-Layer Fluid Stack (`sakuga_Xperiment` / `lean`) Compiler (queries KB prior to semantic intent)
│   ├── kb_bridge.py / closed_loop.py                           # Pre-intent KB query engine, verdict ingestion & RFC 6902 localized beat repair
│   └── scene_graph_linter.py / validator.py                    # 25-Decision Scene Graph Linter & V01-V22 Biomechanical Validator
├── examples/                                                   # ✅ Canonical Golden Baseline Prompts (`gold_master_1..4`) & `variations/variation_1..3`
└── tests/                                                      # 🧪 98 Automated Tests (`test_ontology`, `test_matchups`, `test_slots`, `test_prediction`, `test_fight_plan`, `test_event_graph`, `test_end_to_end`, `test_backfill`, `test_fight_move_system`)
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
| `fight_move_system/block_bridge.py` | Executable bridge translating BLOCK fight plans into `sakuga_Xperiment` 2-Layer Fluid Stack and protected `05:34` `SAKUGA-MLLM-3.1-CAUSAL` prompts |
| `scripts/backfill.py`, `engine/audit.py`, `resources/recovery.json` | BLOCK-scoped missing-record recovery, conflict reporting, and independent coverage checks |
| `docs/model.md`, `docs/llm_reasoning_guide.md` | Exact BLOCK model semantics and step-by-step LLM calculation/retrieval instructions |

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

### BLOCK CLI Commands & Seed-42 Demonstrations

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
- **Knowledge Base Index (`knowledge_base/handbook_index.db`):**
  - `knowledge_base/ai_video_compiler.db` and `knowledge_base/agent_memory.db` ship in Git. Because `handbook_index.db` (~131 MB) exceeds GitHub's 100 MB file limit, on a fresh clone either copy `handbook_index.db` into `knowledge_base/` or build it locally in ~13s via `cd knowledge_base && python3 -m agent index-handbook /path/to/handbook.html`.
