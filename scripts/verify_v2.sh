#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ -x "$ROOT/.venv/bin/python" ]]; then
  PY="$ROOT/.venv/bin/python"
else
  PY="python3"
fi

echo "=== [1/6] Protected & Immutable Files Check ==="
EXISTING_TESTS=(
  "tests/conftest.py"
  "tests/test_backfill.py"
  "tests/test_end_to_end.py"
  "tests/test_event_graph.py"
  "tests/test_fairness_plan.py"
  "tests/test_fight_move_system.py"
  "tests/test_fight_plan.py"
  "tests/test_matchups.py"
  "tests/test_ontology.py"
  "tests/test_prediction.py"
  "tests/test_simulator_v2_and_atomic_compiler.py"
  "tests/test_slots.py"
)
if ! git diff --quiet 0d0734d -- "${EXISTING_TESTS[@]}"; then
  echo "FAIL: Existing tests modified since 0d0734d (violates Rule 9: test immutability)!"
  git diff --stat 0d0734d -- "${EXISTING_TESTS[@]}"
  exit 1
fi
if ! git diff --quiet 0d0734d -- scripts/sakuga_compiler.py data/debt_registry.json _archive_rd_history_do_not_copy/; then
  echo "FAIL: Protected files modified since 0d0734d (violates Rule 10)!"
  exit 1
fi
echo "PASS: Existing tests and protected files are untouched."

echo "=== [2/6] Schema & Data Validation ==="
"$PY" - <<'PYEOF'
import json
from pathlib import Path
import jsonschema

root = Path(".")
def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))

pairs = [
    ("data/option_behaviors.json", "schemas/option_behavior.schema.json"),
    ("data/techniques_v2.json", "schemas/technique_v2.schema.json"),
    ("data/positions.json", "schemas/position_map.schema.json"),
    ("data/model_v2.json", "schemas/model_config_v2.schema.json"),
]
optional_pairs = [
    ("data/rulesets_v2.json", "schemas/rulesets_v2.schema.json"),
    ("data/combinations_v2.json", "schemas/combinations_v2.schema.json"),
    ("data/debt_registry_v2.json", "schemas/debt_registry_v2.schema.json"),
    ("data/capabilities_v2.json", "schemas/capabilities_v2.schema.json"),
]
for dpath, spath in pairs:
    jsonschema.validate(load(dpath), load(spath))
for dpath, spath in optional_pairs:
    if Path(dpath).exists() and Path(spath).exists():
        jsonschema.validate(load(dpath), load(spath))

card_schema = load("schemas/fighter_card_v2.schema.json")
v2_cards = sorted(Path("cards/v2").glob("*.json"))
v1_cards = sorted(Path("cards").glob("*.json"))
assert len(v2_cards) == 12, f"Expected 12 v2 cards, found {len(v2_cards)}"
assert len(v1_cards) == 11, f"Expected 11 v1 cards, found {len(v1_cards)}"
for p in v2_cards + v1_cards:
    jsonschema.validate(load(p), card_schema)

opt_beh = load("data/option_behaviors.json")
assert len(opt_beh["options"]) == 57, f"Expected 57 options, found {len(opt_beh['options'])}"
print(f"PASS: Validated {len(pairs)} core data files, {len(v2_cards)} v2 cards, {len(v1_cards)} v1 cards, 57 options.")
PYEOF

if [[ -f "$ROOT/scripts/validate_v2_data.py" ]]; then
  "$PY" "$ROOT/scripts/validate_v2_data.py"
fi

echo "=== [3/6] v1 Test Suite ==="
V1_FILTER="not disposable_copy"
if [[ "${FULL_V1:-0}" == "1" ]]; then
  V1_FILTER="all_v1_tests"
  "$PY" -m pytest -q \
    tests/test_backfill.py \
    tests/test_end_to_end.py \
    tests/test_event_graph.py \
    tests/test_fight_move_system.py \
    tests/test_fight_plan.py \
    tests/test_matchups.py \
    tests/test_ontology.py \
    tests/test_prediction.py \
    tests/test_slots.py \
    tests/test_fairness_plan.py
else
  "$PY" -m pytest -q -k "$V1_FILTER" \
    tests/test_backfill.py \
    tests/test_end_to_end.py \
    tests/test_event_graph.py \
    tests/test_fight_move_system.py \
    tests/test_fight_plan.py \
    tests/test_matchups.py \
    tests/test_ontology.py \
    tests/test_prediction.py \
    tests/test_slots.py \
    tests/test_fairness_plan.py
fi
git checkout -- knowledge_base/agent_memory.db 2>/dev/null || true

echo "=== [4/6] v2 Fast Tests & D9 Tripwire Verification ==="
V2_TEST_FILES=("tests/test_simulator_v2_and_atomic_compiler.py")
for f in tests/test_v2_*.py; do
  if [[ -f "$f" ]]; then
    V2_TEST_FILES+=("$f")
  fi
done
"$PY" -m pytest -q "${V2_TEST_FILES[@]}" -k "not round_robin_balance_band and not 57_option_audit"

"$PY" - <<'PYEOF'
import copy
from engine.ontology import ROOT, Knowledge, read
from engine.simulator_v2 import (
    compute_card_derived_damage,
    compute_posture_state,
    compute_readiness_profile,
    load_card_v2,
)

k = Knowledge()
opt_map = {o["id"]: o for o in read(ROOT / "data/option_behaviors.json")["options"]}
niran = load_card_v2(k, "thai")
donnell = load_card_v2(k, "donnell")
rook = load_card_v2(k, "street")
darius = load_card_v2(k, "detroit")

fresh = {
    "posture_mode": "standing",
    "balance": "stable",
    "grip": None,
    "sub_grips": {"underhooks": 0},
    "wall_proximity": "far",
    "damage": {"head": 0.0, "body": 0.0, "leg": 0.0},
    "fatigue": 0.0,
    "recovery_window": {"window_type": "none", "last_technique_id": None, "exposed_lanes": [], "readiness_penalty": 0.0},
    "attention": {"focus_line": "neutral", "feinted": False, "outside_angle_conceded": False},
    "read_memory": {"seen_counts": {}, "consecutive_same_move_by_opponent": 0},
}
comp = copy.deepcopy(fresh)
comp["balance"] = "off_base"
comp["damage"]["leg"] = 5.0
comp["recovery_window"] = {
    "window_type": "single_leg_recovery",
    "last_technique_id": "body_kick",
    "exposed_lanes": ["single_support", "leg", "head_straight", "entry"],
    "readiness_penalty": 1.35,
}
body_hurt = copy.deepcopy(fresh)
body_hurt["damage"]["body"] = 8.0
body_hurt["fatigue"] = 6.0

r_fresh = compute_readiness_profile(k, niran, fresh, donnell, fresh, "kick", "closed_stance", "low_kick", opt_map)
r_comp = compute_readiness_profile(k, niran, comp, donnell, fresh, "kick", "closed_stance", "low_kick", opt_map)
r_d_fresh = compute_readiness_profile(k, donnell, fresh, niran, fresh, "punch", "closed_stance", "cross", opt_map)
r_d_hurt = compute_readiness_profile(k, donnell, body_hurt, niran, fresh, "punch", "closed_stance", "cross", opt_map)

dummy = {"fatigue": 0.0, "damage": {"head": 0.0, "body": 0.0, "leg": 0.0}, "wall_proximity": "far", "setups": []}
rook_cross = compute_card_derived_damage(k, rook, darius, "cross", "clean", dummy, dummy)
darius_cross = compute_card_derived_damage(k, darius, rook, "cross", "clean", dummy, dummy)
darius_counter = compute_card_derived_damage(k, darius, rook, "cross", "counter_hit", dummy, dummy)

checks = [
    ("Niran leg readiness > 3.6", r_fresh["leg"], 3.6),
    ("Niran leg readiness drop > 1.5", r_fresh["leg"] - r_comp["leg"], 1.5),
    ("Niran single_support drop > 1.2", r_fresh["single_support"] - r_comp["single_support"], 1.2),
    ("Donnell head_straight drop > 0.8", r_d_fresh["head_straight"] - r_d_hurt["head_straight"], 0.8),
    ("Rook vs Darius power ratio > 1.25", rook_cross["attacker_multiplier"] / darius_cross["attacker_multiplier"], 1.25),
    ("Darius counter vs normal cross > 1.65", darius_counter["final_damage"] / darius_cross["final_damage"], 1.65),
]
for label, val, thresh in checks:
    assert val > thresh, f"D9 Tripwire FAILED: {label} (got {val:.4f} <= {thresh})"
print("PASS: All 6 D9 tripwire thresholds verified:", ", ".join(f"{c[0]}={c[1]:.2f}" for c in checks))
PYEOF

echo "=== [5/6] Determinism Hash & Order Invariance ==="
"$PY" - <<'PYEOF'
import hashlib
import json
from engine.ontology import Knowledge
from engine.simulator_v2 import load_card_v2, simulate_fight_v2

k = Knowledge()
pairs = [
    ("sanda_judo", "thai"),
    ("wrestler", "karate"),
    ("jiujitsu", "street"),
    ("donnell", "detroit"),
    ("philly", "greco"),
]
seeds = [3, 7, 11]
hashes = []
for a_id, b_id in pairs:
    ca = load_card_v2(k, a_id)
    cb = load_card_v2(k, b_id)
    for seed in seeds:
        r1 = simulate_fight_v2(ca, cb, ruleset="mma", duration_s=60.0, seed=seed, arena="cage", knowledge=k)
        r2 = simulate_fight_v2(ca, cb, ruleset="mma", duration_s=60.0, seed=seed, arena="cage", knowledge=k)
        r_ba = simulate_fight_v2(cb, ca, ruleset="mma", duration_s=60.0, seed=seed, arena="cage", knowledge=k)
        s1 = json.dumps(r1, sort_keys=True)
        s2 = json.dumps(r2, sort_keys=True)
        assert s1 == s2, f"Non-deterministic run for {a_id} vs {b_id} seed {seed}"
        assert r1["winner_id"] == r_ba["winner_id"], f"Order invariance winner mismatch for {a_id} vs {b_id} seed {seed}"
        assert r1["exchanges"] == r_ba["exchanges"], f"Order invariance exchanges mismatch for {a_id} vs {b_id} seed {seed}"
        assert r1["final_state_v2"] == r_ba["final_state_v2"], f"Order invariance final_state_v2 mismatch for {a_id} vs {b_id} seed {seed}"
        hashes.append(hashlib.sha256(s1.encode("utf-8")).hexdigest()[:12])
print(f"PASS: Determinism & order invariance verified across {len(pairs)} pairs x {len(seeds)} seeds. Sample hashes:", hashes[:5])
PYEOF

echo "=== [6/6] Engine Literal & ID Scans ==="
"$PY" - <<'PYEOF'
import ast
import json
from pathlib import Path

option_ids = {o["id"] for o in json.loads(Path("data/option_behaviors.json").read_text())["options"]}
tech_ids = {t["id"] for t in json.loads(Path("data/techniques_v2.json").read_text())["techniques"]}
fighter_ids = {p.stem for p in Path("cards/v2").glob("*.json")}

# Allowlisted technique/movement tokens that also happen to be general vocabulary or structural keys/defaults
TECH_VOCAB_ALLOWLIST = {
    "escape",   # general domain/outcome/role word or universal fallback
    "retreat",  # universal D17 fallback
    "step",     # universal empty-pool fallback
    "check",    # general verb/key
    "ride",     # general key
}

v2_dir = Path("engine/v2")
if v2_dir.exists():
    targets = [p for p in sorted(v2_dir.glob("*.py")) if p.name not in ("__init__.py", "data.py")]
    strict = True
else:
    targets = [Path("engine/simulator_v2.py")]
    strict = False

violations = []
for path in targets:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    # Strip module/class/function docstrings
    docstring_nodes = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant) and isinstance(node.body[0].value.value, str):
                docstring_nodes.add(node.body[0].value)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and node not in docstring_nodes:
            val = node.value
            if val in fighter_ids and val not in ("street", "karate"):  # 'street' is also a ruleset name
                violations.append((str(path), node.lineno, "fighter_id", val))
            elif val in option_ids:
                violations.append((str(path), node.lineno, "option_id", val))
            elif val in (tech_ids - TECH_VOCAB_ALLOWLIST):
                violations.append((str(path), node.lineno, "technique_id", val))

if strict:
    if violations:
        print(f"FAIL: Found {len(violations)} disallowed literals in engine/v2/:")
        for v in violations[:30]:
            print(" ", v)
        raise SystemExit(1)
    print(f"PASS: 0 disallowed fighter/option/technique literals across {len(targets)} engine/v2/ modules.")
else:
    print(f"INFO (P0 pre-refactor): {len(violations)} option/technique literals in engine/simulator_v2.py (will become 0 in P1a).")
PYEOF

echo "=== ALL VERIFY_V2 CHECKS PASSED ==="
