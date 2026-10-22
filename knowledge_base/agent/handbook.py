"""Index the CPCS Domain Handbook (handbook.html) into SQLite: tree nodes, passages with lexical
moment/slot/tier labels, typed edges, FTS5, closed vocabularies, and the directive side."""
import hashlib
import json
import re
import sqlite3
from collections import OrderedDict
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

from . import BUNDLE_DIR, DATA_DIR, __version__

DEFAULT_DB = Path(BUNDLE_DIR) / "handbook_index.db"

MOMENT_ORDER = ["anticipation", "execution", "impact", "recoil", "follow_through", "recovery"]
MOMENT_EDGES = [("anticipation", "execution"), ("execution", "impact"), ("impact", "recoil"),
                ("impact", "follow_through"), ("recoil", "recovery"), ("follow_through", "recovery")]
SLOT_TIERS = OrderedDict([("subject_anchor", 1), ("primary_action", 1), ("temporal_cadence", 2), ("camera_optics", 2),
                          ("environment", 3), ("secondary_motion", 3), ("lighting", 4), ("material_shading", 4)])
TIER_NAMES = {1: "primary", 2: "secondary", 3: "tertiary", 4: "quaternary"}

MOMENT_TERMS = {
    "anticipation": ["anticipat", "wind-up", "windup", "wind up", "preparation", "preparatory", "pre-motion", "loading",
                     "load the", "coil", "chamber", "set-up", "setup", "backswing", "pre-tension", "telegraph", "crouch", "wary guard"],
    "execution": ["execution", "execute", "stroke", "accelerat", "initiation", "initiate", "strike path", "swing", "lunge",
                  "drive", "launch", "travel", "action phase", "main movement", "release", "burst", "smear", "flash step", "dash"],
    "impact": ["impact", "contact", "collision", "collide", "apex", "peak", "hit-stop", "hitstop", "hit stop", "clash",
               "connects", "freeze frame", "impact frame", "lands the", "blow lands"],
    "recoil": ["recoil", "reaction", "knockback", "knock-back", "stagger", "absorb", "displacement", "pushed back",
               "thrown back", "flinch", "rebound", "bounce back"],
    "follow_through": ["follow-through", "follow through", "followthrough", "overshoot", "momentum carries", "overlapping action",
                       "overlap", "drag", "lag", "trailing", "carry through", "continues past"],
    "recovery": ["recovery", "recover", "settle", "settling", "reset", "return to guard", "returns to", "rest state",
                 "dissipate", "stable state", "resting pose", "regain balance", "regroup", "end state"],
}
SLOT_TERMS = {
    "subject_anchor": ["identity", "silhouette", "proportion", "costume", "wardrobe", "character design", "consistency",
                       "anatomy", "model sheet", "limb count", "recognizable", "on-model", "off-model", "face"],
    "environment": ["environment", "background", "ground", "floor", "debris", "dust", "terrain", "surface", "parallax",
                    "world", "crater", "fracture", "rubble", "wall", "set dressing", "props"],
    "primary_action": ["biomechanic", "kinetic chain", "weight transfer", "hips", "pelvis", "stance", "footwork", "punch",
                       "kick", "block", "strike", "support leg", "center of mass", "torque", "rotation", "guard", "grapple", "throw"],
    "secondary_motion": ["secondary motion", "secondary action", "overlapping", "cloth", "hair", "cape", "fabric", "drag",
                         "follow-through", "effects", "shockwave", "speed lines", "smear", "particles", "spray", "splash", "trail"],
    "temporal_cadence": ["timing", "cadence", "fps", "frame", "on twos", "on ones", "on threes", "hold", "exposure", "spacing",
                         "tempo", "beat", "duration", "slow motion", "slow-motion", "time remap", "ramp", "seconds", "rhythm", "pacing"],
    "camera_optics": ["camera", "framing", "shot size", "lens", "focal", "pan ", "tilt", "dolly", "tracking", "angle",
                      "composition", "readability", "wide shot", "close-up", "medium shot", "orbit", "handheld", "zoom", "depth of field"],
    "lighting": ["lighting", "light", "shadow", "rim", "key light", "flash", "illuminat", "highlight", "glow", "backlight", "contrast"],
    "material_shading": ["shading", "cel", "ink", "render", "texture", "palette", "color", "colour", "style", "brush",
                         "outline", "flat color", "gradient", "grain", "paint", "line weight", "lineart"],
}
BLOCK_TAGS = {"p": "paragraph", "li": "list_item", "pre": "code", "tr": "table_row", "dt": "definition",
              "dd": "definition", "blockquote": "quote"}
HEADING_TAGS = ("h1", "h2", "h3", "h4", "h5", "h6")
CPCS_ID = re.compile(r"\bcpcs\.[a-z0-9_]+(?:\.[a-z0-9_]+)+")
SRC_ID = re.compile(r"\bSRC-\d{3}\b")
S_ID = re.compile(r"\bS\d{3}\b")
DEPENDENCY = re.compile(r"\b(requires|depends on|depends_on|prerequisites? (?:is|are|:)|conflicts? with|conflicts_with)\s+(.{3,100}?)(?:[.;:]|$)", re.I)
_WS = re.compile(r"\s+")


def _compile(terms):
    return [(t, re.compile(r"\b" + re.escape(t.strip()) + (r"" if t.endswith(" ") or not t[-1].isalnum() else r""), re.I)) for t in terms]


_MOMENT_RX = dict((k, _compile(v)) for k, v in MOMENT_TERMS.items())
_SLOT_RX = dict((k, _compile(v)) for k, v in SLOT_TERMS.items())


def classify(text, heading_path=""):
    sample = (heading_path + " \n " + text)

    def score(table):
        best, best_score, best_terms = None, 0, []
        for label, rxs in table.items():
            hits = [t for t, rx in rxs if rx.search(sample)]
            s = len(hits)
            if s > best_score:
                best, best_score, best_terms = label, s, hits
        return best, best_score, best_terms

    moment, ms, mt = score(_MOMENT_RX)
    slot, ss, st = score(_SLOT_RX)
    tier = SLOT_TIERS.get(slot) if slot else None
    return moment, ms, mt, slot, ss, st, tier, (TIER_NAMES.get(tier) if tier else None)


class _Parser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self, convert_charrefs=True)
        self.chapters, self.sections, self.articles, self.passages, self.links = [], [], [], [], []
        self.stack = []
        self.cur_chapter = self.cur_section = self.cur_article = None
        self.in_toc = 0
        self.heading = None
        self.block = None
        self.block_links = []
        self.banner = None
        self.heading_path = ["", "", "", ""]
        self.passage_ordinal = 0
        self.seen_article_ids = set()
        self.block_language = None

    @staticmethod
    def _classes(attrs):
        return (attrs.get("class") or "").split()

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "nav" and (a.get("id") == "toc" or self.in_toc):
            self.in_toc += 1
        if self.in_toc:
            self.stack.append(tag)
            return
        classes = self._classes(a)
        if tag == "section" and "chapter" in classes:
            self.cur_chapter = {"chapter_id": a.get("id"), "ordinal": len(self.chapters) + 1, "title": "", "domain": a.get("data-domain")}
            self.chapters.append(self.cur_chapter)
        elif tag == "section" and "section" in classes:
            self.cur_section = {"section_id": a.get("id"), "chapter_id": self.cur_chapter["chapter_id"] if self.cur_chapter else None,
                                "ordinal": len(self.sections) + 1, "title": "", "domain": a.get("data-domain")}
            self.sections.append(self.cur_section)
        elif tag == "article":
            aid = a.get("id") or "article-%d" % (len(self.articles) + 1)
            while aid in self.seen_article_ids:
                aid += "-dup"
            self.seen_article_ids.add(aid)
            self.cur_article = {"article_id": aid, "section_id": self.cur_section["section_id"] if self.cur_section else None,
                                "ordinal": len(self.articles) + 1, "title": "", "src": a.get("data-src"), "cpcs_id": a.get("data-cpcs-id"),
                                "kind": a.get("data-kind"), "epistemic": None, "words": None}
            self.articles.append(self.cur_article)
            self.heading_path = ["", "", "", ""]
            self.passage_ordinal = 0
        elif tag == "div" and "src-banner" in classes:
            self.banner = []
        elif tag in HEADING_TAGS and self.block is None:
            self.heading = (tag, [])
        elif tag in BLOCK_TAGS and self.block is None and self.cur_article is not None and self.banner is None:
            self.block = (tag, [], len(self.stack))
            self.block_links = []
            self.block_language = None
        elif tag == "code" and self.block is not None and self.block[0] == "pre":
            cls = (a.get("class") or "")
            self.block_language = cls.split("language-", 1)[1].split()[0] if "language-" in cls else "text"
        elif tag == "a" and self.block is not None and (a.get("href") or "").startswith("#"):
            self.block_links.append(a["href"][1:])
        elif tag in ("td", "th") and self.block is not None and self.block[1]:
            self.block[1].append(" | ")
        elif tag == "br" and self.block is not None:
            self.block[1].append(" ")
        self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag in self.stack:
            while self.stack:
                top = self.stack.pop()
                if top == tag:
                    break
        if tag == "nav" and self.in_toc:
            self.in_toc -= 1
            return
        if self.in_toc:
            return
        if self.heading and tag == self.heading[0]:
            text = _WS.sub(" ", "".join(self.heading[1])).strip()
            self._assign_heading(tag, text)
            self.heading = None
        elif self.block and tag == self.block[0] and len(self.stack) == self.block[2]:
            self._flush_block()
        elif tag == "div" and self.banner is not None:
            text = " ".join(self.banner)
            if self.cur_article is not None:
                m = re.search(r"words:\s*(\d+)", text)
                e = re.search(r"epistemic:\s*([A-Za-z_]+)", text)
                self.cur_article["words"] = int(m.group(1)) if m else None
                self.cur_article["epistemic"] = e.group(1) if e else None
            self.banner = None
        elif tag == "article":
            self.cur_article = None

    def _assign_heading(self, tag, text):
        if tag == "h1" and self.cur_chapter is not None and not self.cur_chapter["title"]:
            self.cur_chapter["title"] = text
        elif tag == "h2" and self.cur_section is not None and not self.cur_section["title"]:
            self.cur_section["title"] = text
        elif tag in ("h3", "h4", "h5", "h6"):
            level = ("h3", "h4", "h5", "h6").index(tag)
            if self.cur_article is not None and tag == "h3" and not self.cur_article["title"]:
                self.cur_article["title"] = text
            self.heading_path[level] = text
            for deeper in range(level + 1, 4):
                self.heading_path[deeper] = ""

    def _flush_block(self):
        tag, buffer, _ = self.block
        text = _WS.sub(" ", "".join(buffer)).strip() if tag != "pre" else "".join(buffer).strip()
        self.block = None
        if len(text) < 3 or self.cur_article is None:
            return
        self.passage_ordinal += 1
        passage_id = "%s#%04d" % (self.cur_article["article_id"], self.passage_ordinal)
        self.passages.append({"passage_id": passage_id, "article_id": self.cur_article["article_id"], "ordinal": self.passage_ordinal,
                              "kind": BLOCK_TAGS[tag], "heading_path": " > ".join(h for h in self.heading_path if h), "text": text,
                              "language": (self.block_language or "text") if tag == "pre" else None})
        for target in self.block_links:
            self.links.append((passage_id, target))
        self.block_links = []

    def handle_data(self, data):
        if self.in_toc:
            return
        if self.heading is not None:
            self.heading[1].append(data)
        elif self.banner is not None:
            self.banner.append(data)
        elif self.block is not None:
            self.block[1].append(data)


def parse_handbook(html_path):
    parser = _Parser()
    parser.feed(Path(html_path).read_text(encoding="utf-8", errors="replace"))
    parser.close()
    return parser


SCHEMA = """
CREATE TABLE handbook_meta (key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE handbook_chapters (chapter_id TEXT PRIMARY KEY, ordinal INTEGER, title TEXT, domain TEXT);
CREATE TABLE handbook_sections (section_id TEXT PRIMARY KEY, chapter_id TEXT, ordinal INTEGER, title TEXT, domain TEXT);
CREATE TABLE handbook_articles (article_id TEXT PRIMARY KEY, section_id TEXT, ordinal INTEGER, title TEXT, src TEXT, cpcs_id TEXT, kind TEXT, epistemic TEXT, words INTEGER);
CREATE TABLE handbook_passages (passage_id TEXT PRIMARY KEY, article_id TEXT, ordinal INTEGER, kind TEXT, heading_path TEXT, text TEXT, chars INTEGER, sha256 TEXT,
    moment_type TEXT, moment_score INTEGER, moment_terms TEXT, slot_id TEXT, slot_score INTEGER, slot_terms TEXT, intent_tier INTEGER, tier_name TEXT, language TEXT);
CREATE INDEX idx_hb_language ON handbook_passages(language);
CREATE INDEX idx_hb_lookup ON handbook_passages(moment_type, slot_id, intent_tier);
CREATE INDEX idx_hb_article ON handbook_passages(article_id, ordinal);
CREATE VIRTUAL TABLE handbook_fts USING fts5(passage_id UNINDEXED, text, heading_path, article_title, tokenize='porter unicode61');
CREATE TABLE handbook_edges (from_kind TEXT, from_id TEXT, to_kind TEXT, to_id TEXT, relation TEXT, evidence TEXT,
    PRIMARY KEY (from_kind, from_id, to_kind, to_id, relation));
CREATE INDEX idx_hb_edges_to ON handbook_edges(to_kind, to_id, relation);
CREATE TABLE moments (moment_type TEXT PRIMARY KEY, ordinal INTEGER);
CREATE TABLE moment_edges (from_moment TEXT, to_moment TEXT, PRIMARY KEY (from_moment, to_moment));
CREATE TABLE slots (slot_id TEXT PRIMARY KEY, ordinal INTEGER, intent_tier INTEGER, tier_name TEXT);
CREATE TABLE directive_requires (directive_id TEXT, token TEXT, satisfier_directive_id TEXT);
CREATE TABLE directive_conflicts (directive_id TEXT, other_id TEXT, PRIMARY KEY (directive_id, other_id));
CREATE TABLE directive_passages (directive_id TEXT, passage_id TEXT, score INTEGER, PRIMARY KEY (directive_id, passage_id));
CREATE TABLE taste_profiles (taste_id TEXT PRIMARY KEY, human_vibe_tags TEXT, laban_effort_preset TEXT, default_cadence TEXT, camera_taste TEXT, shading_taste TEXT, sub_genre_hint TEXT, evidence_status TEXT);
CREATE TABLE taste_profile_directives (taste_id TEXT, slot_id TEXT, directive_id TEXT, mark TEXT, PRIMARY KEY (taste_id, directive_id));
"""


def build_index(html_path, db_path=DEFAULT_DB, catalog=None, policy=None, taste_path=None, memory_path=None):
    html_path, db_path = Path(html_path), Path(db_path)
    raw = html_path.read_bytes()
    parsed = parse_handbook(html_path)
    if db_path.exists():
        db_path.unlink()
    conn = sqlite3.connect(str(db_path))
    conn.executescript(SCHEMA)
    conn.executemany("INSERT INTO handbook_chapters VALUES (?,?,?,?)", [(c["chapter_id"], c["ordinal"], c["title"], c["domain"]) for c in parsed.chapters])
    conn.executemany("INSERT INTO handbook_sections VALUES (?,?,?,?,?)", [(s["section_id"], s["chapter_id"], s["ordinal"], s["title"], s["domain"]) for s in parsed.sections])
    article_rows = []
    for a in parsed.articles:
        aid = a["_id"] = a["article_id"]
        article_rows.append((aid, a["section_id"], a["ordinal"], a["title"], a["src"], a["cpcs_id"], a["kind"], a["epistemic"], a["words"]))
    conn.executemany("INSERT INTO handbook_articles VALUES (?,?,?,?,?,?,?,?,?)", article_rows)
    article_title = dict((a["_id"], a["title"]) for a in parsed.articles)
    cpcs_to_article = dict((a["cpcs_id"], a["_id"]) for a in parsed.articles if a["cpcs_id"])

    passage_rows, fts_rows, edges = [], [], []
    prev_by_article = {}
    for p in parsed.passages:
        aid, pid = p["article_id"], p["passage_id"]
        moment, ms, mt, slot, ss, st, tier, tier_name = classify(p["text"], p["heading_path"])
        sha = hashlib.sha256(p["text"].encode("utf-8")).hexdigest()
        passage_rows.append((pid, aid, p["ordinal"], p["kind"], p["heading_path"], p["text"], len(p["text"]), sha,
                             moment, ms, json.dumps(mt), slot, ss, json.dumps(st), tier, tier_name, p.get("language")))
        fts_rows.append((pid, p["text"], p["heading_path"], article_title.get(aid, "")))
        edges.append(("article", aid, "passage", pid, "contains", None))
        if aid in prev_by_article:
            edges.append(("passage", prev_by_article[aid], "passage", pid, "next", None))
        prev_by_article[aid] = pid
        for card in sorted(set(CPCS_ID.findall(p["text"]))):
            target_kind, target = ("article", cpcs_to_article[card]) if card in cpcs_to_article else ("card", card)
            edges.append(("passage", pid, target_kind, target, "cites_card", card))
        for src in sorted(set(SRC_ID.findall(p["text"])) | set(S_ID.findall(p["text"]))):
            edges.append(("passage", pid, "source", src, "cites_source", None))
        for m in DEPENDENCY.finditer(p["text"]):
            verb = m.group(1).lower().replace("_", " ")
            relation = "conflicts_with" if verb.startswith("conflict") else ("depends_on" if verb.startswith("depends") else "requires")
            edges.append(("passage", pid, "clause", m.group(2).strip()[:100], relation, m.group(0)[:200]))
    for pid, target in parsed.links:
        edges.append(("passage", pid, "anchor", target, "links_to", "#" + target))
    for s in parsed.sections:
        if s["chapter_id"]:
            edges.append(("chapter", s["chapter_id"], "section", s["section_id"], "contains", None))
    for a in parsed.articles:
        if a["section_id"]:
            edges.append(("section", a["section_id"], "article", a["_id"], "contains", None))
    conn.executemany("INSERT INTO handbook_passages VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", passage_rows)
    conn.executemany("INSERT INTO handbook_fts VALUES (?,?,?,?)", fts_rows)
    conn.executemany("INSERT OR IGNORE INTO handbook_edges VALUES (?,?,?,?,?,?)", edges)
    conn.executemany("INSERT INTO moments VALUES (?,?)", [(m, i + 1) for i, m in enumerate(MOMENT_ORDER)])
    conn.executemany("INSERT INTO moment_edges VALUES (?,?)", MOMENT_EDGES)
    conn.executemany("INSERT INTO slots VALUES (?,?,?,?)", [(s, i + 1, t, TIER_NAMES[t]) for i, (s, t) in enumerate(SLOT_TIERS.items())])

    if catalog is not None and policy is not None:
        req_rows, conflict_rows, dp_rows = [], [], []
        for did in catalog.ids:
            for token in catalog.requires(did):
                sats = policy.satisfiers(token)
                if sats:
                    for s in sats:
                        req_rows.append((did, token, s))
                else:
                    req_rows.append((did, token, None))
            for other in catalog.conflicts(did):
                conflict_rows.append((did, other))
            d = catalog.get(did)
            for row in conn.execute("SELECT passage_id, moment_score + slot_score FROM handbook_passages WHERE moment_type=? AND slot_id=? "
                                    "ORDER BY moment_score + slot_score DESC, chars ASC LIMIT 10", (d.moment_type, d.slot_id)):
                dp_rows.append((did, row[0], row[1]))
        conn.executemany("INSERT INTO directive_requires VALUES (?,?,?)", req_rows)
        conn.executemany("INSERT OR IGNORE INTO directive_conflicts VALUES (?,?)", conflict_rows)
        conn.executemany("INSERT OR IGNORE INTO directive_passages VALUES (?,?,?)", dp_rows)
    taste_path = Path(taste_path) if taste_path else Path(DATA_DIR) / "taste_profiles.json"
    if taste_path.exists():
        profiles = json.loads(taste_path.read_text(encoding="utf-8"))["profiles"]
        t_rows, td_rows = [], []
        for p in profiles:
            q = p.get("effort_quality", {})
            preset = "_".join(x for x in (q.get("space"), q.get("weight"), q.get("time"), q.get("flow")) if x)
            pref = p.get("preferred_directives", {})
            first = lambda slot: (pref.get(slot) or [None])[0]
            t_rows.append((p["taste_id"], ", ".join(p.get("human_vibe_tags", [])), preset, first("temporal_cadence"), first("camera_optics"),
                           first("material_shading"), p.get("sub_genre_hint"), p.get("evidence_status")))
            for slot, ids in pref.items():
                for did in ids:
                    td_rows.append((p["taste_id"], slot, did, "preferred"))
            for did in p.get("avoid_directives", []):
                td_rows.append((p["taste_id"], None, did, "avoid"))
        conn.executemany("INSERT INTO taste_profiles VALUES (?,?,?,?,?,?,?,?)", t_rows)
        conn.executemany("INSERT OR IGNORE INTO taste_profile_directives VALUES (?,?,?,?)", td_rows)
    meta = [("source_path", str(html_path)), ("source_sha256", hashlib.sha256(raw).hexdigest()), ("source_bytes", str(len(raw))),
            ("built_at", datetime.now(timezone.utc).isoformat()), ("agent_version", __version__),
            ("chapters", str(len(parsed.chapters))), ("sections", str(len(parsed.sections))), ("articles", str(len(parsed.articles))),
            ("passages", str(len(passage_rows))), ("edges", str(conn.execute("SELECT count(*) FROM handbook_edges").fetchone()[0])),
            ("labelling", "lexical term lists in agent/handbook.py; scores are term-hit counts, not semantic judgments")]
    conn.executemany("INSERT INTO handbook_meta VALUES (?,?)", meta)
    conn.commit()
    from .knowledge import build_layers, load_agent_concepts, MEMORY_DB
    layer_stats = build_layers(conn, catalog=catalog, agent_concepts=load_agent_concepts(memory_path or MEMORY_DB))
    conn.executemany("INSERT OR REPLACE INTO handbook_meta VALUES (?,?)", [(k, str(v)) for k, v in layer_stats.items()])
    conn.commit()
    conn.close()
    return db_path


# --- queries ---------------------------------------------------------------
class HandbookError(RuntimeError):
    pass


def connect(db_path=DEFAULT_DB):
    db_path = Path(db_path)
    if not db_path.exists():
        raise HandbookError("no handbook index at %s; run: python3 -m agent index-handbook <handbook.html>" % db_path)
    conn = sqlite3.connect(db_path.resolve().as_uri() + "?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def meta(conn):
    return dict(conn.execute("SELECT key, value FROM handbook_meta").fetchall())


_SELECT = ("SELECT p.passage_id, p.article_id, p.ordinal, p.kind, p.heading_path, p.text, p.chars, p.moment_type, p.moment_score, "
           "p.moment_terms, p.slot_id, p.slot_score, p.slot_terms, p.intent_tier, p.tier_name, a.title AS article_title, a.src, a.cpcs_id, "
           "a.kind AS article_kind, a.epistemic FROM handbook_passages p JOIN handbook_articles a ON a.article_id = p.article_id ")


def lookup(conn, moment=None, slot=None, tier=None, text=None, min_score=1, limit=10, kinds=None):
    where, params = [], []
    if moment:
        where.append("p.moment_type = ? AND p.moment_score >= ?")
        params += [moment, min_score]
    if slot:
        where.append("p.slot_id = ? AND p.slot_score >= ?")
        params += [slot, min_score]
    if tier:
        where.append("p.intent_tier = ?")
        params.append(int(tier))
    if kinds:
        where.append("p.kind IN (%s)" % ",".join("?" * len(kinds)))
        params += list(kinds)
    if text:
        sql = (_SELECT.replace("SELECT p.passage_id", "SELECT snippet(handbook_fts, 1, '[', ']', '…', 14) AS snip, bm25(handbook_fts) AS bm, p.passage_id", 1)
               + "JOIN handbook_fts ON handbook_fts.passage_id = p.passage_id WHERE handbook_fts MATCH ?")
        params = [text] + params
        if where:
            sql += " AND " + " AND ".join(where)
        sql += " ORDER BY bm25(handbook_fts) LIMIT ?"
    else:
        # length-penalised rank: term hits per passage grow with length, so long templates would otherwise win
        sql = _SELECT + ("WHERE " + " AND ".join(where) if where else "") + " ORDER BY (p.moment_score + p.slot_score) * 1.0 / (1.0 + p.chars / 400.0) DESC, p.chars ASC LIMIT ?"
    params.append(int(limit))
    return [dict(r) for r in conn.execute(sql, params)]


def get_passage(conn, passage_id):
    row = conn.execute(_SELECT + "WHERE p.passage_id = ?", (passage_id,)).fetchone()
    return dict(row) if row else None


def lineage(conn, passage_id):
    row = conn.execute(
        "SELECT c.chapter_id, c.title AS chapter, s.section_id, s.title AS section, a.article_id, a.title AS article, a.src, a.cpcs_id, "
        "a.kind, a.epistemic, p.heading_path FROM handbook_passages p JOIN handbook_articles a ON a.article_id = p.article_id "
        "LEFT JOIN handbook_sections s ON s.section_id = a.section_id LEFT JOIN handbook_chapters c ON c.chapter_id = s.chapter_id "
        "WHERE p.passage_id = ?", (passage_id,)).fetchone()
    return dict(row) if row else None


def neighbors(conn, passage_id):
    prev = conn.execute("SELECT from_id FROM handbook_edges WHERE to_id = ? AND relation = 'next' AND to_kind = 'passage'", (passage_id,)).fetchone()
    nxt = conn.execute("SELECT to_id FROM handbook_edges WHERE from_id = ? AND relation = 'next' AND from_kind = 'passage'", (passage_id,)).fetchone()
    return {"prev": prev[0] if prev else None, "next": nxt[0] if nxt else None}


def edges_from(conn, passage_id, relation=None):
    sql = "SELECT * FROM handbook_edges WHERE from_kind = 'passage' AND from_id = ?"
    params = [passage_id]
    if relation:
        sql += " AND relation = ?"
        params.append(relation)
    return [dict(r) for r in conn.execute(sql, params)]


def phase_walk(conn, slot, start="anticipation", per_moment=3, min_score=1):
    rows = conn.execute(
        "WITH RECURSIVE walk(m, depth) AS (SELECT ?, 0 UNION ALL SELECT e.to_moment, depth + 1 FROM moment_edges e JOIN walk ON e.from_moment = walk.m) "
        "SELECT DISTINCT m, min(depth) AS d FROM walk GROUP BY m ORDER BY d", (start,)).fetchall()
    out = OrderedDict()
    for r in rows:
        out[r["m"]] = lookup(conn, moment=r["m"], slot=slot, min_score=min_score, limit=per_moment)
    return out


def dependency_chain(conn, directive_id):
    rows = conn.execute("SELECT r.token, r.satisfier_directive_id, dp.passage_id, dp.score FROM directive_requires r "
                        "LEFT JOIN directive_passages dp ON dp.directive_id = r.satisfier_directive_id WHERE r.directive_id = ? "
                        "ORDER BY r.token, dp.score DESC", (directive_id,)).fetchall()
    return [dict(r) for r in rows]


def cite(row):
    return "%s · %s · %s · %s" % (row.get("cpcs_id") or row.get("article_id"), row.get("src") or "", row.get("heading_path") or row.get("article_title") or "", row["passage_id"])


def excerpt(row, n=160):
    t = _WS.sub(" ", row["text"])
    return t if len(t) <= n else t[: n - 1] + "…"


def specimens(conn, language=None, text=None, heading=None, limit=20):
    """Typed code blocks (yaml/json/xml/text…): the handbook's schemas and templates, by language, text and heading."""
    where, params = ["p.kind = 'code'"], []
    if language:
        where.append("p.language = ?")
        params.append(language)
    if heading:
        where.append("p.heading_path LIKE ?")
        params.append("%" + heading + "%")
    if text:
        sql = (_SELECT.replace("SELECT p.passage_id", "SELECT p.language, p.passage_id", 1) + "JOIN handbook_fts ON handbook_fts.passage_id = p.passage_id WHERE handbook_fts MATCH ? AND "
               + " AND ".join(where) + " ORDER BY bm25(handbook_fts) LIMIT ?")
        params = [text] + params + [limit]
    else:
        sql = _SELECT.replace("SELECT p.passage_id", "SELECT p.language, p.passage_id", 1) + "WHERE " + " AND ".join(where) + " ORDER BY p.chars DESC LIMIT ?"
        params = params + [limit]
    return [dict(r) for r in conn.execute(sql, params)]
