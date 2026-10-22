"""Swanson A -> B <- C discovery over mechanism concepts, lexical only. Hypotheses, never edges, until resolved in the review queue."""
import math
import re
from collections import OrderedDict

from . import handbook as hb
from . import knowledge as kn

BRIDGE_KINDS = ("mechanism", "technique")
CURE_KINDS = ("paragraph", "list_item", "quote")
STOP = set("the a an and or of to in on for with by from as is are be that this it its into at not no only than then when while which who what over under between "
           "can may must should will would does do did has have had was were been being each per via one two three first second".split())
_TOK = re.compile(r"[a-z][a-z\-]{2,}")
RELATIONS = ("analogous_mechanism", "compensates_for", "extends", "refines", "contradicts", "restates", "unrelated")


def tokens(text):
    return set(w for w in _TOK.findall((text or "").lower()) if w not in STOP)


def _chapter_of(conn):
    return dict(conn.execute("SELECT a.article_id, s.chapter_id FROM handbook_articles a JOIN handbook_sections s ON s.section_id = a.section_id").fetchall())


def _concept_meta(conn):
    out = {}
    for cid, kind, aliases in conn.execute("SELECT concept_id, kind, aliases FROM concepts"):
        import json
        out[cid] = (kind, [a.lower() for a in json.loads(aliases or "[]")])
    return out


def bridges(conn, a_id, kinds=BRIDGE_KINDS, min_chars=80, cross_only=False, limit=20, per_concept=6):
    """Hypotheses [(score, b_concept, c_id, row, cross_chapter, a_alias, c_alias)] for source passage a_id."""
    a = hb.get_passage(conn, a_id)
    if a is None:
        return []
    N = conn.execute("SELECT count(*) FROM handbook_passages WHERE kind != 'code'").fetchone()[0]
    chapter = _chapter_of(conn)
    meta = _concept_meta(conn)
    technique_linked = set(r[0] for r in conn.execute(
        "SELECT DISTINCT cp.passage_id FROM concept_passages cp JOIN concepts c USING(concept_id) WHERE c.kind IN ('technique','mechanism','directive')"))
    a_tokens = tokens(a["text"])
    a_ch = chapter.get(a["article_id"])
    from . import query as q
    import json as _json
    out = []
    for cid, w_ab, matched in conn.execute("SELECT concept_id, weight, matched FROM concept_passages WHERE passage_id = ?", (a_id,)):
        kind, aliases = meta.get(cid, (None, []))
        if kind not in kinds:
            continue
        # the bridge must stand on a specific alias (same 2% cap retrieval uses): "ones" or "contact" are not mechanisms
        specific = set(al.lower() for al, _, _ in q.specific_aliases(conn, cid))
        a_hits = [m.lower() for m in _json.loads(matched or "[]")]
        if not any(m in specific for m in a_hits):
            continue
        alias_tokens = set(t for al in aliases for t in tokens(al))
        df = conn.execute("SELECT count(*) FROM concept_passages WHERE concept_id = ?", (cid,)).fetchone()[0]
        idf = math.log(N / max(df, 1))
        found = 0
        for c_id, w_bc, c_matched in conn.execute("SELECT passage_id, weight, matched FROM concept_passages WHERE concept_id = ? AND passage_id != ? ORDER BY weight DESC", (cid, a_id)):
            row = hb.get_passage(conn, c_id)
            if row is None or row["kind"] not in CURE_KINDS or row["chars"] < min_chars or row["article_id"] == a["article_id"]:
                continue
            if c_id not in technique_linked:
                continue
            shared = (a_tokens & tokens(row["text"])) - alias_tokens
            if shared:
                continue
            cross = chapter.get(row["article_id"]) != a_ch
            if cross_only and not cross:
                continue
            score = (min(w_ab, 3) / 3.0) * (min(w_bc, 3) / 3.0) * idf * (1.5 if cross else 1.0)
            out.append((round(score, 3), cid, c_id, row, cross, matched, c_matched))
            found += 1
            if found >= per_concept:
                break
    out.sort(key=lambda x: -x[0])
    return out[:limit]


def hypothesis_records(conn, a_id, hyps):
    from . import query as q
    recs = []
    for score, cid, c_id, row, cross, a_alias, c_alias in hyps:
        recs.append(OrderedDict([("a", q.short_id(conn, a_id)), ("a_id", a_id), ("b", cid), ("c", q.short_id(conn, c_id)), ("c_id", c_id),
                                 ("score", score), ("cross_chapter", cross), ("a_matched", a_alias), ("c_matched", c_alias),
                                 ("c_cite", hb.cite(row)), ("c_line", hb.excerpt(row, 150))]))
    return recs


def enqueue(mem, a_id, hyps, source="discover"):
    """Insert hypotheses into review_queue (pending); returns the number of new rows."""
    n = 0
    for score, cid, c_id, row, cross, a_alias, c_alias in hyps:
        cur = mem.execute("INSERT OR IGNORE INTO review_queue (kind, a_id, b_concept, c_id, score, evidence, status, created_at, source) VALUES (?,?,?,?,?,?,?,?,?)",
                          ("bridge", a_id, cid, c_id, score, "A matched %s; C matched %s; cross_chapter=%s" % (a_alias, c_alias, cross), "pending", kn.now(), source))
        n += cur.rowcount if cur.rowcount > 0 else 0
    mem.commit()
    return n


def resolve(mem, queue_id, relation, note="", resolved_by="agent"):
    if relation not in RELATIONS:
        raise ValueError("relation must be one of %s" % (RELATIONS,))
    row = mem.execute("SELECT kind, a_id, b_concept, c_id, evidence FROM review_queue WHERE id = ?", (queue_id,)).fetchone()
    if row is None:
        raise KeyError("no review_queue row %s" % queue_id)
    status = "rejected" if relation == "unrelated" else "accepted"
    mem.execute("UPDATE review_queue SET status = ?, relation = ?, note = ?, resolved_at = ?, resolved_by = ? WHERE id = ?",
                (status, relation, note, kn.now(), resolved_by, queue_id))
    if status == "accepted":
        evidence = "%s via concept %s; %s" % (note or "review", row[2], row[4])
        kn.add_link(mem, "passage", row[1], "passage", row[3], relation, evidence, resolved_by)
    mem.commit()
    return status


def pending(mem, limit=20):
    return [dict(r) for r in mem.execute("SELECT id, kind, a_id, b_concept, c_id, score, evidence, created_at FROM review_queue WHERE status = 'pending' ORDER BY score DESC LIMIT ?", (limit,))]
