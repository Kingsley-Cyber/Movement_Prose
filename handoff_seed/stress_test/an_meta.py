"""Stage 3. E7: equal-rank meta game of 12 multi-slot originals + 11 one-slot specialists (all trained): Nash
equilibrium by linear programming with a parametric bootstrap of its stability, noise-corrected Hodge decomposition.
E8: mixed-rank tournament (12 archetypes x ranks trained/expert/master): how transitive is a world with ranks, and
are style and rank additive on the log-odds scale?"""
import json
import math
import os
import sys
from collections import defaultdict

import numpy as np
from scipy import optimize, stats

sys.path.insert(0, '.')
from stats_lib import hodge_noise_corrected, load, nash_symmetric  # noqa: E402

# ---------------- E7 (pool every available replicate: E7 is rank-free, so runs at any theta are the same experiment)
files = ['data/E7_meta_tournament.jsonl'] + [p for p in ('data/E7_meta_tournament_seeds1to60.jsonl',) if os.path.exists(p)]
W = defaultdict(lambda: [0, 0])
for f in files:
    for r in load(f):
        c = r['cell']; W[(c['a'], c['b'])][0] += r['win_focus']; W[(c['a'], c['b'])][1] += 1
builds = sorted({k[0] for k in W} | {k[1] for k in W})
m = len(builds); P = np.full((m, m), 0.5); N = np.zeros((m, m))
pairs = []
for (a, b), (k, n) in W.items():
    i, j = builds.index(a), builds.index(b); P[i, j] = k / n; P[j, i] = 1 - k / n; N[i, j] = N[j, i] = n; pairs.append((a, b, k, n))
ne = nash_symmetric(P, builds)
rs = np.random.default_rng(17)
boot_w = defaultdict(list); spec_in = 0; B = 300
for _ in range(B):
    Pb = np.full((m, m), 0.5)
    for i in range(m):
        for j in range(i + 1, m):
            kb = rs.binomial(int(N[i, j]), P[i, j]); Pb[i, j] = kb / N[i, j]; Pb[j, i] = 1 - Pb[i, j]
    nb = nash_symmetric(Pb, builds)
    for bname in builds:
        boot_w[bname].append(nb['mix'].get(bname, 0.0))
    spec_in += any(k.endswith(':spec2') for k in nb['mix'])
h = hodge_noise_corrected(pairs)
rowmean = {b: float(np.mean([P[builds.index(b), j] for j in range(m) if j != builds.index(b)])) for b in builds}
dominated = [b for b in builds if all(P[builds.index(b), j] < 0.5 for j in range(m) if j != builds.index(b))]
dominant = [b for b in builds if all(P[builds.index(b), j] > 0.5 for j in range(m) if j != builds.index(b))]
weights_ci = {b: (float(np.percentile(v, 5)), float(np.percentile(v, 95))) for b, v in boot_w.items() if max(v) > 0}
support_freq = {b: float(np.mean([w > 1e-4 for w in v])) for b, v in boot_w.items() if max(v) > 0}
weights_min = {b: float(min(v)) for b, v in boot_w.items() if max(v) > 0}
print("  share of replicates in which each build is in the equilibrium:", {k: round(v, 2) for k, v in sorted(support_freq.items(), key=lambda x: -x[1])})
print(f"E7 equal-rank meta: {m} builds, {int(N[0,1])} fights per pair, files {files}")
print("  Nash mix:", {k: round(v, 3) for k, v in sorted(ne['mix'].items(), key=lambda x: -x[1])})
print(f"  bootstrap ({B}): at least one specialist in the equilibrium in {spec_in}/{B}; 90% ranges of weights:",
      {k: (round(a, 2), round(b, 2)) for k, (a, b) in sorted(weights_ci.items(), key=lambda x: -x[1][1])})
print(f"  Hodge: transitive {h['transitive_share']:.3f} (corrected {h['transitive_share_corrected']:.3f})")
print("  dominant:", dominant or "none", " dominated:", dominated or "none")
json.dump({"builds": builds, "P": P.tolist(), "nash": ne, "nash_boot": {"B": B, "spec_in": spec_in, "weights_90": weights_ci, "support_freq": support_freq, "weights_min": weights_min},
           "hodge": {k: v for k, v in h.items() if k != 'potential'}, "rowmean": rowmean, "dominated": dominated, "dominant": dominant,
           "fights_per_pair": int(N[0, 1])}, open('data/E7_fit.json', 'w'), indent=1, default=float)

# ---------------- E8
R8 = load('data/E8_mixed_rank_tournament.jsonl')
W8 = defaultdict(lambda: [0, 0])
for r in R8:
    c = r['cell']; W8[(c['a'], c['b'])][0] += r['win_focus']; W8[(c['a'], c['b'])][1] += 1
pairs8 = [(a, b, k, n) for (a, b), (k, n) in W8.items()]
h8 = hodge_noise_corrected(pairs8, boot=200)
print("\nE8 mixed-rank tournament (12 archetypes x ranks trained/expert/master, 40 seeds/pair)")
print(f"  Hodge: transitive {h8['transitive_share']:.3f} (corrected {h8['transitive_share_corrected']:.3f}); cyclic corrected {h8['cyclic_share_corrected']:.3f}; "
      f"intransitive triads {h8['intransitive_triads']}/{h8['triads']}")
gap = defaultdict(lambda: [0, 0, 0, 0])
for (a, b), (k, n) in W8.items():
    ca, la = a.split('@'); cb, lb = b.split('@'); la, lb = int(la), int(lb)
    if ca == cb or la == lb:
        continue
    hi_wins = k if la > lb else n - k
    gp = abs(la - lb)
    gap[gp][0] += hi_wins; gap[gp][1] += n; gap[gp][2] += int(hi_wins / n > 0.5); gap[gp][3] += 1
for gp in sorted(gap):
    w, n, fav, npairs = gap[gp]
    print(f"  different styles, rank gap {gp}: higher rank wins {w/n:.3f}; favourite in {fav}/{npairs} matchups ({fav/npairs:.0%})")
keyed = defaultdict(list)
for (a, b), (k, n) in W8.items():
    ca, la = a.split('@'); cb, lb = b.split('@')
    if ca == cb:
        continue
    key = tuple(sorted((ca, cb))); sign = 1 if ca == key[0] else -1
    keyed[key].append((sign, int(la) - int(lb), k, n))


def nll_add(beta, per_pair_beta=False):
    tot = 0.0; ms = {}
    for key, obs in keyed.items():
        def f(par):
            mm = par[0]; bb = par[1] if per_pair_beta else beta
            s = 0.0
            for sign, dl, k, n in obs:
                eta = sign * mm + bb * dl
                s -= k * eta - n * np.logaddexp(0, eta)
            return s
        r = optimize.minimize(f, np.array([0.0, 0.7]) if per_pair_beta else np.array([0.0]), method="BFGS")
        tot += r.fun; ms[key] = r.x
    return tot, ms


best = optimize.minimize_scalar(lambda b: nll_add(b)[0], bounds=(0.2, 1.5), method='bounded')
nll_free, ms_free = nll_add(None, per_pair_beta=True)
LR = 2 * (best.fun - nll_free); df = len(keyed) - 1
betas = np.array([v[1] for v in ms_free.values()])
print(f"  style+rank additive model: common beta = {best.x:.3f} logits/rank")
print(f"  LR test matchup-specific slopes vs common: chi2 = {LR:.1f} on {df} df, p = {1 - stats.chi2.cdf(LR, df):.3g}; slopes IQR {np.percentile(betas,25):.2f}-{np.percentile(betas,75):.2f}")
json.dump({"hodge": {k: v for k, v in h8.items() if k != 'potential'}, "gap": {str(k): v for k, v in gap.items()}, "beta_common": best.x, "LR": LR, "df": df,
           "betas": betas.tolist()}, open('data/E8_fit.json', 'w'), indent=1, default=float)
