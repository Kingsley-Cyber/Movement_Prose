"""Checks: the bundle validator's composition rules re-applied to an IR, plus priority, budget and engine rules."""
import json
import re
from pathlib import Path

from . import GLOBAL_SLOTS, PLACEHOLDER
from . import engines as eng
from .budget import budget_violations, overlaps
from .ir import finding, substitute

NUMERIC_RE = re.compile(r"\b\d+(?:\.\d+)?\s*(?:fps|frames?)\b", re.I)
SHORTHAND = ("yutapon", "kanada", "itano", "ohira", "nakamura", "ufotable", "sakuga", "on twos", "on ones",
             "on threes", "kagenashi", "hashimoto", "matsumoto", "imaishi", "sushio")
PROVIDER_REASONS = ("provider_unsupported", "already_encoded_by_stronger_control")


def _entities_of(sel):
    return set(x for x in (sel.actor_id, sel.target_id) if x)


def check_events(ir):
    out, ids = [], set()
    for e in ir.events:
        if e.event_id in ids:
            out.append(finding("error", "EVENT_DUPLICATE_ID", "event_id repeated: %s" % e.event_id, e.event_id))
        ids.add(e.event_id)
    by_id = dict((e.event_id, e) for e in ir.events)
    for e in ir.events:
        if e.end_frame > ir.clip.frame_count:
            out.append(finding("error", "EVENT_OUTSIDE_CLIP", "event %s ends at %d > frame_count %d" % (e.event_id, e.end_frame, ir.clip.frame_count), e.event_id))
        if e.actor_id not in ir.entities:
            out.append(finding("error", "EVENT_UNKNOWN_ENTITY", "event %s actor_id %r is not an entity" % (e.event_id, e.actor_id), e.event_id))
        if e.target_id and e.target_id not in ir.entities:
            out.append(finding("error", "EVENT_UNKNOWN_ENTITY", "event %s target_id %r is not an entity" % (e.event_id, e.target_id), e.event_id))
        for ref_name in ("depends_on", "inherit_from"):
            ref = getattr(e, ref_name)
            if ref is None:
                continue
            if ref not in by_id:
                out.append(finding("error", "EVENT_BAD_REFERENCE", "event %s %s=%r does not exist" % (e.event_id, ref_name, ref), e.event_id))
            elif by_id[ref].start_frame > e.start_frame:
                out.append(finding("error", "EVENT_BAD_REFERENCE", "event %s %s=%r starts later than it" % (e.event_id, ref_name, ref), e.event_id))
    return out


def check_selections(ir, catalog):
    out = []
    for s in ir.selections:
        if s.directive_id not in catalog:
            out.append(finding("error", "UNKNOWN_DIRECTIVE", "unknown directive_id %s" % s.directive_id, s.event_id, s.directive_id))
            continue
        ev = ir.event(s.event_id)
        if ev is None:
            out.append(finding("error", "SELECTION_UNKNOWN_EVENT", "%s refers to missing event %s" % (s.directive_id, s.event_id), s.event_id, s.directive_id))
            continue
        d = catalog.get(s.directive_id)
        if d.moment_type != ev.moment_type:
            out.append(finding("error", "MOMENT_MISMATCH", "%s is a %s row but event %s is %s" % (s.directive_id, d.moment_type, ev.event_id, ev.moment_type), s.event_id, s.directive_id))
        if s.start_frame < ev.start_frame or s.end_frame > ev.end_frame:
            out.append(finding("warning", "SELECTION_OUTSIDE_EVENT", "%s spans [%d,%d) outside event %s [%d,%d)" % (s.directive_id, s.start_frame, s.end_frame, ev.event_id, ev.start_frame, ev.end_frame), s.event_id, s.directive_id))
        for key, value in (("actor_id", s.actor_id), ("target_id", s.target_id)):
            if value and value not in ir.entities:
                out.append(finding("error", "SELECTION_UNKNOWN_ENTITY", "%s %s=%r is not an entity" % (s.directive_id, key, value), s.event_id, s.directive_id))
    return out


def check_bindings(ir, catalog):
    out = []
    for s in ir.active_selections():
        if s.directive_id not in catalog or ir.event(s.event_id) is None:
            continue
        names = catalog.placeholders(s.directive_id)
        if "actor" in names and not s.actor_id:
            out.append(finding("error", "BINDING_MISSING", "%s uses {actor} but the selection has no actor_id" % s.directive_id, s.event_id, s.directive_id))
        if "target" in names and not s.target_id:
            out.append(finding("error", "BINDING_MISSING", "%s uses {target} but the selection has no target_id" % s.directive_id, s.event_id, s.directive_id))
        if "contact_origin" in names and not ir.contact_origins.get(s.event_id):
            out.append(finding("error", "BINDING_MISSING", "%s uses {contact_origin} but event %s has no contact_origins entry" % (s.directive_id, s.event_id), s.event_id, s.directive_id))
        d = catalog.get(s.directive_id)
        for text in (d.prompt_snippet, d.negative_snippet):
            left = PLACEHOLDER.findall(substitute(text, s, ir))
            if left:
                out.append(finding("error", "PLACEHOLDER_UNRESOLVED", "%s leaves %s unresolved" % (s.directive_id, ", ".join(left)), s.event_id, s.directive_id))
    return out


def check_duplicate_slots(ir, catalog, policy, key="subject"):
    out = []
    sels = [s for s in ir.active_selections() if s.directive_id in catalog]
    for i, a in enumerate(sels):
        for b in sels[i + 1:]:
            if not overlaps(a.start_frame, a.end_frame, b.start_frame, b.end_frame):
                continue
            da, db = catalog.get(a.directive_id), catalog.get(b.directive_id)
            if da.slot_id != db.slot_id:
                continue
            if da.slot_id in GLOBAL_SLOTS:
                clash = True
            elif key == "actor":
                clash = a.actor_id == b.actor_id
            else:
                clash = bool(set(policy.subjects_of(a, a.directive_id)) & set(policy.subjects_of(b, b.directive_id)))
            if clash:
                out.append(finding("error", "DUPLICATE_SLOT", "%s and %s both fill %s for the same %s over overlapping frames" % (a.directive_id, b.directive_id, da.slot_id, "global scope" if da.slot_id in GLOBAL_SLOTS else key), a.event_id, a.directive_id))
    return out


def check_declared_conflicts(ir, catalog):
    out = []
    sels = [s for s in ir.active_selections() if s.directive_id in catalog]
    for i, a in enumerate(sels):
        for b in sels[i + 1:]:
            if not overlaps(a.start_frame, a.end_frame, b.start_frame, b.end_frame):
                continue
            if b.directive_id not in catalog.conflicts(a.directive_id):
                continue
            da, db = catalog.get(a.directive_id), catalog.get(b.directive_id)
            global_scope = da.slot_id in GLOBAL_SLOTS or db.slot_id in GLOBAL_SLOTS
            if global_scope or (_entities_of(a) & _entities_of(b)):
                out.append(finding("error", "CONFLICT", "declared conflict %s / %s overlaps in time and scope" % (a.directive_id, b.directive_id), a.event_id, a.directive_id))
    return out


def check_prerequisites(ir, catalog, policy):
    out = []
    active = ir.active_selections()
    for s in active:
        if s.directive_id not in catalog:
            continue
        ev = ir.event(s.event_id)
        declared = set(ev.declared_prerequisites or []) if ev else set()
        for token in catalog.requires(s.directive_id):
            if token in declared:
                continue
            satisfiers = policy.satisfiers(token)
            if any(o.directive_id in satisfiers and o.start_frame < s.end_frame for o in active if o is not s):
                continue
            if not policy.known_token(token):
                hint = "unknown token; declare it on the event"
            elif satisfiers:
                hint = "select one of %s in an earlier or overlapping window, or declare it" % ", ".join(satisfiers)
            else:
                hint = "no catalog row satisfies it; declare it on event %s" % s.event_id
            out.append(finding("error", "PREREQUISITE_MISSING", "%s requires %s: %s" % (s.directive_id, token, hint), s.event_id, s.directive_id))
    return out


def check_priorities(ir, catalog, policy):
    out = []
    for s in ir.selections:
        if s.directive_id not in catalog:
            continue
        if s.priority and s.priority not in policy.classes:
            out.append(finding("error", "PRIORITY_UNKNOWN", "%s priority %r not in %s" % (s.directive_id, s.priority, policy.classes), s.event_id, s.directive_id))
            continue
        locked = policy.is_locked(s.directive_id)
        if locked and s.priority and s.priority != "locked":
            out.append(finding("error", "LOCKED_DOWNGRADED", "%s is locked; priority %r is not allowed" % (s.directive_id, s.priority), s.event_id, s.directive_id))
        if s.suppressed_reason:
            if s.suppressed_reason not in policy.reasons:
                out.append(finding("error", "REASON_UNKNOWN", "%s suppressed with unknown reason %r" % (s.directive_id, s.suppressed_reason), s.event_id, s.directive_id))
                continue
            prio = policy.effective_priority(s, catalog.get(s.directive_id))
            if prio == "locked":
                out.append(finding("error", "LOCKED_SUPPRESSED", "%s is locked and cannot be suppressed" % s.directive_id, s.event_id, s.directive_id))
            elif not policy.may_suppress(prio, s.suppressed_reason):
                out.append(finding("error", "REQUIRED_NEEDS_PROVIDER_REASON", "%s is %s; suppression needs one of %s" % (s.directive_id, prio, ", ".join(PROVIDER_REASONS)), s.event_id, s.directive_id))
    for a in ir.authored:
        if a.priority and a.priority not in policy.classes:
            out.append(finding("error", "PRIORITY_UNKNOWN", "authored %s priority %r unknown" % (a.event_id, a.priority), a.event_id))
    return out


def check_event_has_action(ir, catalog):
    out = []
    for e in ir.events:
        has_row = any(s.event_id == e.event_id and s.directive_id in catalog and catalog.get(s.directive_id).slot_id == "primary_action" for s in ir.active_selections())
        has_authored = any(a.event_id == e.event_id and a.slot_id == "primary_action" for a in ir.authored)
        if not (has_row or has_authored):
            out.append(finding("error", "EVENT_WITHOUT_ACTION", "event %s has no primary_action row and no authored action" % e.event_id, e.event_id))
    return out


def check_engine_profile(ir, profiles):
    out = []
    if ir.engine_profile_id not in profiles:
        out.append(finding("error", "ENGINE_UNKNOWN", "unknown engine_profile_id %r" % ir.engine_profile_id))
        return out
    p = profiles[ir.engine_profile_id]
    status = eng.dispatch_status(p)
    if status == "retired":
        out.append(finding("error", "ENGINE_RETIRED", "%s is a retired target" % ir.engine_profile_id))
    elif status == "exact_target_required":
        out.append(finding("warning", "ENGINE_EXACT_TARGET_REQUIRED", "%s: draft allowed, dispatch refused until the exact model and endpoint are named" % ir.engine_profile_id))
    elif status == "draft_only":
        out.append(finding("warning", "ENGINE_DRAFT_ONLY", "%s documents product capabilities only; no request schema" % ir.engine_profile_id))
    limit = eng.duration_limit(p)
    if limit is not None and ir.clip.duration_seconds > limit:
        out.append(finding("error", "DURATION_LIMIT", "clip is %.2f s; %s documents at most %s s" % (ir.clip.duration_seconds, ir.engine_profile_id, limit)))
    note = eng.frame_note(p, ir.clip.frame_count)
    if note:
        out.append(finding("note", "ENGINE_FRAME_CONTRACT", note))
    if eng.negatives_status(p) == "conditional":
        out.append(finding("note", "NEGATIVES_CONDITIONAL", "%s negatives act only under classifier-free guidance; verify the preset" % ir.engine_profile_id))
    return out


def check_authored_text(ir):
    out = []
    texts = [(a.event_id, a.text) for a in ir.authored] + [(None, ir.scene_context)]
    for event_id, text in texts:
        if NUMERIC_RE.search(text or ""):
            out.append(finding("warning", "NUMERIC_IN_PROMPT", "fps or frame numbers belong in post_plan, not prose: %r" % NUMERIC_RE.search(text).group(0), event_id))
        low = (text or "").lower()
        for word in SHORTHAND:
            if word in low:
                out.append(finding("warning", "SHORTHAND_IN_PROMPT", "animator/studio shorthand %r in prose; describe the visual instead" % word, event_id))
    return out


def check_redundancy(ir, catalog, policy):
    out, seen = [], set()
    sels = [s for s in ir.active_selections() if s.directive_id in catalog]
    for i, a in enumerate(sels):
        for b in sels[i + 1:]:
            if a.directive_id != b.directive_id or a.event_id == b.event_id:
                continue
            ea, eb = ir.event(a.event_id), ir.event(b.event_id)
            if ea is None or eb is None:
                continue
            first, second = (ea, eb) if ea.start_frame <= eb.start_frame else (eb, ea)
            if second.start_frame > first.end_frame:
                continue
            if not (set(policy.subjects_of(a, a.directive_id)) & set(policy.subjects_of(b, b.directive_id))):
                continue
            key = (a.directive_id, first.event_id, second.event_id)
            if key in seen:
                continue
            seen.add(key)
            out.append(finding("warning", "REDUNDANT_RESELECTION", "%s reselected in %s right after %s for the same subject; set inherit_from instead" % (a.directive_id, second.event_id, first.event_id), second.event_id, a.directive_id))
    return out


def check_handbook_refs(ir, handbook_conn):
    out = []
    refs = [(a.event_id, r) for a in ir.authored for r in (a.handbook_refs or [])]
    if not refs:
        return out
    if handbook_conn is None:
        out.append(finding("warning", "HANDBOOK_INDEX_MISSING", "%d handbook_refs cannot be verified: no handbook_index.db" % len(refs)))
        return out
    from . import handbook as hb
    from . import query as q
    for event_id, ref in refs:
        if hb.get_passage(handbook_conn, q.resolve_id(handbook_conn, ref)) is None:
            out.append(finding("error", "HANDBOOK_REF_UNKNOWN", "authored text cites unknown passage %r" % ref, event_id))
    return out


def check_taste(ir, profiles):
    if ir.taste_profile_id and ir.taste_profile_id not in profiles:
        return [finding("error", "TASTE_UNKNOWN", "unknown taste_profile_id %r" % ir.taste_profile_id)]
    return []


LEVEL_ORDER = {"error": 0, "warning": 1, "note": 2}


def check_ir(ir, catalog, policy, engine_profiles, taste_profiles=None, key="subject", handbook_conn=None):
    findings = []
    findings += check_events(ir)
    findings += check_selections(ir, catalog)
    findings += check_bindings(ir, catalog)
    findings += check_duplicate_slots(ir, catalog, policy, key=key)
    findings += check_declared_conflicts(ir, catalog)
    findings += check_prerequisites(ir, catalog, policy)
    findings += check_priorities(ir, catalog, policy)
    findings += check_event_has_action(ir, catalog)
    findings += budget_violations(ir, catalog, policy)
    findings += check_engine_profile(ir, engine_profiles)
    findings += check_authored_text(ir)
    findings += check_redundancy(ir, catalog, policy)
    if taste_profiles is not None:
        findings += check_taste(ir, taste_profiles)
    findings += check_handbook_refs(ir, handbook_conn)
    findings.sort(key=lambda f: (LEVEL_ORDER.get(f.level, 9), f.code, f.event_id or "", f.directive_id or ""))
    return findings


def report(findings, key="subject"):
    errors = [f for f in findings if f.level == "error"]
    return {"status": "fail" if errors else "pass", "key": key,
            "errors": len(errors), "warnings": sum(1 for f in findings if f.level == "warning"),
            "notes": sum(1 for f in findings if f.level == "note"),
            "findings": [f._asdict() for f in findings]}


def write_report(run_dir, rep):
    path = Path(run_dir) / "check_report.json"
    path.write_text(json.dumps(rep, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return path
