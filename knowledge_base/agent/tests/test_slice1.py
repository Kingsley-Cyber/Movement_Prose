import sys
import unittest
from pathlib import Path

BUNDLE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BUNDLE))

from agent import handbook as hb  # noqa: E402
from agent import query as q  # noqa: E402


class PureFunctions(unittest.TestCase):
    def test_long_prose_with_parentheses_is_quoted_and_capped(self):
        text = "Realistic strike spacing: one full arm's length (0.75-0.85m) for punches, " * 10
        expr = q.fts_query(text)
        self.assertNotIn("(0.75", expr)
        self.assertTrue(expr.startswith('"'))
        self.assertLessEqual(expr.count(" AND "), q.MAX_QUERY_WORDS)
        self.assertLessEqual(q.any_word_query(text).count(" OR "), q.MAX_QUERY_WORDS * 2)

    def test_fts_query_quotes_plain_text_and_passes_operators(self):
        self.assertEqual(q.fts_query("wind-up"), '"wind-up"')
        self.assertEqual(q.fts_query("contact hold"), '("contact hold") OR ("contact" AND "hold")')
        self.assertEqual(q.fts_query('"freeze frame" OR hitstop'), '"freeze frame" OR hitstop')

    def test_diversify_caps_and_counts(self):
        hits = [{"id": "p%d" % i, "block": b, "article": a} for i, (b, a) in enumerate(
            [("b1", "A"), ("b1", "A"), ("b2", "A"), ("b3", "A"), ("b4", "B"), ("b4", "B"), ("b5", "C")])]
        kept = q.diversify(hits, per_block=1, per_article=2)
        self.assertEqual([h["id"] for h in kept], ["p0", "p2", "p4", "p6"])
        self.assertEqual(kept[0]["more_in_block"], 1)
        self.assertEqual(kept[0]["more_in_article"], 1)   # p3 dropped by the article cap credits the first A hit
        self.assertEqual(kept[2]["more_in_block"], 1)

    def test_budget_trims_whole_hits(self):
        hits = [{"id": "x%d" % i, "sid": "a001#%04d" % i, "score": 1, "m": "impact/1", "s": "camera_optics/1", "line": "l" * 60, "cite": "c"} for i in range(6)]
        full = q.format_hits2(hits)
        self.assertGreater(len(full), 300)
        self.assertLessEqual(len(q.format_hits2(hits, budget=300)), 300)
        self.assertLessEqual(len(q.format_hits2(hits, budget=50)), 50)


@unittest.skipUnless(hb.DEFAULT_DB.exists(), "no built handbook index")
class RealIndex(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.conn = q.open_all()

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()

    def test_hyphen_query_no_longer_crashes(self):
        hits, _ = q.lookup2(self.conn, text="wind-up", limit=5, min_score=0)
        self.assertTrue(hits)

    def test_expansion_reaches_alias_siblings(self):
        raw, _ = q.lookup2(self.conn, text="freeze frame", limit=20, min_score=0, expand=False, diverse=False, rerank=False)
        expanded, concepts = q.lookup2(self.conn, text="freeze frame", limit=20, min_score=0, expand=True, diverse=False, rerank=False)
        self.assertIn("hit_stop", [c for c, _ in concepts])
        self.assertGreater(len(expanded), len(raw))
        self.assertTrue(any(h["via"].startswith("hit_stop:") and "freeze" not in h["via"] for h in expanded))

    def test_broad_aliases_are_not_expanded(self):
        spec = dict((a, n) for a, n, _ in q.specific_aliases(self.conn, "impact"))
        total = q._passage_total(self.conn)
        self.assertTrue(all(n <= 0.02 * total for n in spec.values()))
        self.assertNotIn("contact", spec)

    def test_hits_carry_snippet_terms_and_short_id(self):
        hits, _ = q.lookup2(self.conn, text="contact hold", limit=5, min_score=0)
        h = hits[0]
        self.assertTrue(h.get("snip"))
        self.assertIsInstance(h["terms"], list)
        self.assertRegex(h["sid"], r"^a\d{3}#\d{4}$")
        self.assertEqual(q.resolve_id(self.conn, h["sid"]), h["id"])

    def test_diversity_on_real_results(self):
        hits, _ = q.lookup2(self.conn, text="hold", limit=10, min_score=0, rerank=False)
        blocks = [h["block"] for h in hits]
        self.assertEqual(len(blocks), len(set(blocks)))

    def test_short_block_id_roundtrip(self):
        block = self.conn.execute("SELECT block_id FROM handbook_blocks LIMIT 1").fetchone()[0]
        self.assertEqual(q.resolve_id(self.conn, q.short_id(self.conn, block)), block)
        self.assertEqual(q.resolve_id(self.conn, "not-a-short-id"), "not-a-short-id")


if __name__ == "__main__":
    unittest.main()


@unittest.skipUnless(hb.DEFAULT_DB.exists(), "no built handbook index")
class Ask(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from agent import catalog as catalog_mod, policy as policy_mod, taste as taste_mod
        cls.conn = q.open_all()
        cls.cat, cls.pol, cls.tastes = catalog_mod.load_catalog(), policy_mod.Policy(), taste_mod.load_profiles()

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()

    def test_ask_resolves_concepts_directives_and_gaps(self):
        res = q.ask(self.conn, "one straight punch and a forearm block, camera locked on the contact", self.cat, self.pol, self.tastes, "raw street brawl")
        self.assertEqual(res["taste"], "raw_street_brawl")
        self.assertIn("forearm_block", [c["id"] for c in res["concepts"]])
        self.assertIn("aa_action_forearm_block", [d["id"] for d in res["directives"]])
        self.assertTrue(any(g["hits"] for g in res["groups"]))
        ids = [h["id"] for g in res["groups"] for h in g["hits"]]
        self.assertEqual(len(ids), len(set(ids)))

    def test_ask_reports_handbook_and_catalog_gaps(self):
        res = q.ask(self.conn, "hero slips a wide swing and lands a rising left hook to the solar plexus", self.cat, self.pol)
        self.assertIn("plexus", res["gaps"]["catalog"])
        self.assertTrue(res["moments"] or res["slots"] or res["concepts"])

    def test_format_ask_respects_budget(self):
        res = q.ask(self.conn, "slow motion impact with debris and a monochrome flash", self.cat, self.pol)
        text = q.format_ask(res, budget=1200)
        self.assertLessEqual(len(text), 1200 + 400)   # header is never trimmed; groups share the rest
        self.assertIn("ask:", text)
