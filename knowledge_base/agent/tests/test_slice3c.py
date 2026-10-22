import json
import sys
import unittest
from pathlib import Path

BUNDLE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BUNDLE))

from agent import bench  # noqa: E402
from agent import handbook as hb  # noqa: E402
from agent import query as q  # noqa: E402


class Rerank(unittest.TestCase):
    def rows(self):
        return [{"passage_id": "p1", "bm": -5.0, "kind": "table_row", "chars": 30, "text": "hit-stop", "epistemic": None, "article_kind": None, "moment_type": "impact", "slot_id": "temporal_cadence"},
                {"passage_id": "p2", "bm": -4.0, "kind": "paragraph", "chars": 300, "text": "hit-stop and impact hold explained", "epistemic": "SOURCE_EVIDENCE", "article_kind": "contract", "moment_type": "impact", "slot_id": "temporal_cadence"},
                {"passage_id": "p3", "bm": -3.0, "kind": "paragraph", "chars": 200, "text": "unrelated", "epistemic": None, "article_kind": "deep_research_prompt", "moment_type": None, "slot_id": None}]

    def test_all_off_keeps_bm25_order(self):
        flags = dict((k, False) for k in q.RERANK_FLAGS)
        out = q.rerank_rows(self.rows(), flags)
        self.assertEqual([r["passage_id"] for r in out], ["p1", "p2", "p3"])

    def test_kind_length_alias_epistemic_lift_the_prose_passage(self):
        flags = dict((k, True) for k in q.RERANK_FLAGS)
        concepts = [("hit_stop", [("hit-stop", 11, 0.3), ("impact hold", 13, 0.3)])]
        out = q.rerank_rows(self.rows(), flags, concepts, query="impact hold timing")
        self.assertEqual(out[0]["passage_id"], "p2")
        self.assertEqual(out[-1]["passage_id"], "p3")

    def test_any_word_query_and_fts_query(self):
        self.assertEqual(q.any_word_query("locked constraints survive"), '"locked" OR "constraints" OR "survive"')
        self.assertTrue(q.fts_query("a b").startswith("("))

    def test_load_rerank_missing_file_is_all_off(self):
        self.assertEqual(set(q.load_rerank("/nonexistent/rerank.json").values()), {False})


@unittest.skipUnless(hb.DEFAULT_DB.exists() and bench.QUERIES_PATH.exists(), "no index or no queries")
class BenchmarkGate(unittest.TestCase):
    """No ranking change ships if the default configuration scores below the recorded baseline."""

    def test_default_config_does_not_drop_below_baseline(self):
        files = sorted((BUNDLE / "docs" / "bench").glob("*baseline*.json"))
        baseline = json.loads(files[-1].read_text(encoding="utf-8"))   # newest baseline moves with the query set
        conn = q.open_all()
        _, records = bench.load_queries()
        res = bench.run_bench(conn, records, limit=10, rerank=None, label="gate")
        conn.close()
        self.assertGreaterEqual(res["recall_at_k"], baseline["recall_at_k"] - 1e-9)

    def test_any_word_fallback_adds_results_when_and_is_empty(self):
        conn = q.open_all()
        off, _ = q.lookup3(conn, text="locked constraints survive the budget", limit=10, min_score=0, rerank=False)
        on, _ = q.lookup3(conn, text="locked constraints survive the budget", limit=10, min_score=0, rerank={"any_word_fallback": True})
        conn.close()
        self.assertGreaterEqual(len(on), len(off))
        self.assertTrue(any("(any-word)" in (h.get("via") or "") for h in on) or len(off) >= 10)


if __name__ == "__main__":
    unittest.main()
