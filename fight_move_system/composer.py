"""§7. Clip Composer — Single-Regime Clip Isolation, State Chaining & Split Proposals."""

import copy
from typing import Any, Dict, List, Optional, Tuple

from .lexicon import Lexicon
from .validator import load_quarantine_ledger, load_thresholds, validate_clip


def compose_clips(
    sheet: Dict[str, Any],
    lexicon: Optional[Lexicon] = None,
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """Split a full fight beat-sheet into regime-isolated, state-chained clips.
    Returns (list_of_clips, split_notes).
    """
    lex = lexicon or Lexicon.load_default()
    thresh = load_thresholds()
    quarantine = load_quarantine_ledger()

    # If the input already has a "clips" list, chain states across them;
    # otherwise split "moments" at regime changes.
    if "clips" in sheet:
        raw_clips = copy.deepcopy(sheet["clips"])
    else:
        raw_clips = _split_by_regime(sheet, lex)

    chained_clips: List[Dict[str, Any]] = []
    notes: List[str] = []

    prev_res = None
    for idx, clip in enumerate(raw_clips):
        if prev_res is not None and prev_res.final_fighter_a and prev_res.final_fighter_b and prev_res.final_dyad:
            # Chain Clip N end state -> Clip N+1 initial state (§7.2)
            fa = prev_res.final_fighter_a
            fb = prev_res.final_fighter_b
            clip.setdefault("fighters", {})
            clip["fighters"].setdefault("A", {})
            clip["fighters"].setdefault("B", {})
            clip["fighters"]["A"].update(
                {
                    "support": fa.support,
                    "coil": fa.coil,
                    "stance": fa.stance,
                    "screen_side": fa.screen_side,
                    "facing": fa.facing,
                    "style": fa.style,
                }
            )
            clip["fighters"]["B"].update(
                {
                    "support": fb.support,
                    "coil": fb.coil,
                    "stance": fb.stance,
                    "screen_side": fb.screen_side,
                    "facing": fb.facing,
                    "style": fb.style,
                }
            )
            clip["initial_range"] = prev_res.final_dyad.range_band
            notes.append(
                f"Chained Clip {idx} end-state -> Clip {idx + 1} start (range='{clip['initial_range']}', A.support='{fa.support}', B.support='{fb.support}')"
            )

        res = validate_clip(clip, lexicon=lex, thresholds=thresh, quarantine_ledger=quarantine)
        if "V13" in res.warning_codes() or "V14" in res.error_codes():
            split_idx = max(1, len(clip.get("moments", [])) // 2)
            notes.append(
                f"Clip {idx + 1} triggered bleed/quarantine rule ({res.error_codes() | res.warning_codes()}); propose splitting at moment index {split_idx}."
            )
        prev_res = res
        chained_clips.append(clip)

    return chained_clips, notes


def _split_by_regime(sheet: Dict[str, Any], lex: Lexicon) -> List[Dict[str, Any]]:
    moments = sheet.get("moments", [])
    if not moments:
        return [copy.deepcopy(sheet)]

    clips: List[Dict[str, Any]] = []
    current_regime = sheet.get("regime", "standup_striking")
    current_moments: List[Dict[str, Any]] = []

    for m in moments:
        target_reg = m.get("regime", current_regime)
        if target_reg != current_regime and current_moments:
            c = copy.deepcopy(sheet)
            c["regime"] = current_regime
            c["moments"] = current_moments
            clips.append(c)
            current_regime = target_reg
            current_moments = [m]
        else:
            current_moments.append(m)

    if current_moments:
        c = copy.deepcopy(sheet)
        c["regime"] = current_regime
        c["moments"] = current_moments
        clips.append(c)

    return clips
