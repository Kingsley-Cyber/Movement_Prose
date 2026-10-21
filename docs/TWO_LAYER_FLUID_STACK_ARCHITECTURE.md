# 2-Layer Unrolled Fluid Stack Architecture (`SAKUGA-MLLM-3.1-CAUSAL` + `--stack`)

This document provides an in-depth, separable specification of the **2-Layer Unrolled Fluid Stack** prompt variation (`--stack`), explaining:
1. How it differs from the **Single-Layer Compact Causal JSON** mode.
2. Why **Prompt Architecture** is completely distinct and separable from **Choreography Archetype** (e.g., Acrobatic Weapon/Wall-Dive vs. High-Intensity Center-Ring Baki Stand-Up War).
3. The 6 mathematical and latent-space engineering rules that make the 2-Layer Unrolled Fluid Stack deterministic on Seedance 2.0 Mini, Seedance 2.5, and Kling.

---

## 1. Architectural Separation: Mode 1 vs. Mode 2

`scripts/sakuga_compiler.py` supports two distinct, separable output modes from the same `SAKUGA-MLLM-3.1-CAUSAL` JSON source:

| Feature | Mode 1: Single-Layer Compact Causal JSON (Default) | Mode 2: 2-Layer Unrolled Fluid Stack (`--stack`) |
| :--- | :--- | :--- |
| **CLI Flag** | `python3 scripts/sakuga_compiler.py compile <spec.json>` | `python3 scripts/sakuga_compiler.py compile --stack <spec.json>` |
| **Structure** | `Natural-Language Header` + `SAKUGA-MLLM-3.1-CAUSAL JSON` | `Header` + `=== LAYER 1: Labanotation-as-Words Timeline ===` + `=== LAYER 2: SAKUGA-MLLM-3.1-CAUSAL JSON ===` |
| **Sub-Beat Density** | 8–10 keyframes in `A_beats` | **14–18 unrolled sub-beats** in `A_beats` (every strike/kick unrolled into Entry/Windup $\rightarrow$ Drive/Turnover $\rightarrow$ Zero-Gap Contact $\rightarrow$ Recovery/Landing) |
| **Bilateral Arm Lock** | Standard limb descriptions | **Mandatory `L_arm` + `R_arm` bilateral silhouette separation** on every beat (`Decision 20`) to eliminate one-arm occlusion |
| **Best Use Case** | Fast grounded weapon duels with simple support transitions (`Gold-Masters #1 & #2`) | High-intensity multi-hit hand-to-hand exchanges, complex kick turnovers, clinches, and multi-axis camera cuts (`Gold-Masters #3, #4, #5`) |

---

## 2. Separating Prompt Architecture from Choreography Archetype

A critical principle of `Movement_Prose` is that **the 2-Layer Unrolled Fluid Stack is a movement-encoding architecture, NOT a fixed choreography template.**

Never reuse a static timestamp skeleton (`1.2s -> 3.05s -> 4.30s -> 5.5s wall-run -> 7.5s ground punch`) when designing a new fight. Every fight archetype has its own rhythm, impact frequency, spatial pocket, and combat logic:

| Dimension | Archetype A: Acrobatic Projectile & Vertical Environment (`Gold-Master #3`) | Archetype B: Relentless Center-Ring Stand-Up War (`Gold-Master #5 — Baki Style`) |
| :--- | :--- | :--- |
| **File** | `examples/gold_master_3_courtyard_sky_cartwheel.json` | `examples/gold_master_5_baki_underground_arena.json` |
| **Combat Style** | Ninja acrobatics + projectile deflection + wall dive | **Baki / Kengan Ashura** bare-knuckle Vale Tudo, Muay Thai clinch, and supersonic karate/boxing |
| **Spatial Pocket** | Full depth + vertical stone wall (`y=0m` to `3.1m`) | **Pure center-ring sand pit (`z=2.3m` to `4.8m`) — ZERO wall-runs, ZERO ground punches** |
| **Opponent (`B`) Activity** | Knocked down against wall at `5.0s`, flinches at `7.5s` | **Stands and fights back fiercely for 8.85 seconds** (throws right straight at `0.0s`, double-axe smash at `1.1s`, clinch lunge at `3.75s`, spinning backfist at `5.7s`) until the `8.85s` KO |
| **Impact Count & Timestamps** | **4 impacts:** `1.20s`, `3.05s`, `4.30s`, `7.50s` | **6 impacts:** `0.65s` (calf kick), `1.75s` (slicing elbow), `3.20s` (3-punch combo hook), `4.85s` (plum-clinch flying knee), `6.40s` (spinning back kick), `8.85s` (Supersonic Mach Straight KO) |
| **Midpoint Screen Cross** | `4.80s` sprint past falling `B` toward wall | `5.25s` **lateral ring-circle pivot** out of the Muay Thai clinch (`screen_left -> screen_right`) |
| **Ending (`8.85s – 10.00s`)** | Deep crouch with reverse-grip kunai | `8.85s` **double sonic-boom Mach Straight knockout** blasting `B` flat onto his back at `z=2.35` (`9.45s`) while `A` holds his extended steaming Mach-Punch follow-through stance |

---

## 3. Deep-Dive Breakdown of the 2-Layer Unrolled Fluid Stack

### Layer 0: The Natural-Language Style & Entity Lock Header
The opening paragraph primes the MLLM's global visual prior before any timestamps appear:
1. **Duration, Frame Rate & Arena Geometry**: e.g., `10s anime fight clip, 24fps, underground circular sand-and-concrete martial arts tournament pit...`
2. **2D Sakuga Style Lock**: `Pure 2D hand-drawn anime, Baki Hanma and Kengan Ashura style hyper-detailed anatomical muscle striations, bulging veins, cel-shaded flat colors with razor-sharp 2-tone high-contrast shadows, heavy ink outlines on A, broken sketchy ink in smears, ultra-thick clean ink on impact holds... Not 3D, not CGI, not live action, not photoreal.`
3. **Entity & Bilateral Limb Lock**: Explicitly states `ZERO weapons` (or exact weapon count) and locks `BOTH left and right bare arms and hands 100% visible in silhouette at all times`.
4. **Anti-HUD & Continuity Rule**: `Execute choreography as one relentless, physically continuous 10-second center-ring stand-up war... no on-screen text, no numbers, no HUD, and no coordinate labels.`

---

### Layer 1: Continuous Support, 5-Phase Force-Event & Prop Timeline (`Labanotation-as-Words`)
Video diffusion transformers lose physical grounding when forced to infer *what bears weight* between sparse timestamps. Layer 1 provides a chronological, human-readable **Labanotation-as-Words** stream where every line obeys the strict grammar:

```text
<seconds> <performer>: SUPPORT (<what bears weight; NO SUPPORT = airborne>) | <bilateral limb placement: both L_arm and R_arm> | <5-phase force event: windup -> drive -> CONTACT -> reaction -> follow-through> | <path in metres>
```

#### Why Layer 1 Works Together with Layer 2:
- **Layer 1** gives the MLLM's natural-language attention heads an unbroken chronological chain of **weight support** (`SUPPORT left bare foot anchored` vs. `NO SUPPORT airborne at knee apex`) and **5-phase force transfer**.
- **Layer 2** gives the MLLM's structured-data attention heads exact **metric coordinates (`pos`, `vel`)**, **causal graph edges (`C01 -> C02`)**, **3-phase contact contracts (`pre -> hit -> post`)**, and **camera/FX bindings** at matching timestamps.

---

### Layer 2: `SAKUGA-MLLM-3.1-CAUSAL` Kinematic & Camera Scene Graph

Layer 2 is governed by **Four Core Engineering Rules** (Decisions 14, 18, 19, 20):

#### Rule A: 4-Phase Sub-Beat Unrolling (`Decision 18`)
Whenever a prompt compresses a multi-stage martial arts technique into a single timestamp (e.g., jumping straight from `3.05s uppercut` to `4.30s kick impact`), the video model has an **800ms–1200ms kinematic void** and hallucinates floaty or morphed anatomy.
In the 2-Layer Fluid Stack, every technique is **unrolled into explicit sequential sub-beats**:
- **Example 1 — 3-Punch Pocket Combination (`2.20s -> 2.65s -> 3.20s` in Gold-Master #5)**:
  - `2.20s` (*Beat 1 — High Probe*): `A` snaps a straight `L_arm` left jab into `B`'s nose (`y=1.48m`) while `R_arm` chambers tight at the right ribs.
  - `2.65s` (*Beat 2 — Level-Change Body Shot*): `A` drops hips to `y=0.70m` and drives a straight `R_arm` right body punch into `B`'s solar plexus (`y=1.12m`) while `L_arm` coils low at the left hip.
  - `3.20s` (*Beat 3 — Rising Jaw Hook Impact*): `A` rises to `y=0.86m` with `R_arm` held high at the right cheekbone in guard and whips a wide `L_arm` left hook across `B`'s jaw (`y=1.46m`, `hold 3f`).
- **Example 2 — Muay Thai Plum Clinch into Flying Knee & Ring-Circle Cross (`3.75s -> 4.30s -> 4.85s -> 5.25s` in Gold-Master #5)**:
  - `3.75s` (*Clinch Entry*): `A` shoots both hands inside `B`'s reach, interlocking `L_arm` and `R_arm` behind `B`'s neck (`zero_gap`).
  - `4.30s` (*Anticipation Hold / Neck Yank*): `A` hangs his weight on both hands, yanking `B`'s head down to `y=1.18m` while coiling his right leg back.
  - `4.85s` (*Airborne Knee Impact*): `A` leaps off his left foot (`none_airborne`), pulling `B`'s head down with both hands while driving his right kneecap upward into `B`'s nose/forehead (`hold 4f, slomo 0.25x`).
  - `5.25s` (*Two-Foot Landing & Lateral Ring-Circle Cross*): `A` lands cleanly on both bare feet, shoves `B` past his left shoulder, and pivots across screen center (`screen_left -> screen_right`).

#### Rule B: Bilateral Two-Arm Silhouette Locking (`Decision 20`)
When a beat describes only the striking arm (e.g., `"drives a right uppercut"` or `"whips a left hook"`), 2D anime diffusion models frequently merge the non-striking arm into the torso silhouette, making the fighter appear one-armed for `0.5s–1.0s`.
- **The Fix**: Every single beat in `A_beats` must explicitly specify both `L_arm:` and `R_arm:` with **clear spatial separation outside the torso silhouette**:
  - During a **deep crouch coil (`2.55s` or `7.35s`)**: One arm extends clearly forward toward `B` with an open taped hand as a range-finding lead guard while the rear striking fist coils low behind the hip.
  - During a **single-arm punch or elbow (`1.75s`, `3.05s`, `3.20s`, `8.85s`)**: The non-striking arm is explicitly placed either in a high cheekbone guard, pinning `B`'s arm forward, or pulled wide back to the opposite hip for counter-torque.

#### Rule C: Zero `<>` Markup Tag Pollution (`Decision 19A`)
Never wrap verbs, strikes, or events in XML/HTML angle brackets (such as `<punch>`, `<impact>`, `<kick>`). In transformer vector space, `<...>` activates the **HTML/XML tag prior**, weakening the physical motion prior. Keep all motion descriptions in direct, active kinematic prose.

#### Rule D: Zero Meta-Negations Inside Beats (`Decision 19B`)
Never write `"A should not float"` or `"NOT a flip"` inside `A_beats` or Layer 1. Attention mechanisms attend to the negated verb (`float`, `flip`). Always state the positive physical law (`vel:[0,-3.6,-0.2]`, `support:"left_bare_foot_anchored_firmly_on_arena_sand"`), and isolate all `"no ..."` tokens strictly inside the top-level `"negative"` field.

#### Rule E: Bilateral Two-Leg Pillar Separation, Bent-Knee Smear Ban & Full-Body Profile Framing (`Decision 21` — The `:04–:05` Clinch Knee Fix)
Empirical render testing on `gold_master_5_baki_underground_arena.json` (`4.30s–4.85s` Muay Thai Plum Clinch Knee) revealed three distinct latent-space failure modes when rendering close-quarters knee strikes:
1. **Failure Mode 1 (Double-Folded Airborne Legs Overlapping in Clinch)**: When `A` is in a point-blank neck clinch (`dz < 0.15m`) and both legs are described as airborne/tucked (`support: "none_airborne"`, `R_leg: folded`, `L_leg: tucked beneath`), both bare legs occupy the exact same `[x,y]` region between `A`'s trunks and `B`'s abdomen, causing the model to fuse `L_leg` and `R_leg` into a deformed 3-legged tangle.
   - **Fix (`Decision 21A`)**: Keep the **standing leg (`L_leg`) anchored straight vertically downward onto the floor as a solid support pillar (`6 o'clock` vector)** while only the **striking knee (`R_leg`) drives high diagonally upward (`8-to-1 o'clock` vector)** with the heel folded tight against the hamstring (`90°+` scissor separation in silhouette).
2. **Failure Mode 2 (Smearing a Bent Knee Joint)**: Applying `smear_frames` to a bent knee joint (`"4.55-4.85: A right knee vertical upward streak"`) blurs the thigh-calf junction into an amorphous flesh blob.
   - **Fix (`Decision 21B`)**: Never apply motion-smear streaks to bent knee strikes; keep both legs in **100% solid, sharp-inked anatomy**.
3. **Failure Mode 3 (`worm_eye` Close-Up Triggering the Uppercut Fist-Leg Hybrid Prior)**: Framing a rising knee impact in a tight `worm_eye` close-up (`fov: 32` looking up at `B`'s chin against the ceiling lights) crops `A`'s pelvis and standing leg out of the frame. Because "tight worm's-eye vertical chin strike + radial star flash" is strongly associated with an **uppercut fist** in anime training data, the model morphs the tip of the rising thigh/knee into a giant clenched fist!
   - **Fix (`Decision 21C`)**: Always frame clinch knee impacts in a **medium-wide side profile (`fov: 38`, `medium_wide_side_profile_grounded_pillar_rising_right_knee_impact`)** that keeps `A`'s entire body from planted standing foot through pelvis, torso, both neck-clinching arms, and the rising knee **100% visible head-to-toe in profile**.

#### Rule F: Realistic Strike-Reach Spacing, 10s Screen-Side Lock & Biomechanical Pose over Franchise Names (`Decision 22`)
1. **Realistic Strike-Reach Spacing (`Decision 22A` — Why `0.20m` Spacing Merges Bodies)**:
   - Staging strikes at `0.15m–0.25m` between `A` and `B` places two adult fighter torsos physically inside each other, forcing the video model to merge chests and limbs.
   - **Rule**: Stage all **punches at one full arm's length (`0.75m – 0.85m` between torso centers)**, all **kicks at one full leg's length (`1.05m – 1.15m` between torso centers)**, and **clinches/elbows at `0.60m – 0.65m`**. State both the metric gap and the natural-language phrase (`"one full arm's length"`, `"one full leg's length"`).
2. **Strict 10-Second Screen-Side Lock (`Decision 22B` — Drop Mid-Clip Side Swaps)**:
   - Swapping `screen_left` and `screen_right` mid-clip while claiming to preserve the 180-degree camera line is a geometric contradiction and is the #1 point where video models swap fighter identities or transfer accessories (such as wrist tape) between fighters.
   - **Rule**: Keep `A` strictly on `screen_left` facing right (`+Z`) and `B` strictly on `screen_right` facing left (`-Z`) for all 10.0 seconds. Spinning techniques (`spinning back kick`) execute cleanly with `A` spinning 360° in place on `screen_left`.
3. **Describe Biomechanical Poses, Never Franchise Attack Names (`Decision 22C`)**:
   - Using franchise move names (`"Triceratops Fist"`, `"Cockroach Dash"`, `"Mach Straight"`) pulls in static anime poster/cutaway poses from training data instead of the intended strike.
   - **Rule**: Keep `"Baki and Kengan Ashura"` strictly in the visual `STYLE` header, and write every technique as direct biomechanical geometry (e.g., `"deep wide lunge, rear left knee low near the sand, right arm locked dead-straight horizontally at chin height, left fist pulled back to the left hip"`).

#### Rule G: Elite 180-Degree Hemisphere Sakuga Cinematography & Multi-Axis Rotational Coverage (`Decision 23`)
Keeping `A` on `screen_left` and `B` on `screen_right` (preserving the 180-degree camera line) must **never** degenerate into locking the camera at a flat $90^\circ$ side-scroller angle (`medium_side_profile`, `fov: 35`) with linear back-and-forth stepping:
1. **Use the Full $+X$ 180-Degree Camera Hemisphere (`Decision 23A`)**:
   - Within the valid front hemisphere (`x > 0`, never crossing the axis line between `A` and `B`), vary camera azimuth, elevation (`y = 0.32m` sand-skimming low angles to `y = 1.82m` over-the-deltoid crane plunges), focal length (`fov: 40` low wide entries to `fov: 28` telephoto impact compressions), and Dutch roll (`-12deg` to `+12deg`) across every beat.
   - Reserve the clean $90^\circ$ full-body `medium_wide_side_profile` (`fov: 38`) specifically for the standing-pillar clinch knee (`4.20s–4.65s`) where head-to-toe pelvis and leg separation is required by `Decision 21C`.
2. **Multi-Axis Torso Torsion, Level Changes & Rotational Momentum Transfer (`Decision 23B`)**:
   - Replace linear rail-stepping with figure-eight head-bob weaves, $45^\circ$ outside slips (specifying the exact shoulder the opponent's punch passes), $90^\circ–110^\circ$ hip/shoulder whip rotations, vertical level-change drop-steps (`y=0.84m -> 0.66m`), and **rotational momentum transfer** (e.g., `B`'s $360^\circ$ spinning right backfist into `A`'s guard at `5.45s` imparting clockwise torque that directly feeds `A`'s $360^\circ$ in-place spinning left back kick at `5.95s–6.50s`).
3. **Anatomically Opposite Head-Snap Vectors (`Decision 23C`)**:
   - Strikes swinging from opposite sides of the target's face must snap the target's head in opposite 3D directions (`1.75s` horizontal right elbow across `B`'s left cheek snaps `B`'s head into the background `-X`; `3.20s` rising left hook across `B`'s right jaw snaps `B`'s head toward the foreground camera `+X`).

---

## 4. Verification & Compilation Workflow

To lint and compile any spec into the 2-Layer Unrolled Fluid Stack:

```bash
# 1. Run the 20-rule physics, causal, and bilateral-arm linter
python3 scripts/sakuga_compiler.py lint examples/gold_master_5_baki_underground_arena.json

# 2. Compile to the 2-Layer Unrolled Fluid Stack (--stack)
python3 scripts/sakuga_compiler.py compile --stack \
  examples/gold_master_5_baki_underground_arena.json \
  --out examples/gold_master_5_baki_underground_arena_fluid_stack.txt
```
