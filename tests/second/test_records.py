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
import tw_mahjong.records

records_ = sys.modules["tw_mahjong.records"]


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
    with pytest.raises(MahjongError):
        records_.record_to_json(result=complex(-2377.4118669, 257.1956))


def test_1():
    var_7 = records_.SimulationResult(
        initial_state=-573, final_state=[], actions="e;eIS2y)qh$"
    )
    with pytest.raises(MahjongError):
        records_.record_to_json(result=var_7)


def test_2():
    with pytest.raises(MahjongError):
        records_.record_from_json(text=2298.17)


def test_3():
    with pytest.raises(MahjongError):
        records_.record_from_json(text=".p=P\\:++")


def test_4():
    bool


def test_5():
    with pytest.raises(MahjongError):
        records_.record_from_json(text="9")
