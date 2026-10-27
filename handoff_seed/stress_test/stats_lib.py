"""Statistics and math used by the stress test (numpy/scipy only)."""
from __future__ import annotations

import json
import math
from collections import defaultdict

import numpy as np
from scipy import optimize, special, stats


def load(path):
    with open(path) as fh:
        return [json.loads(line) for line in fh]


def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"),) * 3
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return p, c - h, c + h


def logit(p, eps=1e-3):
    p = min(max(p, eps), 1 - eps)
    return math.log(p / (1 - p))


def sigmoid(x):
    return 1 / (1 + math.exp(-x))


def elo(p):
    p = min(max(p, 1e-6), 1 - 1e-6)
    return 400 * math.log10(p / (1 - p))


def group(rows, key):
    g = defaultdict(list)
    for r in rows:
        g[key(r)].append(r["win_focus"])
    return g


def binom_logit_fit(x, k, n, intercept=False):
    """MLE of logit(p) = b*x (+ a). x, k, n arrays. Returns params and Fisher SEs."""
    x, k, n = map(np.asarray, (x, k, n))
    X = np.column_stack([x, np.ones_like(x)]) if intercept else x[:, None]

    def nll(b):
        eta = X @ b
        return -(k * eta - n * np.logaddexp(0, eta)).sum()

    b0 = np.zeros(X.shape[1])
    res = optimize.minimize(nll, b0, method="BFGS")
    eta = X @ res.x
    p = 1 / (1 + np.exp(-eta))
    W = n * p * (1 - p)
    cov = np.linalg.inv(X.T @ (X * W[:, None]))
    return res.x, np.sqrt(np.diag(cov))


def bradley_terry(pairs):
    """pairs: list of (i, j, wins_i, n). Returns strength vector (logit scale, mean 0) via MLE."""
    items = sorted({p[0] for p in pairs} | {p[1] for p in pairs})
    idx = {it: t for t, it in enumerate(items)}
    m = len(items)

    def nll(s):
        tot = 0.0
        for i, j, w, n in pairs:
            d = s[idx[i]] - s[idx[j]]
            tot -= w * d - n * np.logaddexp(0, d)
        return tot + 1e-6 * (s.sum() ** 2)

    res = optimize.minimize(nll, np.zeros(m), method="BFGS")
    s = res.x - res.x.mean()
    return dict(zip(items, s))


def hodge(pairs):
    """Combinatorial Hodge decomposition of a pairwise-comparison graph (Jiang, Lim, Yao, Ye 2011).
    pairs: (i, j, wins_i, n). Edge flow Y_ij = logit(P_ij) (with +0.5 smoothing), weight n.
    Returns potential (ranking), transitive share and cyclic share of the flow energy, and intransitive triads."""
    items = sorted({p[0] for p in pairs} | {p[1] for p in pairs})
    idx = {it: t for t, it in enumerate(items)}
    m = len(items)
    L = np.zeros((m, m))
    b = np.zeros(m)
    edges = []
    for i, j, w, n in pairs:
        y = math.log((w + 0.5) / (n - w + 0.5))
        a, c = idx[i], idx[j]
        L[a, a] += n
        L[c, c] += n
        L[a, c] -= n
        L[c, a] -= n
        b[a] += n * y
        b[c] -= n * y
        edges.append((a, c, y, n))
    s = np.linalg.lstsq(L, b, rcond=None)[0]
    s -= s.mean()
    tot = sum(n * y * y for a, c, y, n in edges)
    grad = sum(n * (s[a] - s[c]) ** 2 for a, c, y, n in edges)
    resid = sum(n * (y - (s[a] - s[c])) ** 2 for a, c, y, n in edges)
    # intransitive triads in the majority tournament
    beats = defaultdict(set)
    for a, c, y, n in edges:
        if y > 0:
            beats[a].add(c)
        elif y < 0:
            beats[c].add(a)
    cyc = 0
    tri = 0
    for a in range(m):
        for c in range(a + 1, m):
            for d in range(c + 1, m):
                tri += 1
                ab, bc, ca = c in beats[a], d in beats[c], a in beats[d]
                ba, cb, ac = a in beats[c], c in beats[d], d in beats[a]
                if (ab and bc and ca) or (ba and cb and ac):
                    cyc += 1
    return {"potential": dict(zip(items, s)), "transitive_share": grad / tot, "cyclic_share": resid / tot,
            "intransitive_triads": cyc, "triads": tri}


def nash_symmetric(P, names):
    """Equilibrium of the symmetric zero-sum game with payoff A = P - 0.5 (row player). LP: max v s.t. A^T x >= v."""
    A = np.asarray(P) - 0.5
    m = A.shape[0]
    # variables x (m) and v; maximize v -> minimize -v
    c = np.zeros(m + 1)
    c[-1] = -1
    A_ub = np.hstack([-A.T, np.ones((m, 1))])
    b_ub = np.zeros(m)
    A_eq = np.hstack([np.ones((1, m)), np.zeros((1, 1))])
    res = optimize.linprog(c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=[1], bounds=[(0, None)] * m + [(None, None)], method="highs")
    x = res.x[:m]
    return {"value": res.x[-1], "mix": {names[t]: float(x[t]) for t in range(m) if x[t] > 1e-4}}


def problem_of_points(q, n_a, n_b):
    """P(A collects n_a successes before B collects n_b), each success A's with prob q (Pascal-Fermat).
    Equals the regularized incomplete beta I_q(n_a, n_b)."""
    return float(special.betainc(n_a, n_b, q))


def sobol_from_factorial(cfg_values):
    """Full 2^k factorial (factors coded -1/+1). cfg_values: dict frozenset(on factors) -> response.
    Returns first-order and total Sobol indices of the response variance over the design."""
    factors = sorted({f for k in cfg_values for f in k} | set())
    allf = sorted(set().union(*cfg_values.keys())) if cfg_values else []
    factors = allf
    import itertools
    rows = []
    for on, y in cfg_values.items():
        x = {f: (1 if f in on else -1) for f in factors}
        rows.append((x, y))
    N = len(rows)
    effects = {}
    for r in range(1, len(factors) + 1):
        for S in itertools.combinations(factors, r):
            effects[S] = sum(y * np.prod([x[f] for f in S]) for x, y in rows) / N
    var = sum(v * v for v in effects.values())
    first = {f: effects[(f,)] ** 2 / var for f in factors}
    total = {f: sum(v * v for S, v in effects.items() if f in S) / var for f in factors}
    return {"main_effects": {f: effects[(f,)] for f in factors}, "first_order": first, "total": total,
            "interactions": {"x".join(S): v for S, v in effects.items() if len(S) > 1 and abs(v) > 1e-9}}


def dersimonian_laird(y, v):
    """Random-effects meta-analysis. y: per-study effects (log-odds), v: their sampling variances.
    Returns pooled mean, its SE, tau^2 (between-study variance), I^2 and Cochran's Q."""
    y, v = np.asarray(y, float), np.asarray(v, float)
    w = 1 / v
    mu_f = (w * y).sum() / w.sum()
    Q = (w * (y - mu_f) ** 2).sum()
    df = len(y) - 1
    C = w.sum() - (w ** 2).sum() / w.sum()
    tau2 = max(0.0, (Q - df) / C)
    ws = 1 / (v + tau2)
    mu = (ws * y).sum() / ws.sum()
    return {"mu": mu, "se": math.sqrt(1 / ws.sum()), "tau2": tau2, "tau": math.sqrt(tau2), "I2": max(0.0, (Q - df) / Q) if Q > 0 else 0.0, "Q": Q, "df": df}


def cell_logodds(k, n):
    """Empirical log-odds with Haldane-Anscombe correction and its variance."""
    a, b = k + 0.5, n - k + 0.5
    return math.log(a / b), 1 / a + 1 / b


def hodge_noise_corrected(pairs, boot=300, seed=3):
    """Hodge shares corrected for binomial sampling noise.
    Noise energy N = sum 1/(p(1-p)) is split between the gradient space (dim m-1) and the cyclic space (dim E-m+1)
    in proportion to their dimensions (exact for a complete graph with equal trials per edge).
    Also returns a parametric-bootstrap null: the cyclic share produced by noise alone under the fitted transitive model."""
    h = hodge(pairs)
    items = sorted({p[0] for p in pairs} | {p[1] for p in pairs})
    m, E = len(items), len(pairs)
    tot = grad = cyc = N = 0.0
    s = h["potential"]
    for i, j, w, n in pairs:
        y = math.log((w + 0.5) / (n - w + 0.5))
        g = s[i] - s[j]
        tot += n * y * y; grad += n * g * g; cyc += n * (y - g) ** 2
        p = (w + 0.5) / (n + 1)
        N += 1 / (p * (1 - p))
    grad_c = max(0.0, grad - (m - 1) / E * N)
    cyc_c = max(0.0, cyc - (E - m + 1) / E * N)
    rs = np.random.default_rng(seed)
    null = []
    for _ in range(boot):
        sim = []
        for i, j, w, n in pairs:
            p = 1 / (1 + math.exp(-(s[i] - s[j])))
            sim.append((i, j, int(rs.binomial(n, p)), n))
        null.append(hodge(sim)["cyclic_share"])
    return {**h, "noise_energy_share": N / tot, "transitive_share_corrected": grad_c / (grad_c + cyc_c) if grad_c + cyc_c > 0 else float("nan"),
            "cyclic_share_corrected": cyc_c / (grad_c + cyc_c) if grad_c + cyc_c > 0 else float("nan"),
            "null_cyclic_share_mean": float(np.mean(null)), "null_cyclic_share_95": float(np.percentile(null, 95)),
            "p_value_intransitivity": float(np.mean([x >= h["cyclic_share"] for x in null]))}
