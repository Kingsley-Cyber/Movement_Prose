yea good call, what would happend if we added casual grpah or does it already have it? 
for example

# What Makes This Prompt Exceptionally Good for Fast-Paced Anime Combat

This is a **causal physics specification disguised as a video prompt** — and that's exactly why it works. Here's what it does brilliantly:

---

## 1. It Replaces "Poses" With a Causal Graph

Most action prompts describe a *sequence of poses*: "A punches, B blocks, A kicks." The model then renders each beat semi-independently, producing the classic AI failure mode — **floaty, disconnected animation** where nothing inherits force from anything.

This prompt instead defines **C01 → C23**, where every event explicitly names its `requires` and `causes`. For example:

> `C09: B_right_hook_accelerates — requires: C08 (hip rotation) — causes: C10`

The renderer can't skip the hip rotation and jump to the hook, because the hook *has no valid precursor state* without it. **Choreography becomes a dependency graph, not a storyboard.** That's the single biggest upgrade here.

---

## 2. It Encodes Conservation Laws That Kill the Usual AI Cheats

The `conservation_laws` block is essentially a **list of physics bugs to forbid**:

| Law | Kills the failure mode... |
|---|---|
| `airborne_state_requires_prior_launch_impulse` | Characters floating into jumps |
| `knockback_requires_force_transfer` | Targets flying before being hit |
| `reaction_requires_contact_or_explicit_evasion` | Flinching at nothing |
| `reversal_requires_redirecting_force` | Mid-air direction changes |
| `body_rotation_requires_prior_torque` | Spontaneous spins |
| `explosive_launch_requires_grounded_support` | Groundless power moves |

Notice `C16: A_rotation_redirected — preserves: angular_momentum`. The prompt explicitly says the block *redirects* the spin rather than stopping it — exactly how real sakuga handles a blocked aerial. That's a sophisticated touch most prompts miss.

---

## 3. The `contact_contract` Is a Masterclass in Impact Timing

Shot 04's contact block is the best part for fight choreography:

```
pre_contact:   A_reaction: NONE
at_contact:    B.right_palm ∩ A.torso
post_contact:  A_torso: compress → A_COM: accelerate_backward → B_arm: follow_through
hard_rule:     NO_KNOCKBACK_BEFORE_C19
```

This enforces the **"no reaction before contact"** rule that separates good impact animation from bad. The explicit `follow_through` on B's arm is also key — most AI renders freeze the attacker at the moment of contact. Real sakuga *follows through*. The `compress → accelerate` ordering on the victim mirrors actual squash-and-stretch impact frames.

---

## 4. It Uses "Graph Transitions" Instead of Descriptions

Each shot defines `before` / `after` (and sometimes `intermediate` / `contact`) as **relational tuples**:

```
before: [A, DISTANCE_TO, B, 3.5m]
after:  [A, DISTANCE_TO, B, 0.8m], [B.left_forearm, CONTACT_WITH, A.right_wrist]
```

This forces the model to **interpolate a continuous path** between two verified states rather than invent a pose. The `spatial_continuity: teleportation FORBIDDEN` law backs it up. This is how you get readable approach distances and clean parry contacts instead of fighters teleporting into range.

---

## 5. Camera Rules That Protect Screen Geometry

The `screen_geometry` law is subtle but crucial for fast fights:

> `A_remains_visual_left_until_physical_cross` · `camera_cannot_mirror_fighters` · `screen_direction_change_requires_visible_crossing`

Fast choreography constantly breaks spatial coherence — fighters swap sides, the camera flips, and the viewer loses track of who's where. This prompt **locks the axis** and requires a *visible physical crossing* to change it. Combined with per-shot camera moves (`TRACK_RIGHT`, `ORBIT_CLOCKWISE 25°`, `TRACK_AND_TILT_UP`, `PUSH_IN`, `FAST_PULL_BACK`), each shot has a distinct but **axis-preserving** camera language. The orbit is capped at 25° — enough for dynamism, not enough to disorient.

---

## 6. The `invalid_states` List Is a Negative-Prompt Goldmine

```
- reaction_without_cause        - knockback_before_contact
- airborne_without_launch       - direction_change_without_force
- spontaneous_rotation          - floating / teleportation
- mirrored_screen_positions     - identity_swap / costume_mutation
- duplicated_limbs              - static_punch_exchange
- energy_blasts / aura_charge   - fighting_game_side_view
- disconnected_camera_motion
```

Two things stand out:
- **`energy_blasts` and `aura_charge` are explicitly banned** — this is a *pure physical* fight, no shonen shortcuts. That's a deliberate aesthetic choice (2016 sakuga realism).
- **`fighting_game_side_view`** is banned — the prompt wants cinematic camera language, not a 2D fighter plane. This is the difference between *anime fight* and *game footage*.

---

## 7. "Semantic Physics" Bridges Text and Animation Principles

The phrase `CONSERVE_SEMANTICALLY` is clever: it doesn't demand literal Newtonian simulation, it demands **animator-legible causality** — the thing sakuga artists actually do. The `physics_emphasis` on Shot 03 reads like notes to a key animator:

> `visible_launch_impulse · continuous_rotation · block_changes_rotation · no_midair_direction_change_without_contact`

That last one is the rule that makes spinning kicks read as *weighted* rather than *floaty*.

---

## 8. It Distinguishes Timing From Contact

`C10: A_ducks_under_hook — timing: BEFORE_C09_INTERSECTION`. The evasion is specified as happening *before the punch's intersection point*, not "after the punch is thrown." This encodes the **anticipation window** that makes a dodge look skilled rather than lucky. Fast fights live or die on this kind of sub-beat timing, and almost no other prompt format captures it.

---

## 9. The Render Intent Sets Animation Language, Not Just Style

```
spacing: dynamic · smear_frames: selective · impact_frames: brief
secondary_motion: clothing, hair, dust
```

`selective` smear frames and `brief` impact frames are **actual sakuga vocabulary**. Combined with `weight: HEAVY` and `acceleration: SHARP`, this tells the model *how* to distort time — smears on the fastest limbs only, one-or-two-frame impacts, heavy follow-through. That's how you get punchy 2016-era TV anime action instead of either mushy interpolation or hyper-smooth 60fps.

---

## 10. The Final Instruction Reframes the Whole Task

> *"Render the sequence as one physically continuous combat event. Do not interpret beats as independent poses. Each state must emerge visibly from the previous state."*

This is the thesis statement. It tells the model the **unit of generation is the causal chain, not the shot**. Shots are just camera windows onto one continuous event. That single reframe is what prevents the "five disconnected clips stitched together" feel that plagues AI action video.

---

## Summary: The Core Insight

**Most action prompts specify *what happens*. This one specifies *why each thing is allowed to happen*.**

By making every visual consequence depend on an explicit cause, capping camera motion, locking the screen axis, banning reaction-before-contact and motion-without-force, and giving the renderer animator-grade vocabulary (smears, follow-through, squash, redirect-not-stop), it converts a 10-second fight into a **constraint-satisfaction problem with a unique physically-valid solution**. That's why it would produce coherent, weighty, readable high-speed choreography instead of the usual floaty AI mush.
