# BLOCK Fight Simulator v2: Complete Design Specification (Card-Driven Simulation, Kicking, Grappling, Slots, Exchange Math & Damage Model)

- **Status:** Captured Design Specification & Implementation Backlog
- **Date:** 2026-10-24
- **Target Modules:** `engine/fight_director.py`, `engine/fight_state.py`, `engine/probability.py`, `engine/choreography.py`, `engine/prompt_compiler.py`, `fight_move_system/block_bridge.py`, `data/techniques.json`, `data/debt_registry.json`, `data/combinations.json`, `data/model.json`, `schemas/fighter_card.schema.json`
- **Core Compatibility Constraint:** Build alongside the existing v1 planner so all existing cards (`cards/*.json`), data, and the existing 106/107 tests remain 100% intact.

---

## 1. Current v1 Simulation Gaps (Verified Against `engine/`)

1. **No Real Fight Clock (`engine/fight_director.py:242`):** Fight length is divided evenly across events (`duration * i / len(build.events)`), so a feint takes as long as a takedown, and a 45s fight is just the same events spread thinner.
2. **Space Is a 1D Line (`data/model.json` & `engine/fight_state.py`):** Distance is 5 fixed bands (`clinch 0.45m`, `close 0.7m`, `punch 1.05m`, `kick 1.65m`, `outside 2.4m`), `arena_half_width_m = 3.0`, and `wall_proximity` stays `"far"` by default. There is no circling, no corners, no cutting off the ring, and ring/cage/street behave identically.
3. **Fighters Never Leave the Ground:** `fight_state.py` has no `airborne` posture/support state and no way to grant trained jumping knees, flying entries, or spinning kicks.
4. **Hardcoded 10-Phase Script & Move Repetition (`engine/fight_director.py:140-236`):** Every fight opens with a `jab` (`line 146`), selects the first alphabetically sorted weakness move (`line 113`), and repeats `tid = main` in a `while` loop (`lines 213-230`). Defenses (`line 74`) are cosmetic because `landed=True` is hardcoded (`line 57`).
5. **Slots Are Reduced to a Flat `+0.15` Bonus (`engine/probability.py:27`):** `slot_logit_per_net_slot = 0.15` treats slots as a static number rather than tactical gameplans (`Plan A -> Plan B -> Plan C`) that fighters switch between.
6. **Flat `+1` Contact Mark Damage (`engine/fight_state.py:144`) & Ignored State Feedback:** Every landed hit adds `+1` to `b["damage"][region]` regardless of whether Rook Mercer (planted slugger) throws a haymaker or an out-boxer throws a jab, and accumulated damage/fatigue never feeds back into move selection or defense.
7. **Video Hand-Off Erases Fighter Identity (`fight_move_system/block_bridge.py` & `engine/prompt_compiler.py`):** Hardcodes fighter descriptions, `ufc_mma_octagon` style tags, and a fixed wide two-shot camera instead of driving visual grammar from the fighter card.

---

## 2. Core System 1: Give Every Card Dimension a Job in the Simulation

Without adding physical height/reach/speed stats, character archetypes ("bruiser", "counter-fighter", "slickster", "clincher") emerge qualitatively from how all **8 card dimensions** interact on every exchange:

| Dimension | What It Decides in the Simulation |
| :--- | :--- |
| **`mentality`** | **The fight's shape and initiative:**<br>- `counter`: waits for the opponent to commit first, then fires into their recovery seam with a counter bonus.<br>- `swarmer`: makes repeated short entries with short reset gaps, pushing the opponent toward the wall.<br>- `slugger`: slower buildup, throws fewer/heavier shots, sticks stubbornly to their primary plan.<br>- `outboxer`: circles, exits at angles (`pivot`), and resets to long range.<br>- `spoiler`: ties up in `clinch`, smothers, and breaks rhythm.<br>- `boxer_puncher` / `technician`: balanced reads, chains combinations, switches slot plans rapidly when stymied.<br>- `defensive`: prioritizes shell/frame integrity and attrition. |
| **`tempo`** | Who initiates first, how long fighters reset between exchanges, how many exchanges occur per minute, and how fast `fatigue` builds. |
| **`defense`** | Which active defensive response triggers when attacked (`slip`, `parry`, `shell_block`, `shield_frame`, `check`, `sprawl`, `smother`, `outfight_step_back`, `kick_catch`) and how damage is mitigated or reflected. |
| **`hands`** | What the guard covers and leaves open (`head_coverage`, `body_coverage`, `vision`, `counter_readiness` 1–5 ratings), determining which attack lanes are blocked vs. exposed. |
| **`target`** | Which anatomical level (`head_hunter`, `body_puncher`, `knee_clincher`, `leg_chopper`, `mixer`) the fighter prioritizes and gets specialty damage bonuses on. |
| **`kicking`** | Which kick family the fighter uses (`muay_thai`, `dutch`, `karate`, `sanda`, `wrestler_teep`, `none`) and whether they can catch or check kicks. |
| **`stance`** | How the fighter enters and exits range (`planted` roots feet for heavy power; `crouch` loads short hooks/uppercuts; `shuffle` / `bladed` darts in and out; `switch` changes lead lines via `Uno`). |
| **`tie`** | What positions and grips the fighter hunts when close (`thai_plum`, `greco`, `freestyle`, `bjj`, `wall_boxing`, `anti_grappling`, or `null` untrained attachment). |

---

## 3. Core System 2: Fight Clock, Arena Geometry & Verticality Modes

### 3.1 Real Fight Clock (`24fps` Frame Costs)
- **Per-Technique Frame Costs:** Every technique in `data/techniques.json` has frame costs for `setup_frames`, `strike_frames`, `contact_hold_frames`, and `recovery_frames` (e.g., `jab` is fast; `spinning_back_kick` has longer recovery; `double_leg` and ground control spend real seconds on the mat).
- **Rhythm Between Exchanges:** Determined by `tempo` + `mentality` (long reads + sudden bursts for `counter`; short gaps for `swarmer`; slow load + heavy shot for `slugger`).
- **Fatigue Scaling:** Accumulated `fatigue` stretches `recovery_frames` and widens defensive exposure windows as the fight progresses.
- **Set Duration & Rounds:** Run fights for a set clock (`30s`, `60s`, `90s`, or `3 rounds`), terminating on KO/TKO (regional damage limit), submission completion, or time-expired decision.

### 3.2 2D Arena Geometry Presets
- **Arena Presets (`data/model.json`):**
  - `ring`: Square with 4 corners and ropes (corners trap circular footwork).
  - `cage`: Octagon walls (unlocks wall-pinning, wall-walks, and cage-plum abilities like `maleek.cage_plum`).
  - `open_floor`: No walls (out-boxers cannot be cornered; wall-gated abilities remain locked).
  - `narrow_alley`: Close parallel walls on both sides (restricts lateral circling and wide spinning kicks).
  - `rooftop_edge`: Drop hazard on one boundary.
  - `dojo` / `courtyard`: Traditional hard surface with optional architectural obstacles/pillars.
- **True 2D Positions & Facing (`[x, y]` & `[fx, fy]`):** Out-boxers circle laterally (`pivot`), pressure fighters cut off the ring and drive opponents to the boundary (`wall_proximity -> "near"`), and distance bands (`clinch`, `close`, `punch`, `kick`, `outside`) are computed dynamically from $\|(x_A - x_B, y_A - y_B)\|_2$.

### 3.3 Verticality Modes (`Grounded` / `Athletic` / `Aerial`)
- **Fight-Level Vertical Setting:**
  1. `grounded`: Feet on floor or mat only.
  2. `athletic`: Short hops, jumping knees, superman punches, flying entries.
  3. `aerial`: Full anime elevation and airborne exchanges.
- **Card Capability Gate:** Even in `athletic` or `aerial` mode, a fighter can only leave the ground if their card grants an airborne capability (a 1-slot `Brawler` stays grounded even in `aerial` mode).
- **3-Phase Jump Vulnerability (`takeoff -> peak -> landing`):** The `landing` phase has an extended recovery window that leaves a missed or blocked jumper open to a high-damage counter.

---

## 4. Core System 3: Kicking as a First-Class Subsystem

1. **Kick Families by `kicking` Dimension:**
   - `kicking.muay_thai`: Heavy rear round kicks (`low_kick`, `body_kick`, `head_kick`) that turn all the way through (higher single-leg exposure on miss/check), `teep`, and clinch knees (`knee_body`, `jumping_knee`).
   - `kicking.dutch`: Punch combinations (`jab -> cross -> hook`) ending in a heavy `low_kick` or `switch_kick`.
   - `kicking.karate`: Chambered straight-line kicks (`front_kick`, `side_kick`, `back_kick`) often off the lead leg, plus `spinning_back_kick` and `axe_kick` when vertical mode allows.
   - `kicking.sanda`: Specializes in `kick_catch` followed immediately by a standing-leg sweep/dump (`outside_trip` / `sanda_sweep`).
   - `kicking.wrestler_teep`: Short `teep` to the hip/sternum to freeze the opponent and set up a level-change takedown (`double_leg` / `single_leg`).
   - `kicking.none`: Never kicks; receives a bonus to closing distance (`step`) against kickers during kick recovery.
2. **Unrolled Kick Phase Data (`data/techniques.json`):**
   - `kicking_leg`: `"lead"` | `"rear"` | `"switch"` (derived from fighter's current `orientation`: `orthodox` vs. `southpaw`).
   - `chamber`: knee height and windup frames (`low_snap`, `high_tight_chamber`, `hip_whip_no_chamber`).
   - `support_foot`: pivot angle (`45deg`, `90deg`, `180deg_heel_turn`) and `ball_of_foot_rise`.
   - `path` & `target_region`: `"round_arc"` | `"linear_thrust"` | `"vertical_axe"` | `"spinning_back"` $\to$ `"leg"` | `"body"` | `"head"`.
   - `striking_surface`: `"lower_shin"` | `"instep"` | `"ball_of_foot"` | `"heel"` | `"blade_of_foot"` | `"kneecap"`.
   - `ending`: `"snap_back_to_stance"` | `"carry_through_spin"` | `"step_down_stance_switch"`.
3. **School-Specific Kick Defenses:**
   - `defense.check_frame`: **Shin Check (`check`)** — blocks `low_kick`/`body_kick` and inflicts recoil leg damage back onto the **kicker's** kicking leg!
   - `kicking.sanda` / `defense.parry_catch`: **Kick Catch (`kick_catch`)** — traps the kicking leg (`grip = "caught_leg"`), enabling a sweep, dump, or straight counter while the kicker hops on one foot.
   - `defense.outfight`: **Step Back (`evade_step_back`)** — pulls out of `kick` range so round kicks whiff, leaving the kicker in single-leg recovery.
   - `defense.slip_roll`: **Lean Back (`lean_back`)** — evades `head_kick` cleanly, but remains vulnerable to `low_kick` and `body_kick`.
   - `defense.sprawl_pummel` / `defense.smother`: **Jam (`jam_step`)** — steps inside the chamber of a `teep` or `body_kick` to crowd the kicker into `close`/`clinch` range.
4. **Cumulative Kick Wear & Adaptation:**
   - Accumulated `leg` damage reduces movement speed, penalizes `switch_step`/`pivot`, weakens kicks from that leg, and forces an involuntary stance switch (`orthodox <-> southpaw`) to hide a battered lead leg.
   - A kicker whose kicks are repeatedly checked (`check`) or caught (`kick_catch`) dynamically reduces kick frequency or switches slots.

---

## 5. Core System 4: Grappling as a Position & Grip Map (`data/positions.json`)

1. **Explicit Grappling Position Graph:**
   - **Standing (`posture: "standing"`):** `neutral`, `standing_back_take`, `caught_single_leg`.
   - **Clinch (`range: "clinch"`):** `collar_tie`, `thai_plum`, `over_under`, `double_underhooks`, `front_body_lock`, `rear_body_lock`, `wall_pinned`.
   - **Takedown in Progress (`posture: "transition"`):** `shot_in`, `single_leg_lifted`, `double_leg_drive`, `trip_reap`, `hip_throw`, `caught_kick_dump`.
   - **Ground (`posture: "ground"`, `range: "ground"`):** `closed_guard`, `open_guard`, `half_guard`, `side_control`, `mount`, `back_control`, `turtle`, `north_south`, `front_headlock`.
2. **Tracked Sub-Grips & Hand-Fighting:**
   - Track `underhooks` (`0, 1, 2`), `wrist_control` (`True/False`), and `head_position` (`inside` / `outside` / `trapped`) per fighter so hand-fighting micro-contests gate takedowns, knees, and wall pins.
3. **Scrambles:**
   - When a takedown or sweep is partially defended (e.g., `whizzer` or late `sprawl`), both fighters enter a `scramble` state resolved by `tie` capability, `stance` balance, and current `fatigue`.
4. **3-Stage Submissions (`isolate_limb -> lock_hold -> finish`):**
   - Submissions (`armbar`, `rear_naked_choke`, `guillotine`, `kimura`) progress through 3 stages across clock ticks, giving the defender a card-appropriate escape check (`posture_up`, `peel_grip`, `hitchhiker_escape`, `wall_walk`) at each stage.

---

## 6. Core System 5: Slots as Tactical Gameplans & Depth-vs-Breadth Scaling

Instead of a flat `+0.15` bonus, each entry in `synchronized_capabilities` becomes an executable **Slot Plan**:

1. **Slot Plan Structure (`schemas/fighter_card.schema.json`):**
   - `id` & `capabilities`: The trained capability bundle (e.g., `maleek.slot.1: ["boxing", "shield"]`).
   - `sequence`: Preferred move chain (e.g., `["shield_frame", "jab", "cross", "body_hook"]`).
   - `trigger`: Condition that activates this slot (`"fight_start"`, `"opponent_kicks"`, `"near_wall"`, `"slot_stalled"`, `"leg_damaged"`).
   - `home_range`: Target range band (`"punch"`, `"kick"`, `"clinch"`, `"ground"`).
   - `goal`: `"head_damage"` | `"leg_attrition"` | `"body_fatigue"` | `"takedown_control"` | `"counter_trap"`.
   - `abandon_rule`: When to switch away (e.g., `consecutive_failures >= 2` or `countered_cleanly >= 2`).
   - `links`: Next slot ID to transition into when abandoned or when its setup succeeds.
2. **Slot Count Archetypes & Depth-vs-Breadth Rule (Anti-Slot-Gaming):**
   - **Brawler (`1 slot`):** Has only Plan A (`depth_multiplier = 1.15`). Hits hardest and executes Plan A at peak sharpness, but cannot switch plans if the opponent solves it.
   - **Two-Piece (`2 slots`):** Plan A + Plan B (`depth_multiplier = 1.05`). Switches to Plan B when Plan A is shut down.
   - **Triad (`3 slots`):** Can switch plans twice and shift the fight across ranges (`depth_multiplier = 1.00`).
   - **Anomaly (`4 slots`):** Can blend and chain across all 4 plans mid-exchange (`depth_multiplier = 0.95` per individual plan, trading raw single-note power for maximum adaptability).

---

## 7. Core System 6: Card-Derived Damage Formula & 3-Level Exchange Calculator

### 7.1 Qualitative Card-Derived Damage Formula (`No Physical Size/Speed Stats`)

$$\text{Damage}(e) = \text{Base}(t) \times M_{\text{attacker}}(\text{card}_A, t, \text{state}) \times M_{\text{landing}}(\text{outcome}, \text{setup}, \text{state}) \times M_{\text{defender}}(\text{card}_B, t, \text{state})$$

1. **Move Base Damage & Type (`data/techniques.json`):**
   - **Base Scale:** `jab = 1.0`, `teep = 1.2`, `cross = 2.0`, `low_kick = 2.2`, `body_hook = 2.3`, `hook = 2.5`, `body_kick = 2.6`, `uppercut = 2.7`, `knee_body = 2.8`, `haymaker = 3.2`, `spinning_back_kick = 3.3`, `head_kick = 3.5`, `jumping_knee = 3.6`.
   - **Damage Type:** `impact` (stun/knockdown risk), `buildup` (cumulative leg/body wear), `stamina_drain` (spikes target `fatigue`), `cut` (vision penalty).
2. **Attacker Build Multiplier ($M_{\text{attacker}}$):**
   - **Mentality:** `slugger` (`1.30x` power, `-0.12` accuracy), `pressure` (`1.15x` power), `boxer_puncher` (`1.10x`), `counter` (`0.95x` base, **`1.45x` on counter-hit**), `swarmer` (`0.88x` per shot, higher volume), `outboxer` / `spoiler` (`0.90x` power, `+0.10` accuracy/control).
   - **Stance:** `planted` (`1.20x` punch power), `crouch` (`1.15x` on hooks/uppercuts), `balanced` (`1.00x`), `switch` (`1.10x` after `switch_step`), `bladed` / `shuffle` (`0.90x` power, `+range/evasion`).
   - **Kicking School:** `muay_thai` (`1.25x` on shin round kicks & knees), `dutch` (`1.20x` on `low_kick` finishing a punch combo), `karate` (`1.15x` on linear/spinning kicks).
   - **Target Specialty:** `+15%` damage when move's `target_region` matches `card.dimensions.target` (`head_hunter -> head`, `body_puncher -> body`, `knee_clincher -> clinch body/head`).
   - **Active Slot Alignment:** `1.00x` × `depth_multiplier` when move belongs to active slot; `0.80x` when improvising outside active slot.
3. **Landing Quality Multiplier ($M_{\text{landing}}$):**
   - `miss / evaded`: `0.0x`
   - `blocked`: `0.15x` (chip damage to guard/arms; or reflected shin damage on `check`)
   - `partial / glancing`: `0.50x`
   - `clean`: `1.00x`
   - `counter_hit` (defender caught mid-execution/recovery): `1.40x`
   - `flush` (clean hit after `feint`, `pivot`, or `switch_step` setup against an exposed seam): `1.65x` + knockdown check.
   - **State Modifiers:** Defender `wall_proximity == "near"` adds `1.15x` (cannot roll/retreat); attacker `fatigue` or damaged kicking leg reduces power by up to `-30%`.
4. **Defender Build Mitigation ($M_{\text{defender}}$):**
   - **Hands Coverage Rating (`1–5` in `data/engine_index.json`):** High `head_coverage` (e.g., `helmet`, `high_guard`, `shield52`) or `body_coverage` (`philly_shell`, `check_frame`) scales down incoming damage on covered lines (`1.15 - 0.08 * coverage_rating`).
   - **Defense Dimension:** `block_absorb` converts `30%` of head impact into reduced arm/body wear; `check_frame` reflects `40%` of `low_kick` damage back onto the kicker's leg; `slip_roll` downgrades `clean` head punches to `partial` or `miss`.
   - **Compounding Wear:** Each existing point of regional damage in `head`, `body`, or `leg` increases subsequent damage to that region by `+6%`, making body and leg work pay off late in the fight.

### 7.2 The 3-Level Fight Calculation Pipeline
- **Level 1 (`Pre-Fight Read`):** Rebalanced analytical matchup preview (`engine/probability.py`).
- **Level 2 (`Exchange-by-Exchange Resolver`):** At each clock tick, scores candidate moves from the active slot, resolves attacker lane vs. defender `defense`/`hands` + setup bonuses + state modifiers + **Read Penalty** (repeated moves get read and countered), rolls the seeded outcome (`miss`, `blocked`, `partial`, `clean`, `counter_hit`, `caught`, `flush`), applies the Card-Derived Damage Formula, and updates `fight_state`.
- **Level 3 (`Monte Carlo Many-Runs Simulator & Director Mode`):** Runs $N$ seeded simulations (e.g., `100`–`1,000` runs) to compute empirical win %, method-of-victory breakdown (`KO/TKO`, `Submission`, `Decision`), average fight duration, and dominant slot paths. **Director Mode** selects the highest-probability realistic run where the chosen fighter wins rather than forcing artificial moves.

---

## 8. Implementation Build Order (For Next Simulator Session)

- [ ] **Phase 1 — Card-Derived Damage & Exchange Resolver (`engine/exchange_resolver.py`, `engine/fight_state.py`, `data/model.json`):** Implement the 4-factor damage formula, real defensive outcomes (`miss`, `blocked`, `partial`, `clean`, `counter_hit`, `caught`, `flush`), read-memory penalty, and regional damage feedback (`Rook Mercer` vs. `Darius Reed` cross test).
- [ ] **Phase 2 — Slot Gameplans, Mentality Rhythm & Fight Clock (`engine/fight_director_v2.py`):** Implement frame-based fight clock, slot triggers/abandon rules/links, depth-vs-breadth scaling, and mentality-driven initiative.
- [ ] **Phase 3 — Kicking Subsystem & Grappling Position Map (`data/techniques.json`, `data/positions.json`, `data/debt_registry.json`):** Add unrolled kick phases, new kicks (`head_kick`, `switch_kick`, `spinning_back_kick`, `axe_kick`, `jumping_knee`), kick defenses (`kick_catch`, `lean_back`, `jam_step`), and the grappling position/grip graph.
- [ ] **Phase 4 — 2D Arena Geometry, Vertical Modes & Many-Runs Simulator (`engine/simulator.py`):** Add arena presets (`ring`, `cage`, `open_floor`, `alley`, `rooftop`, `dojo`), verticality modes (`grounded`, `athletic`, `aerial`), and the Monte Carlo multi-seed runner + Director Mode selector.
