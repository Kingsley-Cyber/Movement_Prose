# Phase P4 Verification & Balance Report

## Summary
- **Order Invariance Verified (Full Exchange Log + Final State, D10)**: `True`
- **200-Seed Overall Win Rates**: min `0.400`, max `0.639`
- **All Within [0.35, 0.65] Band**: `True` (outliers: `{}`)
- **Max Pairwise Win Rate**: `0.805` (sweeps > 0.85: `0`)
- **Laterality Invariants (§7.4, D3)**:
  - Natural cards (`handedness`/`footedness`/`grappling_side` matching `stance_orientation` or `"natural"`) have `0.0` dominance deltas (Darius/Rook damage numbers unchanged).
  - Cross-dominant (`tpl_jeet_kune_do`), ambidextrous, and `both` dominance profiles apply data-driven `model.laterality` deltas.
  - Exact mirror laterality invariance verified (flipping both fighters' orientation, dominance, anatomical sides, and `liver_side` produces identical outcomes and mirrored `damage_by_side`).
  - Southpaw-only edge (`southpaw` vs `orthodox` with identical attributes) verified within `[0.0, 0.05]`.

## 200-Seed Overall Win Rates
| Fighter ID | Win Rate |
|---|---|
| `donnell` | `0.639` |
| `greco` | `0.594` |
| `street` | `0.580` |
| `wrestler` | `0.556` |
| `sanda_judo` | `0.493` |
| `philly` | `0.488` |
| `macklin` | `0.483` |
| `maleek` | `0.463` |
| `detroit` | `0.456` |
| `karate` | `0.427` |
| `thai` | `0.420` |
| `jiujitsu` | `0.400` |
