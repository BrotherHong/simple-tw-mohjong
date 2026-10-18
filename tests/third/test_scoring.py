"""Fixed tai awards, exclusivity, winning placements and zero-sum payments."""

from dataclasses import replace

import pytest

from tw_mahjong.engine import validate_state
from tw_mahjong.model import DrawSource, EndReason, MahjongError, Meld, MeldKind, Phase, SettlementConfig, Tile
from tw_mahjong.scoring import score_hand, settle_hand


def items(state):
    score = score_hand(state)
    assert score.tai == sum(item.tai for item in score.items)
    assert tuple(item.code for item in score.items) == tuple(sorted(item.code for item in score.items))
    return {item.code: item.tai for item in score.items}


def test_closed_sequence_self_draw_exact_score(won):
    score = score_hand(won)
    assert items(won) == {"CONCEALED_SELF_DRAW": 3, "SINGLE_WAIT": 1}
    assert score.tai == 4
    assert score.decomposition.pair == 27
    assert score.winning_group is None


def test_closed_discard_win_replaces_combined_award(finish, winning_tiles):
    state = finish(winning_tiles, source=1)
    assert items(state) == {"CONCEALED": 1, "SINGLE_WAIT": 1}


@pytest.mark.parametrize("source", [DrawSource.INITIAL, DrawSource.NORMAL, DrawSource.FLOWER, DrawSource.KONG])
def test_supplement_win_depends_on_draw_source(finish, winning_tiles, source):
    state = finish(winning_tiles, draw_source=source)
    assert ("SUPPLEMENT_WIN" in items(state)) == (source in (DrawSource.FLOWER, DrawSource.KONG))


def test_last_draw_and_last_discard_are_separate(finish, winning_tiles):
    self_draw = finish(winning_tiles, empty_wall=True)
    assert items(self_draw)["LAST_DRAW"] == 1
    assert "LAST_DISCARD" not in items(self_draw)
    discard = finish(winning_tiles, source=1, empty_wall=True)
    assert "LAST_DISCARD" not in items(discard)
    discard = replace(discard, last_discard_last=True)
    assert items(discard)["LAST_DISCARD"] == 1
    assert "LAST_DRAW" not in items(discard)


@pytest.mark.parametrize("codes,awards,absent", [
    ("1m 1m 1m 1p 1p 1p 1s 1s 1s R R R G G G B B",
     {"SMALL_DRAGONS": 4, "ALL_TRIPLETS": 4, "FIVE_CONCEALED": 8},
     {"DRAGON_R", "DRAGON_G", "DRAGON_B", "BIG_DRAGONS", "THREE_CONCEALED", "FOUR_CONCEALED"}),
    ("1m 2m 3m 1p 2p 3p R R R G G G B B B E E",
     {"BIG_DRAGONS": 8}, {"SMALL_DRAGONS", "DRAGON_R", "DRAGON_G", "DRAGON_B"}),
    ("E E E S S S W W W N N N R R R G G",
     {"ALL_HONORS": 16, "BIG_WINDS": 16, "SEAT_WIND": 1, "ROUND_WIND": 1, "DRAGON_R": 1},
     {"ALL_TRIPLETS", "SMALL_WINDS", "PURE_SUIT", "MIXED_SUIT"}),
    ("E E E S S S W W W N N R R R 1m 2m 3m",
     {"SMALL_WINDS": 8, "MIXED_SUIT": 4}, {"BIG_WINDS", "PURE_SUIT", "ALL_HONORS"}),
    ("1m 2m 3m 1m 2m 3m 4m 5m 6m 4m 5m 6m 7m 8m 9m 9m 9m",
     {"PURE_SUIT": 8}, {"MIXED_SUIT", "ALL_HONORS"}),
])
def test_pattern_awards_and_suppression(tiles, finish, codes, awards, absent):
    found = items(finish(tiles(codes)))
    assert awards.items() <= found.items()
    assert not absent.intersection(found)


@pytest.mark.parametrize("winner,dealer,expected", [(0, 0, 2), (0, 1, 2), (2, 1, 2)])
def test_relative_seat_flowers_and_flower_sets(finish, winning_tiles, winner, dealer, expected):
    state = finish(winning_tiles, winner=winner, dealer=dealer,
                   flowers=tuple(Tile(i) for i in range(136, 144)))
    assert items(state)["SEAT_FLOWER"] == expected
    assert items(state)["FLOWER_SET"] == 2


def test_seat_wind_rotates_with_dealer(tiles, finish):
    hand = tiles("1m 2m 3m 4m 5m 6m 1p 2p 3p 1s 2s 3s S S S E E")
    south = finish(hand, winner=2, dealer=1, round_wind=28)
    assert items(south)["SEAT_WIND"] == items(south)["ROUND_WIND"] == 1
    east = finish(hand, winner=2, dealer=2, round_wind=27)
    assert "SEAT_WIND" not in items(east) and "ROUND_WIND" not in items(east)


def test_open_meld_loses_concealed_award_but_concealed_kong_keeps_it(tiles, finish):
    hand = tiles("4m 5m 6m 1p 2p 3p 4p 5p 6p 1s 2s 3s E E")
    peng = Meld(MeldKind.PENG, tuple(Tile(i) for i in range(3)), 1, 0)
    dark = Meld(MeldKind.KONG_CONCEALED, tuple(Tile(i) for i in range(4)), None, None)
    assert items(finish(hand, melds=(peng,))) == {"SELF_DRAW": 1, "SINGLE_WAIT": 1}
    assert items(finish(hand, melds=(dark,))) == {"CONCEALED_SELF_DRAW": 3, "SINGLE_WAIT": 1}


def test_discard_completed_triplet_is_not_concealed(tiles, finish):
    hand = tiles("1m 1m 1m 1p 1p 1p 1s 1s 1s R R R G G G B B")
    draw = finish(hand, last_drawn=126)
    discard = finish(hand, last_drawn=126, source=1)
    assert items(draw)["FIVE_CONCEALED"] == 8
    assert items(discard)["FOUR_CONCEALED"] == 5
    assert "FIVE_CONCEALED" not in items(discard)
    assert score_hand(discard).winning_group == (31, 31, 31)


def test_ambiguous_hand_selects_higher_scoring_triplet_decomposition(tiles, finish):
    hand = tiles("1m 1m 1m 2m 2m 2m 3m 3m 3m 4p 4p 4p 5s 5s 5s E E")
    score = score_hand(finish(hand))
    assert score.decomposition.groups == ((0, 0, 0), (1, 1, 1), (2, 2, 2), (12, 12, 12), (22, 22, 22))
    assert {item.code for item in score.items} >= {"ALL_TRIPLETS", "FIVE_CONCEALED"}


def test_exhausted_game_scores_and_settles_zero(make_state):
    state = make_state(phase=Phase.ENDED, empty_wall=True, end_reason=EndReason.WALL_EXHAUSTED)
    score = score_hand(state)
    assert score.tai == 0 and score.items == ()
    assert score.decomposition is score.winning_group is None
    settlement = settle_hand(state)
    assert settlement.payments == () and settlement.deltas == (0, 0, 0, 0)


def test_scoring_requires_finished_v2(initial, make_state, winning_tiles):
    legacy = make_state(hands={0: winning_tiles}, rules_version=1)
    from tw_mahjong.engine import apply_action
    from tw_mahjong.model import Action, ActionKind
    legacy = apply_action(legacy, Action(ActionKind.HU, 0)).state
    for state in (initial, legacy):
        with pytest.raises(MahjongError) as exc:
            score_hand(state)
        assert exc.value.code == "INVALID_SCORE"


@pytest.mark.parametrize("winner,dealer,source", [(0, 0, None), (2, 0, None), (2, 0, 1), (2, 0, 0), (0, 0, 2)])
@pytest.mark.parametrize("config", [SettlementConfig(), SettlementConfig(0, 1), SettlementConfig(250, 37)])
def test_settlement_payment_formula_and_zero_sum(finish, winning_tiles, winner, dealer, source, config):
    state = finish(winning_tiles, winner=winner, dealer=dealer, source=source)
    settlement = settle_hand(state, config)
    payers = tuple(p for p in range(4) if p != winner) if source is None else (source,)
    assert tuple(p.payer for p in settlement.payments) == payers
    expected = [0] * 4
    for payment in settlement.payments:
        tai = settlement.score.tai + int(winner == dealer or payment.payer == dealer)
        assert payment.payee == winner and payment.tai == tai
        assert payment.amount == config.base + config.tai_value * tai
        expected[payment.payer] -= payment.amount
        expected[winner] += payment.amount
    assert settlement.deltas == tuple(expected)
    assert sum(settlement.deltas) == 0


def test_settle_rejects_nonconfig(won):
    with pytest.raises(MahjongError) as exc:
        settle_hand(won, None)
    assert exc.value.code == "INVALID_SETTLEMENT"


def test_robbed_kong_scores_only_robbery_context_and_source_pays(robbed_win):
    state = robbed_win.final_state
    found = items(state)
    assert found["ROB_KONG"] == 1 and found["CONCEALED"] == 1
    assert not {"SELF_DRAW", "CONCEALED_SELF_DRAW", "SUPPLEMENT_WIN", "LAST_DRAW", "LAST_DISCARD"}.intersection(found)
    settlement = settle_hand(state)
    assert len(settlement.payments) == 1
    assert settlement.payments[0].payer == 0 and settlement.payments[0].payee == 2


def test_multiple_waits_do_not_receive_single_wait(tiles, finish):
    hand = tiles("1m 2m 3m 4p 5p 6p 7p 8p 9p 1s 2s 3s 4s 5s 6s E E")
    state = finish(hand, last_drawn=0)
    assert "SINGLE_WAIT" not in items(state)
