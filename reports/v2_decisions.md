# BLOCK Fight Simulator v2.1 — Owner Decisions Log (`v2_decisions.md`)

Base commit: `0d0734d` (`exp/latent-sakuga-causal-readability` / `main`)
Recorded in Phase: **P0**

---

## 1. Confirmed Owner Decisions

### D1 — Canonical Mio (`cards/v2/sanda_judo.json`)
- **Decision:** Keep the current card dimensions exactly as they are (`orthodox`, `tempo 3`, `defense.parry_catch`).
- **Canonical Name:** `"Mio Tsukihara"`, which the card and code already use. Updated `README.md` and `docs/BLOCK_SIMULATOR_V2_DESIGN_SPEC.md` (which previously said `"Mio Takahashi"`).

### D2 — Default Fight Length and Rounds
- **Quick runs:** `60 s`, single round (`1 × 60 s`). Stays the default for `simulate_fight.py`, the test suite, the golden snapshots, and the 200-seed balance audit.
- **Full-fight audits:** Each ruleset's defaults from §8.5:
  - `mma`: `3 × 300 s` (3 × 5 min, 60 s rest)
  - `boxing`: `3 × 180 s` (3 × 3 min, 60 s rest)
  - `kickboxing`: `3 × 180 s` (3 × 3 min, 60 s rest)
  - `muay_thai`: `5 × 180 s` (5 × 3 min, 60 s rest)
  - `lethwei`: `5 × 180 s` (5 × 3 min, 60 s rest)
  - `street`: `1 × 120 s` (1 × 2 min, 0 s rest)
  Used for the win-method check (D4, §10.6), finishes/decisions/rounds evaluations, and the rank recalibration in P13.
- **CLI (`simulate_fight.py`):** Keep `--duration`. Add `--full-fight` (uses ruleset defaults) and `--rounds` / `--round-length` / `--rest` overrides.
- **Verification & Audit Scripts:**
  - `scripts/verify_v2.sh` runs quick runs only.
  - `scripts/audit_v2.sh` runs both quick runs and full-fight runs and reports them side by side.

### D9 — Six Loosened Test Thresholds from `6e59faa` (§3.5)
- **Decision:** Accept the current thresholds in `tests/test_simulator_v2_and_atomic_compiler.py` as they are. Do **not** restore the pre-`6e59faa` values and do **not** edit the tests. Treat these six assertions as strict tripwires: if any later phase would push any of these six below its current threshold, **stop and report to the owner** instead of changing anything.
- **Measured Baseline Values at `0d0734d`:**

| Test Metric | Measured Value (`0d0734d`) | Pre-`6e59faa` Threshold | Current Threshold (Locked Tripwire) |
|---|---|---|---|
| Niran's fresh leg readiness (`r_fresh["leg"]`) | `3.69` | `> 4.5` | `> 3.6` |
| Niran's leg readiness drop (`r_fresh["leg"] - r_comp["leg"]`) | `2.24` | `> 2.5` | `> 1.5` |
| Niran's single-support drop (`r_fresh["single_support"] - r_comp["single_support"]`) | `1.37` | `> 2.0` | `> 1.2` |
| Donnell's head_straight drop when body-hurt (`r_donnell_fresh["head_straight"] - r_donnell_hurt["head_straight"]`) | `1.51` | `> 1.5` | `> 0.8` |
| Rook vs. Darius cross power ratio (`rook_cross["attacker_multiplier"] / darius_cross["attacker_multiplier"]`) | `1.34` (`1.75 / 1.31`) | `> 1.35` | `> 1.25` |
| Darius counter vs. normal cross damage ratio (`darius_counter["final_damage"] / darius_cross["final_damage"]`) | `1.88` (`1.875×`) | `> 1.95` | `> 1.65` |

### D14 — Vertical Mode Names
- **Decision:** Approved: `grounded / athletic / aerial`. Accept `wall_assisted` as an input alias normalized to `aerial` in CLI and fight settings (fixing the CLI schema `ValidationError` crash, defect A7).

### D15 — Canonical Data Source of Truth
- **Decision:** Approved: the JSON data files in `data/` are the canonical source of truth. `scripts/build_v2_data.py` is retired as a writer and replaced by `scripts/migrate_v2_data.py` (one-time, idempotent) + `scripts/validate_v2_data.py`. Fighter cards are never generated.

---

## 2. Pre-Approved Recommended Defaults (D3, D7, D8, D10–D13, D16–D23)

- **D3 (P4 — Laterality):** Natural stance for all 12 predefined cards (`orthodox -> right/right`, `southpaw -> left/left`, `switching -> right/right`), yielding zero dominance effect unless cross-dominant laterality is explicitly authored on a card (e.g., `tpl_jeet_kune_do`).
- **D7 (P2 — Darius Reed's 2nd slot):** Approve new capability `counter_boxing` (`pull_counter`, `check_hook`) so Darius Reed remains a 2-slot Two-piece counter-puncher (**subject to owner review of before/after card diff before applying in P2**).
- **D8 (P2 — Niran Sol's kick slot):** Move Niran Sol's kick slot to the new `muay_thai` capability (**subject to owner review of before/after card diff before applying in P2**).
- **D10 (P3 — `mentality.defensive`):** Keep positive lane readiness on `mentality.defensive` as a documented deliberate exception.
- **D11 (P1b — Basic punches in striking arts):** `kickboxing`, `muay_thai`, `karate`, and `sanda` grant basic punches (`jab`, `cross`, `hook`, `body_hook`, `body_jab` where listed in §8.1/§8.2).
- **D12 (P1b — New untrained & acrobatic techniques):** Approve `brawler_straight`, `wild_hook`, `shove`, `headbutt` (street/lethwei), and `acrobatics` (`cartwheel_kick`, `wall_run_kick`, `au`, `tornado_kick`).
- **D13 (P1b data / P5 loop — Rulesets):** Add `kickboxing`, `muay_thai`, `street`, `lethwei` alongside `boxing` and `mma` (`data/rulesets_v2.json`).
- **D16 (P9 — Doctor stoppages for cuts):** Off by default (`model.finishes.doctor_stoppage_enabled = false`).
- **D17 (P2 — Untrained defense fallback):** `retreat` for everyone (granted by `basic_movement`), preserving Rook Mercer's tested behavior.
- **D18 (P1b — Kick catches for boxing-trained `parry_catch` fighters):** Keep the seed grant (`boxing` grants `kick_catch`) so Darius Reed and Jo Costa keep their kick catches.
- **D19 (P2 — Untrained techniques inside trained slots):** With slot gating, `haymaker` (granted by `untrained_striking`) is thrown only from a slot that lists `untrained_striking`; trained slots use `overhand`.
- **D20 (Post-P11 — Style presets beyond 57 options):** Do not add options beyond the 57; style packs work via schools + recipes on the existing 57 options.
- **D21 (P5 — Lethwei rules):** Modern Lethwei rules (judged when no finish, keeping the no-draw invariant).
- **D22 (P1b — Kung Fu set):** Approve `wing_chun`, `hung_gar`, `bajiquan`, `baguazhang`, `tai_chi`, `shuai_jiao`, `jeet_kune_do`.
- **D23 (P13 — Rank & Mastery):**
  - Five ranks: `novice (-1)`, `trained (0)`, `expert (+1)`, `master (+2)`, `grandmaster (+3)`.
  - Acts after the style math via the unified contest helper (`contest_logit_per_level = 0.20`) and post-clamp damage multiplier (`damage_dealt_log_per_level = 0.04`, `damage_taken_log_per_level = 0.04`).
  - Rank is a ceiling on `school_mastery`, not a point budget.
  - Weakness shrink (`10% / 25% / 40%` at expert/master/grandmaster, `-25%` at novice) kept as flavour.
  - No separate mentality-by-rank term.
  - Recalibrate in P13 at both quick and full-fight lengths.

---

## 3. Checkpoints Requiring Owner Review Before Locking

1. **Before applying any card change from §8.10 (P2):** Present the exact before/after diff for each modified card in `cards/v2/` for owner approval before copying/applying.
2. **D4 (P9 — Win-method targets):** Run and show the KO/TKO / submission / decision split at the D2 full-fight ruleset lengths first before locking targets.
3. **D5 & D6 (P11 — Balance band & style-sanity list):** Run and show the full balance & style-sanity audit results first before locking thresholds.
