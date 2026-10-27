import sys, json
sys.path.insert(0, '.')
from stats_lib import *
from collections import defaultdict
import numpy as np
rs = np.random.default_rng(11)
summary = {}
for path, label in (('data/E1v0confirm.jsonl', 'V0 (inside clamps), theta=2.45'), ('data/E1v1confirm.jsonl', 'V1 (hit+counter odds, dmg/tough), theta=0.785'),
                    ('data/E1v2confirm.jsonl', 'V2 (every contest), theta=0.764')):
    R = load(path); g = defaultdict(lambda: [0, 0]); gc = defaultdict(lambda: [0, 0])
    for r in R:
        c = r['cell']; g[c['delta']][0] += r['win_focus']; g[c['delta']][1] += 1
        gc[(c['card'], c['delta'])][0] += r['win_focus']; gc[(c['card'], c['delta'])][1] += 1
    cards = sorted({k[0] for k in gc})
    print(f"\n{label}")
    summary[label] = {}
    for d in (1, 2, 3):
        k, n = g[d]; p, lo, hi = wilson(k, n)
        ys, vs = zip(*[cell_logodds(*gc[(c, d)]) for c in cards]); re = dersimonian_laird(ys, vs)
        # parametric bootstrap CI for tau
        taus = []
        for _ in range(1000):
            yb, vb = zip(*[cell_logodds(rs.binomial(gc[(c, d)][1], gc[(c, d)][0] / gc[(c, d)][1]), gc[(c, d)][1]) for c in cards])
            taus.append(dersimonian_laird(yb, vb)['tau'])
        ps = {c: gc[(c, d)][0] / gc[(c, d)][1] for c in cards}
        summary[label][d] = dict(p=p, lo=lo, hi=hi, tau=re['tau'], tau_ci=(float(np.percentile(taus, 2.5)), float(np.percentile(taus, 97.5))), I2=re['I2'],
                                 min=min(ps.values()), argmin=min(ps, key=ps.get), max=max(ps.values()), per=ps)
        print(f"  +{d}: pooled {p:.3f} [{lo:.3f},{hi:.3f}]  tau={re['tau']:.3f} (boot 95% {np.percentile(taus,2.5):.2f}-{np.percentile(taus,97.5):.2f}) I2={re['I2']:.2f}  "
              f"worst {min(ps.values()):.3f} ({min(ps,key=ps.get)}) best {max(ps.values()):.3f} ({max(ps,key=ps.get)})")
json.dump(summary, open('data/confirm_summary.json', 'w'), indent=1)
