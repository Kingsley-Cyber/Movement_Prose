"""E5b: how many rank levels does it take to cancel a style counter? Also tests whether style and rank are additive on
the logit scale (a single Bradley-Terry 'strength' = style matchup term + beta * level)."""
import sys, json, math
from collections import defaultdict
import numpy as np
from scipy import optimize, stats
sys.path.insert(0, '.')
from stats_lib import *

beta_ladder = json.load(open('data/ladder_fit.json'))['beta']
P0 = json.load(open('data/E5a_matrix.json')); names = P0['names']; PM = np.array(P0['P'])
R = load('data/E5b_style_counter_in_levels.jsonl')
g = defaultdict(lambda: [0, 0])
for r in R:
    c = r['cell']; g[(c['fav'], c['dog'], c['delta'])][0] += r['win_focus']; g[(c['fav'], c['dog'], c['delta'])][1] += 1
pairs = sorted({(f, d) for f, d, _ in g})
D = [0, 0.5, 1, 1.5, 2, 2.5, 3]

def nll_pair(params, f, d, common_b=None):
    a, b = (params[0], common_b) if common_b is not None else params
    tot = 0
    for x in D:
        k, n = g[(f, d, x)]; eta = a + b * x
        tot -= k * eta - n * np.logaddexp(0, eta)
    return tot

rows = []; nll2 = 0
for f, d in pairs:
    res = optimize.minimize(nll_pair, np.array([-1.0, 0.7]), args=(f, d), method="BFGS")
    a, b = res.x; nll2 += res.fun
    # Fisher information for (a, b)
    I = np.zeros((2, 2))
    for x in D:
        k, n = g[(f, d, x)]; p = sigmoid(a + b * x); v = np.array([1, x]); I += n * p * (1 - p) * np.outer(v, v)
    cov = np.linalg.inv(I)
    d50 = -a / b
    grad = np.array([-1 / b, a / b ** 2]); se50 = math.sqrt(grad @ cov @ grad)
    p_fav = PM[names.index(f), names.index(d)]
    rows.append(dict(fav=f, dog=d, p_fav_trained=p_fav, a=a, b=b, b_se=math.sqrt(cov[1, 1]), d50=d50, d50_se=se50,
                     predicted_d50=logit(p_fav) / beta_ladder, p_dog=[g[(f, d, x)][0] / g[(f, d, x)][1] for x in D]))
# common-slope model
def nll_common(params):
    b = params[-1]; return sum(nll_pair([params[i]], f, d, common_b=b) for i, (f, d) in enumerate(pairs))
rc = optimize.minimize(nll_common, np.array([-1.0] * len(pairs) + [0.7]), method="BFGS")
LR = 2 * (rc.fun - nll2); dfree = len(pairs) - 1
print(f"common slope across style pairs: beta = {rc.x[-1]:.3f} logits/level (mirror ladder: {beta_ladder:.3f})")
print(f"LR test pair-specific vs common slope: chi2 = {LR:.1f} on {dfree} df, p = {1 - stats.chi2.cdf(LR, dfree):.3g}")
print("\nfavourite > underdog (trained P)   dog P at +0 ... +3           slope (se)     levels to cancel (se)  predicted from P_fav/beta")
for r in sorted(rows, key=lambda r: -r['p_fav_trained']):
    print(f"{r['fav']:>10s} > {r['dog']:<10s} ({r['p_fav_trained']:.2f})  " + " ".join(f"{p:.2f}" for p in r['p_dog']) +
          f"   {r['b']:.2f} ({r['b_se']:.2f})   {r['d50']:.2f} ({r['d50_se']:.2f})          {r['predicted_d50']:.2f}")
x = np.array([r['predicted_d50'] for r in rows]); y = np.array([r['d50'] for r in rows])
sl, ic, rr, pv, se = stats.linregress(x, y)
print(f"\nmeasured vs predicted levels-to-cancel: slope {sl:.2f} (se {se:.2f}), intercept {ic:.2f}, R^2 {rr**2:.2f}")
# distribution of style-counter strength over all 66 trained pairs, in levels
L = np.array([abs(logit(PM[i, j])) / beta_ladder for i in range(12) for j in range(i + 1, 12)])
print(f"all 66 trained matchups: counter size in levels  median {np.median(L):.2f}, mean {L.mean():.2f}, 90th pct {np.percentile(L, 90):.2f}, max {L.max():.2f}")
print(f"  share of matchups worth <= 0.5 level {np.mean(L <= 0.5):.0%}, 0.5-1 level {np.mean((L > 0.5) & (L <= 1)):.0%}, 1-2 levels {np.mean((L > 1) & (L <= 2)):.0%}, > 2 levels {np.mean(L > 2):.0%}")
json.dump({"rows": rows, "beta_common": rc.x[-1], "beta_ladder": beta_ladder, "LR": LR, "df": dfree, "levels_all_pairs": L.tolist()},
          open('data/counter_fit.json', 'w'), indent=1)
