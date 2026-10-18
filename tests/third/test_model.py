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
import tw_mahjong.model

model_ = sys.modules["tw_mahjong.model"]
from tw_mahjong.model import Tile


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
    model_.MeldKind.PENG


def test_1():
    var_48 = model_.Tile(id=102)
    assert var_48 == Tile(id=102)


@pytest.mark.xfail(strict=True)
def test_2():
    var_0 = model_.full_deck()
    var_2 = var_0[1]
    model_.Meld(
        kind=(2452, "&#.RX0D-1FQ88\nQ_W{"),
        tiles=var_0,
        source=var_2,
        claimed_tile=var_0,
    )


@pytest.mark.xfail(strict=True)
def test_3():
    model_.Meld(
        kind={998, -1249.57},
        tiles=False,
        source=set(),
        claimed_tile="FEY.I-X)Ca1()u\t.J",
    )


@pytest.mark.xfail(strict=True)
def test_4():
    model_.Meld(kind=None, tiles=(), source=["0", False, 204], claimed_tile=True)


def test_5():
    model_.MahjongError(code=[], message=())


@pytest.mark.xfail(strict=True)
def test_6():
    var_0 = model_.MeldKind.KONG_CONCEALED
    var_19 = "\rX)|=eRQK0"
    model_.Meld(
        kind=var_0,
        tiles=(0,),
        source=var_19,
        claimed_tile=("Response phase has no last draw", var_19, var_0),
    )


@pytest.mark.xfail(strict=True)
def test_7():
    model_.SettlementConfig(tai_value=1152.01)


@pytest.mark.xfail(strict=True)
def test_8():
    model_.Tile(id=942.37)


@pytest.mark.xfail(strict=True)
def test_9():
    model_.Tile(id=4180)


@pytest.mark.xfail(strict=True)
def test_10():
    model_.Tile(id=-1816)


def test_11():
    var_31 = model_.is_sequence(kinds=())
    assert var_31 is False


def test_12():
    var_51 = model_.is_sequence(kinds=(3, "1; claimed_tile 牌牆耗盡", -1104))
    assert var_51 is False


def test_13():
    with pytest.raises(MahjongError):
        model_.check_player(player=None)


@pytest.mark.xfail(strict=True)
def test_14():
    model_.SettlementConfig(base=-2496)


@pytest.mark.xfail(strict=True)
def test_15():
    model_.SettlementConfig(
        base={"Meld source does not match owner": "L#-@)DoE-Hj3p\r"}
    )


@pytest.mark.xfail(strict=True)
def test_16():
    model_.Meld(
        kind=None,
        tiles=(1096, 686.83, True),
        source=b"\xbf\xabI\x88\x7f\x80e\x80n\x0b\xde+\x05\x05\xe6hv",
        claimed_tile={
            "Non-finite JSON number: ": -532.4,
            "播放結束": True,
            "摸牌": "主要動作:",
        },
    )


def test_17():
    var_43 = model_.tile_kind(code="R")
    assert var_43 == 31
    var_59 = lambda *args, **kwargs: ["Tw\tx{|Ke"]
    var_60 = model_.Decomposition(pair=var_59, groups=var_43)
    var_61 = (var_60, -2772.75)
    model_.HandAnalysis(winning=var_43, decompositions=var_61)
    var_50 = -476
    model_.Decomposition(pair=var_43, groups=var_50)
    var_57 = model_.ActionKind
    model_.Event(kind=b"?\x83\xfcN\x9b\x020d\xc3\xa5\xa8\x86", action=var_57)


@pytest.mark.xfail(strict=True)
def test_18():
    model_.SettlementConfig(base=0, tai_value=-347)


def test_19():
    with pytest.raises(MahjongError):
        model_.tile_kind(code="esPid_Mvos6L`")


def test_20():
    var_94 = model_.is_sequence(kinds=(-2716, ">>A7yT7j.{~gqXG", True))
    assert var_94 is False


def test_21():
    with pytest.raises(MahjongError):
        model_.tile_kind(code=2279)


def test_22():
    var_50 = 1149
    with pytest.raises(MahjongError):
        model_.check_player(player=var_50)


def test_23():
    var_94 = model_.is_sequence(kinds=(False, -1, False))
    assert var_94 is False


def test_24():
    var_50 = -1831
    with pytest.raises(MahjongError):
        model_.check_player(player=var_50)


@pytest.mark.xfail(strict=True)
def test_25():
    var_50 = 0
    model_.check_player(player=var_50)
    var_71 = model_.MeldKind.CHI
    model_.Meld(
        kind=var_71,
        tiles=b"\xf3\x14\xcf\x08\xb3\xd1\x17\x81\xf4H",
        source=None,
        claimed_tile=(),
    )
