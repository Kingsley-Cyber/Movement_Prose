"""Stance relation and laterality helpers for BLOCK Simulator v2."""

from __future__ import annotations


def compute_lead_foot_matchup(orientation_a: str, orientation_b: str) -> str:
    return "closed_stance" if orientation_a == orientation_b else "open_stance"
