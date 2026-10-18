"""Deterministic physical-tile fixtures; no production files are changed."""
from collections import Counter
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from tw_mahjong.engine import create_game, validate_state
from tw_mahjong.model import (
    DrawSource, EndReason, GameState, Phase, PlayerState, Tile, full_deck,
)
from tw_mahjong.wall import Wall


def tiles(*kinds):
    """Allocate distinct physical copies for a sequence of ordinary kinds."""
    counts = Counter()
    result = []
    for kind in kinds:
        assert counts[kind] < 4
        result.append(Tile(4 * kind + counts[kind]))
        counts[kind] += 1
    return tuple(sorted(result))


@pytest.fixture
def initial():
    return create_game(tile_order=full_deck())


@pytest.fixture
def state_factory():
    def build(*, hands=None, melds=None, flowers=None, discards=None,
              turn=0, dealer=0, phase=Phase.DISCARD, wall_ids=None,
              rules_version=2, last_drawn="auto", **context):
        hands = dict(hands or {})
        melds = dict(melds or {})
        flowers = dict(flowers or {})
        rivers = dict(discards or {})
        reserved = [t.id for zone in (hands, flowers, rivers)
                    for group in zone.values() for t in group]
        reserved += [t.id for group in melds.values() for m in group for t in m.tiles]
        if wall_ids is not None:
            reserved += list(wall_ids)
        assert len(reserved) == len(set(reserved)), "fixture duplicates ownership"
        used = set(reserved)
        for player in range(4):
            if player not in hands:
                count = (17 if phase is Phase.DISCARD and player == turn else 16)
                count -= 3 * len(melds.get(player, ()))
                chosen = [t for t in full_deck()[:136] if t.id not in used][:count]
                hands[player] = tuple(chosen)
                used.update(t.id for t in chosen)
        remaining = tuple(t for t in full_deck() if t.id not in used)
        if wall_ids is None:
            wall = Wall(remaining)
        else:
            wall = Wall(tuple(Tile(i) for i in wall_ids))
            # Explicit walls allow exhaustion scenarios; unused tiles stay owned.
            rivers[3] = tuple(t for t in remaining if not t.is_flower) + rivers.get(3, ())
            flowers[3] = tuple(sorted(tuple(t for t in remaining if t.is_flower)
                                     + flowers.get(3, ())))
        if last_drawn == "auto":
            last_drawn = hands[turn][-1].id if phase is Phase.DISCARD else None
        source = DrawSource.NORMAL if last_drawn is not None and rules_version == 2 else None
        state = GameState(wall, tuple(PlayerState(tuple(sorted(hands[p])),
                          melds.get(p, ()), tuple(sorted(flowers.get(p, ()))))
                          for p in range(4)),
                          tuple(rivers.get(p, ()) for p in range(4)), dealer, turn, phase,
                          last_drawn=last_drawn, rules_version=rules_version,
                          draw_source=source, **context)
        validate_state(state)
        return state
    return build


@pytest.fixture
def winning_state(state_factory):
    from tw_mahjong.engine import apply_action
    from tw_mahjong.model import Action, ActionKind
    hand = tiles(0, 0, 0, 9, 9, 9, 18, 18, 18, 27, 27, 27, 31, 31, 31, 33, 33)
    state = state_factory(hands={0: hand}, last_drawn=hand[-1].id)
    return apply_action(state, Action(ActionKind.HU, 0)).state


@pytest.fixture
def exhausted():
    state = GameState(Wall(()), (PlayerState(flowers=full_deck()[136:]),)
                      + (PlayerState(),) * 3,
                      (full_deck()[:136], (), (), ()), 0, 0, Phase.ENDED,
                      end_reason=EndReason.WALL_EXHAUSTED)
    validate_state(state)
    return state
