"""Exact tai awards, exclusive patterns and zero-sum payer calculations."""

from dataclasses import replace

import pytest

from tw_mahjong.model import (
    DrawSource, EndReason, MahjongError, Meld, MeldKind, Phase,
    ScoreItem, ScoreResult, SettlementConfig, Tile,
)
from tw_mahjong.scoring import score_hand, settle_hand


def items(state):
    return {item.code:item.tai for item in score_hand(state).items}


def test_exact_closed_self_draw_score_and_unique_pair_placement(winning_state):
    score = score_hand(winning_state)
    expected = {
        "ALL_TRIPLETS":4, "CONCEALED_SELF_DRAW":3, "DRAGON_R":1,
        "FIVE_CONCEALED":8, "ROUND_WIND":1, "SEAT_WIND":1, "SINGLE_WAIT":1,
    }
    assert score.tai == 19
    assert score.items == tuple(ScoreItem(k,v) for k,v in sorted(expected.items()))
    assert score.decomposition.pair == 33 and score.winning_group is None


def test_exhaustion_has_zero_score_and_no_payments(exhausted_state):
    assert score_hand(exhausted_state) == ScoreResult(0,(),None,None)
    result = settle_hand(exhausted_state)
    assert result.payments == () and result.deltas == (0,0,0,0)


def test_scoring_rejects_unfinished_and_legacy_states(initial_state, exhausted_state):
    for state in (initial_state,replace(exhausted_state,rules_version=1)):
        with pytest.raises(MahjongError) as error:
            score_hand(state)
        assert error.value.code == "INVALID_SCORE"


@pytest.mark.parametrize("source,extra", [(DrawSource.INITIAL,{}), (DrawSource.NORMAL,{}),
                                        (DrawSource.FLOWER,{"SUPPLEMENT_WIN":1}),
                                        (DrawSource.KONG,{"SUPPLEMENT_WIN":1})])
def test_supplement_award_depends_on_draw_source(winning_state, source, extra):
    expected = items(winning_state)
    expected.update(extra)
    assert items(replace(winning_state,draw_source=source)) == expected


def test_self_draw_last_tile_award(state_factory, make_tiles):
    hand = make_tiles([0]*3+[9]*3+[18]*3+[27]*3+[31]*3+[33]*2)
    state = state_factory(hands={0:hand},phase=Phase.ENDED,exhausted=True,
                          winner=0,win_source=0,winning_tile=hand[-1].id,
                          last_drawn=hand[-1].id,end_reason=EndReason.SELF_DRAW)
    assert items(state)["LAST_DRAW"] == 1
    assert "LAST_DISCARD" not in items(state)


@pytest.mark.parametrize("kinds,awarded,excluded", [
    ([0]*3+[1]*3+[2]*3+[3]*3+[4]*3+[8]*2,"PURE_SUIT",("MIXED_SUIT","ALL_HONORS")),
    ([0]*3+[1]*3+[2]*3+[27]*3+[31]*3+[33]*2,"MIXED_SUIT",("PURE_SUIT","ALL_HONORS")),
    ([27]*3+[28]*3+[29]*3+[30]*3+[31]*3+[33]*2,"ALL_HONORS",("PURE_SUIT","MIXED_SUIT","ALL_TRIPLETS")),
])
def test_suit_patterns_are_mutually_exclusive(state_factory, make_tiles, kinds, awarded, excluded):
    hand = make_tiles(kinds)
    state = state_factory(hands={0:hand},phase=Phase.ENDED,
                          winner=0,win_source=0,winning_tile=hand[-1].id,
                          last_drawn=hand[-1].id,end_reason=EndReason.SELF_DRAW)
    score = items(state)
    assert score[awarded] == {"PURE_SUIT":8,"MIXED_SUIT":4,"ALL_HONORS":16}[awarded]
    assert all(code not in score for code in excluded)


@pytest.mark.parametrize("kinds,award,tai", [
    ([0]*3+[9]*3+[18]*3+[31]*3+[32]*3+[33]*2,"SMALL_DRAGONS",4),
    ([0]*3+[9]*3+[31]*3+[32]*3+[33]*3+[18]*2,"BIG_DRAGONS",8),
])
def test_dragon_patterns_suppress_individual_dragon_awards(state_factory, make_tiles, kinds, award, tai):
    hand = make_tiles(kinds)
    state = state_factory(hands={0:hand},phase=Phase.ENDED,
                          winner=0,win_source=0,winning_tile=hand[-1].id,
                          last_drawn=hand[-1].id,end_reason=EndReason.SELF_DRAW)
    result = items(state)
    assert result[award] == tai
    assert not {"DRAGON_R","DRAGON_G","DRAGON_B"}.intersection(result)
    assert not ({"BIG_DRAGONS","SMALL_DRAGONS"}-{award}).intersection(result)


@pytest.mark.parametrize("kinds,award,tai", [
    ([0]*3+[9]*3+[27]*3+[28]*3+[29]*3+[30]*2,"SMALL_WINDS",8),
    ([0]*3+[27]*3+[28]*3+[29]*3+[30]*3+[9]*2,"BIG_WINDS",16),
])
def test_wind_patterns_keep_seat_and_round_wind(state_factory, make_tiles, kinds, award, tai):
    hand = make_tiles(kinds)
    state = state_factory(hands={0:hand},phase=Phase.ENDED,
                          winner=0,win_source=0,winning_tile=hand[-1].id,
                          last_drawn=hand[-1].id,end_reason=EndReason.SELF_DRAW)
    result = items(state)
    assert result[award] == tai
    assert result["SEAT_WIND"] == result["ROUND_WIND"] == 1


def test_seat_wind_is_relative_to_dealer(winning_state):
    assert "SEAT_WIND" not in items(replace(winning_state,dealer=1))
    assert items(replace(winning_state,dealer=1))["ROUND_WIND"] == 1
    assert "ROUND_WIND" not in items(replace(winning_state,round_wind=28))


def test_flower_sets_and_seat_flowers_accumulate(state_factory, make_tiles):
    hand = make_tiles([0]*3+[9]*3+[18]*3+[27]*3+[31]*3+[33]*2)
    state = state_factory(hands={1:hand},flowers={1:tuple(Tile(i) for i in range(136,144))},
                          phase=Phase.ENDED,turn=1,dealer=0,winner=1,win_source=1,
                          winning_tile=hand[-1].id,last_drawn=hand[-1].id,
                          end_reason=EndReason.SELF_DRAW)
    result = items(state)
    assert result["SEAT_FLOWER"] == 2 and result["FLOWER_SET"] == 2
    assert "SEAT_WIND" not in result


def test_open_hand_self_draw_uses_separate_award(state_factory, make_tiles):
    meld = Meld(MeldKind.PENG,(Tile(0),Tile(1),Tile(2)),1,0)
    hand = make_tiles([9]*3+[18]*3+[27]*3+[31]*3+[33]*2)
    state = state_factory(hands={0:hand},melds={0:(meld,)},phase=Phase.ENDED,
                          winner=0,win_source=0,winning_tile=hand[-1].id,
                          last_drawn=hand[-1].id,end_reason=EndReason.SELF_DRAW)
    result = items(state)
    assert result["SELF_DRAW"] == 1 and result["FOUR_CONCEALED"] == 5
    assert "CONCEALED" not in result and "CONCEALED_SELF_DRAW" not in result
    assert "FIVE_CONCEALED" not in result


@pytest.mark.parametrize("last", [False,True])
def test_discard_triplet_is_not_concealed_and_only_source_pays(state_factory, make_tiles, last):
    hand = make_tiles([0]*3+[9]*3+[18]*3+[27]*3+[31]*3+[33]*2)
    win = Tile(2)
    before = tuple(t for t in hand if t != win)
    state = state_factory(hands={1:before},phase=Phase.ENDED,turn=1,
                          discards=((win,),(),(),()),exhausted=last,
                          winner=1,win_source=0,winning_tile=win.id,
                          end_reason=EndReason.DISCARD_WIN,last_discard_last=last)
    result = items(state)
    assert result["CONCEALED"] == 1 and result["FOUR_CONCEALED"] == 5
    assert not {"FIVE_CONCEALED","SELF_DRAW","CONCEALED_SELF_DRAW","LAST_DRAW"}.intersection(result)
    assert result.get("LAST_DISCARD",0) == int(last)
    assert score_hand(state).winning_group == (0,0,0)
    settlement = settle_hand(state,SettlementConfig(10,2))
    assert len(settlement.payments) == 1
    payment = settlement.payments[0]
    assert (payment.payer,payment.payee,payment.tai) == (0,1,settlement.score.tai+1)
    assert payment.amount == 10+2*payment.tai
    assert settlement.deltas == (-payment.amount,payment.amount,0,0)


@pytest.mark.parametrize("dealer", [0,1,2,3])
def test_self_draw_payments_have_individual_dealer_bonus(winning_state, dealer):
    state = replace(winning_state,dealer=dealer)
    settlement = settle_hand(state,SettlementConfig(50,7))
    assert [p.payer for p in settlement.payments] == [1,2,3]
    assert all(p.payee == 0 for p in settlement.payments)
    for payment in settlement.payments:
        expected_tai = settlement.score.tai + int(dealer in (0,payment.payer))
        assert payment.tai == expected_tai
        assert payment.amount == 50+7*expected_tai
        assert settlement.deltas[payment.payer] == -payment.amount
    assert settlement.deltas[0] == sum(p.amount for p in settlement.payments)
    assert sum(settlement.deltas) == 0


@pytest.mark.parametrize("config", [None, {}, (100,20)])
def test_invalid_settlement_argument(winning_state, config):
    with pytest.raises(MahjongError) as error:
        settle_hand(winning_state,config)
    assert error.value.code == "INVALID_SETTLEMENT"
