import sys
import unittest
from pathlib import Path

BUNDLE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BUNDLE))

from agent import handbook as hb  # noqa: E402
from agent import verify  # noqa: E402


@unittest.skipUnless(hb.DEFAULT_DB.exists(), "no built handbook index")
class Verify(unittest.TestCase):
    def test_index_and_memory_are_consistent(self):
        res = verify.run()
        failed = [c for c in res["checks"] if not c["ok"]]
        self.assertEqual(failed, [], verify.format_report(res))
        self.assertGreater(res["counts"]["concept_passages"], 10000)


if __name__ == "__main__":
    unittest.main()
