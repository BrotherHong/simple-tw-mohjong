"""Local fixtures derived only from SPEC.md and the current src/tw_mahjong API."""

import sys
from collections import Counter
from pathlib import Path
from random import Random

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from tw_mahjong import (  # noqa: E402
    DrawSource, EndReason, GameState, Phase, PlayerState, Tile, Wall,
    create_game, validate_state,
)


@pytest.fixture
def make_tiles():
    """Allocate different physical copies for a sequence of ordinary kinds."""
    def allocate(kinds):
        used = Counter()
        result = []
        for kind in kinds:
            assert 0 <= kind < 34 and used[kind] < 4
            result.append(Tile(4 * kind + used[kind]))
            used[kind] += 1
        return tuple(sorted(result))
    return allocate


@pytest.fixture
def state_factory():
    """Build conserved snapshots, filling unspecified hands with unused tiles.

    Explicit wall endpoints are reserved before filling hands. All unassigned
    flowers go to P3; exhaustion moves remaining ordinary tiles to P0's river.
    Test expectations are supplied by each test, rather than computed here.
    """
    def build(*, hands=None, melds=None, flowers=None, discards=None,
              phase=Phase.DISCARD, turn=0, dealer=0, rules_version=2,
              front=(), back=(), exhausted=False, **context):
        hands = {} if hands is None else dict(hands)
        melds = {} if melds is None else dict(melds)
        flowers = {} if flowers is None else dict(flowers)
        rivers = list(discards or ((), (), (), ()))
        reserved = [t.id for zone in hands.values() for t in zone]
        reserved += [t.id for zone in melds.values() for m in zone for t in m.tiles]
        reserved += [t.id for zone in flowers.values() for t in zone]
        reserved += [t.id for zone in rivers for t in zone]
        reserved += list(front) + list(back)
        assert len(reserved) == len(set(reserved)), "Fixture has duplicate ownership"
        used = set(reserved)
        for player in range(4):
            if player not in hands:
                extra = phase in (Phase.DISCARD, Phase.ROB_KONG) and player == turn
                target = 16 + int(extra) - 3 * len(melds.get(player, ()))
                available = [i for i in range(136) if i not in used][:target]
                hands[player] = tuple(Tile(i) for i in available)
                used.update(available)
        remaining_flowers = tuple(Tile(i) for i in range(136, 144) if i not in used)
        flowers[3] = tuple(sorted(flowers.get(3, ()) + remaining_flowers))
        used.update(t.id for t in remaining_flowers)
        middle = tuple(Tile(i) for i in range(144) if i not in used)
        wall = tuple(Tile(i) for i in front) + middle + tuple(Tile(i) for i in back)
        if exhausted:
            assert not any(t.is_flower for t in wall)
            rivers[0] = wall + rivers[0]
            wall = ()
        players = tuple(PlayerState(tuple(sorted(hands[p])), melds.get(p, ()),
                                    tuple(sorted(flowers.get(p, ())))) for p in range(4))
        if phase is Phase.DISCARD and "last_drawn" not in context:
            context["last_drawn"] = players[turn].hand[-1].id
        if context.get("last_drawn") is not None and rules_version == 2:
            context.setdefault("draw_source", DrawSource.NORMAL)
        state = GameState(Wall(wall), players, tuple(rivers), dealer, turn, phase,
                          rules_version=rules_version, **context)
        validate_state(state)
        return state
    return build


@pytest.fixture
def initial_state():
    return create_game(rng=Random(17))


@pytest.fixture
def exhausted_state(state_factory):
    return state_factory(phase=Phase.ENDED, exhausted=True,
                         end_reason=EndReason.WALL_EXHAUSTED)


@pytest.fixture
def winning_state(state_factory, make_tiles):
    # Five distinct triplets and an honor pair; a unique decomposition.
    hand = make_tiles([0] * 3 + [9] * 3 + [18] * 3 + [27] * 3 + [31] * 3 + [33] * 2)
    return state_factory(hands={0: hand}, phase=Phase.ENDED,
                         winner=0, win_source=0, winning_tile=hand[-1].id,
                         last_drawn=hand[-1].id, end_reason=EndReason.SELF_DRAW)


@pytest.fixture(scope="session")
def completed_results():
    from tw_mahjong import SimplePolicy, simulate
    return {version: simulate(create_game(rng=Random(17), rules_version=version),
                              tuple(SimplePolicy(Random(80+p)) for p in range(4)))
            for version in (1, 2)}


@pytest.fixture
def prefix_result(initial_state):
    from tw_mahjong import Action, ActionKind, SimulationResult, apply_action
    state = initial_state
    actions = [Action(ActionKind.DISCARD, state.turn, (state.players[state.turn].hand[0].id,))]
    state = apply_action(state, actions[-1]).state
    for player in range(4):
        if player != initial_state.turn:
            action = Action(ActionKind.PASS, player)
            actions.append(action)
            state = apply_action(state, action).state
    action = Action(ActionKind.DRAW, state.turn)
    actions.append(action)
    state = apply_action(state, action).state
    return SimulationResult(initial_state, state, tuple(actions))
