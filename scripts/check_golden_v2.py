#!/usr/bin/env python3
"""Golden snapshot & baseline diagnostics tool for BLOCK Fight Simulator v2.1 (P0+).

Usage:
  python3 scripts/check_golden_v2.py --write-golden
  python3 scripts/check_golden_v2.py --check-golden
  python3 scripts/check_golden_v2.py --check-golden --normalize-p1b-labels
  python3 scripts/check_golden_v2.py --write-baseline
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import itertools
import json
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import functools
from engine import simulator_v2 as _sim_mod  # noqa: E402
from engine.ontology import Knowledge, read  # noqa: E402
from engine.simulator_v2 import (  # noqa: E402
    audit_round_robin_balance_v2,
    available_v2,
    list_archetypes_v2,
    load_card_v2,
    simulate_fight_v2,
)

import jsonschema

# Cache read-only JSON loaders and compiled jsonschema validators if still uncached in P0
for _fn_name in ("_load_option_behaviors", "_load_model_v2", "_load_techniques_v2", "read"):
    if hasattr(_sim_mod, _fn_name):
        setattr(_sim_mod, _fn_name, functools.lru_cache(maxsize=64)(getattr(_sim_mod, _fn_name)))

_VALIDATOR_CACHE: dict[int, object] = {}
def _fast_validate(instance: object, schema: dict) -> None:
    sid = id(schema)
    v = _VALIDATOR_CACHE.get(sid)
    if v is None:
        cls = jsonschema.validators.validator_for(schema)
        v = cls(schema)
        _VALIDATOR_CACHE[sid] = v
    v.validate(instance)

jsonschema.validate = _fast_validate  # type: ignore[assignment]

GOLDEN_DIR = ROOT / "reports" / "v2_golden"
BASELINE_DIR = ROOT / "reports" / "v2_baseline"


def _canonical_json(obj: object) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def _sha256_str(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _normalize_p1b(fight: dict) -> dict:
    """In P1b, movement/feint damage_type changes label from 'movement'/'feint' to 'none'."""
    out = copy.deepcopy(fight)
    for ex in out.get("exchanges", []):
        if ex.get("technique_id") in ("step", "retreat", "pivot", "switch_step", "escape", "feint"):
            if ex.get("damage_type") in ("movement", "feint"):
                ex["damage_type"] = "none"
    return out


def compute_golden_runs(knowledge: Knowledge | None = None) -> list[dict]:
    k = knowledge or Knowledge()
    arch_ids = sorted(a["fighter_id"] for a in list_archetypes_v2(k))
    cards = {fid: load_card_v2(k, fid) for fid in arch_ids}

    runs = []
    # 1. All 66 unordered card pairs x 3 seeds (MMA, cage, 60 s, grounded) = 198 fights
    for a_id, b_id in itertools.combinations(arch_ids, 2):
        for seed in (1, 2, 3):
            res = simulate_fight_v2(
                cards[a_id],
                cards[b_id],
                ruleset="mma",
                arena="cage",
                duration_s=60.0,
                vertical_mode="grounded",
                seed=seed,
                knowledge=k,
            )
            key = f"mma_cage_60s_{a_id}_vs_{b_id}_seed{seed}"
            runs.append(
                {
                    "key": key,
                    "ruleset": "mma",
                    "arena": "cage",
                    "duration_s": 60.0,
                    "vertical_mode": "grounded",
                    "fighter_a": a_id,
                    "fighter_b": b_id,
                    "seed": seed,
                    "winner_id": res["winner_id"],
                    "finish_reason": res["finish_reason"],
                    "exchange_count": len(res["exchanges"]),
                    "exchanges": res["exchanges"],
                    "final_state_v2": res["final_state_v2"],
                    "sha256": _sha256_str(_canonical_json({"exchanges": res["exchanges"], "final_state_v2": res["final_state_v2"], "winner_id": res["winner_id"], "finish_reason": res["finish_reason"]})),
                }
            )

    # 2. 12 boxing fights (ring, 60 s, grounded) covering all 12 archetypes
    boxing_pairs = [(arch_ids[i], arch_ids[(i + 1) % len(arch_ids)], i + 1) for i in range(12)]
    for a_id, b_id, seed in boxing_pairs:
        res = simulate_fight_v2(
            cards[a_id],
            cards[b_id],
            ruleset="boxing",
            arena="ring",
            duration_s=60.0,
            vertical_mode="grounded",
            seed=seed,
            knowledge=k,
        )
        key = f"boxing_ring_60s_{a_id}_vs_{b_id}_seed{seed}"
        runs.append(
            {
                "key": key,
                "ruleset": "boxing",
                "arena": "ring",
                "duration_s": 60.0,
                "vertical_mode": "grounded",
                "fighter_a": a_id,
                "fighter_b": b_id,
                "seed": seed,
                "winner_id": res["winner_id"],
                "finish_reason": res["finish_reason"],
                "exchange_count": len(res["exchanges"]),
                "exchanges": res["exchanges"],
                "final_state_v2": res["final_state_v2"],
                "sha256": _sha256_str(_canonical_json({"exchanges": res["exchanges"], "final_state_v2": res["final_state_v2"], "winner_id": res["winner_id"], "finish_reason": res["finish_reason"]})),
            }
        )
    return runs


def write_golden() -> None:
    GOLDEN_DIR.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    runs = compute_golden_runs()
    overall_hash = _sha256_str(_canonical_json([r["sha256"] for r in runs]))
    manifest = {
        "base_commit": "0d0734d",
        "total_fights": len(runs),
        "mma_fights": 198,
        "boxing_fights": 12,
        "overall_sha256": overall_hash,
        "fights": [
            {
                "key": r["key"],
                "winner_id": r["winner_id"],
                "finish_reason": r["finish_reason"],
                "exchange_count": r["exchange_count"],
                "sha256": r["sha256"],
            }
            for r in runs
        ],
    }
    (GOLDEN_DIR / "golden_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    with (GOLDEN_DIR / "golden_exchanges.jsonl").open("w", encoding="utf-8") as f:
        for r in runs:
            f.write(_canonical_json(r) + "\n")
    print(f"Wrote {len(runs)} golden fights to {GOLDEN_DIR} in {time.time() - t0:.2f}s (overall SHA-256: {overall_hash})")


def check_golden(normalize_p1b: bool = False) -> int:
    manifest_path = GOLDEN_DIR / "golden_manifest.json"
    jsonl_path = GOLDEN_DIR / "golden_exchanges.jsonl"
    if not manifest_path.exists() or not jsonl_path.exists():
        print(f"ERROR: Golden files not found in {GOLDEN_DIR}")
        return 1

    saved_runs = [json.loads(line) for line in jsonl_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    curr_runs = compute_golden_runs()
    if len(saved_runs) != len(curr_runs):
        print(f"FAIL: Fight count mismatch ({len(saved_runs)} vs {len(curr_runs)})")
        return 1

    diffs = []
    label_only_diffs = 0
    for saved, curr in zip(saved_runs, curr_runs):
        assert saved["key"] == curr["key"]
        if saved["sha256"] == curr["sha256"]:
            continue
        if normalize_p1b:
            s_norm = _normalize_p1b(saved)
            c_norm = _normalize_p1b(curr)
            h_s = _sha256_str(_canonical_json({"exchanges": s_norm["exchanges"], "final_state_v2": s_norm["final_state_v2"], "winner_id": s_norm["winner_id"], "finish_reason": s_norm["finish_reason"]}))
            h_c = _sha256_str(_canonical_json({"exchanges": c_norm["exchanges"], "final_state_v2": c_norm["final_state_v2"], "winner_id": c_norm["winner_id"], "finish_reason": c_norm["finish_reason"]}))
            if h_s == h_c:
                label_only_diffs += 1
                continue
        diffs.append(saved["key"])

    if diffs:
        print(f"FAIL: {len(diffs)} / {len(saved_runs)} golden fights differed: {diffs[:10]}")
        return 1

    if normalize_p1b and label_only_diffs:
        print(f"PASS: All {len(saved_runs)} golden fights match identically after normalizing P1b movement/feint damage_type labels ({label_only_diffs} fights had only that label change).")
    else:
        print(f"PASS: All {len(saved_runs)} golden fights are byte-identical (overall SHA-256: {_sha256_str(_canonical_json([r['sha256'] for r in curr_runs]))}).")
    return 0


def write_baseline() -> None:
    BASELINE_DIR.mkdir(parents=True, exist_ok=True)
    k = Knowledge()
    arch_ids = sorted(a["fighter_id"] for a in list_archetypes_v2(k))
    cards = {fid: load_card_v2(k, fid) for fid in arch_ids}

    t0 = time.time()
    print("Running 200-seed round-robin balance audit and win-method count across all 66 pairs...")
    audit = audit_round_robin_balance_v2(
        runs_per_pair=200,
        ruleset="mma",
        duration_s=60.0,
        arena="cage",
        verify_order_invariance_seeds=3,
        knowledge=k,
    )

    # Tally win methods across the 66 * 200 = 13,200 fights from pairwise_matrix
    method_counts: Counter[str] = Counter()
    for pair_rec in audit["pairwise_matrix"]:
        for m, cnt in pair_rec.get("method_breakdown", {}).items():
            if "KO" in m or "TKO" in m:
                method_counts["KO/TKO"] += int(cnt)
            elif "Submission" in m:
                method_counts["Submission"] += int(cnt)
            else:
                method_counts["Decision"] += int(cnt)

    total_fights = sum(method_counts.values())
    method_pct = {k_m: round(100.0 * v / max(1, total_fights), 2) for k_m, v in method_counts.items()}

    # Diagnostics:
    # 1. Unreachable catalog techniques
    all_techs = {t["id"] for t in read(ROOT / "data/techniques_v2.json")["techniques"]}
    union_avail = set()
    for fid in arch_ids:
        union_avail |= available_v2(k, cards[fid], "mma")
    unreachable_techs = sorted(all_techs - union_avail)

    # 2. Distinct 5-move openings out of 60 fights against a canonical reference opponent ('wrestler' or 'thai')
    openings_by_fighter = {}
    counter_moves: Counter[str] = Counter()
    for fid in arch_ids:
        opp_id = "thai" if fid != "thai" else "wrestler"
        seen_openings = set()
        for seed in range(1, 61):
            sim = simulate_fight_v2(cards[fid], cards[opp_id], ruleset="mma", duration_s=60.0, seed=seed, arena="cage", knowledge=k)
            own_moves = tuple(ex["technique_id"] for ex in sim["exchanges"] if ex["attacker_id"] == fid)[:5]
            seen_openings.add(own_moves)
            for ex in sim["exchanges"]:
                if ex.get("counter_followup"):
                    counter_moves[ex["counter_followup"]["technique_id"]] += 1
        openings_by_fighter[fid] = len(seen_openings)

    # 3. Vertical mode invariance check at 0d0734d
    sim_g = simulate_fight_v2(cards["sanda_judo"], cards["thai"], ruleset="mma", duration_s=60.0, seed=7, arena="cage", vertical_mode="grounded", knowledge=k)
    sim_a = simulate_fight_v2(cards["sanda_judo"], cards["thai"], ruleset="mma", duration_s=60.0, seed=7, arena="cage", vertical_mode="athletic", knowledge=k)
    vertical_identical = sim_g["exchanges"] == sim_a["exchanges"]

    # 4. Arena directional check: Donnell vs Aya across open_floor, cage, ring, narrow_alley (60 seeds)
    arena_donnell_rates = {}
    for ar in ("open_floor", "cage", "ring", "narrow_alley"):
        wins = 0
        for seed in range(1, 61):
            s = simulate_fight_v2(cards["donnell"], cards["karate"], ruleset="mma", duration_s=60.0, seed=seed, arena=ar, knowledge=k)
            if s["winner_id"] == "donnell":
                wins += 1
        arena_donnell_rates[ar] = round(100.0 * wins / 60.0, 1)

    diagnostics = {
        "elapsed_s": round(time.time() - t0, 2),
        "total_balance_fights": total_fights,
        "method_counts": dict(method_counts),
        "method_pct": method_pct,
        "unreachable_techniques_at_baseline": unreachable_techs,
        "distinct_5_move_openings_of_60": openings_by_fighter,
        "counter_technique_counts": dict(counter_moves.most_common()),
        "vertical_mode_grounded_vs_athletic_identical": vertical_identical,
        "donnell_vs_karate_win_pct_by_arena_60_seeds": arena_donnell_rates,
    }

    (BASELINE_DIR / "balance_audit_200.json").write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    (BASELINE_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n", encoding="utf-8")

    # Write a concise markdown summary
    rates_md = "\n".join(
        f"| `{fid}` | {rate * 100:.1f}% | {openings_by_fighter[fid]} / 60 |"
        for fid, rate in sorted(audit["archetype_overall_win_rates"].items(), key=lambda kv: -kv[1])
    )
    summary_md = f"""# BLOCK Simulator v2 — P0 Baseline Report (`0d0734d`)

- **Total Round-Robin Fights (200 seeds × 66 pairs):** `{total_fights}`
- **Order Invariance Verified:** `{audit["order_invariance_verified"]}`
- **All 12 in [35%, 65%] Band:** `{audit["all_within_target_band_35_65"]}`
- **No Pair > 85%:** `{audit["no_sweep_above_85"]}`
- **Win Methods:** KO/TKO `{method_pct.get("KO/TKO", 0.0)}%`, Submission `{method_pct.get("Submission", 0.0)}%`, Decision `{method_pct.get("Decision", 0.0)}%`
- **Unreachable Catalog Techniques ({len(unreachable_techs)}):** `{", ".join(unreachable_techs)}`
- **Donnell vs. Karate Win Rate by Arena (60 seeds):** `{arena_donnell_rates}`

## Archetype Overall Win Rates & Opening Diversity

| Archetype | Overall Win Rate (200 seeds/pair) | Distinct 5-Move Openings (of 60) |
|---|---|---|
{rates_md}
"""
    (BASELINE_DIR / "summary.md").write_text(summary_md, encoding="utf-8")
    print(f"Wrote baseline audit & diagnostics to {BASELINE_DIR} in {diagnostics['elapsed_s']}s.")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-golden", action="store_true")
    parser.add_argument("--check-golden", action="store_true")
    parser.add_argument("--normalize-p1b-labels", action="store_true")
    parser.add_argument("--write-baseline", action="store_true")
    args = parser.parse_args()

    if args.write_golden:
        write_golden()
    if args.write_baseline:
        write_baseline()
    if args.check_golden:
        return check_golden(normalize_p1b=args.normalize_p1b_labels)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
