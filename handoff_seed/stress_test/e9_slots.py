"""E9: 'mastery lives on schools and is inherited by slots'. A fighter whose slots sit at different levels
(same mean level) vs a uniform mirror. Prediction to test: the fighter behaves like a uniform fighter at the
USAGE-WEIGHTED mean level of its slots, P = sigmoid(beta * (L_usage - 1))."""
import sys, os, json, math
from multiprocessing import Pool
from collections import defaultdict
import numpy as np
from scipy import stats
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harness as H
from stats_lib import wilson, sigmoid, logit

THETA = float(sys.argv[1]) if len(sys.argv) > 1 else 0.77
M = {"theta": THETA, "model": "v2"}
CONFIGS = {2: {"uniform": [1, 1], "front": [2, 0], "back": [0, 2]},
           3: {"uniform": [1, 1, 1], "front": [2, 1, 0], "back": [0, 1, 2]}}


def one(job):
    card, cfg, levels, s = job
    focus_a = s % 2 == 0
    f = {"card": card, "slot_m": levels, **M}
    o = {"card": card, "m": 1, **M}
    r = H.run_fight({"seed": s, "a": f if focus_a else o, "b": o if focus_a else f, "keep_log": True})
    fid = card if focus_a else card + "_b"
    slots = [sl["id"] for sl in H._STATE["cards"][card]["synchronized_capabilities"]]
    last = slots[0]; use = defaultdict(int)
    for e in json.loads(r["log"]):
        if e["attacker_id"] == fid:
            use[e["active_slot_id"]] += 1
            last = e["slot_switched_to"] or e["active_slot_id"]
        else:
            use[last] += 1
    return card, cfg, int(r["winner"] == fid), dict(use), slots


if __name__ == "__main__":
    H.init()
    jobs = []
    for card in [c for c in H.ARCHETYPES if c != "street"]:
        n = len(H._STATE["cards"][card]["synchronized_capabilities"])
        for cfg, levels in CONFIGS[n].items():
            off = int(os.environ.get("SEED_OFFSET", "0"))
            jobs += [(card, cfg, levels, s + off) for s in range(1, 201)]
    with Pool(2, initializer=H.init) as p:
        res = p.map(one, jobs, chunksize=40)
    beta = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "ladder_fit.json")))["beta"]
    agg = defaultdict(lambda: {"w": 0, "n": 0, "use": defaultdict(int), "slots": None})
    for card, cfg, w, use, slots in res:
        a = agg[(card, cfg)]; a["w"] += w; a["n"] += 1; a["slots"] = slots
        for k, v in use.items():
            a["use"][k] += v
    rows = []
    print("card        config   slot levels   usage share by slot     usage-weighted level   P(win vs uniform expert)   predicted")
    for (card, cfg), a in sorted(agg.items()):
        n = len(a["slots"]); levels = CONFIGS[n][cfg]
        tot = sum(a["use"].values()); share = [a["use"].get(sid, 0) / tot for sid in a["slots"]]
        lu = sum(sh * lv for sh, lv in zip(share, levels))
        p = a["w"] / a["n"]; pred = sigmoid(beta * (lu - 1))
        rows.append(dict(card=card, cfg=cfg, levels=levels, share=share, lu=lu, p=p, pred=pred, n=a["n"]))
        print(f"{card:11s} {cfg:8s} {str(levels):13s} {' '.join(f'{x:.2f}' for x in share):22s}  {lu:.2f}                  {p:.3f}                      {pred:.3f}")
    x = np.array([logit(r["pred"]) for r in rows]); y = np.array([logit(r["p"]) for r in rows])
    sl, ic, rr, pv, se = stats.linregress(x, y)
    print(f"\nusage-weighted-level rule: measured vs predicted logit slope {sl:.2f} (se {se:.2f}), intercept {ic:+.2f}, R^2 {rr**2:.2f}")
    for cfg in ("uniform", "front", "back"):
        rr_ = [r for r in rows if r["cfg"] == cfg]
        print(f"  {cfg:8s}: mean P {np.mean([r['p'] for r in rr_]):.3f}, mean predicted {np.mean([r['pred'] for r in rr_]):.3f}, "
              f"mean usage-weighted level {np.mean([r['lu'] for r in rr_]):.2f}, slot-1 usage share {np.mean([r['share'][0] for r in rr_]):.2f}")
    json.dump(rows, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "E9_fit.json"), "w"), indent=1)
