"""Saturation audit: how often each archetype's fights sit on an engine clamp (where mastery cannot act)."""
import json, sys, statistics as S
sys.path.insert(0, '.')
import harness as H
H.init()
out = {}
for card in H.ARCHETYPES:
    hp_hi = hp_lo = n = 0; ma_hi = ma_n = 0; rd_lo = rd_hi = 0; nex = []; dmg_landed = []; hits_to_finish = []
    finishes = 0
    for s in range(1, 101):
        r = H.run_fight({'seed': s, 'a': {'card': card}, 'b': {'card': card}, 'keep_log': True})
        ex = json.loads(r['log']); nex.append(len(ex))
        for e in ex:
            n += 1
            hp = e['hit_probability']; hp_hi += hp >= 0.85; hp_lo += hp <= 0.10
            lr = e['lane_readiness_score']; rd_lo += lr <= 1.45; rd_hi += lr >= 4.85
            for d in [e.get('damage')] + [((e.get('counter_followup') or {}).get('damage'))]:
                if d and d['final_damage'] > 0:
                    ma_n += 1; ma_hi += d['attacker_multiplier'] >= 1.75
                    if d['landing_quality'] in ('clean', 'flush', 'counter_hit', 'partial'):
                        dmg_landed.append(d['final_damage'])
    md = S.mean(dmg_landed) if dmg_landed else 0
    out[card] = dict(n_ex=S.mean(nex), hit_at_cap=hp_hi / n, hit_at_floor=hp_lo / n, ready_at_floor=rd_lo / n, ready_at_ceiling=rd_hi / n,
                     mult_at_cap=ma_hi / max(1, ma_n), mean_landed_dmg=md, hits_to_finish=12.0 / md if md else None)
    print(card.ljust(11), " ".join(f"{k}={v:.3f}" if isinstance(v, float) else f"{k}={v}" for k, v in out[card].items()), flush=True)
json.dump(out, open('data/diag_saturation.json', 'w'), indent=1)
