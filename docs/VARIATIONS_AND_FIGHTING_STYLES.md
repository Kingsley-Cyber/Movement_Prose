# Combat-Style Variations & Entity Fighting Style Modeling (`Decisions 21–25`)

> [!IMPORTANT]
> **Strict Separation from the Original Canonical Golden Prompts (`gold_master_1` – `gold_master_4`):**
> The files in [`examples/variations/`](../examples/variations/) are **Combat-Style & Biomechanical Variations** built on top of the `SAKUGA-MLLM-3.1-CAUSAL` + 2-Layer Unrolled Fluid Stack (`--stack`) engine. They are intentionally separated into [`examples/variations/`](../examples/variations/) so that the original 4 Canonical Golden Prompts in [`examples/`](../examples/) (`gold_master_1_blade_exchange.json` through `gold_master_4_shrine_bo_staff_determinism_test.json`) remain untouched as the baseline reference benchmarks.

---

## 1. Canonical Golden Baseline vs. Combat-Style Variations

| Category | File Path | Fighting Style (`laban.A.fighting_style`) | Archetype & Purpose |
| :--- | :--- | :--- | :--- |
| **Canonical Golden #1** | [`examples/gold_master_1_blade_exchange.json`](../examples/gold_master_1_blade_exchange.json) | `shinobi_weapon_acrobat` | Single-Layer JSON baseline: Reverse-grip kunai vs. forearm blade exchange. |
| **Canonical Golden #2** | [`examples/gold_master_2_disarm_dual_blade.json`](../examples/gold_master_2_disarm_dual_blade.json) | `shinobi_weapon_acrobat` | Single-Layer JSON baseline: Wakizashi vs. katana disarm, parabolic launch & dual-blade X-lock. |
| **Canonical Golden #3** | [`examples/gold_master_3_courtyard_sky_cartwheel.json`](../examples/gold_master_3_courtyard_sky_cartwheel.json) | `shinobi_weapon_acrobat` | Original 2-Layer Fluid Stack (`--stack`) baseline: Courtyard sky-cartwheel, rising uppercut (bilateral two-arm lock), wall-run & kunai dive. |
| **Canonical Golden #4** | [`examples/gold_master_4_shrine_bo_staff_determinism_test.json`](../examples/gold_master_4_shrine_bo_staff_determinism_test.json) | `heavy_weapon_master` | Original 2-Layer Fluid Stack (`--stack`) determinism benchmark: Rain shrine bo-staff pole-vault & helicopter spin vs. iron gauntlets. |
| **Variation #1 (Grounded Stand-Up War)** | [`examples/variations/variation_1_baki_grounded_standup_war.json`](../examples/variations/variation_1_baki_grounded_standup_war.json) | `grounded_striker_boxer_baki` | **100% Grounded Bare-Knuckle Stand-Up War** (*Baki / Kengan Ashura*): Dempsey weave slip $\to$ calf kick $\to$ spiral X-parry & $110^\circ$ right elbow $\to$ level-change 3-punch boxing combo $\to$ standing-pillar clinch knee $\to$ B's $360^\circ$ spinning backfist feeding A's in-place $360^\circ$ spinning back kick $\to$ deep-lunge straight right KO. **Zero aerial flips, zero floor sweeps, zero wall-runs.** |
| **Variation #2 (Multi-Domain Freestyle Showcase)** | [`examples/variations/variation_2_multidomain_combative_showcase.json`](../examples/variations/variation_2_multidomain_combative_showcase.json) | `acrobatic_multidomain_freestyle` | **4-Domain Acrobatic Martial Arts Showcase** (*God of High School / Taekwondo / Capoeira*): One-palm floor ankle sweep $\to$ B's push-kick knockdown $\to$ ground bicycle heel up-kick & arched-spine kip-up $\to$ forearm parry into rising elbow & $270^\circ$ spinning backfist $\to$ B's left shovel-hook $\to$ collar-tie snap-down $\to$ jumping scissor switch-knee $\to$ aerial 12-to-6 guillotine axe-heel drop KO. |

---

## 2. Entity Fighting Style Modeling & Preventing Cross-Move Attention Bleed (`Decision 25`)

### 2.1 The Root Problem: Why Aerial Sweeps Can Bleed Into Punch Combos
During empirical testing of multi-domain combat (`Variation #2`), we identified a critical latent-space interaction in video diffusion models:
- When a single 10-second prompt combines **multi-hit grounded boxing punch combinations** (`jab -> cross -> hook`) with **inverted/aerial leg maneuvers** (`one-palm floor ankle sweep`, `bicycle ground up-kick`, `kip-up`, `jumping switch-knee`, `aerial 12-to-6 axe kick`), the video model's **temporal self-attention** shares tokens across the entire 10-second sequence.
- As a result, the global `"acrobatic kicker / floor-sweeper"` prior bleeds into the middle of punch combinations—causing the fighter to randomly throw aerial leg sweeps or kicks during beats meant to be pure hand combinations!

### 2.2 The Solution: Entity `fighting_style` Profiles (`FIGHTING_STYLE_PROFILES`)
Every entity (`laban.A` and `laban.B`) now declares a deterministic **`fighting_style`** profile validated by [`validate_fighting_styles()`](../scripts/sakuga_compiler.py) in [`scripts/sakuga_compiler.py`](../scripts/sakuga_compiler.py):

| `fighting_style` ID | Allowed Biomechanical Vocabulary | Max Airborne Beats | Forbidden Moves (Prevents Attention Bleed) |
| :--- | :--- | :---: | :--- |
| **`grounded_striker_boxer_baki`** | Dempsey head-bob weaves, $45^\circ$ outside slips, low calf kicks, X-forearm parries, horizontal/rising elbows, **multi-hit boxing combos (`jab -> body straight -> hook`)**, standing-pillar clinch knees, spinning backfists, in-place spinning back kicks, deep-lunge straight punches. | `0` | `sky_cartwheel`, `wall_run`, `kip_up`, `bicycle_up_kick`, `one_palm_floor_sweep`, `jumping_scissor_switch_knee`, `high_leap_12_to_6_axe` |
| **`ufc_mma_octagon`** | Realistic Octagon MMA striking & grappling: boxing/Muay Thai combos, low calf kicks, level-change double-leg/ankle-pick takedowns, collar-tie clinch knees, grounded guard up-kicks, technical stand-ups. | `1` | `sky_cartwheel`, `wall_run`, `no_hands_kip_up`, `high_leap_12_to_6_axe` |
| **`muay_thai_nak_muay`** | Pure 8-limb Muay Thai: teep push-kicks, low shin calf/thigh chops, high X-guard blocks, horizontal/rising elbows, Thai plum collar-tie clinches, standing pillar knees. | `1` | `sky_cartwheel`, `wall_run`, `kip_up`, `bicycle_up_kick`, `one_palm_floor_sweep` |
| **`acrobatic_multidomain_freestyle`** | High-flying martial arts showcase: one-palm floor sweeps, bicycle ground up-kicks, arched-spine kip-ups, **2-hit elbow $\to$ spinning backfist chains**, jumping scissor switch-knees, aerial 12-to-6 axe-heel drops. | `3` | `wall_run`, **plus `Decision 25B` Anti-Bleed Rule**: Never pair a 3-punch pure boxing combination with floor sweeps/aerial kicks in the same 10s clip (use 2-hit elbow/backfist spin chains instead). |
| **`shinobi_weapon_acrobat`** | Blade/kunai exchanges, sky-cartwheels, wall-runs, parabolic weapon launches, mid-air catches (`gold_master_1` – `gold_master_3`). | `5` | *(None — weapon acrobat baseline)* |
| **`heavy_weapon_master`** | Polearm/bo-staff sweeps, pole-vaults, helicopter spins vs. heavy gauntlets (`gold_master_4`). | `4` | *(None — polearm baseline)* |

---

## 3. Summary of Empirical Decisions Added in the Variations (`Decisions 21–25`)

1. **`Decision 21` — Standing-Pillar Leg Separation, Bent-Knee Smear Ban & Full-Body Side Profile (`:04–:05` Clinch Knee Fix):**
   - Never fold both legs airborne in a close clinch (`dz < 0.25m`), never apply `smear_frames` to a bent knee joint, and never use a `worm_eye` close-up on a rising knee (which crops out the pelvis and triggers the uppercut fist-leg hybrid prior). Always anchor one leg straight down (`6 o'clock` pillar) or extend it straight back (`5 o'clock` scissor) in clean head-to-toe `medium_wide_side_profile` (`fov: 38`).
2. **`Decision 22` — Full Arm/Leg Strike-Reach Spacing, 10s Screen-Side Lock & Biomechanical Poses over Franchise Names:**
   - Stage punches at **one full arm's length (`0.75–0.85m`)**, elbows/clinches at **half an arm's length (`0.60–0.65m`)**, and kicks at **one full leg's length (`1.05–1.15m`)** with `"both arms separate from the torso in silhouette"` on every hit. Lock `A` on `screen_left` and `B` on `screen_right` for all 10s (zero side swaps), lock outfit/tape identity in header & negative (`no wrist tape on B`), and describe physical poses rather than franchise attack names.
3. **`Decision 23` — Elite 180-Degree Hemisphere Sakuga Cinematography & Multi-Axis Torso Rotations:**
   - Within the $+X$ front hemisphere (never crossing the 180-degree line), vary camera azimuth (`3/4 front-left`, `3/4 over-shoulder`), elevation (`y=0.24m` floor-level to `y=1.82m` crane plunges), focal length (`fov 40` wide coil to `fov 28` telephoto impact snap-zoom), and Dutch roll (`-12°` to `+12°`), while driving multi-axis torso rotations ($90^\circ–360^\circ$) and anatomically opposite head-snap directions (`1.75s` right elbow snaps `B`'s head into background `-X`; `3.20s` left hook snaps `B`'s head toward foreground camera `+X`).
4. **`Decision 24` — 6-Weapon Anatomical Diversity & "Recoil-is-Windup" Chaining:**
   - Cycle across distinct striking surfaces (`shin/calf`, `ankle/heel`, `knee`, `elbow/forearm`, `fist/backfist`, `palm/collar-tie`) and elevations (`low`, `mid`, `high`, `aerial`) so the recoil of Move $N$ physically loads Move $N+1$.
5. **`Decision 25` — Entity `fighting_style` Archetype Gating & Anti-Bleed Isolation:**
   - Lock `laban.<entity>.fighting_style` so grounded boxing/kickboxing wars (`grounded_striker_boxer_baki`, `ufc_mma_octagon`) never get contaminated by acrobatic floor sweeps or aerial flips, and acrobatic showcases (`acrobatic_multidomain_freestyle`) use rotational elbow/backfist chains rather than 3-punch boxing combos.
