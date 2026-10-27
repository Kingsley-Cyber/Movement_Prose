# stress_test — rank & mastery stress test (companion to `RANK_MASTERY_STRESS_TEST.md`)

Everything here runs against a **read-only** checkout of `Kingsley-Cyber/Movement_Prose` at `0d0734d`
(set `BLOCK_REPO`). Nothing in the repo is modified: the harness wraps the engine and, for the V1/V2 rank
models, loads an instrumented copy of `engine/simulator_v2.py` with hook calls on the contested-roll lines.
At rank zero every model reproduces the original exchange logs byte for byte (`control.py`).

| File | What it does |
|---|---|
| `harness.py` | rank models V0/V1/V2, per-slot mastery, specialist variants, one-fight runner |
| `runner.py` | experiment designs (common random numbers, counterbalancing, fixed seeds), 2 worker processes, JSONL output in `data/` |
| `control.py`, `test_slot.py` | identity controls (C1) and the per-slot resolver unit test |
| `diag.py` | clamp-saturation audit (why rank inside the clamps is uneven) |
| `stats_lib.py` | Wilson intervals, logistic and Bradley–Terry MLE, DerSimonian–Laird, Hodge decomposition (+ noise correction and null bootstrap), Nash LP, problem of points, factorial Sobol shares |
| `calib.py`, `an_*.py` | calibration and the per-experiment analyses |
| `e9_slots.py`, `e11_rank_resistant.py`, `e11b_mechanism.py`, `theory.py` | per-slot inheritance, rank-resistant matchups and their mechanism, damage-race theory |
| `summarize.py` | collects every reported number into `results/results.json`, writes `results/tables/*.md` and `results/figures/*.png` |
| `reproduce.sh` | re-runs everything in order (~50 min on 2 cores); seeds: calibration 1–200, model comparison 5001–5400 and 7001–7400, θ choice 7001–7400, holdout 30001–30400, downstream experiments at θ 0.80 on 20001+ (`SEED_OFFSET`) |
| `data/*.json` | the fitted results (small); raw fight logs (`data/*.jsonl`, ~100 MB) are not shipped — `reproduce.sh` regenerates them exactly |

For P13 (handoff §9): keep this folder as the reference implementation of the calibration protocol. After the
engine changes, port `harness.py`'s hooks to the real contest helper (handoff §7.6/§7.18) instead of patching source lines.
