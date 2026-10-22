"""Mechanism-vocabulary mining with lexical pre-filters. Writes a review document; never touches the index."""
import json
import re
from collections import Counter, OrderedDict, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from . import BUNDLE_DIR
from . import handbook as hb

TERM_RX = re.compile(r"\b([a-z]+-[a-z]+(?:-[a-z]+)?|[a-z]{4,} (?:hold|lock|ramp|curve|window|offset|lag|drift|snap|blur|jitter|damping|spring|impulse|decay|onset|interpolation|exposure|flash|smear|arc|recoil|settle|burst|shake|freeze|frame|transfer|chain|contact|velocity|acceleration))\b")
# strict: a number with a unit; bare digits do not count (measured 2026-10-22: strict moved known mechanisms' median rank 16 -> 13
# and workflow/meta terms 7 -> 12 on 17 probe terms)
UNIT_RX = re.compile(r"\b\d+(?:\.\d+)?\s*(?:ms|fps|frames?|deg|°|px|%|hz|s|sec)\b", re.I)
META_STOP = ("peer-reviewed", "natural-language", "provider-specific", "first-class", "model-specific", "package-derived",
             "external-source", "implementation-relevant", "well-defined", "high-level", "low-level", "real-world", "open-source",
             "state-of-the-art", "non-exhaustive", "so-called", "self-contained", "one-to-one", "read-only")
CAUSAL_RELATIONS = ("requires", "depends_on", "conflicts_with")


def known_aliases(conn):
    out = set()
    for (al,) in conn.execute("SELECT aliases FROM concepts"):
        for a in json.loads(al or "[]"):
            out.add(a.lower())
    try:
        for (al,) in conn.execute("SELECT aliases FROM mem.agent_concepts"):
            for a in json.loads(al or "[]"):
                out.add(a.lower())
    except Exception:
        pass
    return out


def mine(conn, min_df=3, max_share=0.01, min_chapters=2, top=150):
    total = conn.execute("SELECT count(*) FROM handbook_passages WHERE kind != 'code'").fetchone()[0]
    chapter_of = dict(conn.execute("SELECT a.article_id, s.chapter_id FROM handbook_articles a JOIN handbook_sections s ON s.section_id = a.section_id").fetchall())
    causal_passages = set(r[0] for r in conn.execute("SELECT DISTINCT from_id FROM handbook_edges WHERE relation IN (%s)" % ",".join("'%s'" % r for r in CAUSAL_RELATIONS)))
    causal_clauses = [r[0].lower() for r in conn.execute("SELECT to_id FROM handbook_edges WHERE relation IN (%s)" % ",".join("'%s'" % r for r in CAUSAL_RELATIONS))]
    aliases = known_aliases(conn)
    df, chapters, unit_hits, label_hits, causal_hits, example = Counter(), defaultdict(set), Counter(), Counter(), Counter(), {}
    for pid, aid, text, ms, ss in conn.execute("SELECT passage_id, article_id, lower(text), moment_score, slot_score FROM handbook_passages WHERE kind != 'code'"):
        terms = set(TERM_RX.findall(text))
        if not terms:
            continue
        has_unit = bool(UNIT_RX.search(text))
        has_label = (ms or 0) >= 2 or (ss or 0) >= 2
        in_causal = pid in causal_passages
        for t in terms:
            df[t] += 1
            chapters[t].add(chapter_of.get(aid))
            if has_unit:
                unit_hits[t] += 1
            if has_label:
                label_hits[t] += 1
            if in_causal:
                causal_hits[t] += 1
            if t not in example or len(text) < len(example[t][1]):
                example[t] = (pid, text)
    rows = []
    for t, n in df.items():
        if not (min_df <= n <= max_share * total) or len(chapters[t]) < min_chapters or t in aliases or t in META_STOP:
            continue
        clause_hits = sum(1 for c in causal_clauses if t in c)
        unit_share, label_share = unit_hits[t] / float(n), label_hits[t] / float(n)
        causal = causal_hits[t] + clause_hits
        score = len(chapters[t]) * 0.5 + 3.0 * unit_share + 2.0 * label_share + 1.0 * min(causal, 5) + (0.5 if "-" in t else 0.0)
        rows.append(OrderedDict([("term", t), ("df", n), ("chapters", len(chapters[t])), ("unit_share", round(unit_share, 2)),
                                 ("label_share", round(label_share, 2)), ("causal", causal), ("clause_hits", clause_hits),
                                 ("score", round(score, 2)), ("example_id", example[t][0]), ("example", example[t][1][:90])]))
    rows.sort(key=lambda r: (-r["score"], -r["df"]))
    return OrderedDict([("mined_at", datetime.now(timezone.utc).isoformat()), ("passages", total), ("candidates", len(rows)),
                        ("rule", "hyphenated or '<word> <mechanism noun>' terms; df %d..%d%%; >= %d chapters; not an alias; META_STOP removed; "
                                 "score = 0.5*chapters + 3*unit_share + 2*label_share + min(causal,5) + 0.5 if hyphenated" % (min_df, int(max_share * 100), min_chapters)),
                        ("top", top), ("rows", rows)])


def load_marks(path=None):
    path = Path(path) if path else Path(BUNDLE_DIR) / "agent" / "data" / "mechanism_marks.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def write_review(result, conn, path=None, marks=None):
    from . import query as q
    path = Path(path) if path else Path(BUNDLE_DIR) / "docs" / "mechanism_candidates.md"
    marks = marks if marks is not None else load_marks()
    rows = result["rows"]
    lines = ["# Mechanism vocabulary candidates (for owner review)", "",
             "Mined %s from %d prose passages: %d candidates after filters; top %d listed, %d more omitted." % (
                 result["mined_at"][:10], result["passages"], result["candidates"], min(result["top"], len(rows)), max(0, len(rows) - result["top"])),
             "", "Rule: " + result["rule"], "",
             "unit = share of the term's passages carrying numbers or units (ms, fps, frames, deg, s, px, %, Hz); label = share with a moment/slot label ≥ 2; "
             "causal = passages with a requires/depends_on/conflicts_with edge + clauses containing the term.", "",
             ("Reviewed by %s. Accepted terms are concept aliases in agent memory and are linked in the index on rebuild." % marks["reviewed_by"]) if marks else
             "Mark **accept** with a kind (mechanism | technique | concept) or **reject**. Accepted terms become concept aliases (`concept-add … --kind mechanism`) and the index is rebuilt. Nothing here is in the index yet.", "",
             "| # | term | df | ch | unit | label | causal | example | accept | reject | kind |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    mk = (marks or {}).get("marks", {})
    kinds = {cid: v["kind"] for cid, v in (marks or {}).get("new_concepts", {}).items()}
    if marks:
        acc_lines = ["", "## Accepted (now concept aliases; excluded from the candidate table below because the miner skips known aliases)", "",
                     "| concept | kind | aliases |", "|---|---|---|"]
        for cid, v in marks.get("new_concepts", {}).items():
            acc_lines.append("| `%s` %s | %s | %s |" % (cid, v["label"], v["kind"], ", ".join(v["aliases"])))
        for cid, aliases in marks.get("alias_additions", {}).items():
            acc_lines.append("| `%s` | alias addition | %s |" % (cid, ", ".join(aliases)))
        acc_lines += ["", "## Remaining candidates (rejected unless marked)", ""]
        lines[-2:-2] = acc_lines
    for i, r in enumerate(rows[:result["top"]], 1):
        m = mk.get(r["term"])
        if m is None:
            acc, rej, kind = "", "", ""
        elif m["decision"] == "accept":
            acc, rej, kind = "→ %s" % m["target"], "", kinds.get(m["target"], "alias")
        else:
            acc, rej, kind = "", m["reason"] or "reject", ""
        lines.append("| %d | `%s` | %d | %d | %.2f | %.2f | %d | %s: %s | %s | %s | %s |" % (
            i, r["term"], r["df"], r["chapters"], r["unit_share"], r["label_share"], r["causal"], q.short_id(conn, r["example_id"]), r["example"].replace("|", "/")[:70], acc, rej, kind))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path
