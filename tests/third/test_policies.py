"""Own-hand partition scores and policy priority/randomness contracts."""

from dataclasses import replace
from random import Random

import pytest

from tw_mahjong.engine import apply_action, legal_actions, validate_state
from tw_mahjong.model import Action, ActionKind as A, MahjongError, Meld, MeldKind, Phase, Tile
from tw_mahjong.policies import BasicEfficiencyPolicy, evaluate_structure
from tw_mahjong.simulation import SimplePolicy


class ChoiceSpy(Random):
    def __init__(self, seed=17):
        super().__init__(seed)
        self.choices = []

    def choice(self, values):
        self.choices.append(tuple(values))
        return super().choice(values)


@pytest.mark.parametrize("codes,value", [
    ("1m 2m E S", 3), ("1m 3m E S", 2), ("1m 4m E S", 0),
    ("1m 1m E S", 4), ("1m 1m 1m E", 12), ("1m 2m 3m E", 12),
    ("9m 1p E S", 0), ("8m 9m 1p E", 3), ("E S W N", 0),
    ("1m 1m 2m 3m", 12),  # a tile cannot score in both pair and sequence
])
def test_disjoint_partition_values(tiles, codes, value):
    melds = tuple(Meld(MeldKind.PENG, tuple(Tile(k * 4 + i) for i in range(3)), 1, k * 4)
                  for k in (18, 21, 24, 31))
    assert evaluate_structure(tiles(codes), melds) == 48 + value


def test_concealed_bonus_and_kong_equivalent_count(tiles):
    hand = tiles("1m 2m E S")
    dark = tuple(Meld(MeldKind.KONG_CONCEALED, tuple(Tile(k * 4 + i) for i in range(4)), None, None)
                 for k in (18, 21, 24, 31))
    assert evaluate_structure(hand, dark) == 48 + 3 + 2
    open_meld = Meld(MeldKind.KONG_EXPOSED, dark[0].tiles, 1, dark[0].tiles[0].id)
    assert evaluate_structure(hand, (open_meld,) + dark[1:]) == 48 + 3


def test_structure_is_invariant_to_order_and_physical_copies(tiles):
    hand = tiles("1m 2m 3m 4m 5m 6m 1p 2p 3p 4p 5p 6p E E R G")
    assert evaluate_structure(hand) == 54
    assert evaluate_structure(tuple(reversed(hand))) == 54
    swapped = tuple(Tile(t.id + 2) for t in hand)
    assert evaluate_structure(swapped) == 54


@pytest.mark.parametrize("bad", [(), [], (Tile(136),) * 16, (Tile(0),) * 16])
def test_structure_rejects_invalid_hand(bad):
    with pytest.raises(MahjongError) as exc:
        evaluate_structure(bad)
    assert exc.value.code == "INVALID_HAND"


@pytest.mark.parametrize("rng", [None, 1, "seed", object()])
def test_basic_policy_requires_random(rng):
    with pytest.raises(MahjongError) as exc:
        BasicEfficiencyPolicy(rng)
    assert exc.value.code == "INVALID_POLICY"


@pytest.mark.parametrize("policy_type", [SimplePolicy, BasicEfficiencyPolicy])
def test_hu_priority_and_no_randomness(make_state, winning_tiles, policy_type):
    rng = ChoiceSpy()
    state = make_state(hands={0: winning_tiles})
    before = rng.getstate()
    assert policy_type(rng)(state, 0) == Action(A.HU, 0)
    assert rng.choices == [] and rng.getstate() == before


@pytest.mark.parametrize("policy_type", [SimplePolicy, BasicEfficiencyPolicy])
def test_kong_priority_and_first_choice(make_state, policy_type):
    rng = ChoiceSpy()
    state = make_state(hands={0: tuple(Tile(i) for i in range(16)) + (Tile(135),)})
    assert policy_type(rng)(state, 0) == Action(A.KONG_CONCEALED, 0, (0, 1, 2, 3))
    assert rng.choices == []


def test_discard_chooses_only_best_tied_tiles_with_one_random_call(tiles, make_state):
    hand = tiles("1m 1m 1m 1p 1p 1p 1s 1s 1s R R R G G G E B")
    state = make_state(hands={0: hand})
    rng = ChoiceSpy()
    chosen = BasicEfficiencyPolicy(rng)(state, 0)
    expected = (Action(A.DISCARD, 0, (108,)), Action(A.DISCARD, 0, (132,)))
    assert rng.choices == [expected]
    assert chosen in expected
    assert state.players[0].hand == hand


def test_even_unique_best_discard_calls_choice(tiles, make_state):
    hand = tiles("1m 1m 1m 1p 1p 1p 1s 1s 1s R R R E E S S 9s")
    state = make_state(hands={0: hand})
    rng = ChoiceSpy()
    assert BasicEfficiencyPolicy(rng)(state, 0) == Action(A.DISCARD, 0, (104,))
    assert rng.choices == [(Action(A.DISCARD, 0, (104,)),)]


@pytest.mark.parametrize("policy_type", [SimplePolicy, BasicEfficiencyPolicy])
def test_draw_and_pass_do_not_consume_randomness(make_state, policy_type):
    rng = ChoiceSpy()
    draw = make_state(phase=Phase.DRAW)
    assert policy_type(rng)(draw, 0) == Action(A.DRAW, 0)
    # A high honor absent from all three opposing hands permits only PASS.
    discard = make_state(hands={0: tuple(Tile(i) for i in range(16)) + (Tile(135),)})
    response = apply_action(discard, Action(A.DISCARD, 0, (135,))).state
    assert legal_actions(response, 1) == (Action(A.PASS, 1),)
    assert policy_type(rng)(response, 1) == Action(A.PASS, 1)
    assert rng.choices == []


def test_policy_ignores_opponent_hand_and_wall_order(initial):
    players = list(initial.players)
    own = players[2]
    # Swap a hidden hand tile with a wall tile, leaving all visible information fixed.
    wall = list(initial.wall.tiles)
    exchanged = own.hand[0]
    players[2] = replace(own, hand=tuple(sorted(own.hand[1:] + (wall[0],))))
    wall[0] = exchanged
    from tw_mahjong.wall import Wall
    changed = replace(initial, players=tuple(players), wall=Wall(tuple(reversed(wall))))
    validate_state(changed)
    rng1, rng2 = ChoiceSpy(), ChoiceSpy()
    assert BasicEfficiencyPolicy(rng1)(initial, 0) == BasicEfficiencyPolicy(rng2)(changed, 0)
    assert rng1.choices == rng2.choices


def test_basic_policy_does_not_claim_when_structure_does_not_improve(tiles, make_state):
    # Breaking a complete sequence and paying the exposed-hand penalty is worse.
    hand = tiles("1m 2m 3m 4m 5m 6m 1p 2p 3p 4p 5p 6p 1s 2s 3s E")
    used = {t.id for t in hand} | {5}
    dealer = (Tile(5),) + tuple(Tile(i) for i in range(136) if i not in used)[:16]
    state = make_state(hands={0: dealer, 1: hand})
    state = apply_action(state, Action(A.DISCARD, 0, (5,))).state
    assert any(a.kind is A.CHI for a in legal_actions(state, 1))
    rng = ChoiceSpy()
    assert BasicEfficiencyPolicy(rng)(state, 1) == Action(A.PASS, 1)
    assert rng.choices == []


def test_basic_policy_claims_strict_improvement_without_randomness(tiles, make_state):
    hand = tiles("1m 1m 4m 7m 1p 4p 7p 1s 4s 7s E S W N R G")
    used = {t.id for t in hand} | {2}
    dealer = (Tile(2),) + tuple(Tile(i) for i in range(136) if i not in used)[:16]
    state = make_state(hands={0: dealer, 1: hand})
    state = apply_action(state, Action(A.DISCARD, 0, (2,))).state
    rng = ChoiceSpy()
    assert BasicEfficiencyPolicy(rng)(state, 1) == Action(A.PENG, 1, (0, 1))
    assert rng.choices == []


def test_basic_policy_rejects_ineligible_player(initial):
    with pytest.raises(MahjongError) as exc:
        BasicEfficiencyPolicy(Random(0))(initial, 1)
    assert exc.value.code == "INVALID_POLICY"


@pytest.mark.parametrize("policy_type", [SimplePolicy, BasicEfficiencyPolicy])
def test_added_kong_is_preferred_to_discard(added_kong_ready, policy_type):
    rng = ChoiceSpy()
    assert policy_type(rng)(added_kong_ready, 0) == Action(A.KONG_ADDED, 0, (3,))
    assert rng.choices == []


@pytest.mark.parametrize("policy_type", [SimplePolicy, BasicEfficiencyPolicy])
def test_exposed_kong_is_preferred_to_peng(make_state, policy_type):
    state = make_state(hands={0: (Tile(0),) + tuple(Tile(i) for i in range(80, 96)),
                              1: tuple(Tile(i) for i in (1, 2, 3)) + tuple(Tile(i) for i in range(20, 33))})
    state = apply_action(state, Action(A.DISCARD, 0, (0,))).state
    rng = ChoiceSpy()
    assert policy_type(rng)(state, 1) == Action(A.KONG_EXPOSED, 1, (1, 2, 3))
    assert rng.choices == []
