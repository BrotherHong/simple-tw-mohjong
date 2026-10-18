"""Visible-frame filtering, pure transcripts and controlled keyboard playback."""

import io
import sys
from dataclasses import replace
from types import SimpleNamespace

import pytest

import tw_mahjong.playback as playback
from tw_mahjong.model import Action, ActionKind as A, Event, EventKind as E, MahjongError, ReplayFrame, SimulationResult
from tw_mahjong.simulation import iter_replay, replay


class Stream(io.StringIO):
    def __init__(self, *, tty=False, encoding="utf-8"):
        super().__init__()
        self.tty = tty
        self.codec = encoding

    @property
    def encoding(self):
        return self.codec

    def isatty(self):
        return self.tty


@pytest.fixture
def streams(monkeypatch):
    def install(*, stdin_tty=False, stdout_tty=False, encoding="utf-8"):
        stdin, stdout = Stream(tty=stdin_tty), Stream(tty=stdout_tty, encoding=encoding)
        monkeypatch.setattr(playback.sys, "stdin", stdin)
        monkeypatch.setattr(playback.sys, "stdout", stdout)
        return stdin, stdout
    return install


def fail_io(*args, **kwargs):
    pytest.fail("plain playback must not wait, read keys, or enter terminal mode")


@pytest.mark.parametrize("speed", [True, False, None, "2", 0, -1, 0.249, 64.001, float("nan"), float("inf"), -float("inf")])
def test_watch_rejects_invalid_speed(prefix, speed):
    with pytest.raises(MahjongError) as exc:
        playback.watch(prefix, speed=speed, plain=True)
    assert exc.value.code == "INVALID_PLAYBACK"


@pytest.mark.parametrize("stdin_tty,stdout_tty,plain", [(False, False, False), (True, False, False), (False, True, False), (True, True, True)])
def test_step_requires_both_ttys_without_plain(prefix, streams, stdin_tty, stdout_tty, plain):
    streams(stdin_tty=stdin_tty, stdout_tty=stdout_tty)
    with pytest.raises(MahjongError) as exc:
        playback.watch(prefix, step=True, plain=plain)
    assert exc.value.code == "INVALID_PLAYBACK"


@pytest.mark.parametrize("speed", [0.25, 2, 64])
@pytest.mark.parametrize("detail,count", [(False, 3), (True, 6)])
def test_plain_watch_has_no_ansi_wait_or_terminal_input(prefix, streams, monkeypatch, speed, detail, count):
    _, out = streams()
    monkeypatch.setattr(playback.time, "sleep", fail_io)
    monkeypatch.setattr(playback.time, "monotonic", fail_io)
    monkeypatch.setattr(playback, "_Terminal", fail_io)
    playback.watch(prefix, speed=speed, detail=detail, ascii_tiles=False, no_color=False)
    text = out.getvalue()
    assert text.count("Taiwanese mahjong |") == count
    assert "\x1b" not in text and text.isascii()
    assert "End of recorded prefix (game unfinished)." in text
    assert ("Action: P1 PASS" in text) == detail
    assert "display 0/" in text and "draws 1 discards 1" in text


def test_explicit_plain_bypasses_interactive_console(prefix, streams, monkeypatch):
    _, out = streams(stdin_tty=True, stdout_tty=True)
    monkeypatch.setattr(playback, "_Terminal", fail_io)
    playback.watch(prefix, plain=True)
    assert "Taiwanese mahjong" in out.getvalue()


@pytest.mark.parametrize("length,expected", [(0, [0]), (1, [0, 1]), (2, [0, 1, 2]), (3, [0, 1, 3]), (4, [0, 1, 4]), (5, [0, 1, 5])])
def test_visible_frames_keep_endpoints_even_for_final_pure_pass(prefix, length, expected):
    actions = prefix.actions[:length]
    result = replace(prefix, actions=actions, final_state=replay(prefix.initial_state, actions))
    frames = playback._visible_frames(result)
    assert [f.frame.index for f in frames] == expected
    assert [f.frame.index for f in playback._visible_frames(result, detail=True)] == list(range(length + 1))


@pytest.mark.parametrize("event_kind", [E.WON, E.KONG_COMPLETED, E.CLAIMED])
def test_main_action_uses_resolved_actor_instead_of_final_pass(prefix, event_kind):
    resolved = Action(A.HU if event_kind is E.WON else A.PENG, 1, () if event_kind is E.WON else (1, 2))
    submitted = Action(A.PASS, 3)
    frame = ReplayFrame(4, prefix.final_state, submitted, (Event(event_kind, 1, 0, resolved),))
    assert playback.main_action(frame) == resolved
    assert playback.main_action(frame, detail=True) == submitted


def test_pure_pass_has_no_main_action(prefix):
    frame = ReplayFrame(2, prefix.final_state, Action(A.PASS, 2), (Event(E.RESPONSE, 2),))
    assert playback.main_action(frame) is None
    assert playback.main_action(frame, detail=True) == frame.action


def test_render_frame_is_pure_and_plain_ignores_styling(prefix):
    frame = next(iter_replay(prefix.initial_state, prefix.actions))
    before = repr(frame.state)
    first = playback.render_frame(frame, prefix, (), speed=2, paused=True,
                                  plain=True, color=True, ascii_tiles=False)
    second = playback.render_frame(frame, prefix, (), speed=2, paused=True,
                                   plain=True, color=False, ascii_tiles=True)
    assert first == second and "\x1b" not in first
    assert repr(frame.state) == before
    assert "PAUSED" in first and first.count("melds: -") == 4


def test_plain_render_keeps_entire_river(prefix):
    from tw_mahjong.model import Tile
    river = tuple(Tile(i * 4) for i in range(20))
    state = replace(prefix.initial_state, discards=(river, (), (), ()))
    frame = ReplayFrame(0, state, None, ())
    text = playback.render_frame(frame, prefix, (), speed=2, paused=False)
    assert "  river: " + " ".join(t.code for t in river) in text


def test_final_frame_includes_score_and_payments(won):
    result = SimulationResult(won, won, ())
    frame = ReplayFrame(0, won, None, ())
    text = playback.render_frame(frame, result, (), speed=2, paused=False)
    assert "Result: SELF_DRAW" in text
    assert "Hand tai: 4" in text and "CONCEALED_SELF_DRAW: +3" in text
    assert all(f"P{p} -> P0:" in text for p in (1, 2, 3))
    assert "Score deltas:" in text


def test_legacy_final_frame_explicitly_has_no_scoring(won):
    legacy = replace(won, rules_version=1, draw_source=None)
    result = SimulationResult(legacy, legacy, ())
    text = playback.render_frame(ReplayFrame(0, legacy, None, ()), result, (), speed=2, paused=False)
    assert "Scoring: unavailable (v1 record)." in text
    assert "Hand tai:" not in text


def test_resolved_claim_pass_is_visible_and_recent_history_omits_pass(prefix, monkeypatch):
    resolved = Action(A.PENG, 1, (1, 2))
    frames = (ReplayFrame(0, prefix.initial_state, None, ()),
              ReplayFrame(2, prefix.final_state, Action(A.PASS, 3), (Event(E.CLAIMED, 1, 0, resolved),)),
              ReplayFrame(5, prefix.final_state, Action(A.PASS, 2), (Event(E.RESPONSE, 2),)))
    monkeypatch.setattr(playback, "iter_replay", lambda *args: iter(frames))
    visible = playback._visible_frames(prefix)
    assert [f.frame.index for f in visible] == [0, 2, 5]
    assert any("P1 PENG" in event for event in visible[1].recent)
    assert all("PASS" not in event and "RESPONSE" not in event for item in visible for event in item.recent)


def test_pending_claim_history_is_request_until_resolution(prefix, monkeypatch):
    request = Action(A.CHI, 1, (4, 8))
    frame = ReplayFrame(1, prefix.initial_state, request, (Event(E.RESPONSE, 1, action=request),))
    monkeypatch.setattr(playback, "iter_replay", lambda *args: iter((frame,)))
    assert playback._visible_frames(prefix)[0].recent == ("P1 REQUEST_CHI 2m 3m",)
    detailed = playback._visible_frames(prefix, detail=True)[0].recent
    assert detailed == ("P1 CHI 2m 3m", "RESPONSE P1")


def test_interactive_keyboard_step_speed_pause_and_quit(prefix, streams, monkeypatch):
    _, out = streams(stdin_tty=True, stdout_tty=True)
    keys = iter(("n", "+", "-", " ", "n", "q"))
    lifecycle = []
    class Terminal:
        def __enter__(self):
            lifecycle.append("enter")
            return self
        def __exit__(self, *args):
            lifecycle.append("exit")
        def key(self):
            return next(keys)
    monkeypatch.setattr(playback, "_Terminal", Terminal)
    monkeypatch.setattr(playback.time, "monotonic", lambda: 0)
    monkeypatch.setattr(playback.time, "sleep", lambda _: None)
    playback.watch(prefix, step=True, detail=True, ascii_tiles=True, no_color=True)
    text = out.getvalue()
    assert lifecycle == ["enter", "exit"]
    assert "PAUSED" in text and "PLAYING" in text
    assert "4 steps/s" in text and "2 steps/s" in text
    assert "operation 2/5" in text and "operation 3/5" not in text


@pytest.mark.parametrize("error", [RuntimeError("console failure"), KeyboardInterrupt()])
def test_terminal_context_exits_when_playback_raises(prefix, streams, monkeypatch, error):
    streams(stdin_tty=True, stdout_tty=True)
    seen = []
    class Terminal:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            seen.append(args[0])
        def key(self):
            raise error
    monkeypatch.setattr(playback, "_Terminal", Terminal)
    with pytest.raises(type(error)) as exc:
        playback.watch(prefix, step=True, ascii_tiles=True)
    assert exc.value is error
    assert seen == [type(error)]


def test_ascii_fallback_for_narrow_output_encoding(prefix, streams, monkeypatch):
    _, out = streams(stdin_tty=True, stdout_tty=True, encoding="ascii")
    class Terminal:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def key(self):
            return "q"
    monkeypatch.setattr(playback, "_Terminal", Terminal)
    playback.watch(prefix, step=True)
    assert out.getvalue().isascii()
    assert "Initial board" in out.getvalue()


def test_chinese_finished_board_includes_named_score_and_payments(won):
    result = SimulationResult(won, won, ())
    text = playback.render_frame(ReplayFrame(0, won, None, ()), result, (),
                                 speed=2, paused=False, plain=False, columns=120)
    assert "結果: 自摸" in text and "門清自摸: +3" in text
    assert "P1 -> P0:" in text and "分數增減:" in text


def test_final_interactive_frame_returns_without_reading_key(won, streams, monkeypatch):
    streams(stdin_tty=True, stdout_tty=True)
    lifecycle = []
    class Terminal:
        def __enter__(self):
            lifecycle.append("enter")
            return self
        def __exit__(self, *args):
            lifecycle.append("exit")
        key = fail_io
    monkeypatch.setattr(playback, "_Terminal", Terminal)
    playback.watch(SimulationResult(won, won, ()), step=True, ascii_tiles=True)
    assert lifecycle == ["enter", "exit"]


@pytest.mark.parametrize("initial_speed,key,expected", [(64, "+", 64), (0.25, "-", 0.25), (2, "=", 4)])
def test_keyboard_speed_clamps_and_equal_key(prefix, streams, monkeypatch, initial_speed, key, expected):
    _, out = streams(stdin_tty=True, stdout_tty=True)
    keys = iter((key, "q"))
    class Terminal:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def key(self):
            return next(keys)
    monkeypatch.setattr(playback, "_Terminal", Terminal)
    monkeypatch.setattr(playback.time, "monotonic", lambda: 0)
    monkeypatch.setattr(playback.time, "sleep", lambda _: None)
    playback.watch(prefix, speed=initial_speed, step=True, ascii_tiles=True)
    assert f"{expected:g} steps/s" in out.getvalue()


def test_terminal_resize_rerenders_current_frame(prefix, streams, monkeypatch):
    streams(stdin_tty=True, stdout_tty=True)
    widths = iter((100, 120, 120, 120))
    keys = iter((None, "q"))
    rendered_widths = []
    class Terminal:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def key(self):
            return next(keys)
    original = playback.render_frame
    def render(*args, **kwargs):
        rendered_widths.append(kwargs["columns"])
        return original(*args, **kwargs)
    monkeypatch.setattr(playback, "_Terminal", Terminal)
    monkeypatch.setattr(playback, "render_frame", render)
    monkeypatch.setattr(playback.shutil, "get_terminal_size", lambda *args: SimpleNamespace(columns=next(widths)))
    monkeypatch.setattr(playback.time, "monotonic", lambda: 0)
    monkeypatch.setattr(playback.time, "sleep", lambda _: None)
    playback.watch(prefix, step=True, ascii_tiles=True)
    assert rendered_widths == [120]


@pytest.fixture
def windows_console(monkeypatch):
    """Fake kernel32 without touching the process's actual console mode."""
    import ctypes
    calls = []
    class Function:
        def __init__(self, function):
            self.function = function
        def __call__(self, *args):
            return self.function(*args)
    def read_mode(handle, pointer):
        pointer._obj.value = 8
        return True
    def set_mode(handle, mode):
        calls.append((handle, mode))
        return True
    kernel = SimpleNamespace(GetStdHandle=Function(lambda _: 123),
                             GetConsoleMode=Function(read_mode), SetConsoleMode=Function(set_mode))
    monkeypatch.setattr(playback, "os", SimpleNamespace(name="nt"))
    monkeypatch.setattr(ctypes, "WinDLL", lambda *args, **kwargs: kernel, raising=False)
    monkeypatch.setattr(ctypes, "get_last_error", lambda: 5, raising=False)
    return kernel, calls


def test_windows_terminal_restores_mode_and_cursor(streams, windows_console):
    _, out = streams()
    _, calls = windows_console
    with playback._Terminal():
        assert calls == [(123, 12)]
    assert calls == [(123, 12), (123, 8)]
    assert "\x1b[?25l" in out.getvalue() and "\x1b[?25h" in out.getvalue()


@pytest.mark.parametrize("operation", ["GetConsoleMode", "SetConsoleMode"])
def test_windows_terminal_setup_failure_reports_oserror(streams, windows_console, operation):
    streams()
    kernel, _ = windows_console
    getattr(kernel, operation).function = lambda *args: False
    with pytest.raises(OSError):
        with playback._Terminal():
            pytest.fail("unsupported terminal must fail before entering body")


def test_windows_terminal_restores_mode_even_when_output_fails(streams, windows_console, monkeypatch):
    _, out = streams()
    _, calls = windows_console
    def fail_write(*args):
        raise OSError("output failed")
    monkeypatch.setattr(out, "write", fail_write)
    with pytest.raises(OSError):
        with playback._Terminal():
            pytest.fail("failed output should prevent entry")
    assert calls[-1] == (123, 8)


@pytest.mark.parametrize("keys,expected", [([], None), (["n"], "n"), (["\x00", "H"], None), (["\xe0", "P"], None)])
def test_windows_key_input_filters_extended_keys(monkeypatch, keys, expected):
    pending = list(keys)
    msvcrt = SimpleNamespace(kbhit=lambda: bool(pending), getwch=lambda: pending.pop(0))
    monkeypatch.setitem(sys.modules, "msvcrt", msvcrt)
    monkeypatch.setattr(playback, "os", SimpleNamespace(name="nt"))
    assert playback._Terminal().key() == expected
    assert pending == []


def test_windows_ctrl_c_raises_keyboard_interrupt(monkeypatch):
    monkeypatch.setitem(sys.modules, "msvcrt", SimpleNamespace(kbhit=lambda: True, getwch=lambda: "\x03"))
    monkeypatch.setattr(playback, "os", SimpleNamespace(name="nt"))
    with pytest.raises(KeyboardInterrupt):
        playback._Terminal().key()
