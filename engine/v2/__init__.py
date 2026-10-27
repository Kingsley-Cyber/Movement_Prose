"""BLOCK Simulator v2 modular engine package."""

from __future__ import annotations

from .audits import (
    audit_option_coverage_v2,
    audit_round_robin_balance_v2,
    explain_matchup_top_causes_v2,
)
from .availability import available_v2, slot_defense_pool_v2, slot_pool_v2
from .cards import (
    compute_school_depth_multiplier,
    list_archetypes_v2,
    load_card_v2,
)
from .data import (
    ARENA_PRESETS,
    DEFENSIVE_DIMS,
    FPS,
    KICK_IDS,
    LANDING_QUALITY_MULT,
    LANES,
    MOVE_BASE_STATS,
    NEUTRAL_DIMS,
    OFFENSIVE_DIMS,
    get_attack_profile,
    load_capabilities_v2,
    load_combinations_v2,
    load_debt_registry_v2,
    load_model_v2,
    load_option_behaviors,
    load_positions_v2,
    load_rulesets_v2,
    load_techniques_v2,
)
from .defense import select_kick_defense, select_native_defense
from .exchange import compute_card_derived_damage, simulate_fight_v2
from .finishes import check_finish_conditions, evaluate_decision_winner
from .geometry import get_arena_preset
from .grappling import update_grappling_position
from .kicking import unroll_kick_anatomy
from .laterality import compute_lead_foot_matchup
from .montecarlo import compile_simulated_fight_to_atomic_beats, simulate_many_v2
from .readiness import compute_readiness_profile
from .selection import build_slot_plans
from .state import compute_posture_state
from .vertical import is_technique_vertically_allowed, normalize_vertical_mode

__all__ = [
    "ARENA_PRESETS",
    "DEFENSIVE_DIMS",
    "FPS",
    "KICK_IDS",
    "LANDING_QUALITY_MULT",
    "LANES",
    "MOVE_BASE_STATS",
    "NEUTRAL_DIMS",
    "OFFENSIVE_DIMS",
    "audit_option_coverage_v2",
    "audit_round_robin_balance_v2",
    "available_v2",
    "slot_defense_pool_v2",
    "slot_pool_v2",
    "build_slot_plans",
    "check_finish_conditions",
    "compile_simulated_fight_to_atomic_beats",
    "compute_card_derived_damage",
    "compute_lead_foot_matchup",
    "compute_posture_state",
    "compute_readiness_profile",
    "compute_school_depth_multiplier",
    "evaluate_decision_winner",
    "explain_matchup_top_causes_v2",
    "get_arena_preset",
    "get_attack_profile",
    "list_archetypes_v2",
    "load_capabilities_v2",
    "load_card_v2",
    "load_combinations_v2",
    "load_debt_registry_v2",
    "load_model_v2",
    "load_option_behaviors",
    "load_positions_v2",
    "load_rulesets_v2",
    "load_techniques_v2",
    "is_technique_vertically_allowed",
    "normalize_vertical_mode",
    "select_kick_defense",
    "select_native_defense",
    "simulate_fight_v2",
    "simulate_many_v2",
    "unroll_kick_anatomy",
    "update_grappling_position",
]
