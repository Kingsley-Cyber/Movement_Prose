import sys
import tempfile
import unittest
from pathlib import Path

BUNDLE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BUNDLE))

from agent import handbook as hb  # noqa: E402
from agent import mechanism  # noqa: E402
from agent import query as q  # noqa: E402


@unittest.skipUnless(hb.DEFAULT_DB.exists(), "no built handbook index")
class Mining(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.conn = q.open_all()
        cls.res = mechanism.mine(cls.conn)

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()

    def test_candidates_shape_and_filters(self):
        rows = self.res["rows"]
        self.assertGreater(len(rows), 100)
        aliases = mechanism.known_aliases(self.conn)
        for r in rows:
            self.assertGreaterEqual(r["df"], 3)
            self.assertGreaterEqual(r["chapters"], 2)
            self.assertTrue(0.0 <= r["unit_share"] <= 1.0 and 0.0 <= r["label_share"] <= 1.0)
            self.assertNotIn(r["term"], aliases)
            self.assertNotIn(r["term"], mechanism.META_STOP)
        self.assertEqual([r["score"] for r in rows], sorted((r["score"] for r in rows), reverse=True))

    def test_review_document_is_written_with_blank_columns(self):
        with tempfile.TemporaryDirectory() as d:
            path = mechanism.write_review(self.res, self.conn, Path(d) / "m.md", marks={})
            text = path.read_text(encoding="utf-8")
            self.assertIn("| accept | reject | kind |", text)
            self.assertIn("Nothing here is in the index yet", text)
            self.assertGreaterEqual(text.count("\n| "), 100)

    def test_review_document_with_marks_lists_accepted_terms(self):
        marks = mechanism.load_marks()
        if not marks:
            self.skipTest("no marks file")
        with tempfile.TemporaryDirectory() as d:
            text = mechanism.write_review(self.res, self.conn, Path(d) / "m.md", marks=marks).read_text(encoding="utf-8")
            self.assertIn("## Accepted", text)
            self.assertIn("Reviewed by", text)
            for cid in list(marks["new_concepts"])[:3]:
                self.assertIn("`%s`" % cid, text)


if __name__ == "__main__":
    unittest.main()
