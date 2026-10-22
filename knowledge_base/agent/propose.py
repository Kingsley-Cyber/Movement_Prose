"""Candidate rows per event x slot (the 'intent decomposer' step is a lookup, not a search), plus lexical gap detection."""
import json
import re
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path

from . import BUNDLE_DIR
from . import taste as taste_mod
from .ir import Event

STOPWORDS = set("a an the and or to of in on at with from into onto by for as is are be that this his her their its "
                "then into over under up down out off he she it they them we you my our your who what which when where "
                "while big huge very really just one two three s".split())
_WORD = re.compile(r"[a-z]+")


def _stems(word):
    out = {word}
    for suffix in ("ing", "ed", "es", "s"):
        if word.endswith(suffix) and len(word) - len(suffix) >= 3:
            out.add(word[: -len(suffix)])
    return out


def catalog_text(catalog, moments=None):
    chunks = []
    for d in catalog.rows():
        if moments and d.moment_type not in moments:
            continue
        cat = d.catalog or {}
        chunks.append(" ".join([d.prompt_snippet, d.negative_snippet, cat.get("title", ""), " ".join(cat.get("aliases", []) or []),
                                d.mechanics.get("editorial_recipe", "") or "", d.directive_id.replace("_", " ")]))
    return " ".join(chunks).lower()


def lexical_gaps(request, catalog, moments=None):
    corpus = catalog_text(catalog, moments)
    gaps = []
    for word in _WORD.findall(request.lower()):
        if len(word) < 4 or word in STOPWORDS:
            continue
        if not any(re.search(r"\b" + re.escape(stem), corpus) for stem in _stems(word)):
            if word not in gaps:
                gaps.append(word)
    return gaps


def default_events(duration_seconds, fps=24, bundle_dir=BUNDLE_DIR):
    """The bundle's single-exchange sequence_plan scaled to the requested duration."""
    plan = json.loads((Path(bundle_dir) / "example_payloads.json").read_text(encoding="utf-8"))["sequence_plan"]
    source_frames = plan["frame_count"]
    frame_count = int(round(duration_seconds * fps))
    scale = float(frame_count) / float(source_frames)
    events = []
    for e in plan["events"]:
        start = int(round(e["start_frame"] * scale))
        end = max(start + 1, int(round(e["end_frame"] * scale)))
        events.append(Event(event_id=e["event_id"], actor_id=e["actor_id"], target_id=e.get("target_id"),
                            moment_type=e["moment_type"], start_frame=start, end_frame=min(end, frame_count),
                            depends_on=e.get("depends_on")))
    return events, frame_count


def propose(request, events, catalog, policy, profile=None, sub_genre=None, handbook_conn=None, handbook_limit=3, mem=None, follow_depth=0):
    proposal = OrderedDict([("request", request), ("taste_profile_id", (profile or {}).get("taste_id")),
                            ("sub_genre_hint", sub_genre or (profile or {}).get("sub_genre_hint")),
                            ("budget_limits", policy.limits), ("propose_hints", policy.budget.get("propose_hints", {})),
                            ("events", [])])
    for ev in events:
        slots = OrderedDict()
        for slot in catalog.slot_order:
            rows = catalog.rows(slot=slot, moment=ev.moment_type)
            ranked = taste_mod.rank(rows, profile, sub_genre)
            slots[slot] = [OrderedDict([
                ("directive_id", d.directive_id), ("title", (d.catalog or {}).get("title", "")), ("mark", mark),
                ("sub_genre", d.sub_genre), ("default_priority", "locked" if policy.is_locked(d.directive_id) else policy.default_priority(d)),
                ("budget_class", policy.budget_class(d.directive_id)), ("subject", policy.subject_kind(d.directive_id)),
                ("placeholders", sorted(catalog.placeholders(d.directive_id))), ("conflicts", sorted(catalog.conflicts(d.directive_id))),
                ("requires", catalog.requires(d.directive_id)),
            ]) for d, mark in ranked]
        handbook = OrderedDict()
        if handbook_conn is not None:
            from . import query as q
            for slot in catalog.slot_order:
                handbook[slot] = [OrderedDict([("id", h["id"]), ("score", h["score"]), ("cite", h["cite"]), ("line", h["line"])])
                                  for h in q.lookup(handbook_conn, moment=ev.moment_type, slot=slot, min_score=2, limit=handbook_limit)]
        pulled = []
        if mem is not None and follow_depth:
            from . import relations as rel
            seeds = [r["directive_id"] for r in slots.get("primary_action", [])]
            for p_ in rel.follow(mem, seeds, depth=follow_depth):
                d = catalog.get(p_["id"]) if p_["id"] in catalog else None
                pulled.append(OrderedDict([("directive_id", p_["id"]), ("slot_id", d.slot_id if d else None), ("moment_type", d.moment_type if d else None),
                                           ("relation", p_["relation"]), ("via", p_["via"]), ("offset", p_["offset"]), ("evidence", p_["evidence"]), ("passage_id", p_["passage_id"])]))
        proposal["events"].append(OrderedDict([("event_id", ev.event_id), ("actor_id", ev.actor_id), ("target_id", ev.target_id),
                                               ("moment_type", ev.moment_type), ("frames", [ev.start_frame, ev.end_frame]),
                                               ("empty_slots", [s for s, rows in slots.items() if not rows]), ("slots", slots),
                                               ("handbook", handbook), ("pulled", pulled)]))
    proposal["lexical_gaps"] = lexical_gaps(request, catalog, set(e.moment_type for e in events))
    proposal["taste_gaps"] = list((profile or {}).get("gaps", []))
    return proposal


def append_gaps(path, request, gaps, taste_id=None):
    path = Path(path)
    if not gaps:
        return 0
    now = datetime.now(timezone.utc).isoformat()
    with path.open("a", encoding="utf-8") as fh:
        for term in gaps:
            fh.write(json.dumps({"when": now, "request": request, "term": term, "taste_profile_id": taste_id,
                                 "kind": "lexical", "note": "no catalog row text mentions this term; author it or add a row"}, ensure_ascii=False) + "\n")
    return len(gaps)


def format_table(proposal, limit=4):
    lines = ["request: %s" % proposal["request"], "taste: %s   sub_genre hint: %s" % (proposal["taste_profile_id"], proposal["sub_genre_hint"])]
    for ev in proposal["events"]:
        lines.append("")
        lines.append("== %s  %s  [%d,%d)  %s%s" % (ev["event_id"], ev["moment_type"], ev["frames"][0], ev["frames"][1], ev["actor_id"],
                                                  (" -> " + ev["target_id"]) if ev["target_id"] else ""))
        for slot, rows in ev["slots"].items():
            shown = rows[:limit]
            cells = ["%s%s[%s/%s]" % ({"preferred": "+", "avoid": "-", "neutral": " "}[r["mark"]], r["directive_id"], r["default_priority"], r["budget_class"]) for r in shown]
            more = "" if len(rows) <= limit else "  (+%d)" % (len(rows) - limit)
            lines.append("  %-17s %s%s" % (slot, "  ".join(cells), more))
            hb = ev.get("handbook", {}).get(slot) or []
            if hb:
                lines.append("  %-17s handbook: %s" % ("", "  ".join("%s(%s)" % (h["id"].split("#")[-1] if "#" in h["id"] else h["id"], h["score"]) for h in hb)))
                lines.append("  %-17s   %s" % ("", hb[0]["line"][:120]))
    for ev in proposal["events"]:
        if ev.get("pulled"):
            lines.append("  %-17s pulled: %s" % ("relations", "  ".join("%s(%s %s)" % (p["directive_id"], p["relation"], p["via"].replace("aa_", "")) for p in ev["pulled"][:8])))
    if proposal.get("lexical_gaps"):
        lines.append("")
        lines.append("lexical gaps (no catalog text mentions): " + ", ".join(proposal["lexical_gaps"]))
    if proposal.get("taste_gaps"):
        lines.append("taste gaps: " + "; ".join(proposal["taste_gaps"]))
    return "\n".join(lines)
