"""Calibrate the global mastery scale theta so that a +1 level gap wins 67.5% (pooled over archetypes),
then read off the implied +2/+3 win rates. Local weighted quadratic fit of logit P vs theta; parametric bootstrap CI."""
import json, sys, math
from collections import defaultdict
import numpy as np
from scipy import optimize
sys.path.insert(0, '.')
from stats_lib import *

def cells(paths):
    g = defaultdict(lambda: [0, 0])
    for p in paths:
        for r in load(p):
            c = r['cell']; g[(c['theta'], c['delta'])][0] += r['win_focus']; g[(c['theta'], c['delta'])][1] += 1
    return g

def fit_theta(g, rng_th, target=0.675, boot=0):
    out = {}
    def solve(gg):
        coefs = {}
        for d in (1, 2, 3):
            th = np.array([t for (t, dd) in gg if dd == d and rng_th[0] <= t <= rng_th[1]])
            th.sort()
            k = np.array([gg[(t, d)][0] for t in th]); n = np.array([gg[(t, d)][1] for t in th])
            y = np.log((k + 0.5) / (n - k + 0.5)); w = 1 / (1 / (k + 0.5) + 1 / (n - k + 0.5))
            coefs[d] = np.polyfit(th, y, 2, w=np.sqrt(w))
        f1 = lambda t: np.polyval(coefs[1], t) - logit(target)
        ts = optimize.brentq(f1, rng_th[0], rng_th[1])
        return ts, {d: sigmoid(np.polyval(coefs[d], ts)) for d in (1, 2, 3)}
    ts, ps = solve(g)
    res = {"theta": ts, "p": ps}
    if boot:
        rs = np.random.default_rng(7)
        bt = []; bp = {1: [], 2: [], 3: []}
        for _ in range(boot):
            gb = {key: [rs.binomial(n, k / n), n] for key, (k, n) in g.items()}
            try:
                t2, p2 = solve(gb)
            except ValueError:
                continue
            bt.append(t2)
            for d in (1, 2, 3): bp[d].append(p2[d])
        res["theta_ci"] = (float(np.percentile(bt, 2.5)), float(np.percentile(bt, 97.5)))
        res["p_ci"] = {d: (float(np.percentile(bp[d], 2.5)), float(np.percentile(bp[d], 97.5))) for d in (1, 2, 3)}
    return res

r0 = fit_theta(cells(['data/E1_dose_response.jsonl', 'data/E1v0fine_calib.jsonl']), (1.5, 3.0), boot=400)
r1 = fit_theta(cells(['data/E1v1_dose_response.jsonl', 'data/E1v1fine_calib.jsonl']), (0.5, 1.0), boot=400)
r2 = fit_theta(cells(['data/E1v2_dose.jsonl']), (0.5, 1.0), boot=400)
for name, r in (("V0", r0), ("V1", r1), ("V2", r2)):
    print(f"{name}: theta* = {r['theta']:.3f}  95% CI [{r['theta_ci'][0]:.3f}, {r['theta_ci'][1]:.3f}]")
    for d in (1, 2, 3):
        print(f"   predicted P(+{d}) = {r['p'][d]:.3f}  CI [{r['p_ci'][d][0]:.3f}, {r['p_ci'][d][1]:.3f}]   BT-linear would be {sigmoid(d*logit(0.675)):.3f}")
json.dump({n: {"theta": r["theta"], "theta_ci": r["theta_ci"], "p": r["p"], "p_ci": r["p_ci"]} for n, r in (("V0", r0), ("V1", r1), ("V2", r2))}, open('data/calibration.json', 'w'), indent=1)
