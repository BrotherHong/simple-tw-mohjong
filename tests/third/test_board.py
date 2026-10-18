#  This file was automatically generated using Pynguin.

import random as _pynguin_random
import pytest
import weakref as _pynguin_weakref

_pynguin_orig_seed = getattr(
    _pynguin_random.Random.seed, "__pynguin_orig__", _pynguin_random.Random.seed
)
_pynguin_tracked = _pynguin_weakref.WeakSet()


def _pynguin_deterministic_seed(self, x=None):
    if x is None:
        x = 59
    elif type(x).__hash__ is object.__hash__:
        x = f"{type(x).__module__}.{type(x).__name__}"
    _pynguin_orig_seed(self, x)
    _pynguin_tracked.add(self)


_pynguin_deterministic_seed.__pynguin_patched__ = True
_pynguin_deterministic_seed.__pynguin_orig__ = _pynguin_orig_seed
_pynguin_deterministic_seed.__pynguin_instances__ = _pynguin_tracked
_pynguin_random.Random.seed = _pynguin_deterministic_seed
import sys
import tw_mahjong.board

board_ = sys.modules["tw_mahjong.board"]


@pytest.fixture(scope="module", autouse=True)
def _pynguin_restore_random():
    yield
    _pynguin_random.Random.seed = _pynguin_orig_seed


@pytest.fixture(autouse=True)
def _pynguin_seed_random():
    _pynguin_random.Random.seed = _pynguin_deterministic_seed
    _pynguin_random.seed(59)
    _pynguin_instances = getattr(
        _pynguin_random.Random.seed, "__pynguin_instances__", None
    )
    if _pynguin_instances is not None:
        for _inst in list(_pynguin_instances):
            _inst.seed(59)
    yield
    _pynguin_random.Random.seed = _pynguin_orig_seed


def test_0():
    var_65 = board_.display_width(text="_WYg#P^-veU")
    assert var_65 == 11
    assert board_.SCORE_NAMES == {
        "CONCEALED": "門清",
        "SELF_DRAW": "自摸",
        "CONCEALED_SELF_DRAW": "門清自摸",
        "DRAGON_R": "紅中",
        "DRAGON_G": "青發",
        "DRAGON_B": "白板",
        "SEAT_WIND": "門風",
        "ROUND_WIND": "圈風",
        "SEAT_FLOWER": "門花",
        "FLOWER_SET": "花槓",
        "ALL_TRIPLETS": "碰碰胡",
        "MIXED_SUIT": "混一色",
        "PURE_SUIT": "清一色",
        "ALL_HONORS": "字一色",
        "SMALL_DRAGONS": "小三元",
        "BIG_DRAGONS": "大三元",
        "SMALL_WINDS": "小四喜",
        "BIG_WINDS": "大四喜",
        "THREE_CONCEALED": "三暗刻",
        "FOUR_CONCEALED": "四暗刻",
        "FIVE_CONCEALED": "五暗刻",
        "SUPPLEMENT_WIN": "槓上開花",
        "ROB_KONG": "搶槓",
        "LAST_DRAW": "海底撈月",
        "LAST_DISCARD": "河底撈魚",
        "SINGLE_WAIT": "獨聽",
    }


def test_1():
    var_69 = 3
    assert board_.SCORE_NAMES == {
        "CONCEALED": "門清",
        "SELF_DRAW": "自摸",
        "CONCEALED_SELF_DRAW": "門清自摸",
        "DRAGON_R": "紅中",
        "DRAGON_G": "青發",
        "DRAGON_B": "白板",
        "SEAT_WIND": "門風",
        "ROUND_WIND": "圈風",
        "SEAT_FLOWER": "門花",
        "FLOWER_SET": "花槓",
        "ALL_TRIPLETS": "碰碰胡",
        "MIXED_SUIT": "混一色",
        "PURE_SUIT": "清一色",
        "ALL_HONORS": "字一色",
        "SMALL_DRAGONS": "小三元",
        "BIG_DRAGONS": "大三元",
        "SMALL_WINDS": "小四喜",
        "BIG_WINDS": "大四喜",
        "THREE_CONCEALED": "三暗刻",
        "FOUR_CONCEALED": "四暗刻",
        "FIVE_CONCEALED": "五暗刻",
        "SUPPLEMENT_WIN": "槓上開花",
        "ROB_KONG": "搶槓",
        "LAST_DRAW": "海底撈月",
        "LAST_DISCARD": "河底撈魚",
        "SINGLE_WAIT": "獨聽",
    }
    var_70 = board_.Tile(id=var_69)
    var_71 = board_.tile_block(
        tile=var_70, ascii_tiles=var_70, color=complex(-1155.56, -2554.0)
    )
    assert var_71 == " \x1b[31m[1m  ]\x1b[0m"


def test_2():
    var_0 = "Cannot read terminal output mode; use --plain-Settlement differs from recomputed result-Draw source must accompany last_drawn"
    assert board_.SCORE_NAMES == {
        "CONCEALED": "門清",
        "SELF_DRAW": "自摸",
        "CONCEALED_SELF_DRAW": "門清自摸",
        "DRAGON_R": "紅中",
        "DRAGON_G": "青發",
        "DRAGON_B": "白板",
        "SEAT_WIND": "門風",
        "ROUND_WIND": "圈風",
        "SEAT_FLOWER": "門花",
        "FLOWER_SET": "花槓",
        "ALL_TRIPLETS": "碰碰胡",
        "MIXED_SUIT": "混一色",
        "PURE_SUIT": "清一色",
        "ALL_HONORS": "字一色",
        "SMALL_DRAGONS": "小三元",
        "BIG_DRAGONS": "大三元",
        "SMALL_WINDS": "小四喜",
        "BIG_WINDS": "大四喜",
        "THREE_CONCEALED": "三暗刻",
        "FOUR_CONCEALED": "四暗刻",
        "FIVE_CONCEALED": "五暗刻",
        "SUPPLEMENT_WIN": "槓上開花",
        "ROB_KONG": "搶槓",
        "LAST_DRAW": "海底撈月",
        "LAST_DISCARD": "河底撈魚",
        "SINGLE_WAIT": "獨聽",
    }
    var_1 = board_.display_width(text=var_0)
    assert var_1 == 125
    var_2 = board_.Tile(id=var_1)
    var_28 = True
    var_29 = board_.tile_block(
        tile=var_2, ascii_tiles=False, color=var_28, marked=False
    )
    assert var_29 == " \x1b[33m[中  ]\x1b[0m"


def test_3():
    var_66 = board_.display_width(text="qy'p}S<3,<CCxFY")
    assert var_66 == 15
    assert board_.SCORE_NAMES == {
        "CONCEALED": "門清",
        "SELF_DRAW": "自摸",
        "CONCEALED_SELF_DRAW": "門清自摸",
        "DRAGON_R": "紅中",
        "DRAGON_G": "青發",
        "DRAGON_B": "白板",
        "SEAT_WIND": "門風",
        "ROUND_WIND": "圈風",
        "SEAT_FLOWER": "門花",
        "FLOWER_SET": "花槓",
        "ALL_TRIPLETS": "碰碰胡",
        "MIXED_SUIT": "混一色",
        "PURE_SUIT": "清一色",
        "ALL_HONORS": "字一色",
        "SMALL_DRAGONS": "小三元",
        "BIG_DRAGONS": "大三元",
        "SMALL_WINDS": "小四喜",
        "BIG_WINDS": "大四喜",
        "THREE_CONCEALED": "三暗刻",
        "FOUR_CONCEALED": "四暗刻",
        "FIVE_CONCEALED": "五暗刻",
        "SUPPLEMENT_WIN": "槓上開花",
        "ROB_KONG": "搶槓",
        "LAST_DRAW": "海底撈月",
        "LAST_DISCARD": "河底撈魚",
        "SINGLE_WAIT": "獨聽",
    }
    var_69 = board_.Tile(id=var_66)
    var_70 = False
    var_71 = board_.tile_block(tile=var_69, ascii_tiles=var_70, color={466})
    assert var_71 == " \x1b[31m[四萬]\x1b[0m"


def test_4():
    var_65 = board_.display_width(
        text="win_sourceQ--plainQ登記回應Q\x1b[?25l\x1b[2J\x1b[H"
    )
    assert var_65 == 41
    assert board_.SCORE_NAMES == {
        "CONCEALED": "門清",
        "SELF_DRAW": "自摸",
        "CONCEALED_SELF_DRAW": "門清自摸",
        "DRAGON_R": "紅中",
        "DRAGON_G": "青發",
        "DRAGON_B": "白板",
        "SEAT_WIND": "門風",
        "ROUND_WIND": "圈風",
        "SEAT_FLOWER": "門花",
        "FLOWER_SET": "花槓",
        "ALL_TRIPLETS": "碰碰胡",
        "MIXED_SUIT": "混一色",
        "PURE_SUIT": "清一色",
        "ALL_HONORS": "字一色",
        "SMALL_DRAGONS": "小三元",
        "BIG_DRAGONS": "大三元",
        "SMALL_WINDS": "小四喜",
        "BIG_WINDS": "大四喜",
        "THREE_CONCEALED": "三暗刻",
        "FOUR_CONCEALED": "四暗刻",
        "FIVE_CONCEALED": "五暗刻",
        "SUPPLEMENT_WIN": "槓上開花",
        "ROB_KONG": "搶槓",
        "LAST_DRAW": "海底撈月",
        "LAST_DISCARD": "河底撈魚",
        "SINGLE_WAIT": "獨聽",
    }


def test_5():
    var_37 = board_.display_width(text="Z5_.c%'BS\\")
    assert var_37 == 10
    assert board_.SCORE_NAMES == {
        "CONCEALED": "門清",
        "SELF_DRAW": "自摸",
        "CONCEALED_SELF_DRAW": "門清自摸",
        "DRAGON_R": "紅中",
        "DRAGON_G": "青發",
        "DRAGON_B": "白板",
        "SEAT_WIND": "門風",
        "ROUND_WIND": "圈風",
        "SEAT_FLOWER": "門花",
        "FLOWER_SET": "花槓",
        "ALL_TRIPLETS": "碰碰胡",
        "MIXED_SUIT": "混一色",
        "PURE_SUIT": "清一色",
        "ALL_HONORS": "字一色",
        "SMALL_DRAGONS": "小三元",
        "BIG_DRAGONS": "大三元",
        "SMALL_WINDS": "小四喜",
        "BIG_WINDS": "大四喜",
        "THREE_CONCEALED": "三暗刻",
        "FOUR_CONCEALED": "四暗刻",
        "FIVE_CONCEALED": "五暗刻",
        "SUPPLEMENT_WIN": "槓上開花",
        "ROB_KONG": "搶槓",
        "LAST_DRAW": "海底撈月",
        "LAST_DISCARD": "河底撈魚",
        "SINGLE_WAIT": "獨聽",
    }
    var_38 = board_.Tile(id=var_37)
    var_39 = False
    var_40 = board_.tile_block(tile=var_38, ascii_tiles=var_37, color=var_39)
    assert var_40 == " [3m  ]"


def test_6():
    var_36 = board_.display_width(text="oHWw^ep\x0c?T]r\n][")
    assert var_36 == 15
    assert board_.SCORE_NAMES == {
        "CONCEALED": "門清",
        "SELF_DRAW": "自摸",
        "CONCEALED_SELF_DRAW": "門清自摸",
        "DRAGON_R": "紅中",
        "DRAGON_G": "青發",
        "DRAGON_B": "白板",
        "SEAT_WIND": "門風",
        "ROUND_WIND": "圈風",
        "SEAT_FLOWER": "門花",
        "FLOWER_SET": "花槓",
        "ALL_TRIPLETS": "碰碰胡",
        "MIXED_SUIT": "混一色",
        "PURE_SUIT": "清一色",
        "ALL_HONORS": "字一色",
        "SMALL_DRAGONS": "小三元",
        "BIG_DRAGONS": "大三元",
        "SMALL_WINDS": "小四喜",
        "BIG_WINDS": "大四喜",
        "THREE_CONCEALED": "三暗刻",
        "FOUR_CONCEALED": "四暗刻",
        "FIVE_CONCEALED": "五暗刻",
        "SUPPLEMENT_WIN": "槓上開花",
        "ROB_KONG": "搶槓",
        "LAST_DRAW": "海底撈月",
        "LAST_DISCARD": "河底撈魚",
        "SINGLE_WAIT": "獨聽",
    }
    var_37 = board_.Tile(id=var_36)
    var_38 = lambda *args, **kwargs: True
    var_39 = board_.tile_block(
        tile=var_37, ascii_tiles=var_38, color=var_36, marked=var_36
    )
    assert var_39 == "*\x1b[1;31m[4m  ]\x1b[0m"


@pytest.mark.xfail(strict=True)
def test_7():
    var_36 = board_.display_width(
        text="End of recorded prefix (game unfinished).\x03KONG_CONCEALED\x03RESPONSE"
    )
    assert var_36 == 65
    assert board_.SCORE_NAMES == {
        "CONCEALED": "門清",
        "SELF_DRAW": "自摸",
        "CONCEALED_SELF_DRAW": "門清自摸",
        "DRAGON_R": "紅中",
        "DRAGON_G": "青發",
        "DRAGON_B": "白板",
        "SEAT_WIND": "門風",
        "ROUND_WIND": "圈風",
        "SEAT_FLOWER": "門花",
        "FLOWER_SET": "花槓",
        "ALL_TRIPLETS": "碰碰胡",
        "MIXED_SUIT": "混一色",
        "PURE_SUIT": "清一色",
        "ALL_HONORS": "字一色",
        "SMALL_DRAGONS": "小三元",
        "BIG_DRAGONS": "大三元",
        "SMALL_WINDS": "小四喜",
        "BIG_WINDS": "大四喜",
        "THREE_CONCEALED": "三暗刻",
        "FOUR_CONCEALED": "四暗刻",
        "FIVE_CONCEALED": "五暗刻",
        "SUPPLEMENT_WIN": "槓上開花",
        "ROB_KONG": "搶槓",
        "LAST_DRAW": "海底撈月",
        "LAST_DISCARD": "河底撈魚",
        "SINGLE_WAIT": "獨聽",
    }
    var_37 = board_.ReplayFrame(
        index=var_36, state=var_36, action=var_36, events=(False,)
    )
    var_38 = board_.Action(kind=var_37, player=())
    var_39 = (var_38, var_37, var_37)
    var_40 = board_.SimulationResult(
        initial_state=var_37, final_state=var_37, actions=var_39
    )
    var_41 = False
    var_42 = 1187
    var_43 = -218
    var_44 = True
    board_.render_board(
        frame=var_37,
        result=var_40,
        recent=complex(458.187, -57.5),
        primary=var_39,
        speed=None,
        paused=var_41,
        visible_index=var_42,
        visible_total=var_41,
        draws=var_36,
        discards=var_43,
        columns=2060,
        ascii_tiles=var_44,
        color=var_44,
        result_lines=complex(-1597.79, -1815.23955),
    )


@pytest.mark.xfail(strict=True)
def test_8():
    var_36 = board_.display_width(text=" @I<L-5eR=M")
    assert var_36 == 11
    assert board_.SCORE_NAMES == {
        "CONCEALED": "門清",
        "SELF_DRAW": "自摸",
        "CONCEALED_SELF_DRAW": "門清自摸",
        "DRAGON_R": "紅中",
        "DRAGON_G": "青發",
        "DRAGON_B": "白板",
        "SEAT_WIND": "門風",
        "ROUND_WIND": "圈風",
        "SEAT_FLOWER": "門花",
        "FLOWER_SET": "花槓",
        "ALL_TRIPLETS": "碰碰胡",
        "MIXED_SUIT": "混一色",
        "PURE_SUIT": "清一色",
        "ALL_HONORS": "字一色",
        "SMALL_DRAGONS": "小三元",
        "BIG_DRAGONS": "大三元",
        "SMALL_WINDS": "小四喜",
        "BIG_WINDS": "大四喜",
        "THREE_CONCEALED": "三暗刻",
        "FOUR_CONCEALED": "四暗刻",
        "FIVE_CONCEALED": "五暗刻",
        "SUPPLEMENT_WIN": "槓上開花",
        "ROB_KONG": "搶槓",
        "LAST_DRAW": "海底撈月",
        "LAST_DISCARD": "河底撈魚",
        "SINGLE_WAIT": "獨聽",
    }
    var_37 = board_.ReplayFrame(
        index=var_36, state=var_36, action=var_36, events=(False,)
    )
    var_38 = board_.Action(kind=var_37, player=())
    var_39 = (var_38, var_37)
    var_40 = board_.SimulationResult(
        initial_state=var_37, final_state=var_37, actions=var_39
    )
    var_41 = True
    var_42 = 1187
    var_43 = -218
    var_44 = False
    board_.render_board(
        frame=var_37,
        result=var_40,
        recent=complex(458.187, -57.5),
        primary=var_39,
        speed=None,
        paused=var_41,
        visible_index=var_42,
        visible_total=var_41,
        draws=var_36,
        discards=var_43,
        columns=2060,
        ascii_tiles=var_44,
        color=var_44,
        result_lines=complex(-1597.79, -1815.23955),
    )
