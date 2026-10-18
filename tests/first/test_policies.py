from dataclasses import replace
from random import Random

import pytest

from tests.first.conftest import tiles
from tw_mahjong.engine import apply_action, legal_actions
from tw_mahjong.model import Action, ActionKind, MahjongError, Meld, MeldKind, Phase, Tile
from tw_mahjong.policies import BasicEfficiencyPolicy, evaluate_structure


def test_completed_groups_and_singleton_exact_structure_score():
    hand = tiles(0, 1, 2, 9, 10, 11, 18, 19, 20, 27, 27, 27, 31, 31, 31, 33)
    assert evaluate_structure(hand) == 62  # five disjoint groups + closed bonus
    assert evaluate_structure(tuple(reversed(hand))) == 62


def test_pairs_not_double_counted_and_honors_do_not_form_runs():
    # Four copies score a triplet (12); they cannot also supply a pair (4).
    hand = tiles(*([27] * 4 + [28] * 4 + [29] * 4 + [30] * 4))
    assert evaluate_structure(hand) == 4 * 12 + 2


def test_open_meld_removes_closed_bonus_and_kong_is_one_group():
    hand = tiles(9, 10, 11, 18, 19, 20, 27, 27, 27, 31, 31, 31, 33)
    peng = Meld(MeldKind.PENG, (Tile(0), Tile(1), Tile(2)), 1, 0)
    kong = Meld(MeldKind.KONG_CONCEALED, tuple(Tile(i) for i in range(4)), None, None)
    assert evaluate_structure(hand, (peng,)) == 60
    assert evaluate_structure(hand, (kong,)) == 62


@pytest.mark.parametrize("rng", [None, 0, object()])
def test_basic_policy_requires_random(rng):
    with pytest.raises(MahjongError) as caught:
        BasicEfficiencyPolicy(rng)
    assert caught.value.code == "INVALID_POLICY"


def test_basic_policy_chooses_only_best_discard_with_one_rng_choice(initial):
    actions = tuple(a for a in legal_actions(initial, 0) if a.kind is ActionKind.DISCARD)
    scores = {a: evaluate_structure(tuple(t for t in initial.players[0].hand if t.id != a.tiles[0]))
              for a in actions}
    best = tuple(a for a in actions if scores[a] == max(scores.values()))
    rng, control = Random(12), Random(12)
    expected = control.choice(best)
    snapshot = repr(initial)
    assert BasicEfficiencyPolicy(rng)(initial, 0) == expected
    assert rng.getstate() == control.getstate()
    assert repr(initial) == snapshot


def test_policy_does_not_use_wall_order_for_scoring(initial):
    reversed_wall = replace(initial, wall=type(initial.wall)(tuple(reversed(initial.wall.tiles))))
    assert BasicEfficiencyPolicy(Random(5))(initial, 0) == BasicEfficiencyPolicy(Random(5))(reversed_wall, 0)


def test_win_precedes_discard_and_does_not_consume_rng(winning_state):
    state = replace(winning_state, phase=Phase.DISCARD, winner=None, win_source=None,
                    winning_tile=None, end_reason=None)
    rng = Random(7)
    before = rng.getstate()
    assert BasicEfficiencyPolicy(rng)(state, 0) == Action(ActionKind.HU, 0)
    assert rng.getstate() == before


def test_draw_and_ineligible_player(state_factory):
    state = state_factory(phase=Phase.DRAW)
    rng = Random(8)
    before = rng.getstate()
    assert BasicEfficiencyPolicy(rng)(state, 0) == Action(ActionKind.DRAW, 0)
    assert rng.getstate() == before
    with pytest.raises(MahjongError) as caught:
        BasicEfficiencyPolicy(rng)(state, 1)
    assert caught.value.code == "INVALID_POLICY"


@pytest.mark.parametrize("hand", [(), [], (Tile(136),) * 16, (Tile(0),) * 16])
def test_evaluation_validates_physical_hand(hand):
    with pytest.raises(MahjongError) as caught:
        evaluate_structure(hand)
    assert caught.value.code == "INVALID_HAND"


def test_claim_that_improves_structure_is_selected_without_rng(state_factory):
    # Five almost-complete groups: taking the third 1m improves the best partition.
    hand = tiles(0, 0, 9, 10, 11, 18, 19, 20, 27, 27, 27, 31, 31, 31, 33, 30)
    source_hand = (Tile(2),) + tuple(Tile(i) for i in range(16, 32))
    state = state_factory(hands={0: source_hand, 1: hand})
    pending = apply_action(state, Action(ActionKind.DISCARD, 0, (2,))).state
    rng = Random(21)
    before = rng.getstate()
    assert BasicEfficiencyPolicy(rng)(pending, 1) == Action(ActionKind.PENG, 1, (0, 1))
    assert rng.getstate() == before
    assert pending.players[1].melds == ()


def test_claim_that_breaks_closed_structure_is_declined(state_factory):
    # Completing 123m twice is better than exposing a peng of the two 2m tiles.
    hand = tiles(0, 0, 1, 1, 2, 2, 9, 10, 11, 18, 19, 20, 27, 27, 27, 33)
    state = state_factory(hands={0: (Tile(6),) + tuple(Tile(i) for i in range(16, 32)), 1: hand})
    pending = apply_action(state, Action(ActionKind.DISCARD, 0, (6,))).state
    assert any(a.kind is ActionKind.PENG for a in legal_actions(pending, 1))
    rng = Random(22)
    before = rng.getstate()
    assert BasicEfficiencyPolicy(rng)(pending, 1) == Action(ActionKind.PASS, 1)
    assert rng.getstate() == before
