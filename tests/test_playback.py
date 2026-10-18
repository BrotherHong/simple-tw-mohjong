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
import tw_mahjong.playback

playback_ = sys.modules["tw_mahjong.playback"]


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
    var_64 = playback_._Terminal()
    with pytest.raises(OSError):
        var_64.__enter__()


def test_1():
    playback_._Terminal()


def test_2():
    var_4 = playback_._Terminal()
    var_4.__exit__()


@pytest.mark.xfail(strict=True)
def test_3():
    playback_.watch(result=None, ascii_tiles=False)


def test_4():
    var_63 = playback_._Terminal()
    var_63.key()


@pytest.mark.xfail(strict=True)
def test_5():
    playback_.watch(result=None, step=True, detail=True)


@pytest.mark.xfail(strict=True)
def test_6():
    var_172 = 282
    var_173 = playback_.ReplayFrame(
        index=var_172, state=None, action=var_172, events=()
    )
    var_195 = -134
    var_219 = playback_.SimulationResult(
        initial_state=None, final_state=var_195, actions=()
    )
    var_220 = -148.5305475368769
    var_221 = True
    playback_.render_frame(
        frame=var_173,
        result=var_219,
        recent=(160.27,),
        speed=var_220,
        paused=True,
        visible_total=complex(2939.0695241, 1410.7719263),
        detail=var_221,
        plain=False,
    )


@pytest.mark.xfail(strict=True)
def test_7():
    var_223 = playback_.ReplayFrame(index=1126, state=None, action=[], events=(-526.7,))
    var_235 = (var_223, True, 27, False, var_223)
    var_236 = playback_.SimulationResult(
        initial_state=var_235, final_state=None, actions=(var_223, var_223, 1937.11)
    )
    var_239 = True
    playback_.render_frame(
        frame=var_223,
        result=var_236,
        recent=var_235,
        speed=3814.51,
        paused=False,
        plain=False,
        ascii_tiles=var_239,
    )


def test_8():
    with pytest.raises(MahjongError):
        playback_.watch(
            result=None,
            speed=-506.58,
            plain=False,
            detail=False,
            ascii_tiles=True,
            no_color=False,
        )


@pytest.mark.xfail(strict=True)
def test_9():
    var_223 = playback_.ReplayFrame(
        index=-3019, state=None, action=b"Ne\x8c", events=()
    )
    var_235 = (var_223, True, 27, False, var_223)
    var_236 = playback_.SimulationResult(
        initial_state=var_235, final_state=None, actions=(var_223, var_223, 1937.11)
    )
    var_239 = True
    playback_.render_frame(
        frame=var_223,
        result=var_236,
        recent=(var_239, 2356),
        speed=-468.29,
        paused=var_239,
        visible_index=var_239,
        plain=False,
    )


def test_10():
    with pytest.raises(MahjongError):
        playback_.watch(result=None, speed=423.44)


@pytest.mark.xfail(strict=True)
def test_11():
    var_223 = playback_.ReplayFrame(index=3, state=None, action=False, events=())
    var_229 = -147
    var_230 = (var_229, var_223, True, 27, False)
    var_231 = playback_.SimulationResult(
        initial_state=var_230,
        final_state=var_230,
        actions=(var_223, var_230, "$SQCfW}\\Q1B\x0bWn"),
    )
    var_232 = False
    playback_.render_frame(
        frame=var_223,
        result=var_231,
        recent=(),
        speed=-1270.62,
        paused=True,
        visible_index=var_232,
    )


def test_12():
    var_64 = playback_._Terminal()
    var_64.__exit__()
    var_81 = hash
    var_82 = playback_.SimulationResult(
        initial_state=var_64, final_state=var_81, actions=False
    )
    var_83 = False
    with pytest.raises(MahjongError):
        playback_.watch(result=var_82, speed=var_64, ascii_tiles=var_83)


@pytest.mark.xfail(strict=True)
def test_13():
    var_64 = playback_._Terminal()
    var_79 = playback_._Terminal()
    var_92 = 5
    var_93 = playback_.ReplayFrame(
        index=var_92, state=var_79, action=["風,nt,nt", var_64, var_79], events=()
    )
    var_95 = var_93.__eq__(other=str)
    var_96 = (var_95, var_93)
    var_98 = var_93.__eq__(other=var_96)
    var_99 = playback_.SimulationResult(
        initial_state=[],
        final_state=(997, False, 1915.0),
        actions=b"C\xa1Wv\xce",
        settlement_config=var_98,
    )
    var_100 = 482.28
    var_101 = False
    var_102 = False
    playback_.render_frame(
        frame=var_93,
        result=var_99,
        recent=var_79,
        speed=var_100,
        paused=var_101,
        detail=var_100,
        plain=var_102,
    )


def test_14():
    with pytest.raises(MahjongError):
        playback_.watch(result=None, step=True, plain=True)


@pytest.mark.xfail(strict=True)
def test_15():
    var_223 = playback_.ReplayFrame(index=3361, state=None, action=3217, events=())
    var_229 = -147
    var_230 = (var_229, var_223, True, 27, False)
    var_231 = playback_.SimulationResult(
        initial_state=var_230,
        final_state=var_230,
        actions=(var_223, var_230, "$SQCfW}\\Q1B\x0bWn"),
    )
    var_232 = False
    playback_.render_frame(
        frame=var_223,
        result=var_231,
        recent=(),
        speed=269.24,
        paused=var_232,
        visible_total={" settlement_config settlement": "('"},
        detail=True,
    )


def test_16():
    var_56 = playback_.ActionKind.KONG_CONCEALED
    var_57 = -634
    var_58 = playback_.Action(kind=var_56, player=var_57)
    var_59 = var_58.__hash__()
    var_60 = var_58.__eq__(other=b"\x1cz\xac\xb5+\x83\xc3\xf8\x96\xa1\x8b\xca\xe7\xf5")
    var_61 = int
    var_62 = var_58.__hash__()
    var_63 = playback_.SimulationResult(
        initial_state=var_59,
        final_state=var_60,
        actions=var_61,
        settlement_config=var_62,
    )
    var_64 = True
    with pytest.raises(MahjongError):
        playback_.watch(result=var_63, speed=True, detail=var_64)


@pytest.mark.xfail(strict=True)
def test_17():
    var_223 = playback_.ReplayFrame(index=0, state=None, action=None, events=())
    var_235 = (var_223, True, 27, False)
    var_236 = playback_.SimulationResult(
        initial_state=var_235, final_state=None, actions=(var_223, var_223, 1937.11)
    )
    var_239 = True
    playback_.render_frame(
        frame=var_223,
        result=var_236,
        recent=var_235,
        speed=3814.51,
        paused=False,
        plain=False,
        ascii_tiles=var_239,
    )
