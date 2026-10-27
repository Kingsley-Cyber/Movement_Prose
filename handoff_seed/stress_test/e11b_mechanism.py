"""E11b: why does rank stop helping the wrestler against the jiu-jitsu player? Logged fights (V2, theta 0.80):
wrestler at +0..+3 vs a trained jiu-jitsu player, 300 seeds each. Per fight we count the wrestler's landed takedowns,
the share of exchanges fought on the ground, the jiu-jitsu player's armbar attempts and landings, and the finish."""
import json
import os
import sys
from collections import defaultdict
from multiprocessing import Pool

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harness as H  # noqa: E402
from stats_lib import wilson  # noqa: E402

M = {"theta": 0.80, "model": "v2"}
TAKEDOWNS = {"double_leg", "single_leg", "outside_trip", "sanda_sweep"}
LANDED = {"clean", "flush", "counter_hit", "partial"}


def one(job):
    d, s = job
    r = H.run_fight({"seed": s, "a": {"card": "wrestler", "m": d, **M}, "b": {"card": "jiujitsu", **M}, "keep_log": True})
    ex = json.loads(r["log"])
    td = sum(1 for e in ex if e["attacker_id"] == "wrestler" and e["technique_id"] in TAKEDOWNS and e["outcome"] in LANDED)
    td_try = sum(1 for e in ex if e["attacker_id"] == "wrestler" and e["technique_id"] in TAKEDOWNS)
    pull = sum(1 for e in ex if e["attacker_id"] == "jiujitsu" and e["technique_id"] == "guard_pull" and e["outcome"] in LANDED)
    ground = sum(1 for e in ex if e["range"] == "ground")
    arm_try = sum(1 for e in ex if e["attacker_id"] == "jiujitsu" and e["technique_id"] == "armbar")
    arm_land = sum(1 for e in ex if e["attacker_id"] == "jiujitsu" and e["technique_id"] == "armbar" and e["outcome"] in LANDED)
    # submission stages reset only when the pair returns to standing: a failed ride on the ground or a landed escape/retreat on the ground
    ride_fail = sum(1 for e in ex if e["range"] == "ground" and e["technique_id"] == "ride" and e["outcome"] not in LANDED)
    rides = sum(1 for e in ex if e["range"] == "ground" and e["technique_id"] == "ride")
    esc = sum(1 for e in ex if e["range"] == "ground" and e["technique_id"] in ("escape", "retreat") and e["outcome"] in LANDED)
    resets = ride_fail + esc
    return d, int(r["winner"] == "wrestler"), r["method"].split(" (")[0], td, td_try, pull, ground, len(ex), arm_try, arm_land, resets, rides, ride_fail


if __name__ == "__main__":
    jobs = [(d, s) for d in (0, 1, 2, 3) for s in range(1, 301)]
    with Pool(2, initializer=H.init) as p:
        res = p.map(one, jobs, chunksize=50)
    agg = defaultdict(lambda: defaultdict(float))
    for d, w, meth, td, td_try, pull, ground, nex, arm_try, arm_land, resets, rides, ride_fail in res:
        a = agg[d]
        a["n"] += 1; a["w"] += w; a["td"] += td; a["td_try"] += td_try; a["pull"] += pull; a["ground"] += ground; a["nex"] += nex
        a["arm_try"] += arm_try; a["arm_land"] += arm_land; a["sub_losses"] += (meth == "Submission" and not w)
        a["resets"] += resets; a["rides"] += rides; a["ride_fail"] += ride_fail
    out = {}
    print("wrestler rank | wins | takedowns landed/fight (success) | guard pulls/fight | ground share | armbar tries/fight (landed) | losses by submission")
    for d in (0, 1, 2, 3):
        a = agg[d]; n = a["n"]
        p, lo, hi = wilson(a["w"], n)
        row = {"wins": p, "ci": (lo, hi), "takedowns_per_fight": a["td"] / n, "takedown_success": a["td"] / max(1, a["td_try"]),
               "guard_pulls_per_fight": a["pull"] / n, "ground_share": a["ground"] / a["nex"], "armbar_tries_per_fight": a["arm_try"] / n,
               "armbar_landed_share": a["arm_land"] / max(1, a["arm_try"]), "armbars_landed_per_fight": a["arm_land"] / n,
               "stage_resets_per_fight": a["resets"] / n, "rides_per_fight": a["rides"] / n, "ride_failure_share": a["ride_fail"] / max(1, a["rides"]),
               "submission_losses": a["sub_losses"] / n}
        out[d] = row
        print(f"+{d}: {p:.3f} | {row['takedowns_per_fight']:.2f} ({row['takedown_success']:.2f}) | {row['guard_pulls_per_fight']:.2f} | {row['ground_share']:.2f} | "
              f"{row['armbar_tries_per_fight']:.2f} ({row['armbar_landed_share']:.2f}; landed {row['armbars_landed_per_fight']:.2f}) | resets {row['stage_resets_per_fight']:.2f} "
              f"(rides {row['rides_per_fight']:.2f}, failed {row['ride_failure_share']:.2f}) | {row['submission_losses']:.3f}")
    json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "E11b_mechanism.json"), "w"), indent=1)
