# Fight Move System — Master Architecture & Execution Plan (v2)

Owner: King. Written 2026-10-21. Status: Approved Architecture Plan (v2 — unifies deterministic Move System with empirical Sakuga/Combat findings from `Movement_Prose`).
Target: A standalone, model-agnostic engine (`fight_move_system/`) that sits in front of any text-to-video pipeline and turns a structured fight beat sheet into:
1. A deterministic **validation report** (`V01–V17`),
2. A **multi-clip regime plan** (one movement regime per clip, chained fighter/dyad state across clips), and
3. A **render-ready caption prompt** (plus optional separate `negative_prompt` channel) so fights are physically coherent, read as fluid, preserve 2D Sakuga / martial-arts impact quality, and do not leak out-of-regime moves across a clip.

---

## 0. Core Engineering Laws (Read First)

1. **Code guarantees structure; renders prove behaviour.**
   - Everything in §3–§8 is 100% deterministic and unit-tested.
   - Everything about what a video model *does* at inference time (attention bleed, stiffness perception, camera motion tolerance, phrasing quality) is a **hypothesis** until verified by the owner's renders (§10). Never state an uncalibrated hypothesis as fact in code comments, docs, or reports.
2. **No invented numbers.**
   - Every threshold (minimum beat duration, bleed budget per clip, camera speed switch) lives in one central config file (`config/thresholds.json`), each row marked `status: "hypothesis" | "calibrated"` with `evidence_render_ids: []`. All thresholds start at `"hypothesis"`.
3. **Numbers never reach the printed positive prompt (`V15`).**
   - Metres (`0.80m`), degrees (`45°`), frame counts (`9f`, `3 frames`), and decimal timestamps (`[t=2.50s]`, `pos=(-0.45, 0, -0.40)`) stay strictly inside code and validation logs.
   - The printed prompt uses **natural physical spacing words** (`"at arm's length"`, `"at kicking range"`, `"chest to chest in the clinch"`) and **natural timing words** (`"an instant later"`, `"at the same moment"`, `"holding briefly on impact"`).
4. **Never print a forbidden move in the positive prompt ("The Pink Elephant Rule", `V15`).**
   - Moves outside the clip's style or regime are completely omitted from the positive prompt.
   - Never print `"no floor sweeps, no kip-ups, no flying knees"` in the main prompt: naming a move injects its tokens into the video model's cross-attention and causes the exact bleed you are trying to prevent.
   - Negative constraints may only be emitted to a separate `negative_prompt` output field when targeting an API that supports a dedicated negative-prompt channel.
5. **No live render or paid API call without the owner's explicit OK.**
   - The agent prepares deterministic render packets; the owner runs the renders and logs visual verdicts.
6. **Owner decisions belong to the owner (§12).**
   - Where a choice affects style, wording taste, or a rule in this plan, use the conservative default, mark it `DRAFT`, and surface it in the milestone report.
7. **Disciplined delivery.**
   - One commit per milestone/piece, 100% tests green before each commit, with a concise changelog entry (what changed, why, evidence).

---

## 1. Consolidation Strategy: What We Keep vs. What We Replace from `Movement_Prose`

| Area | Decision | Why (Empirical Evidence from Earlier Renders) |
|---|---|---|
| **Sakuga / Anime Visual Technique (9/10)** | **KEEP** (Move into §8 Wording Compiler Style Layer) | Impact holds (expressed in words, not frame digits), **single-limb smear** on the striking limb only (never full-body blur), speed lines, shockwaves, anticipation coil before finishers, and thick ink linework produced 9/10 visual quality. |
| **Natural Distance & Spacing Words** | **KEEP & CODIFY** (§3 Range Band $\to$ §8 Range Phrase Table) | Replacing raw metre numbers with `"at arm's length"`, `"half an arm's length"`, `"at a full leg's length"`, and `"chest to chest"` directly fixes the 0.2m body-merging issue (5/10 $\to$ clean separation). |
| **Screen-Side Lock (`A = left`, `B = right`) & Wardrobe Lock** | **KEEP & ENFORCE** (`V16`) | Locking Fighter A to `screen_left` and Fighter B to `screen_right` with high-contrast wardrobe anchors prevents mid-clip identity swaps and wrist-tape jumping. |
| **Body-Shape Move Descriptions (No Franchise Names)** | **KEEP & ENFORCE** (`V15`) | Describing moves by exact body shape (`"deep lunge, rear knee low, right arm straight at chin height"`) instead of franchise names (`"Triceratops Fist"`, `"Mach punch"`) stops the model from pulling in static anime pose tropes. |
| **Two-Way Competitive Exchanges** | **KEEP & ENFORCE** (`V17` warning) | A fight reads as a war when both fighters attack and at least one counter-sequence rides the opponent's landed/blocked blow. |
| **51k-Char 2-Layer Coordinate/Timestamp Dump** | **REPLACE** with Clean Caption Prose (§8) | Video diffusion models are trained on natural video captions, not `[t=2.50s] pos=(-0.45, 0.0, -0.40) (hold 3f) IMPACT FRAME (hold 3 frames)`. |
| **Positive-Prompt "No Sweeps / No Kip-Ups" Lists** | **DROP** (`V15`) | Naming forbidden moves in the positive prompt primes temporal self-attention to hallucinate them. |
| **Regex Keyword Guessing on Free-Form Prose** | **REPLACE** with Closed Move Lexicon (§4) & State Machines (§5) | Regexes cannot verify stance preconditions, coil continuity, or 4-limb occupancy. A closed Move Card lexicon validates them with 100% certainty. |

---

## 2. Six-Part Architecture

| # | Module | Deterministic? | Responsibility |
|---|---|---|---|
| **1** | **Move Lexicon (`lexicon/`)** | **Yes (100%)** | Closed registry of Move Cards: limb, primary joint hinge, path, level, pre/post posture & coil, range rules, 4-limb caption templates. |
| **2** | **Fighter State Machine (`state.py`)** | **Yes (100%)** | Tracks each fighter's `{stance, support, coil, guard_lead, guard_rear, screen_side, facing}` beat by beat. |
| **3** | **Dyad Coupling Validator (`dyad.py`)** | **Yes (100%)** | Tracks shared `{range_band, clinch_state}` and validates every contact beat across both fighters (range, level, camera-relative force direction, clinch symmetry, paired reaction). |
| **4** | **Clip Composer (`composer.py`)** | **Rules: Yes** | Enforces one movement regime per clip, carries end-state into Clip $N+1$, checks bleed budget (`V13`) and quarantine ledger (`V14`), and proposes clip split points on violation. |
| **5** | **Wording Compiler (`compiler.py`)** | **Yes (100%)** | Emits natural caption prose: 1-sentence identity/side lock, stance-resolved left/right limbs, 4-limb occupancy on key beats, spacing phrases, Sakuga impact phrasing, camera prose, zero digits/forbidden move names. |
| **6** | **Evidence Ledgers (`ledgers/`)** | **Empirical Data** | Stores `word_probes.json`, `quarantined_pairs.json`, and `thresholds.json` updated strictly from owner render verdicts. |

**Pipeline Flow:**
`Beat Sheet (JSON) → Validate Self & Dyad (Parts 2 & 3) → Compose Clips (Part 4) → Compile Caption Prompt (Part 5) → Output {Validation Report + Prompt Packet}`

---

## 3. Closed Vocabularies (Strict Enums)

Every field below is a closed enum. Any unknown value raises `V01 (error)`.

* **Stance (Handedness):**
  * `orthodox` (`lead` = `left`, `rear` = `right`)
  * `southpaw` (`lead` = `right`, `rear` = `left`)
* **Support Base (`support`):**
  * `standing`, `crouched`, `airborne`, `kneeling`, `supine`, `prone`, `clinched`
* **Coil / Kinetic Carry State (`coil` — 8 states in v1):**
  * `neutral` (balanced guard; only legal at clip start, after separation, or at exchange end)
  * `loaded_lead` (torso/hips coiled toward lead side — springs into lead hook, lead uppercut, lead leg kick, or slip-counter)
  * `loaded_right` / `loaded_rear` (`loaded_rear`: torso/hips coiled toward rear side — springs into rear cross, rear overhand, rear knee, or rear roundhouse)
  * `overcommitted_forward` (weight pitched past lead foot after heavy lunge/whiff)
  * `recoiling_back` (weight absorbing backward momentum from block or hit)
  * `spinning_cw` (continuous clockwise rotational carry)
  * `spinning_ccw` (continuous counter-clockwise rotational carry)
  * `level_low` (hips dropped below opponent's punch line — springs into rising uppercut, level-change tackle, or rising knee)
* **Guard State (`guard_lead`, `guard_rear`):**
  * `high` (protecting jaw/temple, silhouette separate from torso)
  * `low` (dropped near waist/ribs)
  * `framing` (extended forearm/palm checking opponent's shoulder or bicep)
  * `clinching` (collar tie, underhook, or wrist control)
  * `striking` (currently executing the beat's strike)
* **Shared Dyad Range Band (`range_band` + Canonical Caption Words):**
  * `outside`: *"beyond kicking reach, a full stride apart"*
  * `kick`: *"at a full leg's length apart"*
  * `punch`: *"at a full arm's length apart"*
  * `pocket`: *"half an arm's length apart in close pocket range"*
  * `clinch`: *"chest to chest in a tight clinch"*
  * `ground`: *"tangled at canvas level"*
* **Clip Regime (`regime`):**
  * `standup_striking` (standing punches, elbows, knees, standing kicks, slips, parries, brief collar-tie knees)
  * `clinch` (sustained tie-ups, dirty boxing, plum knees, pummeling, throws/trips)
  * `ground` (sweeps from canvas, up-kicks, guard passes, ground-and-pound, technical stand-ups)
  * `transition` (single boundary beat bridging two regimes, e.g., takedown, sprawl, knockdown, stand-up)
* **Fighting Style (`style`):**
  * `boxing`, `muay_thai`, `mma`, `baki` (grounded bare-knuckle standup war), `freestyle_sakuga`
* **Acting Limb (`limb`):**
  * `lead_hand`, `rear_hand`, `lead_elbow`, `rear_elbow`, `lead_knee`, `rear_knee`, `lead_leg`, `rear_leg`, `head`, `hips`, `both_hands`, `full_body`
* **Primary Joint Hinge (`hinge` — 1 per card for silhouette clarity):**
  * `shoulder_extension`, `elbow_flex`, `hip_whip`, `knee_drive`, `ankle_pivot`, `spine_arch`, `full_body_drop`
* **Trajectory Path (`path`):**
  * `straight`, `arc_horizontal`, `arc_vertical`, `full_rotation`, `ground_arc`, `downward`, `push`, `none`
* **Elevation Level (`level`):**
  * `low` (calf, thigh, ankle), `mid` (ribs, liver, solar plexus, torso), `high` (chin, jaw, temple, nose bridge)
* **Contact Type (`contact`):**
  * `strike`, `grapple`, `evade`, `block`, `none`
* **Body-Relative Force (`force_local` on Move Card) $\to$ Resolved Camera-Relative Force (`force_cam`):**
  * Card stores `force_local`: `forward_straight`, `arc_lead_to_rear`, `arc_rear_to_lead`, `upward`, `downward`, `pull_inward`, `none`.
  * Validator resolves `force_cam` from `fighter.screen_side` (`left` vs. `right`):
    * `toward_screen_left`, `toward_screen_right`, `toward_camera`, `away_from_camera`, `upward`, `downward`, `none`.
* **Bleed Tier (`bleed_tier` — hypothesis until H2/H3 calibrated):**
  * `1`: Local limb motion (jabs, crosses, hooks, uppercuts, slips, parries, blocks, steps)
  * `2`: Heavy torso/hip rotation (roundhouse kicks, step-in elbows, standing clinch knees, sprawls)
  * `3`: Global / high-salience body override (spinning back kicks, tornado kicks, ankle sweeps, kip-ups, flying knees, throws)

---

## 4. Move Card Schema & The 22 Move Classes

### 4.1 Move Card Schema (`lexicon/*.json`)
Note how `{lead_hand}`, `{rear_hand}`, `{lead_leg}`, and `{rear_leg}` are resolved deterministically by the Wording Compiler using the fighter's `stance` (`orthodox` $\to$ `lead=left, rear=right`; `southpaw` $\to$ `lead=right, rear=left`) so the final prompt prints concrete `"left fist"` / `"right fist"` words.

```json
{
  "id": "jab",
  "class": "STRIKE.LINEAR",
  "aliases": ["jab", "lead straight", "left jab"],
  "caption_words": "snaps a crisp straight punch with the {lead_hand} fist",
  "limb": "lead_hand",
  "hinge": "shoulder_extension",
  "path": "straight",
  "level": "high",
  "contact": "strike",
  "pre": {
    "support": ["standing"],
    "coil": ["neutral", "loaded_rear", "recoiling_back"]
  },
  "post": {
    "support": "standing",
    "coil": "loaded_lead",
    "range_delta": "same"
  },
  "partner_pre": {
    "support": ["standing", "crouched"],
    "range": ["punch", "pocket"]
  },
  "partner_reaction_classes": [
    "IMPACT.REACTION",
    "BLOCK.PASSIVE",
    "BLOCK.ACTIVE",
    "EVADE.SLIP"
  ],
  "force_local": "forward_straight",
  "off_limbs": {
    "other_arm": "{rear_hand} fist tucked tight at the {rear_side} cheek in a high guard, both arms clearly separate from the torso",
    "lead_leg": "{lead_leg} foot planted forward",
    "rear_leg": "{rear_leg} heel raised, driving weight forward"
  },
  "regimes": ["standup_striking"],
  "styles": ["boxing", "muay_thai", "mma", "baki", "freestyle_sakuga"],
  "bleed_tier": 1,
  "min_frames_hypothesis": 6,
  "effort": {"weight": "light", "time": "sudden", "space": "direct", "flow": "bound"},
  "probe": {}
}
```

### 4.2 The 22 Canonical Classes
| # | Class ID | Example Move Cards | Support Change | Typical Range |
|---|---|---|---|---|
| 1 | `STRIKE.LINEAR` | `jab`, `cross`, `lead_body_jab`, `rear_body_straight`, `teep`, `spear_knee` | `none` | `punch` / `kick` |
| 2 | `STRIKE.ARC_HORIZ` | `lead_hook`, `lead_liver_hook`, `rear_hook`, `slashing_elbow`, `low_calf_kick`, `body_roundhouse`, `head_roundhouse`, `backfist` | `none` | `pocket` / `punch` / `kick` |
| 3 | `STRIKE.ARC_VERT` | `lead_uppercut`, `rear_uppercut`, `upward_elbow`, `rising_clinch_knee`, `axe_kick` | `none` | `pocket` / `clinch` / `kick` |
| 4 | `STRIKE.FULL_ROT` | `spinning_backfist`, `spinning_back_kick`, `spinning_heel_kick`, `tornado_kick` | `none` (`coil: spinning_*`) | `punch` / `kick` |
| 5 | `STRIKE.DOWNWARD` | `rear_overhand`, `hammerfist_chop`, `downward_elbow` | `none` | `punch` / `pocket` |
| 6 | `THROW.PROJECT` | `hip_throw`, `inside_trip`, `high_crotch_dump` | partner `clinched` $\to$ `supine` | `clinch` $\to$ `ground` |
| 7 | `TAKEDOWN.LEG` | `double_leg_shot`, `single_leg_pick` | `standing` $\to$ `kneeling`; partner $\to$ `supine` | `punch` $\to$ `ground` |
| 8 | `SWEEP.LOW_ROT` | `low_ankle_sweep`, `inside_foot_reap` | `crouched` $\to$ `crouched`; partner $\to$ `supine` | `pocket` / `kick` |
| 9 | `EVADE.SLIP` | `slip_outside`, `slip_inside`, `bob_and_weave`, `pull_back_lean` | `none` (`coil: loaded_lead/rear` or `level_low`) | `punch` / `pocket` |
| 10 | `EVADE.ROOT` | `back_step`, `l_step_pivot`, `outside_angle_step` | `none` (opens or shifts range) | `punch` $\to$ `kick` |
| 11 | `EVADE.LEVEL` | `level_duck`, `reactive_sprawl` | `standing` $\to$ `crouched` | `punch` / `pocket` |
| 12 | `BLOCK.PASSIVE` | `high_shell_guard`, `forearm_frame_absorb`, `body_elbow_tuck` | `none` (`coil: recoiling_back` or `loaded_*`) | `punch` / `pocket` |
| 13 | `BLOCK.ACTIVE` | `lead_palm_parry`, `rear_palm_parry`, `cross_wrist_trap`, `shin_check` | `none` | `punch` / `kick` |
| 14 | `GRAPPLE.ATTACH` | `single_collar_tie`, `double_collar_plum`, `over_under_clinch` | `standing` $\to$ `clinched` (both) | `pocket` $\to$ `clinch` |
| 15 | `GRAPPLE.MAINTAIN` | `clinch_off_balance_jerk`, `inside_bicep_control` | `clinched` $\to$ `clinched` | `clinch` |
| 16 | `GRAPPLE.RELEASE` | `two_hand_chest_shove`, `forearm_throat_frame_break` | `clinched` $\to$ `standing` (both) | `clinch` $\to$ `punch` |
| 17 | `LOCOMOTION.APPROACH` | `burst_step_in`, `pendulum_step_in`, `low_dart_lunge` | `none` (closes range 1 band) | `outside` $\to$ `kick` $\to$ `punch` |
| 18 | `LOCOMOTION.RETREAT` | `push_off_backstep`, `long_retreat_hop` | `none` (opens range 1 band) | `pocket` $\to$ `punch` $\to$ `kick` |
| 19 | `LOCOMOTION.CIRCLE` | `lateral_circle_lead`, `lateral_circle_rear` | `none` | `same` |
| 20 | `RECOVERY.STAND` | `technical_base_standup`, `kip_up_spring` | `supine`/`kneeling` $\to$ `standing` | `ground` $\to$ `kick` |
| 21 | `RECOVERY.RESET` | `guard_reset_breathe` | `any` $\to$ `standing`, `coil: neutral` | `same` |
| 22 | `IMPACT.REACTION` | `head_snap_rear`, `head_whip_lead`, `torso_fold_rib_hit`, `lead_leg_buckle`, `guard_skid_back`, `spin_from_blocked_hook`, `knockout_canvas_collapse` | varies by hit level | `same` or `open_one` |

---

## 5. Deterministic State Machines

### 5.1 Per-Fighter State (`FighterState`)
Tracked independently for Fighter `A` and Fighter `B`:
```python
{
  "id": "A",
  "stance": "orthodox",         # orthodox | southpaw
  "screen_side": "left",        # left | right (locked across clip unless explicit camera cross)
  "facing": "right",            # right | left
  "support": "standing",
  "coil": "neutral",
  "guard_lead": "high",
  "guard_rear": "high"
}
```
* **Transition Rule:** At beat $i$, `fighter.support` must be in `card.pre.support` and `fighter.coil` must be in `card.pre.coil` (else `V04`). After the beat, `fighter.support = card.post.support` and `fighter.coil = card.post.coil`.

### 5.2 Shared Dyad State & Coupling Rules (`DyadState`)
Tracked across the pair `{A, B}` so range and clinch states can never desync:
```python
{
  "range_band": "punch",        # outside | kick | punch | pocket | clinch | ground
  "clinch_engaged": False
}
```
At every contact beat (`strike` or `grapple`), the validator checks:
1. **Range Lock (`V05`):** Current `dyad.range_band` is inside `attacker_card.partner_pre.range`.
2. **Partner Posture Lock (`V05`):** Partner's `support` is inside `attacker_card.partner_pre.support`.
3. **Hit Level Lock (`V06`):** `attacker_card.level` (`low`, `mid`, `high`) equals `partner_reaction_card.level` (e.g., a `low` calf kick can never pair with `head_snap_rear`).
4. **Camera-Relative Force Direction Lock (`V07`):** Resolved `attacker_force_cam` equals resolved `partner_recoil_cam` (e.g., if `A` on `screen_left` throws a `lead_hook` driving `toward_screen_right` / `away_from_camera`, `B`'s head/torso reaction must move in that same direction, never opposite).
5. **Clinch Symmetry (`V08`):** `A.support == "clinched"` if and only if `B.support == "clinched"` and `dyad.range_band == "clinch"`.
6. **Paired Reaction (`V09`):** Every beat with `contact in ("strike", "grapple")` must have a simultaneous partner beat whose card `class` is in `attacker_card.partner_reaction_classes`.

### 5.3 Fluid Chaining (The Anti-Stiffness Rules)
1. **Continuous Coil Transfer (`V11`):** Within an active exchange, a fighter's next offensive/evasive move must accept the previous beat's `post.coil` in its `pre.coil` (the follow-through of Beat $N$ is the windup of Beat $N+1$).
2. **No Mid-Exchange Neutral Reset (`V10`):** `RECOVERY.RESET` (`coil -> neutral`) is legal only at clip boundaries or immediately after a `LOCOMOTION.RETREAT` / `GRAPPLE.RELEASE` that opens range to `kick` or `outside`. Using it inside a `pocket` or `punch` exchange triggers `V10 (stiffness warning)`.
3. **Simultaneous Slip-and-Counter (`overlaps`):** A fighter may execute an `EVADE.SLIP` or `BLOCK.ACTIVE` beat that carries `chains_immediately_into` or `overlaps` so defense and counter-load print as one fluid motion (`"slips outside the straight punch while coiling the left hip"`).
4. **Momentum Carry Within Regime Limits:** Riding a blocked strike or whiffed swing into a spin (`coil: spinning_cw/ccw`) is legal only if the resulting spinning move is allowed by the clip's `style`, `regime`, and `bleed_budget` (`V13`/`V14`).

---

## 6. Validator Codes (`V01–V17`)

| Code | Check Description | Severity |
|---|---|---|
| **V01** | Unknown `move_id` or invalid enum value in beat sheet or card | `error` |
| **V02** | Move is not allowed by the fighter's declared `style` | `error` |
| **V03** | Move's `regimes` does not match the clip's `regime` (except a single boundary `transition` move) | `error` |
| **V04** | Fighter's current `support` or `coil` is not in the move card's `pre` state | `error` |
| **V05** | Partner's `support` or shared `dyad.range_band` is not in the move card's `partner_pre` | `error` |
| **V06** | Attack `level` (`low`/`mid`/`high`) does not match partner reaction `level` | `error` |
| **V07** | Resolved camera-relative attack force direction and partner recoil direction conflict | `error` |
| **V08** | Asymmetric clinch state (`clinched` on one fighter only, or range not `clinch`) | `error` |
| **V09** | `strike` or `grapple` beat lacks a simultaneous partner beat from `partner_reaction_classes` | `error` |
| **V10** | Mid-exchange reset to `neutral` coil while still in `punch`, `pocket`, or `clinch` range (stiffness) | `warning` |
| **V11** | Coil chain break (next move's `pre.coil` does not accept previous beat's `post.coil`) | `warning` |
| **V12** | Beat duration (`frames`) is shorter than card's `min_frames_hypothesis` | `warning` |
| **V13** | Clip exceeds `bleed_tier == 3` budget from `config/thresholds.json` (hypothesis) | `warning` |
| **V14** | Two move classes listed as a quarantined pair in `ledgers/quarantined_pairs.json` share a clip | `error` |
| **V15** | Printed positive prompt contains a digit (`0-9`), metric unit (`m`, `deg`, `fps`), raw alias, franchise move name, or any move word belonging to an out-of-regime/forbidden card | `error` |
| **V16** | Fighter `A` and Fighter `B` swap `screen_side` (`left`/`right`) mid-clip | `error` |
| **V17** | One-sided demo warning: one fighter has zero offensive attempts (`strike` or `grapple`) across a multi-beat exchange | `warning` |

Every validator code `V01–V17` ships with at least one failing unit-test fixture and one passing unit-test fixture.

---

## 7. Clip Composer (`composer.py`)

1. **Single-Regime Clip Isolation:** Scans a full fight beat sheet and splits it into discrete clips at `regime` boundaries (`standup_striking` $\to$ `clinch` $\to$ `ground`), placing the `transition` move at the clip boundary.
2. **Deterministic Cross-Clip State Handshake:** Clip $N+1$ initializes its `FighterState` (`A` and `B`) and `DyadState` (`range_band`, `clinch_engaged`) directly from Clip $N$'s final beat state.
3. **Quarantine & Bleed-Budget Enforcement:** If a single-regime clip still violates `V13` (too many Tier-3 global moves) or `V14` (contains an empirically quarantined pair, e.g., a multi-hit boxing combo + a Tier-3 floor/aerial sweep), the composer proposes the exact beat index to split the clip into Clip $N$ and Clip $N+1$ rather than silently dropping beats.

---

## 8. Wording Compiler (`compiler.py` — 2-Layer Unrolled Fluid Stack / `gold_master_6` Format)

1. **Canonical Output Format (`gold_master_6` 2-Layer Unrolled Fluid Stack):**
   - Compiles validated beat sheets directly into the proven 3-section `gold_master_6` structure:
     1. **Top Style, Entity & Spacing Header** (`10s anime fight clip, 24fps... STYLE: Pure 2D hand-drawn anime... ENTITY COUNT & OUTFIT LOCK...`)
     2. **`=== LAYER 1: CONTINUOUS SUPPORT, FORCE-EVENT & PROP TIMELINE (Labanotation-as-Words) ===`** (`<seconds> <performer> (<frames>f): SUPPORT ... | L_arm:...; R_arm:... (both arms separate from the torso in silhouette); L_leg:...; R_leg:... | FE<N> <MOVE>: ...`)
     3. **`=== LAYER 2: SAKUGA-MLLM-3.1-CAUSAL KINEMATIC & CAMERA SCENE GRAPH ===`** (Complete `SAKUGA-MLLM-3.1-CAUSAL` JSON scene graph with `A_beats`, `B_track`, `camera`, `anime`, and `rules` that passes `scripts/sakuga_compiler.py lint` with `0 errors, 0 warnings`).
2. **Automatic Range-Band to 3D Coordinate Separation (Zero `0.2m` Body Merging):**
   - Automatically maps `dyad.range_band` to exact z-separation (`punch = 0.80m`, `pocket = 0.65m`, `kick = 1.10m`, `clinch = 0.58m`) alongside natural reach words (`"one full arm's length (0.80m)"`, `"half an arm's length (0.65m)"`, `"one full leg's length (1.10m)"`).
3. **Stance-Resolved Concrete Limbs & 4-Limb Occupancy:**
   - Replaces `{lead_hand}`, `{rear_hand}`, `{lead_leg}`, `{rear_leg}` with concrete `"left"` / `"right"` words based on each fighter's `stance` (`orthodox` vs. `southpaw`), and formats every beat's `limbs` field as `L_arm:...; R_arm:... (both arms separate from the torso in silhouette); L_leg:...; R_leg:...`.
4. **Zero Forbidden Words (`V15` Gate):**
   - Scans the compiled output to verify zero franchise attack names, zero positive-prompt `"no <move>"` lists in Layer 1/Header, and zero mentions of out-of-regime/out-of-style move aliases.

---

## 9. Repository Layout & Coexistence with `Movement_Prose`

We build this cleanly inside the existing GitHub repository (`/Users/king/.gemini/antigravity/scratch/Movement_Prose`) under a dedicated package `fight_move_system/` while keeping a synced copy of `PLAN.md` in `/Users/king/Downloads/fight-move-system/PLAN.md`:

```text
Movement_Prose/
├── AGENTS.md                         # Master onboarding & architecture index
├── docs/
│   └── FIGHT_MOVE_SYSTEM_PLAN.md     # Synced copy of this v2 Master Plan
├── fight_move_system/                # New v2 deterministic engine
│   ├── __init__.py
│   ├── enums.py                      # §3 Closed vocabularies
│   ├── lexicon.py                    # §4 Move Card loader & schema validator
│   ├── state.py                      # §5.1 & §5.3 Fighter state + fluid coil rules
│   ├── dyad.py                       # §5.2 Dyad coupling & camera-relative force resolver
│   ├── validator.py                  # §6 Validator (V01–V17)
│   ├── composer.py                   # §7 Clip composer & regime splitter
│   ├── compiler.py                   # §8 Natural caption wording compiler + V15 scanner
│   ├── cli.py                        # CLI: validate | compile | packet
│   ├── config/
│   │   └── thresholds.json           # §0.2 All thresholds marked hypothesis | calibrated
│   ├── ledgers/
│   │   ├── word_probes.json          # §10 Per-model move probe verdicts
│   │   └── quarantined_pairs.json    # §10 Empirically proven bleed pairs
│   ├── lexicon_data/
│   │   └── boxing_v1.json            # M1: ~25 core boxing & standup defense/reaction cards
│   └── fixtures/
│       ├── pass/                     # Passing fixtures for V01–V17 + 10-beat boxing exchange
│       └── fail/                     # Failing fixtures triggering each code V01–V17
└── tests/
    └── test_fight_move_system.py     # Automated pytest/unittest suite covering M1–M4
```

---

## 10. Evidence Program (Owner Renders; Agent Prepares Packets)

Every hypothesis starts as `status: "untested"` in `config/thresholds.json`.

| ID | Hypothesis | Controlled A/B Test Packet | Pass Criterion |
|---|---|---|---|
| **H1** | Plain body-shape caption words beat martial-arts / franchise names | Same move, two wordings, 3 renders each | Caption wording renders the intended body mechanics more reliably |
| **H2** | Tier-3 global words (`sweep`, `scissor`, `kip-up`) leak into Tier-1 hand combos | 3-punch combo clip with vs. without one Tier-3 beat later in the clip | Leak rate into the punch combo is higher when the Tier-3 beat is present |
| **H3** | Attention bleed reaches earlier timestamps in the clip | Same packet as H2; log timestamp where leg/aerial motion appears | Leak appears during the earlier punch beats |
| **H4** | Locked/slow camera on Tier-3 moves renders cleaner than fast whip-pan camera | Same Tier-3 move with locked medium-wide camera vs. fast orbit/whip camera | Locked camera preserves limb anatomy cleaner |
| **H5** | 4-limb occupancy text on strike beats fixes the `:03` missing/merged-arm bug | Strike beat with `off_limbs` guard text vs. striking limb only | Fewer missing or torso-merged off-arms |
| **H6** | Coil-chained beats (`V10`/`V11` clean) read more fluidly than reset-to-neutral beats | Same 4-hit exchange written with coil carry vs. neutral resets between hits | Coil-chained render judged more fluid and continuous |
| **H7** | Minimum beat frame thresholds (`V12`) prevent multi-hit move merging | 3-hit combo at short beat durations vs. `min_frames_hypothesis` durations | Distinct punches survive without mushing into one blur |

---

## 11. Milestones & Acceptance Criteria

| Milestone | Scope | Done When |
|---|---|---|
| **M1** | `enums.py` (§3), `lexicon.py` (§4.1), `boxing_v1.json` (~25 cards), `state.py` (§5.1), `V01–V04`, `V10–V12` | Every card validates; every code (`V01–V04`, `V10–V12`) has passing + failing fixtures; test suite 100% green |
| **M2** | `dyad.py` (§5.2), `V05–V09`, `V16–V17`, simultaneous `overlaps` (§5.3), full 10-beat competitive boxing exchange fixture | 10-beat competitive boxing exchange passes with 0 errors/warnings; every injected error triggers its exact `V` code |
| **M3** | `composer.py` (§7), `V13–V14`, `compiler.py` (§8), `V15` scanner, CLI (`validate`, `compile`) | Boxing beat sheet compiles to a clean caption prompt with zero digits, zero forbidden words, 4-limb key beats, and byte-identical deterministic output |
| **M4** | Render Packet Generator (`cli.py packet`) for `H1`, `H5`, `H6` + initial boxing word probes | Ready-to-paste render packet generated in `fight_move_system/packets/` with 1-line owner evaluation instructions per prompt; zero paid calls made by agent |
| **M5** | Expand lexicon: `muay_thai_clinch_v1.json` (elbows, knees, teeps, calf kicks, sweeps, plum clinch), then `mma_grappling_v1.json`, then `aerial_sakuga_v1.json` | All families validated with pass/fail fixtures and regime split tests |
| **M6** | Render packets for `H2`, `H3`, `H4`, `H7` + Ledger calibration workflow | Owner render verdicts ingested into `ledgers/`; calibrated rules updated strictly from render evidence |

---

## 12. Owner Decisions & Active Defaults (`DRAFT` Until Owner Overrides)

1. **Target video model(s) for probes:** `seedance_2_0` (default primary target).
2. **First style to build & probe:** `boxing` (`baki` / grounded bare-knuckle standup compatible).
3. **Render budget per milestone:** Owner runs renders at their discretion from generated packets.
4. **Target clip duration:** `10s` per clip.
5. **Time representation in compiled prompt:** `words` (*"an instant later"*, *"at the same moment"*) — `DRAFT` until `H1/H7` comparison.
6. **Camera rule `H4` (force slow/locked camera on Tier-3 moves):** `off` by default until `H4` packet is tested.
7. **Visual Style Pack default:** `sakuga_2d` (high-contrast 2D anime linework, single-limb motion smear, brief impact hold phrasing; switchable to `live_action`).
