# Movement_Prose (`SAKUGA-MLLM-3.1-CAUSAL`)

**Movement_Prose** (`sakuga-fight-director`) is an empirically verified **Causal Physics & Biomechanical Choreography Architecture (`SAKUGA-MLLM-3.1-CAUSAL`)**, deterministic Python compiler/linter, and TwelveLabs video-understanding bridge for generating 2D hand-drawn Sakuga martial-arts animations on **Seedance 2.0 Mini, Seedance 2.5, and Kling**.

---

## Repository Structure

```text
Movement_Prose/
├── SKILL.md                                    # Antigravity Skill instructions & YouTube Episode workflow
├── scripts/
│   ├── sakuga_compiler.py                      # Deterministic CLI Compiler, 17-Rule Physics Linter, Style/Taste Injector & Multi-Clip Stitcher
│   └── twelvelabs_bridge.py                    # TwelveLabs Pegasus 1.2 Bridge (Mode A: Reference Extractor, Mode B: Render QA & Handoff)
├── examples/                                   # ✅ CANONICAL TEMPLATES (Use ONLY these for new prompts)
│   ├── gold_master_1_blade_exchange.json       # Verified Gold-Master #1 (Reverse-Grip Kunai vs. Forearm Blade Exchange)
│   └── gold_master_2_disarm_dual_blade.json    # Verified Gold-Master #2 (Wakizashi vs. Katana Disarm, Aerial Catch & Twin-Blade X-Lock)
├── references/
│   └── sakuga_prompt_schema_sop.md             # Master SOP, 17 Empirical Decisions & 5-Axis R&D Diversification Queue
└── _archive_rd_history_do_not_copy/            # ⚠️ HISTORICAL R&D LOGS ONLY (Contains deprecated Euler/Quaternion/Bloat tests — do not copy)
    ├── RD_EXPERIMENT_PROGRESSION_LOG.md        # Complete chronological log of all 13 A/B experiments & empirical render findings
    ├── exp01..exp13_*.txt                      # All 13 prompt iterations tested across the R&D progression (v2.1 -> v3.1-CAUSAL)
    └── baselines/                              # All 5 raw input baselines (v2.0, LBN-2.3-ADV Euler, LBN-2.4-ADV Style Tags, Causal Notes)
```

---

## Quick Start

### 1. Lint & Validate a Fight Choreography Spec
```bash
python3 scripts/sakuga_compiler.py lint examples/gold_master_1_blade_exchange.json examples/gold_master_2_disarm_dual_blade.json
```

### 2. Compile a Single Clip (With Optional Style or Taste Presets)
```bash
# Default verified Gold-Master compile:
python3 scripts/sakuga_compiler.py compile examples/gold_master_2_disarm_dual_blade.json --taste clean

# Compile with Yutaka Nakamura taste layer (hard 2-tone cel, impact chromatic aberration, camera axis lock):
python3 scripts/sakuga_compiler.py compile examples/gold_master_1_blade_exchange.json --taste nakamura

# Re-skin into experimental animation styles (cel_default, genga, sumi_ink, trigger_neon, retro_90s, ufotable):
python3 scripts/sakuga_compiler.py compile examples/gold_master_1_blade_exchange.json --style genga
```

### 3. Stitch Multiple 10s Clips Into a YouTube Episode Pack
```bash
python3 scripts/sakuga_compiler.py stitch examples/gold_master_1_blade_exchange.json examples/gold_master_2_disarm_dual_blade.json --out episode_pack.md
```

### 4. TwelveLabs Video Intelligence Bridge (3-Tier Extraction + Full Account CLI)
```bash
# Authenticate once (saves key to ~/.config/sakuga/twelvelabs.json) & inspect your TwelveLabs account/videos:
python3 scripts/twelvelabs_bridge.py auth --set-key "tlk_your_key_here"
python3 scripts/twelvelabs_bridge.py account
python3 scripts/twelvelabs_bridge.py videos

# 3-Tier Mode A Extraction (accepts local .mp4 OR an existing TwelveLabs video_id / partial name):
#   --tier fast   : 1 API call  (Rapid Storyboard + macro C01->C10 beats)
#   --tier medium : 2 API calls (Gist + single-pass SAKUGA-MLLM-3.1-CAUSAL JSON)
#   --tier full   : 6 passes    (100% TwelveLabs extraction: System Metadata, Gist, Summary/Chapters/Highlights,
#                                Deep Pegasus Pass A Biomechanics/Causal/Laban, Deep Pegasus Pass B Camera/Sakuga/Props/Audio,
#                                and Marengo 2.7 Temporal Action Search + optional --embed vector embeddings)
python3 scripts/twelvelabs_bridge.py extract reference_fight.mp4 --tier fast   --out fast_storyboard.json
python3 scripts/twelvelabs_bridge.py extract reference_fight.mp4 --tier medium --out medium_spec.json
python3 scripts/twelvelabs_bridge.py extract reference_fight.mp4 --tier full   --out full_dossier.json

# Conversational Q&A with Pegasus 1.2 & Marengo 2.7 Moment Search on any indexed video:
python3 scripts/twelvelabs_bridge.py ask reference_fight.mp4 "What happens to the katana after the disarm at t=2.0s?"
python3 scripts/twelvelabs_bridge.py search "metallic blade clash" "shoulder vault"

# Mode B (Audit a Seedance render against your spec & extract true t=10.0s state for Clip N+1):
python3 scripts/twelvelabs_bridge.py audit-render examples/gold_master_2_disarm_dual_blade.json rendered_clip.mp4 --out audit_report.json
```
