"""Taiwanese 16-tile mahjong, simplified deterministic rules, Python 3.10."""

from .model import (
    Action, ActionKind, Decomposition, EndReason, Event, EventKind, GameState,
    HandAnalysis, MahjongError, Meld, MeldKind, PendingDiscard, Phase,
    PlayerState, ReplayFrame, SimulationResult, Tile, Transition, full_deck, tile_kind,
)
from .wall import Wall
from .hand import analyze_hand
from .engine import apply_action, create_game, legal_actions, validate_state
from .simulation import Policy, SimplePolicy, iter_replay, replay, simulate
from .records import record_from_json, record_to_json

__all__ = [
    "Action", "ActionKind", "Decomposition", "EndReason", "Event", "EventKind",
    "GameState", "HandAnalysis", "MahjongError", "Meld", "MeldKind",
    "PendingDiscard", "Phase", "PlayerState", "SimulationResult", "Tile",
    "Transition", "Wall", "full_deck", "tile_kind", "analyze_hand",
    "apply_action", "create_game", "legal_actions", "validate_state",
    "Policy", "SimplePolicy", "replay", "simulate", "record_from_json", "record_to_json",
    "ReplayFrame", "iter_replay",
]
