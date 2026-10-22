import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

BUNDLE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BUNDLE))

from agent import catalog as catalog_mod  # noqa: E402
from agent import check as check_mod  # noqa: E402
from agent import emit as emit_mod  # noqa: E402
from agent import engines as eng  # noqa: E402
from agent import handbook as hb  # noqa: E402
from agent import knowledge as kn  # noqa: E402
from agent import policy as policy_mod  # noqa: E402
from agent import query as q  # noqa: E402
from agent import taste as taste_mod  # noqa: E402
from agent.ir import IR, Authored, Clip, Event, Selection  # noqa: E402

CAT = catalog_mod.load_catalog()
POL = policy_mod.Policy()
ENG = eng.load_engine_profiles()
TASTE = taste_mod.load_profiles()

SYNTHETIC = """<html><body><nav id="toc"><h1>Nav</h1><ol><li><a href="#ch-01">skip me</a></li></ol></nav>
<main>
<section class="chapter" id="ch-01" data-domain="motion"><h1>01. Motion</h1>
<section class="section" id="ch-01-beats" data-domain="motion.beats"><h2>Beats</h2>
<article class="source" id="src-a" data-src="a.md" data-cpcs-id="cpcs.test.a" data-kind="doctrine">
<div class="src-banner"><strong>A</strong><br>src: <a href="#">a.md</a> · words: 120 · id: cpcs.test.a · kind: doctrine · epistemic: AUTHORED</div>
<h3>Article A</h3>
<p>Hold the contact drawing for a brief beat at the impact, then release into recoil. This requires a clear contact point.</p>
<h4>Timing</h4>
<ul><li>Use held drawings on twos during the windup and anticipation.</li><li>See cpcs.test.b and SRC-004 §7 for the hold rule.</li></ul>
<table><tr><th>Beat</th><th>Meaning</th></tr><tr><td>Anticipation</td><td>The pre-motion cue</td></tr></table>
<pre><code>timing: on_twos</code></pre>
<p>Camera holds locked on the impact for readability. <a href="#src-b">see B</a></p>
</article>
<article class="source" id="src-b" data-src="b.md" data-cpcs-id="cpcs.test.b" data-kind="contract">
<div class="src-banner">words: 10 · epistemic: SOURCE_EVIDENCE</div>
<h3>Article B</h3>
<p>Hold the contact drawing for a brief beat at the impact, then release into recoil. This requires a clear contact point.</p>
<p>Recovery: the fighter returns to guard and settles the cloth.</p>
</article>
<article class="source" id="src-b" data-src="b2.md" data-kind="contract"><h3>Dup</h3><p>Duplicate id article paragraph about hard shadow and rim light.</p></article>
</section></section></main></body></html>
"""


class SyntheticIndex(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        root = Path(cls.tmp.name)
        cls.html = root / "hb.html"
        cls.html.write_text(SYNTHETIC, encoding="utf-8")
        cls.db = root / "index.db"
        cls.mem = root / "memory.db"
        hb.build_index(cls.html, cls.db, catalog=CAT, policy=POL, memory_path=cls.mem)   # isolated from the real agent_memory.db
        cls.conn = q.open_all(cls.db, cls.mem)

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()
        cls.tmp.cleanup()

    def test_tree_and_unique_article_ids(self):
        m = hb.meta(self.conn)
        self.assertEqual((m["chapters"], m["sections"], m["articles"]), ("1", "1", "3"))
        ids = [r[0] for r in self.conn.execute("SELECT article_id FROM handbook_articles ORDER BY ordinal")]
        self.assertEqual(ids, ["src-a", "src-b", "src-b-dup"])
        self.assertEqual(m["source_sha256"], hashlib.sha256(self.html.read_bytes()).hexdigest())
        art = dict(self.conn.execute("SELECT * FROM handbook_articles WHERE article_id = 'src-a'").fetchone())
        self.assertEqual((art["title"], art["words"], art["epistemic"], art["cpcs_id"]), ("Article A", 120, "AUTHORED", "cpcs.test.a"))

    def test_passages_kinds_and_toc_skipped(self):
        kinds = dict(self.conn.execute("SELECT kind, count(*) FROM handbook_passages GROUP BY kind").fetchall())
        self.assertEqual(kinds.get("code"), 1)
        self.assertEqual(kinds.get("table_row"), 2)
        self.assertGreaterEqual(kinds.get("list_item", 0), 2)
        self.assertIsNone(self.conn.execute("SELECT 1 FROM handbook_passages WHERE text LIKE '%skip me%'").fetchone())
        ids = [r[0] for r in self.conn.execute("SELECT passage_id FROM handbook_passages")]
        self.assertEqual(len(ids), len(set(ids)))

    def test_labels_and_lookup(self):
        row = self.conn.execute("SELECT moment_type, slot_id, intent_tier, tier_name FROM handbook_passages WHERE passage_id = 'src-a#0001'").fetchone()
        self.assertEqual(row[0], "impact")
        self.assertEqual(row[1], "temporal_cadence")
        self.assertEqual((row[2], row[3]), (2, "secondary"))
        hits = q.lookup(self.conn, moment="impact", min_score=1, limit=5)
        self.assertIn("src-a#0001", [h["id"] for h in hits])
        self.assertNotIn("src-b#0001", [h["id"] for h in hits])  # duplicate text is deduped away
        fts = q.lookup(self.conn, text="contact drawing", min_score=0, limit=5)
        self.assertTrue(fts and fts[0]["id"].startswith("src-"))

    def test_edges(self):
        rel = dict(self.conn.execute("SELECT relation, count(*) FROM handbook_edges GROUP BY relation").fetchall())
        for r in ("contains", "next", "links_to", "cites_card", "cites_source", "requires", "same_text"):
            self.assertIn(r, rel, r)
        card = self.conn.execute("SELECT to_kind, to_id FROM handbook_edges WHERE relation = 'cites_card'").fetchone()
        self.assertEqual(tuple(card), ("article", "src-b"))
        req = self.conn.execute("SELECT evidence FROM handbook_edges WHERE relation = 'requires' LIMIT 1").fetchone()[0]
        self.assertIn("requires a clear contact point", req)
        self.assertEqual(self.conn.execute("SELECT to_id FROM handbook_edges WHERE relation = 'links_to'").fetchone()[0], "src-b")

    def test_lineage_neighbors_walk(self):
        lin = hb.lineage(self.conn, "src-a#0002")
        self.assertEqual((lin["chapter_id"], lin["section_id"], lin["article_id"], lin["src"]), ("ch-01", "ch-01-beats", "src-a", "a.md"))
        self.assertEqual(hb.neighbors(self.conn, "src-a#0002"), {"prev": "src-a#0001", "next": "src-a#0003"})
        walk = hb.phase_walk(self.conn, "temporal_cadence", per_moment=2)
        keys = list(walk)
        self.assertEqual(set(keys), set(hb.MOMENT_ORDER))
        self.assertEqual((keys[0], keys[-1]), ("anticipation", "recovery"))

    def test_vocab_and_directive_side(self):
        self.assertEqual(self.conn.execute("SELECT count(*) FROM moments").fetchone()[0], 6)
        self.assertEqual(dict(self.conn.execute("SELECT slot_id, intent_tier FROM slots").fetchall())["camera_optics"], 2)
        self.assertEqual(self.conn.execute("SELECT count(*) FROM taste_profiles").fetchone()[0], 3)
        self.assertGreater(self.conn.execute("SELECT count(*) FROM taste_profile_directives").fetchone()[0], 100)
        self.assertEqual(self.conn.execute("SELECT satisfier_directive_id FROM directive_requires WHERE directive_id = 'aa_env_yutapon_cubes'").fetchone()[0], "aa_env_radial_fracture")
        self.assertIn(("aa_time_contact_hitstop", "aa_camera_crash_zoom"), set(tuple(r) for r in self.conn.execute("SELECT directive_id, other_id FROM directive_conflicts")))

    def test_knowledge_layers(self):
        self.assertGreaterEqual(self.conn.execute("SELECT count(*) FROM handbook_blocks").fetchone()[0], 3)
        blk = self.conn.execute("SELECT block_id FROM handbook_passages WHERE passage_id = 'src-a#0002'").fetchone()[0]
        self.assertTrue(blk.startswith("src-a/b"))
        for kind in ("passage", "block", "article", "section", "chapter"):
            self.assertTrue(self.conn.execute("SELECT 1 FROM summaries WHERE node_kind = ? LIMIT 1", (kind,)).fetchone(), kind)
        self.assertEqual(self.conn.execute("SELECT count(*) FROM concepts").fetchone()[0], len(kn.SEED_CONCEPTS) + 64)
        on_twos = [r[0] for r in self.conn.execute("SELECT passage_id FROM concept_passages WHERE concept_id = 'on_twos'")]
        self.assertIn("src-a#0002", on_twos)
        impl = set(r[0] for r in self.conn.execute("SELECT directive_id FROM concept_directives WHERE concept_id = 'hit_stop' AND relation = 'implemented_by'"))
        self.assertIn("aa_time_contact_hitstop", impl)
        self.assertEqual(self.conn.execute("SELECT count(*) FROM handbook_edges WHERE relation = 'same_text'").fetchone()[0], 1)

    def test_query_layer(self):
        res = q.find(self.conn, "contact drawing")
        self.assertTrue(res["passages"])
        self.assertTrue(any(c["id"] == "contact_contract" for c in q.find(self.conn, "contact point")["concepts"]))
        rd = q.read(self.conn, "article", "src-a", max_chars=80)
        self.assertTrue(rd["truncated"] and rd["chars"] > 80 and "## Article A > Timing" in q.read(self.conn, "article", "src-a")["text"])
        self.assertEqual([o["id"] for o in q.outline(self.conn)], ["ch-01"])
        self.assertEqual([o["id"] for o in q.outline(self.conn, "chapter", "ch-01")], ["ch-01-beats"])
        self.assertEqual([o["id"] for o in q.outline(self.conn, "section", "ch-01-beats")], ["src-a", "src-b", "src-b-dup"])
        c = q.concept(self.conn, "on_twos")
        self.assertEqual(c["label"], "Exposure on twos")
        near = q.near(self.conn, "src-a#0002")
        self.assertEqual(near["next"], "src-a#0003")
        self.assertIn("on_twos", [x["id"] for x in near["concepts"]])

    def test_memory_tags_usage_summaries(self):
        mem = kn.open_memory(self.mem)
        tag = kn.tag_node(mem, "passage", "src-a#0001", "Impact Readability", note="hold")
        self.assertEqual(tag, "impact_readability")
        kn.add_tag(mem, "hold_rules", "rules about holds", aliases=["holds"])
        self.assertEqual(kn.resolve_tag(mem, "holds"), "hold_rules")
        kn.record_usage(mem, "run_x", "emitted", [("passage", "src-a#0001"), ("directive", "aa_time_contact_hitstop"), ("concept", "hit_stop")])
        kn.record_usage(mem, "run_y", "emitted", [("passage", "src-a#0001"), ("directive", "aa_time_contact_hitstop")])
        uw = kn.used_with(mem, "passage", "src-a#0001")
        self.assertEqual(uw[0]["id"], "aa_time_contact_hitstop")
        self.assertEqual(uw[0]["count"], 2)
        self.assertEqual(kn.usage_stats(mem)[0]["uses"], 2)
        kn.set_summary(mem, "passage", "src-a#0001", "agent line")
        mem.close()
        conn = q.open_all(self.db, self.mem)
        self.assertEqual(q.summary_of(conn, "passage", "src-a#0001"), "agent line")
        self.assertEqual(q.near(conn, "src-a#0001")["tags"], ["impact_readability"])
        conn.close()


@unittest.skipUnless(hb.DEFAULT_DB.exists(), "no built handbook index")
class RealIndex(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.conn = hb.connect(hb.DEFAULT_DB)  # deliberately without the memory db: the query layer must tolerate that

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()

    def test_meta_matches_source(self):
        m = hb.meta(self.conn)
        src = Path(m["source_path"])
        if src.exists():
            self.assertEqual(m["source_sha256"], hashlib.sha256(src.read_bytes()).hexdigest())
        self.assertGreater(int(m["passages"]), 10000)
        self.assertGreater(int(m["concept_passages"]), 1000)

    def test_hit_stop_concept_and_lookup(self):
        c = q.concept(self.conn, "hit_stop")
        self.assertIn("aa_time_contact_hitstop", [d["id"] for d in c["directives"]])
        hits = q.lookup(self.conn, moment="impact", slot="temporal_cadence", min_score=2, limit=5)
        self.assertTrue(hits)
        self.assertTrue(all(h["pkind"] != "code" for h in hits))

    def test_handbook_refs_through_check_and_receipt(self):
        pid = q.lookup(self.conn, moment="impact", slot="temporal_cadence", min_score=2, limit=1)[0]["id"]
        ent = {"A": "A, the fighter in the red jacket", "B": "B, the fighter in the blue jacket"}

        def make(refs):
            return IR(request="t", scene_context="courtyard", entities=ent, clip=Clip(24, 0.5, 12),
                      events=[Event(event_id="e1", actor_id="A", target_id="B", moment_type="execution", start_frame=0, end_frame=12)],
                      selections=[Selection(directive_id="aa_action_hip_led_punch", event_id="e1", actor_id="A", target_id="B", start_frame=0, end_frame=12)],
                      authored=[Authored(event_id="e1", slot_id="secondary_motion", text="The hem lags.", clause="PERFORMANCE", handbook_refs=refs)])

        bad = [f for f in check_mod.check_ir(make(["nope#0001"]), CAT, POL, ENG, TASTE, handbook_conn=self.conn) if f.level == "error"]
        self.assertIn("HANDBOOK_REF_UNKNOWN", [f.code for f in bad])
        good = [f for f in check_mod.check_ir(make([pid]), CAT, POL, ENG, TASTE, handbook_conn=self.conn) if f.level == "error"]
        self.assertEqual(good, [])
        res = emit_mod.emit(make([pid]), CAT, POL, ENG["generic_web_ui"], handbook_conn=self.conn)
        ref = res.receipt["authored"][0]["handbook_refs"][0]
        self.assertEqual(ref["passage_id"], pid)
        self.assertTrue(ref.get("cite"))


if __name__ == "__main__":
    unittest.main()
