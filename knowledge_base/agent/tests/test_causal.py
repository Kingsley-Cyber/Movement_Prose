import sys
import tempfile
import unittest
from pathlib import Path

BUNDLE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BUNDLE))

from agent import causal  # noqa: E402
from agent import handbook as hb  # noqa: E402
from agent import knowledge as kn  # noqa: E402
from agent import query as q  # noqa: E402


class Triples(unittest.TestCase):
    def test_add_validates_and_closure_walks(self):
        with tempfile.TemporaryDirectory() as d:
            mem = kn.open_memory(Path(d) / "m.db")
            with self.assertRaises(ValueError):
                causal.add(mem, "a", "causes", "b", "e")
            with self.assertRaises(ValueError):
                causal.add(mem, "a", "requires", "b", "")
            causal.add(mem, "a", "requires", "b", "e1")
            causal.add(mem, "b", "triggers", "c", "e2")
            causal.add(mem, "c", "requires", "a", "cycle")       # cycle must not loop
            causal.add(mem, "x", "amplifies", "s", "e3")
            causal.add(mem, "y", "dampens", "s", "e4")
            causal.add(mem, "m", "requires", "n", "e5")
            causal.add(mem, "n", "triggers", "o", "e6")
            reach = causal.closure(mem, "a", depth=3)
            self.assertEqual([r["concept"] for r in reach][:2], ["b", "c"])
            comp = causal.compensations(mem, "s")
            self.assertEqual((comp[0]["cause"], comp[0]["cure"]), ("x", "y"))
            iso = causal.isomorphs(mem)
            self.assertTrue(any(r["pattern"] == "requires>triggers" for r in iso))
            self.assertEqual(len(causal.list_triples(mem)), 7)
            mem.close()


@unittest.skipUnless(hb.DEFAULT_DB.exists(), "no built handbook index")
class Seeding(unittest.TestCase):
    def test_seed_counts_and_yutapon_closure(self):
        conn = q.open_all()
        with tempfile.TemporaryDirectory() as d:
            mem = kn.open_memory(Path(d) / "m.db")
            h = causal.seed_from_handbook(conn, mem)
            c = causal.seed_from_catalog(conn, mem)
            self.assertGreaterEqual(c, 20)
            self.assertGreaterEqual(h, 1)
            reach = causal.closure(mem, "directive:aa_env_yutapon_cubes", depth=3)
            self.assertIn("directive:aa_env_radial_fracture", [r["concept"] for r in reach])
            self.assertEqual(causal.seed_from_catalog(conn, mem), 0)   # idempotent
            mem.close()
        conn.close()


if __name__ == "__main__":
    unittest.main()
