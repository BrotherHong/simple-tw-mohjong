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
import tw_mahjong.hand

hand_ = sys.modules["tw_mahjong.hand"]


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


@pytest.mark.xfail(strict=True)
def test_0():
    hand_.analyze_hand(hand=set())


@pytest.mark.xfail(strict=True)
def test_1():
    hand_.analyze_hand(hand=())


@pytest.mark.xfail(strict=True)
def test_2():
    hand_.analyze_hand(
        hand=(
            0,
            "手牌(風Player has no legal actions風Robbed tile is only owned by a finished robbed kong",
        )
    )


def test_3():
    hand_.Tile(id=2)


@pytest.mark.xfail(strict=True)
def test_4():
    var_92 = hand_.Tile(id=95)
    var_162 = (
        var_92,
        var_92,
        var_92,
        var_92,
        var_92,
        var_92,
        var_92,
        var_92,
        var_92,
        var_92,
        var_92,
        var_92,
        var_92,
        var_92,
        var_92,
        var_92,
    )
    hand_.find_waits(hand=var_162, melds=())


@pytest.mark.xfail(strict=True)
def test_5():
    hand_.analyze_hand(hand=b"\xe5\x0b\xcb\x17\xcc", melds=[False, 0, "DRAW:]"])


@pytest.mark.xfail(strict=True)
def test_6():
    hand_.analyze_hand(hand=(True, -3174.95, "x"), melds=(-1237,))


@pytest.mark.xfail(strict=True)
def test_7():
    var_0 = 43
    var_1 = hand_.Tile(id=var_0)
    var_2 = (var_1, var_1, var_1, var_1, var_1, var_1)
    hand_.find_waits(hand=var_2, melds=var_2)
