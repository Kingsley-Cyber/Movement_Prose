"""Experiment runner: builds fight specs per experiment, runs them on 2 worker processes, writes JSONL.

Design principles: common random numbers (the same seed set across conditions -> paired comparisons),
counterbalancing (the focal fighter alternates between canonical-first and canonical-second ids),
and fixed seeds (fully reproducible).
Usage:
  python3 runner.py 1                                  stage 1 (V0 dose-response, round robin, specialist baseline)
  python3 runner.py dose <model> <name> <thetas> <deltas> [seed range]
  python3 runner.py 2  <theta> <model>                 ladder, component factorial, robustness
  python3 runner.py 2b <theta> <model> <pairs json>    style counter in levels, specialist exchange rate
  python3 runner.py 3  <theta> <model> <delta_star>    equal-rank meta tournament + mixed-rank tournament
"""
from __future__ import annotations

import itertools
import json
import os
import sys
import time
from multiprocessing import Pool

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harness as H  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(OUT, exist_ok=True)
A = H.ARCHETYPES
MULTI = [c for c in A if c != "street"]
ENV_KEYS = ("dur", "arena", "ruleset", "clamp_off")
OFFSET = int(os.environ.get("SEED_OFFSET", "0"))   # shifts every seed of a run (fresh seeds without editing the designs)


def mirror(exp, cell, card, hi, lo, seeds, **kw):
    """Mirror match: same archetype, focal fighter at level `hi` vs a copy at `lo`. Focus alternates sides."""
    out = []
    for s in seeds:
        focus_a = (s % 2 == 0)
        f = {"card": card, "m": hi, **kw.get("f", {})}
        o = {"card": card, "m": lo, **kw.get("o", {})}
        sp = {"exp": exp, "cell": cell, "seed": s, "a": f if focus_a else o, "b": o if focus_a else f, "focus": "a" if focus_a else "b"}
        sp.update({k: v for k, v in kw.items() if k in ENV_KEYS})
        out.append(sp)
    return out


def versus(exp, cell, fa, fb, seeds, **kw):
    """Different builds: focal fa vs fb (the engine is order-invariant by construction)."""
    out = []
    for s in seeds:
        sp = {"exp": exp, "cell": cell, "seed": s, "a": fa, "b": fb, "focus": "a"}
        sp.update({k: v for k, v in kw.items() if k in ENV_KEYS})
        out.append(sp)
    return out


def work(sp):
    r = H.run_fight(sp)
    r["win_focus"] = r["win_a"] if sp["focus"] == "a" else 1 - r["win_a"]
    return r


def run(name, specs):
    t = time.time()
    for sp in specs:
        sp["seed"] += OFFSET
    path = os.path.join(OUT, f"{name}.jsonl")
    with Pool(2, initializer=H.init) as pool, open(path, "w") as fh:
        for r in pool.imap_unordered(work, specs, chunksize=64):
            fh.write(json.dumps(r) + "\n")
    print(f"{name}: {len(specs)} fights in {time.time() - t:.0f}s", flush=True)


def stage1():
    seeds = range(1, 101)
    specs = []
    for card, theta, d in itertools.product(A, [0.5, 1.0, 1.5, 2.0, 3.0], [1, 2, 3]):
        specs += mirror("E1", {"card": card, "theta": theta, "delta": d}, card, d, 0, seeds, f={"theta": theta}, o={"theta": theta})
    run("E1_dose_response", specs)
    specs = []
    for i, j in itertools.combinations(A, 2):
        specs += versus("E5a", {"a": i, "b": j}, {"card": i}, {"card": j}, range(1, 101))
    run("E5a_round_robin_trained", specs)
    specs = []
    for card in MULTI:
        for opp in A:
            if opp == card:
                continue
            for var in ("orig", "spec", "spec2"):
                specs += versus("E6a", {"card": card, "variant": var, "opp": opp}, {"card": card, "variant": var}, {"card": opp}, range(1, 41))
        for var in ("spec", "spec2"):
            specs += versus("E6a_h2h", {"card": card, "variant": var}, {"card": card, "variant": var}, {"card": card}, range(1, 201))
    run("E6a_specialist_equal_level", specs)


def dose(model, name, thetas, deltas, seeds=range(1, 101), comps=None):
    specs = []
    for card, theta, d in itertools.product(A, thetas, deltas):
        f = {"theta": theta, "model": model}
        if comps is not None:
            f["comps"] = list(comps)
        specs += mirror(name.split("_")[0], {"card": card, "theta": theta, "delta": d, "model": model}, card, d, 0, seeds, f=f, o=dict(f))
    run(name, specs)


def stage2(theta, model):
    M = {"theta": theta, "model": model}
    levels = [-1, 0, 1, 2, 3]
    specs = []
    for card in A:
        for lo, hi in itertools.combinations(levels, 2):
            specs += mirror("E2", {"card": card, "lo": lo, "hi": hi}, card, hi, lo, range(1, 201), f=dict(M), o=dict(M))
    run("E2_ladder", specs)
    comps_all = ("odds", "cnt", "pow", "tough", "shrink") if model != "v0" else ("acc", "def", "pow", "shrink")
    specs = []
    for card in A:
        for r in range(0, len(comps_all) + 1):
            for comps in itertools.combinations(comps_all, r):
                specs += mirror("E3", {"card": card, "comps": list(comps)}, card, 2, 0, range(1, 61),
                                f={**M, "comps": list(comps)}, o={**M, "comps": list(comps)})
        # V0 explanation: power-only mastery with the engine's multiplier clamp on vs off
        for clamp_off in (False, True):
            v0 = {"theta": 2.45, "model": "v0", "comps": ["pow"]}
            specs += mirror("E3b", {"card": card, "clamp_off": clamp_off}, card, 2, 0, range(1, 101), clamp_off=clamp_off, f=dict(v0), o=dict(v0))
    run("E3_components", specs)
    specs = []
    envs = [{}, {"dur": 30.0}, {"dur": 180.0}, {"arena": "ring"}, {"arena": "open_floor"}, {"arena": "narrow_alley"}, {"arena": "dojo"}, {"ruleset": "boxing"}]
    for card in A:
        for env in envs:
            for d in (1, 2):
                specs += mirror("E4", {"card": card, "delta": d, "env": json.dumps(env, sort_keys=True)}, card, d, 0, range(1, 151), f=dict(M), o=dict(M), **env)
    run("E4_robustness", specs)


def stage2b(theta, model, pairs):
    M = {"theta": theta, "model": model}
    specs = []
    for fav, dog in pairs:
        for d in (0, 0.5, 1, 1.5, 2, 2.5, 3):
            specs += versus("E5b", {"fav": fav, "dog": dog, "delta": d}, {"card": dog, "m": d, **M}, {"card": fav}, range(1, 151))
    run("E5b_style_counter_in_levels", specs)
    # exchange rate at an expert baseline (everyone at level 1), so the sweep -1.5..+1.5 stays inside novice..grandmaster
    specs = []
    for card in MULTI:
        for opp in A:
            if opp == card:
                continue
            specs += versus("E6b", {"card": card, "variant": "orig", "delta": 0.0, "opp": opp}, {"card": card, "m": 1, **M},
                            {"card": opp, "m": 1, **M}, range(1, 41))
            for d in (-1.5, -1.0, -0.5, 0.0, 0.5, 1.0, 1.5):
                specs += versus("E6b", {"card": card, "variant": "spec2", "delta": d, "opp": opp}, {"card": card, "variant": "spec2", "m": 1 + d, **M},
                                {"card": opp, "m": 1, **M}, range(1, 41))
    run("E6b_specialist_exchange_rate", specs)


def stage3(theta, model, delta_star):
    M = {"theta": theta, "model": model}
    builds = [("orig", c, 0.0) for c in A] + [("spec2", c, delta_star) for c in MULTI]
    specs = []
    for (v1, c1, m1), (v2, c2, m2) in itertools.combinations(builds, 2):
        fa = {"card": c1, "variant": v1, "m": m1, **M}
        fb = {"card": c2, "variant": v2, "m": m2, **M}
        specs += versus("E7", {"a": f"{c1}:{v1}", "b": f"{c2}:{v2}"}, fa, fb, range(1, 61))
    run("E7_meta_tournament", specs)
    builds = [(c, lv) for c in A for lv in (0, 1, 2)]
    specs = []
    for (c1, l1), (c2, l2) in itertools.combinations(builds, 2):
        cell = {"a": f"{c1}@{l1}", "b": f"{c2}@{l2}"}
        if c1 == c2:
            # same archetype: mirror() renames side b and counterbalances; focus = the l1 side
            specs += mirror("E8", cell, c1, l1, l2, range(1, 41), f=dict(M), o=dict(M))
        else:
            specs += versus("E8", cell, {"card": c1, "m": l1, **M}, {"card": c2, "m": l2, **M}, range(1, 41))
    run("E8_mixed_rank_tournament", specs)


def validate(theta, model, name):
    """Out-of-sample validation of a chosen theta: mirror gaps (fresh seeds) and cross-style gaps (all 66 style pairs)."""
    M = {"theta": theta, "model": model}
    specs = []
    for card, d in itertools.product(A, (1, 2, 3)):
        specs += mirror("V_mirror", {"card": card, "delta": d}, card, d, 0, range(7001, 7401), f=dict(M), o=dict(M))
    for c1, c2 in itertools.combinations(A, 2):
        for d in (1, 2, 3):
            specs += versus("V_cross", {"hi": c1, "lo": c2, "delta": d}, {"card": c1, "m": d, **M}, {"card": c2, "m": 0, **M}, range(7001, 7041))
            specs += versus("V_cross", {"hi": c2, "lo": c1, "delta": d}, {"card": c2, "m": d, **M}, {"card": c1, "m": 0, **M}, range(7001, 7041))
    run(name, specs)


if __name__ == "__main__":
    st = sys.argv[1]
    if st == "1":
        stage1()
    elif st == "dose":
        sd = json.loads(sys.argv[6]) if len(sys.argv) > 6 else [1, 101]
        dose(sys.argv[2], sys.argv[3], json.loads(sys.argv[4]), json.loads(sys.argv[5]), seeds=range(sd[0], sd[1]))
    elif st == "2":
        stage2(float(sys.argv[2]), sys.argv[3])
    elif st == "2b":
        stage2b(float(sys.argv[2]), sys.argv[3], json.loads(sys.argv[4]))
    elif st == "val":
        validate(float(sys.argv[2]), sys.argv[3], sys.argv[4])
    elif st == "3":
        stage3(float(sys.argv[2]), sys.argv[3], float(sys.argv[4]))
