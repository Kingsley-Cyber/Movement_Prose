"""Token-efficient queries over handbook_index.db (+ agent_memory.db attached as `mem`).

Every function returns compact records (ids, scores, a citation and one line of text); `read` expands on demand.
"""
import json
import sqlite3
from collections import OrderedDict

from . import handbook as hb
from . import knowledge as kn

NON_CODE = ("paragraph", "list_item", "table_row", "quote", "definition")


def open_all(db_path=hb.DEFAULT_DB, memory_path=kn.MEMORY_DB):
    conn = hb.connect(db_path)
    kn.attach_memory(conn, memory_path)
    return conn


def _conn_key(conn):
    """Cache key for a connection: the main database file and its mtime (ids of closed connections get reused)."""
    import os
    try:
        path = [r[2] for r in conn.execute("PRAGMA database_list") if r[1] == "main"][0]
        return (path, os.path.getmtime(path) if path and os.path.exists(path) else 0)
    except Exception:
        return ("memory", id(conn))


def _dupes(conn):
    key = ("dupes",) + _conn_key(conn)
    cache = getattr(_dupes, "cache", {})
    if key not in cache:
        cache[key] = set(r[0] for r in conn.execute("SELECT to_id FROM handbook_edges WHERE relation = 'same_text'"))
        _dupes.cache = cache
    return cache[key]


def _mem_rows(conn, sql, params=()):
    """Rows from the attached memory db, or [] when it is not attached."""
    try:
        return conn.execute(sql, params).fetchall()
    except sqlite3.OperationalError:
        return []


def summary_of(conn, kind, node_id):
    rows = _mem_rows(conn, "SELECT text FROM mem.agent_summaries WHERE node_kind = ? AND node_id = ? AND level = 'one_line'", (kind, node_id))
    if rows:
        return rows[0][0]
    row = conn.execute("SELECT text FROM summaries WHERE node_kind = ? AND node_id = ? AND level = 'one_line'", (kind, node_id)).fetchone()
    return row[0] if row else ""


def _hit(conn, row, score=None):
    return OrderedDict([("kind", "passage"), ("id", row["passage_id"]), ("score", score if score is not None else (row["moment_score"] or 0) + (row["slot_score"] or 0)),
                        ("m", "%s/%s" % (row["moment_type"] or "-", row["moment_score"] or 0)), ("s", "%s/%s" % (row["slot_id"] or "-", row["slot_score"] or 0)),
                        ("tier", row["intent_tier"]), ("pkind", row["kind"]), ("cite", hb.cite(row)), ("line", summary_of(conn, "passage", row["passage_id"]) or hb.excerpt(row))])


def lookup(conn, moment=None, slot=None, tier=None, text=None, min_score=1, limit=10, kinds=NON_CODE, dedupe=True):
    rows = hb.lookup(conn, moment, slot, tier, text, min_score, limit * 3 if dedupe else limit, kinds)
    dupes = _dupes(conn) if dedupe else set()
    out = [_hit(conn, r) for r in rows if r["passage_id"] not in dupes]
    return out[:limit]


def find(conn, text, limit=8, kinds=NON_CODE):
    """One call, three indexes: concepts, tags, passages (deduped)."""
    out = OrderedDict([("concepts", []), ("tags", []), ("passages", [])])
    phrase = text if any(ch in text for ch in '"*') else " ".join(text.split())
    try:
        rows = conn.execute("SELECT c.concept_id, c.label, c.kind FROM concept_fts JOIN concepts c ON c.concept_id = concept_fts.concept_id "
                            "WHERE concept_fts MATCH ? ORDER BY bm25(concept_fts) LIMIT 5", (phrase,)).fetchall()
    except sqlite3.OperationalError:
        rows = []  # malformed FTS query text
    for r in rows:
        out["concepts"].append(OrderedDict([("kind", "concept"), ("id", r[0]), ("label", r[1]), ("ckind", r[2])]))
    for r in _mem_rows(conn, "SELECT tag FROM mem.tag_fts WHERE tag_fts MATCH ? ORDER BY bm25(tag_fts) LIMIT 5", (phrase,)):
        out["tags"].append(OrderedDict([("kind", "tag"), ("id", r[0])]))
    out["passages"] = lookup(conn, text=phrase, limit=limit, kinds=kinds, min_score=0)
    return out


def read(conn, kind, node_id, max_chars=1500):
    if kind == "passage":
        row = hb.get_passage(conn, node_id)
        if not row:
            return None
        text = row["text"]
    elif kind == "block":
        rows = conn.execute("SELECT text FROM handbook_passages WHERE block_id = ? ORDER BY ordinal", (node_id,)).fetchall()
        if not rows:
            return None
        text = "\n".join(r[0] for r in rows)
    elif kind == "article":
        rows = conn.execute("SELECT heading_path, text FROM handbook_passages WHERE article_id = ? ORDER BY ordinal", (node_id,)).fetchall()
        if not rows:
            return None
        parts, last = [], None
        for hp, t in rows:
            if hp != last:
                parts.append("## " + hp if hp else "")
                last = hp
            parts.append(t)
        text = "\n".join(p for p in parts if p)
    else:
        return None
    truncated = len(text) > max_chars
    return OrderedDict([("kind", kind), ("id", node_id), ("chars", len(text)), ("truncated", truncated),
                        ("text", text if not truncated else text[:max_chars] + "\n… (+%d chars; raise --max-chars or read a block)" % (len(text) - max_chars))])


def outline(conn, kind=None, node_id=None):
    if kind is None:
        return [OrderedDict([("kind", "chapter"), ("id", r[0]), ("line", summary_of(conn, "chapter", r[0]))])
                for r in conn.execute("SELECT chapter_id FROM handbook_chapters ORDER BY ordinal")]
    if kind == "chapter":
        return [OrderedDict([("kind", "section"), ("id", r[0]), ("line", summary_of(conn, "section", r[0]))])
                for r in conn.execute("SELECT section_id FROM handbook_sections WHERE chapter_id = ? ORDER BY ordinal", (node_id,))]
    if kind == "section":
        return [OrderedDict([("kind", "article"), ("id", r[0]), ("src", r[1]), ("cpcs_id", r[2]), ("akind", r[3]), ("epistemic", r[4]), ("words", r[5]), ("line", summary_of(conn, "article", r[0]))])
                for r in conn.execute("SELECT article_id, src, cpcs_id, kind, epistemic, words FROM handbook_articles WHERE section_id = ? ORDER BY ordinal", (node_id,))]
    if kind == "article":
        return [OrderedDict([("kind", "block"), ("id", r[0]), ("title", r[1]), ("passages", r[2]), ("chars", r[3]), ("line", summary_of(conn, "block", r[0]))])
                for r in conn.execute("SELECT block_id, title, passage_count, chars FROM handbook_blocks WHERE article_id = ? ORDER BY ordinal", (node_id,))]
    if kind == "block":
        return [OrderedDict([("kind", "passage"), ("id", r[0]), ("pkind", r[1]), ("chars", r[2]), ("line", summary_of(conn, "passage", r[0]))])
                for r in conn.execute("SELECT passage_id, kind, chars FROM handbook_passages WHERE block_id = ? ORDER BY ordinal", (node_id,))]
    if kind == "passage":
        return [hb.lineage(conn, node_id)]
    return []


def concept(conn, concept_id, limit=8):
    row = conn.execute("SELECT * FROM concepts WHERE concept_id = ?", (concept_id,)).fetchone()
    if not row:
        rows = _mem_rows(conn, "SELECT concept_id, label, kind, aliases, description, 'agent' AS source FROM mem.agent_concepts WHERE concept_id = ?", (concept_id,))
        row = rows[0] if rows else None
    if not row:
        return None
    out = OrderedDict([("id", row["concept_id"]), ("label", row["label"]), ("kind", row["kind"]), ("aliases", json.loads(row["aliases"] or "[]")),
                       ("description", row["description"] or ""), ("source", row["source"])])
    dupes = _dupes(conn)
    out["passages"] = []
    for r in conn.execute("SELECT passage_id, weight, matched FROM concept_passages WHERE concept_id = ? ORDER BY weight DESC LIMIT ?", (concept_id, limit * 3)):
        if r[0] in dupes:
            continue
        p = hb.get_passage(conn, r[0])
        if p:
            h = _hit(conn, p, score=r[1])
            h["matched"] = json.loads(r[2] or "[]")
            out["passages"].append(h)
        if len(out["passages"]) >= limit:
            break
    rel = []
    for r in conn.execute("SELECT to_concept AS other, relation, weight FROM concept_edges WHERE from_concept = ? UNION ALL "
                          "SELECT from_concept, relation, weight FROM concept_edges WHERE to_concept = ? ORDER BY weight DESC LIMIT ?", (concept_id, concept_id, limit * 2)):
        rel.append(OrderedDict([("id", r[0]), ("relation", r[1]), ("weight", r[2])]))
    out["related"] = rel
    out["directives"] = [OrderedDict([("id", r[0]), ("relation", r[1])]) for r in conn.execute("SELECT directive_id, relation FROM concept_directives WHERE concept_id = ?", (concept_id,))]
    out["tags"] = [r[0] for r in _mem_rows(conn, "SELECT tag FROM mem.node_tags WHERE node_kind = 'concept' AND node_id = ?", (concept_id,))]
    out["used_with"] = kn.used_with(conn, "concept", concept_id) if _has_mem(conn) else []
    out["agent_links"] = [dict(r) for r in _mem_rows(conn, "SELECT to_kind, to_id, relation, note FROM mem.agent_links WHERE from_kind = 'concept' AND from_id = ?", (concept_id,))]
    return out


def _has_mem(conn):
    try:
        conn.execute("SELECT 1 FROM mem.usage_events LIMIT 1")
        return True
    except Exception:
        return False


def near(conn, passage_id):
    p = hb.get_passage(conn, passage_id)
    if not p:
        return None
    out = OrderedDict([("id", passage_id), ("cite", hb.cite(p)), ("line", summary_of(conn, "passage", passage_id)), ("block", None)])
    out["block"] = conn.execute("SELECT block_id FROM handbook_passages WHERE passage_id = ?", (passage_id,)).fetchone()[0]
    out.update(hb.neighbors(conn, passage_id))
    out["same_text"] = [r[0] for r in conn.execute("SELECT to_id FROM handbook_edges WHERE from_id = ? AND relation = 'same_text' UNION SELECT from_id FROM handbook_edges WHERE to_id = ? AND relation = 'same_text'", (passage_id, passage_id))]
    out["concepts"] = [OrderedDict([("id", r[0]), ("weight", r[1])]) for r in conn.execute("SELECT concept_id, weight FROM concept_passages WHERE passage_id = ? ORDER BY weight DESC", (passage_id,))]
    out["cites"] = [OrderedDict([("to", r[0]), ("relation", r[1])]) for r in conn.execute("SELECT to_id, relation FROM handbook_edges WHERE from_id = ? AND relation IN ('cites_card','cites_source','links_to','requires','depends_on','conflicts_with')", (passage_id,))]
    out["tags"] = [r[0] for r in _mem_rows(conn, "SELECT tag FROM mem.node_tags WHERE node_kind = 'passage' AND node_id = ?", (passage_id,))]
    out["used_with"] = kn.used_with(conn, "passage", passage_id) if _has_mem(conn) else []
    return out


def walk(conn, slot, start="anticipation", per_moment=3, min_score=2):
    out = OrderedDict()
    for moment, rows in hb.phase_walk(conn, slot, start, per_moment * 3, min_score).items():
        dupes = _dupes(conn)
        out[moment] = [_hit(conn, r) for r in rows if r["passage_id"] not in dupes][:per_moment]
    return out


def deps(conn, directive_id):
    chain = hb.dependency_chain(conn, directive_id)
    for item in chain:
        if item.get("passage_id"):
            item["line"] = summary_of(conn, "passage", item["passage_id"])
    return chain


def tagged(conn, tag, limit=20):
    tag = tag.strip().lower().replace(" ", "_")
    return [dict(r) for r in _mem_rows(conn, "SELECT node_kind, node_id, weight, note FROM mem.node_tags WHERE tag = ? ORDER BY weight DESC LIMIT ?", (tag, limit))]


def format_hits(hits):
    lines = []
    for h in hits:
        if h.get("kind") == "passage":
            lines.append("%-5s %s  %s  %s\n      %s" % (str(h.get("score")), h.get("m"), h.get("s"), h["id"], h.get("line", "")))
        elif h.get("kind") == "concept":
            lines.append("concept %s  %s [%s]" % (h["id"], h.get("label", ""), h.get("ckind", "")))
        elif h.get("kind") == "tag":
            lines.append("tag %s" % h["id"])
        else:
            lines.append("%s %s  %s" % (h.get("kind"), h.get("id"), h.get("line", "")))
    return "\n".join(lines)


# =====================================================================================================
# Slice 1 (2026-10-21): FTS quoting, alias expansion with specificity, diversity with roll-up counts,
# matched terms + snippet, character budget, short display ids. No schema change.
# =====================================================================================================
import re as _re
import math as _math

# a deliberate FTS expression carries quotes, a prefix star or an uppercase boolean; parentheses in prose are not operators
FTS_OPS = _re.compile(r'["*]|\bOR\b|\bAND\b|\bNOT\b|\bNEAR\b')
_WORD = _re.compile(r"[A-Za-z0-9][A-Za-z0-9\-']*")
ALIAS_MAX_SHARE = 0.02      # an alias matching more than 2% of passages is too broad to expand through
MAX_CONCEPTS = 2
MAX_QUERY_WORDS = 24        # a long prose request contributes its first 24 distinct words of 4+ letters


def fts_phrase(text):
    return '"' + text.replace('"', '""') + '"'


def fts_query(text):
    """User text -> FTS5 expression. Operators pass through; plain text becomes phrase OR all-words, each word quoted
    so hyphens and other punctuation never reach the parser."""
    text = (text or "").strip()
    if not text:
        return '""'
    if FTS_OPS.search(text):
        return text
    words = _WORD.findall(text)
    if not words:
        return fts_phrase(text)
    if len(words) == 1:
        return fts_phrase(words[0])
    if len(words) > MAX_QUERY_WORDS:
        seen, kept = set(), []
        for w in words:
            lw = w.lower()
            if len(lw) >= 4 and lw not in seen:
                seen.add(lw)
                kept.append(w)
            if len(kept) >= MAX_QUERY_WORDS:
                break
        return " AND ".join(fts_phrase(w) for w in kept) if kept else fts_phrase(" ".join(words[:MAX_QUERY_WORDS]))
    return "(%s) OR (%s)" % (fts_phrase(" ".join(words)), " AND ".join(fts_phrase(w) for w in words))


def _passage_total(conn):
    cache = getattr(_passage_total, "cache", {})
    key = _conn_key(conn)
    if key not in cache:
        cache[key] = conn.execute("SELECT count(*) FROM handbook_passages").fetchone()[0]
        _passage_total.cache = cache
    return cache[key]


def alias_df(conn, alias):
    cache = getattr(alias_df, "cache", {})
    key = (_conn_key(conn), alias.lower())
    if key not in cache:
        try:
            cache[key] = conn.execute("SELECT count(*) FROM handbook_fts WHERE handbook_fts MATCH ?", (fts_phrase(alias),)).fetchone()[0]
        except sqlite3.OperationalError:
            cache[key] = 0
        alias_df.cache = cache
    return cache[key]


def specific_aliases(conn, concept_id, max_share=ALIAS_MAX_SHARE):
    """[(alias, df, weight)] for aliases that occur and are not too broad; weight falls with document frequency."""
    row = conn.execute("SELECT aliases FROM concepts WHERE concept_id = ?", (concept_id,)).fetchone()
    aliases = json.loads(row[0]) if row else []
    for r in _mem_rows(conn, "SELECT aliases FROM mem.agent_concepts WHERE concept_id = ?", (concept_id,)):
        aliases += json.loads(r[0] or "[]")
    total = _passage_total(conn)
    out = []
    for a in aliases:
        if len(a) < 3:
            continue
        n = alias_df(conn, a)
        if 0 < n <= max_share * total:
            out.append((a, n, round(1.0 / (1.0 + _math.log(1 + n)), 3)))
    return out


def resolve_concepts(conn, text, max_concepts=MAX_CONCEPTS):
    """Concepts the text names: exact alias containment first, then the concept FTS. [(concept_id, label, how)]"""
    low = " " + " ".join(_WORD.findall((text or "").lower())) + " "
    found = []
    rows = conn.execute("SELECT concept_id, label, aliases FROM concepts").fetchall() + \
        [(r[0], r[1], r[2]) for r in _mem_rows(conn, "SELECT concept_id, label, aliases FROM mem.agent_concepts")]
    seen_ids = set()
    for cid, label, aliases in rows:
        if cid in seen_ids:
            continue
        for a in json.loads(aliases or "[]"):
            a_norm = " " + " ".join(_WORD.findall(a.lower())) + " "
            if len(a_norm.strip()) >= 3 and a_norm in low:
                found.append((cid, label, "alias:" + a))
                seen_ids.add(cid)
                break
    if len(found) < max_concepts:
        try:
            for r in conn.execute("SELECT c.concept_id, c.label FROM concept_fts JOIN concepts c ON c.concept_id = concept_fts.concept_id "
                                  "WHERE concept_fts MATCH ? ORDER BY bm25(concept_fts) LIMIT ?", (fts_query(text), max_concepts * 2)):
                if r[0] not in [f[0] for f in found]:
                    found.append((r[0], r[1], "fts"))
        except sqlite3.OperationalError:
            pass
    return found[:max_concepts]


def expand_query(conn, text, max_concepts=MAX_CONCEPTS):
    """-> (fts_expression, [(concept_id, [(alias, df, weight)])]). Plain text plus the specific aliases of the concepts it names."""
    concepts = []
    parts = [fts_query(text)]
    for cid, label, how in resolve_concepts(conn, text, max_concepts):
        spec = specific_aliases(conn, cid)
        concepts.append((cid, spec))
        parts += [fts_phrase(a) for a, _, _ in spec]
    seen, uniq = set(), []
    for p in parts:
        if p not in seen:
            seen.add(p)
            uniq.append(p)
    return " OR ".join("(%s)" % p if " " in p and not p.startswith('"') else p for p in uniq), concepts


def _via(text, query, concepts):
    low = (text or "").lower()
    for cid, spec in concepts:
        for a, _, _ in sorted(spec, key=lambda x: -len(x[0])):
            if a.lower() in low:
                return "%s:%s" % (cid, a)
    words = [w.lower() for w in _WORD.findall(query or "")]
    if words and all(w in low for w in words):
        return "query"
    return "query~"


# --- short display ids ---------------------------------------------------------------------------
_SHORT = _re.compile(r"^a(\d{3})(#\d{4}|/b\d{3})?$")


def _article_maps(conn):
    cache = getattr(_article_maps, "cache", {})
    key = _conn_key(conn)
    if key not in cache:
        rows = conn.execute("SELECT article_id, ordinal FROM handbook_articles").fetchall()
        cache[key] = (dict((a, o) for a, o in rows), dict((o, a) for a, o in rows))
        _article_maps.cache = cache
    return cache[key]


def short_id(conn, node_id):
    """'src-…#0980' -> 'a017#0980'; 'src-…/b051' -> 'a017/b051'; unknown ids unchanged."""
    by_article, _ = _article_maps(conn)
    for sep in ("#", "/"):
        if sep in node_id:
            art, rest = node_id.split(sep, 1)
            if art in by_article:
                return "a%03d%s%s" % (by_article[art], sep, rest)
    if node_id in by_article:
        return "a%03d" % by_article[node_id]
    return node_id


def resolve_id(conn, node_id):
    """Accept a short id or a canonical id; return the canonical id (or the input unchanged)."""
    m = _SHORT.match(node_id or "")
    if not m:
        return node_id
    _, by_ordinal = _article_maps(conn)
    art = by_ordinal.get(int(m.group(1)))
    if art is None:
        return node_id
    return art + (m.group(2) or "")


# --- hits ----------------------------------------------------------------------------------------
def _hit2(conn, row, query=None, concepts=()):
    h = _hit(conn, row)
    h["sid"] = short_id(conn, row["passage_id"])
    terms = []
    for col in ("moment_terms", "slot_terms"):
        try:
            terms += json.loads(row.get(col) or "[]")
        except Exception:
            pass
    h["terms"] = terms
    if row.get("snip"):
        h["snip"] = _WS_RE.sub(" ", row["snip"]).strip()
    if query is not None:
        h["via"] = _via(row.get("text"), query, concepts)
    return h


_WS_RE = _re.compile(r"\s+")


def diversify(hits, per_block=1, per_article=2):
    """Keep order; cap hits per block and per article; attach roll-up counts to the kept hit of that block/article."""
    kept, nb, na, first_b, first_a = [], {}, {}, {}, {}
    for h in hits:
        b, a = h.get("block"), h.get("article")
        if b is not None and nb.get(b, 0) >= per_block:
            first_b[b]["more_in_block"] = first_b[b].get("more_in_block", 0) + 1
            continue
        if a is not None and na.get(a, 0) >= per_article:
            first_a[a]["more_in_article"] = first_a[a].get("more_in_article", 0) + 1
            continue
        nb[b] = nb.get(b, 0) + 1
        na[a] = na.get(a, 0) + 1
        first_b.setdefault(b, h)
        first_a.setdefault(a, h)
        kept.append(h)
    return kept


def lookup2(conn, moment=None, slot=None, tier=None, text=None, min_score=1, limit=10, kinds=NON_CODE, dedupe=True,
            expand=True, diverse=True, per_block=1, per_article=None, rerank=None, spread=0.5, per_concept=None):
    """Slice-1 lookup plus the gated flags (see lookup3); kept as the single entry point for callers."""
    return lookup3(conn, moment, slot, tier, text, min_score, limit, kinds, dedupe, expand, diverse, per_block, per_article, rerank, spread, per_concept)


def _lookup2_slice1(conn, moment=None, slot=None, tier=None, text=None, min_score=1, limit=10, kinds=NON_CODE, dedupe=True,
                    expand=True, diverse=True, per_block=1, per_article=2):
    """The Slice-1 behaviour, kept for comparison."""
    concepts = []
    expr = None
    if text:
        expr, concepts = expand_query(conn, text) if expand else (fts_query(text), [])
    fetch = limit * (4 if (dedupe or diverse) else 1)
    rows = hb.lookup(conn, moment, slot, tier, expr, min_score, fetch, kinds)
    dupes = _dupes(conn) if dedupe else set()
    hits = []
    for r in rows:
        if r["passage_id"] in dupes:
            continue
        r["block"] = conn.execute("SELECT block_id FROM handbook_passages WHERE passage_id = ?", (r["passage_id"],)).fetchone()[0]
        h = _hit2(conn, r, text, concepts)
        h["block"] = r["block"]
        h["article"] = r["article_id"]
        hits.append(h)
    if text and flags.get("allocator") and hits:
        chosen, footer = allocate(hits, concepts, limit, spread=spread, per_concept=per_concept, edges=passage_edges(conn, [h["id"] for h in hits]))
        if chosen:
            chosen[0]["coverage_footer"] = footer
        return chosen, concepts
    if diverse:
        hits = diversify(hits, per_block, per_article)
    return hits[:limit], concepts


def find2(conn, text, limit=8, kinds=NON_CODE, expand=True, diverse=True, spread=0.5, per_concept=None):
    out = OrderedDict([("query", text), ("concepts", []), ("tags", []), ("passages", [])])
    hits, concepts = lookup2(conn, text=text, limit=limit, kinds=kinds, min_score=0, expand=expand, diverse=diverse, spread=spread, per_concept=per_concept)
    for cid, spec in concepts:
        row = conn.execute("SELECT label, kind FROM concepts WHERE concept_id = ?", (cid,)).fetchone()
        out["concepts"].append(OrderedDict([("kind", "concept"), ("id", cid), ("label", row[0] if row else cid), ("ckind", row[1] if row else "agent"),
                                            ("aliases_used", [a for a, _, _ in spec])]))
    for r in _mem_rows(conn, "SELECT tag FROM mem.tag_fts WHERE tag_fts MATCH ? ORDER BY bm25(tag_fts) LIMIT 5", (fts_query(text),)):
        out["tags"].append(OrderedDict([("kind", "tag"), ("id", r[0])]))
    out["passages"] = hits
    return out


def format_hits2(hits, budget=None, show_cite=False):
    """Compact lines: sid score m s via (+N in block) / snippet-or-line. Budget trims trailing hits, then the line."""
    lines = []
    for h in hits:
        head = "%-10s %-5s %-18s %-24s" % (h.get("sid", h["id"]), str(h.get("score")), h.get("m", ""), h.get("s", ""))
        if h.get("via"):
            head += " via %s" % h["via"]
        if h.get("nuance"):
            head += "  nuance %s" % h["nuance"]
        extras = []
        if h.get("more_in_block"):
            extras.append("+%d in block %s" % (h["more_in_block"], short_id_block(h)))
        if h.get("more_in_article"):
            extras.append("+%d in article" % h["more_in_article"])
        if extras:
            head += "  (" + "; ".join(extras) + ")"
        body = h.get("snip") or h.get("line", "")
        if h.get("terms"):
            body += "  [%s]" % ", ".join(h["terms"][:6])
        block = head + "\n      " + body + ("\n      " + h["cite"] if show_cite else "")
        lines.append(block)
    footer = hits[0].get("coverage_footer") if hits else None
    if footer:
        lines.append("coverage: " + "; ".join("%s %d/%d (%d articles)" % (g, v["shown"], v["candidates"], v["articles"]) for g, v in footer.items()))
    if budget:
        out, used = [], 0
        for block in lines:
            if used + len(block) + 1 > budget:
                if not out and block:
                    out.append(block[: max(0, budget - 1)])
                break
            out.append(block)
            used += len(block) + 1
        lines = out
    return "\n".join(lines)


def short_id_block(h):
    b = h.get("block") or ""
    sid = h.get("sid") or ""
    if "#" in sid and "/" in b:
        return sid.split("#")[0] + "/" + b.split("/", 1)[1]
    return b


# =====================================================================================================
# Rank 5 (2026-10-21): `ask` — one call from a plain request to moments, slots, concepts, hits, directives and gaps.
# =====================================================================================================
def label_scores(text):
    """All moment and slot labels with their term-hit counts and matched terms, best first."""
    out = {"moments": [], "slots": []}
    for key, table in (("moments", hb._MOMENT_RX), ("slots", hb._SLOT_RX)):
        for label, rxs in table.items():
            hits = [t for t, rx in rxs if rx.search(text)]
            if hits:
                out[key].append((label, len(hits), hits))
        out[key].sort(key=lambda x: (-x[1], x[0]))
    return out


def ask(conn, request, catalog=None, policy=None, tastes=None, taste_text=None, limit_per=3, kinds=NON_CODE, max_concepts=4, discover=0):
    from .propose import lexical_gaps
    labels = label_scores(request)
    concepts = resolve_concepts(conn, request, max_concepts=max_concepts)
    seen, groups = set(), []

    def take(name, hits, note=""):
        fresh = [h for h in hits if h["id"] not in seen]
        for h in fresh:
            seen.add(h["id"])
        groups.append(OrderedDict([("name", name), ("note", note), ("hits", fresh[:limit_per])]))

    # 1. the request itself, no expansion (what the words say)
    direct, _ = lookup2(conn, text=request, limit=limit_per, min_score=0, kinds=kinds, expand=False)
    take("direct", direct, "FTS on the request words")
    # 2. each named concept through its specific aliases
    concept_rows = []
    for cid, label, how in concepts:
        spec = specific_aliases(conn, cid)
        if not spec:
            concept_rows.append(OrderedDict([("id", cid), ("label", label), ("how", how), ("aliases_used", [])]))
            continue
        expr = " OR ".join(fts_phrase(a) for a, _, _ in spec)
        rows = hb.lookup(conn, text=expr, min_score=0, limit=limit_per * 4, kinds=kinds)
        dupes = _dupes(conn)
        hits = []
        for r in rows:
            if r["passage_id"] in dupes:
                continue
            r["block"] = conn.execute("SELECT block_id FROM handbook_passages WHERE passage_id = ?", (r["passage_id"],)).fetchone()[0]
            h = _hit2(conn, r, request, [(cid, spec)])
            h["block"], h["article"] = r["block"], r["article_id"]
            hits.append(h)
        take("concept:" + cid, diversify(hits), "%s (%s)" % (label, how))
        concept_rows.append(OrderedDict([("id", cid), ("label", label), ("how", how), ("aliases_used", [a for a, _, _ in spec])]))
    # 3. the best moment x slot pairing by labels
    if labels["moments"] and labels["slots"]:
        m, s = labels["moments"][0][0], labels["slots"][0][0]
        hits, _ = lookup2(conn, moment=m, slot=s, min_score=2, limit=limit_per, kinds=kinds)
        take("labels:%s x %s" % (m, s), hits, "passages labelled with the request's top moment and slot")
    # 4. directives: implemented_by for the resolved concepts, plus id-token overlap with the request
    directives = []
    if catalog is not None:
        words = set(w.lower() for w in _WORD.findall(request) if len(w) > 3)
        for cid, label, how in concepts:
            for r in conn.execute("SELECT directive_id, relation FROM concept_directives WHERE concept_id = ? AND relation = 'implemented_by'", (cid,)):
                directives.append(OrderedDict([("id", r[0]), ("why", "implements " + cid)]))
            if cid.startswith("directive:"):
                directives.append(OrderedDict([("id", cid.split(":", 1)[1]), ("why", how)]))
        for d in catalog.rows():
            toks = set(d.directive_id.replace("aa_", "").split("_"))
            if len(words & toks) >= 2 and d.directive_id not in [x["id"] for x in directives]:
                directives.append(OrderedDict([("id", d.directive_id), ("why", "id words: " + ", ".join(sorted(words & toks)))]))
        if policy is not None:
            for x in directives:
                try:
                    d = catalog.get(x["id"])
                    x["priority"] = "locked" if policy.is_locked(d.directive_id) else policy.default_priority(d)
                    x["budget_class"] = policy.budget_class(d.directive_id)
                except Exception:
                    pass
    # 4b. serendipity: Swanson bridges from the best direct hit, outside the normal groups
    if discover and (direct or any(g["hits"] for g in groups)):
        from . import discover as disc
        seed = (direct or [h for g in groups for h in g["hits"]])[0]["id"]
        hyps = disc.bridges(conn, seed, limit=discover * 3)
        bridge_hits = []
        for rec in disc.hypothesis_records(conn, seed, hyps):
            if rec["c_id"] in seen:
                continue
            seen.add(rec["c_id"])
            bridge_hits.append(OrderedDict([("kind", "passage"), ("id", rec["c_id"]), ("sid", rec["c"]), ("score", rec["score"]), ("m", "bridge"),
                                            ("s", rec["b"]), ("via", "A %s -> %s <- C" % (rec["a"], rec["b"])), ("cite", rec["c_cite"]), ("line", rec["c_line"])]))
            if len(bridge_hits) >= discover:
                break
        groups.append(OrderedDict([("name", "bridges"), ("note", "Swanson A->B<-C from %s; hypotheses, not facts" % q_short(conn, seed)), ("hits", bridge_hits)]))
    # 5. gaps: words no handbook passage mentions; words no catalog row mentions
    hb_gaps = [w for w in sorted(set(w.lower() for w in _WORD.findall(request) if len(w) > 3)) if alias_df(conn, w) == 0]
    cat_gaps = lexical_gaps(request, catalog) if catalog is not None else []
    taste = None
    if tastes and taste_text:
        from . import taste as taste_mod
        taste = taste_mod.best(taste_text, tastes)
    return OrderedDict([("request", request), ("taste", taste),
                        ("moments", [OrderedDict([("label", l), ("score", n), ("terms", t)]) for l, n, t in labels["moments"][:3]]),
                        ("slots", [OrderedDict([("label", l), ("score", n), ("terms", t)]) for l, n, t in labels["slots"][:3]]),
                        ("concepts", concept_rows), ("groups", groups), ("directives", directives),
                        ("gaps", OrderedDict([("handbook", hb_gaps), ("catalog", cat_gaps)]))])


def format_ask(res, budget=1500, show_cite=False):
    head = ["ask: %s" % res["request"]]
    if res.get("taste"):
        head.append("taste: %s" % res["taste"])
    head.append("moments: " + (", ".join("%s(%d)" % (m["label"], m["score"]) for m in res["moments"]) or "-")
                + "   slots: " + (", ".join("%s(%d)" % (s["label"], s["score"]) for s in res["slots"]) or "-"))
    head.append("concepts: " + (", ".join("%s[%s]" % (c["id"], c["how"]) for c in res["concepts"]) or "-"))
    if res["directives"]:
        head.append("directives: " + ", ".join("%s(%s)" % (d["id"], d.get("priority", d["why"])) for d in res["directives"][:8]))
    gaps = res["gaps"]
    if gaps["handbook"] or gaps["catalog"]:
        head.append("gaps: handbook has no text for [%s]; catalog has no row for [%s]" % (", ".join(gaps["handbook"]), ", ".join(gaps["catalog"])))
    text = "\n".join(head)
    groups = [g for g in res["groups"] if g["hits"]]
    remaining = max(0, (budget or 10 ** 9) - len(text) - 2)
    share = remaining // max(1, len(groups)) if budget else None
    for g in groups:
        body = format_hits2(g["hits"], budget=share, show_cite=show_cite)
        if body:
            text += "\n== %s  %s\n%s" % (g["name"], g["note"], body)
    return text


# =====================================================================================================
# Slice 3c (2026-10-21): static rerank + Sbase fixes behind flags, gated by the benchmark (agent/data/rerank.json).
# =====================================================================================================
from pathlib import Path
from . import DATA_DIR as _DATA_DIR

RERANK_PATH = Path(_DATA_DIR) / "rerank.json"
RERANK_FLAGS = ("any_word_fallback", "per_article_3", "no_article_cap", "per_block_2", "judged_labels", "allocator", "kind_weight", "multi_alias_bonus", "length_floor", "epistemic_weight", "label_agreement")
KIND_WEIGHT = {"paragraph": 1.0, "list_item": 0.95, "quote": 0.95, "definition": 0.95, "table_row": 0.85, "code": 0.7}
LOW_VALUE_KINDS = ("deep_research_prompt", "specimen", "schema_draft")


def load_rerank(path=RERANK_PATH):
    try:
        doc = json.loads(Path(path).read_text(encoding="utf-8"))
        return dict((k, bool(doc.get("flags", {}).get(k, False))) for k in RERANK_FLAGS)
    except Exception:
        return dict((k, False) for k in RERANK_FLAGS)


def any_word_query(text):
    words, seen = [], set()
    for w in _WORD.findall(text or ""):
        if len(w) > 2 and w.lower() not in seen:
            seen.add(w.lower())
            words.append(w)
        if len(words) >= MAX_QUERY_WORDS * 2:
            break
    return " OR ".join(fts_phrase(w) for w in words) if words else fts_query(text)


def rerank_rows(rows, flags, concepts=(), query=None):
    """rows: dicts from hb.lookup with 'bm' (bm25, lower is better). Returns rows sorted by the adjusted score, with 'sbase'."""
    if not rows:
        return rows
    bms = [r.get("bm") for r in rows if r.get("bm") is not None]
    if not bms:
        return rows
    lo, hi = min(bms), max(bms)
    phase_concepts = set(c for c, _ in concepts if c in hb.MOMENT_ORDER)
    top_slot = None
    if flags.get("label_agreement") and query:
        ls = label_scores(query)["slots"]
        top_slot = ls[0][0] if ls else None
    for r in rows:
        bm = r.get("bm")
        base = 1.0 if hi == lo else (hi - bm) / (hi - lo)
        base = 0.5 + 0.5 * base                      # rank-relative, never zero
        if flags.get("kind_weight"):
            base *= KIND_WEIGHT.get(r.get("kind"), 0.9)
        if flags.get("multi_alias_bonus") and concepts:
            low = (r.get("text") or "").lower()
            n = sum(1 for _, spec in concepts for a, _, _ in spec if a.lower() in low)
            base *= 1.0 + min(0.3, 0.1 * max(0, n - 1))
        if flags.get("length_floor") and (r.get("chars") or 0) < 40:
            base *= 0.7
        if flags.get("epistemic_weight"):
            if (r.get("epistemic") or "") == "SOURCE_EVIDENCE":
                base *= 1.1
            if (r.get("article_kind") or "") in LOW_VALUE_KINDS:
                base *= 0.8
        if flags.get("label_agreement"):
            if phase_concepts and r.get("moment_type") in phase_concepts:
                base *= 1.1
            if top_slot and r.get("slot_id") == top_slot:
                base *= 1.05
        r["sbase"] = round(base, 4)
    rows.sort(key=lambda r: (-r.get("sbase", 0.0), r.get("chars") or 0))
    return rows


def lookup3(conn, moment=None, slot=None, tier=None, text=None, min_score=1, limit=10, kinds=NON_CODE, dedupe=True,
            expand=True, diverse=True, per_block=1, per_article=None, rerank=None, spread=0.5, per_concept=None):
    """lookup2 plus the Slice-3c flags. rerank: None (defaults from rerank.json), False (all off), True (all on) or a dict."""
    if rerank is None:
        flags = load_rerank()
    elif rerank is True:
        flags = dict((k, True) for k in RERANK_FLAGS)
    elif rerank is False:
        flags = dict((k, False) for k in RERANK_FLAGS)
    else:
        flags = dict((k, bool(rerank.get(k, False))) for k in RERANK_FLAGS)
    if per_article is None:
        per_article = 10 ** 6 if flags.get("no_article_cap") else (3 if flags.get("per_article_3") else 2)
    if flags.get("per_block_2") and per_block == 1:
        per_block = 2
    concepts, expr = [], None
    if text:
        expr, concepts = expand_query(conn, text) if expand else (fts_query(text), [])
    fetch = limit * (4 if (dedupe or diverse) else 1)
    rows = hb.lookup(conn, moment, slot, tier, expr, min_score, fetch, kinds)
    if flags.get("judged_labels") and not text and (moment or slot):
        judged = judged_rows(conn, moment, slot, kinds)
        jid = set(j["passage_id"] for j in judged)
        denied = judged_none(conn, moment, slot)
        rows = judged + [r for r in rows if r["passage_id"] not in jid and r["passage_id"] not in denied]
    if text and flags.get("any_word_fallback") and len(rows) < fetch:
        seen = set(r["passage_id"] for r in rows)
        extra = hb.lookup(conn, moment, slot, tier, any_word_query(text), min_score, fetch, kinds)
        for r in extra:
            if r["passage_id"] not in seen:
                r["fallback"] = True
                rows.append(r)
                seen.add(r["passage_id"])
    if text and any(flags.get(k) for k in ("kind_weight", "multi_alias_bonus", "length_floor", "epistemic_weight", "label_agreement")):
        primary = [r for r in rows if not r.get("fallback")]
        fallback = [r for r in rows if r.get("fallback")]
        rows = rerank_rows(primary, flags, concepts, text) + rerank_rows(fallback, flags, concepts, text)
    dupes = _dupes(conn) if dedupe else set()
    hits = []
    for r in rows:
        if r["passage_id"] in dupes:
            continue
        r["block"] = conn.execute("SELECT block_id FROM handbook_passages WHERE passage_id = ?", (r["passage_id"],)).fetchone()[0]
        h = _hit2(conn, r, text, concepts)
        h["block"], h["article"] = r["block"], r["article_id"]
        if r.get("sbase") is not None:
            h["sbase"] = r["sbase"]
        if flags.get("judged_labels"):
            j = kn.get_label(conn, r["passage_id"], attached=True)
            if j:
                h["judged"] = j
                if j.get("moment_type"):
                    h["m"] = "%s*" % j["moment_type"]
                if j.get("slot_id"):
                    h["s"] = "%s*" % j["slot_id"]
        if r.get("fallback"):
            h["via"] = (h.get("via") or "") + " (any-word)"
        hits.append(h)
    if text and flags.get("allocator") and hits:
        chosen, footer = allocate(hits, concepts, limit, spread=spread, per_concept=per_concept, edges=passage_edges(conn, [h["id"] for h in hits]))
        if chosen:
            chosen[0]["coverage_footer"] = footer
        return chosen, concepts
    if diverse:
        hits = diversify(hits, per_block, per_article)
    return hits[:limit], concepts


def judged_rows(conn, moment=None, slot=None, kinds=NON_CODE):
    """Passages whose judged label (agent memory) matches the requested moment/slot, as hb.lookup-shaped rows."""
    where, params = ["1=1"], []
    if moment:
        where.append("l.moment_type = ?")
        params.append(moment)
    if slot:
        where.append("l.slot_id = ?")
        params.append(slot)
    if kinds:
        where.append("p.kind IN (%s)" % ",".join("?" * len(kinds)))
        params += list(kinds)
    sql = (hb._SELECT + "JOIN mem.agent_labels l ON l.node_kind = 'passage' AND l.node_id = p.passage_id WHERE " + " AND ".join(where)
           + " ORDER BY l.confidence DESC, p.chars ASC")
    try:
        return [dict(r) for r in conn.execute(sql, params)]
    except sqlite3.OperationalError:
        return []


def judged_none(conn, moment=None, slot=None):
    """Passages whose judged label says 'none' for the requested dimension: a correction of a wrong lexical label."""
    out = set()
    try:
        if moment:
            out |= set(r[0] for r in conn.execute("SELECT node_id FROM mem.agent_labels WHERE node_kind='passage' AND moment_type='none'"))
        if slot:
            out |= set(r[0] for r in conn.execute("SELECT node_id FROM mem.agent_labels WHERE node_kind='passage' AND slot_id='none'"))
    except sqlite3.OperationalError:
        pass
    return out


def q_short(conn, pid):
    return short_id(conn, pid)


# =====================================================================================================
# Allocator (2026-10-22): coverage-first quotas, soft decay, roll-ups, nuance hop over accepted agent_links edges.
# Behind the `allocator` flag; the benchmark gate decides whether it ships.
# =====================================================================================================
LAMBDA_BLOCK, LAMBDA_ARTICLE, GAMMA_NUANCE = 0.35, 0.15, 0.05


def passage_edges(conn, ids):
    """{(a, b): relation} over accepted agent_links between passages in ids (both directions)."""
    ids = list(ids)
    if not ids:
        return {}
    out = {}
    try:
        rows = conn.execute("SELECT from_id, to_id, relation FROM mem.agent_links WHERE from_kind = 'passage' AND to_kind = 'passage'").fetchall()
    except sqlite3.OperationalError:
        return {}
    idset = set(ids)
    for a, b, rel in rows:
        if a in idset and b in idset:
            out[(a, b)] = rel
            out[(b, a)] = rel
    return out


def allocate(hits, concepts, k, spread=0.5, per_concept=None, edges=None, lam_block=LAMBDA_BLOCK, lam_article=LAMBDA_ARTICLE, gamma=GAMMA_NUANCE):
    """hits: candidate dicts (id, block, article, via, optional sbase) in rank order. Returns (chosen, footer)."""
    edges = edges or {}
    n = max(1, len(hits))
    for i, h in enumerate(hits):
        if h.get("sbase") is None:
            h["sbase"] = round(0.5 + 0.5 * (1.0 - i / float(n)), 4)
        via = h.get("via") or "query"
        h["_group"] = via.split(":", 1)[0] if ":" in via else "query"
    groups = OrderedDict()
    for cid, _ in concepts:
        groups[cid] = [h for h in hits if h["_group"] == cid]
    groups["query"] = [h for h in hits if h["_group"] not in groups]
    groups = OrderedDict((g, hs) for g, hs in groups.items() if hs)
    mass = dict((g, sum(h["sbase"] for h in hs)) for g, hs in groups.items())
    total = sum(mass.values()) or 1.0
    quota = dict((g, max(1, int(round(k * mass[g] / total)))) for g in groups)
    if per_concept:
        for g in quota:
            if g != "query":
                quota[g] = max(quota[g], per_concept)
    chosen, taken, nb, na = [], dict((g, 0) for g in groups), {}, {}
    remaining = dict((h["id"], h) for h in hits)

    def pick(h, why=None):
        chosen.append(h)
        remaining.pop(h["id"], None)
        taken[h["_group"]] += 1
        nb[h["block"]] = nb.get(h["block"], 0) + 1
        na[h["article"]] = na.get(h["article"], 0) + 1
        if why:
            h["allocated"] = why

    # 1. coverage: every group's best candidate
    for g, hs in sorted(groups.items(), key=lambda kv: -mass[kv[0]]):
        if len(chosen) >= k:
            break
        pick(hs[0], "coverage")
    # 2 + 3. quotas, then free slots, by decayed score with the nuance hop
    while len(chosen) < k and remaining:
        under = [g for g in groups if taken[g] < quota[g]]
        best = None
        for h in remaining.values():
            if under and h["_group"] not in under:
                continue
            decay = (1 - lam_block * spread * nb.get(h["block"], 0)) * (1 - lam_article * spread * na.get(h["article"], 0))
            score = h["sbase"] * max(decay, 0.05)
            nuance = None
            for c in chosen:
                rel = edges.get((h["id"], c["id"]))
                if rel:
                    score += gamma
                    nuance = "%s -> %s" % (rel, c.get("sid", c["id"]))
                    break
            if best is None or score > best[0]:
                best = (score, h, decay, nuance)
        if best is None:
            break
        score, h, decay, nuance = best
        h["sfinal"], h["decay"] = round(score, 4), round(decay, 2)
        if nuance:
            h["nuance"] = nuance
        pick(h, "quota" if under else "free")
    # roll-ups: unchosen candidates sharing a block with a chosen hit
    first_in_block = {}
    for c in chosen:
        first_in_block.setdefault(c["block"], c)
    for h in remaining.values():
        if h["block"] in first_in_block:
            c = first_in_block[h["block"]]
            c["more_in_block"] = c.get("more_in_block", 0) + 1
    footer = OrderedDict()
    for g, hs in groups.items():
        footer[g] = OrderedDict([("shown", taken[g]), ("candidates", len(hs)), ("articles", len(set(h["article"] for h in hs)))])
    for h in hits:
        h.pop("_group", None)
    return chosen, footer
