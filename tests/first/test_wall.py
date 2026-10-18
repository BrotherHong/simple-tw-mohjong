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
from tw_mahjong.model import MahjongError
import sys
import tw_mahjong.wall

wall_ = sys.modules["tw_mahjong.wall"]
from tw_mahjong.wall import Wall


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
    wall_.Wall(tiles=2216)


def test_1():
    var_28 = wall_.Wall(tiles=())
    assert var_28 == Wall(tiles=())


@pytest.mark.xfail(strict=True)
def test_2():
    var_0 = (True, False)
    wall_.Wall(tiles=var_0)


def test_3():
    var_48 = wall_.Wall(tiles=())
    assert var_48 == Wall(tiles=())
    with pytest.raises(MahjongError):
        var_48.draw_back()


def test_4():
    var_48 = wall_.Wall(tiles=())
    assert var_48 == Wall(tiles=())
    with pytest.raises(MahjongError):
        var_48.draw_front()
