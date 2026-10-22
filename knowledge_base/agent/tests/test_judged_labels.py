import sys
import tempfile
import unittest
from pathlib import Path

BUNDLE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BUNDLE))

from agent import handbook as hb  # noqa: E402
from agent import knowledge as kn  # noqa: E402
from agent import query as q  # noqa: E402


class Memory(unittest.TestCase):
    def test_label_requires_reason_and_a_value(self):
        with tempfile.TemporaryDirectory() as d:
            mem = kn.open_memory(Path(d) / "m.db")
            with self.assertRaises(ValueError):
                kn.set_label(mem, "x#0001", "impact", None, "")
            with self.assertRaises(ValueError):
                kn.set_label(mem, "x#0001", None, None, "why")
            kn.set_label(mem, "x#0001", "impact", "temporal_cadence", "because", 0.9)
            lab = kn.get_label(mem, "x#0001")
            self.assertEqual((lab["moment_type"], lab["slot_id"], lab["intent_tier"]), ("impact", "temporal_cadence", 2))
            kn.set_label(mem, "x#0002", None, "none", "no slot applies")
            self.assertIsNone(kn.get_label(mem, "x#0002")["intent_tier"])
            mem.close()


@unittest.skipUnless(hb.DEFAULT_DB.exists(), "no built handbook index")
class Retrieval(unittest.TestCase):
    def test_judged_first_and_none_excluded_only_with_flag(self):
        with tempfile.TemporaryDirectory() as d:
            mem_path = Path(d) / "m.db"
            conn = q.open_all(memory_path=mem_path)
            mem = kn.open_memory(mem_path)
            lexical, _ = q.lookup3(conn, moment="impact", slot="temporal_cadence", min_score=2, limit=10, rerank=False)
            self.assertTrue(lexical)
            promoted = hb.get_passage(conn, q.resolve_id(conn, "a035#0027"))["passage_id"]
            demoted = lexical[0]["id"]
            kn.set_label(mem, promoted, "impact", "temporal_cadence", "hit-stop definition", 0.9)
            kn.set_label(mem, demoted, "none", "none", "test correction", 0.9)
            off, _ = q.lookup3(conn, moment="impact", slot="temporal_cadence", min_score=2, limit=10, rerank=False)
            self.assertEqual(off[0]["id"], demoted)
            on, _ = q.lookup3(conn, moment="impact", slot="temporal_cadence", min_score=2, limit=10, rerank={"judged_labels": True})
            self.assertEqual(on[0]["id"], promoted)
            self.assertEqual(on[0]["m"], "impact*")
            self.assertNotIn(demoted, [h["id"] for h in on])
            conn.close()
            mem.close()


if __name__ == "__main__":
    unittest.main()
