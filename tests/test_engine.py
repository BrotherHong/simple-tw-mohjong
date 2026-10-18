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
import tw_mahjong.engine

engine_ = sys.modules["tw_mahjong.engine"]


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
    with pytest.raises(MahjongError):
        engine_.apply_action(state=None, action=None)


def test_1():
    var_25 = engine_.GameState(
        wall=(True,),
        players=complex(-1336.124, 2058.8387088),
        discards="space pause | n/Enter step | +/- speed | q quit",
        dealer=True,
        turn=None,
        phase=(),
        last_discard_last=1,
    )
    with pytest.raises(MahjongError):
        engine_.validate_state(state=var_25)


def test_2():
    with pytest.raises(MahjongError):
        engine_.create_game(rules_version=None)


def test_3():
    with pytest.raises(MahjongError):
        engine_.create_game(rng=0.0)


@pytest.mark.xfail(strict=True)
def test_4():
    engine_.legal_actions(state=None, player=1109)


def test_5():
    with pytest.raises(MahjongError):
        engine_.create_game(round_wind={"萬筒索": 175})


def test_6():
    with pytest.raises(MahjongError):
        engine_.create_game(rng=None, round_wind=1)


def test_7():
    with pytest.raises(MahjongError):
        engine_.create_game(tile_order=set())


def test_8():
    with pytest.raises(MahjongError):
        engine_.create_game(rng=30, rules_version=326)


def test_9():
    with pytest.raises(MahjongError):
        engine_.create_game()


def test_10():
    with pytest.raises(MahjongError):
        engine_.create_game(rng=(False, 1710.05, -777.57), round_wind=884)


def test_11():
    with pytest.raises(MahjongError):
        engine_.create_game(tile_order=())


def test_12():
    with pytest.raises(MahjongError):
        engine_.create_game(rules_version=1)
