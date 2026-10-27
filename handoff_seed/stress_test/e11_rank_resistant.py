"""E11: matchups where rank barely helps the underdog. Underdog at +0..+3 vs a trained favourite, 300 seeds each,
with the finish-method mix, to find the mechanism (V2, theta 0.80)."""
import sys, os, json
from multiprocessing import Pool
from collections import defaultdict, Counter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harness as H
from stats_lib import wilson
M = {"theta": 0.80, "model": "v2"}
PAIRS = [("jiujitsu", "wrestler"), ("wrestler", "maleek"), ("jiujitsu", "maleek"), ("wrestler", "thai"), ("karate", "thai")]

def one(job):
    fav, dog, d, s = job
    r = H.run_fight({"seed": s, "a": {"card": dog, "m": d, **M}, "b": {"card": fav, **M}})
    return fav, dog, d, r["win_a"], r["method"].split(" (")[0], r["n_ex"]

if __name__ == "__main__":
    jobs = [(f, dg, d, s) for f, dg in PAIRS for d in (0, 1, 2, 3) for s in range(1, 301)]
    with Pool(2, initializer=H.init) as p:
        res = p.map(one, jobs, chunksize=50)
    agg = defaultdict(lambda: {"w": 0, "n": 0, "m_dog": Counter(), "m_fav": Counter(), "nex": 0})
    for fav, dog, d, w, m, nex in res:
        a = agg[(fav, dog, d)]; a["w"] += w; a["n"] += 1; a["nex"] += nex
        (a["m_dog"] if w else a["m_fav"])[m] += 1
    out = {}
    for (fav, dog, d), a in sorted(agg.items()):
        p, lo, hi = wilson(a["w"], a["n"])
        out[f"{fav}>{dog}@{d}"] = {"p": p, "lo": lo, "hi": hi, "dog_wins_by": dict(a["m_dog"]), "fav_wins_by": dict(a["m_fav"]), "exchanges": a["nex"] / a["n"]}
        print(f"{dog:9s} at +{d} vs trained {fav:9s}: underdog wins {p:.3f} [{lo:.3f},{hi:.3f}]  favourite's wins by {dict(a['m_fav'])}  exchanges {a['nex']/a['n']:.1f}")
    json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "E11_rank_resistant.json"), "w"), indent=1)
