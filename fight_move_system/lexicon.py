"""§4. Move Card Schema Validator & Lexicon Registry."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .chain import validate_kinetic_chain
from .enums import (
    BLEED_TIERS,
    COILS,
    COM_POSITIONS,
    CONTACTS,
    EASING_CURVES,
    EFFORT_FLOW,
    EFFORT_SPACE,
    EFFORT_TIME,
    EFFORT_WEIGHT,
    FORCE_LOCAL,
    HINGES,
    IMPULSE_TIERS,
    LEVELS,
    LIMBS,
    MOVE_CLASSES,
    PATHS,
    RANGE_BANDS,
    RANGE_DELTAS,
    REGIMES,
    STYLES,
    SUPPORT_BASES,
)

REQUIRED_CARD_FIELDS = {
    "id",
    "class",
    "aliases",
    "caption_words",
    "limb",
    "hinge",
    "path",
    "level",
    "contact",
    "pre",
    "post",
    "partner_pre",
    "partner_reaction_classes",
    "force_local",
    "off_limbs",
    "regimes",
    "styles",
    "bleed_tier",
    "effort",
    "probe",
    "chain",
    "chain_frames",
    "weight_split",
    "com_position",
    "easing_curve",
    "spacing_phases",
    "impulse_tier",
}


def validate_spacing_phases(phases: Any, owner: str) -> List[Tuple[str, str]]:
    """V21: Validate spacing_phases dict {slow_in, snap, hold, ease_out}."""
    errors: List[Tuple[str, str]] = []
    if not isinstance(phases, dict):
        return [("V21", f"{owner}: 'spacing_phases' must be a dict")]
    required_keys = ["slow_in", "snap", "hold", "ease_out"]
    missing = [k for k in required_keys if k not in phases]
    if missing:
        return [("V21", f"{owner}: 'spacing_phases' missing keys {missing}")]
    prev_end: Optional[int] = None
    for k in required_keys:
        window = phases[k]
        if (
            not isinstance(window, list)
            or len(window) != 2
            or not all(isinstance(v, int) and not isinstance(v, bool) and v >= 0 for v in window)
        ):
            errors.append(("V21", f"{owner}: spacing_phases['{k}'] must be a 2-int list [start, end], got {window}"))
            continue
        if window[1] < window[0]:
            errors.append(("V21", f"{owner}: spacing_phases['{k}'] end ({window[1]}) < start ({window[0]})"))
        if prev_end is None and window[0] != 0:
            errors.append(("V21", f"{owner}: spacing_phases['slow_in'] must start at frame 0, got {window[0]}"))
        elif prev_end is not None and window[0] != prev_end:
            errors.append(
                ("V21", f"{owner}: spacing_phases['{k}'] start ({window[0]}) must equal previous phase end ({prev_end})")
            )
        prev_end = window[1]
    if isinstance(phases.get("snap"), list) and len(phases["snap"]) == 2:
        if phases["snap"][1] <= phases["snap"][0]:
            errors.append(("V21", f"{owner}: spacing_phases['snap'] must span at least 1 frame"))
    return errors


def validate_card(card: Dict[str, Any]) -> List[Tuple[str, str]]:
    """Validate a single Move Card dictionary. Returns list of (code, message) tuples."""
    errors: List[Tuple[str, str]] = []
    cid = card.get("id", "<missing_id>")

    missing = REQUIRED_CARD_FIELDS - set(card.keys())
    if missing:
        errors.append(("V01", f"Card '{cid}' missing required fields: {sorted(missing)}"))
        return errors

    if not isinstance(card["id"], str) or not card["id"].strip():
        errors.append(("V01", "Card 'id' must be a non-empty string"))

    if card["class"] not in MOVE_CLASSES:
        errors.append(("V01", f"Card '{cid}' has unknown class '{card['class']}'"))

    if not isinstance(card["aliases"], list) or not all(isinstance(a, str) for a in card["aliases"]):
        errors.append(("V01", f"Card '{cid}' aliases must be a list of strings"))

    if not isinstance(card["caption_words"], str) or not card["caption_words"].strip():
        errors.append(("V01", f"Card '{cid}' caption_words must be a non-empty string"))

    if card["limb"] not in LIMBS:
        errors.append(("V01", f"Card '{cid}' has unknown limb '{card['limb']}'"))

    if card["hinge"] not in HINGES:
        errors.append(("V01", f"Card '{cid}' has unknown hinge '{card['hinge']}'"))

    if card["path"] not in PATHS:
        errors.append(("V01", f"Card '{cid}' has unknown path '{card['path']}'"))

    if card["level"] not in LEVELS:
        errors.append(("V01", f"Card '{cid}' has unknown level '{card['level']}'"))

    if card["contact"] not in CONTACTS:
        errors.append(("V01", f"Card '{cid}' has unknown contact '{card['contact']}'"))

    # Pre-state checks
    pre = card["pre"]
    if not isinstance(pre, dict) or "support" not in pre or "coil" not in pre:
        errors.append(("V01", f"Card '{cid}' pre must contain 'support' and 'coil' lists"))
    else:
        for s in pre["support"]:
            if s not in SUPPORT_BASES:
                errors.append(("V01", f"Card '{cid}' pre.support has unknown value '{s}'"))
        for c in pre["coil"]:
            if c not in COILS:
                errors.append(("V01", f"Card '{cid}' pre.coil has unknown value '{c}'"))

    # Post-state checks
    post = card["post"]
    if not isinstance(post, dict) or "support" not in post or "coil" not in post:
        errors.append(("V01", f"Card '{cid}' post must contain 'support' and 'coil'"))
    else:
        if post["support"] not in SUPPORT_BASES:
            errors.append(("V01", f"Card '{cid}' post.support has unknown value '{post['support']}'"))
        if post["coil"] not in COILS:
            errors.append(("V01", f"Card '{cid}' post.coil has unknown value '{post['coil']}'"))
        range_delta = post.get("range_delta", "same")
        if range_delta not in RANGE_DELTAS:
            errors.append(("V01", f"Card '{cid}' post.range_delta has unknown value '{range_delta}'"))

    # Partner pre-state checks
    p_pre = card["partner_pre"]
    if not isinstance(p_pre, dict) or "support" not in p_pre or "range" not in p_pre:
        errors.append(("V01", f"Card '{cid}' partner_pre must contain 'support' and 'range' lists"))
    else:
        for s in p_pre["support"]:
            if s not in SUPPORT_BASES:
                errors.append(("V01", f"Card '{cid}' partner_pre.support has unknown value '{s}'"))
        for r in p_pre["range"]:
            if r not in RANGE_BANDS:
                errors.append(("V01", f"Card '{cid}' partner_pre.range has unknown value '{r}'"))

    for rc in card["partner_reaction_classes"]:
        if rc not in MOVE_CLASSES:
            errors.append(("V01", f"Card '{cid}' partner_reaction_classes has unknown class '{rc}'"))

    if card["force_local"] not in FORCE_LOCAL:
        errors.append(("V01", f"Card '{cid}' force_local has unknown value '{card['force_local']}'"))

    off = card["off_limbs"]
    if not isinstance(off, dict) or not {"other_arm", "lead_leg", "rear_leg"}.issubset(set(off.keys())):
        errors.append(
            ("V01", f"Card '{cid}' off_limbs must define 'other_arm', 'lead_leg', and 'rear_leg'")
        )

    for reg in card["regimes"]:
        if reg not in REGIMES:
            errors.append(("V01", f"Card '{cid}' regimes has unknown value '{reg}'"))

    for st in card["styles"]:
        if st not in STYLES:
            errors.append(("V01", f"Card '{cid}' styles has unknown value '{st}'"))

    if card["bleed_tier"] not in BLEED_TIERS:
        errors.append(("V01", f"Card '{cid}' bleed_tier '{card['bleed_tier']}' not in {BLEED_TIERS}"))

    eff = card["effort"]
    if not isinstance(eff, dict):
        errors.append(("V01", f"Card '{cid}' effort must be a dict"))
    else:
        if eff.get("weight") not in EFFORT_WEIGHT:
            errors.append(("V01", f"Card '{cid}' effort.weight invalid"))
        if eff.get("time") not in EFFORT_TIME:
            errors.append(("V01", f"Card '{cid}' effort.time invalid"))
        if eff.get("space") not in EFFORT_SPACE:
            errors.append(("V01", f"Card '{cid}' effort.space invalid"))
        if eff.get("flow") not in EFFORT_FLOW:
            errors.append(("V01", f"Card '{cid}' effort.flow invalid"))

    # V18: the card's default kinetic chain (spliced into every beat's causal
    # string as segment four) and its internal chain_frames timing offsets.
    errors.extend(
        validate_kinetic_chain(
            card.get("chain"),
            owner=f"Card '{cid}'",
            chain_frames=card.get("chain_frames"),
            require_frames=True,
        )
    )

    # V19: weight_split and com_position vs support base
    ws = card.get("weight_split")
    if (
        not isinstance(ws, list)
        or len(ws) != 2
        or not all(isinstance(v, int) and not isinstance(v, bool) and 0 <= v <= 100 for v in ws)
        or sum(ws) not in {0, 100}
    ):
        errors.append(("V19", f"Card '{cid}' weight_split must be a 2-int list [lead_pct, rear_pct] summing to 100 (or 0 for airborne)"))
    com = card.get("com_position")
    if com not in COM_POSITIONS:
        errors.append(("V19", f"Card '{cid}' has unknown com_position '{com}'"))
    elif com == "outside_support_falling":
        post_sup = card.get("post", {}).get("support")
        if post_sup not in {"supine", "prone", "kneeling", "airborne"}:
            errors.append(
                (
                    "V19",
                    f"Card '{cid}' has com_position='outside_support_falling' while post.support='{post_sup}' (CoG outside support base requires knockdown/fall or step recovery)",
                )
            )

    # V21: easing_curve and spacing_phases
    ec = card.get("easing_curve")
    if ec not in EASING_CURVES:
        errors.append(("V21", f"Card '{cid}' has unknown easing_curve '{ec}'"))
    errors.extend(validate_spacing_phases(card.get("spacing_phases"), owner=f"Card '{cid}'"))

    # V22: impulse_tier
    it = card.get("impulse_tier")
    if isinstance(it, bool) or it not in IMPULSE_TIERS:
        errors.append(("V22", f"Card '{cid}' has invalid impulse_tier '{it}' (must be in {IMPULSE_TIERS})"))

    return errors


class Lexicon:
    """Closed registry of validated Move Cards."""

    def __init__(self, cards: List[Dict[str, Any]]):
        self.cards_by_id: Dict[str, Dict[str, Any]] = {}
        self.validation_errors: List[Tuple[str, str]] = []
        for card in cards:
            errs = validate_card(card)
            self.validation_errors.extend(errs)
            cid = card.get("id")
            if isinstance(cid, str):
                if cid in self.cards_by_id:
                    self.validation_errors.append(("V01", f"Duplicate card id '{cid}'"))
                self.cards_by_id[cid] = card

    @classmethod
    def load_default(cls) -> "Lexicon":
        data_dir = Path(__file__).parent / "lexicon_data"
        all_cards: List[Dict[str, Any]] = []
        for path in sorted(data_dir.glob("*.json")):
            with open(path, "r", encoding="utf-8") as f:
                payload = json.load(f)
                all_cards.extend(payload.get("cards", []))
        return cls(all_cards)

    def get(self, move_id: str) -> Optional[Dict[str, Any]]:
        return self.cards_by_id.get(move_id)
