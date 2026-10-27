import json, sys, math, itertools
from collections import defaultdict
import numpy as np
sys.path.insert(0, '.')
from stats_lib import *

E1 = load('data/E1_dose_response.jsonl')
g = defaultdict(lambda: [0, 0])
ga = defaultdict(lambda: [0, 0])
for r in E1:
    c = r['cell']
    g[(c['theta'], c['delta'])][0] += r['win_focus']; g[(c['theta'], c['delta'])][1] += 1
    ga[(c['card'], c['theta'], c['delta'])][0] += r['win_focus']; ga[(c['card'], c['theta'], c['delta'])][1] += 1
print("E1 pooled P(higher wins) by theta x delta  [Wilson 95%]")
for th in [0.5, 1, 1.5, 2, 3]:
    row = []
    for d in [1, 2, 3]:
        k, n = g[(th, d)]
        p, lo, hi = wilson(k, n)
        row.append(f"d{d}: {p:.3f} [{lo:.3f},{hi:.3f}]")
    print(f"theta={th}: " + "  ".join(row))
# Per-archetype at theta=1
print("\nper archetype (theta=1.0):")
for card in sorted({r['cell']['card'] for r in E1}):
    print(card.ljust(11), " ".join(f"{ga[(card,1.0,d)][0]/ga[(card,1.0,d)][1]:.2f}" for d in [1,2,3]), "|",
          " ".join(f"{ga[(card,th,1)][0]/ga[(card,th,1)][1]:.2f}" for th in [0.5,1,1.5,2,3]))
# logistic fits: logit p = beta * (theta*delta) per delta, i.e. check linearity in delta
x=[];k=[];n=[]
for (th,d),(kk,nn) in g.items():
    x.append(th*d); k.append(kk); n.append(nn)
b, se = binom_logit_fit(x, k, n)
print("\nfit logit p = b*theta*delta: b=%.4f se=%.4f" % (b[0], se[0]))
# deviance-based lack-of-fit
x=np.array(x);k=np.array(k);n=np.array(n)
p=1/(1+np.exp(-b[0]*x))
dev = 2*np.sum(np.where(k>0,k*np.log(np.maximum(k,1e-9)/(n*p)),0)+np.where(n-k>0,(n-k)*np.log(np.maximum(n-k,1e-9)/(n*(1-p))),0))
from scipy import stats as st
print("deviance %.1f on %d df, p=%.3g" % (dev, len(x)-1, 1-st.chi2.cdf(dev, len(x)-1)))
for (th,d),(kk,nn) in sorted(g.items()):
    print(th, d, round(kk/nn,3), "pred", round(1/(1+math.exp(-b[0]*th*d)),3))
