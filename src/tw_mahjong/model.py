"""Immutable public values and physical tile identities (SPEC TILE/MELD/API)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .wall import Wall


class MahjongError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(message)


def is_int(value: object) -> bool:
    return type(value) is int


def check_player(player: object) -> None:
    if not is_int(player) or not 0 <= player < 4:
        raise MahjongError("INVALID_PLAYER", "Player must be an integer from 0 to 3")


_CODES = tuple(f"{rank}{suit}" for suit in "mps" for rank in range(1, 10)) + (
    "E", "S", "W", "N", "R", "G", "B",
) + tuple(f"F{i}" for i in range(1, 9))


def tile_kind(code: str) -> int:
    if not isinstance(code, str) or code not in _CODES:
        raise MahjongError("INVALID_TILE", "Unknown tile code")
    return _CODES.index(code)


@dataclass(frozen=True, order=True)
class Tile:
    id: int

    def __post_init__(self) -> None:
        if not is_int(self.id) or not 0 <= self.id < 144:
            raise MahjongError("INVALID_TILE", "Tile id must be an integer from 0 to 143")

    @property
    def kind(self) -> int:
        return self.id // 4 if self.id < 136 else self.id - 102

    @property
    def code(self) -> str:
        return _CODES[self.kind]

    @property
    def is_flower(self) -> bool:
        return self.id >= 136


def full_deck() -> tuple[Tile, ...]:
    return tuple(Tile(i) for i in range(144))


class MeldKind(Enum):
    CHI = "CHI"
    PENG = "PENG"


def is_sequence(kinds: tuple[int, ...]) -> bool:
    return (
        len(kinds) == 3
        and 0 <= kinds[0] < 27
        and kinds[0] // 9 == kinds[2] // 9
        and kinds == (kinds[0], kinds[0] + 1, kinds[0] + 2)
    )


@dataclass(frozen=True)
class Meld:
    kind: MeldKind
    tiles: tuple[Tile, ...]
    source: int
    claimed_tile: int

    def __post_init__(self) -> None:
        valid_tiles = (
            isinstance(self.tiles, tuple)
            and len(self.tiles) == 3
            and all(isinstance(t, Tile) and not t.is_flower for t in self.tiles)
        )
        if not valid_tiles:
            raise MahjongError("INVALID_MELD", "A meld needs three ordinary physical tiles")
        ids = tuple(t.id for t in self.tiles)
        if ids != tuple(sorted(set(ids))):
            raise MahjongError("INVALID_MELD", "Meld tile ids must be unique and sorted")
        if not is_int(self.source) or not 0 <= self.source < 4:
            raise MahjongError("INVALID_MELD", "Invalid meld source")
        if not is_int(self.claimed_tile) or self.claimed_tile not in ids:
            raise MahjongError("INVALID_MELD", "Claimed tile must belong to meld")
        kinds = tuple(t.kind for t in self.tiles)
        if self.kind is MeldKind.CHI and is_sequence(kinds):
            return
        if self.kind is MeldKind.PENG and len(set(kinds)) == 1:
            return
        raise MahjongError("INVALID_MELD", "Meld must be a sequence or triplet")


class Phase(Enum):
    DRAW = "DRAW"
    DISCARD = "DISCARD"
    RESPONSE = "RESPONSE"
    ENDED = "ENDED"


class ActionKind(Enum):
    DRAW = "DRAW"
    DISCARD = "DISCARD"
    CHI = "CHI"
    PENG = "PENG"
    HU = "HU"
    PASS = "PASS"


class EndReason(Enum):
    SELF_DRAW = "SELF_DRAW"
    DISCARD_WIN = "DISCARD_WIN"
    WALL_EXHAUSTED = "WALL_EXHAUSTED"


@dataclass(frozen=True)
class Action:
    kind: ActionKind
    player: int
    tiles: tuple[int, ...] = ()


@dataclass(frozen=True)
class PlayerState:
    hand: tuple[Tile, ...] = ()
    melds: tuple[Meld, ...] = ()
    flowers: tuple[Tile, ...] = ()


@dataclass(frozen=True)
class PendingDiscard:
    player: int
    tile: Tile


@dataclass(frozen=True)
class GameState:
    wall: Wall
    players: tuple[PlayerState, ...]
    discards: tuple[tuple[Tile, ...], ...]
    dealer: int
    turn: int
    phase: Phase
    pending: Optional[PendingDiscard] = None
    responses: tuple[Action, ...] = ()
    last_drawn: Optional[int] = None
    winner: Optional[int] = None
    win_source: Optional[int] = None
    winning_tile: Optional[int] = None
    end_reason: Optional[EndReason] = None


class EventKind(Enum):
    DRAWN = "DRAWN"
    FLOWER = "FLOWER"
    DISCARDED = "DISCARDED"
    RESPONSE = "RESPONSE"
    CLAIMED = "CLAIMED"
    TURN = "TURN"
    WON = "WON"
    EXHAUSTED = "EXHAUSTED"


@dataclass(frozen=True)
class Event:
    kind: EventKind
    player: Optional[int] = None
    tile: Optional[int] = None
    action: Optional[Action] = None


@dataclass(frozen=True)
class Transition:
    state: GameState
    events: tuple[Event, ...]


@dataclass(frozen=True, order=True)
class Decomposition:
    pair: int
    groups: tuple[tuple[int, int, int], ...]


@dataclass(frozen=True)
class HandAnalysis:
    winning: bool
    decompositions: tuple[Decomposition, ...]


@dataclass(frozen=True)
class SimulationResult:
    initial_state: GameState
    final_state: GameState
    actions: tuple[Action, ...]


@dataclass(frozen=True)
class ReplayFrame:
    index: int
    state: GameState
    action: Optional[Action]
    events: tuple[Event, ...]
