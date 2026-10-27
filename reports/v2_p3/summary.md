# Phase P3 Verification & Balance Report

## Summary
- **Order Invariance Verified (Full Exchange Log + Final State, D10)**: `True`
- **200-Seed Overall Win Rates**: min `0.374`, max `0.656`
- **All Within [0.35, 0.65] Band**: `False` (outliers: `{'donnell': 0.656}`)
- **Max Pairwise Win Rate**: `0.815` (sweeps > 0.85: `0`)

## 200-Seed Overall Win Rates
| Fighter ID | Win Rate |
|---|---|
| `donnell` | `0.656` |
| `greco` | `0.604` |
| `street` | `0.586` |
| `wrestler` | `0.556` |
| `sanda_judo` | `0.532` |
| `karate` | `0.482` |
| `philly` | `0.467` |
| `macklin` | `0.458` |
| `maleek` | `0.454` |
| `jiujitsu` | `0.417` |
| `detroit` | `0.415` |
| `thai` | `0.374` |

## 50-Seed Technique & Defense Diversity
| Fighter ID | Distinct Attacks (>= 6) | Distinct Defenses | Combos Fired |
|---|---|---|---|
| `detroit` | `6` | `3` | `5` |
| `donnell` | `10` | `5` | `6` |
| `greco` | `12` | `3` | `5` |
| `jiujitsu` | `11` | `4` | `6` |
| `karate` | `14` | `2` | `6` |
| `macklin` | `10` | `3` | `6` |
| `maleek` | `10` | `4` | `5` |
| `philly` | `13` | `5` | `6` |
| `sanda_judo` | `15` | `4` | `5` |
| `street` | `4` | `1` | `2` |
| `thai` | `13` | `3` | `8` |
| `wrestler` | `13` | `4` | `6` |
