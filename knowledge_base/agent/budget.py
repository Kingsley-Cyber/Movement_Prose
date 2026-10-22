"""Motion complexity budget over overlapping windows (handbook heuristic, upper bounds only)."""
from .ir import finding
from .policy import CLASSES, SCENE

PRIORITY_RANK = dict((c, i) for i, c in enumerate(CLASSES))


def overlaps(a_start, a_end, b_start, b_end):
    return max(a_start, b_start) < min(a_end, b_end)


def windows(items):
    """items: [(start, end, payload)] -> [(a, b, [payloads active over [a, b))] over elementary intervals."""
    points = sorted(set([s for s, _, _ in items] + [e for _, e, _ in items]))
    out = []
    for a, b in zip(points, points[1:]):
        active = [p for s, e, p in items if s < b and e > a]
        if active:
            out.append((a, b, active))
    return out


def _authored_class(a):
    if a.budget_class:
        return a.budget_class
    return {"primary_action": "dominant_action", "camera_optics": "camera_move",
            "secondary_motion": "secondary_body"}.get(a.slot_id, "none")


def budget_items(ir, catalog, policy):
    items = []
    for s in ir.active_selections():
        d = catalog.get(s.directive_id)
        cls = policy.budget_class(s.directive_id)
        if cls in ("none", "camera_static"):
            continue
        items.append({"kind": cls, "subjects": policy.subjects_of(s, s.directive_id), "start": s.start_frame,
                      "end": s.end_frame, "ref": s.directive_id, "event_id": s.event_id,
                      "priority": policy.effective_priority(s, d), "locked": policy.is_locked(s.directive_id)})
    for a in ir.authored:
        ev = ir.event(a.event_id)
        if ev is None:
            continue
        cls = _authored_class(a)
        if cls in ("none", "camera_static"):
            continue
        locked = a.slot_id in policy.locked_authored_slots
        subjects = [SCENE] if cls in ("material_response", "camera_move") else [ev.actor_id]
        items.append({"kind": cls, "subjects": subjects, "start": ev.start_frame, "end": ev.end_frame,
                      "ref": "authored:%s:%s" % (a.event_id, a.slot_id), "event_id": a.event_id,
                      "priority": "locked" if locked else (a.priority or "medium"), "locked": locked})
    return items


def drop_candidate(group):
    candidates = [g for g in group if not g["locked"]]
    if not candidates:
        return None
    return max(candidates, key=lambda g: (PRIORITY_RANK.get(g["priority"], 99), g["ref"]))


def _violation(code, label, group, limit, window=None):
    refs = ", ".join(sorted(g["ref"] for g in group))
    drop = drop_candidate(group)
    where = "" if window is None else " in frames [%d,%d)" % window
    advice = ("drop candidate %s (reason lower_priority)" % drop["ref"]) if drop else "every item is locked: re-stage the beats"
    msg = "%d %s%s (max %d): %s; %s" % (len(group), label, where, limit, refs, advice)
    return finding("error", code, msg, group[0]["event_id"], None if not drop else (drop["ref"] if not drop["ref"].startswith("authored:") else None))


def budget_violations(ir, catalog, policy):
    out, seen = [], set()
    items = budget_items(ir, catalog, policy)
    limits = policy.limits

    def add(f, key):
        if key not in seen:
            seen.add(key)
            out.append(f)

    cams = [i for i in items if i["kind"] == "camera_move" and i["ref"] not in policy.camera_count_exempt]
    if len(cams) > limits["camera_move"]["max"]:
        add(_violation("BUDGET_CAMERA_MOVE", "camera moves in the clip", cams, limits["camera_move"]["max"]),
            ("cam", frozenset(c["ref"] for c in cams)))
    for a, b, active in windows([(i["start"], i["end"], i) for i in items]):
        mats = [i for i in active if i["kind"] == "material_response"]
        if len(mats) > limits["material_response"]["max"]:
            add(_violation("BUDGET_MATERIAL_RESPONSE", "passive material responses", mats, limits["material_response"]["max"], (a, b)),
                ("mat", frozenset(m["ref"] for m in mats)))
        subjects = set(s for i in active for s in i["subjects"])
        for subj in sorted(subjects):
            for kind, code, label in (("dominant_action", "BUDGET_DOMINANT_ACTION", "dominant actions for %s" % subj),
                                      ("secondary_body", "BUDGET_SECONDARY_BODY", "secondary body actions for %s" % subj)):
                group = [i for i in active if i["kind"] == kind and subj in i["subjects"]]
                if len(group) > limits[kind]["max"]:
                    add(_violation(code, label, group, limits[kind]["max"], (a, b)),
                        (kind, subj, frozenset(g["ref"] for g in group)))
    for s in ir.active_selections():
        if s.directive_id in policy.camera_count_exempt:
            if not any(c["start"] < s.start_frame for c in cams):
                out.append(finding("note", "CAMERA_SETTLE_WITHOUT_MOVE",
                                   "%s selected with no earlier camera move to settle from" % s.directive_id,
                                   s.event_id, s.directive_id))
    return out
