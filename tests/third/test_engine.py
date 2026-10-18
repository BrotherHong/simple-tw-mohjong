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
    with pytest.raises(MahjongError):
        engine_.validate_state(state=None)


def test_1():
    with pytest.raises(MahjongError):
        engine_.create_game(
            dealer=1, tile_order=('RtJ7@=M#y>jcp?["8',), rng=True, rules_version=17
        )


@pytest.mark.xfail(strict=True)
def test_2():
    engine_.legal_actions(state=None, player=-988)


def test_3():
    engine_.GameState(
        wall=(3, False, False),
        players={},
        discards="zci~(\r9,<s%G#!",
        dealer=-1994,
        turn=(4294967295, 1139, "wC&N^Qn:~8ag"),
        phase=3032.02,
        last_drawn="dvtLWE^.E",
        robbed_tile=[],
    )


def test_4():
    with pytest.raises(MahjongError):
        engine_.create_game(tile_order={True}, round_wind=-2946)


def test_5():
    with pytest.raises(MahjongError):
        engine_.create_game(round_wind=-116.23)


def test_6():
    with pytest.raises(MahjongError):
        engine_.create_game()


def test_7():
    with pytest.raises(MahjongError):
        engine_.create_game(rng="O#xm:g,_!eW")


def test_8():
    with pytest.raises(MahjongError):
        engine_.create_game(
            rules_version={-547.78, -1, "@X("},
            round_wind=b"C4\xca\x03\n\xa6R\x02C\x91\x8e\x9e\xb9",
        )


def test_9():
    with pytest.raises(MahjongError):
        engine_.create_game(tile_order=b"\xe3f,n\x06\x18")


def test_10():
    with pytest.raises(MahjongError):
        engine_.create_game(
            tile_order={"KONG_DECLARED": -1002}, rng=None, round_wind=2079
        )


def test_11():
    var_51 = engine_.GameState(
        wall="INVALID_STATEmINVALID_STATEmversion",
        players=-2901.02,
        discards=1575,
        dealer=[-1520, "胡牌"],
        turn=set(),
        phase=429,
        win_source=complex(1813.84, -2525.5926313),
        draw_source=False,
        last_discard_last=169,
    )
    with pytest.raises(MahjongError):
        engine_.validate_state(state=var_51)


def test_12():
    with pytest.raises(MahjongError):
        engine_.create_game(rules_version=1)


def test_13():
    with pytest.raises(MahjongError):
        engine_.create_game(tile_order=())
