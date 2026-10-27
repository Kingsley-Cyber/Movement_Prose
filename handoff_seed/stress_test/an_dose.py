import json, sys, math
from collections import defaultdict
import numpy as np
sys.path.insert(0, '.')
from stats_lib import *

def analyze(path, label):
    R = load(path)
    g = defaultdict(lambda: [0, 0]); gc = defaultdict(lambda: [0, 0])
    for r in R:
        c = r['cell']; key = (c['theta'], c['delta'])
        g[key][0] += r['win_focus']; g[key][1] += 1
        gc[(c['card'],) + key][0] += r['win_focus']; gc[(c['card'],) + key][1] += 1
    cards = sorted({k[0] for k in gc})
    print(f"\n=== {label} ===   pooled P(higher wins) | random-effects over 12 archetypes: mean P, tau (logits), I2, min..max archetype")
    out = {}
    for th in sorted({k[0] for k in g}):
        for d in (1, 2, 3):
            k, n = g[(th, d)]
            ys, vs = zip(*[cell_logodds(*gc[(c, th, d)]) for c in cards])
            re = dersimonian_laird(ys, vs)
            ps = [gc[(c, th, d)][0] / gc[(c, th, d)][1] for c in cards]
            out[(th, d)] = dict(p=k / n, mu=sigmoid(re['mu']), tau=re['tau'], I2=re['I2'], lo=min(ps), hi=max(ps))
            print(f"theta={th:<4} d={d}: pooled {k/n:.3f} | RE {sigmoid(re['mu']):.3f} tau={re['tau']:.3f} I2={re['I2']:.2f} range {min(ps):.2f}..{max(ps):.2f} (worst {cards[int(np.argmin(ps))]})")
    return out, gc, cards

o0, g0, cards = analyze('data/E1_dose_response.jsonl', 'V0: mastery through readiness/multiplier (inside the clamps)')
o1, g1, _ = analyze('data/E1v1_dose_response.jsonl', 'V1: odds-space mastery (after the style math, outside the clamps)')
print("\nper archetype P(+1) at theta=2 / theta=3: V0 | V1")
for c in cards:
    f = lambda g, th, d: g[(c, th, d)][0] / g[(c, th, d)][1]
    print(c.ljust(11), f"{f(g0,2.0,1):.2f} {f(g0,3.0,1):.2f} | {f(g1,2.0,1):.2f} {f(g1,3.0,1):.2f}   d3: {f(g0,3.0,3):.2f} | {f(g1,3.0,3):.2f}")
