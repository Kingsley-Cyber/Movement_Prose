"""Project a checked IR to prose in the handbook's director-language clause order."""
import hashlib
import json
from collections import OrderedDict, namedtuple
from pathlib import Path

from . import __version__
from . import engines as eng
from .ir import frames_to_seconds, substitute

EmitResult = namedtuple("EmitResult", "prompt negative post_plan receipt")
MOMENT_WORDS = {"anticipation": "anticipation", "execution": "execution", "impact": "impact",
                "recoil": "recoil", "follow_through": "follow-through", "recovery": "recovery"}


def clause_of(directive, budget_class):
    if budget_class == "secondary_body":
        return "PERFORMANCE"
    if directive.slot_id in ("subject_anchor", "primary_action"):
        return "SUBJECT AND ACTION"
    if directive.slot_id == "temporal_cadence":
        return "TIMING"
    return "CAMERA AND PRESENTATION"


def _dedupe_phrases(texts):
    seen, out = set(), []
    for text in texts:
        for phrase in [p.strip().rstrip(".") for p in text.split(",")]:
            key = phrase.lower()
            if phrase and key not in seen:
                seen.add(key)
                out.append(phrase)
    return out


def _beat_label(index, ev, inherit_index=None):
    who = ev.actor_id if not ev.target_id else "%s vs %s" % (ev.actor_id, ev.target_id)
    if inherit_index:
        return "Beat %d (%s, continuing from beat %d)" % (index, who, inherit_index)
    return "Beat %d (%s)" % (index, who)


def _span(ev, fps):
    return "%.2f-%.2f s" % (frames_to_seconds(ev.start_frame, fps), frames_to_seconds(ev.end_frame, fps))


def negatives_for(profile, phrases, avoid_sentence=False):
    """-> (negative_text_or_None, inline_sentence_or_None, route, reason)"""
    status = eng.negatives_status(profile)
    text = ", ".join(phrases) if phrases else ""
    if not phrases:
        return None, None, "none", None
    if status in ("active", "conditional"):
        return text, None, "negative_field" if status == "active" else "negative_field_conditional", None
    if avoid_sentence:
        return None, "Avoid: " + text + ".", "inline_positive_unverified", None
    return None, None, "suppressed", "provider_unsupported"


def post_plan(ir, catalog):
    entries = []
    fps = ir.clip.editorial_fps
    for s in ir.active_selections():
        d = catalog.get(s.directive_id)
        route = d.mechanics.get("preferred_route") or ""
        if "editorial" in route or "post" in route or "retime" in route:
            entries.append(OrderedDict([
                ("directive_id", s.directive_id), ("event_id", s.event_id), ("preferred_route", route),
                ("frames", [s.start_frame, s.end_frame]),
                ("seconds", [frames_to_seconds(s.start_frame, fps), frames_to_seconds(s.end_frame, fps)]),
                ("editorial_recipe", d.mechanics.get("editorial_recipe")), ("camera_rule", d.mechanics.get("camera_rule")),
                ("validation", d.mechanics.get("validation")),
            ]))
    return OrderedDict([
        ("editorial_fps", fps), ("frame_count", ir.clip.frame_count),
        ("interval_convention", "zero-based [start_frame,end_frame)"),
        ("note", "Frame-level operations belong to an exposure sheet or postproduction, not to the prompt (lexicon section 4)."),
        ("editorial_operations", list(ir.editorial_operations)),
        ("routed_directives", entries),
    ])


def emit(ir, catalog, policy, profile, taste_profile=None, avoid_sentence=False, handbook_conn=None):
    fps = ir.clip.editorial_fps
    events = ir.events_in_order()
    index_of = dict((e.event_id, i + 1) for i, e in enumerate(events))
    slot_rank = dict((s, i) for i, s in enumerate(catalog.slot_order))
    by_event = {}
    for s in ir.active_selections():
        by_event.setdefault(s.event_id, []).append(s)
    for sels in by_event.values():
        sels.sort(key=lambda s: (slot_rank.get(catalog.get(s.directive_id).slot_id, 99), s.start_frame, s.directive_id))
    authored_by_event = {}
    for a in ir.authored:
        authored_by_event.setdefault(a.event_id, []).append(a)

    manifest, negatives, chars_by_event = [], [], OrderedDict()
    shot_parts = ["A %.1f-second shot." % ir.clip.duration_seconds, ir.scene_context.strip()]
    action_lines, perf_lines, timing_lines, cam_lines = [], [], [], []
    if taste_profile and taste_profile.get("effort_quality"):
        q = taste_profile["effort_quality"]
        perf_lines.append("Movement quality: %s weight, %s time, %s space, %s flow." % (q.get("weight"), q.get("time"), q.get("space"), q.get("flow")))
    for i, ev in enumerate(events, 1):
        parts = {"SUBJECT AND ACTION": [], "PERFORMANCE": [], "TIMING": [], "CAMERA AND PRESENTATION": []}
        for s in by_event.get(ev.event_id, []):
            d = catalog.get(s.directive_id)
            cls = policy.budget_class(s.directive_id)
            text = substitute(d.prompt_snippet, s, ir).strip()
            clause = clause_of(d, cls)
            if i == 1 and cls == "camera_static":
                shot_parts.append(text)
                clause = "SHOT AND DURATION"
            else:
                parts[clause].append(text)
            negatives.append(substitute(d.negative_snippet, s, ir))
            manifest.append(OrderedDict([("ordinal", len(manifest) + 1), ("directive_id", s.directive_id), ("event_id", s.event_id),
                                         ("slot_id", d.slot_id), ("moment_type", d.moment_type), ("clause", clause),
                                         ("priority", policy.effective_priority(s, d)), ("budget_class", cls),
                                         ("subjects", policy.subjects_of(s, s.directive_id)), ("frames", [s.start_frame, s.end_frame])]))
        for a in authored_by_event.get(ev.event_id, []):
            clause = a.clause if a.clause in parts else "SUBJECT AND ACTION"
            parts[clause].append(a.text.strip())
            manifest.append(OrderedDict([("ordinal", len(manifest) + 1), ("directive_id", None), ("event_id", a.event_id),
                                         ("slot_id", a.slot_id), ("clause", clause), ("origin", a.origin), ("why", a.why),
                                         ("priority", "locked" if a.slot_id in policy.locked_authored_slots else (a.priority or "medium")),
                                         ("text", a.text)]))
        inherit_index = index_of.get(ev.inherit_from) if ev.inherit_from else None
        label = _beat_label(i, ev, inherit_index)
        if parts["SUBJECT AND ACTION"]:
            action_lines.append("%s: %s" % (label, " ".join(parts["SUBJECT AND ACTION"])))
        else:
            action_lines.append("%s: (no new action text; state continues)" % label)
        if parts["PERFORMANCE"]:
            perf_lines.append("Beat %d: %s" % (i, " ".join(parts["PERFORMANCE"])))
        who = ev.actor_id if not ev.target_id else "%s on %s" % (ev.actor_id, ev.target_id)
        timing = "Beat %d, %s (%s; %s)" % (i, _span(ev, fps), MOMENT_WORDS.get(ev.moment_type, ev.moment_type), who)
        if ev.depends_on:
            timing += ", after beat %d" % index_of.get(ev.depends_on, 0)
        if parts["TIMING"]:
            timing += ": " + " ".join(parts["TIMING"])
        else:
            timing += "."
        timing_lines.append(timing)
        if parts["CAMERA AND PRESENTATION"]:
            cam_lines.append("Beat %d: %s" % (i, " ".join(parts["CAMERA AND PRESENTATION"])))
        chars_by_event[ev.event_id] = sum(len(t) for group in parts.values() for t in group)

    sections = [("SHOT AND DURATION", [" ".join(p for p in shot_parts if p)]),
                ("SUBJECT AND ACTION", action_lines), ("PERFORMANCE", perf_lines),
                ("TIMING", timing_lines), ("CAMERA AND PRESENTATION", cam_lines)]
    phrases = _dedupe_phrases(negatives)
    negative_text, inline, route, reason = negatives_for(profile, phrases, avoid_sentence)
    if inline:
        sections.append(("NEGATIVES", [inline]))
    prompt = "\n\n".join("[%s]\n%s" % (name, "\n".join(lines)) for name, lines in sections if lines) + "\n"

    covered, total = 0, 0
    for s in ir.active_selections():
        d = catalog.get(s.directive_id)
        probe = substitute(d.prompt_snippet, s, ir).strip()[:40]
        total += 1
        if probe and probe in prompt:
            covered += 1
    receipt = OrderedDict([
        ("agent_version", __version__), ("catalog_fingerprint", catalog.fingerprint()),
        ("engine_profile_id", profile["profile_id"]), ("engine_status", profile.get("status")),
        ("taste_profile_id", ir.taste_profile_id), ("request", ir.request),
        ("chars_total", len(prompt)), ("chars_by_event", chars_by_event),
        ("prompt_sha256", hashlib.sha256(prompt.encode("utf-8")).hexdigest()),
        ("coverage", {"covered": covered, "total": total}),
        ("negatives", OrderedDict([("route", route), ("reason", reason), ("status", eng.negatives_status(profile)),
                                   ("phrases", phrases), ("chars", len(negative_text or ""))])),
        ("suppressed", [OrderedDict([("directive_id", s.directive_id), ("event_id", s.event_id), ("reason", s.suppressed_reason)])
                        for s in ir.selections if s.suppressed_reason]),
        ("authored", [OrderedDict([("event_id", a.event_id), ("slot_id", a.slot_id), ("clause", a.clause), ("why", a.why),
                                   ("handbook_refs", _ref_cites(handbook_conn, a.handbook_refs))]) for a in ir.authored]),
        ("manifest", manifest),
        ("limits", ["No render was run; every row is an untested prompt candidate.",
                    "Coverage counts the first 40 characters of each selected snippet found in the prompt; it does not prove the model obeys them."]),
    ])
    return EmitResult(prompt, negative_text, post_plan(ir, catalog), receipt)


def _ref_cites(handbook_conn, refs):
    out = []
    for ref in refs or []:
        entry = OrderedDict([("passage_id", ref)])
        if handbook_conn is not None:
            from . import handbook as hb
            from . import query as q
            row = hb.get_passage(handbook_conn, q.resolve_id(handbook_conn, ref))
            if row:
                entry["cite"] = hb.cite(row)
                entry["src"] = row.get("src")
                entry["cpcs_id"] = row.get("cpcs_id")
        out.append(entry)
    return out


def write_outputs(out_dir, result):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "prompt.txt").write_text(result.prompt, encoding="utf-8")
    neg = out_dir / "negative.txt"
    if result.negative:
        neg.write_text(result.negative + "\n", encoding="utf-8")
    elif neg.exists():
        neg.unlink()
    (out_dir / "post_plan.json").write_text(json.dumps(result.post_plan, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    (out_dir / "receipt.json").write_text(json.dumps(result.receipt, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return out_dir
