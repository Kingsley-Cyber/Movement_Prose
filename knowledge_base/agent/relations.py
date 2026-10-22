"""Module relations: the handbook's temporal-coupling vocabulary over directives and concepts, authored with evidence; `follow` pulls supporting rows."""
import json
from collections import OrderedDict

from . import knowledge as kn

RELATIONS = ("precedes", "lags", "synchronizes_with", "peaks_with", "holds_during", "releases_after", "triggered_by", "requires_setup", "reacts_to")
PULL = {  # when following from a seed, which endpoint the seed is and which relation it pulls through
    "requires_setup": "source",   # seed requires_setup X  -> pull X (the setup)
    "triggered_by": "source",     # seed triggered_by X    -> pull X
    "lags": "target",             # X lags seed            -> pull X (the reaction)
    "synchronizes_with": "both",
    "peaks_with": "both",
    "holds_during": "both",
    "releases_after": "target",   # X releases_after seed  -> pull X
    "reacts_to": "target",        # X reacts_to seed       -> pull X
    "precedes": "both",
}


def add(mem, source, relation, target, evidence, passage_id=None, offset="", confidence=0.6, created_by="agent"):
    if relation not in RELATIONS:
        raise ValueError("relation must be one of %s" % (RELATIONS,))
    if not (evidence or "").strip():
        raise ValueError("a relation needs evidence")
    if not source or not target or source == target:
        raise ValueError("source and target must differ")
    mem.execute("INSERT OR IGNORE INTO module_relations (source, relation, target, offset, evidence, passage_id, confidence, created_at, created_by) VALUES (?,?,?,?,?,?,?,?,?)",
                (source, relation, target, offset, evidence.strip(), passage_id, float(confidence), kn.now(), created_by))
    mem.commit()


def list_relations(mem, node=None, limit=200):
    if node:
        rows = mem.execute("SELECT * FROM module_relations WHERE source = ? OR target = ? ORDER BY id LIMIT ?", (node, node, limit)).fetchall()
    else:
        rows = mem.execute("SELECT * FROM module_relations ORDER BY id LIMIT ?", (limit,)).fetchall()
    return [dict(r) for r in rows]


def follow(mem, seeds, depth=1, directives_only=True):
    """Rows pulled by relations from the seed ids. -> [{'id', 'relation', 'via', 'evidence', 'passage_id', 'offset', 'depth'}]"""
    pulled, seen, frontier = [], set(seeds), list(seeds)
    for d in range(1, depth + 1):
        nxt = []
        for s in frontier:
            for r in mem.execute("SELECT source, relation, target, evidence, passage_id, offset FROM module_relations WHERE source = ? OR target = ?", (s, s)):
                src, rel, tgt = r[0], r[1], r[2]
                side = PULL.get(rel, "both")
                other = None
                if src == s and side in ("source", "both"):
                    other = tgt
                elif tgt == s and side in ("target", "both"):
                    other = src
                if other is None or other in seen:
                    continue
                if directives_only and not other.startswith("aa_"):
                    continue
                seen.add(other)
                nxt.append(other)
                pulled.append(OrderedDict([("id", other), ("relation", rel), ("via", s), ("evidence", r[3]), ("passage_id", r[4]), ("offset", r[5]), ("depth", d)]))
        frontier = nxt
        if not frontier:
            break
    return pulled


def seed(mem):
    """Handbook example edges (generic events) + authored directive-level edges, each with its passage."""
    n0 = mem.execute("SELECT count(*) FROM module_relations").fetchone()[0]
    H = "handbook:a013#0003"
    for s, r, t in (("gaze_shift", "precedes", "head_orientation"), ("head_orientation", "precedes", "torso_reorientation"),
                    ("breath_hold", "holds_during", "anticipation"), ("exhale", "synchronizes_with", "action_release"), ("facs.au4", "peaks_with", "action_apex")):
        add(mem, s, r, t, "Temporal Coupling card coordination example", "src-cpcs-canonical-temporal_coupling#0003", "", 0.7, H)
    A = [  # (source, relation, target, evidence, passage short id, offset)
        ("aa_action_hip_led_punch", "requires_setup", "aa_action_weight_load", "a hit with no wind-up and no recovery reads weightless", "a035#0021", "setup precedes the strike"),
        ("aa_action_flash_step", "requires_setup", "aa_time_hold_then_burst", "a vanish needs a held key before the burst (anticipation expansion)", "a035#0023", "hold precedes the burst"),
        ("aa_action_followthrough_arc", "triggered_by", "aa_action_hip_led_punch", "overshoot / follow-through continues the stroke past the apex", "a019#0031", "immediately after the stroke"),
        ("aa_action_guard_recovery", "releases_after", "aa_action_followthrough_arc", "the return from one action becomes the wind-up or guard for the next", "a036#0263", "after the follow-through settles"),
        ("aa_action_absorb_recoil", "lags", "aa_action_forearm_block", "a reaction cannot precede its cause; no flinch or knockback before contact", "a035#0009", "a few frames after contact"),
        ("aa_action_absorb_recoil", "lags", "aa_action_hip_led_punch", "the struck fighter's catch step follows the landed strike", "a035#0009", "a few frames after contact"),
        ("aa_time_contact_hitstop", "peaks_with", "aa_action_forearm_block", "hit-stop is the contact-beat freeze; the single most important it-landed cue", "a035#0027", "on the contact frame"),
        ("aa_time_contact_hitstop", "peaks_with", "aa_action_hip_led_punch", "hit-stop on a landed strike", "a035#0027", "on the contact frame"),
        ("aa_camera_contact_lock", "holds_during", "aa_time_contact_hitstop", "lock the camera through the contact hold", "a036#0315", "for the length of the hold"),
        ("aa_secondary_contact_ring", "synchronizes_with", "aa_action_hip_led_punch", "shock ring is an effect of contact, never before it", "a035#0028", "from the contact frame onward"),
        ("aa_secondary_angular_impact_star", "synchronizes_with", "aa_action_forearm_block", "contact star is an effect of contact, never before it", "a035#0028", "from the contact frame onward"),
        ("aa_material_monochrome_impact", "synchronizes_with", "aa_action_hip_led_punch", "impact-frame flash coincides with the contact drawing", "a035#0035", "on the contact frame"),
        ("aa_secondary_cloth_lag", "lags", "aa_action_weight_load", "tight clothing and short hair lag the body by a few frames", "a016#0109", "a few frames behind the torso"),
        ("aa_secondary_cloth_settle", "lags", "aa_action_guard_recovery", "fabric settles after the body stops", "a016#0109", "after the body stops"),
        ("aa_env_skid_gouge", "releases_after", "aa_action_absorb_recoil", "the gouge needs the heel ground-contact interval of the catch step", "directive:aa_env_skid_gouge.requires", "during the recovery step"),
        ("aa_env_preimpact_quiet", "precedes", "aa_env_radial_fracture", "the floor must be in its established state before the fracture", "a035#0028", "before contact"),
        ("aa_subject_recoil_identity", "synchronizes_with", "aa_action_absorb_recoil", "identity holds through the recoil", "directive:aa_subject_recoil_identity", "through the recoil"),
        ("aa_time_hold_then_burst", "holds_during", "aa_action_weight_load", "the preparation pose registers as a held still before release", "a035#0023", "through the wind-up"),
        ("aa_subject_loaded_silhouette", "synchronizes_with", "aa_action_weight_load", "the loaded silhouette is the readable form of the wind-up", "a036#0321", "through the wind-up"),
        ("aa_camera_low_tilt", "precedes", "aa_action_hip_led_punch", "the setup framing sits before the strike", "a031#1899", "before the strike"),
    ]
    for s, r, t, ev, pid, off in A:
        add(mem, s, r, t, ev, pid, off, 0.6, "agent")
    return mem.execute("SELECT count(*) FROM module_relations").fetchone()[0] - n0
