"""E6a/E6b: is a one-slot specialist weaker than the multi-slot original at the same rank?

Exchange rate (per style) = the rank offset d* at which the core specialist (one slot, the 1-2 schools backing most of
the card's picks) matches the field win rate of its multi-slot original. Measured at an expert baseline (everyone at
level 1) with the specialist swept from -1.5 to +1.5 ranks. Negative d* = the specialist is stronger at equal rank."""
import json
import math
import sys
from collections import defaultdict

import numpy as np
from scipy import stats

sys.path.insert(0, '.')
from stats_lib import binom_logit_fit, load, logit, wilson  # noqa: E402
import harness as H  # noqa: E402

E6 = load('data/E6a_specialist_equal_level.jsonl'); E6b = load('data/E6b_specialist_exchange_rate.jsonl')
field_a = defaultdict(lambda: [0, 0]); h2h = defaultdict(lambda: [0, 0])
for r in E6:
    c = r['cell']
    if r['exp'] == 'E6a':
        field_a[c['variant']][0] += r['win_focus']; field_a[c['variant']][1] += 1
    else:
        h2h[c['variant']][0] += r['win_focus']; h2h[c['variant']][1] += 1
orig = defaultdict(lambda: [0, 0]); sweep = defaultdict(lambda: [0, 0])
for r in E6b:
    c = r['cell']
    if c['variant'] == 'orig':
        orig[c['card']][0] += r['win_focus']; orig[c['card']][1] += 1
    else:
        sweep[(c['card'], c['delta'])][0] += r['win_focus']; sweep[(c['card'], c['delta'])][1] += 1
st = H.init()
D = [-1.5, -1.0, -0.5, 0.0, 0.5, 1.0, 1.5]
rows = []
for card in sorted(orig):
    po = orig[card][0] / orig[card][1]
    xs = np.array(D); k = np.array([sweep[(card, d)][0] for d in D]); n = np.array([sweep[(card, d)][1] for d in D])
    (b, a), _ = binom_logit_fit(xs, k, n, intercept=True)
    d_star = (logit(po) - a) / b
    v = H.specialist_variant(st['cards'][card], st['K'], 'best2')
    lost = sum(1 for dname, o in st['cards'][card]['dimensions'].items() if o and not v['dimensions'].get(dname))
    rows.append(dict(card=card, p_orig=po, p_spec_at0=sweep[(card, 0.0)][0] / sweep[(card, 0.0)][1], slope=b, d_star=d_star,
                     extrapolated=bool(d_star < D[0] or d_star > D[-1]), picks_lost=lost,
                     schools=v['synchronized_capabilities'][0]['capabilities'], slots_orig=len(st['cards'][card]['synchronized_capabilities'])))
print("card        slots  specialist keeps          picks lost  field: original  specialist (same rank)  exchange rate (ranks)")
for r in rows:
    print(f"{r['card']:11s} {r['slots_orig']}      {'+'.join(r['schools']):24s}  {r['picks_lost']}           {r['p_orig']:.3f}            {r['p_spec_at0']:.3f}                   {r['d_star']:+.2f}{' (extrapolated)' if r['extrapolated'] else ''}")
ds = np.array([r['d_star'] for r in rows]); pl = np.array([r['picks_lost'] for r in rows])
lr = stats.linregress(pl, ds)
po_all = sum(orig[c][0] for c in orig) / sum(orig[c][1] for c in orig)
ps_all = sum(sweep[(c, 0.0)][0] for c in orig) / sum(sweep[(c, 0.0)][1] for c in orig)
summary = {"mean_d_star": float(ds.mean()), "sd_d_star": float(ds.std(ddof=1)), "median_d_star": float(np.median(ds)),
           "min_d_star": float(ds.min()), "max_d_star": float(ds.max()), "any_extrapolated": bool(any(r['extrapolated'] for r in rows)),
           "picks_lost_slope": lr.slope, "picks_lost_slope_se": lr.stderr, "picks_lost_R2": lr.rvalue ** 2,
           "field_expert_orig": po_all, "field_expert_spec": ps_all,
           "field_trained": {k: v[0] / v[1] for k, v in field_a.items()}, "field_trained_n": {k: v[1] for k, v in field_a.items()},
           "h2h_spec2": wilson(*h2h['spec2']), "h2h_spec2_n": h2h['spec2'][1]}
print(f"\nmean exchange rate {ds.mean():+.2f} ranks (sd {ds.std(ddof=1):.2f}, median {np.median(ds):+.2f}, range {ds.min():+.2f}..{ds.max():+.2f})")
print(f"exchange rate vs picks lost: {lr.slope:+.2f} ranks per pick (se {lr.stderr:.2f}), R^2 {lr.rvalue**2:.2f}")
print(f"field win rate at expert: originals {po_all:.3f}, specialists {ps_all:.3f}; at trained (E6a): {summary['field_trained']}")
print(f"head-to-head, core specialist vs its own original (trained): {summary['h2h_spec2'][0]:.3f} [{summary['h2h_spec2'][1]:.3f}, {summary['h2h_spec2'][2]:.3f}]")
json.dump({"rows": rows, **summary}, open('data/spec_fit.json', 'w'), indent=1)
