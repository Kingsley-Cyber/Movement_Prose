"""E4 robustness: does the calibrated level effect hold across arenas, durations and rulesets?
Paired design (same seeds as baseline). Pre-registered C8: |P_env - P_base| <= 0.05 at +1 and +2 (pooled)."""
import sys, json
from collections import defaultdict
import numpy as np
sys.path.insert(0, '.')
from stats_lib import *
R = load('data/E4_robustness.jsonl')
g = defaultdict(lambda: [0, 0]); seedwin = defaultdict(dict); meth = defaultdict(lambda: defaultdict(int))
for r in R:
    c = r['cell']; key = (c['env'], c['delta'])
    g[key][0] += r['win_focus']; g[key][1] += 1
    seedwin[key][(c['card'], r['seed'])] = r['win_focus']
    meth[c['env']][r['method'].split(' (')[0]] += 1
base = json.dumps({}, sort_keys=True)
out = {}
print("env                         +1: P (diff vs base, paired 95% CI)      +2: P (diff)            finish mix")
for env in sorted({k[0] for k in g}, key=lambda e: (e != base, e)):
    row = []
    for d in (1, 2):
        k, n = g[(env, d)]; p = k / n
        if env == base:
            row.append(f"{p:.3f}"); out[(env, d)] = (p, 0, 0, 0); continue
        diffs = np.array([seedwin[(env, d)][s] - seedwin[(base, d)][s] for s in seedwin[(env, d)]])
        m, se = diffs.mean(), diffs.std(ddof=1) / np.sqrt(len(diffs))
        out[(env, d)] = (p, m, m - 1.96 * se, m + 1.96 * se)
        row.append(f"{p:.3f} ({m:+.3f} [{m-1.96*se:+.3f},{m+1.96*se:+.3f}])")
    tot = sum(meth[env].values())
    mix = ", ".join(f"{k} {v/tot:.0%}" for k, v in sorted(meth[env].items(), key=lambda x: -x[1])[:3])
    print(f"{(env if env != base else 'baseline (cage, 60s, mma)'):27s} " + "   ".join(row) + "   " + mix)
ok = all(abs(v[1]) <= 0.05 for k, v in out.items())
print("C8 robustness (all |diff| <= 0.05):", ok)
json.dump({f"{k[0]}|{k[1]}": v for k, v in out.items()}, open('data/robustness_fit.json', 'w'), indent=1)
