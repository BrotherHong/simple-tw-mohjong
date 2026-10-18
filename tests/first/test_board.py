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
        x = 17
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
    _pynguin_random.seed(17)
    _pynguin_instances = getattr(
        _pynguin_random.Random.seed, "__pynguin_instances__", None
    )
    if _pynguin_instances is not None:
        for _inst in list(_pynguin_instances):
            _inst.seed(17)
    yield
    _pynguin_random.Random.seed = _pynguin_orig_seed


def test_0():
    board_.display_width(text="m3Yy B/%'VTvB6+{2")
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
    var_63 = board_.display_width(text="9C-ZZ}Z>QB5@@&y-J")
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
    var_70 = board_.Tile(id=var_63)
    var_71 = board_.tile_block(tile=var_70, ascii_tiles=False, color=False)
    assert var_71 == " [五萬]"


def test_2():
    var_63 = board_.display_width(text="9C-ZZ}Z>QB5@@&y-J")
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
    var_70 = board_.Tile(id=var_63)
    board_.tile_block(tile=var_70, ascii_tiles=var_70, color=-1035.61)


def test_3():
    var_88 = board_.display_width(text="aU>Z ")
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
    var_89 = board_.Tile(id=var_88)
    var_90 = board_.tile_block(
        tile=var_89, ascii_tiles=var_89, color=var_89, marked=True
    )
    assert var_90 == "*\x1b[1;31m[2m  ]\x1b[0m"


def test_4():
    var_6 = board_.display_width(text="加槓P播放中PFlowers:PInvalid winning discard")
    assert var_6 == 44
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


@pytest.mark.xfail(strict=True)
def test_5():
    var_89 = -2305
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
    var_90 = board_.ReplayFrame(index=502, state=None, action=[var_89], events=(2,))
    var_97 = ()
    var_98 = board_.SimulationResult(
        initial_state=None, final_state=None, actions=(var_90, True, var_90)
    )
    var_99 = False
    board_.render_board(
        frame=var_90,
        result=var_98,
        recent=(),
        primary={"discards": True, "Disable tile colors": var_90},
        speed=-1645.48,
        paused=var_99,
        visible_index=var_89,
        visible_total=768,
        draws=-310,
        discards=var_99,
        columns=var_89,
        ascii_tiles=var_99,
        color=False,
        result_lines=var_97,
    )


@pytest.mark.xfail(strict=True)
def test_6():
    var_89 = 3
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
    var_90 = board_.ReplayFrame(index=502, state=None, action=[var_89], events=(2,))
    var_97 = (False,)
    var_98 = board_.SimulationResult(
        initial_state=var_89, final_state=None, actions=var_97
    )
    var_102 = True
    board_.render_board(
        frame=var_90,
        result=var_98,
        recent=(),
        primary={"discards": True, "Disable tile colors": var_90},
        speed=-1645.48,
        paused=var_102,
        visible_index=var_89,
        visible_total=768,
        draws=-310,
        discards=var_102,
        columns=var_89,
        ascii_tiles=var_102,
        color=False,
        result_lines=var_97,
    )


def test_7():
    var_63 = board_.display_width(
        text="Expected a tuple of four callable policiesGUnsupported rules versionGExpected random.RandomG一二三四五六七八九"
    )
    assert var_63 == 110
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
    var_93 = board_.Tile(id=var_63)
    board_.tile_block(tile=var_93, ascii_tiles=False, color=True)


def test_8():
    var_89 = 136
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
    var_101 = board_.Tile(id=var_89)
    var_102 = board_.tile_block(tile=var_101, ascii_tiles=False, color=True)
    assert var_102 == " \x1b[95m[春花]\x1b[0m"
