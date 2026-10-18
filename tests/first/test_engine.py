from dataclasses import replace
from itertools import permutations
from random import Random

import pytest

from tests.first.conftest import tiles
from tw_mahjong.engine import apply_action, create_game, legal_actions, validate_state
from tw_mahjong.model import (
    Action, ActionKind, DrawSource, EndReason, EventKind, MahjongError,
    Meld, MeldKind, Phase, Tile, full_deck,
)
from tw_mahjong.wall import Wall


def respond(state, choices, order=(1, 2, 3)):
    transition = None
    for player in order:
        transition = apply_action(state, choices.get(player, Action(ActionKind.PASS, player)))
        state = transition.state
    return transition


@pytest.mark.parametrize("dealer", range(4))
@pytest.mark.parametrize("version", [1, 2])
def test_deal_round_robin_and_extra_tile(dealer, version):
    state = create_game(dealer=dealer, tile_order=full_deck(), rules_version=version)
    assert state.phase is Phase.DISCARD
    assert state.turn == state.dealer == dealer
    for offset in range(4):
        player = (dealer + offset) % 4
        expected = tuple(range(offset, 64, 4)) + ((64,) if offset == 0 else ())
        assert tuple(t.id for t in state.players[player].hand) == expected
        assert state.players[player].melds == state.players[player].flowers == ()
    assert state.last_drawn == 64
    assert state.draw_source == (DrawSource.INITIAL if version == 2 else None)
    assert state.wall.tiles == full_deck()[65:]
    validate_state(state)


def test_initial_flower_chain_replaced_from_back():
    order = (Tile(136),) + tuple(Tile(i) for i in range(136)) + tuple(Tile(i) for i in range(137, 144))
    state = create_game(tile_order=order)
    assert state.players[0].flowers == tuple(Tile(i) for i in range(136, 144))
    assert Tile(135) in state.players[0].hand
    assert all(not t.is_flower for p in state.players for t in p.hand)
    assert sum(len(p.hand) for p in state.players) == 65


def test_shuffle_is_one_caller_owned_rng_operation():
    rng = Random(42)
    expected_rng = Random(42)
    expected_order = list(full_deck())
    expected_rng.shuffle(expected_order)
    assert create_game(rng=rng) == create_game(tile_order=tuple(expected_order))
    assert rng.getstate() == expected_rng.getstate()


@pytest.mark.parametrize("kwargs,code", [
    ({}, "INVALID_WALL"),
    ({"tile_order": full_deck(), "rng": Random(0)}, "INVALID_WALL"),
    ({"tile_order": full_deck()[:-1]}, "INVALID_WALL"),
    ({"tile_order": full_deck()[:-1] + (Tile(0),)}, "INVALID_WALL"),
    ({"rng": 42}, "INVALID_WALL"),
    ({"dealer": True, "tile_order": full_deck()}, "INVALID_PLAYER"),
    ({"rules_version": True, "tile_order": full_deck()}, "INVALID_STATE"),
    ({"rules_version": 1, "round_wind": 28, "tile_order": full_deck()}, "INVALID_STATE"),
])
def test_invalid_initialization(kwargs, code):
    with pytest.raises(MahjongError) as caught:
        create_game(**kwargs)
    assert caught.value.code == code


def test_discard_pass_cycle_and_front_draw(initial):
    action = Action(ActionKind.DISCARD, 0, (0,))
    transition = apply_action(initial, action)
    response = transition.state
    assert initial.players[0].hand[0] == Tile(0)
    assert response.discards[0] == (Tile(0),)
    assert response.pending.tile == Tile(0)
    assert response.last_drawn is response.draw_source is None
    assert transition.events[0].kind is EventKind.DISCARDED
    assert legal_actions(response, 0) == ()
    first = apply_action(response, Action(ActionKind.PASS, 3)).state
    assert first.responses == (Action(ActionKind.PASS, 3),)
    assert legal_actions(first, 3) == ()
    second = apply_action(first, Action(ActionKind.PASS, 1)).state
    assert tuple(a.player for a in second.responses) == (1, 3)
    resolved = apply_action(second, Action(ActionKind.PASS, 2))
    assert resolved.state.phase is Phase.DRAW
    assert resolved.state.turn == 1
    assert resolved.state.pending is None
    assert resolved.events[-1].kind is EventKind.TURN
    draw = apply_action(resolved.state, Action(ActionKind.DRAW, 1))
    assert draw.state.last_drawn == 65
    assert draw.state.draw_source is DrawSource.NORMAL
    assert draw.state.phase is Phase.DISCARD
    assert draw.events[0].tile == 65


@pytest.mark.parametrize("action", [
    None, Action("DISCARD", 0, (0,)), Action(ActionKind.DISCARD, True, (0,)),
    Action(ActionKind.DISCARD, 1, (0,)), Action(ActionKind.DISCARD, 0, [0]),
    Action(ActionKind.DISCARD, 0, (True,)), Action(ActionKind.DISCARD, 0, (143,)),
    Action(ActionKind.DISCARD, 0, (0, 4)), Action(ActionKind.PASS, 0),
])
def test_invalid_actions_are_rejected_without_mutation(initial, action):
    before = repr(initial)
    with pytest.raises(MahjongError) as caught:
        apply_action(initial, action)
    assert caught.value.code == "INVALID_ACTION"
    assert repr(initial) == before


@pytest.mark.parametrize("change", [
    {"wall": Wall(())}, {"dealer": True}, {"phase": "DISCARD"},
    {"rules_version": 3}, {"round_wind": 31}, {"draw_source": None},
    {"last_discard_last": True}, {"winner": 0}, {"responses": []},
])
def test_invalid_state_metadata(initial, change):
    with pytest.raises(MahjongError) as caught:
        validate_state(replace(initial, **change))
    assert caught.value.code == "INVALID_STATE"


def test_state_rejects_unsorted_hand_and_duplicate_ownership(initial):
    own = initial.players[0]
    for hand in (tuple(reversed(own.hand)), own.hand[:-1] + (own.hand[0],)):
        state = replace(initial, players=(replace(own, hand=hand),) + initial.players[1:])
        with pytest.raises(MahjongError) as caught:
            validate_state(state)
        assert caught.value.code == "INVALID_STATE"


@pytest.mark.parametrize("player", [-1, 4, True, 0.0])
def test_legal_actions_invalid_player(initial, player):
    with pytest.raises(MahjongError) as caught:
        legal_actions(initial, player)
    assert caught.value.code == "INVALID_PLAYER"


def test_peng_beats_chi_independent_of_response_order(state_factory):
    # P1 can chi 1m-2m-3m; P2 can peng the discarded 1m.
    source = state_factory(hands={0: tuple(Tile(i) for i in (0, *range(60, 76))),
                                  1: tuple(Tile(i) for i in (4, 8, *range(76, 90))),
                                  2: tuple(Tile(i) for i in (1, 2, *range(90, 104)))})
    pending = apply_action(source, Action(ActionKind.DISCARD, 0, (0,))).state
    chi = Action(ActionKind.CHI, 1, (4, 8))
    peng = Action(ActionKind.PENG, 2, (1, 2))
    assert chi in legal_actions(pending, 1)
    assert peng in legal_actions(pending, 2)
    results = []
    for order in permutations((1, 2, 3)):
        first = apply_action(pending, {1: chi, 2: peng, 3: Action(ActionKind.PASS, 3)}[order[0]])
        assert first.state.players == pending.players
        final = respond(pending, {1: chi, 2: peng}, order)
        assert final.state.turn == 2
        assert final.state.discards[0] == ()
        assert final.state.players[2].melds[-1] == Meld(MeldKind.PENG, (Tile(0), Tile(1), Tile(2)), 0, 0)
        assert final.state.last_drawn is None
        assert Action(ActionKind.HU, 2) not in legal_actions(final.state, 2)
        assert final.events[-2].kind is EventKind.CLAIMED
        results.append(final.state)
    assert all(state == results[0] for state in results)


def test_concealed_kong_draws_back_through_flowers(state_factory):
    hand = tuple(Tile(i) for i in (*range(4), *range(40, 53)))
    state = state_factory(hands={0: hand}, wall_ids=(100, 101, 136, 137))
    action = Action(ActionKind.KONG_CONCEALED, 0, (0, 1, 2, 3))
    assert action in legal_actions(state, 0)
    result = apply_action(state, action)
    assert [e.kind for e in result.events] == [EventKind.KONG_COMPLETED, EventKind.FLOWER,
                                              EventKind.FLOWER, EventKind.DRAWN]
    assert [e.tile for e in result.events[1:]] == [137, 136, 101]
    assert result.state.draw_source is DrawSource.KONG
    assert result.state.last_drawn == 101
    assert result.state.players[0].melds[0].source is None
    assert result.state.wall.tiles == (Tile(100),)


def test_v1_cannot_kong(state_factory):
    state = state_factory(hands={0: tuple(Tile(i) for i in range(17))}, rules_version=1)
    assert all(a.kind is not ActionKind.KONG_CONCEALED for a in legal_actions(state, 0))


def test_added_kong_waits_for_all_passes(state_factory):
    peng = Meld(MeldKind.PENG, (Tile(0), Tile(1), Tile(2)), 1, 0)
    state = state_factory(hands={0: (Tile(3),) + tuple(Tile(i) for i in range(40, 53))},
                          melds={0: (peng,)}, wall_ids=(100, 101))
    action = Action(ActionKind.KONG_ADDED, 0, (3,))
    declared = apply_action(state, action)
    assert declared.state.phase is Phase.ROB_KONG
    assert declared.state.players == state.players
    assert declared.events[0].kind is EventKind.KONG_DECLARED
    completed = respond(declared.state, {})
    meld = completed.state.players[0].melds[0]
    assert meld.kind is MeldKind.KONG_ADDED
    assert (meld.source, meld.claimed_tile) == (1, 0)
    assert completed.state.last_drawn == 101
    assert completed.state.draw_source is DrawSource.KONG


def test_draw_exhausts_after_only_flowers(state_factory):
    state = state_factory(phase=Phase.DRAW, wall_ids=(136, 137))
    result = apply_action(state, Action(ActionKind.DRAW, 0))
    assert [e.kind for e in result.events] == [EventKind.FLOWER, EventKind.FLOWER, EventKind.EXHAUSTED]
    assert result.state.end_reason is EndReason.WALL_EXHAUSTED
    assert result.state.phase is Phase.ENDED
    assert all(legal_actions(result.state, p) == () for p in range(4))


def test_self_draw_ends_game_and_preserves_winning_tile(winning_state):
    assert winning_state.end_reason is EndReason.SELF_DRAW
    assert winning_state.winner == winning_state.win_source == 0
    assert Tile(winning_state.winning_tile) in winning_state.players[0].hand
    assert all(legal_actions(winning_state, p) == () for p in range(4))


@pytest.mark.parametrize("order", list(permutations((1, 2, 3))))
def test_multiple_discard_winners_choose_nearest_and_leave_tile_in_river(state_factory, order):
    first = tiles(*([0] * 3 + [9] * 3 + [18] * 3 + [27] * 3 + [31] * 3 + [33]))
    second = tiles(*([1] * 3 + [10] * 3 + [19] * 3 + [28] * 3 + [32] * 3)) + (Tile(133),)
    state = state_factory(hands={0: (Tile(134),) + tuple(Tile(i) for i in range(12, 28)),
                                 1: first, 2: second})
    pending = apply_action(state, Action(ActionKind.DISCARD, 0, (134,))).state
    choices = {1: Action(ActionKind.HU, 1), 2: Action(ActionKind.HU, 2)}
    assert all(choices[p] in legal_actions(pending, p) for p in choices)
    resolved = respond(pending, choices, order)
    assert resolved.state.winner == resolved.state.turn == 1
    assert resolved.state.win_source == 0
    assert resolved.state.end_reason is EndReason.DISCARD_WIN
    assert resolved.state.winning_tile == 134
    assert resolved.state.discards[0][-1] == Tile(134)
    assert Tile(134) not in resolved.state.players[1].hand
    assert resolved.events[-1].kind is EventKind.WON


def test_exposed_kong_lists_every_peng_and_draws_replacement(state_factory):
    state = state_factory(hands={0: (Tile(0),) + tuple(Tile(i) for i in range(60, 76)),
                                 1: tuple(Tile(i) for i in (1, 2, 3, *range(80, 93)))},
                          wall_ids=(100, 136, 137))
    pending = apply_action(state, Action(ActionKind.DISCARD, 0, (0,))).state
    actions = legal_actions(pending, 1)
    assert tuple(a.tiles for a in actions if a.kind is ActionKind.PENG) == ((1, 2), (1, 3), (2, 3))
    kong = Action(ActionKind.KONG_EXPOSED, 1, (1, 2, 3))
    assert actions.index(kong) < next(i for i, a in enumerate(actions) if a.kind is ActionKind.PENG)
    result = respond(pending, {1: kong})
    assert [e.kind for e in result.events] == [EventKind.RESPONSE, EventKind.KONG_COMPLETED,
                                              EventKind.FLOWER, EventKind.FLOWER, EventKind.DRAWN]
    assert result.state.players[1].melds[-1] == Meld(
        MeldKind.KONG_EXPOSED, tuple(Tile(i) for i in range(4)), 0, 0)
    assert result.state.discards[0] == ()
    assert result.state.turn == 1
    assert result.state.last_drawn == 100
    assert result.state.draw_source is DrawSource.KONG


def test_chi_enumerates_physical_choices_only_for_next_player(state_factory):
    state = state_factory(hands={0: (Tile(0),) + tuple(Tile(i) for i in range(60, 76)),
                                 1: tuple(Tile(i) for i in (4, 5, 8, 9, *range(80, 92))),
                                 2: tuple(Tile(i) for i in (6, 10, *range(92, 106)))})
    pending = apply_action(state, Action(ActionKind.DISCARD, 0, (0,))).state
    assert tuple(a.tiles for a in legal_actions(pending, 1) if a.kind is ActionKind.CHI) == (
        (4, 8), (4, 9), (5, 8), (5, 9))
    assert all(a.kind is not ActionKind.CHI for a in legal_actions(pending, 2))
    result = respond(pending, {1: Action(ActionKind.CHI, 1, (5, 9))})
    assert result.state.players[1].melds[-1].tiles == (Tile(0), Tile(5), Tile(9))
    assert result.state.phase is Phase.DISCARD
    assert result.state.turn == 1
    assert result.state.draw_source is result.state.last_drawn is None


def test_rob_kong_keeps_original_peng_and_transfers_tile_to_own_zone(state_factory):
    peng = Meld(MeldKind.PENG, (Tile(0), Tile(1), Tile(2)), 2, 0)
    waiting = tiles(1, 2, *([9] * 3 + [18] * 3 + [27] * 3 + [31] * 3 + [33] * 2))
    state = state_factory(hands={0: (Tile(3),) + tuple(Tile(i) for i in range(40, 53)),
                                 1: waiting}, melds={0: (peng,)})
    declared = apply_action(state, Action(ActionKind.KONG_ADDED, 0, (3,))).state
    assert legal_actions(declared, 1) == (Action(ActionKind.HU, 1), Action(ActionKind.PASS, 1))
    result = respond(declared, {1: Action(ActionKind.HU, 1)})
    final = result.state
    assert final.end_reason is EndReason.ROB_KONG
    assert (final.winner, final.win_source, final.winning_tile) == (1, 0, 3)
    assert final.robbed_tile == Tile(3)
    assert final.players[0].melds == (peng,)
    assert all(Tile(3) not in p.hand for p in final.players)
    assert all(Tile(3) not in river for river in final.discards)
    assert final.pending_kong is final.last_drawn is final.draw_source is None
    from tw_mahjong.scoring import score_hand, settle_hand
    scored = {item.code: item.tai for item in score_hand(final).items}
    assert scored["ROB_KONG"] == 1
    settlement = settle_hand(final)
    assert len(settlement.payments) == 1
    assert (settlement.payments[0].payer, settlement.payments[0].payee) == (0, 1)
    assert sum(settlement.deltas) == 0


def test_concealed_kong_with_empty_wall_retains_meld_and_ends(state_factory):
    state = state_factory(hands={0: tuple(Tile(i) for i in range(17))}, wall_ids=())
    result = apply_action(state, Action(ActionKind.KONG_CONCEALED, 0, (0, 1, 2, 3)))
    assert [e.kind for e in result.events] == [EventKind.KONG_COMPLETED, EventKind.EXHAUSTED]
    assert result.state.end_reason is EndReason.WALL_EXHAUSTED
    assert result.state.players[0].melds[0].kind is MeldKind.KONG_CONCEALED


def test_last_draw_discard_context_is_cleared_when_everyone_passes(state_factory):
    state = state_factory(phase=Phase.DRAW, wall_ids=(100,))
    drawn = apply_action(state, Action(ActionKind.DRAW, 0)).state
    assert drawn.last_drawn == 100
    pending = apply_action(drawn, Action(ActionKind.DISCARD, 0, (100,))).state
    assert pending.last_discard_last
    resolved = respond(pending, {})
    assert not resolved.state.last_discard_last
    ended = apply_action(resolved.state, Action(ActionKind.DRAW, 1)).state
    assert ended.end_reason is EndReason.WALL_EXHAUSTED
