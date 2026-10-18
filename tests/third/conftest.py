"""Deterministic physical-tile fixtures derived from SPEC.md only."""

import sys
from collections import Counter
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from tw_mahjong.engine import create_game, validate_state
from tw_mahjong.model import (
    DrawSource, GameState, Phase, PlayerState, Tile, full_deck, tile_kind,
)
from tw_mahjong.wall import Wall


@pytest.fixture
def tiles():
    def build(codes):
        counts = Counter()
        result = []
        for code in codes.split():
            kind = tile_kind(code)
            copy = counts[kind]
            assert copy < (1 if kind >= 34 else 4), "fixture exceeds physical copies"
            result.append(Tile(kind * 4 + copy if kind < 34 else kind + 102))
            counts[kind] += 1
        return tuple(sorted(result))
    return build


@pytest.fixture
def make_state():
    """Fill unspecified hands and wall while preserving every physical tile."""
    def build(*, hands=None, melds=None, flowers=None, rivers=None, turn=0,
              dealer=0, phase=Phase.DISCARD, rules_version=2, wall_ids=None,
              empty_wall=False, last_drawn=None, **context):
        hands, melds = dict(hands or {}), dict(melds or {})
        flowers, rivers = dict(flowers or {}), dict(rivers or {})
        reserved = [t.id for zone in (hands, flowers, rivers) for group in zone.values() for t in group]
        reserved += [t.id for group in melds.values() for meld in group for t in meld.tiles]
        assert len(reserved) == len(set(reserved)), "fixture duplicates a physical tile"
        if wall_ids is not None:
            assert not set(reserved).intersection(wall_ids)
            reserved += list(wall_ids)
        available = [t for t in full_deck() if t.id not in reserved]
        for player in range(4):
            if player not in hands:
                count = (17 if phase in (Phase.DISCARD, Phase.ROB_KONG) and player == turn else 16)
                count -= 3 * len(melds.get(player, ()))
                chosen = tuple(t for t in available if not t.is_flower)[:count]
                hands[player] = chosen
                available = [t for t in available if t not in chosen]
        if empty_wall:
            rivers[3] = rivers.get(3, ()) + tuple(t for t in available if not t.is_flower)
            flowers[3] = tuple(sorted(flowers.get(3, ()) + tuple(t for t in available if t.is_flower)))
            available = []
        elif wall_ids is not None:
            # Explicit wall order; place unused tiles in non-hand owning zones.
            rivers[3] = rivers.get(3, ()) + tuple(t for t in available if not t.is_flower)
            flowers[3] = tuple(sorted(flowers.get(3, ()) + tuple(t for t in available if t.is_flower)))
            available = [Tile(i) for i in wall_ids]
        if last_drawn is None and phase in (Phase.DISCARD, Phase.ROB_KONG):
            last_drawn = hands[turn][-1].id
        state = GameState(
            wall=Wall(tuple(available)),
            players=tuple(PlayerState(tuple(sorted(hands[p])), melds.get(p, ()),
                                      tuple(sorted(flowers.get(p, ())))) for p in range(4)),
            discards=tuple(rivers.get(p, ()) for p in range(4)),
            dealer=dealer, turn=turn, phase=phase, rules_version=rules_version,
            last_drawn=last_drawn,
            draw_source=DrawSource.NORMAL if last_drawn is not None and rules_version == 2 else None,
            **context,
        )
        validate_state(state)
        return state
    return build


@pytest.fixture
def initial():
    return create_game(tile_order=full_deck())


@pytest.fixture
def winning_tiles(tiles):
    # Five disjoint sequences and a single honor pair: exactly one decomposition.
    return tiles("1m 2m 3m 4m 5m 6m 1p 2p 3p 4p 5p 6p 1s 2s 3s E E")


@pytest.fixture
def won(make_state, winning_tiles):
    from tw_mahjong.engine import apply_action
    from tw_mahjong.model import Action, ActionKind
    state = make_state(hands={0: winning_tiles})
    return apply_action(state, Action(ActionKind.HU, 0)).state


@pytest.fixture
def finish(make_state):
    """Produce a validated win; a discard win leaves its tile in the river."""
    from dataclasses import replace
    from tw_mahjong.engine import apply_action
    from tw_mahjong.model import Action, ActionKind, EndReason

    def build(hand, *, winner=0, dealer=0, source=None, melds=(), flowers=(),
              draw_source=None, **kwargs):
        state = make_state(hands={winner: hand}, melds={winner: melds},
                           flowers={winner: flowers}, turn=winner, dealer=dealer, **kwargs)
        if draw_source is not None:
            state = replace(state, draw_source=draw_source)
        state = apply_action(state, Action(ActionKind.HU, winner)).state
        if source is not None:
            win = Tile(state.winning_tile)
            players = list(state.players)
            players[winner] = replace(players[winner], hand=tuple(t for t in hand if t != win))
            rivers = list(state.discards)
            rivers[source] += (win,)
            state = replace(state, players=tuple(players), discards=tuple(rivers),
                            win_source=source, end_reason=EndReason.DISCARD_WIN,
                            last_drawn=None, draw_source=None)
        validate_state(state)
        return state
    return build


@pytest.fixture
def prefix(initial):
    from tw_mahjong.engine import apply_action
    from tw_mahjong.model import Action, ActionKind, SimulationResult
    actions = (Action(ActionKind.DISCARD, 0, (0,)),) + tuple(
        Action(ActionKind.PASS, p) for p in (1, 2, 3)
    ) + (Action(ActionKind.DRAW, 1),)
    state = initial
    for action in actions:
        state = apply_action(state, action).state
    return SimulationResult(initial, state, actions)


@pytest.fixture
def added_kong_ready(make_state, tiles):
    from tw_mahjong.model import Meld, MeldKind
    meld = Meld(MeldKind.PENG, (Tile(0), Tile(1), Tile(2)), 1, 0)
    waiting = tiles("2m 3m 4m 5m 6m 1p 2p 3p 4p 5p 6p 1s 2s 3s E E")
    own = tuple(Tile(kind * 4 + 3) for kind in range(14))
    return make_state(hands={0: own, 2: waiting}, melds={0: (meld,)}, wall_ids=(130,))


@pytest.fixture
def robbed_win(added_kong_ready):
    from tw_mahjong.engine import apply_action
    from tw_mahjong.model import Action, ActionKind, SimulationResult
    actions = (Action(ActionKind.KONG_ADDED, 0, (3,)), Action(ActionKind.PASS, 1),
               Action(ActionKind.HU, 2), Action(ActionKind.PASS, 3))
    state = added_kong_ready
    for action in actions:
        state = apply_action(state, action).state
    return SimulationResult(added_kong_ready, state, actions)
