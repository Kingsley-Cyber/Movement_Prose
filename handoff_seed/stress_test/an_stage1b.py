import json, sys, math, itertools
from collections import defaultdict
import numpy as np
sys.path.insert(0, '.')
from stats_lib import *

A = ["detroit","donnell","greco","jiujitsu","karate","macklin","maleek","philly","sanda_judo","street","thai","wrestler"]
E5 = load('data/E5a_round_robin_trained.jsonl')
W = defaultdict(lambda: [0, 0])
for r in E5:
    c = r['cell']; W[(c['a'], c['b'])][0] += r['win_focus']; W[(c['a'], c['b'])][1] += 1
P = np.full((12, 12), 0.5)
pairs = []
for (a, b), (k, n) in W.items():
    i, j = A.index(a), A.index(b)
    P[i, j] = k / n; P[j, i] = 1 - k / n
    pairs.append((a, b, k, n))
print("Round robin (trained, 100 seeds/pair). Row win%:")
print("".ljust(11) + " ".join(x[:5].rjust(5) for x in A) + "   mean")
for i, a in enumerate(A):
    print(a.ljust(11) + " ".join(f"{P[i,j]:.2f}".rjust(5) if i != j else "  -  " for j in range(12)) + f"   {np.mean([P[i,j] for j in range(12) if j!=i]):.3f}")
lop = sorted([(max(P[i, j], P[j, i]), A[i] if P[i, j] > P[j, i] else A[j], A[j] if P[i, j] > P[j, i] else A[i]) for i, j in itertools.combinations(range(12), 2)], reverse=True)
print("\nmost lopsided pairs (fav, dog, P_fav):")
for p, f, d in lop[:14]:
    print(f"  {f:11s} > {d:11s} {p:.2f}  ({elo(p):.0f} Elo, {logit(p):.2f} logits)")
h = hodge(pairs)
print("\nHodge (trained): transitive share %.3f cyclic share %.3f, intransitive triads %d/%d" % (h['transitive_share'], h['cyclic_share'], h['intransitive_triads'], h['triads']))
print("potential:", {k: round(v, 2) for k, v in sorted(h['potential'].items(), key=lambda x: -x[1])})
ne = nash_symmetric(P, A)
print("Nash (trained roster):", {k: round(v, 3) for k, v in ne['mix'].items()}, "value", round(ne['value'], 4))
json.dump({"P": P.tolist(), "names": A}, open('data/E5a_matrix.json', 'w'))

# E6a: specialist variants at equal level
E6 = load('data/E6a_specialist_equal_level.jsonl')
g = defaultdict(lambda: [0, 0]); h2h = defaultdict(lambda: [0, 0])
for r in E6:
    c = r['cell']
    if r['exp'] == 'E6a':
        g[(c['card'], c['variant'])][0] += r['win_focus']; g[(c['card'], c['variant'])][1] += 1
    else:
        h2h[(c['card'], c['variant'])][0] += r['win_focus']; h2h[(c['card'], c['variant'])][1] += 1
print("\nSpecialist variants vs the roster (11 opps x 40 seeds) and head-to-head vs own original (200 seeds):")
print("card        orig   spec(plan A)  spec2(core)   h2h spec  h2h spec2")
dsum = defaultdict(list)
for card in A:
    if card == 'street': continue
    o = g[(card, 'orig')]; s = g[(card, 'spec')]; s2 = g[(card, 'spec2')]
    hs = h2h[(card, 'spec')]; hs2 = h2h[(card, 'spec2')]
    print(f"{card:11s} {o[0]/o[1]:.3f}  {s[0]/s[1]:.3f}        {s2[0]/s2[1]:.3f}        {hs[0]/hs[1]:.3f}     {hs2[0]/hs2[1]:.3f}")
    dsum['spec'].append(logit(s[0]/s[1]) - logit(o[0]/o[1])); dsum['spec2'].append(logit(s2[0]/s2[1]) - logit(o[0]/o[1]))
    dsum['h2h_spec'].append(logit(hs[0]/hs[1])); dsum['h2h_spec2'].append(logit(hs2[0]/hs2[1]))
for k, v in dsum.items():
    v = np.array(v); print(f"mean logit shift {k}: {v.mean():.3f} (sd {v.std(ddof=1):.3f}) -> P {sigmoid(v.mean()):.3f}")
