"""E3: full 2^5 factorial of mastery components at a +2 gap (V2). Response = logit P(higher level wins), pooled over
12 archetypes (60 seeds each). Main effects, interactions and Sobol variance shares. E3b: V0 power-only, clamp on/off."""
import sys, json, itertools, math
from collections import defaultdict
import numpy as np
sys.path.insert(0, '.')
from stats_lib import *

R = load('data/E3_components.jsonl')
g = defaultdict(lambda: [0, 0]); gb = defaultdict(lambda: [0, 0]); gbc = defaultdict(lambda: [0, 0])
for r in R:
    c = r['cell']
    if r['exp'] == 'E3':
        key = frozenset(c['comps']); g[key][0] += r['win_focus']; g[key][1] += 1
    else:
        gb[c['clamp_off']][0] += r['win_focus']; gb[c['clamp_off']][1] += 1
        gbc[(c['card'], c['clamp_off'])][0] += r['win_focus']; gbc[(c['card'], c['clamp_off'])][1] += 1
F = ["odds", "cnt", "pow", "tough", "shrink"]
resp = {k: cell_logodds(*v)[0] for k, v in g.items()}
print("single components alone (+2 gap):")
for f in [()] + [(x,) for x in F] + [tuple(F)]:
    k, n = g[frozenset(f)]; p, lo, hi = wilson(k, n)
    print(f"  {'+'.join(f) or 'none':32s} P={p:.3f} [{lo:.3f},{hi:.3f}]  logit {resp[frozenset(f)]:+.3f}")
sob = sobol_from_factorial(resp)
tot_eff = sum(2 * sob['main_effects'][f] for f in F)
eff_share = {f: 2 * sob['main_effects'][f] / tot_eff for f in F}
print("\nmain effects (full on-vs-off logit effect, averaged over the design) and shares:")
for f in F:
    print(f"  {f:7s} effect {2*sob['main_effects'][f]:+.3f} logits  share of the rank effect {eff_share[f]:.1%}  variance share (Sobol first order) {sob['first_order'][f]:.1%}")
big = sorted(sob['interactions'].items(), key=lambda x: -abs(x[1]))[:5]
print("largest interactions:", ", ".join(f"{k} {v:+.3f}" for k, v in big))
# additivity: compare the all-on logit with the sum of single-component logits (minus none)
none = resp[frozenset()]
add = none + sum(resp[frozenset([f])] - none for f in F)
print(f"additivity check: sum of single effects predicts logit {add:.3f} vs observed all-on {resp[frozenset(F)]:.3f}")
print("\nE3b (V0 power-only at +2): engine clamp ON  P=%.3f | clamp OFF  P=%.3f" % (gb[False][0] / gb[False][1], gb[True][0] / gb[True][1]))
print("  per archetype (on/off):", {c: (round(gbc[(c, False)][0] / gbc[(c, False)][1], 2), round(gbc[(c, True)][0] / gbc[(c, True)][1], 2))
                                    for c in sorted({k[0] for k in gbc})})
json.dump({"main": sob['main_effects'], "effect_share": eff_share, "first": sob['first_order'], "total": sob['total'],
           "single": {"+".join(sorted(k)) or "none": v for k, v in resp.items()},
           "E3b": {"clamp_on": gb[False][0] / gb[False][1], "clamp_off": gb[True][0] / gb[True][1],
                   "per_style": {c: [gbc[(c, False)][0] / gbc[(c, False)][1], gbc[(c, True)][0] / gbc[(c, True)][1]] for c in sorted({k[0] for k in gbc})}}},
          open('data/components_fit.json', 'w'), indent=1)
