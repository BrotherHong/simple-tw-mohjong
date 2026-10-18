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
import tw_mahjong.hand

hand_ = sys.modules["tw_mahjong.hand"]


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


@pytest.mark.xfail(strict=True)
def test_0():
    hand_.analyze_hand(hand=0.25, melds=[])


@pytest.mark.xfail(strict=True)
def test_1():
    hand_.analyze_hand(hand={-445.43})


@pytest.mark.xfail(strict=True)
def test_2():
    hand_.analyze_hand(hand=("Claimed tile must belong to meld", -2328))


@pytest.mark.xfail(strict=True)
def test_3():
    var_61 = hand_.Tile(id=2)
    var_62 = (var_61, var_61)
    hand_.analyze_hand(hand=var_62)


@pytest.mark.xfail(strict=True)
def test_4():
    hand_.analyze_hand(hand=())


@pytest.mark.xfail(strict=True)
def test_5():
    hand_.analyze_hand(hand=(True, False), melds=(False, True, "KONG_ADDED"))


@pytest.mark.xfail(strict=True)
def test_6():
    var_37 = hand_.Tile(id=4)
    var_48 = (var_37, var_37, var_37, var_37, var_37, var_37)
    hand_.find_waits(hand=(True,), melds=var_48)


@pytest.mark.xfail(strict=True)
def test_7():
    var_37 = hand_.Tile(id=3)
    var_282 = (
        var_37,
        var_37,
        var_37,
        var_37,
        var_37,
        var_37,
        var_37,
        var_37,
        var_37,
        var_37,
        var_37,
        var_37,
        var_37,
        var_37,
        var_37,
        var_37,
    )
    hand_.find_waits(hand=var_282)
