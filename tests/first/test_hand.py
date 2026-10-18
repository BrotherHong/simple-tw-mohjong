from collections import Counter

import pytest

from tests.first.conftest import tiles
from tw_mahjong.hand import analyze_hand, find_waits
from tw_mahjong.model import Decomposition, MahjongError, Meld, MeldKind, Tile


def test_unique_five_groups_and_pair():
    hand = tiles(0, 1, 2, 9, 10, 11, 18, 19, 20, 27, 27, 27, 31, 31, 31, 33, 33)
    expected = Decomposition(33, ((0, 1, 2), (9, 10, 11), (18, 19, 20),
                                  (27, 27, 27), (31, 31, 31)))
    assert analyze_hand(hand).decompositions == (expected,)
    assert analyze_hand(hand).winning
    assert analyze_hand(tuple(reversed(hand))) == analyze_hand(hand)


def test_ambiguous_hand_explores_triplets_and_sequences():
    hand = tiles(*([0] * 3 + [1] * 3 + [2] * 3 + [9] * 3 + [18] * 3 + [33] * 2))
    result = analyze_hand(hand)
    groups = {d.groups for d in result.decompositions}
    assert ((0, 0, 0), (1, 1, 1), (2, 2, 2), (9, 9, 9), (18, 18, 18)) in groups
    assert ((0, 1, 2), (0, 1, 2), (0, 1, 2), (9, 9, 9), (18, 18, 18)) in groups
    assert result.decompositions == tuple(sorted(set(result.decompositions)))
    # Every returned decomposition reconstructs exactly the supplied multiset.
    for d in result.decompositions:
        assert Counter([d.pair] * 2 + [k for g in d.groups for k in g]) == Counter(t.kind for t in hand)


def test_valid_nonwinning_hand():
    result = analyze_hand(tiles(*range(17)))
    assert not result.winning
    assert result.decompositions == ()


@pytest.mark.parametrize("kind", [MeldKind.PENG, MeldKind.KONG_CONCEALED])
def test_declared_meld_counts_as_one_group(kind):
    meld = Meld(kind, tuple(Tile(i) for i in range(3 if kind is MeldKind.PENG else 4)),
                1 if kind is MeldKind.PENG else None, 0 if kind is MeldKind.PENG else None)
    hand = tiles(9, 10, 11, 18, 19, 20, 27, 27, 27, 31, 31, 31, 33, 33)
    result = analyze_hand(hand, (meld,))
    assert result.winning
    assert all(len(d.groups) == 4 for d in result.decompositions)


def test_single_pair_wait_and_copy_independence():
    hand = tiles(0, 0, 0, 9, 9, 9, 18, 18, 18, 27, 27, 27, 31, 31, 31, 33)
    assert find_waits(hand) == (33,)
    assert find_waits(tuple(reversed(hand))) == (33,)
    swapped = tuple(Tile(t.id + 1) if t.kind == 33 else t for t in hand)
    assert find_waits(swapped) == (33,)


def test_five_melds_leave_only_the_pair():
    melds = tuple(Meld(MeldKind.PENG, tuple(Tile(k * 4 + i) for i in range(3)), 1, k * 4)
                  for k in (0, 9, 18, 27, 31))
    assert analyze_hand(tiles(33, 33), melds).decompositions == (Decomposition(33, ()),)
    assert find_waits(tiles(33), melds) == (33,)


@pytest.mark.parametrize("function,length", [(analyze_hand, 17), (find_waits, 16)])
@pytest.mark.parametrize("problem", ["list", "short", "duplicate", "flower", "non_tile"])
def test_invalid_hands(function, length, problem):
    hand = tuple(Tile(i) for i in range(length))
    if problem == "list":
        hand = list(hand)
    elif problem == "short":
        hand = hand[:-1]
    elif problem == "duplicate":
        hand = hand[:-1] + (hand[0],)
    elif problem == "flower":
        hand = hand[:-1] + (Tile(136),)
    else:
        hand = hand[:-1] + (0,)
    with pytest.raises(MahjongError) as caught:
        function(hand)
    assert caught.value.code == "INVALID_HAND"


@pytest.mark.parametrize("melds", [[], (None,), (None,) * 6])
def test_invalid_meld_collection(melds):
    with pytest.raises(MahjongError) as caught:
        analyze_hand(tuple(Tile(i) for i in range(17)), melds)
    assert caught.value.code == "INVALID_MELD"


def test_duplicate_between_meld_and_hand_rejected():
    meld = Meld(MeldKind.PENG, (Tile(0), Tile(1), Tile(2)), 1, 0)
    with pytest.raises(MahjongError) as caught:
        analyze_hand(tuple(Tile(i) for i in range(14)), (meld,))
    assert caught.value.code == "INVALID_HAND"


def test_two_sided_wait_is_sorted_and_stays_in_suit():
    melds = tuple(Meld(MeldKind.PENG, tuple(Tile(k * 4 + i) for i in range(3)), 1, k * 4)
                  for k in (27, 28, 31, 32))
    assert find_waits(tiles(3, 4, 33, 33), melds) == (2, 5)


def test_waits_cannot_invent_fifth_copy_already_owned_in_meld():
    melds = tuple(Meld(MeldKind.PENG, tuple(Tile(k * 4 + i) for i in range(3)), 1, k * 4)
                  for k in (0, 9, 18, 27))
    # 4m can form the pair with 123m; a fifth 1m must not be offered.
    assert find_waits((Tile(3), Tile(4), Tile(8), Tile(12)), melds) == (3,)
