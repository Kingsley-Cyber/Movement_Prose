"""Causal triples between concepts with a closed predicate set; closure and isomorphism queries. Stored in agent memory."""
import json
import re
from collections import OrderedDict

from . import knowledge as kn

PREDICATES = ("amplifies", "dampens", "triggers", "inhibits", "requires", "breaks", "compensates_for")
FORWARD = ("requires", "triggers", "amplifies")
CLAUSE_MAP = {"requires": "requires", "depends_on": "requires", "conflicts_with": "inhibits"}


def add(mem, subject, predicate, obj, evidence, passage_id=None, confidence=0.6, created_by="agent"):
    if predicate not in PREDICATES:
        raise ValueError("predicate must be one of %s" % (PREDICATES,))
    if not (evidence or "").strip():
        raise ValueError("a causal triple needs evidence")
    if not subject or not obj or subject == obj:
        raise ValueError("subject and object must be two different concept ids")
    mem.execute("INSERT OR IGNORE INTO causal_triples (subject_concept, predicate, object_concept, evidence, passage_id, confidence, created_at, created_by) VALUES (?,?,?,?,?,?,?,?)",
                (subject, predicate, obj, evidence.strip(), passage_id, float(confidence), kn.now(), created_by))
    mem.commit()
    return mem.total_changes


def list_triples(mem, concept=None, limit=200):
    if concept:
        rows = mem.execute("SELECT * FROM causal_triples WHERE subject_concept = ? OR object_concept = ? ORDER BY id LIMIT ?", (concept, concept, limit)).fetchall()
    else:
        rows = mem.execute("SELECT * FROM causal_triples ORDER BY id LIMIT ?", (limit,)).fetchall()
    return [dict(r) for r in rows]


def closure(mem, concept, predicates=FORWARD, depth=3):
    """Concepts reachable from `concept` along the given predicates, with depth and the path's predicates."""
    ph = ",".join("?" * len(predicates))
    rows = mem.execute(
        "WITH RECURSIVE walk(node, depth, path) AS (SELECT ?, 0, '' UNION ALL "
        "SELECT t.object_concept, w.depth + 1, w.path || t.predicate || '>' || t.object_concept || ' ' FROM causal_triples t JOIN walk w ON t.subject_concept = w.node "
        "WHERE t.predicate IN (%s) AND w.depth < ? AND instr(w.path, t.object_concept) = 0) "
        "SELECT node, min(depth) AS d, min(path) AS path FROM walk WHERE depth > 0 GROUP BY node ORDER BY d, node" % ph,
        [concept] + list(predicates) + [depth]).fetchall()
    return [OrderedDict([("concept", r[0]), ("depth", r[1]), ("path", r[2].strip())]) for r in rows]


def compensations(mem, concept):
    """Swanson-shaped read over triples: X --amplifies/triggers--> concept <--dampens/inhibits/compensates_for-- Y, so Y compensates for X."""
    rows = mem.execute(
        "SELECT a.subject_concept AS cause, a.predicate AS p1, b.subject_concept AS cure, b.predicate AS p2 FROM causal_triples a JOIN causal_triples b "
        "ON a.object_concept = b.object_concept WHERE a.object_concept = ? AND a.predicate IN ('amplifies','triggers') AND b.predicate IN ('dampens','inhibits','compensates_for') "
        "AND a.subject_concept != b.subject_concept", (concept,)).fetchall()
    return [dict(r) for r in rows]


def isomorphs(mem, limit=50):
    """Pairs of two-edge chains (X -p1-> Y -p2-> Z) and (M -p1-> N -p2-> O) with the same predicate sequence and no shared concept."""
    rows = mem.execute(
        "WITH chains AS (SELECT a.subject_concept AS x, a.predicate AS p1, a.object_concept AS y, b.predicate AS p2, b.object_concept AS z "
        "FROM causal_triples a JOIN causal_triples b ON a.object_concept = b.subject_concept WHERE a.subject_concept != b.object_concept) "
        "SELECT c1.x, c1.p1, c1.y, c1.p2, c1.z, c2.x, c2.y, c2.z FROM chains c1 JOIN chains c2 ON c1.p1 = c2.p1 AND c1.p2 = c2.p2 "
        "AND c1.x < c2.x AND c1.y != c2.y AND c1.z != c2.z AND c1.x != c2.y AND c1.x != c2.z AND c1.y != c2.x AND c1.z != c2.x LIMIT ?", (limit,)).fetchall()
    return [OrderedDict([("pattern", "%s>%s" % (r[1], r[3])), ("chain_a", [r[0], r[2], r[4]]), ("chain_b", [r[5], r[6], r[7]])]) for r in rows]


# --- seeding from grounded sources -----------------------------------------------------------------
def _alias_index(conn):
    idx = []
    for cid, aliases in conn.execute("SELECT concept_id, aliases FROM concepts"):
        for a in json.loads(aliases or "[]"):
            if len(a) >= 4:
                idx.append((a.lower(), cid))
    idx.sort(key=lambda x: -len(x[0]))
    return idx


def seed_from_handbook(conn, mem):
    """Lexical requires/depends_on/conflicts_with clauses whose object names a concept alias and whose passage carries a concept."""
    idx = _alias_index(conn)
    n = 0
    # materialise first: an open read statement on `conn` (which has memory attached) would hold a shared lock while `mem` tries to commit
    clauses = conn.execute("SELECT from_id, relation, to_id, evidence FROM handbook_edges WHERE relation IN ('requires','depends_on','conflicts_with')").fetchall()
    for pid, rel, clause, evidence in clauses:
        low = (clause or "").lower()
        obj = next((cid for a, cid in idx if a in low), None)
        if obj is None:
            continue
        # subject = the passage's most specific mechanism/technique concept, judged by the alias it matched (same 2% cap as retrieval)
        from . import query as q
        best = None
        links = conn.execute("SELECT cp.concept_id, cp.matched FROM concept_passages cp JOIN concepts c USING(concept_id) WHERE cp.passage_id = ? AND c.kind IN ('mechanism','technique','directive')", (pid,)).fetchall()
        for cid, matched in links:
            spec = dict((a.lower(), w) for a, _, w in q.specific_aliases(conn, cid))
            w = max([spec[m.lower()] for m in json.loads(matched or "[]") if m.lower() in spec] or [0])
            if w > 0 and (best is None or w > best[1]):
                best = (cid, w)
        if best is None or best[0] == obj:
            continue
        subj = (best[0],)
        before = mem.total_changes
        add(mem, subj[0], CLAUSE_MAP[rel], obj, "handbook clause: %s" % (evidence or clause)[:200], pid, 0.5, "seed:handbook")
        n += 1 if mem.total_changes > before else 0
    return n


def seed_from_catalog(conn, mem):
    """Catalog mechanics: directive requires satisfiers -> requires; conflicts_with -> inhibits (both directions)."""
    n = 0
    for d, token, sat in conn.execute("SELECT directive_id, token, satisfier_directive_id FROM directive_requires WHERE satisfier_directive_id IS NOT NULL"):
        before = mem.total_changes
        add(mem, "directive:" + d, "requires", "directive:" + sat, "mechanical_guidance requires %s, satisfied by %s" % (token, sat), None, 0.8, "seed:catalog")
        n += 1 if mem.total_changes > before else 0
    for a, b in conn.execute("SELECT directive_id, other_id FROM directive_conflicts"):
        before = mem.total_changes
        add(mem, "directive:" + a, "inhibits", "directive:" + b, "mechanical_guidance conflicts_with (same interval and scope)", None, 0.8, "seed:catalog")
        n += 1 if mem.total_changes > before else 0
    return n
