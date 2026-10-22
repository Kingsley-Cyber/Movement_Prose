import json
import sys
import tempfile
import unittest
from pathlib import Path

BUNDLE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BUNDLE))

from agent import knobs as kb  # noqa: E402
from agent import knowledge as kn  # noqa: E402
from agent import relations as rel  # noqa: E402


class Knobs(unittest.TestCase):
    def test_five_axes_three_options_no_numerics(self):
        k = kb.load()
        self.assertEqual(len(k["axes"]), 5)
        for a, v in k["axes"].items():
            self.assertEqual(len(v["options"]), 3, a)
            self.assertIn(a, k["field_map"])
        self.assertEqual(kb.check_prose(k), [])

    def test_apply_changes_exactly_one_grammar_field(self):
        base = json.loads((BUNDLE / "runs" / "002_rooftop_cage_fight" / "prompt.json").read_text(encoding="utf-8"))
        for axis, options in kb.axes().items():
            for name in options:
                v = kb.apply(base, axis, name)
                changed = kb.changed_fields(base, v)
                self.assertTrue(changed, (axis, name))
                self.assertTrue(all(c.startswith("animation_grammar." + kb.load()["field_map"][axis]) for c in changed), (axis, name, changed))
                self.assertEqual(v["variant"]["axis"], axis)
        with self.assertRaises(KeyError):
            kb.apply(base, "laban_profile", "nope")

    def test_write_variants(self):
        with tempfile.TemporaryDirectory() as d:
            src = BUNDLE / "runs" / "002_rooftop_cage_fight" / "prompt.json"
            (Path(d) / "prompt.json").write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
            paths = kb.write_variants(d, "smear_policy")
            self.assertEqual(len(paths), 3)
            self.assertTrue(all(p.exists() for p in paths))


class Relations(unittest.TestCase):
    def test_add_validates_seed_and_follow(self):
        with tempfile.TemporaryDirectory() as d:
            mem = kn.open_memory(Path(d) / "m.db")
            with self.assertRaises(ValueError):
                rel.add(mem, "a", "causes", "b", "e")
            with self.assertRaises(ValueError):
                rel.add(mem, "a", "lags", "b", "")
            n = rel.seed(mem)
            self.assertGreaterEqual(n, 20)
            self.assertEqual(rel.seed(mem), 0)          # idempotent
            pulled = rel.follow(mem, ["aa_action_hip_led_punch"], depth=1)
            ids = [p["id"] for p in pulled]
            self.assertIn("aa_action_weight_load", ids)          # requires_setup
            self.assertIn("aa_action_absorb_recoil", ids)        # lags
            self.assertIn("aa_time_contact_hitstop", ids)        # peaks_with
            self.assertNotIn("gaze_shift", ids)                  # generic handbook events are not directives
            deeper = rel.follow(mem, ["aa_action_hip_led_punch"], depth=2)
            self.assertGreater(len(deeper), len(pulled))
            mem.close()


if __name__ == "__main__":
    unittest.main()
