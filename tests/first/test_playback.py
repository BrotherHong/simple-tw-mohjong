from dataclasses import replace
from io import StringIO

import pytest

import tw_mahjong.playback as playback
from tw_mahjong.engine import apply_action
from tw_mahjong.model import (
    Action, ActionKind, Event, EventKind, MahjongError, ReplayFrame, SimulationResult,
)
from tw_mahjong.simulation import iter_replay, replay


def prefix(initial):
    actions = (Action(ActionKind.DISCARD, 0, (0,)),
               Action(ActionKind.PASS, 1), Action(ActionKind.PASS, 2),
               Action(ActionKind.PASS, 3), Action(ActionKind.DRAW, 1))
    return SimulationResult(initial, replay(initial, actions), actions)


def test_main_action_shows_resolved_claim_instead_of_last_pass(initial):
    claim = Action(ActionKind.PENG, 2, (1, 2))
    last = Action(ActionKind.PASS, 3)
    frame = ReplayFrame(4, initial, last,
                        (Event(EventKind.RESPONSE, 3, action=last),
                         Event(EventKind.CLAIMED, 2, 0, claim), Event(EventKind.TURN, 2)))
    assert playback.main_action(frame) == claim
    assert playback.main_action(frame, detail=True) == last
    assert playback.main_action(replace(frame, events=())) is None


def test_visible_frames_filter_pass_but_keep_endpoints_and_counters(initial):
    result = prefix(initial)
    visible = playback._visible_frames(result)
    detailed = playback._visible_frames(result, detail=True)
    assert [item.frame.index for item in visible] == [0, 1, 5]
    assert [item.frame.index for item in detailed] == list(range(6))
    assert (visible[-1].draws, visible[-1].discards) == (1, 1)
    assert all("PASS" not in event and "RESPONSE" not in event
               for item in visible for event in item.recent)
    assert any("PASS" in event for item in detailed for event in item.recent)
    short = SimulationResult(initial, replay(initial, result.actions[:2]), result.actions[:2])
    assert [item.frame.index for item in playback._visible_frames(short)] == [0, 1, 2]


def test_empty_record_still_has_initial_frame(initial):
    visible = playback._visible_frames(SimulationResult(initial, initial, ()))
    assert len(visible) == 1
    assert visible[0].frame.index == visible[0].draws == visible[0].discards == 0


def test_plain_render_is_complete_english_and_has_no_ansi(exhausted):
    result = SimulationResult(exhausted, exhausted, ())
    frame = ReplayFrame(0, exhausted, None, ())
    text = playback.render_frame(frame, result, (), speed=2, paused=False,
                                 plain=True, ascii_tiles=False, color=True)
    assert "FINISHED" in text
    assert "WALL_EXHAUSTED" in text
    assert "Hand tai: 0" in text
    assert "Score deltas: (0, 0, 0, 0)" in text
    assert "\x1b" not in text
    assert text.isascii()
    river = next(line for line in text.splitlines() if "river: 1m" in line)
    assert len(river.split("river: ")[1].split()) == 136
    assert text.count("melds: -") == 4


def test_render_unfinished_prefix_and_legacy_result(initial, exhausted):
    text = playback.render_frame(ReplayFrame(0, initial, None, ()),
                                 SimulationResult(initial, initial, ()), (), speed=2, paused=False)
    assert "End of recorded prefix (game unfinished)." in text
    legacy = replace(exhausted, rules_version=1)
    text = playback.render_frame(ReplayFrame(0, legacy, None, ()),
                                 SimulationResult(legacy, legacy, ()), (), speed=2, paused=False)
    assert "Scoring: unavailable (v1 record)." in text


@pytest.mark.parametrize("speed", [True, False, None, "2", 0, 0.24, 65, float("nan"), float("inf"), -float("inf")])
def test_watch_rejects_invalid_speed(initial, speed):
    with pytest.raises(MahjongError) as caught:
        playback.watch(SimulationResult(initial, initial, ()), speed=speed, plain=True)
    assert caught.value.code == "INVALID_PLAYBACK"


def test_watch_plain_transcript_has_no_clock_or_keyboard_wait(initial, monkeypatch, capsys):
    def forbidden(*args, **kwargs):
        pytest.fail("Plain playback must not wait or initialize a terminal")
    monkeypatch.setattr(playback.time, "sleep", forbidden)
    monkeypatch.setattr(playback.time, "monotonic", forbidden)
    monkeypatch.setattr(playback, "_Terminal", forbidden)
    result = prefix(initial)
    before = repr(result)
    playback.watch(result, plain=True)
    text = capsys.readouterr().out
    assert text.count("Taiwanese mahjong") == 3
    assert "operation 5/5" in text
    assert "\x1b" not in text
    assert repr(result) == before


def test_watch_step_requires_interactive_terminal(initial):
    with pytest.raises(MahjongError) as caught:
        playback.watch(SimulationResult(initial, initial, ()), step=True, plain=True)
    assert caught.value.code == "INVALID_PLAYBACK"


def test_non_tty_automatically_uses_plain_transcript(initial, monkeypatch):
    output = StringIO()
    monkeypatch.setattr(playback.sys, "stdin", StringIO())
    monkeypatch.setattr(playback.sys, "stdout", output)
    playback.watch(SimulationResult(initial, initial, ()))
    assert "Taiwanese mahjong" in output.getvalue()
    assert "\x1b" not in output.getvalue()


def interactive_console(monkeypatch, keys):
    class TTY(StringIO):
        def isatty(self):
            return True
    class Terminal:
        entered = False
        exited = False
        exit_error = None
        def __enter__(self):
            self.entered = True
            return self
        def __exit__(self, exc_type, exc, tb):
            self.exited = True
            self.exit_error = exc
        def key(self):
            value = next(keys)
            if isinstance(value, BaseException):
                raise value
            return value
    terminal = Terminal()
    output = TTY()
    monkeypatch.setattr(playback.sys, "stdin", TTY())
    monkeypatch.setattr(playback.sys, "stdout", output)
    monkeypatch.setattr(playback, "_Terminal", lambda: terminal)
    monkeypatch.setattr(playback.time, "monotonic", lambda: 0)
    monkeypatch.setattr(playback.time, "sleep", lambda delay: None)
    return terminal, output


def test_interactive_step_uses_visible_frames_and_exits_at_last_frame(initial, monkeypatch):
    terminal, output = interactive_console(monkeypatch, iter(["n", "\r"]))
    playback.watch(prefix(initial), step=True, ascii_tiles=True, no_color=True)
    assert terminal.entered and terminal.exited
    assert "operation 5/5" in output.getvalue()
    assert "FINISHED" in output.getvalue()
    assert "\x1b[H" in output.getvalue()


def test_interactive_speed_is_clamped_and_quit_leaves_terminal(initial, monkeypatch):
    terminal, output = interactive_console(monkeypatch, iter(["+", "+", "-", "q"]))
    playback.watch(prefix(initial), speed=64, step=True, ascii_tiles=True)
    assert "64 steps/s" in output.getvalue()
    assert "32 steps/s" in output.getvalue()
    assert "operation 5/5" not in output.getvalue()
    assert terminal.exited


def test_interactive_exception_leaves_terminal_context(initial, monkeypatch):
    error = RuntimeError("input failed")
    terminal, _ = interactive_console(monkeypatch, iter([error]))
    with pytest.raises(RuntimeError) as caught:
        playback.watch(prefix(initial), step=True, ascii_tiles=True)
    assert caught.value is error
    assert terminal.exited
    assert terminal.exit_error is error
