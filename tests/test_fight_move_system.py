"""Automated test suite for Fight Move System v2 (Milestones M1, M2, M3, M4, M5)."""

import copy
import json
import re
import tempfile
import unittest
from pathlib import Path

from fight_move_system.chain import scan_prompt_v18, validate_chain_frames, validate_kinetic_chain
from fight_move_system.cli import generate_m4_packets
from fight_move_system.closed_loop import (
    apply_localized_repair,
    build_next_clip_handoff,
    ingest_render_verdict,
    parse_scorecard_markdown,
    plan_localized_repair,
)
from fight_move_system.compiler import compile_clip_prompt, scan_prompt_v15
from fight_move_system.composer import compose_clips
from fight_move_system.kb_bridge import (
    IN_REPO_KB_DIR,
    kb_find,
    kb_lookup,
    kb_verify,
    load_semantic_directives,
    query_kb_prior_to_semantic_intent,
    sync_lexicon_gaps_to_memory,
    verify_bundle_integrity,
)
from fight_move_system.lexicon import Lexicon, validate_card
from fight_move_system.original_causal_compiler import (
    FORBIDDEN_XPERIMENT_KEYS,
    ORIGINAL_TEMPLATE_PATH,
    assert_pure_0534_causal_spec,
    compile_beatsheet_to_original_0534_causal,
    compile_original_causal_spec_with_kb,
    verify_original_compiler_protection,
)
from fight_move_system.validator import validate_clip


class TestFightMoveSystem(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.lexicon = Lexicon.load_default()
        fixture_path = (
            Path(__file__).parent.parent
            / "fight_move_system"
            / "fixtures"
            / "pass"
            / "10_beat_boxing_exchange.json"
        )
        with open(fixture_path, "r", encoding="utf-8") as f:
            cls.valid_10_beat = json.load(f)

        var3_path = (
            Path(__file__).parent.parent
            / "fight_move_system"
            / "fixtures"
            / "pass"
            / "variation_3_eight_limbs_muay_thai_mma_war_sheet.json"
        )
        with open(var3_path, "r", encoding="utf-8") as f:
            cls.valid_var3 = json.load(f)

    def _base_clip(self) -> dict:
        return {
            "regime": "standup_striking",
            "initial_range": "punch",
            "allow_one_sided_probe": True,
            "fighters": {
                "A": {
                    "style": "boxing",
                    "stance": "orthodox",
                    "screen_side": "left",
                    "facing": "right",
                    "support": "standing",
                    "coil": "neutral",
                },
                "B": {
                    "style": "boxing",
                    "stance": "orthodox",
                    "screen_side": "right",
                    "facing": "left",
                    "support": "standing",
                    "coil": "neutral",
                },
            },
            "moments": [
                {
                    "frames": 7,
                    "A": {"move": "jab"},
                    "B": {"move": "head_snap_back"},
                }
            ],
        }

    # --- M1: Lexicon & Card Schema ---
    def test_lexicon_loads_and_all_cards_valid(self) -> None:
        self.assertEqual(self.lexicon.validation_errors, [])
        self.assertGreaterEqual(len(self.lexicon.cards_by_id), 25)

    def test_v01_unknown_move_and_enum(self) -> None:
        # Fail fixture: unknown move
        clip = self._base_clip()
        clip["moments"][0]["A"]["move"] = "non_existent_dragon_punch"
        res = validate_clip(clip, lexicon=self.lexicon)
        self.assertIn("V01", res.error_codes())

        # Fail fixture: invalid card enum
        bad_card = copy.deepcopy(self.lexicon.get("jab"))
        bad_card["limb"] = "third_tentacle"
        errs = validate_card(bad_card)
        self.assertTrue(any(code == "V01" for code, _ in errs))

        # Pass fixture
        res_pass = validate_clip(self._base_clip(), lexicon=self.lexicon)
        self.assertNotIn("V01", res_pass.error_codes())

    def test_v02_style_illegal_move(self) -> None:
        # Fail: boxing fighter attempting spinning_back_kick (only muay_thai/mma/baki/freestyle_sakuga)
        clip = self._base_clip()
        clip["fighters"]["A"]["coil"] = "loaded_rear"
        clip["moments"][0]["A"]["move"] = "spinning_back_kick"
        clip["moments"][0]["B"]["move"] = "torso_fold_rib_hit"
        res = validate_clip(clip, lexicon=self.lexicon)
        self.assertIn("V02", res.error_codes())

        # Pass: baki style fighter throwing spinning_back_kick
        clip_pass = copy.deepcopy(clip)
        clip_pass["fighters"]["A"]["style"] = "baki"
        res_pass = validate_clip(clip_pass, lexicon=self.lexicon)
        self.assertNotIn("V02", res_pass.error_codes())

    def test_v03_regime_mismatch(self) -> None:
        # Fail: ground move inside a standup_striking clip on a middle (non-boundary) beat
        clip = self._base_clip()
        clip["fighters"]["A"]["style"] = "freestyle_sakuga"
        clip["moments"] = [
            {"frames": 7, "A": {"move": "level_duck"}},
            {"frames": 10, "A": {"move": "low_ankle_sweep"}, "B": {"move": "outside_angle_step"}},
            {"frames": 7, "A": {"move": "body_jab"}, "B": {"move": "torso_fold_rib_hit"}},
        ]
        res = validate_clip(clip, lexicon=self.lexicon)
        self.assertIn("V03", res.error_codes())

    def test_v04_pre_support_and_coil_violation(self) -> None:
        # Fail: throwing jab from supine support
        clip = self._base_clip()
        clip["fighters"]["A"]["support"] = "supine"
        res = validate_clip(clip, lexicon=self.lexicon)
        self.assertIn("V04", res.error_codes())

    # --- M2: Dyad Coupling & Fluidity (V05–V12, V16–V17) ---
    def test_v05_partner_range_and_posture_mismatch(self) -> None:
        # Fail: throwing jab from 'outside' range
        clip = self._base_clip()
        clip["initial_range"] = "outside"
        res = validate_clip(clip, lexicon=self.lexicon)
        self.assertIn("V05", res.error_codes())

    def test_v06_hit_level_mismatch(self) -> None:
        # Fail: high jab paired with mid torso_fold_rib_hit reaction
        clip = self._base_clip()
        clip["moments"][0]["A"]["move"] = "jab"
        clip["moments"][0]["B"]["move"] = "torso_fold_rib_hit"
        res = validate_clip(clip, lexicon=self.lexicon)
        self.assertIn("V06", res.error_codes())

    def test_v07_force_direction_mismatch(self) -> None:
        # Fail: upward uppercut paired with forward_straight head_snap_back
        clip = self._base_clip()
        clip["fighters"]["A"]["coil"] = "loaded_lead"
        clip["moments"][0]["A"]["move"] = "lead_uppercut"
        clip["moments"][0]["B"]["move"] = "head_snap_back"
        res = validate_clip(clip, lexicon=self.lexicon)
        self.assertIn("V07", res.error_codes())

        # Pass: upward uppercut paired with upward head_snap_up
        clip["moments"][0]["B"]["move"] = "head_snap_up"
        res_pass = validate_clip(clip, lexicon=self.lexicon)
        self.assertNotIn("V07", res_pass.error_codes())

    def test_v08_clinch_asymmetry(self) -> None:
        # Fail: A attaches collar tie (post.support = clinched), B does high_shell_guard (post.support = standing)
        clip = self._base_clip()
        clip["fighters"]["A"]["style"] = "muay_thai"
        clip["moments"][0]["A"]["move"] = "single_collar_tie"
        clip["moments"][0]["B"]["move"] = "high_shell_guard"
        res = validate_clip(clip, lexicon=self.lexicon)
        self.assertIn("V08", res.error_codes())

        # Pass: B reacts with clinch_captured_react (both post.support = clinched)
        clip["moments"][0]["B"]["move"] = "clinch_captured_react"
        res_pass = validate_clip(clip, lexicon=self.lexicon)
        self.assertNotIn("V08", res_pass.error_codes())

    def test_v09_contact_without_reaction(self) -> None:
        # Fail: A throws jab, B has no beat at all
        clip = self._base_clip()
        del clip["moments"][0]["B"]
        res = validate_clip(clip, lexicon=self.lexicon)
        self.assertIn("V09", res.error_codes())

    def test_v10_mid_exchange_neutral_reset_stiffness(self) -> None:
        # Warn: A throws jab in punch range, then immediately does guard_reset_breathe in punch range
        clip = self._base_clip()
        clip["moments"].append({"frames": 6, "A": {"move": "guard_reset_breathe"}})
        res = validate_clip(clip, lexicon=self.lexicon)
        self.assertIn("V10", res.warning_codes())

    def test_v11_coil_chain_break(self) -> None:
        # Warn: A starts in level_low coil (standing) and throws jab (pre.coil = neutral, loaded_rear, recoiling_back)
        clip = self._base_clip()
        clip["fighters"]["A"]["coil"] = "level_low"
        res = validate_clip(clip, lexicon=self.lexicon)
        self.assertIn("V11", res.warning_codes())

    def test_v12_beat_shorter_than_minimum(self) -> None:
        # Warn: jab given only 2 frames (< 6f hypothesis minimum)
        clip = self._base_clip()
        clip["moments"][0]["frames"] = 2
        res = validate_clip(clip, lexicon=self.lexicon)
        self.assertIn("V12", res.warning_codes())

    def test_v13_bleed_budget_exceeded(self) -> None:
        # Warn: two tier-3 spinning_back_kick moves in one clip (exceeds max_tier_3 = 1)
        clip = self._base_clip()
        clip["fighters"]["A"]["style"] = "muay_thai"
        clip["fighters"]["A"]["coil"] = "loaded_rear"
        clip["moments"] = [
            {
                "frames": 12,
                "A": {"move": "spinning_back_kick"},
                "B": {"move": "torso_fold_rib_hit"},
            },
            {
                "frames": 12,
                "A": {
                    "overlaps_move": "burst_step_in",
                    "move": "spinning_back_kick",
                },
                "B": {"move": "torso_fold_rib_hit"},
            },
        ]
        res = validate_clip(clip, lexicon=self.lexicon)
        self.assertIn("V13", res.warning_codes())

    def test_v14_quarantined_pair_shares_clip(self) -> None:
        # Fail: SWEEP.LOW_ROT + STRIKE.LINEAR in same clip
        clip = self._base_clip()
        clip["regime"] = "transition"
        clip["fighters"]["A"]["style"] = "freestyle_sakuga"
        clip["moments"] = [
            {"frames": 7, "A": {"move": "jab"}, "B": {"move": "head_snap_back"}},
            {
                "frames": 10,
                "A": {"overlaps_move": "level_duck", "move": "low_ankle_sweep"},
                "B": {"move": "outside_angle_step"},
            },
        ]
        res = validate_clip(clip, lexicon=self.lexicon)
        self.assertIn("V14", res.error_codes())

    def test_v15_prompt_scanner(self) -> None:
        # Fail on digits
        errs_digit = scan_prompt_v15("Fighter A steps to 0.8m and punches.", "standup_striking", {"boxing"}, self.lexicon)
        self.assertTrue(any(c == "V15" for c, _ in errs_digit))

        # Fail on negative move list
        errs_neg = scan_prompt_v15("Clean boxing match, no ankle sweeps allowed.", "standup_striking", {"boxing"}, self.lexicon)
        self.assertTrue(any(c == "V15" for c, _ in errs_neg))

        # Fail on franchise move name
        errs_fran = scan_prompt_v15("He unleashes a Triceratops Fist.", "standup_striking", {"boxing"}, self.lexicon)
        self.assertTrue(any(c == "V15" for c, _ in errs_fran))

        # Fail on out-of-style move alias ("spinning back kick" in pure boxing clip)
        errs_style = scan_prompt_v15("He throws a spinning back kick.", "standup_striking", {"boxing"}, self.lexicon)
        self.assertTrue(any(c == "V15" for c, _ in errs_style))

    def test_v16_screen_side_swap(self) -> None:
        clip = self._base_clip()
        clip["moments"][0]["screen_side_override"] = {"A": "right", "B": "left"}
        res = validate_clip(clip, lexicon=self.lexicon)
        self.assertIn("V16", res.error_codes())

    def test_v17_one_sided_exchange_warning(self) -> None:
        clip = self._base_clip()
        clip["allow_one_sided_probe"] = False
        clip["moments"] = [
            {"frames": 7, "A": {"move": "jab"}, "B": {"move": "head_snap_back"}},
            {"frames": 7, "A": {"move": "cross"}, "B": {"move": "head_snap_back"}},
            {"frames": 8, "A": {"move": "lead_hook"}, "B": {"move": "head_whip_side"}},
            {"frames": 7, "A": {"move": "cross"}, "B": {"move": "head_snap_back"}},
        ]
        res = validate_clip(clip, lexicon=self.lexicon)
        self.assertIn("V17", res.warning_codes())

    # --- M2 & M3: 10-Beat Competitive Boxing Exchange & Deterministic Compilation ---
    def test_10_beat_competitive_boxing_exchange_passes_cleanly(self) -> None:
        res = validate_clip(self.valid_10_beat, lexicon=self.lexicon)
        self.assertEqual(res.errors, [])
        self.assertEqual(res.warnings, [])

    def test_compiler_produces_clean_byte_identical_prompt(self) -> None:
        prompt1, res1 = compile_clip_prompt(self.valid_10_beat, lexicon=self.lexicon)
        prompt2, res2 = compile_clip_prompt(self.valid_10_beat, lexicon=self.lexicon)
        self.assertTrue(res1.ok)
        self.assertTrue(res2.ok)
        self.assertEqual(prompt1, prompt2)
        self.assertIn("=== LAYER 1: CONTINUOUS SUPPORT, FORCE-EVENT & PROP TIMELINE (Labanotation-as-Words) ===", prompt1)
        self.assertIn("=== LAYER 2: sakuga_Xperiment KINEMATIC & CAMERA SCENE GRAPH ===", prompt1)
        # Verify Layer 2 JSON parses cleanly and has schema sakuga_Xperiment
        layer2_str = prompt1.split("=== LAYER 2: sakuga_Xperiment KINEMATIC & CAMERA SCENE GRAPH ===")[1].strip()
        layer2_json = json.loads(layer2_str)
        self.assertEqual(layer2_json["schema"], "sakuga_Xperiment")
        self.assertEqual(layer2_json["duration"], 10.0)

    def test_variation_3_eight_limbs_muay_thai_mma_determinism(self) -> None:
        res = validate_clip(self.valid_var3, lexicon=self.lexicon)
        self.assertEqual(res.errors, [])
        self.assertEqual(res.warnings, [])
        p1, r1 = compile_clip_prompt(self.valid_var3, lexicon=self.lexicon)
        p2, r2 = compile_clip_prompt(self.valid_var3, lexicon=self.lexicon)
        self.assertTrue(r1.ok)
        self.assertTrue(r2.ok)
        self.assertEqual(p1, p2)

    def test_composer_chains_fighter_and_dyad_states_across_clips(self) -> None:
        sheet = {
            "regime": "standup_striking",
            "initial_range": "kick",
            "fighters": copy.deepcopy(self.valid_10_beat["fighters"]),
            "moments": [
                {
                    "regime": "standup_striking",
                    "frames": 6,
                    "A": {"move": "burst_step_in"},
                    "B": {"move": "slip_inside"},
                },
                {
                    "regime": "clinch",
                    "frames": 7,
                    "A": {"move": "clinch_captured_react"},
                    "B": {"move": "clinch_captured_react"},
                },
            ],
        }
        clips, notes = compose_clips(sheet, lexicon=self.lexicon)
        self.assertEqual(len(clips), 2)
        # Clip 1 burst_step_in closed range from 'kick' to 'punch' and set A.coil='loaded_rear'
        self.assertEqual(clips[1]["initial_range"], "punch")
        self.assertEqual(clips[1]["fighters"]["A"]["coil"], "loaded_rear")
        self.assertTrue(any("Chained Clip 1" in n for n in notes))

    # --- M5: Kinetic Chain (V18) — chain as the fourth causal segment ---
    def test_v18_all_card_chains_and_frames_are_valid(self) -> None:
        self.assertEqual(self.lexicon.validation_errors, [])
        for cid, card in self.lexicon.cards_by_id.items():
            self.assertIn("chain", card, f"card '{cid}' has no default chain")
            self.assertIn("chain_frames", card, f"card '{cid}' has no chain_frames")
            self.assertEqual(
                validate_kinetic_chain(
                    card["chain"],
                    owner=cid,
                    chain_frames=card["chain_frames"],
                    require_frames=True,
                ),
                [],
            )

    def test_v18_bad_chain_shoulder_before_hips_rejected(self) -> None:
        # Deliberately out of order: shoulder (rank 5) listed before hips (rank 3).
        bad_chain = "right shoulder drives forward > hips snap square > right heel pivots out > right fist lands on the jaw"
        errs = validate_kinetic_chain(bad_chain, owner="test", chain_frames=[0, 2, 3, 5], require_frames=True)
        self.assertEqual({code for code, _ in errs}, {"V18"})
        messages = " | ".join(msg for _, msg in errs)
        self.assertIn(
            "ground-up order broken at link 2 'hips snap square' (rank 3) after link 1 'right shoulder drives forward' (rank 5)",
            messages,
        )
        self.assertIn("chain must start at the ground", messages)

        # The same bad chain is rejected through the card schema validator.
        bad_card = copy.deepcopy(self.lexicon.cards_by_id["cross"])
        bad_card["chain"] = bad_chain
        card_errs = validate_card(bad_card)
        self.assertTrue(any(code == "V18" for code, _ in card_errs))

    def test_v18_clip_beat_inherits_card_chain_and_accepts_override(self) -> None:
        # Inherit: fixture beats carry no per-beat chain, so the card defaults apply.
        res = validate_clip(self.valid_10_beat, lexicon=self.lexicon)
        self.assertEqual(res.error_codes(), set())

        clip = copy.deepcopy(self.valid_10_beat)
        clip["moments"][1]["A"]["chain"] = "left toe pivots out > hips snap square > left shoulder drives forward > left fist lands on the jaw"
        clip["moments"][1]["A"]["chain_frames"] = [0, 2, 3, 5]
        clip["moments"][1]["B"]["chain"] = "both heels plant > knees dip > hips rock back > head snaps clear of the line"
        clip["moments"][1]["B"]["chain_frames"] = [0, 2, 3, 5]
        res_ok = validate_clip(clip, lexicon=self.lexicon)
        self.assertEqual(res_ok.error_codes(), set())

        # A bad override (shoulder before hips) is caught at clip level.
        clip["moments"][1]["A"]["chain"] = "left shoulder drives forward > hips snap square > left toe pivots out > left fist lands on the jaw"
        res_bad = validate_clip(clip, lexicon=self.lexicon)
        self.assertIn("V18", res_bad.error_codes())

    def test_v18_prompt_scanner_rules(self) -> None:
        good = (
            '{"causal":"C02: requires C01_prev_state -> preserves loaded_momentum -> chain: '
            "left heel pivots out > hips snap square > left arm extends > left fist lands on the chin"
            ' -> causes C02_jab"}'
        )
        self.assertEqual(scan_prompt_v18(good), [])

        # shoulder before hips inside an emitted chain
        bad_order = (
            '{"causal":"C02: requires C01_prev_state -> preserves loaded_momentum -> chain: '
            "right shoulder drives forward > hips snap square > right heel pivots out > right fist lands on the jaw"
            ' -> causes C02_cross"}'
        )
        errs_order = scan_prompt_v18(bad_order)
        self.assertTrue(any("ground-up order broken at link 2" in msg for _, msg in errs_order), errs_order)

        # a '>' separator used in the requires segment, i.e. outside the chain segment
        bad_sep = (
            '{"causal":"C02: requires init_stance > C01_prev_state -> preserves loaded_momentum -> chain: '
            "left heel pivots out > hips snap square > left fist lands on the chin"
            ' -> causes C02_jab"}'
        )
        errs_sep = scan_prompt_v18(bad_sep)
        self.assertTrue(any("used outside a 'chain:' segment" in msg for _, msg in errs_sep), errs_sep)

        # a digit inside the chain segment (frame offsets stay internal)
        bad_digits = (
            '{"causal":"C02: requires C01_prev_state -> preserves loaded_momentum -> chain: '
            "left heel pivots out > hips snap square at frame 2 > left fist lands on the chin"
            ' -> causes C02_jab"}'
        )
        errs_digits = scan_prompt_v18(bad_digits)
        self.assertTrue(any("contains digit '2'" in msg for _, msg in errs_digits), errs_digits)

        # chain_frames leaks into prompt text
        errs_leak = scan_prompt_v18('{"chain_frames":[0,2,3,5]}')
        self.assertTrue(any("leaked into emitted prompt text" in msg for _, msg in errs_leak), errs_leak)

        # a move causal missing the chain segment
        missing = '{"causal":"C02: requires C01_prev_state -> preserves loaded_momentum -> causes C02_jab"}'
        errs_missing = scan_prompt_v18(missing)
        self.assertTrue(any("missing segments [' -> chain: ']" in msg for _, msg in errs_missing), errs_missing)

        # pre-existing canonical '>' sites stay legal: laban movement chain and '<placeholder>' legend
        canonical = (
            '{"laban":{"A":{"chain":"C01_jab_0.00s > C02_cross_0.88s"}}} '
            "MOVEMENT LANGUAGE: <seconds> <performer>: SUPPORT | path in metres."
        )
        self.assertEqual(scan_prompt_v18(canonical), [])

    def test_v18_compiler_splices_chain_as_fourth_segment(self) -> None:
        prompt, res = compile_clip_prompt(self.valid_10_beat, lexicon=self.lexicon, emit_chain_in_causal=True)
        self.assertTrue(res.ok)
        self.assertEqual(scan_prompt_v18(prompt), [])
        self.assertNotIn("chain_frames", prompt)
        self.assertIsNone(self.valid_10_beat["moments"][1]["A"].get("chain"))  # fixture inherits

        jab_chain = (
            "hips snap square > left shoulder drives forward > "
            "left arm extends > left fist lands on the chin"
        )
        self.assertIn(
            f'"causal":"C02: requires C01_prev_state -> preserves loaded_lead_momentum -> chain: {jab_chain} -> causes C02_jab"',
            prompt,
        )

        causals = re.findall(r'"causal":"([^"]*)"', prompt)
        self.assertEqual(len(causals), 11)  # 10 move beats + the 10.0s terminal hold
        move_causals = [causal for causal in causals if "requires" in causal]
        self.assertEqual(len(move_causals), 10)
        for causal in move_causals:
            for marker in (" -> preserves ", " -> chain: ", " -> causes "):
                self.assertIn(marker, causal)

    def test_v18_compiler_beat_override_wins_over_card_chain(self) -> None:
        clip = copy.deepcopy(self.valid_10_beat)
        override = "left toe pivots out > hips snap square > left shoulder drives forward > left fist lands on the jaw"
        clip["moments"][1]["A"]["chain"] = override
        clip["moments"][1]["A"]["chain_frames"] = [0, 2, 3, 5]
        prompt, res = compile_clip_prompt(clip, lexicon=self.lexicon, emit_chain_in_causal=True)
        self.assertTrue(res.ok)
        self.assertIn(f"chain: {override} -> causes C02_jab", prompt)
        default_jab_chain = (
            "hips snap square > left shoulder drives forward > "
            "left arm extends > left fist lands on the chin"
        )
        self.assertNotIn(default_jab_chain, prompt)
        self.assertNotIn("chain_frames", prompt)

    def test_v18_frame_offsets_stay_internal(self) -> None:
        self.assertEqual(validate_chain_frames([0, 2, 3, 5], owner="t", link_count=4, required=True), [])
        errs_zero = validate_chain_frames([1, 2, 3], owner="t", link_count=3, required=True)
        self.assertTrue(any("must start at frame offset 0" in msg for _, msg in errs_zero))
        errs_count = validate_chain_frames([0, 2, 3], owner="t", link_count=4, required=True)
        self.assertTrue(any("has 3 offsets for 4 links" in msg for _, msg in errs_count))
        errs_missing = validate_chain_frames(None, owner="t", link_count=4, required=True)
        self.assertTrue(any("missing 'chain_frames' frame offsets" in msg for _, msg in errs_missing))

    # --- M6: Weight Split & CoG (V19), Camera Occlusion (V20), Spacing Curves (V21), Impulse Tier (V22) ---
    def test_v19_weight_split_and_com_outside_support_check(self) -> None:
        # Standing fighter with CoG outside_support_falling without knockdown/catch_step -> V19 error
        clip = self._base_clip()
        clip["moments"][0]["A"]["com_position"] = "outside_support_falling"
        res = validate_clip(clip, lexicon=self.lexicon)
        self.assertIn("V19", res.error_codes())

        # With explicit catch_step=True recovery -> passes V19
        clip["moments"][0]["A"]["catch_step"] = True
        res_ok = validate_clip(clip, lexicon=self.lexicon)
        self.assertNotIn("V19", res_ok.error_codes())

        # Invalid weight_split not summing to 100 -> V19 error
        clip_bad_ws = self._base_clip()
        clip_bad_ws["moments"][0]["A"]["weight_split"] = [80, 40]
        res_ws = validate_clip(clip_bad_ws, lexicon=self.lexicon)
        self.assertIn("V19", res_ws.error_codes())

    def test_v20_camera_angle_limb_occlusion_warning(self) -> None:
        # worm_eye camera hides lead_leg/rear_leg/hips -> warns V20 on a low_calf_kick (rear_leg)
        clip = self._base_clip()
        clip["initial_range"] = "kick"
        clip["fighters"]["A"]["style"] = "mma"
        clip["fighters"]["B"]["style"] = "mma"
        clip["moments"][0]["camera"] = "worm_eye_low_angle"
        clip["moments"][0]["A"]["move"] = "low_calf_kick"
        clip["moments"][0]["B"]["move"] = "lead_leg_buckle"
        res = validate_clip(clip, lexicon=self.lexicon)
        self.assertIn("V20", res.warning_codes())

        # over_B_right_shoulder hides lead_hand -> warns V20 on a jab (lead_hand)
        clip2 = self._base_clip()
        clip2["moments"][0]["camera"] = "over_B_right_shoulder_tight"
        res2 = validate_clip(clip2, lexicon=self.lexicon)
        self.assertIn("V20", res2.warning_codes())

    def test_v21_spacing_curves_and_phases_validation(self) -> None:
        clip = self._base_clip()
        clip["moments"][0]["A"]["easing_curve"] = "linear_robot_constant_speed"
        res = validate_clip(clip, lexicon=self.lexicon)
        self.assertIn("V21", res.error_codes())

        clip2 = self._base_clip()
        clip2["moments"][0]["A"]["spacing_phases"] = {
            "slow_in": [0, 2],
            "snap": [3, 5],  # non-contiguous gap between 2 and 3
            "hold": [5, 7],
            "ease_out": [7, 8],
        }
        res2 = validate_clip(clip2, lexicon=self.lexicon)
        self.assertIn("V21", res2.error_codes())

    def test_v22_impulse_tier_and_reaction_matching(self) -> None:
        # Fail: light jab (impulse_tier=1) triggering tier-3 knockout_canvas_collapse on a non-hero beat
        clip_over = self._base_clip()
        clip_over["moments"][0]["A"]["move"] = "jab"
        clip_over["moments"][0]["B"]["move"] = "knockout_canvas_collapse"
        res_over = validate_clip(clip_over, lexicon=self.lexicon)
        self.assertIn("V22", res_over.error_codes())

        # Fail: heavy rear_overhand (impulse_tier=3) under-sold by tier-2 reaction on a non-hero beat
        clip_under = self._base_clip()
        clip_under["fighters"]["A"]["coil"] = "loaded_rear"
        clip_under["moments"][0]["frames"] = 9
        clip_under["moments"][0]["A"]["move"] = "rear_overhand"
        clip_under["moments"][0]["B"] = {"move": "head_snap_back", "impulse_tier": 2}
        res_under = validate_clip(clip_under, lexicon=self.lexicon)
        self.assertIn("V22", res_under.error_codes())

        # Pass: heavy rear_overhand paired with tier-3 knockout_canvas_collapse
        clip_pass = copy.deepcopy(clip_under)
        clip_pass["moments"][0]["B"] = {"move": "knockout_canvas_collapse"}
        res_pass = validate_clip(clip_pass, lexicon=self.lexicon)
        self.assertNotIn("V22", res_pass.error_codes())

    # --- M4: Render Packet Generation ---
    def test_m4_render_packet_generation(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            bundle = generate_m4_packets(Path(tmpdir))
            self.assertEqual(bundle["meta"]["paid_calls_made_by_agent"], 0)
            self.assertIn("H1_plain_caption_vs_expert_names", bundle["hypothesis_packets"])
            self.assertIn("H5_four_limb_occupancy_vs_single_limb", bundle["hypothesis_packets"])
            self.assertIn("H6_fluid_coil_chained_vs_neutral_reset", bundle["hypothesis_packets"])
            self.assertGreaterEqual(len(bundle["boxing_word_probes"]), 25)

    # --- M7: Original e91c686 Compiler Lock, Compiler Bug Fixes, KB Bridge & Closed-Loop ---
    def test_m7_original_e91c686_sakuga_compiler_preserved(self) -> None:
        import subprocess
        repo_root = Path(__file__).parent.parent
        gm1 = repo_root / "examples" / "gold_master_1_blade_exchange.json"
        gm2 = repo_root / "examples" / "gold_master_2_disarm_dual_blade.json"
        script = repo_root / "scripts" / "sakuga_compiler.py"
        for gm in (gm1, gm2):
            proc = subprocess.run(
                ["python3", str(script), "lint", str(gm)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertIn("0 errors, 0 warnings", proc.stdout)

    def test_m7_compiler_bug_fixes_in_variation_3(self) -> None:
        prompt, res = compile_clip_prompt(self.valid_var3, lexicon=self.lexicon)
        self.assertTrue(res.ok)
        # 1. No empty 'L_arm:left arm ;' split bug
        self.assertNotIn("L_arm:left arm ;", prompt)
        # 2. 'slashing_rear_elbow' does not match 'shin' substring
        self.assertNotIn("A_slashing_rear_elbow_windup -> hit:A_right_shin", prompt)
        self.assertIn("hit:A_right_elbow_and_forearm_into_B_jawline_and_chin", prompt)
        # 3. Passive blocks at 2.64s and 7.04s record B's strike meeting A's guard
        self.assertIn("hit:B_right_fist_cross_meets_A_vertical_forearm_shell", prompt)
        self.assertIn("hit:B_right_fist_cross_meets_A_tucked_left_elbow_guard", prompt)
        # 4. Wardrobe legend dynamically reflects beat-sheet wardrobe
        self.assertIn("midnight-blue shorts, white wrist tape, gold ankle wraps", prompt)

    def test_m7_knowledge_base_bridge_and_bundle_integrity(self) -> None:
        self.assertTrue((IN_REPO_KB_DIR / "ai_video_compiler.db").is_file())
        ok, errs = verify_bundle_integrity()
        self.assertTrue(ok, errs)
        ver = kb_verify()
        self.assertTrue(ver["ok"], ver)
        directives = load_semantic_directives()
        if directives:
            self.assertEqual(len(directives), 64)
            sync_res = sync_lexicon_gaps_to_memory()
            self.assertGreaterEqual(sync_res["concepts_synced"], 44)
            hits = kb_find("hitstop", limit=5)
            self.assertTrue(hits["passages"] or hits["concepts"])
            sample_dir = next(iter(directives.values()))
            look = kb_lookup(moment=sample_dir["moment_type"], slot=sample_dir["slot_id"])
            self.assertTrue(look["directives"] or look["passages"])
            pre_intent = query_kb_prior_to_semantic_intent(self.valid_var3)
            self.assertEqual(pre_intent["bundle_dir"], str(IN_REPO_KB_DIR))
            self.assertTrue(pre_intent["knobs"])
            self.assertTrue(pre_intent["animation_grammar_rules"])
            self.assertTrue(pre_intent["pulled_relations"])
            self.assertTrue(pre_intent["causal_chains"])
            ver_after = kb_verify()
            self.assertTrue(ver_after["ok"], ver_after)

    def test_m7_closed_loop_verdict_repair_and_next_clip_handoff(self) -> None:
        # 1. Parse scorecard markdown
        sample_md = """
| Prompt Variant | Engine / Model ID | Verdict | Notes |
|---|---|---|---|
| compiled | seedance-2.0 | works | Clean hitstop and zero torso merge |
"""
        parsed = parse_scorecard_markdown(sample_md)
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0]["verdict"], "works")

        # 2. Plan & apply RFC 6902 localized repair across failure classes
        clip = copy.deepcopy(self.valid_var3)
        for fclass in ("contact_flicker", "phantom_force", "dead_contact", "pose_reset", "camera_occlusion"):
            plan = plan_localized_repair(clip, beat_index=2, failure_type=fclass)
            self.assertIn(fclass, plan["failure_id"])
            self.assertTrue(len(plan["patch"]) >= 1)
            patched = apply_localized_repair(clip, plan)
            self.assertIsInstance(patched, dict)

        # 3. Build next-clip handoff at t=10.0s
        handoff = build_next_clip_handoff(self.valid_var3)
        self.assertEqual(handoff["fighters"]["A"]["screen_side"], "left")
        self.assertEqual(handoff["fighters"]["B"]["screen_side"], "right")
        self.assertEqual(handoff["fighters"]["B"]["support"], "crouched")

    # --- M8: Protected 05:34 (e91c686) SAKUGA-MLLM-3.1-CAUSAL Code Path + Pre-Intent KB Integration ---
    def test_m8_protected_0534_causal_path_and_kb_integration(self) -> None:
        # 1. Verify scripts/sakuga_compiler.py is byte-identical to e91c686
        ok_prot, sha = verify_original_compiler_protection()
        self.assertTrue(ok_prot, sha)

        # 2. Path A: Compile the protected 05:34 template with pre-intent KB query
        prompt_a, spec_a, kb_a, errs_a, warns_a = compile_original_causal_spec_with_kb(
            ORIGINAL_TEMPLATE_PATH,
            taste="clean",
            style="cel_default",
        )
        self.assertEqual(errs_a, [])
        self.assertEqual(warns_a, [])
        self.assertEqual(spec_a["schema"], "SAKUGA-MLLM-3.1-CAUSAL")
        self.assertNotIn("=== LAYER 1", prompt_a)
        self.assertNotIn("MOVEMENT LANGUAGE:", prompt_a)
        self.assertTrue(kb_a["knobs"])
        self.assertTrue(kb_a["pulled_relations"])
        for beat in spec_a["A_beats"]:
            self.assertEqual(set(beat.keys()).intersection(FORBIDDEN_XPERIMENT_KEYS), set())
        for beat in spec_a["B_track"]:
            self.assertEqual(set(beat.keys()).intersection(FORBIDDEN_XPERIMENT_KEYS), set())

        # 3. Path B: Compile a beat-sheet into a pure 05:34 SAKUGA-MLLM-3.1-CAUSAL single-layer prompt via KB
        prompt_b, spec_b, kb_b, val_b = compile_beatsheet_to_original_0534_causal(
            self.valid_10_beat,
            lexicon=self.lexicon,
            taste="nakamura",
            style="cel_default",
        )
        self.assertTrue(val_b.ok, val_b.errors)
        self.assertEqual(val_b.warnings, [])
        self.assertEqual(spec_b["schema"], "SAKUGA-MLLM-3.1-CAUSAL")
        self.assertNotIn("=== LAYER 1", prompt_b)
        self.assertNotIn("MOVEMENT LANGUAGE:", prompt_b)
        self.assertTrue(kb_b["knobs"])
        self.assertTrue(kb_b["pulled_relations"])
        for beat in spec_b["A_beats"]:
            self.assertEqual(set(beat.keys()).intersection(FORBIDDEN_XPERIMENT_KEYS), set())
            self.assertNotIn(" -> chain: ", beat["causal"])
        for beat in spec_b["B_track"]:
            self.assertEqual(set(beat.keys()).intersection(FORBIDDEN_XPERIMENT_KEYS), set())

        # 4. Verify KB integrity remains 25/25 after recording usage from both 05:34 paths
        ver = kb_verify()
        self.assertTrue(ver["ok"], ver)


if __name__ == "__main__":
    unittest.main()
