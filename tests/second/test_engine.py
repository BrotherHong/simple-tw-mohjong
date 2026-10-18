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
import tw_mahjong.engine

engine_ = sys.modules["tw_mahjong.engine"]


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
        engine_.validate_state(state=None)


def test_1():
    with pytest.raises(MahjongError):
        engine_.create_game(
            dealer=3,
            tile_order=None,
            rng=complex(-3349.4261848, -565.83),
            round_wind=29,
        )


@pytest.mark.xfail(strict=True)
def test_2():
    engine_.legal_actions(state=b"<\x9e\xd3", player={})


def test_3():
    with pytest.raises(MahjongError):
        engine_.create_game(
            tile_order=["INVALID_STATE 補花 INVALID_STATE", 158, True],
            rng=b"\x83\x98\x81\xe2\xfe\xc7\x95r\xe6%\xe5\x1c\x15\xf9q\xf6\x05\xbb\xd6",
        )


def test_4():
    with pytest.raises(MahjongError):
        engine_.create_game(rng=-1632, round_wind=None)


def test_5():
    with pytest.raises(MahjongError):
        engine_.create_game(round_wind=2)


def test_6():
    with pytest.raises(MahjongError):
        engine_.create_game(tile_order="#LU1(m73x(5RYE", round_wind=2371)


def test_7():
    with pytest.raises(MahjongError):
        engine_.create_game(tile_order=set())


def test_8():
    var_31 = engine_.GameState(
        wall="b!6@X-d!oD[!\r",
        players=(False, "z7Gd?N(DrC]\">OQk'\n@", 0.0),
        discards=complex(-165.371183, -3083.9),
        dealer="p42Ixhsrp",
        turn=3270,
        phase=(),
        pending=False,
        win_source=2669.81,
        winning_tile={-1534.34, 3352.55},
        draw_source=complex(761.6867, -2122.79),
        last_discard_last="Replay requires a tuple of actions,INVALID_STATE",
    )
    with pytest.raises(MahjongError):
        engine_.validate_state(state=var_31)


def test_9():
    with pytest.raises(MahjongError):
        engine_.create_game(rng=True, rules_version=3, round_wind=34)


def test_10():
    with pytest.raises(MahjongError):
        engine_.create_game(rules_version=1)


def test_11():
    with pytest.raises(MahjongError):
        engine_.create_game(rules_version=[])


def test_12():
    with pytest.raises(MahjongError):
        engine_.create_game(dealer=3, tile_order=())
