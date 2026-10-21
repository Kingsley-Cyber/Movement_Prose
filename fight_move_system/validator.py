"""§6. Deterministic Beat-Sheet & Clip Validator (V01–V17)."""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from .dyad import DyadState
from .enums import REGIMES
from .lexicon import Lexicon
from .state import FighterState


@dataclass
class ValidationResult:
    errors: List[Tuple[str, str]] = field(default_factory=list)
    warnings: List[Tuple[str, str]] = field(default_factory=list)
    final_fighter_a: Optional[FighterState] = None
    final_fighter_b: Optional[FighterState] = None
    final_dyad: Optional[DyadState] = None

    @property
    def ok(self) -> bool:
        return len(self.errors) == 0

    def error_codes(self) -> Set[str]:
        return {code for code, _ in self.errors}

    def warning_codes(self) -> Set[str]:
        return {code for code, _ in self.warnings}


def load_thresholds() -> Dict[str, Any]:
    path = Path(__file__).parent / "config" / "thresholds.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_quarantine_ledger() -> Dict[str, Any]:
    path = Path(__file__).parent / "ledgers" / "quarantined_pairs.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_clip(
    clip: Dict[str, Any],
    lexicon: Optional[Lexicon] = None,
    thresholds: Optional[Dict[str, Any]] = None,
    quarantine_ledger: Optional[Dict[str, Any]] = None,
) -> ValidationResult:
    """Validate a single clip beat-sheet dictionary against V01–V14, V16–V17."""
    res = ValidationResult()
    lex = lexicon or Lexicon.load_default()
    thresh = thresholds or load_thresholds()
    quarantine = quarantine_ledger or load_quarantine_ledger()

    if lex.validation_errors:
        res.errors.extend(lex.validation_errors)

    clip_regime = clip.get("regime", "standup_striking")
    if clip_regime not in REGIMES:
        res.errors.append(("V01", f"Clip has unknown regime '{clip_regime}'"))

    fighters_cfg = clip.get("fighters", {})
    a_cfg = fighters_cfg.get("A", {})
    b_cfg = fighters_cfg.get("B", {})

    fighter_a = FighterState(
        id="A",
        style=a_cfg.get("style", "boxing"),
        stance=a_cfg.get("stance", "orthodox"),
        screen_side=a_cfg.get("screen_side", "left"),
        facing=a_cfg.get("facing", "right"),
        support=a_cfg.get("support", "standing"),
        coil=a_cfg.get("coil", "neutral"),
        guard_lead=a_cfg.get("guard_lead", "high"),
        guard_rear=a_cfg.get("guard_rear", "high"),
    )
    fighter_b = FighterState(
        id="B",
        style=b_cfg.get("style", "boxing"),
        stance=b_cfg.get("stance", "orthodox"),
        screen_side=b_cfg.get("screen_side", "right"),
        facing=b_cfg.get("facing", "left"),
        support=b_cfg.get("support", "standing"),
        coil=b_cfg.get("coil", "neutral"),
        guard_lead=b_cfg.get("guard_lead", "high"),
        guard_rear=b_cfg.get("guard_rear", "high"),
    )

    res.errors.extend(fighter_a.validate_enums())
    res.errors.extend(fighter_b.validate_enums())

    dyad = DyadState(range_band=clip.get("initial_range", "punch"))
    res.errors.extend(dyad.validate_enums())

    if res.errors:
        return res

    initial_sides = (fighter_a.screen_side, fighter_b.screen_side)
    moments: List[Dict[str, Any]] = clip.get("moments", [])
    min_frames_table = thresh.get("class_min_frames", {})
    max_tier_3 = thresh.get("max_tier_3_moves_per_clip", {}).get("value", 1)

    tier_3_count = 0
    seen_classes: Set[str] = set()
    seen_moves: Set[str] = set()
    offensive_counts = {"A": 0, "B": 0}
    in_active_exchange = False

    for idx, moment in enumerate(moments):
        is_boundary = idx == 0 or idx == len(moments) - 1
        frames = moment.get("frames", 8)

        # V16: Check if moment attempts to swap screen sides
        if "screen_side_override" in moment:
            override = moment["screen_side_override"]
            if (override.get("A", fighter_a.screen_side), override.get("B", fighter_b.screen_side)) != initial_sides:
                res.errors.append(
                    ("V16", f"Moment {idx} swaps fighter screen sides from {initial_sides} to {override}")
                )

        a_action = moment.get("A")
        b_action = moment.get("B")

        a_card = None
        b_card = None

        unknown_move_in_moment = False
        if a_action:
            mid = a_action.get("move")
            a_card = lex.get(mid)
            if a_card is None:
                res.errors.append(("V01", f"Moment {idx} Fighter A has unknown move '{mid}'"))
                unknown_move_in_moment = True
        if b_action:
            mid = b_action.get("move")
            b_card = lex.get(mid)
            if b_card is None:
                res.errors.append(("V01", f"Moment {idx} Fighter B has unknown move '{mid}'"))
                unknown_move_in_moment = True

        if unknown_move_in_moment:
            continue

        # Snapshot pre-supports before applying state changes
        a_pre_support = fighter_a.support
        b_pre_support = fighter_b.support

        # Handle simultaneous overlap action if present (e.g. slip + counter in same moment)
        for f_state, f_act, f_card in [(fighter_a, a_action, a_card), (fighter_b, b_action, b_card)]:
            if f_act and "overlaps_move" in f_act:
                ov_id = f_act["overlaps_move"]
                ov_card = lex.get(ov_id)
                if ov_card is None:
                    res.errors.append(("V01", f"Moment {idx} Fighter {f_state.id} has unknown overlaps_move '{ov_id}'"))
                else:
                    ov_errs, ov_warns = f_state.check_and_apply_move(
                        card=ov_card,
                        clip_regime=clip_regime,
                        current_range=dyad.range_band,
                        in_active_exchange=in_active_exchange,
                        min_frames_table=min_frames_table,
                        beat_frames=f_act.get("frames", frames),
                        is_boundary_beat=is_boundary,
                    )
                    res.errors.extend(ov_errs)
                    res.warnings.extend(ov_warns)

        # Validate Dyad Coupling BEFORE mutating support states
        if a_card and a_card["contact"] in {"strike", "grapple"}:
            offensive_counts["A"] += 1
            in_active_exchange = True
            c_errs = dyad.validate_contact_coupling(
                attacker_pre_support=a_pre_support,
                defender_pre_support=b_pre_support,
                attacker=fighter_a,
                defender=fighter_b,
                attack_card=a_card,
                reaction_card=b_card,
                reaction_beat=b_action,
            )
            res.errors.extend(c_errs)

        if b_card and b_card["contact"] in {"strike", "grapple"}:
            offensive_counts["B"] += 1
            in_active_exchange = True
            c_errs = dyad.validate_contact_coupling(
                attacker_pre_support=b_pre_support,
                defender_pre_support=a_pre_support,
                attacker=fighter_b,
                defender=fighter_a,
                attack_card=b_card,
                reaction_card=a_card,
                reaction_beat=a_action,
            )
            res.errors.extend(c_errs)

        # Apply Fighter A move
        if a_card:
            errs, warns = fighter_a.check_and_apply_move(
                card=a_card,
                clip_regime=clip_regime,
                current_range=dyad.range_band,
                in_active_exchange=in_active_exchange,
                min_frames_table=min_frames_table,
                beat_frames=a_action.get("frames", frames),
                is_boundary_beat=is_boundary,
            )
            res.errors.extend(errs)
            res.warnings.extend(warns)
            seen_classes.add(a_card["class"])
            seen_moves.add(a_card["id"])
            if a_card["bleed_tier"] == 3:
                tier_3_count += 1

        # Apply Fighter B move
        if b_card:
            errs, warns = fighter_b.check_and_apply_move(
                card=b_card,
                clip_regime=clip_regime,
                current_range=dyad.range_band,
                in_active_exchange=in_active_exchange,
                min_frames_table=min_frames_table,
                beat_frames=b_action.get("frames", frames),
                is_boundary_beat=is_boundary,
            )
            res.errors.extend(errs)
            res.warnings.extend(warns)
            seen_classes.add(b_card["class"])
            seen_moves.add(b_card["id"])
            if b_card["bleed_tier"] == 3:
                tier_3_count += 1

        # Apply range delta (from primary locomotion/attack/reaction)
        for card in (a_card, b_card):
            if card:
                delta = card["post"].get("range_delta", "same")
                if delta != "same":
                    dyad.apply_range_delta(delta)
                    if dyad.range_band in {"outside", "kick"}:
                        in_active_exchange = False
                    break

        # V08: Clinch symmetry after moment resolves
        res.errors.extend(DyadState.validate_clinch_symmetry(fighter_a, fighter_b))

    # V13: Bleed budget (tier-3 count per clip)
    if tier_3_count > max_tier_3:
        res.warnings.append(
            (
                "V13",
                f"Clip has {tier_3_count} bleed_tier==3 moves, exceeding hypothesis budget of {max_tier_3}",
            )
        )

    # V14: Quarantined class or move pairs
    for entry in quarantine.get("quarantined_class_pairs", []):
        pair = entry.get("pair", [])
        if len(pair) == 2 and pair[0] in seen_classes and pair[1] in seen_classes:
            res.errors.append(
                (
                    "V14",
                    f"Quarantined class pair {pair} shares clip ({entry.get('evidence_note', '')})",
                )
            )
    for entry in quarantine.get("quarantined_move_pairs", []):
        pair = entry.get("pair", [])
        if len(pair) == 2 and pair[0] in seen_moves and pair[1] in seen_moves:
            res.errors.append(
                (
                    "V14",
                    f"Quarantined move pair {pair} shares clip ({entry.get('evidence_note', '')})",
                )
            )

    # V17: Competitive exchange check (if clip has >= 4 moments and is not a single-move probe)
    if len(moments) >= 4 and not clip.get("allow_one_sided_probe", False):
        if offensive_counts["A"] == 0 or offensive_counts["B"] == 0:
            res.warnings.append(
                (
                    "V17",
                    f"One-sided exchange: offensive counts A={offensive_counts['A']}, B={offensive_counts['B']}",
                )
            )

    res.final_fighter_a = fighter_a
    res.final_fighter_b = fighter_b
    res.final_dyad = dyad
    return res
