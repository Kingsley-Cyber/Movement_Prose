import sys, json, hashlib, time
sys.path.insert(0, ".")
import harness as H
mode = sys.argv[1]
H.init(patch=(mode != "orig"))
pairs = [("donnell", "thai"), ("sanda_judo", "wrestler"), ("karate", "greco"), ("street", "jiujitsu")]
specs = []
for a, b in pairs:
    for s in range(1, 9):
        sp = {"a": {"card": a}, "b": {"card": b}, "seed": s, "keep_log": True}
        if mode in ("zero", "zero1", "zero2"):
            sp["a"]["force_m"] = True; sp["b"]["force_m"] = True     # mastery dicts present but all zero
            if mode != "zero":
                sp["a"]["model"] = sp["b"]["model"] = {"zero1": "v1", "zero2": "v2"}[mode]
        specs.append(sp)
t = time.time()
h = hashlib.sha256()
res = [H.run_fight(sp) for sp in specs]
for r in res:
    h.update((r["winner"] + r["log"]).encode())
print(mode, h.hexdigest()[:16], f"{len(specs)/(time.time()-t):.1f} fights/s", res[0]["method"][:40], res[0]["dur"])
