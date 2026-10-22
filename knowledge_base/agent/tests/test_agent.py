import json
import subprocess
import sys
import unittest
from collections import Counter
from pathlib import Path

BUNDLE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BUNDLE))

from agent import CANONICAL_FINGERPRINT, GLOBAL_SLOTS, MOMENTS, PLACEHOLDER, SLOTS  # noqa: E402
from agent import catalog as catalog_mod  # noqa: E402
from agent import check as check_mod  # noqa: E402
from agent import emit as emit_mod  # noqa: E402
from agent import engines as eng  # noqa: E402
from agent import fixtures  # noqa: E402
from agent import policy as policy_mod  # noqa: E402
from agent import propose as propose_mod  # noqa: E402
from agent import taste as taste_mod  # noqa: E402
from agent.ir import IR, Authored, Clip, Event, Selection, to_dict, validate_shape  # noqa: E402

CAT = catalog_mod.load_catalog()
POL = policy_mod.Policy()
ENG = eng.load_engine_profiles()
TASTE = taste_mod.load_profiles()
ENT = {"A": "A, the fighter in the red jacket", "B": "B, the fighter in the blue jacket"}


def ev(event_id, moment, start, end, actor="A", target="B", **kw):
    return Event(event_id=event_id, actor_id=actor, target_id=target, moment_type=moment, start_frame=start, end_frame=end, **kw)


def sel(directive_id, event_id, start, end, actor="A", target="B", **kw):
    return Selection(directive_id=directive_id, event_id=event_id, actor_id=actor, target_id=target, start_frame=start, end_frame=end, **kw)


def make_ir(events, selections, authored=None, engine="generic_web_ui", frame_count=72, contact=None, taste=None, duration=None):
    return IR(request="test", scene_context="A and B face each other in a stone courtyard.", entities=dict(ENT),
              clip=Clip(24, duration if duration is not None else frame_count / 24.0, frame_count), events=events,
              selections=selections, authored=authored or [], contact_origins=contact or {}, engine_profile_id=engine,
              taste_profile_id=taste)


def findings(ir, key="subject"):
    return check_mod.check_ir(ir, CAT, POL, ENG, TASTE, key=key)


def errors(ir, key="subject"):
    return [f for f in findings(ir, key) if f.level == "error"]


def codes(fs):
    return sorted(set(f.code for f in fs))


class CatalogAndPolicy(unittest.TestCase):
    def test_catalog_fingerprint_matches_validation_report(self):
        report = json.loads((BUNDLE / "validation_report.json").read_text(encoding="utf-8"))
        self.assertEqual(len(CAT), 64)
        self.assertEqual(CAT.fingerprint(), CANONICAL_FINGERPRINT)
        self.assertEqual(CAT.fingerprint(), report["canonical_content_sha256"])

    def test_budget_classes_cover_all_64_exactly_once(self):
        classes = POL.budget["classes"]
        self.assertEqual(set(classes), set(CAT.ids))
        for did, entry in classes.items():
            self.assertIn(entry["class"], policy_mod.BUDGET_CLASSES, did)
            self.assertIn(entry["subject"], policy_mod.SUBJECT_KINDS, did)
        self.assertEqual(Counter(e["class"] for e in classes.values()),
                         Counter({"none": 26, "material_response": 16, "dominant_action": 8, "secondary_body": 6, "camera_move": 4, "camera_static": 4}))

    def test_priority_defaults_cover_all_slot_moments(self):
        for slot in SLOTS:
            for moment in MOMENTS:
                self.assertIn(POL.priority["table"][slot][moment], POL.classes)
        for did in list(POL.priority["row_overrides"]) + list(POL.locked_ids):
            self.assertIn(did, CAT)
        self.assertEqual(POL.effective_priority(sel("aa_action_hip_led_punch", "e", 0, 1, priority="low"), CAT.get("aa_action_hip_led_punch")), "locked")

    def test_subject_kind_matches_placeholders(self):
        for did in CAT.ids:
            kind = POL.subject_kind(did)
            names = CAT.placeholders(did)
            allowed = {"scene"} if CAT.get(did).slot_id in GLOBAL_SLOTS else set()
            if "target" in names and "actor" not in names:
                allowed |= {"target", "both"}
            elif "actor" in names and "target" not in names:
                allowed |= {"actor", "both"}
            else:
                allowed |= set(policy_mod.SUBJECT_KINDS)
            self.assertIn(kind, allowed, did)


class BundleFixtures(unittest.TestCase):
    def test_bundle_examples_pass_check(self):
        for example in fixtures.load_examples()["examples"]:
            for key in ("actor", "subject"):
                self.assertEqual(errors(fixtures.example_ir(example), key), [], (example["example_id"], key))

    def test_sequence_plan_fixture_passes_subject_keyed(self):
        self.assertEqual(errors(fixtures.sequence_plan_ir()), [])

    def test_actor_keyed_reproduces_validator_rejection_on_sequence_plan(self):
        errs = errors(fixtures.sequence_plan_ir(), key="actor")
        self.assertEqual(codes(errs), ["DUPLICATE_SLOT"])
        self.assertTrue(any("aa_action_followthrough_arc" in f.message and "aa_action_absorb_recoil" in f.message for f in errs))

    def test_validate_shape_rejects_bad_frames(self):
        doc = to_dict(fixtures.sequence_plan_ir())
        doc["selections"][0]["start_frame"] = doc["selections"][0]["end_frame"]
        self.assertTrue(any(f.code == "SHAPE" for f in validate_shape(doc)))
        self.assertEqual(validate_shape(to_dict(fixtures.sequence_plan_ir())), [])


class Budget(unittest.TestCase):
    def test_two_dominant_actions_same_subject_fails(self):
        ir = make_ir([ev("e1", "execution", 0, 12)], [sel("aa_action_hip_led_punch", "e1", 0, 12)],
                     authored=[Authored(event_id="e1", slot_id="primary_action", text="A also sweeps the lead leg.")])
        self.assertIn("BUDGET_DOMINANT_ACTION", codes(errors(ir)))

    def test_overlapping_finish_and_recoil_different_subjects_allowed(self):
        ir = make_ir([ev("a_finish", "follow_through", 26, 40, target=None), ev("b_recoil", "recoil", 26, 44, actor="B", target=None)],
                     [sel("aa_action_followthrough_arc", "a_finish", 26, 40), sel("aa_action_absorb_recoil", "b_recoil", 26, 44)])
        self.assertEqual(errors(ir), [])
        self.assertEqual(codes(errors(ir, key="actor")), ["DUPLICATE_SLOT"])

    def test_camera_move_budget_is_per_clip_and_settle_exempt(self):
        events = [ev("e1", "execution", 0, 12), ev("e2", "follow_through", 12, 24), ev("e3", "recovery", 24, 36)]
        base = [sel("aa_action_hip_led_punch", "e1", 0, 12), sel("aa_action_followthrough_arc", "e2", 12, 24),
                sel("aa_action_guard_recovery", "e3", 24, 36), sel("aa_camera_recovery_settle", "e3", 24, 36)]
        two_moves = base + [sel("aa_camera_lateral_track", "e1", 0, 12), sel("aa_camera_whip_reacquire", "e2", 12, 24)]
        self.assertIn("BUDGET_CAMERA_MOVE", codes(errors(make_ir(events, two_moves))))
        one_move = base + [sel("aa_camera_lateral_track", "e1", 0, 12)]
        fs = findings(make_ir(events, one_move))
        self.assertEqual([f for f in fs if f.level == "error"], [])
        self.assertNotIn("CAMERA_SETTLE_WITHOUT_MOVE", codes(fs))
        self.assertIn("CAMERA_SETTLE_WITHOUT_MOVE", codes(findings(make_ir(events, base))))

    def test_material_response_budget_per_window(self):
        contact = {"e1": "the meeting point of the fists"}
        events = [ev("e1", "impact", 24, 26)]
        sels = [sel("aa_action_forearm_block", "e1", 24, 26), sel("aa_secondary_angular_impact_star", "e1", 24, 26),
                sel("aa_secondary_contact_ring", "e1", 24, 26), sel("aa_material_monochrome_impact", "e1", 24, 26),
                sel("aa_light_silhouette_flash", "e1", 24, 26)]
        self.assertIn("BUDGET_MATERIAL_RESPONSE", codes(errors(make_ir(events, sels, contact=contact))))
        self.assertNotIn("BUDGET_MATERIAL_RESPONSE", codes(errors(make_ir(events, sels[:4], contact=contact))))


class Rules(unittest.TestCase):
    def test_declared_conflict_requires_overlap_and_scope(self):
        events = [ev("e1", "impact", 24, 28)]
        clash = [sel("aa_action_forearm_block", "e1", 24, 28), sel("aa_time_contact_hitstop", "e1", 24, 26), sel("aa_camera_crash_zoom", "e1", 24, 26)]
        self.assertIn("CONFLICT", codes(errors(make_ir(events, clash))))
        sequential = [sel("aa_action_forearm_block", "e1", 24, 28), sel("aa_time_contact_hitstop", "e1", 24, 26), sel("aa_camera_crash_zoom", "e1", 26, 28)]
        self.assertNotIn("CONFLICT", codes(errors(make_ir(events, sequential))))

    def test_kagenashi_two_tone_different_actors_ok(self):
        events = [ev("prep", "anticipation", 0, 12, actor="B", target="A"), ev("go", "execution", 0, 12)]
        same = [sel("aa_action_weight_load", "prep", 0, 12, actor="B", target="A"), sel("aa_material_two_tone_cel", "prep", 0, 12, actor="A", target=None),
                sel("aa_action_hip_led_punch", "go", 0, 12), sel("aa_light_kagenashi", "go", 0, 12, actor="A", target=None)]
        self.assertIn("CONFLICT", codes(errors(make_ir(events, same))))
        different = [sel("aa_action_weight_load", "prep", 0, 12, actor="B", target="A"), sel("aa_material_two_tone_cel", "prep", 0, 12, actor="B", target=None),
                     sel("aa_action_hip_led_punch", "go", 0, 12), sel("aa_light_kagenashi", "go", 0, 12, actor="A", target=None)]
        self.assertNotIn("CONFLICT", codes(errors(make_ir(events, different))))

    def test_locked_cannot_be_downgraded_or_suppressed(self):
        events = [ev("e1", "execution", 0, 12)]
        self.assertIn("LOCKED_DOWNGRADED", codes(errors(make_ir(events, [sel("aa_action_hip_led_punch", "e1", 0, 12, priority="low")]))))
        self.assertIn("LOCKED_SUPPRESSED", codes(errors(make_ir(events, [sel("aa_action_hip_led_punch", "e1", 0, 12, suppressed_reason="lower_priority")]))))

    def test_required_needs_provider_reason(self):
        events = [ev("e1", "anticipation", 0, 12)]
        base = [sel("aa_action_weight_load", "e1", 0, 12)]
        bad = base + [sel("aa_env_preimpact_quiet", "e1", 0, 12, suppressed_reason="lower_priority")]
        self.assertIn("REQUIRED_NEEDS_PROVIDER_REASON", codes(errors(make_ir(events, bad))))
        ok = base + [sel("aa_env_preimpact_quiet", "e1", 0, 12, suppressed_reason="provider_unsupported")]
        self.assertEqual(errors(make_ir(events, ok)), [])

    def test_prerequisite_by_prior_selection_or_declared(self):
        contact = {"hit": "the meeting point of A's fist and the stone floor", "fall": "the meeting point of A's fist and the stone floor"}
        missing = make_ir([ev("fall", "recoil", 26, 44)], [sel("aa_action_absorb_recoil", "fall", 26, 44), sel("aa_env_yutapon_cubes", "fall", 26, 44)], contact=contact)
        self.assertIn("PREREQUISITE_MISSING", codes(errors(missing)))
        declared = make_ir([ev("fall", "recoil", 26, 44, declared_prerequisites=["surface_fracture_event"])],
                           [sel("aa_action_absorb_recoil", "fall", 26, 44), sel("aa_env_yutapon_cubes", "fall", 26, 44)], contact=contact)
        self.assertNotIn("PREREQUISITE_MISSING", codes(errors(declared)))
        prior = make_ir([ev("hit", "impact", 24, 26, declared_prerequisites=["contact_event_on_solid_surface"]), ev("fall", "recoil", 26, 44)],
                        [sel("aa_action_forearm_block", "hit", 24, 26), sel("aa_env_radial_fracture", "hit", 24, 26),
                         sel("aa_action_absorb_recoil", "fall", 26, 44), sel("aa_env_yutapon_cubes", "fall", 26, 44)], contact=contact)
        self.assertNotIn("PREREQUISITE_MISSING", codes(errors(prior)))

    def test_missing_target_binding_is_error(self):
        ir = make_ir([ev("e1", "execution", 0, 12, target=None)], [sel("aa_action_hip_led_punch", "e1", 0, 12, target=None)])
        self.assertIn("BINDING_MISSING", codes(errors(ir)))

    def test_event_without_action_fails(self):
        ir = make_ir([ev("e1", "anticipation", 0, 12)], [sel("aa_subject_loaded_silhouette", "e1", 0, 12)])
        self.assertIn("EVENT_WITHOUT_ACTION", codes(errors(ir)))

    def test_redundancy_warning_for_consecutive_reselection(self):
        events = [ev("e1", "recovery", 40, 56), ev("e2", "recovery", 56, 72)]
        sels = [sel("aa_action_guard_recovery", "e1", 40, 56), sel("aa_action_guard_recovery", "e2", 56, 72)]
        self.assertIn("REDUNDANT_RESELECTION", codes(findings(make_ir(events, sels))))

    def test_authored_text_warnings(self):
        ir = make_ir([ev("e1", "execution", 0, 12)], [sel("aa_action_hip_led_punch", "e1", 0, 12)],
                     authored=[Authored(event_id="e1", slot_id="secondary_motion", text="Yutapon cubes burst at 12 fps.", clause="CAMERA AND PRESENTATION")])
        self.assertEqual(sorted(c for c in codes(findings(ir)) if c.endswith("_IN_PROMPT")), ["NUMERIC_IN_PROMPT", "SHORTHAND_IN_PROMPT"])

    def test_kling_omni_duration_limit(self):
        ir = make_ir([ev("e1", "execution", 0, 384)], [sel("aa_action_hip_led_punch", "e1", 0, 384)],
                     engine="kling_video_30_omni_documented_references", frame_count=384, duration=16.0)
        self.assertIn("DURATION_LIMIT", codes(errors(ir)))
        self.assertIn("ENGINE_RETIRED", codes(errors(make_ir([ev("e1", "execution", 0, 12)], [sel("aa_action_hip_led_punch", "e1", 0, 12)], engine="runway_gen3_historical"))))


class Emit(unittest.TestCase):
    def setUp(self):
        self.ir = fixtures.sequence_plan_ir()
        self.result = emit_mod.emit(self.ir, CAT, POL, ENG["generic_web_ui"], TASTE["raw_street_brawl"])

    def test_emit_has_no_placeholders_fps_or_frame_numbers(self):
        self.assertIsNone(PLACEHOLDER.search(self.result.prompt))
        self.assertIsNone(check_mod.NUMERIC_RE.search(self.result.prompt))

    def test_emit_order_is_event_then_slot_order(self):
        prompt = self.result.prompt
        order = [(m["directive_id"], m["event_id"]) for m in self.result.receipt["manifest"] if m["directive_id"] and m["clause"] == "SUBJECT AND ACTION"]
        positions = []
        for did, event_id in order:
            s = next(x for x in self.ir.selections if x.directive_id == did and x.event_id == event_id)
            probe = emit_mod.substitute(CAT.get(did).prompt_snippet, s, self.ir).strip()[:40]
            positions.append(prompt.index(probe))
        self.assertEqual(positions, sorted(positions))
        self.assertLess(prompt.index("[SHOT AND DURATION]"), prompt.index("[SUBJECT AND ACTION]"))
        self.assertLess(prompt.index("[SUBJECT AND ACTION]"), prompt.index("[PERFORMANCE]"))
        self.assertLess(prompt.index("[PERFORMANCE]"), prompt.index("[TIMING]"))
        self.assertLess(prompt.index("[TIMING]"), prompt.index("[CAMERA AND PRESENTATION]"))

    def test_emit_coverage_every_selected_snippet_present(self):
        cov = self.result.receipt["coverage"]
        self.assertEqual(cov["covered"], cov["total"])
        self.assertEqual(cov["total"], len(self.ir.selections))

    def test_inactive_profile_emits_no_negatives(self):
        off = emit_mod.emit(self.ir, CAT, POL, ENG["ltx_video_098_distilled_default"])
        self.assertIsNone(off.negative)
        self.assertEqual((off.receipt["negatives"]["route"], off.receipt["negatives"]["reason"]), ("suppressed", "provider_unsupported"))
        self.assertNotIn("[NEGATIVES]", off.prompt)
        on = emit_mod.emit(self.ir, CAT, POL, ENG["wan21_t2v_diffusers"])
        self.assertTrue(on.negative and len(on.negative) > 50)
        self.assertEqual(on.receipt["negatives"]["route"], "negative_field")
        self.assertNotIn("[NEGATIVES]", on.prompt)

    def test_avoid_sentence_requires_optin(self):
        self.assertNotIn("Avoid:", self.result.prompt)
        self.assertEqual(self.result.receipt["negatives"]["route"], "suppressed")
        folded = emit_mod.emit(self.ir, CAT, POL, ENG["generic_web_ui"], avoid_sentence=True)
        self.assertIn("[NEGATIVES]\nAvoid: ", folded.prompt)
        self.assertEqual(folded.receipt["negatives"]["route"], "inline_positive_unverified")

    def test_receipt_sha256_matches_prompt(self):
        import hashlib
        self.assertEqual(self.result.receipt["prompt_sha256"], hashlib.sha256(self.result.prompt.encode("utf-8")).hexdigest())
        self.assertEqual(self.result.receipt["chars_total"], len(self.result.prompt))

    def test_post_plan_carries_ops_and_exposure_routes(self):
        plan = self.result.post_plan
        self.assertEqual(len(plan["editorial_operations"]), 4)
        routed = dict((e["directive_id"], e["preferred_route"]) for e in plan["routed_directives"])
        self.assertEqual(routed.get("aa_time_contact_hitstop"), "editorial_exposure_control")
        self.assertNotIn("aa_action_hip_led_punch", routed)


class Taste(unittest.TestCase):
    def test_taste_match_token_overlap(self):
        self.assertEqual(taste_mod.best("heavy, brutal, old-school counter-punch", TASTE), "gritty_90s_ova")
        self.assertEqual(taste_mod.best("clean modern sakuga", TASTE), "modern_ufotable_sakuga")
        self.assertEqual(taste_mod.best("raw street brawl", TASTE), "raw_street_brawl")
        self.assertIsNone(taste_mod.best("pastel romance", TASTE))

    def test_taste_rank_never_filters(self):
        rows = CAT.rows(slot="primary_action", moment="execution")
        ranked = taste_mod.rank(rows, TASTE["gritty_90s_ova"])
        self.assertEqual(len(ranked), len(rows))
        marks = [m for _, m in ranked]
        self.assertEqual(marks, sorted(marks, key=lambda m: {"preferred": 0, "neutral": 1, "avoid": 2}[m]))
        self.assertEqual(marks[-1], "avoid")

    def test_propose_lists_every_slot_and_finds_lexical_gaps(self):
        events, frame_count = propose_mod.default_events(5.0)
        self.assertEqual(frame_count, 120)
        proposal = propose_mod.propose("hero slips a wide swing and lands a rising left hook to the solar plexus", events, CAT, POL, TASTE["gritty_90s_ova"])
        for e in proposal["events"]:
            self.assertEqual(list(e["slots"]), CAT.slot_order)
            self.assertEqual(e["empty_slots"], [])
        self.assertIn("plexus", proposal["lexical_gaps"])


class BundleIntegrity(unittest.TestCase):
    def test_bundle_validator_still_passes(self):
        out = subprocess.run([sys.executable, "-I", str(BUNDLE / "validate_anime_seed.py"), "--db", str(BUNDLE / "ai_video_compiler.db")],
                             capture_output=True, text=True, cwd=str(BUNDLE))
        self.assertEqual(out.returncode, 0, out.stdout[-800:] + out.stderr[-800:])
        report = json.loads(out.stdout)
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["database_content_sha256"], CANONICAL_FINGERPRINT)


if __name__ == "__main__":
    unittest.main()
