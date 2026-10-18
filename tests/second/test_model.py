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
import tw_mahjong.model

model_ = sys.modules["tw_mahjong.model"]


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
    model_.full_deck()


@pytest.mark.xfail(strict=True)
def test_1():
    var_62 = model_.is_sequence(kinds=(True, False, -340.01))
    assert var_62 is False
    var_104 = 1
    var_105 = model_.PendingKong
    model_.Payment(payer=var_104, payee=var_104, tai=var_105, amount=var_105)
    model_.Tile(id=None)


@pytest.mark.xfail(strict=True)
def test_2():
    model_.Meld(kind=None, tiles=(), source=b"}", claimed_tile=[])


def test_3():
    with pytest.raises(MahjongError):
        model_.tile_kind(code=False)


@pytest.mark.xfail(strict=True)
def test_4():
    model_.Tile(id=1042)


@pytest.mark.xfail(strict=True)
def test_5():
    model_.SettlementConfig(
        tai_value={
            "Invalid winning discard": "Q\x0cH]/6=?G8Gc",
            "Duplicate physical tile across hand and melds": -491.92,
        }
    )


@pytest.mark.xfail(strict=True)
def test_6():
    var_66 = 367
    var_100 = model_.MeldKind.KONG_ADDED
    model_.Meld(
        kind=var_100,
        tiles=True,
        source=var_66,
        claimed_tile=(1, "Invalid player snapshot"),
    )


@pytest.mark.xfail(strict=True)
def test_7():
    var_24 = -1468
    model_.SettlementConfig(base=var_24, tai_value=var_24)


@pytest.mark.xfail(strict=True)
def test_8():
    model_.Tile(id=-486)


def test_9():
    var_60 = model_.is_sequence(kinds={})
    assert var_60 is False


@pytest.mark.xfail(strict=True)
def test_10():
    var_66 = model_.MeldKind.KONG_EXPOSED
    model_.Meld(kind=var_66, tiles=(), source=var_66, claimed_tile=var_66)


@pytest.mark.xfail(strict=True)
def test_11():
    model_.Meld(
        kind=None, tiles=(False, False, True), source="B>?i\n\x0bsv", claimed_tile={}
    )


def test_12():
    var_62 = model_.is_sequence(kinds=(1350.6, True, "sx.aQ_"))
    assert var_62 is False


@pytest.mark.xfail(strict=True)
def test_13():
    var_63 = model_.Payment
    var_62 = model_.is_sequence(
        kinds=(
            315.26,
            "Display àspace pause | n/Enter step | +/- speed | q quit | * drawn/discardedàDISCARD",
            var_63,
        )
    )
    assert var_62 is False
    var_95 = -753
    model_.SettlementConfig(tai_value=var_95)


@pytest.mark.xfail(strict=True)
def test_14():
    model_.SettlementConfig(base=[])


def test_15():
    with pytest.raises(MahjongError):
        model_.check_player(player=None)


def test_16():
    var_66 = 367
    with pytest.raises(MahjongError):
        model_.check_player(player=var_66)


def test_17():
    with pytest.raises(MahjongError):
        model_.tile_kind(code="FINISHED")


def test_18():
    var_66 = -93
    with pytest.raises(MahjongError):
        model_.check_player(player=var_66)


def test_19():
    var_62 = model_.is_sequence(kinds=(True, False, -340.01))
    assert var_62 is False


@pytest.mark.xfail(strict=True)
def test_20():
    var_66 = 3
    model_.check_player(player=var_66)
    model_.Meld(
        kind=var_66,
        tiles=(False, var_66, 'OI (2"[n27*>[2JW'),
        source=var_66,
        claimed_tile=var_66,
    )


@pytest.mark.xfail(strict=True)
def test_21():
    var_62 = model_.is_sequence(kinds=(-2088.78, "{SbF=v\x0cIr", 315.26))
    assert var_62 is False
    var_111 = model_.MeldKind.CHI
    model_.Meld(
        kind=None, tiles=(1350.6, var_62, var_111), source=var_62, claimed_tile=var_111
    )


def test_22():
    var_62 = model_.is_sequence(kinds=(False, False, True))
    assert var_62 is False


def test_23():
    var_59 = model_.tile_kind(code="E")
    assert var_59 == 27
    var_77 = bool
    var_78 = model_.ScoreItem(code=var_77, tai=var_77)
    var_79 = (var_78, 3450)
    model_.ScoreResult(
        tai=var_59, items=var_79, decomposition=var_79, winning_group=None
    )
