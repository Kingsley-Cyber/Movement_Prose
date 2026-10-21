"""§5.1 Fighter State Machine & §5.3 Fluid Chaining Rules."""

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

from .enums import COILS, FACINGS, GUARDS, SCREEN_SIDES, STANCES, STYLES, SUPPORT_BASES


@dataclass
class FighterState:
    id: str
    style: str = "boxing"
    stance: str = "orthodox"
    screen_side: str = "left"
    facing: str = "right"
    support: str = "standing"
    coil: str = "neutral"
    guard_lead: str = "high"
    guard_rear: str = "high"

    def validate_enums(self) -> List[Tuple[str, str]]:
        errs: List[Tuple[str, str]] = []
        if self.style not in STYLES:
            errs.append(("V01", f"Fighter '{self.id}' has unknown style '{self.style}'"))
        if self.stance not in STANCES:
            errs.append(("V01", f"Fighter '{self.id}' has unknown stance '{self.stance}'"))
        if self.screen_side not in SCREEN_SIDES:
            errs.append(("V01", f"Fighter '{self.id}' has unknown screen_side '{self.screen_side}'"))
        if self.facing not in FACINGS:
            errs.append(("V01", f"Fighter '{self.id}' has unknown facing '{self.facing}'"))
        if self.support not in SUPPORT_BASES:
            errs.append(("V01", f"Fighter '{self.id}' has unknown support '{self.support}'"))
        if self.coil not in COILS:
            errs.append(("V01", f"Fighter '{self.id}' has unknown coil '{self.coil}'"))
        if self.guard_lead not in GUARDS:
            errs.append(("V01", f"Fighter '{self.id}' has unknown guard_lead '{self.guard_lead}'"))
        if self.guard_rear not in GUARDS:
            errs.append(("V01", f"Fighter '{self.id}' has unknown guard_rear '{self.guard_rear}'"))
        return errs

    def limb_words(self) -> Dict[str, str]:
        """Deterministically resolve lead/rear limbs to concrete left/right words."""
        if self.stance == "orthodox":
            return {
                "lead_hand": "left",
                "rear_hand": "right",
                "lead_leg": "left",
                "rear_leg": "right",
                "lead_side": "left",
                "rear_side": "right",
            }
        return {
            "lead_hand": "right",
            "rear_hand": "left",
            "lead_leg": "right",
            "rear_leg": "left",
            "lead_side": "right",
            "rear_side": "left",
        }

    def check_and_apply_move(
        self,
        card: Dict[str, Any],
        clip_regime: str,
        current_range: str,
        in_active_exchange: bool,
        min_frames_table: Dict[str, Any],
        beat_frames: int,
        is_boundary_beat: bool = False,
    ) -> Tuple[List[Tuple[str, str]], List[Tuple[str, str]]]:
        """Validate a single fighter's move against style, regime, support, coil, and duration.
        Returns (errors, warnings) and mutates self to post-state.
        """
        errors: List[Tuple[str, str]] = []
        warnings: List[Tuple[str, str]] = []
        cid = card["id"]

        # V02: move legal for fighter's style
        if self.style not in card["styles"]:
            errors.append(
                ("V02", f"Fighter '{self.id}' move '{cid}' is not legal for style '{self.style}'")
            )

        # V03: move regime matches clip regime (unless transition on a boundary beat)
        card_regimes = card["regimes"]
        if clip_regime not in card_regimes:
            if not (is_boundary_beat and "transition" in card_regimes):
                errors.append(
                    (
                        "V03",
                        f"Move '{cid}' regimes {card_regimes} do not match clip regime '{clip_regime}'",
                    )
                )

        # V04: support base precondition
        if self.support not in card["pre"]["support"]:
            errors.append(
                (
                    "V04",
                    f"Fighter '{self.id}' support '{self.support}' not in move '{cid}' pre.support {card['pre']['support']}",
                )
            )

        # V04 & V11: coil precondition / fluid coil chain
        if self.coil not in card["pre"]["coil"]:
            # If the fighter is in standing/crouched support but the coil doesn't chain cleanly:
            # In strict mode, V04 checks if the move is fundamentally impossible from this state,
            # while V11 flags a coil chain break inside an exchange.
            if self.coil in {"spinning_cw", "spinning_ccw", "overcommitted_forward"}:
                errors.append(
                    (
                        "V04",
                        f"Fighter '{self.id}' coil '{self.coil}' not in move '{cid}' pre.coil {card['pre']['coil']}",
                    )
                )
            else:
                warnings.append(
                    (
                        "V11",
                        f"Fighter '{self.id}' coil chain break: current coil '{self.coil}' not in move '{cid}' pre.coil {card['pre']['coil']}",
                    )
                )

        # V10: neutral reset inside an active close-range exchange (stiffness)
        if (
            card["class"] == "RECOVERY.RESET"
            and in_active_exchange
            and current_range in {"punch", "pocket", "clinch"}
        ):
            warnings.append(
                (
                    "V10",
                    f"Fighter '{self.id}' performs neutral reset '{cid}' inside an active '{current_range}' exchange (stiffness)",
                )
            )

        # V12: beat shorter than class minimum (hypothesis)
        c_class = card["class"]
        min_f_entry = min_frames_table.get(c_class, {})
        min_f = min_f_entry.get("value", 4) if isinstance(min_f_entry, dict) else 4
        if beat_frames < min_f:
            warnings.append(
                (
                    "V12",
                    f"Move '{cid}' ({c_class}) duration {beat_frames}f is shorter than hypothesis minimum {min_f}f",
                )
            )

        # Apply post-state
        self.support = card["post"]["support"]
        self.coil = card["post"]["coil"]
        return errors, warnings
