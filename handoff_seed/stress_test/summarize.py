"""Collect every number the report uses into results/results.json, write the markdown tables the report embeds
(results/tables/*.md) and draw the three figures (results/figures/*.png). Run after all experiments and analyses."""
import glob
import json
import math
import os
import sys
from collections import defaultdict

import numpy as np
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from stats_lib import cell_logodds, dersimonian_laird, hodge_noise_corrected, load, logit, wilson  # noqa: E402

D = os.path.join(HERE, "data")
OUT = os.path.join(HERE, "results")
os.makedirs(os.path.join(OUT, "tables"), exist_ok=True)
os.makedirs(os.path.join(OUT, "figures"), exist_ok=True)
J = lambda name: json.load(open(os.path.join(D, name)))  # noqa: E731
pct = lambda p: f"{100 * p:.1f}%"  # noqa: E731
R = {}

# ------------------------------------------------------------------ volume (fights behind the numbers reported)
n_jsonl = {os.path.basename(p)[:-6]: sum(1 for _ in open(p)) for p in sorted(glob.glob(os.path.join(D, "*.jsonl")))}
extra = {"saturation audit": 1200, "theory (race model, logged)": 7200, "per-slot inheritance (E9)": 6600,
         "rank-resistant matchups (E11)": 6000, "wrestler vs jiu-jitsu mechanism (E11b, logged)": 1200, "controls + resolver tests": 5 * 32 + 120}
R["volume"] = {"jsonl": n_jsonl, "other": extra, "total": sum(n_jsonl.values()) + sum(extra.values())}

# ------------------------------------------------------------------ controls (hashes recorded from control.py / test_slot.py runs)
R["control"] = {"hash": "104086e61e691c8c", "modes": ["original engine", "wrapped engine, no mastery", "V0 mastery all zero", "V1 mastery all zero",
                                                     "V2 mastery all zero (instrumented contests)"], "identical": True,
                "per_slot_resolver": "equal per-slot levels reproduce uniform mastery byte-for-byte (4 archetypes x 10 seeds); unequal levels change the log"}
R["saturation"] = J("diag_saturation.json")
R["calibration"] = J("calibration.json")

# ------------------------------------------------------------------ model comparison on two fresh seed sets
CONF = {"V0": {"theta": 2.45, "A": ["E1v0confirm.jsonl"], "B": ["E1v0confirm2.jsonl"]},
        "V1": {"theta": 0.785, "A": ["E1v1confirm.jsonl"], "B": ["E1v1confirm2.jsonl"]},
        "V2": {"theta": 0.80, "A": ["E1v2confirm080.jsonl"], "B": ["E10_validate_theta080.jsonl"]}}


def mirror_cells(files):
    gc = defaultdict(lambda: [0, 0])
    for f in files:
        for r in load(os.path.join(D, f)):
            if r["exp"] == "V_cross":
                continue
            c = r["cell"]; gc[(c["card"], c["delta"])][0] += r["win_focus"]; gc[(c["card"], c["delta"])][1] += 1
    return gc


def spread(gc, d):
    cards = sorted({k[0] for k in gc})
    ys, vs = zip(*[cell_logodds(*gc[(c, d)]) for c in cards])
    re = dersimonian_laird(ys, vs)
    ps = {c: gc[(c, d)][0] / gc[(c, d)][1] for c in cards}
    k = sum(gc[(c, d)][0] for c in cards); n = sum(gc[(c, d)][1] for c in cards)
    return {"p": k / n, "ci": wilson(k, n)[1:], "tau": re["tau"], "I2": re["I2"], "min": min(ps.values()), "argmin": min(ps, key=ps.get),
            "max": max(ps.values()), "argmax": max(ps, key=ps.get), "per": ps, "n": n}


R["confirm"] = {}
for mname, cfg in CONF.items():
    A_, B_ = mirror_cells(cfg["A"]), mirror_cells(cfg["B"])
    P_ = mirror_cells(cfg["A"] + cfg["B"])
    R["confirm"][mname] = {"theta": cfg["theta"], **{f"+{d}": {"A": spread(A_, d), "B": spread(B_, d), "pooled": spread(P_, d)} for d in (1, 2, 3)}}
c0, c2 = R["confirm"]["V0"], R["confirm"]["V2"]
R["confirm_summary"] = {f"tau_drop_+{d}": 1 - c2[f"+{d}"]["pooled"]["tau"] / c0[f"+{d}"]["pooled"]["tau"] for d in (2, 3)}

# ------------------------------------------------------------------ validation (selection set 7001-7400; holdout 30001-30400)
R["validation"] = J("validate_fit.json")


def cross_fav(path):
    gp = defaultdict(lambda: [0, 0])
    for r in load(os.path.join(D, path)):
        if r["exp"] == "V_cross":
            c = r["cell"]; gp[(c["hi"], c["lo"], c["delta"])][0] += r["win_focus"]; gp[(c["hi"], c["lo"], c["delta"])][1] += 1
    out = {}
    for d in (1, 2, 3):
        cells = {k: v[0] / v[1] for k, v in gp.items() if k[2] == d}
        worst = min(cells, key=cells.get)
        out[d] = {"fav_share": float(np.mean([p > 0.5 for p in cells.values()])), "worst_p": cells[worst], "worst": f"{worst[0]} (+{d}) vs {worst[1]}",
                  "n_matchups": len(cells)}
    return out


R["validation_fav"] = {"holdout": cross_fav("E10_holdout_theta080.jsonl"), "selection": cross_fav("E10_validate_theta080.jsonl")}

# ------------------------------------------------------------------ ladder (theta 0.80, seeds 20001-20200)
lad = J("ladder_fit.json")
R["ladder"] = lad
g2 = defaultdict(lambda: [0, 0])
for r in load(os.path.join(D, "E2_ladder.jsonl")):
    c = r["cell"]; g2[(c["lo"], c["hi"])][0] += r["win_focus"]; g2[(c["lo"], c["hi"])][1] += 1
R["ladder"]["pairs"] = {f"{lo}|{hi}": v[0] / v[1] for (lo, hi), v in g2.items()}
R["ladder"]["LR_p"] = float(1 - stats.chi2.cdf(lad["LR"], 3))
R["ladder"]["dev_p"] = float(1 - stats.chi2.cdf(lad["dev"], 6))
R["ladder"]["elo_per_rank"] = 400 / math.log(10) * lad["beta"]

# ------------------------------------------------------------------ components
comp = J("components_fit.json")
gs = defaultdict(lambda: [0, 0])
for r in load(os.path.join(D, "E3_components.jsonl")):
    if r["exp"] == "E3":
        key = "+".join(sorted(r["cell"]["comps"])) or "none"
        gs[key][0] += r["win_focus"]; gs[key][1] += 1
comp["single_P"] = {k: wilson(*v) for k, v in gs.items() if k.count("+") in (0, 4) or k == "none"}
R["components"] = comp

# ------------------------------------------------------------------ robustness, counters
R["robustness"] = J("robustness_fit.json")
R["counters"] = J("counter_fit.json")
R["counters"]["LR_p"] = float(1 - stats.chi2.cdf(R["counters"]["LR"], R["counters"]["df"]))
L = np.array(R["counters"]["levels_all_pairs"])
R["counters"]["dist"] = {"median": float(np.median(L)), "mean": float(L.mean()), "p90": float(np.percentile(L, 90)), "max": float(L.max()),
                         "le_0.5": float(np.mean(L <= 0.5)), "0.5_1": float(np.mean((L > 0.5) & (L <= 1))), "1_2": float(np.mean((L > 1) & (L <= 2))),
                         "gt_2": float(np.mean(L > 2))}
rows = R["counters"]["rows"]
x = np.array([r["predicted_d50"] for r in rows]); y = np.array([r["d50"] for r in rows])
lr = stats.linregress(x, y)
R["counters"]["pred_vs_meas"] = {"slope": lr.slope, "slope_se": lr.stderr, "intercept": lr.intercept, "R2": lr.rvalue ** 2}
hard = [r["d50"] for r in rows if r["p_fav_trained"] >= 0.70]
R["counters"]["hard_counter_levels"] = {"n": len(hard), "min": min(hard), "median": float(np.median(hard)), "max": max(hard)}
R["counters"]["slope_range"] = [min(r["b"] for r in rows), max(r["b"] for r in rows)]

# ------------------------------------------------------------------ specialists, tournaments, slots
R["specialists"] = J("spec_fit.json")
R["E7"] = J("E7_fit.json")
sp = [v for k, v in R["E7"]["rowmean"].items() if k.endswith(":spec2")]; og = [v for k, v in R["E7"]["rowmean"].items() if k.endswith(":orig")]
R["E7"]["mean_spec"], R["E7"]["mean_orig"] = float(np.mean(sp)), float(np.mean(og))
R["E8"] = J("E8_fit.json")
R["E8"]["LR_p"] = float(1 - stats.chi2.cdf(R["E8"]["LR"], R["E8"]["df"]))
R["E8"]["gap_summary"] = {k: {"higher_wins": v[0] / v[1], "fav_share": v[2] / v[3], "n_matchups": v[3]} for k, v in R["E8"]["gap"].items()}
R["E9"] = J("E9_fit.json")
x9 = np.array([logit(r["pred"]) for r in R["E9"]]); y9 = np.array([logit(r["p"]) for r in R["E9"]])
s9 = stats.linregress(x9, y9)
R["E9_summary"] = {"slope": s9.slope, "slope_se": s9.stderr, "intercept": s9.intercept, "R2": s9.rvalue ** 2,
                   "by_cfg": {cfg: {"p": float(np.mean([r["p"] for r in R["E9"] if r["cfg"] == cfg])),
                                    "pred": float(np.mean([r["pred"] for r in R["E9"] if r["cfg"] == cfg])),
                                    "lu": float(np.mean([r["lu"] for r in R["E9"] if r["cfg"] == cfg])),
                                    "slot1": float(np.mean([r["share"][0] for r in R["E9"] if r["cfg"] == cfg]))} for cfg in ("uniform", "front", "back")}}

# trained round robin structure (E5a)
W = defaultdict(lambda: [0, 0])
for r in load(os.path.join(D, "E5a_round_robin_trained.jsonl")):
    c = r["cell"]; W[(c["a"], c["b"])][0] += r["win_focus"]; W[(c["a"], c["b"])][1] += 1
h5 = hodge_noise_corrected([(a, b, k, n) for (a, b), (k, n) in W.items()])
R["E5a_hodge"] = {k: v for k, v in h5.items() if k != "potential"}

# theory (36 style x gap cells at theta 0.80): overall and within-gap fit
th = J("theory_rows.json")
lg = lambda p: np.log((np.asarray(p) + 1e-3) / (1 - np.asarray(p) + 1e-3))  # noqa: E731
sim = np.array([r["sim"] for r in th]); p1 = np.array([r["pred"] for r in th]); p2 = np.array([r["pred_compound"] for r in th])
gaps = np.array([r["d"] for r in th])
a1 = stats.linregress(lg(p1), lg(sim)); a2 = stats.linregress(lg(p2), lg(sim))
gap_means = np.array([lg(sim)[gaps == g].mean() for g in gaps])
r2_gap_only = 1 - np.sum((lg(sim) - gap_means) ** 2) / np.sum((lg(sim) - lg(sim).mean()) ** 2)
within = {int(g): float(stats.linregress(lg(p2)[gaps == g], lg(sim)[gaps == g]).rvalue ** 2) for g in (1, 2, 3)}
R["theory"] = {"points": {"R2": a1.rvalue ** 2, "slope": a1.slope, "slope_se": a1.stderr, "mae": float(np.mean(np.abs(sim - p1)))},
               "compound": {"R2": a2.rvalue ** 2, "slope": a2.slope, "slope_se": a2.stderr, "mae": float(np.mean(np.abs(sim - p2)))},
               "R2_rank_gap_only": float(r2_gap_only), "R2_within_gap_compound": within, "rows": th}

R["E11"] = J("E11_rank_resistant.json")
R["E11b"] = J("E11b_mechanism.json")
json.dump(R, open(os.path.join(OUT, "results.json"), "w"), indent=1, default=float)

# ------------------------------------------------------------------ tables
T = {}
NAMES = {"-1": "Novice", "0": "Trained", "1": "Expert", "2": "Master", "3": "Grandmaster"}
t = ["| Rank | Level | Strength (logits, SE) | Elo vs Trained | Step from rank below |", "|---|---|---|---|---|"]
prev = None
for lv in ["-1", "0", "1", "2", "3"]:
    s_ = lad["s"][lv]; se_ = lad["se"][lv]
    step = "" if prev is None else f"{s_ - prev:+.2f}"
    t.append(f"| {NAMES[lv]} | {int(lv):+d} | {s_:+.2f} ({se_:.2f}) | {400 / math.log(10) * s_:+.0f} | {step} |")
    prev = s_
T["ladder"] = "\n".join(t)

band = {1: "65–70%", 2: "78–87%", 3: "87–95%"}
t = ["| Gap | Same style (mirror, 4,800 fights) | Different styles (all 66 pairs, 5,280 fights) | Pass band | Higher rank is the favourite in |", "|---|---|---|---|---|"]
vh = R["validation"]["holdout_0.8"]; fh = R["validation_fav"]["holdout"]
for d in (1, 2, 3):
    m = vh[f"V_mirror|{d}"]; c = vh[f"V_cross|{d}"]
    t.append(f"| +{d} | {pct(m[0])} [{pct(m[1])}–{pct(m[2])}] | {pct(c[0])} [{pct(c[1])}–{pct(c[2])}] | {band[d]} | "
             f"{fh[d]['fav_share']:.0%} of 132 matchups (worst: {fh[d]['worst']}, {pct(fh[d]['worst_p'])}) |")
T["validation"] = "\n".join(t)

t = ["| Model | How rank enters the fight | Calibrated scale θ* (95% CI) → used | +1 / +2 / +3 (pooled, 9,600 fights per gap) | Spread across styles τ at +2 (set A / B) | τ at +3 (A / B) | Least responsive style at +3 (pooled) |",
     "|---|---|---|---|---|---|---|"]
desc = {"V0": "inside the style math: readiness, accuracy, attacker multiplier (all clamped)",
        "V1": "after the style math: odds shift on hit and counter rolls, damage dealt/taken",
        "V2": "after the style math: odds shift on every contested roll, damage dealt/taken"}
for k in ("V0", "V1", "V2"):
    cal = R["calibration"][k]; cf = R["confirm"][k]
    t.append(f"| {k} | {desc[k]} | {cal['theta']:.2f} ({cal['theta_ci'][0]:.2f}–{cal['theta_ci'][1]:.2f}) → {cf['theta']:.2f} | "
             f"{pct(cf['+1']['pooled']['p'])} / {pct(cf['+2']['pooled']['p'])} / {pct(cf['+3']['pooled']['p'])} | "
             f"{cf['+2']['A']['tau']:.2f} / {cf['+2']['B']['tau']:.2f} | {cf['+3']['A']['tau']:.2f} / {cf['+3']['B']['tau']:.2f} | "
             f"{cf['+3']['pooled']['argmin']} {pct(cf['+3']['pooled']['min'])} |")
T["models"] = "\n".join(t)

t = ["| Component (alone, at a +2 gap) | Win chance alone (720 fights) | Share of the rank effect (log-odds) | Share of the variance (Sobol) |", "|---|---|---|---|"]
lab = {"odds": "Contest odds (every contested roll)", "cnt": "Counter odds", "pow": "Damage dealt", "tough": "Damage taken (toughness)", "shrink": "Weakness shrink (seams)"}
for f in ("odds", "pow", "tough", "cnt", "shrink"):
    p, lo, hi = comp["single_P"][f]
    t.append(f"| {lab[f]} | {pct(p)} [{pct(lo)}–{pct(hi)}] | {100 * comp['effect_share'][f]:.0f}% | {100 * comp['first'][f]:.1f}% |")
p, lo, hi = comp["single_P"]["none"]; t.append(f"| none (control) | {pct(p)} [{pct(lo)}–{pct(hi)}] | — | — |")
p, lo, hi = comp["single_P"]["cnt+odds+pow+shrink+tough"]
t.append(f"| all five | {pct(p)} [{pct(lo)}–{pct(hi)}] | 100% | interactions {100 * (1 - sum(comp['first'].values())):.1f}% |")
T["components"] = "\n".join(t)

t = ["| Condition | +1 | change vs cage/60 s/MMA (paired 95% CI) | +2 | change |", "|---|---|---|---|---|"]
base = json.dumps({}, sort_keys=True)
for key in sorted({k.split("|")[0] for k in R["robustness"]}, key=lambda e: (e != base, e)):
    a = R["robustness"][f"{key}|1"]; b = R["robustness"][f"{key}|2"]
    if key == base:
        t.append(f"| Baseline: cage, 60 s, MMA | {pct(a[0])} | — | {pct(b[0])} | — |")
        continue
    nm = ", ".join(f"{k} {v}" for k, v in json.loads(key).items()).replace("dur ", "duration ").replace(".0", " s").replace("arena ", "").replace("ruleset ", "rules: ")
    t.append(f"| {nm} | {pct(a[0])} | {100 * a[1]:+.1f} pts [{100 * a[2]:+.1f}, {100 * a[3]:+.1f}] | {pct(b[0])} | {100 * b[1]:+.1f} pts [{100 * b[2]:+.1f}, {100 * b[3]:+.1f}] |")
T["robustness"] = "\n".join(t)

t = ["| Favourite > underdog | Favourite's win chance (both trained) | Underdog's win chance at +0 / +1 / +2 / +3 | Levels the underdog needs for 50% (SE) | Predicted: logit(P) / β |", "|---|---|---|---|---|"]
for r in sorted(rows, key=lambda r: -r["p_fav_trained"]):
    pdg = r["p_dog"]
    t.append(f"| {r['fav']} > {r['dog']} | {pct(r['p_fav_trained'])} | {pct(pdg[0])} / {pct(pdg[2])} / {pct(pdg[4])} / {pct(pdg[6])} | {r['d50']:.2f} ({r['d50_se']:.2f}) | {r['predicted_d50']:.2f} |")
T["counters"] = "\n".join(t)

spec = R["specialists"]
t = ["| Style | Slots | Specialist keeps | Field win chance: original (all at expert) | Specialist, same rank | Exchange rate: ranks the specialist needs (negative = it is stronger) |", "|---|---|---|---|---|---|"]
for r in sorted(spec["rows"], key=lambda r: r["d_star"]):
    t.append(f"| {r['card']} | {r['slots_orig']} | {' + '.join(r['schools'])} | {pct(r['p_orig'])} | {pct(r['p_spec_at0'])} | {r['d_star']:+.2f}{' (outside the ±1.5 sweep)' if r['extrapolated'] else ''} |")
T["specialists"] = "\n".join(t)

sat = R["saturation"]
t = ["| Style | Exchanges at the 0.85 hit cap | Defender readiness at the 1.45 floor | Damage multiplier at the 1.75 cap | V0 +3 | V2 +3 |", "|---|---|---|---|---|---|"]
P0s = R["confirm"]["V0"]["+3"]["pooled"]["per"]; P2s = R["confirm"]["V2"]["+3"]["pooled"]["per"]
for c in sorted(sat, key=lambda c: P0s[c]):
    t.append(f"| {c} | {pct(sat[c]['hit_at_cap'])} | {pct(sat[c]['ready_at_floor'])} | {pct(sat[c]['mult_at_cap'])} | {pct(P0s[c])} | {pct(P2s[c])} |")
T["saturation"] = "\n".join(t)

t = ["| Underdog vs trained favourite | Underdog at +0 | +1 | +2 | +3 | How the favourite wins at +3 |", "|---|---|---|---|---|---|"]
for fav_, dog in (("wrestler", "maleek"), ("wrestler", "thai"), ("karate", "thai"), ("jiujitsu", "maleek"), ("jiujitsu", "wrestler")):
    cells = [R["E11"][f"{fav_}>{dog}@{d}"] for d in (0, 1, 2, 3)]
    how = ", ".join(f"{k} {v}" for k, v in sorted(cells[3]["fav_wins_by"].items(), key=lambda x: -x[1]))
    t.append(f"| {dog} vs {fav_} | " + " | ".join(f"{pct(c['p'])}" for c in cells) + f" | {how} (of 300) |")
T["rank_resistant"] = "\n".join(t)

t = ["| Wrestler's rank | Wrestler wins | Takedowns landed per fight | Share of exchanges on the ground | Wrestler's rides that fail | Returns to standing per fight (the only stage resets) | Armbars landed per fight (of attempts) | Fights lost by submission |",
     "|---|---|---|---|---|---|---|---|"]
for d in ("0", "1", "2", "3"):
    e = R["E11b"][d]
    t.append(f"| +{d} | {pct(e['wins'])} | {e['takedowns_per_fight']:.2f} | {pct(e['ground_share'])} | {pct(e['ride_failure_share'])} | {e['stage_resets_per_fight']:.2f} | "
             f"{e['armbars_landed_per_fight']:.2f} (of {e['armbar_tries_per_fight']:.2f}) | {pct(e['submission_losses'])} |")
T["mechanism"] = "\n".join(t)

for k, v in T.items():
    open(os.path.join(OUT, "tables", f"{k}.md"), "w").write(v + "\n")

# ------------------------------------------------------------------ figures (light surface, validated slots 1-3)
import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import font_manager  # noqa: E402
from matplotlib.ticker import MaxNLocator  # noqa: E402

for f in glob.glob("/usr/share/fonts/opentype/inter/Inter-*.otf"):
    font_manager.fontManager.addfont(f)
SURF, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e6e5e1"
C1, C2 = "#2a78d6", "#eb6834"
plt.rcParams.update({"font.family": "Inter", "font.size": 10, "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
                     "axes.facecolor": SURF, "figure.facecolor": SURF, "savefig.facecolor": SURF, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8,
                     "axes.spines.top": False, "axes.spines.right": False, "axes.titleweight": "semibold", "axes.titlecolor": INK, "axes.titlesize": 12})

fig, ax = plt.subplots(figsize=(7.2, 4.2), dpi=160)
gaps3 = [1, 2, 3]
bands = {1: (0.65, 0.70), 2: (0.78, 0.87), 3: (0.87, 0.95)}
for gx in gaps3:
    ax.add_patch(plt.Rectangle((gx - 0.28, 100 * bands[gx][0]), 0.56, 100 * (bands[gx][1] - bands[gx][0]), color="#d9d8d3", alpha=0.6, lw=0, zorder=1))
mir = [100 * vh[f"V_mirror|{d}"][0] for d in gaps3]; cro = [100 * vh[f"V_cross|{d}"][0] for d in gaps3]
ax.plot([g - 0.07 for g in gaps3], mir, color=C1, lw=2, marker="o", ms=8, mec=SURF, mew=2, zorder=3, label="Same style (mirror)")
ax.plot([g + 0.07 for g in gaps3], cro, color=C2, lw=2, marker="s", ms=8, mec=SURF, mew=2, zorder=3, label="Different styles (66 pairs)")
for gx, a, b in zip(gaps3, mir, cro):
    ax.annotate(f"{a:.0f}%", (gx - 0.07, a), xytext=(-30, 0), textcoords="offset points", va="center", color=INK, fontsize=9)
    ax.annotate(f"{b:.0f}%", (gx + 0.07, b), xytext=(10, 0), textcoords="offset points", va="center", color=INK, fontsize=9)
ax.set_xticks(gaps3, ["+1 rank", "+2 ranks", "+3 ranks"]); ax.set_xlim(0.5, 3.5); ax.set_ylim(50, 100)
ax.set_ylabel("Higher rank wins (%)")
ax.set_title("Rank gap vs win chance at the recommended settings", loc="left", pad=22)
ax.text(0.0, 1.02, "Grey boxes: pass bands. Holdout: 30,240 fights on seeds never used before.", transform=ax.transAxes, color=INK2, fontsize=9)
ax.legend(loc="lower right", frameon=False, labelcolor=INK)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "figures", "fig1_rank_gap.png")); plt.close(fig)

order = sorted(P2s, key=lambda c: P2s[c])
fig, ax = plt.subplots(figsize=(7.2, 4.8), dpi=160)
ax.axvspan(87, 95, color="#d9d8d3", alpha=0.6, lw=0, zorder=1)
ys = np.arange(len(order))
for yy, c in zip(ys, order):
    ax.plot([100 * P0s[c], 100 * P2s[c]], [yy, yy], color=GRID, lw=2, zorder=2)
ax.scatter([100 * P0s[c] for c in order], ys, s=64, color=C2, edgecolor=SURF, linewidth=2, marker="s", zorder=3, label="V0: rank inside the clamps (θ 2.45)")
ax.scatter([100 * P2s[c] for c in order], ys, s=64, color=C1, edgecolor=SURF, linewidth=2, marker="o", zorder=4, label="V2: rank on every contest (θ 0.80, recommended)")
ax.set_yticks(ys, [c.replace("_", " ") for c in order]); ax.set_xlim(70, 100)
ax.set_xlabel("Grandmaster beats a trained copy of the same fighter (%)")
ax.set_title("Same rank gap, every style: V2 narrows the spread", loc="left", pad=22)
ax.text(0.0, 1.02, "Grey band: pass band 87–95% for a +3 gap. 800 fights per dot (two fresh seed sets).", transform=ax.transAxes, color=INK2, fontsize=9)
ax.legend(loc="upper center", bbox_to_anchor=(0.45, -0.13), ncol=2, frameon=False, labelcolor=INK, fontsize=9)
ax.grid(axis="y", visible=False)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "figures", "fig2_uniformity.png")); plt.close(fig)

fig, ax = plt.subplots(figsize=(7.2, 3.8), dpi=160)
bins = np.arange(0, 2.25, 0.25)
cnt, edges = np.histogram(L, bins=bins)
ax.bar(edges[:-1] + 0.125, cnt, width=0.21, color=C1, zorder=3)
for xx, cc in zip(edges[:-1] + 0.125, cnt):
    if cc:
        ax.text(xx, cc + 0.3, str(cc), ha="center", color=INK, fontsize=9)
med = R["counters"]["dist"]["median"]
ax.vlines(med, 0, cnt[int(med // 0.25)], color=SURF, lw=1.5, zorder=4)
ax.set_ylim(0, max(cnt) + 4)
ax.annotate(f"median {med:.2f} ranks", xy=(med, cnt[int(med // 0.25)]), xytext=(med + 0.35, max(cnt) + 2.2), color=INK2, fontsize=9,
            arrowprops=dict(arrowstyle="-", color=INK2, lw=0.8))
ax.yaxis.set_major_locator(MaxNLocator(integer=True))
ax.set_xlabel(f"Size of the style edge, in ranks (|logit P| / {R['counters']['beta_ladder']:.2f})"); ax.set_ylabel("Matchups")
ax.set_title("How big are style counters? 66 trained matchups", loc="left")
ax.grid(axis="x", visible=False)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "figures", "fig3_counters.png")); plt.close(fig)
print("total fights:", R["volume"]["total"])
