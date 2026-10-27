#!/usr/bin/env bash
# Re-runs every experiment and analysis behind RANK_MASTERY_STRESS_TEST.md, in order.
# About 50 minutes on 2 cores; writes data/*.jsonl (raw fights, ~100 MB) and results/ (results.json, tables, figures).
# Needs BLOCK_REPO = a checkout of Kingsley-Cyber/Movement_Prose at 0d0734d (read-only; nothing in it is modified).
set -euo pipefail
cd "$(dirname "$0")"
: "${BLOCK_REPO:?set BLOCK_REPO to a checkout of Movement_Prose at 0d0734d}"
export BLOCK_REPO
PAIRS='[["wrestler","maleek"],["sanda_judo","jiujitsu"],["karate","thai"],["street","detroit"],["philly","jiujitsu"],["sanda_judo","maleek"],["wrestler","thai"],["greco","jiujitsu"],["karate","macklin"],["jiujitsu","detroit"],["greco","donnell"],["donnell","macklin"]]'

# 0. controls (every line must print the same hash) and the clamp-saturation audit
for m in orig patched zero zero1 zero2; do python3 -I control.py "$m"; done
python3 -I test_slot.py
python3 -I diag.py

# 1. calibration (seeds 1-200): V0/V1/V2 dose-response; trained round robin and trained specialist baseline (rank-free)
python3 -I runner.py 1
python3 -I runner.py dose v1 E1v1_dose_response '[0.5,1,1.5,2,3]' '[1,2,3]'
python3 -I runner.py dose v0 E1v0fine_calib '[2.2,2.4,2.6]' '[1,2,3]' '[1,201]'
python3 -I runner.py dose v1 E1v1fine_calib '[0.7,0.8,0.9]' '[1,2,3]' '[1,201]'
python3 -I runner.py dose v2 E1v2_dose '[0.4,0.5,0.6,0.7,0.8,1.0]' '[1,2,3]' '[1,201]'
python3 -I calib.py

# 2. model comparison on two fresh seed sets (A = 5001-5400, B = 7001-7400)
python3 -I runner.py dose v0 E1v0confirm '[2.45]' '[1,2,3]' '[5001,5401]'
python3 -I runner.py dose v1 E1v1confirm '[0.785]' '[1,2,3]' '[5001,5401]'
python3 -I runner.py dose v2 E1v2confirm '[0.764]' '[1,2,3]' '[5001,5401]'
python3 -I runner.py dose v2 E1v2confirm080 '[0.80]' '[1,2,3]' '[5001,5401]'
python3 -I runner.py dose v0 E1v0confirm2 '[2.45]' '[1,2,3]' '[7001,7401]'
python3 -I runner.py dose v1 E1v1confirm2 '[0.785]' '[1,2,3]' '[7001,7401]'

# 3. choice of theta among 0.77 / 0.80 / 0.82 (seeds 7001-7400), then the holdout (seeds 30001-30400, used once)
python3 -I runner.py val 0.77 v2 E10_validate_theta077
python3 -I runner.py val 0.80 v2 E10_validate_theta080
python3 -I runner.py val 0.82 v2 E10_validate_theta082
SEED_OFFSET=23000 python3 -I runner.py val 0.80 v2 E10_holdout_theta080

# 4. downstream experiments at theta 0.80 on fresh seeds (20001+); the rank-free 23-build tournament pools two replicates
python3 -I runner.py 3 0.80 v2 0.0 && mv data/E7_meta_tournament.jsonl data/E7_meta_tournament_seeds1to60.jsonl
SEED_OFFSET=20000 python3 -I runner.py 2 0.80 v2
SEED_OFFSET=20000 python3 -I runner.py 2b 0.80 v2 "$PAIRS"
SEED_OFFSET=20000 python3 -I runner.py 3 0.80 v2 0.0
python3 -I e11_rank_resistant.py                                         # matchups that resist rank (seeds 1-300)
python3 -I e11b_mechanism.py                                             # wrestler vs jiu-jitsu, logged
python3 -I theory.py 0.80 v2                                             # damage-race theory check (logged)

# 5. analyses (order matters: later scripts read earlier fits)
python3 -I an_stage1.py; python3 -I an_stage1b.py; python3 -I an_dose.py; python3 -I an_confirm.py
python3 -I an_ladder.py; python3 -I an_components.py; python3 -I an_robust.py
python3 -I an_counter.py; python3 -I an_spec.py; python3 -I an_meta.py; python3 -I an_validate.py
SEED_OFFSET=20000 python3 -I e9_slots.py 0.80                            # per-slot inheritance (needs the ladder fit)
python3 -I summarize.py                                                  # results/results.json, tables, figures
