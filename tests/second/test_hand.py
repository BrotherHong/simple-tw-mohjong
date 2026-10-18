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
import tw_mahjong.hand

hand_ = sys.modules["tw_mahjong.hand"]


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


@pytest.mark.xfail(strict=True)
def test_0():
    hand_.analyze_hand(hand="%\n}g:E?%O`$zd,Rk")


@pytest.mark.xfail(strict=True)
def test_1():
    hand_.analyze_hand(hand=())


@pytest.mark.xfail(strict=True)
def test_2():
    hand_.analyze_hand(hand=(" -> PINITIAL--output",))


def test_3():
    bytes


@pytest.mark.xfail(strict=True)
def test_4():
    var_20 = hand_.Tile(id=3)
    var_21 = (var_20, var_20)
    hand_.analyze_hand(hand=var_21)


@pytest.mark.xfail(strict=True)
def test_5():
    hand_.analyze_hand(hand=b"\x96", melds=True)


@pytest.mark.xfail(strict=True)
def test_6():
    hand_.analyze_hand(hand=(-1430, 1531.21, False), melds=(-2267, 987, -45))


@pytest.mark.xfail(strict=True)
def test_7():
    var_0 = 37
    var_49 = hand_.Tile(id=var_0)
    var_59 = (var_49, var_49, var_49, var_49, var_49, 2817)
    hand_.find_waits(hand=var_59, melds=var_59)


@pytest.mark.xfail(strict=True)
def test_8():
    var_153 = hand_.Tile(id=0)
    var_156 = (
        var_153,
        var_153,
        var_153,
        var_153,
        var_153,
        var_153,
        var_153,
        var_153,
        var_153,
        var_153,
        var_153,
        var_153,
        var_153,
        var_153,
        var_153,
        var_153,
    )
    hand_.find_waits(hand=var_156)
