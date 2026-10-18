"""Initialization, state validation and deterministic v1/v2 transitions."""

from dataclasses import replace
from itertools import permutations
from random import Random

import pytest

from tw_mahjong.engine import apply_action, create_game, legal_actions, validate_state
from tw_mahjong.model import (
    Action, ActionKind, DrawSource, EndReason, EventKind, MahjongError,
    Meld, MeldKind, PendingDiscard, Phase, Tile, full_deck,
)
from tw_mahjong.wall import Wall


def respond(state, choices):
    transition = None
    for action in choices:
        transition = apply_action(state, action)
        state = transition.state
    return transition


@pytest.mark.parametrize("dealer", range(4))
@pytest.mark.parametrize("version", [1, 2])
def test_round_robin_deal_exact_order(dealer, version):
    state = create_game(dealer=dealer, tile_order=full_deck(), rules_version=version)
    assert state.phase is Phase.DISCARD and state.turn == dealer
    for offset in range(4):
        seat = (dealer+offset) % 4
        expected = tuple(Tile(i) for i in range(offset, 64, 4))
        if seat == dealer:
            expected += (Tile(64),)
        assert state.players[seat].hand == expected
        assert state.players[seat].melds == state.players[seat].flowers == ()
    assert state.wall.tiles == full_deck()[65:]
    assert state.last_drawn == 64
    assert state.draw_source is (DrawSource.INITIAL if version == 2 else None)
    assert state.discards == ((), (), (), ()) and state.responses == ()
    assert validate_state(state) is None


def test_initial_flowers_are_replaced_from_back_until_ordinary():
    order = (Tile(136),) + tuple(Tile(i) for i in range(136)) + tuple(Tile(i) for i in range(137,144))
    state = create_game(tile_order=order)
    assert state.players[0].flowers == tuple(Tile(i) for i in range(136,144))
    assert Tile(135) in state.players[0].hand
    assert state.players[1].hand[0] == Tile(0)
    assert state.last_drawn == 63
    # Only the final dealer draw determines current draw context.
    assert state.draw_source is DrawSource.INITIAL


def test_shuffle_is_once_and_uses_only_injected_random():
    class CountingRandom(Random):
        def __init__(self, seed):
            super().__init__(seed)
            self.calls = 0
        def shuffle(self, values):
            self.calls += 1
            super().shuffle(values)
    rng = CountingRandom(42)
    before = rng.getstate()
    state = create_game(rng=rng)
    assert rng.calls == 1 and rng.getstate() != before
    assert state == create_game(rng=Random(42))


@pytest.mark.parametrize("kwargs,code", [
    ({}, "INVALID_WALL"),
    ({"rng": Random(0), "tile_order": full_deck()}, "INVALID_WALL"),
    ({"rng": 0}, "INVALID_WALL"),
    ({"tile_order": full_deck()[:-1]}, "INVALID_WALL"),
    ({"tile_order": full_deck()[:-1]+(Tile(0),)}, "INVALID_WALL"),
    ({"tile_order": list(full_deck())}, "INVALID_WALL"),
    ({"tile_order": full_deck(), "dealer": True}, "INVALID_PLAYER"),
    ({"tile_order": full_deck(), "dealer": 4}, "INVALID_PLAYER"),
    ({"tile_order": full_deck(), "rules_version": True}, "INVALID_STATE"),
    ({"tile_order": full_deck(), "rules_version": 3}, "INVALID_STATE"),
    ({"tile_order": full_deck(), "round_wind": 26}, "INVALID_STATE"),
    ({"tile_order": full_deck(), "round_wind": 31}, "INVALID_STATE"),
    ({"tile_order": full_deck(), "rules_version": 1, "round_wind": 28}, "INVALID_STATE"),
])
def test_invalid_initialization(kwargs, code):
    with pytest.raises(MahjongError) as error:
        create_game(**kwargs)
    assert error.value.code == code


def test_discard_pass_draw_cycle_is_immutable(initial_state):
    state = initial_state
    tile = state.players[state.turn].hand[0]
    action = Action(ActionKind.DISCARD, state.turn, (tile.id,))
    transition = apply_action(state, action)
    after = transition.state
    assert tile in state.players[state.turn].hand
    assert tile not in after.players[state.turn].hand
    assert after.pending == PendingDiscard(state.turn, tile)
    assert after.discards[state.turn][-1] == tile
    assert after.last_drawn is after.draw_source is None
    assert [(e.kind, e.player, e.tile, e.action) for e in transition.events] == [
        (EventKind.DISCARDED, state.turn, tile.id, action)]
    assert legal_actions(after, state.turn) == ()
    players = tuple(p for p in range(4) if p != state.turn)
    first = apply_action(after, Action(ActionKind.PASS, players[-1])).state
    assert first.phase is Phase.RESPONSE
    assert legal_actions(first, players[-1]) == ()
    final = respond(first, [Action(ActionKind.PASS, p) for p in players[:-1]])
    assert final.state.phase is Phase.DRAW
    assert final.state.turn == (state.turn+1) % 4
    assert final.state.pending is None and final.state.responses == ()
    assert final.events[-1].kind is EventKind.TURN
    assert legal_actions(final.state, final.state.turn) == (Action(ActionKind.DRAW, final.state.turn),)


@pytest.mark.parametrize("version", [1,2])
def test_draw_chain_of_flowers_and_event_order(state_factory, version):
    state = state_factory(phase=Phase.DRAW, rules_version=version,
                          front=(136,), back=(135,138,137))
    action = Action(ActionKind.DRAW, 0)
    transition = apply_action(state, action)
    assert [e.kind for e in transition.events] == [EventKind.FLOWER]*3+[EventKind.DRAWN]
    assert [e.tile for e in transition.events] == [136,137,138,135]
    assert all(e.action == action for e in transition.events)
    assert transition.state.last_drawn == 135
    assert transition.state.draw_source is (DrawSource.FLOWER if version == 2 else None)
    assert transition.state.players[0].flowers == tuple(Tile(i) for i in (136,137,138))
    assert transition.state.phase is Phase.DISCARD
    assert state.players[0].flowers == ()


def test_draw_empty_wall_ends_without_winner(state_factory):
    state = state_factory(phase=Phase.DRAW, exhausted=True)
    transition = apply_action(state, Action(ActionKind.DRAW, 0))
    assert transition.state.end_reason is EndReason.WALL_EXHAUSTED
    assert transition.state.phase is Phase.ENDED
    assert transition.state.winner is transition.state.win_source is transition.state.winning_tile is None
    assert [e.kind for e in transition.events] == [EventKind.EXHAUSTED]
    assert all(legal_actions(transition.state, p) == () for p in range(4))


@pytest.mark.parametrize("mutation", [
    {"turn": True}, {"dealer": 4}, {"players": ()}, {"discards": []},
    {"phase": "DISCARD"}, {"winner": 1}, {"last_drawn": 143},
    {"draw_source": None}, {"last_discard_last": 1}, {"round_wind": True},
    {"responses": []}, {"wall": Wall(())},
])
def test_invalid_state_context_and_tile_conservation(initial_state, mutation):
    with pytest.raises(MahjongError) as error:
        validate_state(replace(initial_state, **mutation))
    assert error.value.code == "INVALID_STATE"


def test_unsorted_or_duplicated_hand_is_invalid(initial_state):
    own = initial_state.players[0]
    for hand in (tuple(reversed(own.hand)), own.hand[:-1]+(own.hand[0],)):
        players = (replace(own, hand=hand),) + initial_state.players[1:]
        with pytest.raises(MahjongError) as error:
            legal_actions(replace(initial_state, players=players), 0)
        assert error.value.code == "INVALID_STATE"


@pytest.mark.parametrize("action", [
    None, "DRAW", Action("DISCARD",0,(0,)), Action(ActionKind.PASS,0),
    Action(ActionKind.DISCARD,True,(0,)), Action(ActionKind.DISCARD,4,(0,)),
    Action(ActionKind.DISCARD,0,[0]), Action(ActionKind.DISCARD,0,(True,)),
    Action(ActionKind.DISCARD,0,(144,)), Action(ActionKind.DISCARD,0,()),
    Action(ActionKind.CHI,1,(2,1)), Action(ActionKind.PENG,1,(1,1)),
])
def test_invalid_actions_are_rejected_without_mutation(initial_state, action):
    before = initial_state
    with pytest.raises(MahjongError) as error:
        apply_action(initial_state, action)
    assert error.value.code == "INVALID_ACTION"
    assert initial_state == before


@pytest.mark.parametrize("player", [True, -1, 4, 0.0])
def test_legal_actions_checks_player(initial_state, player):
    with pytest.raises(MahjongError) as error:
        legal_actions(initial_state, player)
    assert error.value.code == "INVALID_PLAYER"


def test_chi_is_only_for_next_player_and_lists_physical_choices(state_factory):
    hand = tuple(Tile(i) for i in (4,5,8,9)+tuple(range(40,52)))
    state = state_factory(hands={1:hand})
    state = apply_action(state, Action(ActionKind.DISCARD,0,(0,))).state
    chi = tuple(a.tiles for a in legal_actions(state,1) if a.kind is ActionKind.CHI)
    assert chi == ((4,8),(4,9),(5,8),(5,9))
    assert not any(a.kind is ActionKind.CHI for p in (2,3) for a in legal_actions(state,p))
    claimed = respond(state, [Action(ActionKind.CHI,1,(4,8)),
                              Action(ActionKind.PASS,3), Action(ActionKind.PASS,2)])
    after = claimed.state
    assert after.turn == 1 and after.phase is Phase.DISCARD
    assert after.players[1].melds == (Meld(MeldKind.CHI,(Tile(0),Tile(4),Tile(8)),0,0),)
    assert after.discards[0] == () and len(after.players[1].hand) == 14
    assert after.last_drawn is None and after.pending is None
    assert not any(a.kind in (ActionKind.HU,ActionKind.KONG_CONCEALED,ActionKind.KONG_ADDED)
                   for a in legal_actions(after,1))


@pytest.mark.parametrize("order", list(permutations((1,2,3))))
def test_hu_overrides_peng_regardless_of_response_order(state_factory, order):
    peng_hand = tuple(Tile(i) for i in (1,2)+tuple(range(36,50)))
    hu_ids = (3,60,61,62,72,73,74,84,85,86,96,97,98,132,133,134)
    state = state_factory(hands={1:peng_hand,2:tuple(Tile(i) for i in hu_ids)})
    state = apply_action(state,Action(ActionKind.DISCARD,0,(0,))).state
    choices = {1:Action(ActionKind.PENG,1,(1,2)), 2:Action(ActionKind.HU,2), 3:Action(ActionKind.PASS,3)}
    first = apply_action(state,choices[order[0]]).state
    assert first.phase is Phase.RESPONSE and first.players == state.players
    after = respond(first,[choices[p] for p in order[1:]]).state
    assert (after.winner,after.win_source,after.winning_tile) == (2,0,0)
    assert after.end_reason is EndReason.DISCARD_WIN
    assert after.players[2].hand == state.players[2].hand
    assert after.discards[0][-1] == Tile(0)


def test_self_draw_ends_and_prevents_further_actions(winning_state):
    state = replace(winning_state,phase=Phase.DISCARD,winner=None,win_source=None,
                    winning_tile=None,end_reason=None)
    action = Action(ActionKind.HU,0)
    assert legal_actions(state,0)[0] == action
    transition = apply_action(state,action)
    assert transition.state == winning_state
    assert transition.events[0].kind is EventKind.WON
    with pytest.raises(MahjongError) as error:
        apply_action(transition.state,action)
    assert error.value.code == "INVALID_ACTION"


def test_concealed_kong_draws_from_back_and_keeps_kong_source(state_factory):
    state = state_factory(back=(135,136))
    action = Action(ActionKind.KONG_CONCEALED,0,(0,1,2,3))
    assert action in legal_actions(state,0)
    transition = apply_action(state,action)
    after = transition.state
    assert [e.kind for e in transition.events] == [EventKind.KONG_COMPLETED,EventKind.FLOWER,EventKind.DRAWN]
    assert [e.tile for e in transition.events[1:]] == [136,135]
    assert after.players[0].melds == (Meld(MeldKind.KONG_CONCEALED,tuple(Tile(i) for i in range(4)),None,None),)
    assert after.last_drawn == 135 and after.draw_source is DrawSource.KONG
    assert len(after.players[0].hand) == 14


def test_v1_never_offers_kongs(state_factory):
    state = state_factory(rules_version=1)
    assert not any(a.kind.name.startswith("KONG") for a in legal_actions(state,0))
    with pytest.raises(MahjongError) as error:
        apply_action(state,Action(ActionKind.KONG_CONCEALED,0,(0,1,2,3)))
    assert error.value.code == "INVALID_ACTION"


def test_added_kong_waits_for_all_passes_and_preserves_original_claim(state_factory):
    meld = Meld(MeldKind.PENG,(Tile(0),Tile(1),Tile(2)),1,1)
    state = state_factory(melds={0:(meld,)},back=(135,))
    action = Action(ActionKind.KONG_ADDED,0,(3,))
    declared = apply_action(state,action)
    assert declared.state.phase is Phase.ROB_KONG
    assert declared.state.players == state.players
    assert declared.state.last_drawn == state.last_drawn
    assert declared.events[0].kind is EventKind.KONG_DECLARED
    assert all(a.kind in (ActionKind.HU,ActionKind.PASS) for p in (1,2,3)
               for a in legal_actions(declared.state,p))
    final = respond(declared.state,[Action(ActionKind.PASS,p) for p in (3,1,2)])
    kong = final.state.players[0].melds[0]
    assert kong == Meld(MeldKind.KONG_ADDED,tuple(Tile(i) for i in range(4)),1,1)
    assert final.state.pending_kong is None and final.state.draw_source is DrawSource.KONG
    assert final.state.last_drawn == 135


def test_robbed_kong_has_separate_tile_zone(state_factory, make_tiles):
    meld = Meld(MeldKind.PENG,(Tile(0),Tile(1),Tile(2)),2,1)
    # Rob the fourth 1m by completing a 123m sequence with 2m/3m.
    waiting = tuple(Tile(i) for i in (4,8,60,61,62,72,73,74,84,85,86,96,97,98,132,133))
    # Four triplets, one sequence completed by 1m, and a white pair.
    state = state_factory(hands={1:waiting},melds={0:(meld,)})
    declared = apply_action(state,Action(ActionKind.KONG_ADDED,0,(3,))).state
    assert Action(ActionKind.HU,1) in legal_actions(declared,1)
    after = respond(declared,[Action(ActionKind.PASS,3),Action(ActionKind.HU,1),Action(ActionKind.PASS,2)]).state
    assert after.end_reason is EndReason.ROB_KONG and after.winner == 1
    assert after.robbed_tile == Tile(3) and after.winning_tile == 3
    assert after.players[0].melds == (meld,)
    assert Tile(3) not in after.players[0].hand and Tile(3) not in after.players[1].hand
    assert after.pending_kong is after.last_drawn is after.draw_source is None
    validate_state(after)
