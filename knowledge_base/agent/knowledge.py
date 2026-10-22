"""Knowledge layers over the handbook index: blocks (mid granularity), one-line summaries, duplicate links,
a concept layer with equivalent terms, and the agent's own memory database (tags, usage log, used_with links).

Two files:
  handbook_index.db   derived from handbook.html + the bundle; rebuilt from scratch by `index-handbook`.
  agent_memory.db     grows as the agent works (tags, usage events, agent summaries/concepts); never rebuilt.
"""
import hashlib
import json
import re
import sqlite3
from collections import OrderedDict, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from . import BUNDLE_DIR

MEMORY_DB = Path(BUNDLE_DIR) / "agent_memory.db"
_WS = re.compile(r"\s+")
_SENT = re.compile(r"(?<=[.!?])\s+(?=[A-Z\[(])")

# --- seed concepts: equivalent terms the handbook and the lexicon use for the same thing ------------------
# concept_id: (label, kind, [aliases...]). Aliases are matched as FTS phrases (porter-stemmed), so singular/plural fold.
SEED_CONCEPTS = OrderedDict([
    ("hit_stop", ("Hit-stop / impact hold", "technique", ["hit-stop", "hitstop", "hit stop", "impact hold", "contact hold", "freeze frame", "impact freeze", "contact freeze"])),
    ("smear", ("Smear frame", "technique", ["smear", "smear frame", "multiple contour", "multiple-contour", "motion smear", "stretch frame"])),
    ("on_twos", ("Exposure on twos", "technique", ["on twos", "on 2s", "twos", "two-frame exposure", "12 drawings per second", "held for two frames"])),
    ("on_ones", ("Exposure on ones", "technique", ["on ones", "on 1s", "ones", "single-frame exposure", "24 drawings per second"])),
    ("exposure_sheet", ("Exposure sheet / timing chart", "technique", ["exposure sheet", "x-sheet", "timing chart", "dope sheet", "editorial timeline", "exposure schedule"])),
    ("anticipation", ("Anticipation / wind-up", "phase", ["anticipation", "wind-up", "windup", "wind up", "preparation", "backswing", "loading", "coil", "telegraph"])),
    ("execution", ("Execution / stroke", "phase", ["execution", "stroke", "acceleration", "initiation", "main action", "action phase"])),
    ("impact", ("Impact / contact", "phase", ["impact", "contact", "collision", "apex", "contact beat", "impact frame"])),
    ("recoil", ("Recoil / reaction", "phase", ["recoil", "reaction", "knockback", "stagger", "displacement"])),
    ("follow_through", ("Follow-through / overshoot", "phase", ["follow-through", "follow through", "overshoot", "overlapping action", "momentum carries"])),
    ("recovery", ("Recovery / settle", "phase", ["recovery", "settle", "reset", "return to guard", "rest state", "regain balance"])),
    ("phase_grammar", ("Phase grammar / motion beats", "concept", ["phase grammar", "beat structure", "motion beats", "choreography grammar", "phase graph", "phase spine", "beat grammar"])),
    ("impact_flash", ("Impact flash / accent frame", "technique", ["impact flash", "inverse-color flash", "inverted flash", "monochrome accent", "monochrome impact", "impact accent", "flash frame", "silhouette flash", "charcoal impact"])),
    ("shock_ring", ("Shockwave ring", "technique", ["shockwave ring", "shock ring", "contact ring", "concentric ring", "impact ring", "shockwave"])),
    ("impact_star", ("Impact star / starburst", "technique", ["impact star", "starburst", "angular star", "contact star", "impact burst"])),
    ("speed_lines", ("Speed lines", "technique", ["speed lines", "motion lines", "focus lines", "speed void", "speed background", "streak background"])),
    ("yutapon_cubes", ("Yutapon cubes / cubic debris", "technique", ["yutapon cubes", "yutapon", "cubic debris", "cube debris", "cubic fragments", "debris cubes"])),
    ("kanada_dragon", ("Kanada dragon / flame dragon", "technique", ["kanada dragon", "flame dragon", "kanada fire", "graphic flame"])),
    ("kanada_perspective", ("Kanada perspective / foreshortening", "technique", ["kanada perspective", "foreshortening", "foreshortened fist", "perspective break", "extreme foreshortening"])),
    ("itano_circus", ("Itano circus / missile swarm", "technique", ["itano circus", "missile swarm", "missile evasion", "converging missiles", "itano"])),
    ("kagenashi", ("Kagenashi / shadowless shading", "technique", ["kagenashi", "shadowless", "no cast shadow", "flat lighting", "shadowless shading"])),
    ("cel_shading", ("Cel shading / two-tone", "technique", ["cel shading", "cel-shading", "two-tone", "two tone", "hard shadow edge", "flat color", "cel look"])),
    ("line_boil", ("Line boil", "technique", ["line boil", "boiling line", "line jitter", "wobbling line"])),
    ("hard_shadow", ("Hard shadow / key light", "technique", ["hard shadow", "hard key", "key light", "crisp shadow", "sharp shadow"])),
    ("rim_light", ("Rim light", "technique", ["rim light", "rim lighting", "thin rim", "edge light", "backlight"])),
    ("sakuga", ("Sakuga", "concept", ["sakuga", "sakuga cut", "sakuga anime"])),
    ("camera_lock", ("Camera lock on contact", "technique", ["camera lock", "contact lock", "locked camera", "locked off", "hold the camera", "static camera", "fixed camera"])),
    ("crash_zoom", ("Crash zoom", "technique", ["crash zoom", "snap zoom", "push-in on impact", "punch in"])),
    ("whip_pan", ("Whip pan / reacquire", "technique", ["whip pan", "whip reacquire", "whip-pan", "fast pan"])),
    ("lateral_track", ("Lateral tracking", "technique", ["lateral track", "tracking shot", "lateral tracking", "side track", "truck"])),
    ("camera_shake", ("Camera shake", "technique", ["camera shake", "impact shake", "handheld shake", "screen shake"])),
    ("parallax", ("Background parallax", "technique", ["parallax", "layered background", "depth layers", "background layers"])),
    ("dust_debris", ("Dust and debris", "technique", ["dust", "debris", "dust billow", "dust ring", "rubble", "fragments"])),
    ("ground_fracture", ("Ground fracture / crater", "technique", ["ground fracture", "radial fracture", "crater", "cracked ground", "cracks beneath", "floor cracks"])),
    ("skid_gouge", ("Skid / gouge", "technique", ["skid", "gouge", "skid mark", "heel slide", "sliding back"])),
    ("cloth_lag", ("Cloth and hair lag", "technique", ["cloth lag", "hair lag", "fabric lag", "hem lags", "hair snap", "cape overshoot", "cloth settle", "secondary motion"])),
    ("weight_load", ("Weight loading", "technique", ["weight load", "load the rear foot", "rear foot plant", "weight onto the rear", "weight shift", "loads weight"])),
    ("hip_led_punch", ("Hip-led straight punch", "technique", ["hip-led", "hip led", "straight punch", "cross", "jab", "rear hand", "punch from the hips"])),
    ("forearm_block", ("Forearm block / parry", "technique", ["forearm block", "parry", "block with the forearm", "outer forearm", "intercept"])),
    ("flash_step", ("Flash step / vanish-arrive", "technique", ["flash step", "vanish", "teleport", "blink", "instant displacement", "arrival pose"])),
    ("guard_recovery", ("Guard recovery", "technique", ["guard recovery", "return to guard", "back to guard", "resets the guard", "recovers the guard"])),
    ("kinetic_chain", ("Kinetic chain", "concept", ["kinetic chain", "feet to hips", "hips to shoulder", "ground reaction", "chain of force", "proximal to distal"])),
    ("weight_transfer", ("Weight transfer", "concept", ["weight transfer", "center of mass", "centre of mass", "center of gravity", "balance shift", "support leg"])),
    ("silhouette", ("Readable silhouette", "concept", ["silhouette", "readable pose", "pose readability", "clear silhouette", "line of action"])),
    ("identity_lock", ("Identity lock / continuity", "concept", ["identity drift", "identity lock", "continuity lock", "character consistency", "on-model", "wardrobe consistency", "costume attachment"])),
    ("laban_effort", ("Laban effort quality", "concept", ["laban", "effort quality", "effort factors", "weight time space flow", "bound flow", "free flow", "strong weight", "sudden time", "direct space", "indirect space"])),
    ("complexity_budget", ("Complexity / attention budget", "concept", ["complexity budget", "attention budget", "motion budget", "attention dilution", "one dominant", "salience ranking", "salience budget"])),
    ("priority_classes", ("Control priority classes", "concept", ["locked constraint", "priority class", "required control", "suppression reason", "control priority", "locked constraints"])),
    ("capability_classes", ("Provider capability classes", "concept", ["capability class", "native control", "approximate control", "semantic projection", "unsupported control", "provider capability"])),
    ("compilation_loss", ("Compilation loss record", "concept", ["compilation loss", "loss record", "compilation-loss", "loss ledger"])),
    ("negatives", ("Negative prompt / avoid list", "concept", ["negative prompt", "negatives", "avoid list", "negative constraints", "negative field", "negative conditioning"])),
    ("director_language", ("Director-language clause pattern", "concept", ["director-language", "director language", "clause pattern", "bracketed clause", "shot and duration", "clause classes"])),
    ("canonical_ir", ("Canonical IR / universal score", "concept", ["canonical ir", "intermediate representation", "universal score", "canonical schema", "canonical semantic", "control ir"])),
    ("frame_rate", ("Frame rate / fps", "concept", ["frame rate", "fps", "frames per second", "output fps", "native fps", "playback rate"])),
    ("slow_motion", ("Slow motion / time ramp", "technique", ["slow motion", "slow-motion", "time ramp", "speed ramp", "time remap", "ramp down", "slowed"])),
    ("contact_contract", ("Contact contract", "concept", ["contact contract", "what touches what", "point of contact", "contact point", "contact geometry", "contact event"])),
    ("end_frame", ("End-frame goal", "concept", ["end frame", "end-frame goal", "final pose", "final frame", "last frame", "end state"])),
    ("i2v", ("Image-to-video", "workflow", ["image-to-video", "image to video", "i2v", "first frame lock", "motion delta"])),
    ("first_last_frame", ("First/last frame workflow", "workflow", ["first/last frame", "first and last frame", "start and end frames", "keyframe pair"])),
])

SCHEMA_INDEX = """
CREATE TABLE handbook_blocks (block_id TEXT PRIMARY KEY, article_id TEXT, ordinal INTEGER, heading_path TEXT, title TEXT,
    passage_count INTEGER, chars INTEGER, first_passage_id TEXT, last_passage_id TEXT);
CREATE INDEX idx_hb_blocks_article ON handbook_blocks(article_id, ordinal);
CREATE TABLE summaries (node_kind TEXT, node_id TEXT, level TEXT, text TEXT, source TEXT, created_at TEXT, PRIMARY KEY (node_kind, node_id, level, source));
CREATE VIRTUAL TABLE summary_fts USING fts5(node_kind UNINDEXED, node_id UNINDEXED, text, tokenize='porter unicode61');
CREATE TABLE concepts (concept_id TEXT PRIMARY KEY, label TEXT, kind TEXT, aliases TEXT, description TEXT, source TEXT);
CREATE VIRTUAL TABLE concept_fts USING fts5(concept_id UNINDEXED, label, aliases, tokenize='porter unicode61');
CREATE TABLE concept_passages (concept_id TEXT, passage_id TEXT, weight INTEGER, matched TEXT, PRIMARY KEY (concept_id, passage_id));
CREATE INDEX idx_cp_passage ON concept_passages(passage_id);
CREATE TABLE concept_edges (from_concept TEXT, to_concept TEXT, relation TEXT, weight INTEGER, evidence TEXT, PRIMARY KEY (from_concept, to_concept, relation));
CREATE TABLE concept_directives (concept_id TEXT, directive_id TEXT, relation TEXT, PRIMARY KEY (concept_id, directive_id, relation));
"""

SCHEMA_MEMORY = """
CREATE TABLE IF NOT EXISTS tags (tag TEXT PRIMARY KEY, description TEXT, created_at TEXT, created_by TEXT);
CREATE TABLE IF NOT EXISTS tag_aliases (alias TEXT PRIMARY KEY, tag TEXT);
CREATE TABLE IF NOT EXISTS node_tags (node_kind TEXT, node_id TEXT, tag TEXT, weight REAL, note TEXT, created_at TEXT, created_by TEXT, PRIMARY KEY (node_kind, node_id, tag));
CREATE INDEX IF NOT EXISTS idx_node_tags_tag ON node_tags(tag);
CREATE VIRTUAL TABLE IF NOT EXISTS tag_fts USING fts5(tag UNINDEXED, text, tokenize='porter unicode61');
CREATE TABLE IF NOT EXISTS usage_events (event_id INTEGER PRIMARY KEY AUTOINCREMENT, at TEXT, run_id TEXT, action TEXT, node_kind TEXT, node_id TEXT, context TEXT);
CREATE INDEX IF NOT EXISTS idx_usage_node ON usage_events(node_kind, node_id);
CREATE INDEX IF NOT EXISTS idx_usage_run ON usage_events(run_id, action);
CREATE TABLE IF NOT EXISTS used_with (a_kind TEXT, a_id TEXT, b_kind TEXT, b_id TEXT, count INTEGER, last_at TEXT, PRIMARY KEY (a_kind, a_id, b_kind, b_id));
CREATE TABLE IF NOT EXISTS agent_summaries (node_kind TEXT, node_id TEXT, level TEXT, text TEXT, created_at TEXT, created_by TEXT, PRIMARY KEY (node_kind, node_id, level));
CREATE TABLE IF NOT EXISTS agent_concepts (concept_id TEXT PRIMARY KEY, label TEXT, kind TEXT, aliases TEXT, description TEXT, created_at TEXT, created_by TEXT);
CREATE TABLE IF NOT EXISTS agent_links (from_kind TEXT, from_id TEXT, to_kind TEXT, to_id TEXT, relation TEXT, note TEXT, created_at TEXT, created_by TEXT,
    PRIMARY KEY (from_kind, from_id, to_kind, to_id, relation));
CREATE TABLE IF NOT EXISTS review_queue (id INTEGER PRIMARY KEY AUTOINCREMENT, kind TEXT, a_id TEXT, b_concept TEXT, c_id TEXT, score REAL, evidence TEXT,
    status TEXT, relation TEXT, note TEXT, created_at TEXT, resolved_at TEXT, resolved_by TEXT, source TEXT, UNIQUE (kind, a_id, b_concept, c_id));
CREATE TABLE IF NOT EXISTS module_relations (id INTEGER PRIMARY KEY AUTOINCREMENT, source TEXT, relation TEXT, target TEXT, offset TEXT, evidence TEXT, passage_id TEXT,
    confidence REAL, created_at TEXT, created_by TEXT, UNIQUE (source, relation, target));
CREATE INDEX IF NOT EXISTS idx_rel_source ON module_relations(source);
CREATE INDEX IF NOT EXISTS idx_rel_target ON module_relations(target);
CREATE TABLE IF NOT EXISTS causal_triples (id INTEGER PRIMARY KEY AUTOINCREMENT, subject_concept TEXT, predicate TEXT, object_concept TEXT, evidence TEXT,
    passage_id TEXT, confidence REAL, created_at TEXT, created_by TEXT, UNIQUE (subject_concept, predicate, object_concept));
CREATE INDEX IF NOT EXISTS idx_causal_subject ON causal_triples(subject_concept);
CREATE INDEX IF NOT EXISTS idx_causal_object ON causal_triples(object_concept);
CREATE TABLE IF NOT EXISTS agent_labels (node_kind TEXT, node_id TEXT, moment_type TEXT, slot_id TEXT, intent_tier INTEGER, reason TEXT, confidence REAL,
    created_at TEXT, created_by TEXT, PRIMARY KEY (node_kind, node_id));
"""


def now():
    return datetime.now(timezone.utc).isoformat()


def one_line(text, limit=140):
    text = _WS.sub(" ", text or "").strip()
    first = _SENT.split(text, 1)[0] if text else ""
    out = first if first else text
    return out if len(out) <= limit else out[: limit - 1] + "…"


def _fts_phrase(alias):
    return '"' + alias.replace('"', '""') + '"'


# --- derived layers written into handbook_index.db at build time -------------------------------------------
def load_agent_concepts(memory_path=MEMORY_DB):
    """[(concept_id, label, kind, aliases, description)] from agent_memory.db, or [] when absent."""
    path = Path(memory_path)
    if not path.exists():
        return []
    mem = sqlite3.connect(str(path))
    try:
        rows = mem.execute("SELECT concept_id, label, kind, aliases, description FROM agent_concepts").fetchall()
    except sqlite3.OperationalError:
        rows = []
    mem.close()
    return [(r[0], r[1], r[2], json.loads(r[3] or "[]"), r[4] or "") for r in rows]


def build_layers(conn, catalog=None, agent_concepts=None):
    if agent_concepts is None:
        agent_concepts = load_agent_concepts()
    conn.executescript(SCHEMA_INDEX)
    conn.execute("ALTER TABLE handbook_passages ADD COLUMN block_id TEXT")
    passages = conn.execute("SELECT passage_id, article_id, ordinal, heading_path, text, chars, sha256 FROM handbook_passages "
                            "ORDER BY article_id, ordinal").fetchall()
    # blocks: consecutive passages of one article under the same heading path
    blocks, block_rows, pass_block = OrderedDict(), [], []
    for pid, aid, ordinal, hp, text, chars, sha in passages:
        key = (aid, hp)
        if key not in blocks:
            b_ord = sum(1 for k in blocks if k[0] == aid) + 1
            blocks[key] = {"block_id": "%s/b%03d" % (aid, b_ord), "article_id": aid, "ordinal": b_ord, "heading_path": hp,
                           "title": hp.split(" > ")[-1] if hp else "", "passage_count": 0, "chars": 0, "first": pid, "last": pid}
        b = blocks[key]
        b["passage_count"] += 1
        b["chars"] += chars
        b["last"] = pid
        pass_block.append((b["block_id"], pid))
    for b in blocks.values():
        block_rows.append((b["block_id"], b["article_id"], b["ordinal"], b["heading_path"], b["title"], b["passage_count"], b["chars"], b["first"], b["last"]))
    conn.executemany("INSERT INTO handbook_blocks VALUES (?,?,?,?,?,?,?,?,?)", block_rows)
    conn.executemany("UPDATE handbook_passages SET block_id = ? WHERE passage_id = ?", pass_block)
    conn.executemany("INSERT OR IGNORE INTO handbook_edges VALUES ('block', ?, 'passage', ?, 'contains', NULL)", pass_block)
    conn.executemany("INSERT OR IGNORE INTO handbook_edges VALUES ('article', ?, 'block', ?, 'contains', NULL)",
                     [(b["article_id"], b["block_id"]) for b in blocks.values()])
    # duplicate text links
    by_sha = defaultdict(list)
    for pid, aid, ordinal, hp, text, chars, sha in passages:
        if chars >= 40:
            by_sha[sha].append(pid)
    dupes = [(ids[0], other) for ids in by_sha.values() if len(ids) > 1 for other in ids[1:]]
    conn.executemany("INSERT OR IGNORE INTO handbook_edges VALUES ('passage', ?, 'passage', ?, 'same_text', NULL)", dupes)
    # auto summaries: one line per passage, block, article, section, chapter
    ts = now()
    srows = []
    for pid, aid, ordinal, hp, text, chars, sha in passages:
        srows.append(("passage", pid, "one_line", one_line(text), "auto", ts))
    first_text = {}
    for pid, aid, ordinal, hp, text, chars, sha in passages:
        first_text.setdefault(("block", pass_block_lookup(pass_block, pid)), one_line(text, 100))
        first_text.setdefault(("article", aid), one_line(text, 100))
    for b in blocks.values():
        srows.append(("block", b["block_id"], "one_line", ("%s — %s" % (b["title"], first_text.get(("block", b["block_id"]), ""))).strip(" —"), "auto", ts))
    for aid, title, src, kind in conn.execute("SELECT article_id, title, src, kind FROM handbook_articles"):
        srows.append(("article", aid, "one_line", ("%s — %s" % (title or aid, first_text.get(("article", aid), ""))).strip(" —"), "auto", ts))
    for sid, title in conn.execute("SELECT section_id, title FROM handbook_sections"):
        n = conn.execute("SELECT count(*) FROM handbook_articles WHERE section_id = ?", (sid,)).fetchone()[0]
        srows.append(("section", sid, "one_line", "%s (%d articles)" % (title, n), "auto", ts))
    for cid, title in conn.execute("SELECT chapter_id, title FROM handbook_chapters"):
        n = conn.execute("SELECT count(*) FROM handbook_sections WHERE chapter_id = ?", (cid,)).fetchone()[0]
        srows.append(("chapter", cid, "one_line", "%s (%d sections)" % (title, n), "auto", ts))
    conn.executemany("INSERT OR IGNORE INTO summaries VALUES (?,?,?,?,?,?)", srows)
    conn.executemany("INSERT INTO summary_fts VALUES (?,?,?)", [(r[0], r[1], r[3]) for r in srows])
    # concepts: seeds + one per directive; alias matching through FTS; co-occurrence edges
    crows, cfts = [], []
    concepts = OrderedDict()
    for cid, (label, kind, aliases) in SEED_CONCEPTS.items():
        concepts[cid] = (label, kind, list(aliases), "", "seed")
    if catalog is not None:
        for d in catalog.rows():
            title = (d.catalog or {}).get("title") or d.directive_id
            aliases = [title] + list((d.catalog or {}).get("aliases") or [])
            cid = "directive:" + d.directive_id
            concepts[cid] = (title, "directive", aliases, (d.catalog or {}).get("anticipated_failure", "") or "", "catalog")
    for cid, label, kind, aliases, desc in agent_concepts:
        if cid in concepts:   # alias additions to a seed or catalog concept keep its label/kind/source, aliases merge
            old_label, old_kind, old_aliases, old_desc, old_source = concepts[cid]
            merged = list(old_aliases) + [a for a in aliases if a not in old_aliases]
            concepts[cid] = (old_label, old_kind, merged, old_desc, old_source + "+agent")
        else:
            concepts[cid] = (label, kind or "concept", list(aliases), desc, "agent")
    for cid, (label, kind, aliases, desc, source) in concepts.items():
        crows.append((cid, label, kind, json.dumps(aliases), desc, source))
        cfts.append((cid, label, " ; ".join(aliases)))
    conn.executemany("INSERT INTO concepts VALUES (?,?,?,?,?,?)", crows)
    conn.executemany("INSERT INTO concept_fts VALUES (?,?,?)", cfts)
    cp = defaultdict(lambda: [0, []])
    for cid, (label, kind, aliases, desc, source) in concepts.items():
        for alias in aliases:
            if len(alias) < 3:
                continue
            try:
                hits = conn.execute("SELECT passage_id FROM handbook_fts WHERE handbook_fts MATCH ?", (_fts_phrase(alias),)).fetchall()
            except sqlite3.OperationalError:
                continue
            for (pid,) in hits:
                cp[(cid, pid)][0] += 1
                cp[(cid, pid)][1].append(alias)
    conn.executemany("INSERT OR IGNORE INTO concept_passages VALUES (?,?,?,?)",
                     [(cid, pid, w, json.dumps(sorted(set(m)))) for (cid, pid), (w, m) in cp.items()])
    per_passage = defaultdict(set)
    for (cid, pid) in cp:
        per_passage[pid].add(cid)
    co = defaultdict(int)
    for pid, cids in per_passage.items():
        cids = sorted(cids)
        for i, a in enumerate(cids):
            for b in cids[i + 1:]:
                co[(a, b)] += 1
    conn.executemany("INSERT OR IGNORE INTO concept_edges VALUES (?,?,'co_occurs',?,NULL)", [(a, b, n) for (a, b), n in co.items() if n >= 2])
    # phase order and directive relations as concept edges
    for a, b in (("anticipation", "execution"), ("execution", "impact"), ("impact", "recoil"), ("impact", "follow_through"),
                 ("recoil", "recovery"), ("follow_through", "recovery")):
        conn.execute("INSERT OR IGNORE INTO concept_edges VALUES (?,?,'precedes',1,'moment_edges')", (a, b))
    if catalog is not None:
        cd = []
        for d in catalog.rows():
            cd.append(("directive:" + d.directive_id, d.directive_id, "is"))
            cd.append((d.moment_type, d.directive_id, "phase_of"))
            for other in catalog.conflicts(d.directive_id):
                conn.execute("INSERT OR IGNORE INTO concept_edges VALUES (?,?,'conflicts_with',1,'mechanical_guidance')",
                             ("directive:" + d.directive_id, "directive:" + other))
        # link seed concepts to directives whose title/aliases/id share an alias
        for cid, (label, kind, aliases, desc, source) in concepts.items():
            if source != "seed":
                continue
            for d in catalog.rows():
                hay = (" ".join([(d.catalog or {}).get("title", ""), " ".join((d.catalog or {}).get("aliases") or []), d.directive_id.replace("_", " ")])).lower()
                if any(a.lower() in hay for a in aliases if len(a) > 3):
                    cd.append((cid, d.directive_id, "implemented_by"))
        conn.executemany("INSERT OR IGNORE INTO concept_directives VALUES (?,?,?)", cd)
    conn.commit()
    return {"blocks": len(block_rows), "same_text": len(dupes), "summaries": len(srows), "concepts": len(crows),
            "concept_passages": len(cp), "co_occurs": sum(1 for n in co.values() if n >= 2)}


def pass_block_lookup(pass_block, pid):
    # pass_block is a list of (block_id, passage_id); build a dict once per call site
    if not hasattr(pass_block_lookup, "_cache") or pass_block_lookup._cache[0] is not pass_block:
        pass_block_lookup._cache = (pass_block, dict((p, b) for b, p in pass_block))
    return pass_block_lookup._cache[1].get(pid)


# --- the agent's memory database ---------------------------------------------------------------------------
def open_memory(path=MEMORY_DB):
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA_MEMORY)
    return conn


def attach_memory(index_conn, path=MEMORY_DB):
    """Attach the memory db to a read-only index connection as `mem` (created if absent)."""
    path = Path(path)
    if not path.exists():
        open_memory(path).close()
    index_conn.execute("ATTACH DATABASE ? AS mem", (str(path),))
    return index_conn


def add_tag(mem, tag, description="", aliases=(), created_by="agent"):
    tag = tag.strip().lower().replace(" ", "_")
    mem.execute("INSERT OR IGNORE INTO tags VALUES (?,?,?,?)", (tag, description, now(), created_by))
    mem.execute("INSERT OR REPLACE INTO tag_fts VALUES (?,?)", (tag, " ".join([tag.replace("_", " "), description] + list(aliases))))
    for a in aliases:
        mem.execute("INSERT OR IGNORE INTO tag_aliases VALUES (?,?)", (a.strip().lower(), tag))
    mem.commit()
    return tag


def tag_node(mem, node_kind, node_id, tag, weight=1.0, note="", created_by="agent"):
    tag = add_tag(mem, tag, created_by=created_by)
    mem.execute("INSERT OR REPLACE INTO node_tags VALUES (?,?,?,?,?,?,?)", (node_kind, node_id, tag, weight, note, now(), created_by))
    mem.commit()
    return tag


def resolve_tag(mem, word):
    word = word.strip().lower()
    row = mem.execute("SELECT tag FROM tag_aliases WHERE alias = ?", (word,)).fetchone()
    if row:
        return row[0]
    row = mem.execute("SELECT tag FROM tags WHERE tag = ?", (word.replace(" ", "_"),)).fetchone()
    if row:
        return row[0]
    row = mem.execute("SELECT tag FROM tag_fts WHERE tag_fts MATCH ? ORDER BY bm25(tag_fts) LIMIT 1", (_fts_phrase(word),)).fetchone()
    return row[0] if row else None


def record_usage(mem, run_id, action, nodes, context=None):
    """nodes: [(node_kind, node_id)]. Also updates used_with for every pair cited in the same call."""
    ts = now()
    ctx = json.dumps(context or {}, ensure_ascii=False)
    mem.executemany("INSERT INTO usage_events (at, run_id, action, node_kind, node_id, context) VALUES (?,?,?,?,?,?)",
                    [(ts, run_id, action, k, i, ctx) for k, i in nodes])
    uniq = sorted(set(nodes))
    for i, a in enumerate(uniq):
        for b in uniq[i + 1:]:
            mem.execute("INSERT INTO used_with VALUES (?,?,?,?,1,?) ON CONFLICT(a_kind, a_id, b_kind, b_id) DO UPDATE SET count = count + 1, last_at = excluded.last_at",
                        (a[0], a[1], b[0], b[1], ts))
    mem.commit()
    return len(nodes)


def record_cited(mem, run_id, refs, context=None):
    """One 'cited' event per resolved handbook passage an IR's authored text cites. refs: [(event_id, canonical_passage_id)]."""
    n = 0
    for event_id, pid in refs:
        ctx = dict(context or {})
        ctx["event_id"] = event_id
        n += record_usage(mem, run_id, "cited", [("passage", pid)], ctx)
    return n


def used_with(mem, node_kind, node_id, limit=10):
    rows = mem.execute("SELECT b_kind AS kind, b_id AS id, count FROM used_with WHERE a_kind = ? AND a_id = ? UNION ALL "
                       "SELECT a_kind, a_id, count FROM used_with WHERE b_kind = ? AND b_id = ? ORDER BY count DESC LIMIT ?",
                       (node_kind, node_id, node_kind, node_id, limit)).fetchall()
    return [dict(r) for r in rows]


def usage_stats(mem, node_kind=None, limit=20):
    sql = "SELECT node_kind, node_id, count(*) AS uses, max(at) AS last_at FROM usage_events "
    params = []
    if node_kind:
        sql += "WHERE node_kind = ? "
        params.append(node_kind)
    sql += "GROUP BY node_kind, node_id ORDER BY uses DESC, last_at DESC LIMIT ?"
    params.append(limit)
    return [dict(r) for r in mem.execute(sql, params)]


def set_summary(mem, node_kind, node_id, text, level="one_line", created_by="agent"):
    mem.execute("INSERT OR REPLACE INTO agent_summaries VALUES (?,?,?,?,?,?)", (node_kind, node_id, level, text.strip(), now(), created_by))
    mem.commit()


def add_concept(mem, concept_id, label, kind="concept", aliases=(), description="", created_by="agent"):
    mem.execute("INSERT OR REPLACE INTO agent_concepts VALUES (?,?,?,?,?,?,?)",
                (concept_id, label, kind, json.dumps(list(aliases)), description, now(), created_by))
    mem.commit()


def add_link(mem, from_kind, from_id, to_kind, to_id, relation, note="", created_by="agent"):
    mem.execute("INSERT OR REPLACE INTO agent_links VALUES (?,?,?,?,?,?,?,?)", (from_kind, from_id, to_kind, to_id, relation, note, now(), created_by))
    mem.commit()


SLOT_TIERS_FOR_LABELS = {"subject_anchor": 1, "primary_action": 1, "temporal_cadence": 2, "camera_optics": 2,
                         "environment": 3, "secondary_motion": 3, "lighting": 4, "material_shading": 4}


def set_label(mem, node_id, moment_type=None, slot_id=None, reason="", confidence=0.7, created_by="agent", node_kind="passage"):
    """A judged label with its evidence. reason is required (invariant 5: no silent labels)."""
    if not (reason or "").strip():
        raise ValueError("a judged label needs a reason")
    if moment_type is None and slot_id is None:
        raise ValueError("a judged label needs a moment_type or a slot_id ('none' records that no label applies)")
    tier = SLOT_TIERS_FOR_LABELS.get(slot_id) if slot_id and slot_id != "none" else None
    mem.execute("INSERT OR REPLACE INTO agent_labels VALUES (?,?,?,?,?,?,?,?,?)",
                (node_kind, node_id, moment_type, slot_id, tier, reason.strip(), float(confidence), now(), created_by))
    mem.commit()


def get_label(mem_or_conn, node_id, attached=False):
    sql = "SELECT moment_type, slot_id, intent_tier, reason, confidence FROM %sagent_labels WHERE node_kind = 'passage' AND node_id = ?" % ("mem." if attached else "")
    try:
        row = mem_or_conn.execute(sql, (node_id,)).fetchone()
    except sqlite3.OperationalError:
        return None
    return dict(zip(("moment_type", "slot_id", "intent_tier", "reason", "confidence"), row)) if row else None
