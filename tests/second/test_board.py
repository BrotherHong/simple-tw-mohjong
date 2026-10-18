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
        x = 42
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
    _pynguin_random.seed(42)
    _pynguin_instances = getattr(
        _pynguin_random.Random.seed, "__pynguin_instances__", None
    )
    if _pynguin_instances is not None:
        for _inst in list(_pynguin_instances):
            _inst.seed(42)
    yield
    _pynguin_random.Random.seed = _pynguin_orig_seed


def test_0():
    var_0 = board_.display_width(text="播放 ,RESPONSE,摸牌")
    assert var_0 == 19
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
    var_68 = board_.Tile(id=94)
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
    var_69 = board_.tile_block(tile=var_68, ascii_tiles=False, color=False)
    assert var_69 == " [六索]"


def test_2():
    var_0 = board_.display_width(text="?e")
    assert var_0 == 2
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
    var_68 = board_.Tile(id=var_0)
    var_69 = board_.tile_block(tile=var_68, ascii_tiles=18, color=var_68, marked=552.71)
    assert var_69 == "*\x1b[1;31m[1m  ]\x1b[0m"


def test_3():
    var_69 = board_.display_width(text="牌牆耗盡,Disable tile colors")
    assert var_69 == 28
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
        tile=var_70, ascii_tiles=2760.64, color=complex(494.98, 706.3)
    )
    assert var_71 == " \x1b[31m[8m  ]\x1b[0m"


@pytest.mark.xfail(strict=True)
def test_4():
    var_70 = lambda *args, **kwargs: "Expected at most five melds,\x03,紅中,replay"
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
    var_71 = board_.ReplayFrame(index=1436, state=None, action=[], events=(0.25,))
    var_74 = (var_71, var_70)
    var_98 = board_.SimulationResult(
        initial_state=None, final_state=var_74, actions=var_74
    )
    var_99 = 2917
    var_100 = True
    board_.render_board(
        frame=var_71,
        result=var_98,
        recent=var_74,
        primary=var_74,
        speed=-2340.58,
        paused=False,
        visible_index=var_99,
        visible_total=var_100,
        draws=var_100,
        discards=var_99,
        columns=var_99,
        ascii_tiles=var_100,
        color=var_100,
        result_lines=var_74,
    )


@pytest.mark.xfail(strict=True)
def test_5():
    var_70 = lambda *args, **kwargs: "Expected at most five melds,\x03,紅中,replay"
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
    var_71 = board_.ReplayFrame(index=1436, state=None, action=[], events=(0.25,))
    var_74 = (var_71, var_70)
    var_98 = board_.SimulationResult(
        initial_state=None, final_state=var_74, actions=var_74
    )
    var_99 = 2917
    var_103 = True
    board_.render_board(
        frame=var_71,
        result=var_98,
        recent=var_74,
        primary=var_99,
        speed=0.02,
        paused=False,
        visible_index=var_99,
        visible_total=4294967295,
        draws=var_99,
        discards=var_99,
        columns=var_103,
        ascii_tiles=False,
        color=True,
        result_lines=var_74,
    )


def test_6():
    var_0 = board_.display_width(
        text=" declared,Wrong concealed tile count for meld count,一二三四五六七八九,v1 cannot contain settlement settings"
    )
    assert var_0 == 108
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
    var_78 = board_.Tile(id=var_0)
    var_79 = True
    var_80 = board_.tile_block(tile=var_78, ascii_tiles=False, color=var_79)
    assert var_80 == " \x1b[33m[東  ]\x1b[0m"


@pytest.mark.xfail(strict=True)
def test_7():
    var_74 = 140
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
    var_86 = board_.Tile(id=var_74)
    var_87 = ["x}1n46z<", var_86]
    var_88 = board_.tile_block(tile=var_86, ascii_tiles=(), color=var_87)
    assert var_88 == " \x1b[95m[梅花]\x1b[0m"
    var_89 = "z"
    var_90 = object
    var_91 = board_.Action(kind=var_88, player=var_86, tiles=var_90)
    var_92 = var_91.__hash__()
    var_93 = board_.ReplayFrame(
        index=var_87, state=var_92, action={}, events=(-1373.0,)
    )
    var_98 = False
    var_99 = (var_88, False)
    var_101 = -1132
    var_102 = 48
    var_103 = True
    var_104 = True
    board_.render_board(
        frame=var_93,
        result={"TvjAMs=6kM1?#", -3374.37},
        recent=var_99,
        primary=-1177,
        speed=var_88,
        paused=var_90,
        visible_index=var_101,
        visible_total=var_102,
        draws=var_89,
        discards=var_98,
        columns=var_91,
        ascii_tiles=var_103,
        color=var_104,
        result_lines=var_88,
    )
