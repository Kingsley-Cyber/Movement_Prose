"""Benchmark: recall@10, MRR and retrieval-to-citation rate over docs/queries.jsonl.

queries.jsonl: first line may be a meta record {"meta": true, "authored_by": ..., "owner_reviewed": ...};
every other line {"id", "query", "expected": [passage ids or short ids], "mode": "find"|"lookup",
                  optional "moment", "slot", "note"}.
"""
import json
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path

from . import BUNDLE_DIR, __version__
from . import knowledge as kn
from . import query as q

QUERIES_PATH = Path(BUNDLE_DIR) / "docs" / "queries.jsonl"


def load_queries(path=QUERIES_PATH):
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError("no query file at %s" % path)
    meta, records = {}, []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        doc = json.loads(line)
        if doc.get("meta"):
            meta = doc
            continue
        if not doc.get("query") or not doc.get("expected"):
            raise ValueError("query record needs 'query' and 'expected': %r" % line[:80])
        doc.setdefault("mode", "find")
        doc.setdefault("id", "q%03d" % (len(records) + 1))
        records.append(doc)
    return meta, records


def recall_at_k(expected, got, k=10):
    expected = set(expected)
    if not expected:
        return 0.0
    return len(expected & set(got[:k])) / float(len(expected))


def reciprocal_rank(expected, got):
    expected = set(expected)
    for i, g in enumerate(got, 1):
        if g in expected:
            return 1.0 / i
    return 0.0


def run_query(conn, rec, limit=10, expand=True, diverse=True, rerank=None):
    kwargs = dict(limit=limit, expand=expand, diverse=diverse, rerank=rerank)
    if rec.get("mode") == "lookup":
        hits, _ = q.lookup2(conn, moment=rec.get("moment"), slot=rec.get("slot"), text=rec.get("query") if rec.get("use_text") else None,
                            min_score=rec.get("min_score", 2), **kwargs)
    else:
        hits, _ = q.lookup2(conn, text=rec["query"], min_score=0, **kwargs)
    return [h["id"] for h in hits]


def cited_passages(conn):
    """Passage ids with at least one 'cited' usage event (memory attached as mem, or a memory connection)."""
    try:
        rows = conn.execute("SELECT DISTINCT node_id FROM mem.usage_events WHERE action = 'cited' AND node_kind = 'passage'").fetchall()
    except Exception:
        try:
            rows = conn.execute("SELECT DISTINCT node_id FROM usage_events WHERE action = 'cited' AND node_kind = 'passage'").fetchall()
        except Exception:
            rows = []
    return set(r[0] for r in rows)


def run_bench(conn, records, limit=10, expand=True, diverse=True, rerank=None, label="bench"):
    rows, retrieved = [], set()
    for rec in records:
        expected = [q.resolve_id(conn, e) for e in rec["expected"]]
        got = run_query(conn, rec, limit, expand, diverse, rerank)
        retrieved |= set(got)
        rows.append(OrderedDict([("id", rec["id"]), ("query", rec["query"]), ("mode", rec.get("mode", "find")),
                                 ("recall", round(recall_at_k(expected, got, limit), 3)), ("rr", round(reciprocal_rank(expected, got), 3)),
                                 ("expected", [q.short_id(conn, e) for e in expected]), ("got", [q.short_id(conn, g) for g in got]),
                                 ("missing", [q.short_id(conn, e) for e in expected if e not in got[:limit]])]))
    n = max(1, len(rows))
    cited = cited_passages(conn)
    result = OrderedDict([
        ("label", label), ("at", datetime.now(timezone.utc).isoformat()), ("agent_version", __version__),
        ("config", OrderedDict([("limit", limit), ("expand", expand), ("diverse", diverse), ("rerank", rerank)])),
        ("queries", len(rows)),
        ("recall_at_k", round(sum(r["recall"] for r in rows) / n, 4)),
        ("mrr", round(sum(r["rr"] for r in rows) / n, 4)),
        ("retrieved_distinct", len(retrieved)),
        ("cited_distinct", len(cited)),
        ("retrieval_to_citation", round(len(cited & retrieved) / float(len(retrieved)), 4) if retrieved else 0.0),
        ("definition", "retrieval_to_citation = share of passages in the benchmark top-k that have ever been cited by a checked IR"),
        ("rows", rows),
    ])
    return result


def format_report(result):
    lines = ["bench %s  queries=%d  recall@%d=%.3f  MRR=%.3f  retrieved=%d  cited=%d  retrieval->citation=%.3f  config=%s" % (
        result["label"], result["queries"], result["config"]["limit"], result["recall_at_k"], result["mrr"], result["retrieved_distinct"],
        result["cited_distinct"], result["retrieval_to_citation"], json.dumps(result["config"]))]
    for r in result["rows"]:
        flag = "ok " if r["recall"] >= 1.0 else ("part" if r["recall"] > 0 else "MISS")
        lines.append("  %s %-5s recall %.2f rr %.2f  %s%s" % (flag, r["id"], r["recall"], r["rr"], r["query"][:60],
                                                             ("  missing " + ", ".join(r["missing"])) if r["missing"] else ""))
    return "\n".join(lines)


def save(result, out_dir=None, name=None):
    out_dir = Path(out_dir) if out_dir else Path(BUNDLE_DIR) / "docs" / "bench"
    out_dir.mkdir(parents=True, exist_ok=True)
    name = name or "%s-%s.json" % (datetime.now(timezone.utc).strftime("%Y-%m-%d"), result["label"])
    path = out_dir / name
    path.write_text(json.dumps(result, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return path
