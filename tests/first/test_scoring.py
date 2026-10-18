from dataclasses import replace

import pytest

from tests.first.conftest import tiles
from tw_mahjong.engine import apply_action
from tw_mahjong.model import Action, ActionKind, DrawSource, MahjongError, Phase, SettlementConfig, Tile
from tw_mahjong.scoring import score_hand, settle_hand


def win(state_factory, kinds, **kwargs):
    state = state_factory(hands={0: tiles(*kinds)}, **kwargs)
    return apply_action(state, Action(ActionKind.HU, 0)).state


def items(state):
    return {item.code: item.tai for item in score_hand(state).items}


def test_fixed_score_items_and_total(winning_state):
    score = score_hand(winning_state)
    assert items(winning_state) == {
        "ALL_TRIPLETS": 4, "CONCEALED_SELF_DRAW": 3, "DRAGON_R": 1,
        "FIVE_CONCEALED": 8, "ROUND_WIND": 1, "SEAT_WIND": 1, "SINGLE_WAIT": 1,
    }
    assert score.tai == 19
    assert score.items == tuple(sorted(score.items))
    assert score.winning_group is None
    assert score.decomposition.pair == 33


@pytest.mark.parametrize("source", [DrawSource.FLOWER, DrawSource.KONG])
def test_supplement_award(source, winning_state):
    scored = items(replace(winning_state, draw_source=source))
    assert scored["SUPPLEMENT_WIN"] == 1
    assert "SELF_DRAW" not in scored
    assert "CONCEALED" not in scored


def test_all_honors_and_big_dragons_suppress_overlapping_items(state_factory):
    state = win(state_factory, [27] * 3 + [28] * 3 + [31] * 3 + [32] * 3 + [33] * 3 + [29] * 2)
    scored = items(state)
    assert scored["ALL_HONORS"] == 16
    assert scored["BIG_DRAGONS"] == 8
    assert not {"ALL_TRIPLETS", "MIXED_SUIT", "PURE_SUIT", "DRAGON_R", "DRAGON_G", "DRAGON_B"} & scored.keys()


def test_big_winds_and_seat_round_wind_accumulate(state_factory):
    state = win(state_factory, [27] * 3 + [28] * 3 + [29] * 3 + [30] * 3 + [31] * 3 + [33] * 2)
    scored = items(state)
    assert scored["BIG_WINDS"] == 16
    assert scored["SEAT_WIND"] == scored["ROUND_WIND"] == 1
    assert "SMALL_WINDS" not in scored


def test_small_dragons_suppress_individual_awards(state_factory):
    state = win(state_factory, [0] * 3 + [9] * 3 + [18] * 3 + [31] * 3 + [32] * 3 + [33] * 2)
    scored = items(state)
    assert scored["SMALL_DRAGONS"] == 4
    assert not {"BIG_DRAGONS", "DRAGON_R", "DRAGON_G", "DRAGON_B"} & scored.keys()


def test_pure_suit_and_mixed_suit_are_exclusive(state_factory):
    pure = win(state_factory, [0] * 3 + [1] * 3 + [2] * 3 + [3] * 3 + [4] * 3 + [8] * 2)
    mixed = win(state_factory, [0] * 3 + [1] * 3 + [2] * 3 + [3] * 3 + [31] * 3 + [33] * 2)
    assert items(pure)["PURE_SUIT"] == 8
    assert "MIXED_SUIT" not in items(pure)
    assert items(mixed)["MIXED_SUIT"] == 4
    assert "PURE_SUIT" not in items(mixed)


def test_flower_sets_and_relative_seat_flowers(state_factory):
    state = win(state_factory, [0] * 3 + [9] * 3 + [18] * 3 + [27] * 3 + [31] * 3 + [33] * 2,
                dealer=2, flowers={0: tuple(Tile(i) for i in range(136, 144))})
    scored = items(state)
    assert scored["SEAT_FLOWER"] == 2
    assert scored["FLOWER_SET"] == 2
    assert "SEAT_WIND" not in scored  # P0 is west when P2 is dealer.
    assert scored["ROUND_WIND"] == 1


def test_draw_has_zero_score_and_no_payments(exhausted):
    score = score_hand(exhausted)
    assert (score.tai, score.items, score.decomposition, score.winning_group) == (0, (), None, None)
    settled = settle_hand(exhausted)
    assert settled.payments == ()
    assert settled.deltas == (0, 0, 0, 0)


def test_unfinished_and_legacy_cannot_be_scored(initial, exhausted):
    for state in (initial, replace(exhausted, rules_version=1)):
        with pytest.raises(MahjongError) as caught:
            score_hand(state)
        assert caught.value.code == "INVALID_SCORE"


@pytest.mark.parametrize("dealer", [0, 1, 2, 3])
def test_self_draw_settlement_dealer_bonus_and_zero_sum(winning_state, dealer):
    state = replace(winning_state, dealer=dealer)
    config = SettlementConfig(7, 3)
    settlement = settle_hand(state, config)
    assert tuple(p.payer for p in settlement.payments) == (1, 2, 3)
    for payment in settlement.payments:
        assert payment.payee == 0
        assert payment.tai == settlement.score.tai + int(dealer in (0, payment.payer))
        assert payment.amount == 7 + 3 * payment.tai
        assert settlement.deltas[payment.payer] == -payment.amount
    assert settlement.deltas[0] == sum(p.amount for p in settlement.payments)
    assert sum(settlement.deltas) == 0


@pytest.mark.parametrize("config", [None, {}, 1])
def test_invalid_settlement_config(winning_state, config):
    with pytest.raises(MahjongError) as caught:
        settle_hand(winning_state, config)
    assert caught.value.code == "INVALID_SETTLEMENT"
