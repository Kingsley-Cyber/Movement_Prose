"""§5.2 Shared Dyad State & Opponent-Coupled Validation Rules."""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from .enums import RANGE_BANDS, RANGE_ORDER
from .state import FighterState


def resolve_camera_force(force_local: str, attacker: FighterState) -> str:
    """Resolve a move card's body-relative force_local into a camera-relative force direction."""
    if force_local == "none":
        return "none"
    if force_local in {"upward", "downward"}:
        return force_local
    if force_local == "forward_straight":
        return "toward_screen_right" if attacker.screen_side == "left" else "toward_screen_left"
    if force_local == "pull_inward":
        return "toward_screen_left" if attacker.screen_side == "left" else "toward_screen_right"
    if force_local == "arc_lead_to_rear":
        # A lead hook sweeps from lead side across toward rear side (and forward toward opponent)
        return "toward_screen_right" if attacker.screen_side == "left" else "toward_screen_left"
    if force_local == "arc_rear_to_lead":
        return "toward_screen_right" if attacker.screen_side == "left" else "toward_screen_left"
    return "none"


def resolve_reaction_force(reaction_card: Dict[str, Any], defender: FighterState, attacker: FighterState) -> str:
    """Resolve the direction of a defender's reaction (unless explicitly overridden on the beat)."""
    fl = reaction_card["force_local"]
    if fl == "none":
        return "none"
    if fl in {"upward", "downward"}:
        return fl
    # Standard impact reactions (head_snap_back, head_whip_side, torso_fold_rib_hit) move away from the attacker
    if fl in {"forward_straight", "arc_lead_to_rear", "arc_rear_to_lead"}:
        return "toward_screen_right" if attacker.screen_side == "left" else "toward_screen_left"
    if fl == "pull_inward":
        return "toward_screen_left" if attacker.screen_side == "left" else "toward_screen_right"
    return "none"


@dataclass
class DyadState:
    range_band: str = "punch"

    def validate_enums(self) -> List[Tuple[str, str]]:
        if self.range_band not in RANGE_BANDS:
            return [("V01", f"Dyad has unknown range_band '{self.range_band}'")]
        return []

    def apply_range_delta(self, delta: str) -> None:
        if delta == "same" or not delta:
            return
        if delta == "to_clinch":
            self.range_band = "clinch"
            return
        if delta == "to_punch":
            self.range_band = "punch"
            return
        if delta == "to_kick":
            self.range_band = "kick"
            return
        if delta == "to_ground":
            self.range_band = "ground"
            return
        idx = RANGE_ORDER.index(self.range_band)
        if delta == "close_one":
            self.range_band = RANGE_ORDER[min(idx + 1, len(RANGE_ORDER) - 1)]
        elif delta == "open_one":
            self.range_band = RANGE_ORDER[max(idx - 1, 0)]

    def validate_contact_coupling(
        self,
        attacker_pre_support: str,
        defender_pre_support: str,
        attacker: FighterState,
        defender: FighterState,
        attack_card: Dict[str, Any],
        reaction_card: Optional[Dict[str, Any]],
        reaction_beat: Optional[Dict[str, Any]] = None,
        is_hero: bool = False,
    ) -> List[Tuple[str, str]]:
        """Validate V05, V06, V07, V08, V09, V22 on a contact beat."""
        errors: List[Tuple[str, str]] = []
        aid = attack_card["id"]

        # V05: Range and partner posture check
        if self.range_band not in attack_card["partner_pre"]["range"]:
            errors.append(
                (
                    "V05",
                    f"Attack '{aid}' requires range in {attack_card['partner_pre']['range']}, but dyad range is '{self.range_band}'",
                )
            )
        if defender_pre_support not in attack_card["partner_pre"]["support"]:
            errors.append(
                (
                    "V05",
                    f"Attack '{aid}' requires partner support in {attack_card['partner_pre']['support']}, but partner '{defender.id}' support is '{defender_pre_support}'",
                )
            )

        # V09: Contact must have a paired reaction beat from partner_reaction_classes
        if attack_card["contact"] in {"strike", "grapple"}:
            if reaction_card is None:
                errors.append(
                    (
                        "V09",
                        f"Contact move '{aid}' by '{attacker.id}' has no paired reaction beat from partner '{defender.id}'",
                    )
                )
                return errors

            if reaction_card["class"] not in attack_card["partner_reaction_classes"]:
                errors.append(
                    (
                        "V09",
                        f"Partner reaction '{reaction_card['id']}' ({reaction_card['class']}) not in '{aid}' allowed partner_reaction_classes {attack_card['partner_reaction_classes']}",
                    )
                )

            # V06: Hit level match (for IMPACT.REACTION and BLOCK.*)
            if reaction_card["class"] in {"IMPACT.REACTION", "BLOCK.PASSIVE", "BLOCK.ACTIVE"}:
                if reaction_card["level"] != attack_card["level"]:
                    errors.append(
                        (
                            "V06",
                            f"Attack '{aid}' level '{attack_card['level']}' does not match reaction '{reaction_card['id']}' level '{reaction_card['level']}'",
                        )
                    )

            # V07: Force direction and partner recoil direction match
            if reaction_card["class"] == "IMPACT.REACTION":
                att_force = resolve_camera_force(attack_card["force_local"], attacker)
                if reaction_beat and "recoil_force_override" in reaction_beat:
                    def_recoil = reaction_beat["recoil_force_override"]
                else:
                    def_recoil = resolve_reaction_force(reaction_card, defender, attacker)
                if att_force != "none" and def_recoil != "none" and att_force != def_recoil:
                    errors.append(
                        (
                            "V07",
                            f"Attack '{aid}' camera force '{att_force}' conflicts with partner recoil direction '{def_recoil}'",
                        )
                    )

            # V22: Impulse Tier & Reaction Strength Matching
            if reaction_card["class"] in {"IMPACT.REACTION", "BLOCK.PASSIVE", "BLOCK.ACTIVE"}:
                att_tier = int(attack_card.get("impulse_tier", 1))
                def_tier = int(
                    reaction_beat.get("impulse_tier", reaction_card.get("impulse_tier", 1))
                    if isinstance(reaction_beat, dict)
                    else reaction_card.get("impulse_tier", 1)
                )
                if is_hero:
                    # Hero finisher beat upgrades a medium (tier 2) strike or reaction to heavy (tier 3)
                    effective_att = max(att_tier, 3) if att_tier >= 2 else att_tier
                    effective_def = max(def_tier, 3) if def_tier >= 2 else def_tier
                else:
                    effective_att = att_tier
                    effective_def = def_tier

                if reaction_card["class"] == "IMPACT.REACTION":
                    if effective_def < effective_att:
                        errors.append(
                            (
                                "V22",
                                f"Attack '{aid}' (impulse_tier={effective_att}) under-sold by weaker reaction '{reaction_card['id']}' (impulse_tier={effective_def})",
                            )
                        )
                    elif effective_def > effective_att + 1 or (def_tier == 3 and not is_hero and att_tier < 2):
                        errors.append(
                            (
                                "V22",
                                f"Attack '{aid}' (impulse_tier={att_tier}) over-sold by excessive reaction '{reaction_card['id']}' (impulse_tier={def_tier})",
                            )
                        )
                    elif reaction_card["id"] == "knockout_canvas_collapse" and not is_hero and att_tier < 3:
                        errors.append(
                            (
                                "V22",
                                f"Attack '{aid}' (impulse_tier={att_tier}) over-sold by knockout reaction '{reaction_card['id']}' (impulse_tier={def_tier})",
                            )
                        )
                else:
                    # BLOCK.ACTIVE / BLOCK.PASSIVE
                    if abs(effective_att - effective_def) > 1:
                        errors.append(
                            (
                                "V22",
                                f"Attack '{aid}' (impulse_tier={effective_att}) mismatched with block '{reaction_card['id']}' (impulse_tier={effective_def})",
                            )
                        )

        return errors

    @staticmethod
    def validate_clinch_symmetry(fighter_a: FighterState, fighter_b: FighterState) -> List[Tuple[str, str]]:
        """V08: Clinch symmetry check after a moment resolves."""
        a_clinch = fighter_a.support == "clinched"
        b_clinch = fighter_b.support == "clinched"
        if a_clinch != b_clinch:
            return [
                (
                    "V08",
                    f"Asymmetric clinch state: A.support='{fighter_a.support}' vs B.support='{fighter_b.support}'",
                )
            ]
        return []
