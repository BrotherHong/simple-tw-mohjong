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
import tw_mahjong.playback

playback_ = sys.modules["tw_mahjong.playback"]


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
    var_24 = playback_._Terminal()
    with pytest.raises(OSError):
        var_24.__enter__()


def test_1():
    var_28 = playback_._Terminal()
    var_28.__exit__()


@pytest.mark.xfail(strict=True)
def test_2():
    playback_.watch(result=None)


def test_3():
    playback_._Terminal()


def test_4():
    var_28 = playback_._Terminal()
    var_28.key()


@pytest.mark.xfail(strict=True)
def test_5():
    playback_.watch(result=None, step=True, detail=False)


def test_6():
    with pytest.raises(MahjongError):
        playback_.watch(result=None, speed=1256.5, plain=True, detail=False)


def test_7():
    with pytest.raises(MahjongError):
        playback_.watch(result=None, step=True, plain=True, ascii_tiles=True)


def test_8():
    with pytest.raises(MahjongError):
        playback_.watch(
            result=None, speed=-355.84, plain=True, detail=False, no_color=False
        )


def test_9():
    with pytest.raises(MahjongError):
        playback_.watch(result=0, speed=[-1488.21, True, False], no_color=True)


@pytest.mark.xfail(strict=True)
def test_10():
    var_86 = (2278, -1515.81, 1, -1, "")
    var_103 = playback_.ReplayFrame(index=3019, state=None, action=var_86, events=())
    var_110 = playback_.SimulationResult(
        initial_state=var_86, final_state=None, actions=(False, var_86)
    )
    playback_.render_frame(
        frame=var_103,
        result=var_110,
        recent=var_86,
        speed=274.14,
        paused=False,
        draws=2,
        detail=False,
    )


@pytest.mark.xfail(strict=True)
def test_11():
    var_86 = b"\t^\xf1\xeaS9\x10"
    var_103 = playback_.ReplayFrame(index=3019, state=None, action=var_86, events=())
    var_110 = playback_.SimulationResult(
        initial_state=var_86, final_state=None, actions=(False, var_86)
    )
    playback_.render_frame(
        frame=var_103,
        result=var_110,
        recent=(),
        speed=-174.85,
        paused=True,
        visible_index=complex(-797.46, 435.0),
        discards=2646,
        detail=True,
        ascii_tiles=True,
    )


@pytest.mark.xfail(strict=True)
def test_12():
    var_86 = (2278, -3572)
    var_100 = playback_.ReplayFrame(index=0, state=var_86, action=var_86, events=var_86)
    var_101 = playback_.SimulationResult(
        initial_state=None, final_state=None, actions=(), settlement_config=None
    )
    playback_.render_frame(
        frame=var_100,
        result=var_101,
        recent=(var_100,),
        speed=-1628.1,
        paused=True,
        detail=True,
        plain=False,
        columns=-680,
    )


@pytest.mark.xfail(strict=True)
def test_13():
    var_86 = b"\x8a(\x9aE\x1a\x0e\xbd\xf1\xe2\xdev"
    var_118 = playback_.ReplayFrame(
        index=1238, state=None, action=(), events=(-609.28, var_86)
    )
    var_119 = playback_.SimulationResult(
        initial_state=var_118, final_state=var_118, actions=(var_118, var_86)
    )
    playback_.render_frame(
        frame=var_118,
        result=var_119,
        recent=(var_119, -614.61, -3607),
        speed=1819.23,
        paused=False,
        visible_total=var_86,
        detail=False,
    )


@pytest.mark.xfail(strict=True)
def test_14():
    var_86 = (2278, -3572, "mKA%D_;F}:;']u(")
    var_100 = playback_.ReplayFrame(
        index=3651, state=None, action="ULg>LKZq\r", events=(False, var_86, var_86)
    )
    var_103 = playback_.SimulationResult(
        initial_state=None, final_state=var_86, actions=var_86
    )
    playback_.render_frame(
        frame=var_100,
        result=var_103,
        recent=var_86,
        speed=1026.63,
        paused=False,
        plain=False,
    )


@pytest.mark.xfail(strict=True)
def test_15():
    var_86 = b"\xcb\x9f\xb6\x04\xa6\x10\xa0(\x83E\xee[\xa1\x9b\x8b<o"
    var_103 = playback_.ReplayFrame(index=-4931, state=None, action=var_86, events=())
    var_110 = playback_.SimulationResult(
        initial_state=None, final_state=None, actions=(), settlement_config=None
    )
    playback_.render_frame(
        frame=var_103,
        result=var_110,
        recent=(var_103,),
        speed=-1628.1,
        paused=True,
        detail=True,
        plain=False,
        columns=-680,
    )


@pytest.mark.xfail(strict=True)
def test_16():
    var_86 = (2278, -3572, "mKA%D_;F}:;']u(", False)
    var_100 = playback_.ReplayFrame(
        index=4417,
        state=var_86,
        action=b"\xaay|\x84?[\xb5\xd38\xf31p\x06f\xf9\xfd\xc6$",
        events=(),
    )
    var_103 = playback_.SimulationResult(
        initial_state=None, final_state=None, actions=var_86
    )
    playback_.render_frame(
        frame=var_100,
        result=var_103,
        recent=var_86,
        speed=1026.63,
        paused=False,
        plain=False,
    )


def test_17():
    with pytest.raises(MahjongError):
        playback_.watch(result=-1023.28, speed=False)


@pytest.mark.xfail(strict=True)
def test_18():
    var_86 = b"\xcb\x9f\xb6\x04\xa6\x10\xa0(\x83E\xee[\xa1\x9b\x8b<o"
    var_103 = playback_.ReplayFrame(
        index=5, state=None, action=None, events=("H,.me", 1243, var_86)
    )
    var_115 = playback_.SimulationResult(
        initial_state=None, final_state=None, actions=()
    )
    playback_.render_frame(
        frame=var_103,
        result=var_115,
        recent=(var_103,),
        speed=-1628.1,
        paused=True,
        detail=True,
        plain=False,
        columns=-680,
    )
