"""Independent heuristic examples, own-hand decisions and RNG discipline."""

from dataclasses import replace
from random import Random

import pytest

from tw_mahjong.engine import apply_action, legal_actions
from tw_mahjong.model import Action, ActionKind, MahjongError, Meld, MeldKind, Phase, Tile
from tw_mahjong.policies import BasicEfficiencyPolicy, evaluate_structure
from tw_mahjong.simulation import SimplePolicy


class ChoiceSpy(Random):
    def __init__(self):
        super().__init__(3)
        self.calls = []
    def choice(self, options):
        self.calls.append(tuple(options))
        return options[-1]


@pytest.mark.parametrize("kinds,expected", [
    ([0,1,2,8],12), ([0,0,0,8],12), ([0,0,8,8],8),
    ([0,1,6,8],5), ([0,2,5,8],2), ([0,3,6,8],2),
    ([7,8,9,10],6),  # Two adjacent runs; no cross-suit sequence.
    ([0,0,1,2],12),  # A sequence beats a pair plus run; tiles used once.
])
def test_structure_exact_small_hand_partitions(make_tiles, kinds, expected):
    melds = tuple(Meld(MeldKind.PENG,make_tiles([k]*3),1,k*4) for k in (27,28,29,30))
    assert evaluate_structure(make_tiles(kinds),melds) == 48+expected


def test_honors_never_form_runs_and_closed_bonus_is_two(make_tiles):
    hand = make_tiles([0]*3+[9]*3+[18]*3+[27,28,29,30,31,32,33])
    assert evaluate_structure(hand) == 3*12+2
    assert evaluate_structure(tuple(reversed(hand))) == 38


def test_concealed_kong_is_closed_and_counts_one_completed_group(make_tiles):
    concealed = Meld(MeldKind.KONG_CONCEALED,tuple(Tile(i) for i in range(4)),None,None)
    exposed = Meld(MeldKind.KONG_EXPOSED,tuple(Tile(i) for i in range(4)),1,0)
    hand = make_tiles([9]*3+[18]*3+[27]*3+[31]*3+[33])
    assert evaluate_structure(hand,(concealed,)) == 62
    assert evaluate_structure(hand,(exposed,)) == 60


@pytest.mark.parametrize("hand,melds,code", [
    ((),(),"INVALID_HAND"), ([],(),"INVALID_HAND"),
    ((Tile(0),)*16,(),"INVALID_HAND"),
    (tuple(Tile(i) for i in range(15))+(Tile(136),),(),"INVALID_HAND"),
    ((),[],"INVALID_MELD"), ((),(None,),"INVALID_MELD"),
])
def test_structure_input_validation(hand, melds, code):
    with pytest.raises(MahjongError) as error:
        evaluate_structure(hand,melds)
    assert error.value.code == code


@pytest.mark.parametrize("rng", [None, 0, object()])
def test_basic_policy_requires_injected_random(rng):
    with pytest.raises(MahjongError) as error:
        BasicEfficiencyPolicy(rng)
    assert error.value.code == "INVALID_POLICY"


@pytest.mark.parametrize("policy_type", [BasicEfficiencyPolicy,SimplePolicy])
def test_win_priority_does_not_consume_randomness(winning_state, policy_type):
    state = replace(winning_state,phase=Phase.DISCARD,winner=None,win_source=None,
                    winning_tile=None,end_reason=None)
    rng = ChoiceSpy()
    before = rng.getstate()
    assert policy_type(rng)(state,0) == Action(ActionKind.HU,0)
    assert rng.calls == [] and rng.getstate() == before


@pytest.mark.parametrize("policy_type", [BasicEfficiencyPolicy,SimplePolicy])
def test_concealed_kong_priority_over_discard(state_factory, policy_type):
    hand = tuple(Tile(i) for i in (0,1,2,3,36,40,44,72,76,80,84,88,92,108,112,124,132))
    state = state_factory(hands={0:hand})
    rng = ChoiceSpy()
    assert policy_type(rng)(state,0) == Action(ActionKind.KONG_CONCEALED,0,(0,1,2,3))
    assert rng.calls == []


def test_basic_policy_discards_isolated_honor_and_calls_choice_even_single_candidate(state_factory, make_tiles):
    # Five completed triplets and a singleton leave exactly one best discard.
    hand = make_tiles([0]*3+[9]*3+[18]*3+[27]*3+[31]*3+[33,32])
    state = state_factory(hands={0:hand})
    rng = ChoiceSpy()
    action = BasicEfficiencyPolicy(rng)(state,0)
    # Both single honors tie, in physical id order.
    expected = (Action(ActionKind.DISCARD,0,(128,)),Action(ActionKind.DISCARD,0,(132,)))
    assert rng.calls == [expected] and action == expected[-1]


def test_unique_best_discard_still_calls_rng_once(state_factory, make_tiles):
    hand = make_tiles([0,1,2,9,10,11,18,19,20,21,22,23,27,27,31,31,33])
    state = state_factory(hands={0:hand})
    rng = ChoiceSpy()
    expected = Action(ActionKind.DISCARD,0,(132,))
    assert BasicEfficiencyPolicy(rng)(state,0) == expected
    assert rng.calls == [(expected,)]


def test_basic_policy_discard_is_best_legal_structure(initial_state):
    own = initial_state.players[0]
    discards = tuple(a for a in legal_actions(initial_state,0) if a.kind is ActionKind.DISCARD)
    scores = [evaluate_structure(tuple(t for t in own.hand if t.id != a.tiles[0]),own.melds) for a in discards]
    best = tuple(a for a,s in zip(discards,scores) if s == max(scores))
    rng = ChoiceSpy()
    assert BasicEfficiencyPolicy(rng)(initial_state,0) == best[-1]
    assert rng.calls == [best]


def test_hidden_wall_and_other_hands_do_not_affect_decision(initial_state):
    # All swaps preserve a valid state and the acting player's visible holdings.
    players = list(initial_state.players)
    players[1] = replace(players[1],hand=initial_state.players[2].hand)
    players[2] = replace(players[2],hand=initial_state.players[1].hand)
    changed = replace(initial_state,players=tuple(players),
                      wall=type(initial_state.wall)(tuple(reversed(initial_state.wall.tiles))))
    assert BasicEfficiencyPolicy(Random(7))(initial_state,0) == BasicEfficiencyPolicy(Random(7))(changed,0)


@pytest.mark.parametrize("policy_type", [BasicEfficiencyPolicy,SimplePolicy])
def test_no_options_is_invalid_policy(initial_state, policy_type):
    with pytest.raises(MahjongError) as error:
        policy_type(Random(0))(initial_state,1)
    assert error.value.code == "INVALID_POLICY"


def test_draw_needs_no_random_choice(state_factory):
    state = state_factory(phase=Phase.DRAW)
    rng = ChoiceSpy()
    assert BasicEfficiencyPolicy(rng)(state,0) == Action(ActionKind.DRAW,0)
    assert rng.calls == []


def test_claim_without_strict_improvement_passes(state_factory, make_tiles):
    # Breaking the existing 123m sequence to claim 1m costs the closed bonus.
    hand = make_tiles([0,1,2,9,10,11,18,19,20,21,22,23,27,27,31,31])
    state = state_factory(hands={1:hand})
    # P0 owns the second physical 1m after fixture allocation.
    discard = next(t for t in state.players[0].hand if t.kind == 0)
    state = apply_action(state,Action(ActionKind.DISCARD,0,(discard.id,))).state
    assert any(a.kind is ActionKind.CHI for a in legal_actions(state,1))
    rng = ChoiceSpy()
    assert BasicEfficiencyPolicy(rng)(state,1) == Action(ActionKind.PASS,1)
    assert rng.calls == []


def test_improving_peng_is_selected_without_random_choice(state_factory):
    hand = tuple(Tile(i) for i in (1,2,36,40,44,72,76,80,84,88,92,108,112,116,124,128))
    state = state_factory(hands={1:hand})
    state = apply_action(state,Action(ActionKind.DISCARD,0,(0,))).state
    rng = ChoiceSpy()
    assert BasicEfficiencyPolicy(rng)(state,1) == Action(ActionKind.PENG,1,(1,2))
    assert rng.calls == []
