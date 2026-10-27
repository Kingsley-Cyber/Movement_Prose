"""E2 ladder: Bradley-Terry on rank levels. Tests (i) linear (equal) spacing, (ii) BT adequacy (P depends only on the
strength difference), (iii) upset (giant-killing) rates by gap, (iv) per-archetype spread."""
import sys, json, math, itertools
from collections import defaultdict
import numpy as np
from scipy import optimize, stats
sys.path.insert(0, '.')
from stats_lib import *

R = load('data/E2_ladder.jsonl')
L = [-1, 0, 1, 2, 3]
NAMES = {-1: "novice", 0: "trained", 1: "expert", 2: "master", 3: "grandmaster"}
g = defaultdict(lambda: [0, 0]); gc = defaultdict(lambda: [0, 0])
for r in R:
    c = r['cell']; key = (c['lo'], c['hi'])
    g[key][0] += r['win_focus']; g[key][1] += 1
    gc[(c['card'],) + key][0] += r['win_focus']; gc[(c['card'],) + key][1] += 1
pairs = sorted(g)

def nll_free(s_free):
    s = dict(zip([-1, 1, 2, 3], s_free)); s[0] = 0.0
    tot = 0
    for (lo, hi) in pairs:
        k, n = g[(lo, hi)]; d = s[hi] - s[lo]
        tot -= k * d - n * np.logaddexp(0, d)
    return tot

def nll_lin(b):
    tot = 0
    for (lo, hi) in pairs:
        k, n = g[(lo, hi)]; d = b[0] * (hi - lo)
        tot -= k * d - n * np.logaddexp(0, d)
    return tot

rf = optimize.minimize(nll_free, np.array([-0.7, 0.7, 1.4, 2.1]), method="BFGS")
rl = optimize.minimize(nll_lin, np.array([0.7]), method="BFGS")
s = dict(zip([-1, 1, 2, 3], rf.x)); s[0] = 0.0
# exact Fisher information for the free-level BT model (parameters: s_-1, s_1, s_2, s_3; s_0 = 0)
idx = {-1: 0, 1: 1, 2: 2, 3: 3}
I = np.zeros((4, 4))
s_tmp = dict(zip([-1, 1, 2, 3], rf.x)); s_tmp[0] = 0.0
for (lo, hi) in pairs:
    k, n = g[(lo, hi)]
    x = np.zeros(4)
    if hi in idx: x[idx[hi]] += 1
    if lo in idx: x[idx[lo]] -= 1
    pp = 1 / (1 + math.exp(-(s_tmp[hi] - s_tmp[lo])))
    I += n * pp * (1 - pp) * np.outer(x, x)
cov = np.linalg.inv(I)
se = dict(zip([-1, 1, 2, 3], np.sqrt(np.diag(cov)))); se[0] = 0.0
LR = 2 * (rl.fun - rf.fun)
print("Bradley-Terry level strengths (logits, trained = 0) with SE; Elo = 400/ln10 * s:")
for lv in L:
    print(f"  {NAMES[lv]:12s} s={s[lv]:+.3f} (se {se[lv]:.3f})  Elo {400/math.log(10)*s[lv]:+.0f}")
steps = [s[l + 1] - s[l] for l in L[:-1]]
print("step sizes:", ", ".join(f"{NAMES[l]}->{NAMES[l+1]}: {st:.3f}" for l, st in zip(L[:-1], steps)))
print(f"linear model: beta = {rl.x[0]:.3f} logits/level ({400/math.log(10)*rl.x[0]:.0f} Elo/level)")
max_dev = max(abs(st - rl.x[0]) for st in steps)
print(f"largest |step - beta| = {max_dev:.3f} logits (equivalence gate in the handoff: <= 0.15)")
print(f"LR test free vs linear: chi2 = {LR:.2f} on 3 df, p = {1 - stats.chi2.cdf(LR, 3):.3g}")
# BT adequacy: residual deviance of the free model over the 10 pairs (10 obs - 4 params = 6 df)
dev = 0
print("\npair         observed  BT-free pred   linear pred")
for (lo, hi) in pairs:
    k, n = g[(lo, hi)]; p = k / n
    pf = sigmoid(s[hi] - s[lo]); pl = sigmoid(rl.x[0] * (hi - lo))
    dev += 2 * (k * math.log(max(k, 1e-9) / (n * pf)) + (n - k) * math.log(max(n - k, 1e-9) / (n * (1 - pf))))
    print(f"{NAMES[hi]:>11s} vs {NAMES[lo]:<11s} {p:.3f}    {pf:.3f}        {pl:.3f}")
print(f"BT goodness of fit: deviance {dev:.2f} on 6 df, p = {1 - stats.chi2.cdf(dev, 6):.3g}")
# Upset rates by gap
print("\nupset rate (lower rank wins) by gap, pooled:")
by_gap = defaultdict(lambda: [0, 0])
for (lo, hi), (k, n) in g.items():
    by_gap[hi - lo][0] += n - k; by_gap[hi - lo][1] += n
for gap in sorted(by_gap):
    k, n = by_gap[gap]; p, a, b = wilson(k, n)
    print(f"  gap {gap}: {p:.3f} [{a:.3f}, {b:.3f}]")
# per-archetype grandmaster vs novice and expert vs trained
cards = sorted({k[0] for k in gc})
print("\nper archetype: expert>trained, master>trained, grandmaster>trained, trained>novice, grandmaster>novice")
for c in cards:
    f = lambda lo, hi: gc[(c, lo, hi)][0] / gc[(c, lo, hi)][1]
    print(f"  {c:11s} {f(0,1):.2f} {f(0,2):.2f} {f(0,3):.2f} {f(-1,0):.2f} {f(-1,3):.2f}")
json.dump({"s": {str(k): v for k, v in s.items()}, "se": {str(k): v for k, v in se.items()}, "beta": rl.x[0], "LR": LR, "dev": dev, "max_step_dev": max_dev,
           "steps": steps,
           "upset": {str(k): v[0] / v[1] for k, v in by_gap.items()}}, open('data/ladder_fit.json', 'w'), indent=1)
