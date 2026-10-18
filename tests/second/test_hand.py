"""Five melds and a pair, exhaustive decompositions and physical-copy waits."""

from collections import Counter
from itertools import combinations

import pytest

from tw_mahjong.hand import analyze_hand, find_waits
from tw_mahjong.model import Decomposition, MahjongError, Meld, MeldKind, Tile


def test_unique_triplet_hand_has_exact_decomposition(make_tiles):
    hand = make_tiles([0]*3 + [9]*3 + [18]*3 + [27]*3 + [31]*3 + [33]*2)
    result = analyze_hand(hand)
    assert result.winning
    assert result.decompositions == (Decomposition(33, ((0,0,0), (9,9,9), (18,18,18), (27,27,27), (31,31,31))),)


def test_ambiguous_hand_explores_triplets_and_sequences(make_tiles):
    hand = make_tiles([0]*3 + [1]*3 + [2]*3 + [9,10,11,18,19,20,27,27])
    expected = (
        Decomposition(27, ((0,0,0), (1,1,1), (2,2,2), (9,10,11), (18,19,20))),
        Decomposition(27, ((0,1,2), (0,1,2), (0,1,2), (9,10,11), (18,19,20))),
    )
    result = analyze_hand(hand)
    assert result.decompositions == expected
    assert analyze_hand(tuple(reversed(hand))) == result
    # Exchange copies without changing kinds or creating duplicate physical ids.
    swapped = tuple(Tile(t.id + 1) if t.kind == 27 else t for t in hand)
    assert analyze_hand(swapped) == result


def test_valid_nonwinning_hand_is_not_an_input_error(make_tiles):
    hand = make_tiles([0,2,4,6,8,9,11,13,15,17,18,20,22,24,26,27,28])
    assert analyze_hand(hand).winning is False
    assert analyze_hand(hand).decompositions == ()


@pytest.mark.parametrize("kind,ids,source,claimed", [
    (MeldKind.CHI, (0,4,8), 1, 0),
    (MeldKind.PENG, (0,1,2), 1, 0),
    (MeldKind.KONG_CONCEALED, (0,1,2,3), None, None),
])
def test_declared_meld_counts_as_one_group_not_returned_in_decomposition(make_tiles, kind, ids, source, claimed):
    meld = Meld(kind, tuple(Tile(i) for i in ids), source, claimed)
    hand = make_tiles([9]*3 + [18]*3 + [27]*3 + [31]*3 + [33]*2)
    result = analyze_hand(hand, (meld,))
    assert result.decompositions == (Decomposition(33, ((9,9,9), (18,18,18), (27,27,27), (31,31,31))),)


def test_five_open_melds_require_only_pair(make_tiles):
    melds = tuple(Meld(MeldKind.PENG, make_tiles([k]*3), 1, k*4) for k in (0,9,18,27,31))
    assert analyze_hand(make_tiles([33,33]), melds).decompositions == (Decomposition(33, ()),)
    assert find_waits(make_tiles([33]), tuple(reversed(melds))) == (33,)


@pytest.mark.parametrize("hand", [(), [], (Tile(0),)*17, (None,)*17, tuple(Tile(i) for i in range(16)) + (Tile(136),)])
def test_invalid_hands_report_invalid_hand(hand):
    with pytest.raises(MahjongError) as error:
        analyze_hand(hand)
    assert error.value.code == "INVALID_HAND"


@pytest.mark.parametrize("melds", [[], (None,), (None,)*6])
def test_invalid_meld_container_and_members(make_tiles, melds):
    with pytest.raises(MahjongError) as error:
        analyze_hand(make_tiles([0]*3+[9]*3+[18]*3+[27]*3+[31]*3+[33]*2), melds)
    assert error.value.code == "INVALID_MELD"


def test_duplicate_identity_across_hand_and_meld_is_rejected(make_tiles):
    meld = Meld(MeldKind.PENG, make_tiles([0]*3), 1, 0)
    hand = make_tiles([0,9,9,9,18,18,18,27,27,27,31,31,31,33])
    with pytest.raises(MahjongError) as error:
        analyze_hand(hand, (meld,))
    assert error.value.code == "INVALID_HAND"


def test_waits_single_pair_and_two_sided_sequence(make_tiles):
    triplets = [9]*3+[18]*3+[27]*3+[31]*3
    assert find_waits(make_tiles(triplets+[0,1,2,33])) == (33,)
    hand = make_tiles(triplets+[1,2,33,33])
    assert find_waits(hand) == (0,3)
    assert find_waits(tuple(reversed(hand))) == (0,3)


def test_waits_never_invents_a_fifth_physical_copy(make_tiles):
    melds = (
        Meld(MeldKind.PENG, make_tiles([0]*3), 1, 0),
        Meld(MeldKind.PENG, make_tiles([9]*3), 1, 36),
        Meld(MeldKind.PENG, make_tiles([18]*3), 1, 72),
        Meld(MeldKind.PENG, make_tiles([27]*3), 1, 108),
    )
    hand = (Tile(3), Tile(4), Tile(8), Tile(12))
    # 1m would form a pair and 234m, but all four copies are already owned.
    assert find_waits(hand, melds) == (3,)


def test_small_open_hand_matches_independent_brute_force_oracle(make_tiles):
    """Exhaust all 4-tile waits from one suit with four fixed honor melds.

    Independent oracle chooses a pair and checks the remaining three tiles;
    it does not call the implementation to compute the expected waits.
    """
    melds = tuple(Meld(MeldKind.PENG, make_tiles([k]*3), 1, 4*k) for k in (27,28,29,30))
    for kinds in combinations(range(7), 4):
        expected = []
        for candidate in range(34):
            counts = Counter(kinds + (candidate,))
            for pair in counts:
                if counts[pair] < 2:
                    continue
                rest = sorted((counts - Counter({pair: 2})).elements())
                if len(set(rest)) == 1 or (rest[0] < 27 and rest[0]//9 == rest[2]//9
                                                        and rest == list(range(rest[0], rest[0]+3))):
                    expected.append(candidate)
                    break
        assert find_waits(make_tiles(kinds), melds) == tuple(expected)


@pytest.mark.parametrize("hand", [(), [], (Tile(0),)*16, tuple(Tile(i) for i in range(17))])
def test_waits_rejects_wrong_count_or_duplicate_tiles(hand):
    with pytest.raises(MahjongError) as error:
        find_waits(hand)
    assert error.value.code == "INVALID_HAND"
