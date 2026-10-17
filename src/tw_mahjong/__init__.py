"""Taiwanese 16-tile mahjong, simplified deterministic rules, Python 3.10."""

from .model import (
    Action, ActionKind, Decomposition, DrawSource, EndReason, Event, EventKind, GameState,
    HandAnalysis, MahjongError, Meld, MeldKind, PendingDiscard, Phase,
    Payment, PendingKong, PlayerState, ReplayFrame, ScoreItem, ScoreResult, Settlement,
    SettlementConfig, SimulationResult, Tile, Transition, full_deck, tile_kind,
)
from .wall import Wall
from .hand import analyze_hand, find_waits
from .engine import apply_action, create_game, legal_actions, validate_state
from .simulation import Policy, SimplePolicy, iter_replay, replay, simulate
from .records import record_from_json, record_to_json
from .scoring import score_hand, settle_hand
from .policies import BasicEfficiencyPolicy, evaluate_structure

__all__ = [
    "Action", "ActionKind", "Decomposition", "EndReason", "Event", "EventKind",
    "GameState", "HandAnalysis", "MahjongError", "Meld", "MeldKind",
    "PendingDiscard", "Phase", "PlayerState", "SimulationResult", "Tile",
    "Transition", "Wall", "full_deck", "tile_kind", "analyze_hand",
    "apply_action", "create_game", "legal_actions", "validate_state",
    "Policy", "SimplePolicy", "replay", "simulate", "record_from_json", "record_to_json",
    "ReplayFrame", "iter_replay",
    "DrawSource", "PendingKong", "ScoreItem", "ScoreResult", "Payment", "Settlement", "SettlementConfig",
    "find_waits", "score_hand", "settle_hand",
    "BasicEfficiencyPolicy", "evaluate_structure",
]
