"""Own-hand structural heuristics, without hidden-information lookahead."""

from __future__ import annotations

from functools import lru_cache
from random import Random

from .engine import legal_actions
from .hand import _validate_hand
from .model import Action, ActionKind, GameState, MahjongError, Meld, MeldKind, Tile


@lru_cache(maxsize=32768)
def _best_partition(counts: tuple[int, ...]) -> int:
    """Partition one suit (nine counts) or honors (seven counts) exactly once."""
    first = next((i for i, count in enumerate(counts) if count), None)
    if first is None:
        return 0
    possibilities = [((first,), 0)]
    if counts[first] >= 2:
        possibilities.append(((first, first), 4))
    if counts[first] >= 3:
        possibilities.append(((first, first, first), 12))
    if len(counts) == 9:
        if first < 8 and counts[first + 1]:
            possibilities.append(((first, first + 1), 3))
        if first < 7 and counts[first + 2]:
            possibilities.append(((first, first + 2), 2))
        if first < 7 and counts[first + 1] and counts[first + 2]:
            possibilities.append(((first, first + 1, first + 2), 12))
    best = 0
    for group, value in possibilities:
        remaining = list(counts)
        for index in group:
            remaining[index] -= 1
        best = max(best, value + _best_partition(tuple(remaining)))
    return best


def evaluate_structure(hand: tuple[Tile, ...], melds: tuple[Meld, ...] = ()) -> int:
    """Score an equivalent 16-tile hand, using disjoint groups (SPEC AI-001)."""
    counts = _validate_hand(hand, melds, 16)
    score = sum(_best_partition(tuple(counts[start:start + 9])) for start in (0, 9, 18))
    score += _best_partition(tuple(counts[27:]))
    score += 12 * len(melds)
    if all(meld.kind is MeldKind.KONG_CONCEALED for meld in melds):
        score += 2
    return score


class BasicEfficiencyPolicy:
    def __init__(self, rng: Random) -> None:
        if not isinstance(rng, Random):
            raise MahjongError("INVALID_POLICY", "BasicEfficiencyPolicy requires random.Random")
        self.rng = rng

    def __call__(self, state: GameState, player: int) -> Action:
        options = legal_actions(state, player)
        if not options:
            raise MahjongError("INVALID_POLICY", "Player has no legal actions")
        for kind in (ActionKind.HU, ActionKind.KONG_EXPOSED, ActionKind.KONG_CONCEALED, ActionKind.KONG_ADDED):
            for action in options:
                if action.kind is kind:
                    return action
        own = state.players[player]
        claims = tuple(action for action in options if action.kind in (ActionKind.CHI, ActionKind.PENG))
        if claims:
            baseline = evaluate_structure(own.hand, own.melds)
            candidates = []
            for action in claims:
                pending = state.pending
                consumed = tuple(tile for tile in own.hand if tile.id in action.tiles)
                meld = Meld(MeldKind(action.kind.value), tuple(sorted(consumed + (pending.tile,))), pending.player, pending.tile.id)
                hand = tuple(tile for tile in own.hand if tile.id not in action.tiles)
                melds = own.melds + (meld,)
                value = max(evaluate_structure(hand[:i] + hand[i + 1:], melds) for i in range(len(hand)))
                if value > baseline:
                    candidates.append((value, action))
            if candidates:
                return min(candidates, key=lambda item: (
                    -item[0], 0 if item[1].kind is ActionKind.PENG else 1, item[1].tiles,
                ))[1]
        for action in options:
            if action.kind is ActionKind.DRAW:
                return action
        discards = tuple(action for action in options if action.kind is ActionKind.DISCARD)
        if discards:
            values = tuple(evaluate_structure(tuple(tile for tile in own.hand if tile.id != action.tiles[0]), own.melds)
                           for action in discards)
            best = max(values)
            return self.rng.choice(tuple(action for action, value in zip(discards, values) if value == best))
        return next(action for action in options if action.kind is ActionKind.PASS)
