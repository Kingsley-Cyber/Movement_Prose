"""Unit tests of the per-slot mastery resolver: equal per-slot levels must reproduce uniform mastery byte-for-byte."""
import sys, json, hashlib
sys.path.insert(0, '.')
import harness as H
H.init()
M = {"theta": 0.77, "model": "v2"}
def h(side_a, side_b, seeds):
    x = hashlib.sha256()
    for s in seeds:
        r = H.run_fight({"seed": s, "a": side_a, "b": side_b, "keep_log": True}); x.update((r["winner"] + r["log"]).encode())
    return x.hexdigest()[:16]
ok = True
for card, opp in (("donnell", "thai"), ("karate", "wrestler"), ("sanda_judo", "greco"), ("maleek", "jiujitsu")):
    n = len(H._STATE["cards"][card]["synchronized_capabilities"])
    u = h({"card": card, "m": 1.5, **M}, {"card": opp, "m": 0.5, **M}, range(1, 11))
    p = h({"card": card, "slot_m": [1.5] * n, **M}, {"card": opp, "m": 0.5, **M}, range(1, 11))
    d = h({"card": card, "slot_m": [3] + [0] * (n - 1), **M}, {"card": opp, "m": 0.5, **M}, range(1, 11))
    print(card, n, "uniform", u, "per-slot equal", p, "per-slot unequal", d, "OK" if (u == p and d != u) else "FAIL")
    ok &= (u == p and d != u)
print("resolver tests pass:", ok)
