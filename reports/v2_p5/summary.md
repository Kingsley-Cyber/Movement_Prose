# Phase P5 Verification & Per-Ruleset Audit Report

## Summary
- **Order Invariance Verified (D10)**: `True`
- **All Within [0.35, 0.65] Band (200-seed MMA)**: `True` (outliers: `{}`)
- **No Sweep Above 0.85**: `True` (max pair: `0.805`)
- **Legality Matrix (§10.9)**: PASS across `boxing`, `kickboxing`, `muay_thai`, `mma`, `street`, and `lethwei`
- **Equipment, `stop_hit`, `cut_chance`, `on_success_effects` (§7.17), & `rooftop_edge` Ring-Out**: PASS

## 200-Seed MMA Overall Win Rates
| Fighter ID | Win Rate |
|---|---|
| `donnell` | `0.620` |
| `greco` | `0.596` |
| `street` | `0.581` |
| `wrestler` | `0.560` |
| `philly` | `0.483` |
| `sanda_judo` | `0.482` |
| `macklin` | `0.470` |
| `maleek` | `0.458` |
| `karate` | `0.454` |
| `detroit` | `0.453` |
| `jiujitsu` | `0.425` |
| `thai` | `0.419` |
