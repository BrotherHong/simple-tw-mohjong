"""Exhaustive canonical decompositions and physically possible waits."""

from dataclasses import replace

import pytest

from tw_mahjong.hand import analyze_hand, find_waits
from tw_mahjong.model import Decomposition, MahjongError, Meld, MeldKind, Tile


def test_five_sequences_and_pair(winning_tiles):
    result = analyze_hand(winning_tiles)
    assert result.winning
    assert result.decompositions == (Decomposition(27, ((0, 1, 2), (3, 4, 5), (9, 10, 11), (12, 13, 14), (18, 19, 20))),)
    assert analyze_hand(tuple(reversed(winning_tiles))) == result


def test_triplet_and_sequence_branches_are_both_explored(tiles):
    hand = tiles("1m 1m 1m 2m 2m 2m 3m 3m 3m 4p 5p 6p 7s 8s 9s E E")
    common = ((12, 13, 14), (24, 25, 26))
    assert analyze_hand(hand).decompositions == (
        Decomposition(27, ((0, 0, 0), (1, 1, 1), (2, 2, 2)) + common),
        Decomposition(27, ((0, 1, 2),) * 3 + common),
    )
    swapped = tuple(Tile(t.id ^ 1) if t.kind >= 9 else t for t in hand)
    assert analyze_hand(swapped) == analyze_hand(hand)


@pytest.mark.parametrize("codes", [
    "8m 9m 1p 2p 3p 4p 1s 2s 3s 4s 5s 6s E E E S S",
    "E S W 1m 2m 3m 4p 5p 6p 7s 8s 9s R R R B B",
])
def test_suits_and_honors_cannot_make_false_sequences(tiles, codes):
    result = analyze_hand(tiles(codes))
    assert not result.winning
    assert result.decompositions == ()


@pytest.mark.parametrize("kong", [False, True])
def test_declared_melds_not_repeated_in_decomposition(tiles, kong):
    meld = Meld(MeldKind.KONG_CONCEALED if kong else MeldKind.PENG,
                tuple(Tile(i) for i in range(4 if kong else 3)),
                None if kong else 2, None if kong else 0)
    hand = tiles("4m 5m 6m 1p 2p 3p 4p 5p 6p 1s 2s 3s E E")
    analysis = analyze_hand(hand, (meld,))
    assert analysis.winning
    assert len(analysis.decompositions[0].groups) == 4


def test_five_melds_leave_only_pair(tiles):
    melds = tuple(Meld(MeldKind.PENG, tuple(Tile(k * 4 + i) for i in range(3)), 1, k * 4) for k in range(5))
    assert analyze_hand(tiles("E E"), melds).decompositions == (Decomposition(27, ()),)
    assert find_waits(tiles("E"), melds) == (27,)
    assert analyze_hand(tiles("E E"), tuple(reversed(melds))) == analyze_hand(tiles("E E"), melds)


def test_single_wait_and_two_sided_wait(tiles, winning_tiles):
    assert find_waits(winning_tiles[:-1]) == (27,)
    hand = tiles("2m 3m 4p 5p 6p 7p 8p 9p 1s 2s 3s 4s 5s 6s E E")
    assert find_waits(hand) == (0, 3)
    assert find_waits(tuple(reversed(hand))) == (0, 3)


def test_waits_never_invent_fifth_copy(tiles):
    melds = tuple(Meld(MeldKind.PENG, tuple(Tile(k * 4 + i) for i in range(3)), 1, k * 4) for k in range(5))
    assert find_waits((Tile(3),), melds) == ()


@pytest.mark.parametrize("function,size", [(analyze_hand, 17), (find_waits, 16)])
def test_hand_rejects_container_flowers_duplicates_and_wrong_size(function, size):
    good = tuple(Tile(i) for i in range(size))
    for bad in (list(good), good[:-1], good + (Tile(80),), (Tile(136),) + good[1:], (good[1],) + good[1:], (None,) + good[1:]):
        with pytest.raises(MahjongError) as exc:
            function(bad)
        assert exc.value.code == "INVALID_HAND"


@pytest.mark.parametrize("melds", [[], (None,), (None,) * 6])
def test_invalid_meld_collection(winning_tiles, melds):
    with pytest.raises(MahjongError) as exc:
        analyze_hand(winning_tiles, melds)
    assert exc.value.code == "INVALID_MELD"


def test_duplicate_between_hand_and_meld_is_rejected(tiles):
    meld = Meld(MeldKind.CHI, (Tile(0), Tile(4), Tile(8)), 1, 0)
    hand = tiles("1m 5m 6m 1p 2p 3p 4p 5p 6p 1s 2s 3s E E")
    with pytest.raises(MahjongError) as exc:
        analyze_hand(hand, (meld,))
    assert exc.value.code == "INVALID_HAND"
