"""Theory check: does a damage-race ("problem of points") model predict the simulated level effects?

For each archetype mirror at gap +d (V2, theta*), from the exchange logs we measure
  q   = share of landed damaging blows thrown by the higher-level fighter (per-blow edge)
  n_f = finish threshold / mean landed damage of the higher-level fighter  (blows it needs)
  n_o = same for the lower-level fighter
and predict P(higher wins) = I_q(n_f, n_o) (regularized incomplete beta = Pascal-Fermat problem of points,
continuous in n). We compare predictions with the simulated win rates (R^2, calibration slope).
Second, the sqrt(n) law: at small edges, d logit P / d logit q = I'_q(n, n) at q = 1/2, which grows like sqrt(n).
"""
import json
import math
import os
import sys
from multiprocessing import Pool

import numpy as np
from scipy import special, stats

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harness as H  # noqa: E402

THETA = float(sys.argv[1]) if len(sys.argv) > 2 else 0.80
MODEL = sys.argv[2] if len(sys.argv) > 2 else "v2"
T = 12.0
LANDED = ("clean", "flush", "counter_hit", "partial")


def one(args):
    card, d, s = args
    focus_a = s % 2 == 0
    f = {"card": card, "m": d, "theta": THETA, "model": MODEL}
    o = {"card": card, "m": 0, "theta": THETA, "model": MODEL}
    sp = {"seed": s, "a": f if focus_a else o, "b": o if focus_a else f, "keep_log": True}
    r = H.run_fight(sp)
    fid = card if focus_a else card + "_b"           # side a keeps the plain id, side b is renamed
    ex = json.loads(r["log"])
    blows = []                                        # (by_focal, damage)
    for e in ex:
        dmg = e.get("damage")
        if dmg and dmg["final_damage"] > 0 and dmg["landing_quality"] in LANDED and dmg["damage_type"] != "stamina_drain":
            blows.append((e["attacker_id"] == fid, dmg["final_damage"], dmg["target_region"]))
        cf = e.get("counter_followup")
        if cf and cf.get("damage") and cf["damage"]["final_damage"] > 0:
            blows.append((cf["counter_actor_id"] == fid, cf["damage"]["final_damage"], cf["damage"]["target_region"]))
    win = int((r["winner"] == fid))
    return card, d, win, blows, len(ex)


LIMITS = {"head": 11.5, "body": 12.0, "leg": 12.5}


def compound_race(q, df, rf, do, ro, races=20000, seed=5):
    """Monte-Carlo race with each side's empirical (damage, region) blow distribution and the engine's regional
    finish thresholds: each blow is the focal fighter's with probability q; first to push any region past its limit wins."""
    rs = np.random.default_rng(seed)
    if not df or not do:
        return float("nan")
    df, do = np.array(df), np.array(do)
    ri = {"head": 0, "body": 1, "leg": 2}
    rf = np.array([ri.get(x, 1) for x in rf]); ro = np.array([ri.get(x, 1) for x in ro])
    lim = np.array([LIMITS["head"], LIMITS["body"], LIMITS["leg"]])
    wins = 0
    for _ in range(races):
        acc = [np.zeros(3), np.zeros(3)]          # damage taken by opponent (index 0) and by focal (index 1)
        while True:
            if rs.random() < q:
                k = rs.integers(len(df)); acc[0][rf[k]] += df[k]
                if acc[0][rf[k]] >= lim[rf[k]]:
                    wins += 1; break
            else:
                k = rs.integers(len(do)); acc[1][ro[k]] += do[k]
                if acc[1][ro[k]] >= lim[ro[k]]:
                    break
    return wins / races


if __name__ == "__main__":
    jobs = [(c, d, s) for c in H.ARCHETYPES for d in (1, 2, 3) for s in range(1, 201)]
    with Pool(2, initializer=H.init) as p:
        res = p.map(one, jobs, chunksize=50)
    agg = {}
    for card, d, win, blows, nex in res:
        a = agg.setdefault((card, d), {"w": 0, "n": 0, "bf": 0, "bo": 0, "df": [], "do": [], "rf": [], "ro": [], "nex": []})
        a["w"] += win; a["n"] += 1; a["nex"].append(nex)
        for by_f, dm, reg in blows:
            if by_f:
                a["bf"] += 1; a["df"].append(dm); a["rf"].append(reg)
            else:
                a["bo"] += 1; a["do"].append(dm); a["ro"].append(reg)
    rows = []
    for (card, d), a in sorted(agg.items()):
        q = a["bf"] / max(1, a["bf"] + a["bo"])
        nf = T / np.mean(a["df"]) if a["df"] else 99
        no = T / np.mean(a["do"]) if a["do"] else 99
        pred = float(special.betainc(nf, no, q))
        sim = a["w"] / a["n"]
        pred2 = compound_race(q, a["df"], a["rf"], a["do"], a["ro"])
        rows.append({"card": card, "d": d, "q": q, "n_f": nf, "n_o": no, "pred": pred, "pred_compound": pred2, "sim": sim, "nex": float(np.mean(a["nex"]))})
    sim = np.array([r["sim"] for r in rows]); pred = np.array([r["pred"] for r in rows])
    ls, lp = np.log((sim + 1e-3) / (1 - sim + 1e-3)), np.log((pred + 1e-3) / (1 - pred + 1e-3))
    slope, icpt, rr, pv, se = stats.linregress(lp, ls)
    print(f"problem-of-points model: R^2 (logit scale) = {rr**2:.3f}, calibration slope {slope:.2f} (se {se:.2f}), intercept {icpt:.2f}; "
          f"mean |P_sim - P_pred| = {np.mean(np.abs(sim - pred)):.3f}")
    pc = np.array([r["pred_compound"] for r in rows]); lc = np.log((pc + 1e-3) / (1 - pc + 1e-3))
    slope2, icpt2, rr2_, pv_, se2_ = stats.linregress(lc, ls)
    print(f"compound race (empirical blow sizes + regional limits): R^2 = {rr2_**2:.3f}, calibration slope {slope2:.2f} (se {se2_:.2f}), "
          f"intercept {icpt2:.2f}; mean |P_sim - P_pred| = {np.mean(np.abs(sim - pc)):.3f}")
    for r in rows:
        print(f"  {r['card']:11s} +{r['d']}: q={r['q']:.3f} n_f={r['n_f']:.2f} n_o={r['n_o']:.2f}  pointsmodel {r['pred']:.3f}  compound {r['pred_compound']:.3f}  sim {r['sim']:.3f}  exchanges {r['nex']:.1f}")
    # sqrt(n) law: per-archetype +1 effect vs race length, controlling for the per-blow edge
    d1 = [r for r in rows if r["d"] == 1]
    sens = [math.log(r["sim"] / (1 - r["sim"])) / max(1e-6, math.log(r["q"] / (1 - r["q"]))) for r in d1]
    n_mean = [0.5 * (r["n_f"] + r["n_o"]) for r in d1]
    sl, ic, rr2, pv2, se2 = stats.linregress(np.sqrt(n_mean), sens)
    print(f"sqrt(n) law: match-level sensitivity (d logit P / d logit q) vs sqrt(blows needed): slope {sl:.2f} (se {se2:.2f}), R^2 {rr2**2:.2f}, p={pv2:.3g}")
    theo = [(nn, float((0.25 ** (nn - 1)) / special.beta(nn, nn))) for nn in (1.5, 2, 3, 4, 5, 6, 8)]
    print("  theory I'_{1/2}(n,n):", ", ".join(f"n={nn}: {v:.2f}" for nn, v in theo))
    json.dump(rows, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "theory_rows.json"), "w"), indent=1)
