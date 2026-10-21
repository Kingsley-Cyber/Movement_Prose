# Movement_Prose (`SAKUGA-MLLM-3.1-CAUSAL` & 2-Layer Unrolled Fluid Stack)

**Movement_Prose** (`sakuga-fight-director`) is an empirically verified **Causal Physics & Biomechanical Choreography Architecture (`SAKUGA-MLLM-3.1-CAUSAL`)**, deterministic Python compiler/linter, and TwelveLabs video-understanding bridge for generating 2D hand-drawn Sakuga martial-arts animations on **Seedance 2.0 Mini, Seedance 2.5, and Kling**.

---

## Repository Structure

```text
Movement_Prose/
├── AGENTS.md                                                   # 👈 Deterministic Agent Onboarding, Directory Map & 25-Decision Index
├── SKILL.md                                                   # Antigravity Skill instructions & YouTube Episode workflow
├── docs/
│   ├── TWO_LAYER_FLUID_STACK_ARCHITECTURE.md                  # Deep-dive guide: Mode 1 vs Mode 2 (--stack) & Choreography Separation
│   └── VARIATIONS_AND_FIGHTING_STYLES.md                      # Deep-dive: Decisions 21-25, Entity Fighting Styles & Variations vs Golden Baseline
├── scripts/
│   ├── sakuga_compiler.py                                     # Deterministic CLI Compiler, 25-Rule Physics/Diversity/Style Linter, --stack Generator & Stitcher
│   └── twelvelabs_bridge.py                                   # TwelveLabs Pegasus 1.2 Bridge (Mode A: Reference Extractor, Mode B: Render QA & Handoff)
├── examples/                                                  # ✅ ORIGINAL CANONICAL GOLDEN BASELINE PROMPTS (gold_master_1..4)
│   ├── gold_master_1_blade_exchange.json                      # Gold-Master #1: Single-Layer JSON (Reverse-Grip Kunai vs. Forearm Blade Exchange)
│   ├── gold_master_2_disarm_dual_blade.json                   # Gold-Master #2: Single-Layer JSON (Wakizashi vs. Katana Disarm, Aerial Catch & X-Lock)
│   ├── gold_master_3_courtyard_sky_cartwheel.json             # Gold-Master #3: 2-Layer Fluid Stack Source (Sky-Cartwheel, Uppercut, Wall-Run & Dive)
│   ├── gold_master_3_courtyard_fluid_stack.txt                # Gold-Master #3: Compiled 2-Layer Unrolled Fluid Stack Prompt (--stack)
│   ├── gold_master_4_shrine_bo_staff_determinism_test.json    # Gold-Master #4: 2-Layer Fluid Stack Source (Rain Shrine Bo-Staff vs. Iron Gauntlets)
│   ├── gold_master_4_shrine_bo_staff_fluid_stack.txt          # Gold-Master #4: Compiled 2-Layer Unrolled Fluid Stack Prompt (--stack)
│   └── variations/                                            # 🔥 COMBAT-STYLE & BIOMECHANICAL VARIATIONS (Distinct from Golden #1-#4)
│       ├── variation_1_baki_grounded_standup_war.json         # Variation #1 (style: grounded_striker_boxer_baki): 100% Grounded Baki Stand-Up War
│       ├── variation_1_baki_grounded_standup_war_fluid_stack.txt
│       ├── variation_2_multidomain_combative_showcase.json    # Variation #2 (style: acrobatic_multidomain_freestyle): 4-Domain Acrobatic Showcase
│       └── variation_2_multidomain_combative_showcase_fluid_stack.txt
├── references/
│   └── sakuga_prompt_schema_sop.md                            # Master SOP, Empirical Decisions & 2-Layer Fluid Stack Breakdown
└── _archive_rd_history_do_not_copy/                           # ⚠️ HISTORICAL R&D LOGS ONLY (Contains deprecated Euler/Quaternion/Bloat tests — do not copy)
    ├── RD_EXPERIMENT_PROGRESSION_LOG.md                       # Complete chronological log of all 15 A/B experiments & empirical render findings
    ├── exp01..exp15_*.txt                                     # All 15 prompt iterations tested across the R&D progression (v2.1 -> v3.1-CAUSAL + Fluid Stack)
    └── baselines/                                             # Raw input baselines (v2.0, LBN-2.3-ADV Euler, LBN-2.4-ADV Style Tags, Causal Notes)
```

---

## Architectural Breakdown: Single-Layer JSON vs. 2-Layer Unrolled Fluid Stack (`--stack`)

> **Full Deep-Dive Documentation:** See [`AGENTS.md`](AGENTS.md), [`docs/TWO_LAYER_FLUID_STACK_ARCHITECTURE.md`](docs/TWO_LAYER_FLUID_STACK_ARCHITECTURE.md), and [`docs/VARIATIONS_AND_FIGHTING_STYLES.md`](docs/VARIATIONS_AND_FIGHTING_STYLES.md) for the complete architectural specification, Entity Fighting Style profiles (`Decision 25`), and the strict separation between the **Original Canonical Golden Prompts (`examples/gold_master_1..4`)** and **Combat-Style Variations (`examples/variations/variation_1..2`)**.

To eliminate any confusion, **both modes use the exact same `SAKUGA-MLLM-3.1-CAUSAL` JSON source file and compiler (`scripts/sakuga_compiler.py`)**. The difference is whether you compile into a **Single-Layer JSON prompt** (default) or a **2-Layer Unrolled Fluid Stack prompt** (`--stack`):

| Feature | Mode 1: Single-Layer Causal JSON (`compile`) | Mode 2: 2-Layer Unrolled Fluid Stack (`compile --stack`) |
| :--- | :--- | :--- |
| **Canonical Golden Examples (`examples/`)** | `gold_master_1_blade_exchange.json`<br>`gold_master_2_disarm_dual_blade.json` | `gold_master_3_courtyard_sky_cartwheel.json` (4-Impact Acrobatic)<br>`gold_master_4_shrine_bo_staff_determinism_test.json` (Weapon Staff) |
| **Combat-Style Variations (`examples/variations/`)** | — | `variation_1_baki_grounded_standup_war.json` (`grounded_striker_boxer_baki`)<br>`variation_2_multidomain_combative_showcase.json` (`acrobatic_multidomain_freestyle`) |
| **Prompt Structure** | `Header` + `SAKUGA-MLLM-3.1-CAUSAL JSON` | `Header` + **`LAYER 1 (Labanotation-as-Words Timeline)`** + **`LAYER 2 (SAKUGA-MLLM-3.1-CAUSAL JSON)`** |
| **Sub-Beat Density** | **11–14 beats** (`~0.7s–0.9s` spacing) | **16–18 unrolled beats** (`~0.4s–0.6s` spacing; every move unrolled into 3–4 phases: `Entry/Windup -> Drive/Apex -> Contact -> Landing/Recovery`) |
| **Best Used For** | Grounded close-quarters blade/fist exchanges with simple support transitions. | **High-intensity multi-hit hand-to-hand wars, clinches, kick turnovers, OR complex acrobatic/vertical choreography.** |
| **Why It Works on Seedance 2.0 Mini** | Compact causal KV-cache (`A_beats -> B_track -> props -> camera -> anime -> rules`) locks hit timing without token bloat. | **Layer 1** feeds narrative/sequence attention heads an unbroken chronological chain (`SUPPORT | bilateral limbs | 5-phase force event | path`), while **Layer 2** locks exact 3D kinematics, camera cuts, and limb-isolated smears. |

### The 3 Laws of the 2-Layer Unrolled Fluid Stack (Decisions 18, 19, 20)

1. **Decision 18 — 4-Phase Sub-Beat Unrolling (`Entry/Windup -> Drive/Apex -> Contact -> Landing/Recovery`):**
   * On Seedance 2.0 Mini, why did the `3.05s` uppercut render unambiguously on the first try while complex moves had weird moments? Because the uppercut had **3 explicit sequential keyframes** (`2.20s` approach steps $\rightarrow$ `2.75s` deep hip-sink coil $\rightarrow$ `3.05s` vertical drive & chin impact), whereas complex acrobatic moves skipped intermediate states (e.g., jumping from a `4.3s` mid-air kick directly to a `5.5s` vertical wall-run without a `4.8s` floor landing).
   * **Rule:** Every complex rotation, vault, wall-run, or dive must be unrolled into **3–4 sequential keyframes** in both Layer 1 and Layer 2 (`0.9s` left-hand plant $\rightarrow$ `1.2s` both-hands inverted deflect $\rightarrow$ `1.6s` right-hand push-off $\rightarrow$ `2.2s` feet touchdown; `3.6s` $90^\circ$ rise $\rightarrow$ `4.0s` $180^\circ$ inverted apex $\rightarrow$ `4.3s` $270^\circ$ heel impact $\rightarrow$ `4.8s` floor landing).
2. **Decision 19 — Single-Source 2-Layer Synchronization & Zero `<verb>` Markup Pollution:**
   * **Layer 1** (`Labanotation-as-Words`) and **Layer 2** (`SAKUGA-MLLM-3.1-CAUSAL` JSON) are compiled from the **same JSON source** so timestamps, coordinates, and prop ownership never contradict each other.
   * **Never wrap verbs or motions in `<punch>` or `<impact>` XML/HTML tags**—angle brackets activate the LLM's markup/tag prior, turning active motion verbs into static labels.
3. **Decision 20 — Bilateral Two-Arm Silhouette Locking (The `:03` One-Arm Fix):**
   * **Root Cause:** During single-handed strike windups (such as the `2.75s–3.05s` rising left uppercut viewed over B's shoulder), if the prompt only describes the striking **LEFT fist** and gives the non-striking **RIGHT arm** a vague tag (`"R_arm:high guard"`), the model tucks or occludes the unmentioned right arm behind the dark coat torso—making the fighter look one-armed.
   * **Rule:** On every single beat, **both `L_arm` and `R_arm` must be explicitly placed in clear, non-occluded silhouette outside the torso** in Layer 1, `limbs`, and `pose` (e.g., at `2.75s`: *"R_arm extended forward toward B's chest with open right palm as a range-finding lead guard while L_arm is cocked low at the left hip with clenched left fist, keeping both left and right arms 100% visible outside the torso silhouette"*), reinforced by `"no missing arms, no one-armed fighter, both left and right arms and hands always visible"` in `"negative"`.

---

## Quick Start

### 1. Lint & Validate Fight Choreography Specs (Checks All 20 Decisions)
```bash
python3 scripts/sakuga_compiler.py lint examples/*.json
```

### 2. Compile in Mode 1 (Single-Layer JSON) or Mode 2 (2-Layer Fluid Stack `--stack`)
```bash
# Mode 1: Single-Layer Causal JSON (default):
python3 scripts/sakuga_compiler.py compile examples/gold_master_2_disarm_dual_blade.json --taste clean

# Mode 2: 2-Layer Unrolled Fluid Stack (--stack) for complex acrobatic/weapon choreography:
python3 scripts/sakuga_compiler.py compile examples/gold_master_3_courtyard_sky_cartwheel.json --stack --out examples/gold_master_3_courtyard_fluid_stack.txt
python3 scripts/sakuga_compiler.py compile examples/gold_master_4_shrine_bo_staff_determinism_test.json --stack --out examples/gold_master_4_shrine_bo_staff_fluid_stack.txt

# Optional Yutaka Nakamura taste layer or animation style presets (cel_default, genga, sumi_ink, trigger_neon, retro_90s, ufotable):
python3 scripts/sakuga_compiler.py compile examples/gold_master_3_courtyard_sky_cartwheel.json --stack --taste nakamura
python3 scripts/sakuga_compiler.py compile examples/gold_master_4_shrine_bo_staff_determinism_test.json --stack --style ufotable
```

### 3. Stitch Multiple 10s Clips Into a YouTube Episode Pack
```bash
python3 scripts/sakuga_compiler.py stitch examples/gold_master_3_courtyard_sky_cartwheel.json examples/gold_master_4_shrine_bo_staff_determinism_test.json --stack --out episode_pack.md
```

### 4. TwelveLabs Video Intelligence Bridge (3-Tier Extraction + Full Account CLI)
```bash
# Authenticate once (saves key to ~/.config/sakuga/twelvelabs.json) & inspect your TwelveLabs account/videos:
python3 scripts/twelvelabs_bridge.py auth --set-key "tlk_your_key_here"
python3 scripts/twelvelabs_bridge.py account
python3 scripts/twelvelabs_bridge.py videos

# 3-Tier Mode A Extraction (accepts local .mp4 OR an existing TwelveLabs video_id / partial name):
python3 scripts/twelvelabs_bridge.py extract reference_fight.mp4 --tier fast   --out fast_storyboard.json
python3 scripts/twelvelabs_bridge.py extract reference_fight.mp4 --tier medium --out medium_spec.json
python3 scripts/twelvelabs_bridge.py extract reference_fight.mp4 --tier full   --out full_dossier.json

# Mode B (Audit a Seedance render against your spec & extract true t=10.0s state for Clip N+1):
python3 scripts/twelvelabs_bridge.py audit-render examples/gold_master_3_courtyard_sky_cartwheel.json rendered_clip.mp4 --out audit_report.json
```
