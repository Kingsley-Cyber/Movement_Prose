import sys
import unittest
from pathlib import Path

BUNDLE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BUNDLE))

from agent import handbook as hb  # noqa: E402
from agent import query as q  # noqa: E402


def H(i, block, article, via, sbase):
    return {"id": "p%d" % i, "sid": "a%03d#%04d" % (article, i), "block": block, "article": "A%d" % article, "via": via, "sbase": sbase}


class Allocate(unittest.TestCase):
    def hits(self):
        return [H(1, "b1", 1, "hit_stop:hit-stop", 0.96), H(2, "b1", 1, "hit_stop:hit-stop", 0.95), H(3, "b1", 1, "hit_stop:impact hold", 0.94),
                H(4, "b2", 2, "camera_lock:camera lock", 0.60), H(5, "b3", 3, "hit_stop:freeze frame", 0.90), H(6, "b4", 4, "query", 0.50),
                H(7, "b5", 5, "camera_lock:locked off", 0.40)]

    def test_coverage_first_and_quota_sum(self):
        chosen, footer = q.allocate(self.hits(), [("hit_stop", []), ("camera_lock", [])], k=5)
        ids = [c["id"] for c in chosen]
        self.assertEqual(len(ids), 5)
        self.assertIn("p1", ids[:2])
        self.assertIn("p4", ids[:3])           # camera_lock's best is covered early despite its low score
        self.assertEqual(footer["hit_stop"]["candidates"], 4)
        self.assertEqual(sum(v["shown"] for v in footer.values()), 5)

    def test_soft_decay_prefers_new_blocks_and_rolls_up(self):
        chosen, footer = q.allocate(self.hits(), [("hit_stop", []), ("camera_lock", [])], k=4, spread=1.0)
        ids = [c["id"] for c in chosen]
        self.assertIn("p5", ids)               # different block beats p2/p3 in the same block as p1
        first = [c for c in chosen if c["id"] == "p1"][0]
        self.assertGreaterEqual(first.get("more_in_block", 0), 1)
        chosen0, _ = q.allocate(self.hits(), [("hit_stop", []), ("camera_lock", [])], k=4, spread=0.0)
        self.assertNotEqual([c["id"] for c in chosen0], ids)   # spread changes the allocation

    def test_nuance_hop_annotates_and_boosts(self):
        hits = [H(1, "b1", 1, "hit_stop:hit-stop", 0.96), H(2, "b2", 2, "hit_stop:hit-stop", 0.95), H(3, "b3", 3, "hit_stop:impact hold", 0.955)]
        plain, _ = q.allocate([dict(h) for h in hits], [("hit_stop", [])], k=2, spread=0.0)
        self.assertEqual([c["id"] for c in plain], ["p1", "p3"])            # without edges the higher base wins
        edges = {("p2", "p1"): "compensates_for", ("p1", "p2"): "compensates_for"}
        boosted, _ = q.allocate([dict(h) for h in hits], [("hit_stop", [])], k=2, spread=0.0, edges=edges)
        self.assertEqual([c["id"] for c in boosted], ["p1", "p2"])          # the edge to the chosen p1 lifts p2 over p3
        self.assertTrue(boosted[1].get("nuance", "").startswith("compensates_for"))


@unittest.skipUnless(hb.DEFAULT_DB.exists(), "no built handbook index")
class Live(unittest.TestCase):
    def test_flag_on_returns_footer_and_respects_limit(self):
        conn = q.open_all()
        hits, concepts = q.lookup3(conn, text="impact hold", limit=6, min_score=0, rerank={"allocator": True, "any_word_fallback": True})
        self.assertLessEqual(len(hits), 6)
        self.assertIn("coverage_footer", hits[0])
        self.assertIn("hit_stop", hits[0]["coverage_footer"])
        text = q.format_hits2(hits, budget=1500)
        self.assertIn("coverage:", text)
        conn.close()


if __name__ == "__main__":
    unittest.main()
