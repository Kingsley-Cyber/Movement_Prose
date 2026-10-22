import sys
import tempfile
import time
import unittest
from pathlib import Path

BUNDLE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BUNDLE))

from agent import discover as disc  # noqa: E402
from agent import handbook as hb  # noqa: E402
from agent import knowledge as kn  # noqa: E402
from agent import query as q  # noqa: E402


@unittest.skipUnless(hb.DEFAULT_DB.exists(), "no built handbook index")
class Swanson(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.conn = q.open_all()
        cls.seed = cls.conn.execute("SELECT p.passage_id FROM handbook_fts f JOIN handbook_passages p ON p.passage_id = f.passage_id "
                                    "WHERE handbook_fts MATCH '\"floaty\"' AND p.kind = 'paragraph' ORDER BY bm25(handbook_fts) LIMIT 1").fetchone()[0]

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()

    def test_bridges_respect_constraints(self):
        t0 = time.time()
        hyps = disc.bridges(self.conn, self.seed, limit=25)
        self.assertLess(time.time() - t0, 3.0)
        self.assertTrue(hyps)
        phase = set(r[0] for r in self.conn.execute("SELECT concept_id FROM concepts WHERE kind NOT IN ('mechanism','technique')"))
        a = hb.get_passage(self.conn, self.seed)
        for score, cid, c_id, row, cross, a_alias, c_alias in hyps:
            self.assertNotIn(cid, phase)
            self.assertGreaterEqual(row["chars"], 80)
            self.assertNotEqual(row["article_id"], a["article_id"])
            self.assertIn(row["kind"], disc.CURE_KINDS)
        self.assertTrue(any(h[4] for h in hyps), "at least one cross-chapter bridge")
        self.assertEqual([h[0] for h in hyps], sorted((h[0] for h in hyps), reverse=True))

    def test_queue_resolve_roundtrip(self):
        hyps = disc.bridges(self.conn, self.seed, limit=3)
        with tempfile.TemporaryDirectory() as d:
            mem = kn.open_memory(Path(d) / "m.db")
            n = disc.enqueue(mem, self.seed, hyps)
            self.assertEqual(n, len(hyps))
            self.assertEqual(disc.enqueue(mem, self.seed, hyps), 0)   # idempotent
            row = disc.pending(mem)[0]
            self.assertEqual(disc.resolve(mem, row["id"], "compensates_for", "test"), "accepted")
            edge = mem.execute("SELECT relation, note FROM agent_links WHERE from_id = ? AND to_id = ?", (row["a_id"], row["c_id"])).fetchone()
            self.assertEqual(edge[0], "compensates_for")
            self.assertIn(row["b_concept"], edge[1])
            row2 = disc.pending(mem)
            if row2:
                self.assertEqual(disc.resolve(mem, row2[0]["id"], "unrelated"), "rejected")
            with self.assertRaises(ValueError):
                disc.resolve(mem, row["id"], "causes")
            mem.close()

    def test_ask_discover_group_is_outside_top_k(self):
        from agent import catalog as catalog_mod, policy as policy_mod
        cat, pol = catalog_mod.load_catalog(), policy_mod.Policy()
        plain = q.ask(self.conn, "floaty deceleration", cat, pol)
        with_b = q.ask(self.conn, "floaty deceleration", cat, pol, discover=2)
        self.assertEqual([g["name"] for g in plain["groups"]], [g["name"] for g in with_b["groups"] if g["name"] != "bridges"])
        bridges = [g for g in with_b["groups"] if g["name"] == "bridges"]
        self.assertEqual(len(bridges), 1)
        self.assertLessEqual(len(bridges[0]["hits"]), 2)


if __name__ == "__main__":
    unittest.main()
