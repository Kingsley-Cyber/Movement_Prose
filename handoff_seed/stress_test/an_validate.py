"""E10: validation of theta on (a) mirror gaps and (b) cross-style gaps over all 66 style pairs.
Seeds 7001-7400 were used to choose theta = 0.80 among 0.77/0.80/0.82 (selection set); seeds 30001-30400 are the
untouched holdout. Pass bands fixed before the runs: +1 in [0.65, 0.70], +2 in [0.78, 0.87], +3 in [0.87, 0.95]."""
import sys, json
from collections import defaultdict
import numpy as np
sys.path.insert(0, '.')
from stats_lib import *
BANDS = {1: (0.65, 0.70), 2: (0.78, 0.87), 3: (0.87, 0.95)}
res = {}
for th, path in ((0.77, 'data/E10_validate_theta077.jsonl'), (0.80, 'data/E10_validate_theta080.jsonl'), (0.82, 'data/E10_validate_theta082.jsonl'),
                 ('holdout_0.8', 'data/E10_holdout_theta080.jsonl')):
    R = load(path)
    g = defaultdict(lambda: [0, 0]); fav = defaultdict(lambda: [0, 0])
    pair = defaultdict(lambda: [0, 0])
    for r in R:
        c = r['cell']; kind = r['exp']
        g[(kind, c['delta'])][0] += r['win_focus']; g[(kind, c['delta'])][1] += 1
        if kind == 'V_cross':
            pair[(c['hi'], c['lo'], c['delta'])][0] += r['win_focus']; pair[(c['hi'], c['lo'], c['delta'])][1] += 1
    print(f"\ntheta = {th}")
    res[th] = {}
    for kind in ('V_mirror', 'V_cross'):
        for d in (1, 2, 3):
            k, n = g[(kind, d)]; p, lo, hi = wilson(k, n)
            inb = BANDS[d][0] <= p <= BANDS[d][1]
            extra = ""
            if kind == 'V_cross':
                ps = np.array([v[0] / v[1] for kk, v in pair.items() if kk[2] == d])
                extra = f"   higher rank favoured in {np.mean(ps > 0.5):.0%} of the 132 ordered style matchups; worst matchup {ps.min():.2f}"
            res[th][f"{kind}|{d}"] = (p, lo, hi, inb)
            print(f"  {kind[2:]:6s} +{d}: {p:.3f} [{lo:.3f},{hi:.3f}]  {'in band' if inb else 'OUT of band'} {BANDS[d]}{extra}")
json.dump({str(k): v for k, v in res.items()}, open('data/validate_fit.json', 'w'), indent=1)
