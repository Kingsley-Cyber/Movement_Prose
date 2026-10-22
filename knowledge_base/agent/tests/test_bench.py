import json
import sys
import tempfile
import unittest
from pathlib import Path

BUNDLE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BUNDLE))

from agent import bench  # noqa: E402
from agent import handbook as hb  # noqa: E402
from agent import knowledge as kn  # noqa: E402
from agent import query as q  # noqa: E402


class Metrics(unittest.TestCase):
    def test_recall_and_rr(self):
        self.assertEqual(bench.recall_at_k(["a", "b"], ["x", "b", "y", "a"], k=10), 1.0)
        self.assertEqual(bench.recall_at_k(["a", "b"], ["x", "b"], k=10), 0.5)
        self.assertEqual(bench.recall_at_k(["a"], ["x"] * 10 + ["a"], k=10), 0.0)
        self.assertEqual(bench.reciprocal_rank(["a"], ["x", "y", "a"]), 1.0 / 3)
        self.assertEqual(bench.reciprocal_rank(["a"], ["x"]), 0.0)

    def test_load_queries_meta_and_validation(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "q.jsonl"
            p.write_text('{"meta": true, "authored_by": "agent", "owner_reviewed": false}\n'
                         '{"id": "q1", "query": "freeze frame", "expected": ["a001#0001"]}\n'
                         '# comment\n{"query": "hold", "expected": ["a001#0002"], "mode": "find"}\n', encoding="utf-8")
            meta, recs = bench.load_queries(p)
            self.assertFalse(meta["owner_reviewed"])
            self.assertEqual([r["id"] for r in recs], ["q1", "q002"])
            p.write_text('{"query": "x"}\n', encoding="utf-8")
            with self.assertRaises(ValueError):
                bench.load_queries(p)
            with self.assertRaises(FileNotFoundError):
                bench.load_queries(Path(d) / "missing.jsonl")

    def test_record_cited_counts_and_used_with(self):
        with tempfile.TemporaryDirectory() as d:
            mem = kn.open_memory(Path(d) / "m.db")
            n = kn.record_cited(mem, "run_t", [("e1", "src-x#0001"), ("e1", "src-x#0002")], {"status": "pass"})
            self.assertEqual(n, 2)
            self.assertEqual(mem.execute("SELECT count(*) FROM usage_events WHERE action='cited'").fetchone()[0], 2)
            self.assertEqual(bench.cited_passages(mem), {"src-x#0001", "src-x#0002"})
            mem.close()


@unittest.skipUnless(hb.DEFAULT_DB.exists(), "no built handbook index")
class RealBench(unittest.TestCase):
    def test_bench_on_exact_alias_queries(self):
        conn = q.open_all()
        hit = q.lookup2(conn, text="hit-stop", limit=3, min_score=0)[0][0]
        recs = [{"id": "t1", "query": "hit-stop", "expected": [hit["sid"]], "mode": "find"},
                {"id": "t2", "query": "freeze frame", "expected": [hit["id"]], "mode": "find"},
                {"id": "t3", "query": "no such phrase zzqx", "expected": ["a001#0001"], "mode": "find"}]
        res = bench.run_bench(conn, recs, limit=10, label="test")
        self.assertEqual(res["queries"], 3)
        self.assertEqual(res["rows"][0]["recall"], 1.0)
        self.assertGreaterEqual(res["recall_at_k"], 1.0 / 3)
        self.assertGreater(res["mrr"], 0.0)
        self.assertIn("retrieval_to_citation", res)
        self.assertIn("bench test", bench.format_report(res))
        conn.close()


if __name__ == "__main__":
    unittest.main()
