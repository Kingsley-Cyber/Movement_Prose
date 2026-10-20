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
├── examples/
│   ├── gold_master_1_blade_exchange.json       # Verified Gold-Master #1 (Reverse-Grip Kunai vs. Forearm Blade Exchange)
│   └── gold_master_2_disarm_dual_blade.json    # Verified Gold-Master #2 (Wakizashi vs. Katana Disarm, Aerial Catch & Twin-Blade X-Lock)
└── references/
    └── sakuga_prompt_schema_sop.md             # Master SOP, 17 Empirical Decisions & 5-Axis R&D Diversification Queue
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

### 4. TwelveLabs Video-to-Sakuga Bridge (Mode A & Mode B)
```bash
# Mode A (Web Playground Prompt — zero API key needed):
python3 scripts/twelvelabs_bridge.py extract-ref --print-prompt

# Mode A (Direct API extraction from a reference fight video):
export TWELVELABS_API_KEY="tlk_your_key_here"
python3 scripts/twelvelabs_bridge.py extract-ref reference_fight.mp4 --out extracted_ref.json

# Mode B (Audit a Seedance render against your spec & extract true t=10.0s state for Clip N+1):
python3 scripts/twelvelabs_bridge.py audit-render examples/gold_master_2_disarm_dual_blade.json rendered_clip.mp4 --out audit_report.json
```
