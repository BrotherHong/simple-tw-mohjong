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
import tw_mahjong.model

model_ = sys.modules["tw_mahjong.model"]
from tw_mahjong.model import SettlementConfig, Tile


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
    var_28 = model_.SettlementConfig(tai_value=3)
    assert var_28 == SettlementConfig(base=100, tai_value=3)


def test_1():
    with pytest.raises(MahjongError):
        model_.tile_kind(code="-\\C")


@pytest.mark.xfail(strict=True)
def test_2():
    model_.Tile(id=None)


@pytest.mark.xfail(strict=True)
def test_3():
    model_.Meld(
        kind={
            "SEAT_WIND": 639,
            "End of recorded prefix (game unfinished).": "O,",
            "等待搶槓": 351.08,
        },
        tiles=complex(-2950.0915, 2256.0),
        source=None,
        claimed_tile=None,
    )


@pytest.mark.xfail(strict=True)
def test_4():
    model_.Meld(
        kind=None,
        tiles=("c'AHgV`a%N\x0cC\"", True, 756),
        source={
            "Hand(": " discards \rInvalid winning discard\r起手盤面\r  melds:",
            "Meld must be a sequence or triplet": 3982.93,
        },
        claimed_tile="SMALL_WINDS.四暗刻.A meld needs three or four ordinary physical tiles.Concealed kong has no external source",
    )


@pytest.mark.xfail(strict=True)
def test_5():
    model_.SettlementConfig(tai_value=-1028)


def test_6():
    model_.Tile(id=121)


@pytest.mark.xfail(strict=True)
def test_7():
    var_46 = model_.MeldKind.KONG_ADDED
    var_47 = lambda *args, **kwargs: "VN]1%\x0bkQ"
    var_48 = model_.full_deck()
    var_49 = var_48[0]
    assert var_49 == Tile(id=0)
    var_50 = var_48[1]
    model_.Meld(kind=var_46, tiles=var_48, source=var_50, claimed_tile=var_47)


@pytest.mark.xfail(strict=True)
def test_8():
    model_.Tile(id=-1283)


@pytest.mark.xfail(strict=True)
def test_9():
    model_.Tile(id=3664)


def test_10():
    var_0 = "R"
    var_1 = model_.tile_kind(code=var_0)
    assert var_1 == 31
    var_2 = -109
    model_.ScoreItem(code=var_0, tai=var_2)


@pytest.mark.xfail(strict=True)
def test_11():
    model_.Meld(
        kind=None,
        tiles=(976.8, 0.02),
        source={
            "Invalid winning discard": "_^$J#>vDv)_L",
            "Invalid winning discard": -2935.08,
            "PLAYING": "u9=yTFXWO",
        },
        claimed_tile=2325,
    )


def test_12():
    with pytest.raises(MahjongError):
        model_.tile_kind(code=b"6uhW{\xa8d=Sq\xb4")


@pytest.mark.xfail(strict=True)
def test_13():
    model_.SettlementConfig(base=-36)


@pytest.mark.xfail(strict=True)
def test_14():
    model_.SettlementConfig(base=b"\r6\xd9\xfb3\xf1")


def test_15():
    with pytest.raises(MahjongError):
        model_.check_player(player=None)


def test_16():
    model_.is_sequence(kinds=[])


@pytest.mark.xfail(strict=True)
def test_17():
    model_.SettlementConfig(tai_value=False)


def test_18():
    with pytest.raises(MahjongError):
        model_.check_player(player=616)


def test_19():
    var_48 = lambda *args, **kwargs: [-135, False]
    var_53 = (False, var_48, True)
    var_54 = model_.is_sequence(kinds=var_53)
    assert var_54 is False


def test_20():
    var_48 = lambda *args, **kwargs: [-135, False]
    var_52 = 1219
    var_53 = (var_52, var_48, var_48)
    var_54 = model_.is_sequence(kinds=var_53)
    assert var_54 is False


@pytest.mark.xfail(strict=True)
def test_21():
    var_48 = lambda *args, **kwargs: [-135, False]
    var_52 = -105
    var_53 = (var_52, var_48, var_48)
    var_54 = model_.is_sequence(kinds=var_53)
    assert var_54 is False
    model_.PlayerState(melds="Expected JSON text\n\n\nphase\nplayers")
    var_59 = -1441
    model_.Tile(id=var_59)


def test_22():
    var_0 = -1757
    with pytest.raises(MahjongError):
        model_.check_player(player=var_0)


def test_23():
    var_48 = lambda *args, **kwargs: [-135, False]
    var_89 = (False, var_48, -488)
    model_.is_sequence(kinds=var_89)
