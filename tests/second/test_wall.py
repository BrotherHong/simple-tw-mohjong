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
    wall_.Wall(tiles=complex(-1706.56362, -2024.5527))


def test_1():
    var_1 = wall_.Wall(tiles=())
    assert var_1 == Wall(tiles=())


@pytest.mark.xfail(strict=True)
def test_2():
    wall_.Wall(tiles=("final_state", 0.0, True))


def test_3():
    var_47 = wall_.Wall(tiles=())
    assert var_47 == Wall(tiles=())
    with pytest.raises(MahjongError):
        var_47.draw_front()


def test_4():
    var_1 = wall_.Wall(tiles=())
    assert var_1 == Wall(tiles=())
    with pytest.raises(MahjongError):
        var_1.draw_back()
