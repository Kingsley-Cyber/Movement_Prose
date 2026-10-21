# Movement_Prose (`SAKUGA-MLLM-3.1-CAUSAL`): Complete Chronological R&D Experiment & A/B Test Log

This document records the complete chronological progression of every baseline, hypothesis, prompt experiment (`exp01`–`exp13`), and empirical render result on **Seedance 2.0 Mini** and **Seedance 2.5** that led to the verified **`SAKUGA-MLLM-3.1-CAUSAL`** architecture.

---

## 1. Input Baselines (`experiments/baselines/`)

| File | Description | Key Characteristics & Issues |
| :--- | :--- | :--- |
| [baseline01_sky_cartwheel_v2_0.txt](./baselines/baseline01_sky_cartwheel_v2_0.txt) | Original 10s `courtyard_10s_sky_cartwheel` prompt | Compact JSON (`A_beats`, `B_track`, `kunai`, `camera`, `anime`, `rules`), no Laban block, contrastive negations (`"NOT a kick"`) inside beat `3.05`. |
| [baseline02_lbn_2_3_adv_sky_cartwheel_euler.txt](./baselines/baseline02_lbn_2_3_adv_sky_cartwheel_euler.txt) | `LBN-2.3-ADV` 10-bone Euler dictionary variant (`sky_cartwheel`) | Contained ~1,400 tokens of 10-bone Euler triplets (`{"Sp":[30,0,0],"LUL":[-60,0,0]...}`), causing stiff 3D mocap bias and on-screen HUD number bleed. |
| [baseline03_lbn_2_3_adv_naruto_kawarimi_pillar.txt](./baselines/baseline03_lbn_2_3_adv_naruto_kawarimi_pillar.txt) | `LBN-2.3-ADV` Naruto Kawarimi Substitution & Pillar Fight (4 props, 21 beats) | Complex 4-prop choreography (`kunai`, `rope_dart`, `smoke_pellet`, `shuriken_volley`) weighed down by 10-bone Euler dictionaries and `"Render spec exactly"` HUD triggers. |
| [baseline04_lbn_2_4_adv_naruto_kawarimi_style_tags.txt](./baselines/baseline04_lbn_2_4_adv_naruto_kawarimi_style_tags.txt) | `LBN-2.4-ADV` variant with per-beat `style`, `fx`, `expression`, `camera_tempo` | Added 6 non-kinematic metadata keys to every beat + top-level `fx_presets` dictionary. |
| [baseline05_causal_physics_graph_analysis_notes.md](./baselines/baseline05_causal_physics_graph_analysis_notes.md) | 10-Point Causal Physics Specification Analysis | Introduced `C01->C23` causal dependency edges (`requires`/`causes`), `conservation_laws`, 3-phase `contact_contract` (`pre->at->post`), `BEFORE_INTERSECTION` evasion timing, and 180° `screen_geometry`. |

---

## 2. Chronological Experimental Progression (`exp01` $\rightarrow$ `exp13`)

### Experiment 01: Cannibalizing Laban, Limb Shorthand & Prop Ownership (`v2.1`)
* **File:** [exp01_sky_cartwheel_v2_1_cannibalized.txt](./exp01_sky_cartwheel_v2_1_cannibalized.txt)
* **What Changed:** Stripped the 1,400 tokens of 10-bone Euler dictionaries from `LBN-2.3-ADV` while cannibalizing its highest-signal semantic locks (`laban` Effort + Chain, `limbs` L/R/feet anatomical shorthand, explicit `owner` in `kunai` track, `hold_frames` in `camera`, and Anti-HUD header directives).
* **Empirical Render Result (Seedance 2.0 Mini vs. 2.5):**
  * **Seedance 2.5:** Rendered the `t=3.05` uppercut punch cleanly.
  * **Seedance 2.0 Mini:** Rendered a **kick** at `t=3.05` instead of a punch, and the flip after the kick + `:07–:08` wall-run was slightly weird/floaty.
* **Root-Cause Discovery:** Beat `3.05` contained `"PUNCH NOT A KICK — BOTH FEET STAY ON THE GROUND"`. Distilled models (Mini) suffer from **contrastive negation leakage**—seeing the token `"KICK"` activates the kicking motion prior!

---

### Experiment 02: Positive-Only Limb Immobilization & Wall-Run Grounding (`v2.2`)
* **File:** [exp02_sky_cartwheel_v2_2_positive_limb_lock.txt](./exp02_sky_cartwheel_v2_2_positive_limb_lock.txt)
* **What Changed:**
  1. Removed every instance of `"NOT a kick"` / `"NOT a punch"` from `A_beats`.
  2. Replaced them with **Positive-Only Limb Immobilization** (`"feet:both boots planted flat on stone floor in wide horse stance"`).
  3. Added explicit intermediate contact frames for the `:07–:08` wall-run (`z=5.7` against the `z=6.0` wall).
* **Result:** Established **Decision 03 (Positive-Only Limb Immobilization)**.

---

### Experiment 03: Upgrading to 6D Orthogonal Basis (`axis`), Winding (`arc`), Support & Contact (`v2.3`)
* **File:** [exp03_sky_cartwheel_v2_3_6d_basis_arc_contact.txt](./exp03_sky_cartwheel_v2_3_6d_basis_arc_contact.txt)
* **What Changed:** Audited 8 spatial/rotational representation systems (World Cartesian, Joint-Parent Local, Cylindrical/Spherical, Euler, Quaternions, Axis-Angle, 6D Orthogonal Basis, Pairwise Relational Graph) and upgraded `A_beats` with `axis` (6D head/chest/facing vectors), `arc` (monotonic winding `0->90->180->270->360` + 2D clock-face arcs), `support` (positive ground lock), and `contact` (pairwise target binding).
* **Empirical Render Result:** Kinematics improved, **but** the choreography of `sky_cartwheel` still felt non-immersive on Seedance 2.0 Mini because Fighter B was knocked out at `t=5.0s` (leaving A doing isolated gymnastics in empty air from `5.0s–10.0s` in a wide `fov 45–50` shot).

---

### Experiment 04: Close-Quarters Two-Way Blade Exchange (`cqc_sakuga_10s_blade_exchange` — Non-Quaternion Winner)
* **File:** [exp04_cqc_blade_exchange_v3_0_non_quaternion_winner.txt](./exp04_cqc_blade_exchange_v3_0_non_quaternion_winner.txt)
* **What Changed:** Replaced distant solo gymnastics with a continuous, two-way close-quarters martial arts exchange ($\Delta z \le 1.5\text{m}$, tight `fov 28–38` lenses, active blade parry $\rightarrow$ inside liver hook $\rightarrow$ U-weave under elbow $\rightarrow$ rising palm $\rightarrow$ 360 spinning hook kick into guard skid $\rightarrow$ shoulder-plant vault $\rightarrow$ low ankle sweep $\rightarrow$ chest pommel pin $\rightarrow$ throat blade lock).
* **Empirical Render Result:** **Huge win on Seedance 2.0 Mini.** Understood the assignment with crisp contact and zero lag.

---

### Experiment 05: Direct 1-to-1 Quaternion (`q_root`, `q_rig`, `slerp`) A/B Test
* **File:** [exp05_cqc_blade_exchange_quaternion_slerp_ab_test.txt](./exp05_cqc_blade_exchange_quaternion_slerp_ab_test.txt)
* **What Changed:** Converted `cqc_sakuga_10s_blade_exchange` into exact unit quaternions (`q_root: [w,x,y,z]`, `q_rig` for spine/arms/legs, and `interp: "slerp_constant_omega"`).
* **Empirical Render Result (Crucial A/B Finding):**
  * **The Non-Quaternion version (`exp04`) WON.**
  * With Quaternions (`exp05`), **the character sometimes missed and hit empty air**, and had **weird motion lag**.
* **Why Quaternions Lost:**
  1. Injecting 28 floating-point numbers per beat diluted the MLLM's self-attention over `"contact"` and `"pos"`, breaking spatial hit registration.
  2. `"slerp"` biased the temporal DiT layers toward constant-velocity spline smoothing instead of snappy on-twos Sakuga step-functions.
* **Result:** Established **Decision 04 (Never Use Quaternions in Text Prompts)**.

---

### Experiment 06: Porting Complex 4-Prop Naruto Kawarimi Pillar Prompt to `SAKUGA-MLLM-3.0`
* **File:** [exp06_naruto_kawarimi_pillar_v3_0_initial_port.txt](./exp06_naruto_kawarimi_pillar_v3_0_initial_port.txt)
* **What Changed:** Ported `baseline03_lbn_2_3_adv_naruto_kawarimi_pillar.txt` (4 props: `kunai`, `rope_dart`, `smoke_pellet`, `shuriken_volley`, plus `substitution_log`) into `SAKUGA-MLLM-3.0`, stripping all 10-bone Euler dicts and adding `axis`, `arc`, `support`, and `contact`.
* **Empirical Render Result:** Clean transition ("honestly better than I expected"), though slightly fast-paced (finished the enemy around `:08`).

---

### Experiment 07: Pacing Rebalance + Explicit Kawarimi Motivation (`v3.1`)
* **File:** [exp07_naruto_kawarimi_pillar_v3_1_10s_rebalanced.txt](./exp07_naruto_kawarimi_pillar_v3_1_10s_rebalanced.txt)
* **What Changed:** Stretched the 21-beat timeline so the final axe-kick knockdown lands at `t=8.8s` instead of `t=7.8s`, and clarified B's kunai throw (`t=1.6s`) and B's point-blank rope-dart thrust (`t=3.5s`) to motivate the `t=3.7s` Kawarimi smoke substitution.

---

### Experiment 08: Testing Per-Beat Metadata Bloat from `LBN-2.4-ADV` (`v3.2` — Regression Test)
* **File:** [exp08_naruto_kawarimi_pillar_v3_2_metadata_bloat_regression.txt](./exp08_naruto_kawarimi_pillar_v3_2_metadata_bloat_regression.txt)
* **What Changed:** Ported `LBN-2.4-ADV`'s 6 extra non-kinematic metadata keys (`style`, `duration_frames`, `camera_tempo`, `fx_preset`, `expression`, `contrast`) into every beat of `A_beats` + top-level `fx_presets`.
* **Empirical Render Result:** **Got worse.** The run down the wooden pillar became weird and broken.
* **Root-Cause Discovery:**
  1. Adding 6 extra non-kinematic keys per beat diluted attention over `pos`, `axis`, and `support` (same token-dilution mechanism as Quaternions).
  2. Writing `"spine:horizontal_to_ground_parallel_to_pillar"` created a $90^\circ$ geometric contradiction (a vertical pillar is perpendicular to the ground, not horizontal!).
* **Result:** Established **Decision 13 (Reject Per-Beat Non-Kinematic Metadata Bloat)**.

---

### Experiment 09: Restoring Pure Kinematic `SAKUGA-MLLM-3.0` + Vertical Pillar Geometry Fix (`clean_v3`)
* **File:** [exp09_naruto_kawarimi_pillar_v3_0_clean_restored.txt](./exp09_naruto_kawarimi_pillar_v3_0_clean_restored.txt)
* **What Changed:** Stripped all 6 per-beat bloat keys from `A_beats` and fixed the pillar sprint geometry (`"spine:parallel_to_vertical_pillar"`, starting `t=0.0` at `z=5.5` directly above the `z=5.8` pillar face).

---

### Experiment 10: The Causal Physics Graph Upgrade (`SAKUGA-MLLM-3.1-CAUSAL` — Progressive Milestone)
* **File:** [exp10_cqc_blade_exchange_v3_1_causal_milestone.txt](./exp10_cqc_blade_exchange_v3_1_causal_milestone.txt)
* **What Changed:** Integrated the 5 missing primitives from the Causal Physics Specification into `cqc_sakuga_10s_blade_exchange` **without bloating per-beat keys**:
  1. Compact `"causal"` edge per beat (`C01 -> C10` with `requires -> timing: BEFORE_INTERSECTION -> preserves -> causes`).
  2. 3-Phase Contact Contract inside `"contact"` (`pre:... -> hit:..._zero_gap -> post:...`).
  3. Top-level `"screen_geometry"` + per-beat `screen_side:left|right` 180-degree camera lock.
  4. Top-level `"conservation_laws"` array (`CONSERVE_SEMANTICALLY`).
  5. Header & `rules` Continuous Combat Event thesis.
* **Empirical Render Result:** **Major progressive milestone on Seedance 2.0 Mini ("hey this increases the render a lot. this is a progressive milestone").** Locked as **Canonical Gold-Master #1**.

---

### Experiment 11: Brand-New Choreography — Kung-Fu Recoil/Uncoil + Mid-Fight Sword Disarm & Aerial Catch (`Gold-Master #2`)
* **File:** [exp11_cqc_disarm_dual_blade_v3_1_causal_winner.txt](./exp11_cqc_disarm_dual_blade_v3_1_causal_winner.txt)
* **What Changed:** Built a brand-new fight (`cqc_sakuga_10s_disarm_dual_blade_lock`) on `SAKUGA-MLLM-3.1-CAUSAL` testing:
  * Elastic kung-fu recoil/uncoil transitions (`C04` limbo back-sway $\rightarrow$ `C05` whiplash front kick; `C06` shoulder-bump bind $\rightarrow$ `C07` upward crescent kick wrist disarm).
  * Multi-prop ownership transfer (`katana` kicked upward to `y=2.1m` at `t=4.4s` $\rightarrow$ caught in A's empty left hand at `t=5.2s` while ducking B's haymaker and crossing `screen_left -> screen_right` $\rightarrow$ twin-blade X-scissor neck lock at `t=7.4s–10.0s`).
* **Empirical Render Result:** **Winner ("this is actually good and beautiful, it even has good kungfu natural movements").** Locked as **Canonical Gold-Master #2**.

---

### Experiment 12: Static Screen-Side Decomposition A/B Test (`mini_clean` vs. Dynamic Midpoint Cross)
* **File:** [exp12_cqc_disarm_dual_blade_mini_static_standoff_ab_test.txt](./exp12_cqc_disarm_dual_blade_mini_static_standoff_ab_test.txt)
* **What Changed:** Tested keeping `A` on `screen_left` and `B` on `screen_right` for all 10 seconds, popping the disarmed sword to "hover at chest height" (`y=1.4m`), and pausing on planted boots at `t=5.1s` to snatch it.
* **Empirical Render Result:** **Lost to `exp11` ("i think the other one was better").**
* **Why `exp11` Beat `exp12`:**
  1. Keeping fighters on fixed screen sides for all 10 seconds creates a static standoff; a **Dynamic Midpoint Physical Cross (`screen_left -> screen_right` around `t=4.9s–5.2s`)** is essential for sweeping 3D Sakuga momentum.
  2. Launching the disarmed blade to a true parabolic apex (`y=2.1m`) and catching it on the move (`y=1.42m`) beats "hovering" prop physics.
* **Result:** Established **Decision 16 (Preserve Dynamic Mid-Fight Screen-Crosses & Parabolic Prop Gravity)**.

---

### Experiment 13: Per-Beat Laban Effort Signatures (`SLASH`/`PUNCH`/`DAB`) + Localized Rule-Breaking (`Taste Layer` Asymptote)
* **File:** [exp13_cqc_blade_exchange_laban_nakamura_taste_layer.txt](./exp13_cqc_blade_exchange_laban_nakamura_taste_layer.txt)
* **What Changed:** Added per-beat Laban Effort prefixes (`LABAN_SLASH`, `LABAN_PUNCH`, `LABAN_DAB`, `LABAN_PRESS`) inside `"arc"`, camera `"preserve_axis": true` + `"OVERSHOOT"`, and `"chromatic_aberration": "impact_frames_only"` inside `"anime"`.
* **Empirical Render Result:** Good render, with a slight/marginal aesthetic difference ("at this point its gotten to a point of slight or bare increase and its now like a taste modifications layer").
* **Result:** Established **Decision 17 (Tier-1 Structural Backbone vs. Tier-2 Optional Taste/Seasoning Layer)** and exposed `--taste nakamura` as an optional compiler flag in [sakuga_compiler.py](../scripts/sakuga_compiler.py).

---

### Experiment 14: 2-Layer Fluid Stack V1 on Courtyard Sky-Cartwheel (`Collapsed Sub-Beats` Diagnosis)
* **File:** [exp14_courtyard_sky_cartwheel_v1_collapsed_subbeats.txt](./exp14_courtyard_sky_cartwheel_v1_collapsed_subbeats.txt)
* **What Changed:** Combined **Layer 1 (`Labanotation-as-Words` Support + Force-Event Timeline)** above **Layer 2 (`SAKUGA-MLLM-3.1-CAUSAL` JSON)** for the 10s Courtyard Sky-Cartwheel & Kunai Dive choreography (`14 beats`).
* **Empirical Render Result (Seedance 2.0 Mini):**
  * **Good overall, and the `3.05s` rising left uppercut punch rendered unambiguously.**
  * **However, the other 4 complex moves (sky-cartwheel, aerial leg-cartwheel kick, wall-run, and dive) had weird moments.**
* **Root-Cause Discovery:**
  * The `3.05s` uppercut succeeded because it had **3 sequential keyframes** (`2.20s` approach steps $\rightarrow$ `2.75s` deep hip sink $\rightarrow$ `3.05s` upward drive & chin impact).
  * The other 4 moves skipped intermediate keyframes in `A_beats` (e.g., jumping from a `4.3s` mid-air kick directly to a `5.5s` wall-run without a `4.8s` floor landing; skipping the `4.0s` $180^\circ$ inverted aerial apex; skipping the `5.9s` wall push-off; and writing `"the model should not float or drift"` inside the `6.6s` dive beat).
* **Result:** Established **Decision 18 (4-Phase Sub-Beat Unrolling)** and **Decision 19 (Single-Source 2-Layer Fluid Stack & Zero Meta-Negation / `<verb>` Markup Pollution)**.

---

### Experiment 15: 2-Layer Unrolled Fluid Stack V2 (`17 Unrolled Beats` + Bilateral Arm Silhouette Lock — `Gold-Master #3`)
* **File:** [exp15_courtyard_sky_cartwheel_v2_unrolled_2layer_winner.txt](./exp15_courtyard_sky_cartwheel_v2_unrolled_2layer_winner.txt)
* **What Changed:**
  1. Unrolled all 5 moves into **17 sequential keyframes** across both Layer 1 and Layer 2 (`0.9s -> 1.2s -> 1.6s -> 2.2s` traveling cartwheel; `2.2s -> 2.75s -> 3.05s` uppercut; `3.6s -> 4.0s -> 4.3s -> 4.8s` aerial wheel apex + floor landing; `5.5s -> 5.7s -> 5.9s` fast `0.35s` wall-run + high push-off; `6.6s -> 7.1s -> 7.5s` mid-air catch + steep `vy=-3.6` dive drive + three-point landing).
  2. Removed the meta-negation `"should not float or drift"`.
* **Empirical Render Result (Seedance 2.0 Mini):**
  * **Confirmed Winner ("this prompt is good").** All 5 moves rendered fluidly.
  * **Single Remaining Visual Quirk & Fix (`:03` One-Arm Occlusion -> Decision 20):** At `:03` (`2.75s–3.05s` uppercut windup viewed over B's shoulder), Fighter A appeared to have only 1 arm (left fist cocked at left hip) because the non-striking right arm was only tagged `"R_arm:high guard"` and got occluded behind A's forward-leaning dark coat torso. Fixed in [gold_master_3_courtyard_sky_cartwheel.json](../examples/gold_master_3_courtyard_sky_cartwheel.json) by locking **Bilateral Two-Arm Silhouette Placement** on every beat (`R_arm extended clearly forward toward B's chest with open right palm as a range-finding lead guard while L_arm coils low at left hip`).
