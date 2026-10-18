"""Initialization, conservation, response arbitration and v1/v2 transitions."""

from dataclasses import replace
from itertools import permutations
from random import Random

import pytest

from tw_mahjong.engine import apply_action, create_game, legal_actions, validate_state
from tw_mahjong.model import (
    Action, ActionKind as A, DrawSource, EndReason, EventKind as E,
    MahjongError, Meld, MeldKind, Phase, Tile, full_deck,
)


def ids(start, stop):
    return tuple(Tile(i) for i in range(start, stop))


def respond(state, choices):
    transition = None
    for choice in choices:
        transition = apply_action(state, choice)
        state = transition.state
    return transition


@pytest.mark.parametrize("dealer", range(4))
@pytest.mark.parametrize("version", [1, 2])
def test_ordered_deal_round_robin(dealer, version):
    state = create_game(dealer=dealer, tile_order=full_deck(), rules_version=version)
    assert state.phase is Phase.DISCARD
    assert state.turn == state.dealer == dealer
    assert state.last_drawn == 64
    assert state.draw_source == (DrawSource.INITIAL if version == 2 else None)
    for offset in range(4):
        hand = state.players[(dealer + offset) % 4].hand
        expected = tuple(range(offset, 64, 4)) + ((64,) if offset == 0 else ())
        assert tuple(t.id for t in hand) == expected
    assert state.wall.tiles == full_deck()[65:]
    assert state.discards == ((),) * 4
    assert all(not own.flowers and not own.melds for own in state.players)
    assert validate_state(state) is None


def test_initial_flowers_are_replaced_from_back_without_advancing_deal_slot():
    order = (Tile(136),) + tuple(Tile(i) for i in range(136)) + tuple(Tile(i) for i in range(137, 144))
    state = create_game(tile_order=order)
    assert state.players[0].flowers == tuple(Tile(i) for i in range(136, 144))
    assert Tile(135) in state.players[0].hand
    assert Tile(0) in state.players[1].hand
    assert state.last_drawn == 63
    assert state.wall.tiles == tuple(Tile(i) for i in range(64, 135))


def test_seeded_deal_is_reproducible_and_shuffles_once():
    class SpyRandom(Random):
        calls = 0
        def shuffle(self, values):
            self.calls += 1
            super().shuffle(values)
    rng = SpyRandom(41)
    before = rng.getstate()
    state = create_game(rng=rng, dealer=2)
    assert rng.calls == 1
    assert rng.getstate() != before
    assert state == create_game(rng=Random(41), dealer=2)


@pytest.mark.parametrize("kwargs,code", [
    ({}, "INVALID_WALL"),
    ({"rng": Random(1), "tile_order": full_deck()}, "INVALID_WALL"),
    ({"rng": 1}, "INVALID_WALL"),
    ({"tile_order": full_deck()[:-1]}, "INVALID_WALL"),
    ({"tile_order": full_deck()[:-1] + (Tile(0),)}, "INVALID_WALL"),
    ({"tile_order": list(full_deck())}, "INVALID_WALL"),
    ({"dealer": True, "tile_order": full_deck()}, "INVALID_PLAYER"),
    ({"dealer": 4, "tile_order": full_deck()}, "INVALID_PLAYER"),
    ({"rules_version": True, "tile_order": full_deck()}, "INVALID_STATE"),
    ({"rules_version": 3, "tile_order": full_deck()}, "INVALID_STATE"),
    ({"round_wind": 31, "tile_order": full_deck()}, "INVALID_STATE"),
    ({"rules_version": 1, "round_wind": 28, "tile_order": full_deck()}, "INVALID_STATE"),
])
def test_create_rejects_invalid_inputs(kwargs, code):
    with pytest.raises(MahjongError) as exc:
        create_game(**kwargs)
    assert exc.value.code == code


def test_discard_pass_draw_cycle_is_immutable(initial):
    options = legal_actions(initial, 0)
    discards = tuple(a for a in options if a.kind is A.DISCARD)
    assert tuple(a.tiles for a in discards) == tuple((t.id,) for t in initial.players[0].hand)
    assert all(legal_actions(initial, p) == () for p in (1, 2, 3))
    action = discards[0]
    transition = apply_action(initial, action)
    state = transition.state
    assert initial.phase is Phase.DISCARD and initial.discards[0] == ()
    assert state.phase is Phase.RESPONSE and state.turn == 0
    assert state.pending.tile == Tile(action.tiles[0])
    assert state.discards[0] == (state.pending.tile,)
    assert state.last_drawn is state.draw_source is None
    assert transition.events[0].kind is E.DISCARDED
    assert transition.events[0].action == action
    state = apply_action(state, Action(A.PASS, 3)).state
    assert not legal_actions(state, 3)
    state = apply_action(state, Action(A.PASS, 1)).state
    assert tuple(a.player for a in state.responses) == (1, 3)
    last = apply_action(state, Action(A.PASS, 2))
    assert [e.kind for e in last.events] == [E.RESPONSE, E.TURN]
    assert last.state.phase is Phase.DRAW and last.state.turn == 1
    assert last.state.pending is None and last.state.responses == ()
    assert legal_actions(last.state, 1) == (Action(A.DRAW, 1),)
    drawn = apply_action(last.state, Action(A.DRAW, 1))
    assert drawn.state.last_drawn == initial.wall.tiles[0].id
    assert drawn.state.draw_source is DrawSource.NORMAL
    assert drawn.state.phase is Phase.DISCARD


@pytest.mark.parametrize("changes", [
    {"turn": True}, {"dealer": -1}, {"rules_version": 0}, {"round_wind": True},
    {"phase": "DISCARD"}, {"players": ()}, {"discards": []},
    {"responses": []}, {"last_drawn": 143}, {"draw_source": None},
    {"last_discard_last": True}, {"winner": 0},
])
def test_invalid_state_metadata(initial, changes):
    with pytest.raises(MahjongError) as exc:
        validate_state(replace(initial, **changes))
    assert exc.value.code == "INVALID_STATE"


def test_state_rejects_missing_duplicate_unsorted_and_flower_tiles(initial):
    own = initial.players[0]
    for hand in (own.hand[:-1], own.hand[:-1] + (own.hand[0],),
                 tuple(reversed(own.hand)), own.hand[:-1] + (Tile(136),)):
        state = replace(initial, players=(replace(own, hand=hand),) + initial.players[1:])
        with pytest.raises(MahjongError) as exc:
            validate_state(state)
        assert exc.value.code == "INVALID_STATE"


@pytest.mark.parametrize("action", [None, Action("DISCARD", 0, (0,)),
    Action(A.DISCARD, True, (0,)), Action(A.DISCARD, 4, (0,)),
    Action(A.DISCARD, 0, (True,)), Action(A.DISCARD, 0, [0]),
    Action(A.DISCARD, 0, (0, 4)), Action(A.DISCARD, 0, (143,)),
    Action(A.DRAW, 0), Action(A.PASS, 0), Action(A.DISCARD, 1, (1,))])
def test_illegal_actions(initial, action):
    with pytest.raises(MahjongError) as exc:
        apply_action(initial, action)
    assert exc.value.code == "INVALID_ACTION"


@pytest.mark.parametrize("player", [True, -1, 4, 1.0, None])
def test_legal_actions_validates_seat(initial, player):
    with pytest.raises(MahjongError) as exc:
        legal_actions(initial, player)
    assert exc.value.code == "INVALID_PLAYER"


@pytest.mark.parametrize("order", list(permutations((1, 2, 3))))
def test_peng_beats_chi_regardless_of_submission_order(make_state, order):
    state = make_state(hands={0: (Tile(0),) + ids(80, 96),
                              1: (Tile(4), Tile(8)) + ids(20, 34),
                              2: (Tile(1), Tile(2)) + ids(40, 54)})
    state = apply_action(state, Action(A.DISCARD, 0, (0,))).state
    choices = {1: Action(A.CHI, 1, (4, 8)), 2: Action(A.PENG, 2, (1, 2)), 3: Action(A.PASS, 3)}
    transition = respond(state, [choices[p] for p in order])
    final = transition.state
    assert final.turn == 2 and final.phase is Phase.DISCARD
    assert final.discards[0] == ()
    assert final.players[2].melds == (Meld(MeldKind.PENG, ids(0, 3), 0, 0),)
    assert final.last_drawn is None
    assert all(a.kind not in (A.HU, A.KONG_CONCEALED, A.KONG_ADDED) for a in legal_actions(final, 2))
    assert [e.kind for e in transition.events] == [E.RESPONSE, E.CLAIMED, E.TURN]
    assert transition.events[1].action == choices[2]


def test_all_physical_peng_choices_and_chi_only_next_player(make_state):
    state = make_state(hands={0: (Tile(0),) + ids(80, 96),
                              1: (Tile(1), Tile(2), Tile(3), Tile(4), Tile(8)) + ids(20, 31)})
    state = apply_action(state, Action(A.DISCARD, 0, (0,))).state
    options = legal_actions(state, 1)
    assert tuple(a.tiles for a in options if a.kind is A.PENG) == ((1, 2), (1, 3), (2, 3))
    assert Action(A.KONG_EXPOSED, 1, (1, 2, 3)) in options
    assert Action(A.CHI, 1, (4, 8)) in options
    assert options[-1] == Action(A.PASS, 1)
    assert all(a.kind is not A.CHI for p in (2, 3) for a in legal_actions(state, p))
    assert legal_actions(state, 0) == ()


def test_multiple_hu_resolves_by_distance_from_discarder(make_state, winning_tiles):
    first = winning_tiles[:-1]
    second = tuple(Tile(t.id + 2) for t in first)
    used = {t.id for t in first + second} | {109}
    dealer_hand = (Tile(109),) + tuple(Tile(i) for i in range(136) if i not in used)[:16]
    state = make_state(hands={0: dealer_hand, 1: first, 2: second})
    state = apply_action(state, Action(A.DISCARD, 0, (109,))).state
    transition = respond(state, [Action(A.HU, 2), Action(A.PASS, 3), Action(A.HU, 1)])
    assert transition.state.winner == 1
    assert transition.state.win_source == 0
    assert transition.state.end_reason is EndReason.DISCARD_WIN
    assert transition.state.discards[0][-1] == Tile(109)
    assert Tile(109) not in transition.state.players[1].hand
    assert transition.events[-1].kind is E.WON
    assert all(legal_actions(transition.state, p) == () for p in range(4))


def test_self_draw_and_finished_game_rejects_further_action(won):
    assert won.end_reason is EndReason.SELF_DRAW
    assert won.winner == won.win_source == won.turn == 0
    assert won.winning_tile == won.last_drawn
    with pytest.raises(MahjongError) as exc:
        apply_action(won, Action(A.HU, 0))
    assert exc.value.code == "INVALID_ACTION"


def test_draw_flower_chain_uses_back_and_preserves_event_order(make_state):
    state = make_state(phase=Phase.DRAW, wall_ids=(136, 100, 137))
    action = Action(A.DRAW, 0)
    transition = apply_action(state, action)
    assert [(e.kind, e.tile) for e in transition.events] == [(E.FLOWER, 136), (E.FLOWER, 137), (E.DRAWN, 100)]
    assert all(e.action == action for e in transition.events)
    assert transition.state.players[0].flowers == (Tile(136), Tile(137))
    assert transition.state.draw_source is DrawSource.FLOWER
    assert transition.state.last_drawn == 100
    assert not transition.state.wall.tiles


@pytest.mark.parametrize("wall_ids", [(), (136,), (136, 137)])
def test_draw_exhaustion_including_failed_flower_replacement(make_state, wall_ids):
    state = make_state(phase=Phase.DRAW, wall_ids=wall_ids)
    transition = apply_action(state, Action(A.DRAW, 0))
    assert transition.state.phase is Phase.ENDED
    assert transition.state.end_reason is EndReason.WALL_EXHAUSTED
    assert transition.state.winner is transition.state.last_drawn is transition.state.draw_source is None
    assert transition.events[-1].kind is E.EXHAUSTED
    assert len(transition.state.players[0].flowers) == len(wall_ids)


def test_last_ordinary_draw_sets_last_discard_context(make_state):
    state = make_state(phase=Phase.DRAW, wall_ids=(100,))
    state = apply_action(state, Action(A.DRAW, 0)).state
    state = apply_action(state, Action(A.DISCARD, 0, (100,))).state
    assert state.last_discard_last
    state = respond(state, [Action(A.PASS, p) for p in (1, 2, 3)]).state
    assert not state.last_discard_last
    assert apply_action(state, Action(A.DRAW, 1)).state.end_reason is EndReason.WALL_EXHAUSTED


def test_concealed_kong_replacement_and_flower_chain(make_state):
    state = make_state(hands={0: ids(0, 17)}, wall_ids=(100, 136, 137))
    transition = apply_action(state, Action(A.KONG_CONCEALED, 0, (0, 1, 2, 3)))
    final = transition.state
    assert [e.kind for e in transition.events] == [E.KONG_COMPLETED, E.FLOWER, E.FLOWER, E.DRAWN]
    assert final.players[0].melds == (Meld(MeldKind.KONG_CONCEALED, ids(0, 4), None, None),)
    assert len(final.players[0].hand) == 14
    assert final.last_drawn == 100 and final.draw_source is DrawSource.KONG
    assert final.phase is Phase.DISCARD


def test_exposed_kong_transfers_discard_and_draws_from_back(make_state):
    state = make_state(hands={0: (Tile(0),) + ids(80, 96),
                              1: ids(1, 4) + ids(20, 33)}, wall_ids=(100, 101))
    state = apply_action(state, Action(A.DISCARD, 0, (0,))).state
    transition = respond(state, [Action(A.KONG_EXPOSED, 1, (1, 2, 3)), Action(A.PASS, 2), Action(A.PASS, 3)])
    final = transition.state
    assert final.discards[0] == ()
    assert final.players[1].melds[0] == Meld(MeldKind.KONG_EXPOSED, ids(0, 4), 0, 0)
    assert final.last_drawn == 101 and final.wall.tiles == (Tile(100),)
    assert final.draw_source is DrawSource.KONG


@pytest.mark.parametrize("rob", [False, True])
def test_added_kong_waits_for_responses_and_can_be_robbed(make_state, tiles, rob):
    meld = Meld(MeldKind.PENG, ids(0, 3), 1, 0)
    waiting = tiles("2m 3m 4m 5m 6m 1p 2p 3p 4p 5p 6p 1s 2s 3s E E")
    used = {t.id for t in waiting} | {0, 1, 2, 3, 130}
    own = (Tile(3),) + tuple(Tile(i) for i in range(136) if i not in used)[:13]
    state = make_state(hands={0: own, 2: waiting}, melds={0: (meld,)}, wall_ids=(130,))
    declared = apply_action(state, Action(A.KONG_ADDED, 0, (3,)))
    state = declared.state
    assert state.phase is Phase.ROB_KONG
    assert state.players[0].melds == (meld,) and Tile(3) in state.players[0].hand
    assert declared.events[0].kind is E.KONG_DECLARED
    assert all(a.kind in (A.HU, A.PASS) for p in (1, 2, 3) for a in legal_actions(state, p))
    transition = respond(state, [Action(A.PASS, 1), Action(A.HU if rob else A.PASS, 2), Action(A.PASS, 3)])
    final = transition.state
    if rob:
        assert final.end_reason is EndReason.ROB_KONG
        assert final.winner == 2 and final.win_source == 0
        assert final.robbed_tile == Tile(3) and final.winning_tile == 3
        assert final.players[0].melds == (meld,)
        assert Tile(3) not in final.players[0].hand
        assert final.pending_kong is final.last_drawn is final.draw_source is None
    else:
        assert final.phase is Phase.DISCARD
        assert final.players[0].melds == (Meld(MeldKind.KONG_ADDED, ids(0, 4), 1, 0),)
        assert final.last_drawn == 130 and final.draw_source is DrawSource.KONG


def test_kong_exhaustion_retains_completed_meld(make_state):
    state = make_state(hands={0: ids(0, 17)}, empty_wall=True)
    transition = apply_action(state, Action(A.KONG_CONCEALED, 0, (0, 1, 2, 3)))
    assert transition.state.end_reason is EndReason.WALL_EXHAUSTED
    assert len(transition.state.players[0].melds) == 1
    assert [e.kind for e in transition.events] == [E.KONG_COMPLETED, E.EXHAUSTED]


def test_v1_does_not_offer_kongs(make_state):
    state = make_state(hands={0: ids(0, 17)}, rules_version=1)
    assert all(a.kind not in (A.KONG_ADDED, A.KONG_CONCEALED, A.KONG_EXPOSED) for a in legal_actions(state, 0))
    with pytest.raises(MahjongError) as exc:
        apply_action(state, Action(A.KONG_CONCEALED, 0, (0, 1, 2, 3)))
    assert exc.value.code == "INVALID_ACTION"


def test_chi_moves_external_tile_and_requires_discard(make_state):
    state = make_state(hands={0: (Tile(0),) + ids(80, 96),
                              1: (Tile(4), Tile(8)) + ids(20, 34)})
    state = apply_action(state, Action(A.DISCARD, 0, (0,))).state
    transition = respond(state, [Action(A.PASS, 3), Action(A.CHI, 1, (4, 8)), Action(A.PASS, 2)])
    final = transition.state
    assert final.players[1].melds == (Meld(MeldKind.CHI, (Tile(0), Tile(4), Tile(8)), 0, 0),)
    assert final.turn == 1 and final.phase is Phase.DISCARD
    assert len(final.players[1].hand) == 14 and final.discards[0] == ()
    assert final.last_drawn is final.draw_source is None
    assert all(a.kind is A.DISCARD for a in legal_actions(final, 1))


def test_hu_beats_peng(make_state, winning_tiles):
    waiting = winning_tiles[:-1]
    used = {t.id for t in waiting} | {109, 110, 111}
    other = (Tile(110), Tile(111)) + tuple(Tile(i) for i in range(136) if i not in used)[:14]
    used.update(t.id for t in other)
    dealer = (Tile(109),) + tuple(Tile(i) for i in range(136) if i not in used)[:16]
    state = make_state(hands={0: dealer, 1: waiting, 2: other})
    state = apply_action(state, Action(A.DISCARD, 0, (109,))).state
    final = respond(state, [Action(A.PENG, 2, (110, 111)), Action(A.HU, 1), Action(A.PASS, 3)]).state
    assert final.winner == 1 and final.end_reason is EndReason.DISCARD_WIN
    assert not final.players[2].melds


def test_nearest_hu_uses_cyclic_distance_rather_than_smallest_seat(make_state, winning_tiles):
    first = winning_tiles[:-1]
    second = tuple(Tile(t.id + 2) for t in first)
    used = {t.id for t in first + second} | {109}
    dealer = (Tile(109),) + tuple(Tile(i) for i in range(136) if i not in used)[:16]
    state = make_state(hands={0: first, 3: second, 2: dealer}, turn=2, dealer=2)
    state = apply_action(state, Action(A.DISCARD, 2, (109,))).state
    final = respond(state, [Action(A.HU, 0), Action(A.PASS, 1), Action(A.HU, 3)]).state
    assert final.winner == 3 and final.win_source == 2


def test_repeated_response_is_illegal(prefix):
    state = apply_action(prefix.initial_state, prefix.actions[0]).state
    state = apply_action(state, Action(A.PASS, 1)).state
    with pytest.raises(MahjongError) as exc:
        apply_action(state, Action(A.PASS, 1))
    assert exc.value.code == "INVALID_ACTION"


def test_v1_rejects_v2_draw_context(initial):
    with pytest.raises(MahjongError) as exc:
        validate_state(replace(initial, rules_version=1))
    assert exc.value.code == "INVALID_STATE"
