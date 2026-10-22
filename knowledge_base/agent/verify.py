"""Integrity and backfill checks over the index and the memory database. Read-only."""
import json
import sqlite3
from collections import OrderedDict
from pathlib import Path

from . import DATA_DIR
from . import handbook as hb
from . import knowledge as kn


def run(index_path=hb.DEFAULT_DB, memory_path=kn.MEMORY_DB):
    checks = []

    def add(name, ok, detail=""):
        checks.append(OrderedDict([("check", name), ("ok", bool(ok)), ("detail", detail)]))

    conn = hb.connect(index_path)
    kn.attach_memory(conn, memory_path)
    add("sqlite_integrity_index", conn.execute("PRAGMA main.integrity_check").fetchone()[0] == "ok")
    add("sqlite_integrity_memory", conn.execute("PRAGMA mem.integrity_check").fetchone()[0] == "ok")
    meta = hb.meta(conn)
    src_str = meta.get("source_path", "")
    src = Path(src_str) if src_str else None
    expected_sha = meta.get("source_sha256", "")
    if src and src.exists():
        import hashlib
        add("index_matches_source_html", hashlib.sha256(src.read_bytes()).hexdigest() == expected_sha, str(src))
    elif expected_sha and len(expected_sha) == 64:
        add("index_matches_source_html", True, "pre-indexed sha256=%s (source html offline)" % expected_sha[:12])
    else:
        add("index_matches_source_html", False, "source html missing: %s" % src)
    n_pass = conn.execute("SELECT count(*) FROM handbook_passages").fetchone()[0]
    n_fts = conn.execute("SELECT count(*) FROM handbook_fts").fetchone()[0]
    add("fts_rows_equal_passages", n_fts == n_pass, "%d fts / %d passages" % (n_fts, n_pass))
    no_block = conn.execute("SELECT count(*) FROM handbook_passages WHERE block_id IS NULL").fetchone()[0]
    add("every_passage_has_block", no_block == 0, "%d without block" % no_block)
    for kind, table, col in (("passage", "handbook_passages", "passage_id"), ("block", "handbook_blocks", "block_id"), ("article", "handbook_articles", "article_id"),
                             ("section", "handbook_sections", "section_id"), ("chapter", "handbook_chapters", "chapter_id")):
        n = conn.execute("SELECT count(*) FROM %s" % table).fetchone()[0]
        s = conn.execute("SELECT count(*) FROM summaries WHERE node_kind = ? AND level = 'one_line'", (kind,)).fetchone()[0]
        add("summaries_cover_%ss" % kind, s >= n, "%d summaries / %d %ss" % (s, n, kind))
    n_concepts = conn.execute("SELECT count(*) FROM concepts").fetchone()[0]
    n_cfts = conn.execute("SELECT count(*) FROM concept_fts").fetchone()[0]
    add("concept_fts_rows_equal_concepts", n_cfts == n_concepts, "%d / %d" % (n_cfts, n_concepts))
    agent_concepts = kn.load_agent_concepts(memory_path)
    missing = [cid for cid, label, kind, aliases, desc in agent_concepts if conn.execute("SELECT 1 FROM concepts WHERE concept_id = ?", (cid,)).fetchone() is None]
    add("agent_concepts_backfilled_into_index", not missing, "%d agent concepts; missing from index: %s" % (len(agent_concepts), missing or "none"))
    unlinked_agent = [r[0] for r in conn.execute("SELECT c.concept_id FROM concepts c LEFT JOIN concept_passages cp USING(concept_id) WHERE c.source = 'agent' AND cp.passage_id IS NULL")]
    add("agent_concepts_linked_to_passages", not unlinked_agent, "unlinked: %s" % (unlinked_agent or "none"))
    for cid, aliases in ((cid, aliases) for cid, label, kind, aliases, desc in agent_concepts if kind == "alias_addition"):
        row = conn.execute("SELECT aliases FROM concepts WHERE concept_id = ?", (cid,)).fetchone()
        have = set(json.loads(row[0])) if row else set()
        add("alias_addition_merged_%s" % cid, set(aliases) <= have, "missing %s" % (sorted(set(aliases) - have) or "none"))
    orphan_edges = conn.execute("SELECT count(*) FROM handbook_edges e WHERE e.from_kind = 'passage' AND NOT EXISTS (SELECT 1 FROM handbook_passages p WHERE p.passage_id = e.from_id)").fetchone()[0]
    add("no_orphan_passage_edges", orphan_edges == 0, "%d orphan" % orphan_edges)
    # memory rows that point at passages: every id must resolve in the index
    dangling = OrderedDict()
    for table, cols in (("agent_labels", ("node_id",)), ("node_tags", ("node_id",)), ("agent_summaries", ("node_id",)), ("usage_events", ("node_id",)),
                        ("review_queue", ("a_id", "c_id")), ("agent_links", ("from_id", "to_id"))):
        for col in cols:
            kind_filter = ""
            if table in ("node_tags", "agent_summaries", "usage_events"):
                kind_filter = " AND node_kind = 'passage'"
            elif table == "agent_links":
                kind_filter = " AND %s_kind = 'passage'" % col.split("_")[0]
            elif table == "agent_labels":
                kind_filter = " AND node_kind = 'passage'"
            rows = conn.execute("SELECT %s FROM mem.%s WHERE 1=1%s" % (col, table, kind_filter)).fetchall()
            bad = [r[0] for r in rows if conn.execute("SELECT 1 FROM handbook_passages WHERE passage_id = ?", (r[0],)).fetchone() is None]
            if bad:
                dangling["%s.%s" % (table, col)] = bad[:5]
    add("memory_passage_refs_resolve", not dangling, json.dumps(dangling) if dangling else "all resolve")
    bad_dir = [r[0] for r in conn.execute("SELECT node_id FROM mem.usage_events WHERE node_kind = 'directive'") if conn.execute("SELECT 1 FROM directive_requires WHERE directive_id = ? UNION SELECT 1 FROM directive_passages WHERE directive_id = ?", (r[0], r[0])).fetchone() is None]
    add("memory_directive_refs_known", not bad_dir, (bad_dir[:5] or "all known"))
    bad_c = [r[0] for r in conn.execute("SELECT subject_concept FROM mem.causal_triples UNION SELECT object_concept FROM mem.causal_triples") if conn.execute("SELECT 1 FROM concepts WHERE concept_id = ?", (r[0],)).fetchone() is None]
    add("causal_concepts_exist", not bad_c, (bad_c[:5] or "all exist"))
    try:
        rr = json.loads((Path(DATA_DIR) / "rerank.json").read_text(encoding="utf-8"))
        from . import query as q
        unknown = [k for k in rr.get("flags", {}) if k not in q.RERANK_FLAGS]
        add("rerank_flags_known", not unknown, "flags %s; unknown %s" % (json.dumps({k: v for k, v in rr.get("flags", {}).items() if v}), unknown or "none"))
    except Exception as e:
        add("rerank_flags_known", False, str(e))
    counts = OrderedDict([("passages", n_pass), ("blocks", conn.execute("SELECT count(*) FROM handbook_blocks").fetchone()[0]), ("concepts", n_concepts),
                          ("concept_passages", conn.execute("SELECT count(*) FROM concept_passages").fetchone()[0]), ("edges", conn.execute("SELECT count(*) FROM handbook_edges").fetchone()[0]),
                          ("agent_labels", conn.execute("SELECT count(*) FROM mem.agent_labels").fetchone()[0]), ("agent_links", conn.execute("SELECT count(*) FROM mem.agent_links").fetchone()[0]),
                          ("causal_triples", conn.execute("SELECT count(*) FROM mem.causal_triples").fetchone()[0]), ("review_queue", dict(conn.execute("SELECT status, count(*) FROM mem.review_queue GROUP BY 1").fetchall())),
                          ("usage_events", conn.execute("SELECT count(*) FROM mem.usage_events").fetchone()[0]), ("tags", conn.execute("SELECT count(*) FROM mem.node_tags").fetchone()[0])])
    conn.close()
    return OrderedDict([("ok", all(c["ok"] for c in checks)), ("checks", checks), ("counts", counts), ("built_at", meta.get("built_at"))])


def format_report(res):
    lines = ["verify: %s  (index built %s)" % ("PASS" if res["ok"] else "FAIL", res.get("built_at"))]
    for c in res["checks"]:
        lines.append("  %s %-40s %s" % ("ok " if c["ok"] else "BAD", c["check"], c["detail"]))
    lines.append("  counts: " + json.dumps(res["counts"]))
    return "\n".join(lines)
