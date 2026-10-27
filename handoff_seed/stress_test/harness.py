"""Rank & mastery stress-test harness around the real BLOCK v2 engine (repo @ 0d0734d, read-only).

Rank ("mastery level" L: novice -1, trained 0, expert 1, master 2, grandmaster 3) is injected per fighter without
touching repo code or data. Three models (field "model" of a fighter spec):
  V0 (inside the style math, all engine clamps kept)
    * accuracy  -> the defender's readiness on the attacked lane is lowered (logit_hit = skill - readiness)
    * defense   -> the fighter's own readiness is raised
    * power     -> added to the additive attacker multiplier (engine clamp [0.75, 1.75] kept unless clamp_off)
  V1 (after the style math): odds shift on the hit roll and the counter roll + damage x exp(pow*L_att - tough*L_def)
  V2 (after the style math, every contest): V1 + the same odds shift on kick catch, sweep after a catch, range
     step-in/out, clinch break and feint (the recommended model; handoff 7.18)
  All models: weakness shrink closes a fraction of the fighter's own seams (negative lane bonuses x 0.62).
V1/V2 load an instrumented copy of engine/simulator_v2.py with hook calls on those lines (no extra random draws).
Per-slot mastery ("slot_m") resolves the level of the slot each fighter is in, exchange by exchange.
With every level at 0 the engine's own logs are reproduced byte for byte (control.py, test_slot.py).
Set BLOCK_REPO to a checkout of Movement_Prose at 0d0734d.
"""
from __future__ import annotations

import copy
import json
import math
import os
import sys

REPO = os.environ.get("BLOCK_REPO", "/home/claude/kingsley-cyber/mp_v2")   # a checkout of Movement_Prose at 0d0734d
sys.path.insert(0, REPO)

LANES = ["head_straight", "head_hook", "head_uppercut", "body", "leg", "entry", "clinch", "single_support"]
READ_MIN, READ_MAX, COMP = 1.45, 4.85, 0.62
SHRINK = {-1: -0.25, 0: 0.0, 1: 0.10, 2: 0.25, 3: 0.40}
BASE_STEP = {"acc": 0.12, "def": 0.10, "pow": 0.05}
ARCHETYPES = ["detroit", "donnell", "greco", "jiujitsu", "karate", "macklin", "maleek", "philly", "sanda_judo", "street", "thai", "wrestler"]

_STATE = {}
MASTERY = {}   # fighter_id -> mastery dict for the current fight (cards themselves are never modified)
BASEOF = {}    # fighter_id -> archetype id (for seam lookup)

# Model V1 ("odds-space mastery"): mastery is applied AFTER the engine's style math and outside its clamps.
#   hit chance      p' = clip(sigmoid(logit(p_engine) + odds_att - odds_def), 0.05, 0.95)
#   counter chance  c' = clip(sigmoid(logit(c_engine) + cnt_counterer - cnt_victim), 0.05, 0.75)
#   damage          d' = d_engine * exp(pow_att - tough_def)
V1_STEP = {"odds": 0.25, "cnt": 0.25, "pow": 0.05, "tough": 0.05}
HIT_BAND, CNT_BAND = (0.05, 0.95), (0.05, 0.75)
_HIT_LINE = "hit_prob = round(max(0.10, min(0.85, 1.0 / (1.0 + math.exp(-logit_hit)))), 3)"
_CNT_LINE = "if rng.random() < counter_prob:"
# Model V2 ("every contest"): V1 plus the same odds shift on every other contested roll between the two fighters.
_CONTEST_LINES = {
    "if rng.random() < catch_prob:": "if rng.random() < _MX(defender_card, attacker_card or {}, catch_prob, 0.05, 0.85):",
    'elif str(active_plan["home_range"]) in ("kick", "punch") and rng.random() < 0.42:':
        'elif str(active_plan["home_range"]) in ("kick", "punch") and rng.random() < _MX(att_card, def_card, 0.42, 0.05, 0.95):',
    "if rng.random() < step_prob:": "if rng.random() < _MX(att_card, def_card, step_prob, 0.05, 0.95):",
    "if rng.random() < pull_prob:": "if rng.random() < _MX(att_card, def_card, pull_prob, 0.05, 0.95):",
    "feinted_this_exchange = (feint_prob > 0.0 and rng.random() < feint_prob)":
        "feinted_this_exchange = (feint_prob > 0.0 and rng.random() < _MX(att_card, def_card, feint_prob, 0.01, 0.80))",
    "if rng.random() < sweep_prob:": "if rng.random() < _MX(def_card, att_card, sweep_prob, 0.05, 0.90):",
}


def _shrink_at(level: float) -> float:
    lo = int(max(-1, min(3, (level // 1))))
    hi = min(3, lo + 1)
    frac = level - lo
    return SHRINK[lo] + (SHRINK[hi] - SHRINK[lo]) * frac if hi != lo else SHRINK[lo]


def mastery(level: float, theta: float = 1.0, comps=None, step=None, model: str = "v0"):
    """Mastery effects for a level relative to 'trained' (0). Non-integer levels interpolate the shrink table."""
    if model in ("v1", "v2"):
        comps = ("odds", "cnt", "pow", "tough", "shrink") if comps is None else comps
        st = dict(V1_STEP if step is None else step)
        out = {k: (st[k] * theta * level if k in comps else 0.0) for k in ("odds", "cnt", "pow", "tough")}
        out.update({"model": model, "acc": 0.0, "def": 0.0, "shrink": _shrink_at(level) if "shrink" in comps else 0.0})
        return out
    comps = ("acc", "def", "pow", "shrink") if comps is None else comps
    st = dict(BASE_STEP if step is None else step)
    return {"model": "v0",
            "acc": st["acc"] * theta * level if "acc" in comps else 0.0,
            "def": st["def"] * theta * level if "def" in comps else 0.0,
            "pow": st["pow"] * theta * level if "pow" in comps else 0.0,
            "shrink": _shrink_at(level) if "shrink" in comps else 0.0}


CURRENT_SLOT = {}   # fighter_id -> slot currently in use (set by the _SLOT hook at the start of every exchange)
_SLOT_LINE = 'att_state["active_slot_id"] = active_plan["slot_id"]'


def _SLOT(att_card: dict, att_state: dict, def_card: dict, def_state: dict, slot_id: str) -> str:
    """Records which slot each fighter is in for this exchange (attacker: the slot it attacks from; defender: its last slot)."""
    CURRENT_SLOT[att_card["fighter_id"]] = slot_id
    CURRENT_SLOT[def_card["fighter_id"]] = def_state.get("active_slot_id")
    return slot_id


def _m(fid):
    """Effective mastery of a fighter right now: per-slot mastery if the card has it, else the fighter-level mastery."""
    m = MASTERY.get(fid)
    if m and "per_slot" in m:
        return m["per_slot"].get(CURRENT_SLOT.get(fid), m)
    return m


def _odds_shift(p: float, s: float, band) -> float:
    if not s:
        return p
    x = math.log(p / (1.0 - p)) + s
    return round(min(band[1], max(band[0], 1.0 / (1.0 + math.exp(-x)))), 3)


def _MH(att: dict, dfn: dict, p: float) -> float:
    ma, md = _m(att["fighter_id"]), _m(dfn["fighter_id"])
    s = (ma.get("odds", 0.0) if ma else 0.0) - (md.get("odds", 0.0) if md else 0.0)
    return _odds_shift(p, s, HIT_BAND)


def _MC(counterer: dict, victim: dict, c: float) -> float:
    mc, mv = _m(counterer["fighter_id"]), _m(victim["fighter_id"])
    s = (mc.get("cnt", 0.0) if mc else 0.0) - (mv.get("cnt", 0.0) if mv else 0.0)
    return _odds_shift(c, s, CNT_BAND)


def _MX(actor: dict, opponent: dict, p: float, lo: float, hi: float) -> float:
    """V2 only: odds shift on a generic contested roll won by `actor`."""
    ma, mo = _m(actor.get("fighter_id")), _m(opponent.get("fighter_id"))
    sa = ma.get("odds", 0.0) if ma and ma.get("model") == "v2" else 0.0
    so = mo.get("odds", 0.0) if mo and mo.get("model") == "v2" else 0.0
    if not (sa - so) or p <= 0.0 or p >= 1.0:
        return p
    return _odds_shift(p, sa - so, (lo, hi))


def _load_instrumented_engine():
    """Load engine.simulator_v2 from its own source with two hook calls inserted (hit chance, counter chance).
    The hooks are the identity unless a fighter carries V1 mastery; the RNG call sequence is unchanged."""
    import types
    import engine  # noqa: F401  (package must exist for the module's relative imports)
    path = os.path.join(REPO, "engine", "simulator_v2.py")
    src = open(path).read()
    assert src.count(_HIT_LINE) == 1 and src.count(_CNT_LINE) == 1, "engine source changed: re-check hook lines"
    src = src.replace(_HIT_LINE, "hit_prob = _MH(att_card, def_card, " + _HIT_LINE.split(" = ", 1)[1] + ")")
    src = src.replace(_CNT_LINE, "if rng.random() < _MC(def_card, att_card, counter_prob):")
    for old, new in _CONTEST_LINES.items():
        assert src.count(old) == 1, ("engine source changed: re-check contest line", old)
        src = src.replace(old, new)
    assert src.count(_SLOT_LINE) == 1, "engine source changed: re-check slot line"
    src = src.replace(_SLOT_LINE, 'att_state["active_slot_id"] = _SLOT(att_card, att_state, def_card, def_state, active_plan["slot_id"])')
    mod = types.ModuleType("engine.simulator_v2")
    mod.__file__, mod.__package__ = path, "engine"
    mod.__dict__.update(_MH=_MH, _MC=_MC, _MX=_MX, _SLOT=_SLOT)
    sys.modules["engine.simulator_v2"] = mod
    exec(compile(src, path, "exec"), mod.__dict__)
    return mod


def init(patch: bool = True, clamp_off: bool = False, instrument: bool = True):
    """Load the engine once per process and (optionally) install the mastery wrappers + speed patches."""
    import jsonschema
    if patch:
        jsonschema.validate = lambda *a, **k: None          # schema checks have no side effects (control test proves it)
    if patch and instrument:
        SIM = _load_instrumented_engine()
    else:
        import engine.simulator_v2 as SIM
    from engine.ontology import Knowledge, read
    K = Knowledge()
    opts = {o["id"]: o for o in read(os.path.join(REPO, "data/option_behaviors.json"))["options"]}
    cards = {cid: K.card(os.path.join(REPO, "cards/v2", f"{cid}.json")) for cid in ARCHETYPES}
    seams = {}
    for cid, c in cards.items():
        seams[cid] = {ln: -COMP * sum(min(0.0, float(opts[o]["lane_readiness_bonus"][ln])) for o in c["dimensions"].values() if o) for ln in LANES}
    _STATE.update(SIM=SIM, K=K, cards=cards, seams=seams, opts=opts, clamp_off=clamp_off)
    if patch:
        orig_rp = SIM.compute_readiness_profile
        orig_dmg = SIM.compute_card_derived_damage

        def rp(*args, **kw):
            prof = orig_rp(*args, **kw)
            card, opp = args[1], args[3] if len(args) > 3 else kw.get("opponent_card")
            md, mo = _m(card["fighter_id"]), _m((opp or {}).get("fighter_id"))
            if not md and not mo:
                return prof
            out = dict(prof)
            sm = seams.get(BASEOF.get(card["fighter_id"]), {})
            for ln in LANES:
                if ln not in out:
                    continue
                v = float(out[ln])
                if md:
                    v += md["def"] + md["shrink"] * sm.get(ln, 0.0)
                if mo:
                    v -= mo["acc"]
                out[ln] = round(min(READ_MAX, max(READ_MIN, v)), 3)
            return out

        def dmg(*args, **kw):
            r = orig_dmg(*args, **kw)
            att, dfn = args[1], args[2]
            m, md = _m(att["fighter_id"]), _m(dfn["fighter_id"])
            if r["final_damage"] <= 0:
                return r
            V = ("v1", "v2")
            if (m and m.get("model") in V) or (md and md.get("model") in V):
                e = (m.get("pow", 0.0) if m and m.get("model") in V else 0.0) - (md.get("tough", 0.0) if md and md.get("model") in V else 0.0)
                if not e:
                    return r
                r = dict(r)
                r["final_damage"] = round(r["final_damage"] * math.exp(e), 3)
                return r
            if not m or not m["pow"]:
                return r
            ma = float(r["attacker_multiplier"])
            ma2 = ma + m["pow"]
            if not _STATE["clamp_off"]:
                ma2 = max(0.75, min(1.75, ma2))
            r = dict(r)
            r["final_damage"] = round(r["final_damage"] * ma2 / ma, 3)
            r["attacker_multiplier"] = round(ma2, 3)
            return r

        SIM.compute_readiness_profile = rp
        SIM.compute_card_derived_damage = dmg
    return _STATE


def specialist_variant(card: dict, K, mode: str = "slot1") -> dict:
    """Collapse a card to ONE slot.
    slot1: keep the opening slot as it is ("the fighter only has plan A").
    best2: keep the 1-2 schools that back the most of the card's 7 picks ("a specialist built around the core").
    Training, techniques, picks and seams that the kept schools no longer support are dropped (the engine requires it).
    """
    from itertools import combinations
    from engine.capabilities import option_supported, training
    slots = card["synchronized_capabilities"]
    if mode == "slot1":
        caps = list(slots[0]["capabilities"])
        seq_src = list(slots[0].get("sequence", []))
    else:
        schools = []
        for s_ in slots:
            for c_ in s_["capabilities"]:
                if c_ not in schools and c_ != "basic_movement":
                    schools.append(c_)
        best, best_key = None, None
        for r in (1, 2):
            for sub in combinations(schools, r):
                tmp = copy.deepcopy(card)
                tmp["synchronized_capabilities"] = [{"id": "x", "capabilities": list(sub), "description": "x"}]
                tr = training(tmp)
                tmp["active_techniques"] = [t for t in card["active_techniques"] if set(K.techniques[t]["required_capabilities"]) & tr]
                n = sum(1 for o in card["dimensions"].values() if o and option_supported(K, tmp, o))
                key = (n, len(set(sub) & set(slots[0]["capabilities"])), -len(sub), [-schools.index(x) for x in sub])
                if best_key is None or key > best_key:
                    best, best_key = sub, key
        caps = list(best)
        seq_src = [m for s_ in slots for m in s_.get("sequence", [])]
    c = copy.deepcopy(card)
    tmp_slot = copy.deepcopy(slots[0])
    tmp_slot["capabilities"] = caps
    tmp_slot["links"] = [tmp_slot["id"]]
    c["synchronized_capabilities"] = [tmp_slot]
    c["slot_count"], c["slot_label"] = 1, "Brawler"
    tr = training(c)
    c["active_techniques"] = [t for t in c["active_techniques"] if set(K.techniques[t]["required_capabilities"]) & tr]
    granted = [m for m in dict.fromkeys(seq_src) if m in c["active_techniques"] and set(K.techniques[m]["required_capabilities"]) & set(caps)]
    tmp_slot["sequence"] = granted or [m for m in c["active_techniques"] if K.techniques[m]["kind"] not in ("movement", "feint", "defense")][:5] or seq_src[:1]
    for dim, oid in list(c["dimensions"].items()):
        if oid and not option_supported(K, c, oid):
            c["dimensions"][dim] = None
    keep = {d for o in c["dimensions"].values() if o for d in K.options[o]["exploitable_debt_ids"]}
    c["exploitable_seams"] = [d for d in c["exploitable_seams"] if d in keep]
    suffix = "_spec" if mode == "slot1" else "_spec2"
    c["fighter_id"] = card["fighter_id"] + suffix
    c["name"] = card["name"] + (" (plan A only)" if mode == "slot1" else " (core specialist)")
    return K.card(c)


def build_card(side: dict, rename: str | None = None) -> dict:
    st = _STATE
    base = st["cards"][side["card"]]
    if side.get("variant") in ("spec", "spec2"):
        key = (side["variant"], side["card"])
        if key not in st:
            st[key] = specialist_variant(base, st["K"], "slot1" if side["variant"] == "spec" else "best2")
        base = st[key]
    c = dict(base)
    if rename:
        c["fighter_id"] = c["fighter_id"] + rename
    BASEOF[c["fighter_id"]] = side["card"]
    lvl = side.get("m", 0)
    CURRENT_SLOT.pop(c["fighter_id"], None)
    comps = tuple(side["comps"]) if "comps" in side else None
    if "slot_m" in side:
        ids = [sl["id"] for sl in c["synchronized_capabilities"]]
        levels = list(side["slot_m"])
        assert len(levels) == len(ids), (c["fighter_id"], ids, levels)
        m = mastery(sum(levels) / len(levels), side.get("theta", 1.0), comps, side.get("step"), side.get("model", "v0"))
        m["per_slot"] = {sid: mastery(lv, side.get("theta", 1.0), comps, side.get("step"), side.get("model", "v0")) for sid, lv in zip(ids, levels)}
        MASTERY[c["fighter_id"]] = m
    elif lvl or side.get("force_m"):
        MASTERY[c["fighter_id"]] = mastery(lvl, side.get("theta", 1.0), comps, side.get("step"), side.get("model", "v0"))
    else:
        MASTERY.pop(c["fighter_id"], None)
    return c


def run_fight(spec: dict) -> dict:
    st = _STATE
    if not st:
        init(patch=spec.get("patch", True), clamp_off=spec.get("clamp_off", False))
    st["clamp_off"] = spec.get("clamp_off", False)
    a = build_card(spec["a"])
    b = build_card(spec["b"], rename="_b" if (spec["a"]["card"] == spec["b"]["card"] and spec["a"].get("variant") == spec["b"].get("variant")) else None)
    sim = st["SIM"].simulate_fight_v2(a, b, ruleset=spec.get("ruleset", "mma"), duration_s=spec.get("dur", 60.0), seed=spec["seed"],
                                      arena=spec.get("arena", "cage"), knowledge=st["K"])
    win_a = sim["winner_id"] == a["fighter_id"]
    out = {"exp": spec.get("exp"), "cell": spec.get("cell"), "seed": spec["seed"], "win_a": int(win_a),
           "method": sim.get("finish_reason", ""), "n_ex": len(sim["exchanges"]), "dur": sim.get("duration_actual_s", None)}
    if spec.get("keep_log"):
        out["log"] = json.dumps(sim["exchanges"], sort_keys=True)
        out["winner"] = sim["winner_id"]
    return out
