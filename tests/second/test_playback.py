"""Pure rendering and terminal-local playback without real waits or key input."""

import io
from dataclasses import replace

import pytest

import tw_mahjong.playback as playback
from tw_mahjong.model import (
    Action, ActionKind, Event, EventKind, MahjongError, ReplayFrame, SimulationResult, Tile,
)
from tw_mahjong.simulation import iter_replay


@pytest.mark.parametrize("kind", [EventKind.WON,EventKind.KONG_COMPLETED,EventKind.CLAIMED])
def test_resolved_action_takes_precedence_over_last_pass(initial_state, kind):
    resolved = Action(ActionKind.HU if kind is EventKind.WON else ActionKind.PENG,1)
    last = Action(ActionKind.PASS,3)
    frame = ReplayFrame(4,initial_state,last,(Event(kind,1,0,resolved),))
    assert playback.main_action(frame) == resolved
    assert playback.main_action(frame,detail=True) == last


def test_pure_pass_hidden_and_nonpass_shown(initial_state):
    assert playback.main_action(ReplayFrame(0,initial_state,None,())) is None
    passed = ReplayFrame(1,initial_state,Action(ActionKind.PASS,1),())
    assert playback.main_action(passed) is None
    assert playback.main_action(passed,True) == passed.action
    discard = Action(ActionKind.DISCARD,0,(0,))
    assert playback.main_action(replace(passed,action=discard)) == discard


def test_visible_filter_keeps_endpoints_and_counts_raw_actions(prefix_result):
    frames = playback._visible_frames(prefix_result)
    assert [f.frame.index for f in frames] == [0,1,5]
    assert [(f.draws,f.discards) for f in frames] == [(0,0),(0,1),(1,1)]
    assert all("RESPONSE" not in event and "PASS" not in event for f in frames for event in f.recent)
    detailed = playback._visible_frames(prefix_result,detail=True)
    assert [f.frame.index for f in detailed] == list(range(6))
    assert any("PASS" in event for f in detailed for event in f.recent)
    assert all(len(f.recent) <= 5 for f in detailed)


def test_last_pure_pass_is_still_visible(prefix_result):
    frames = tuple(iter_replay(prefix_result.initial_state,prefix_result.actions[:2]))
    result = SimulationResult(prefix_result.initial_state,frames[-1].state,prefix_result.actions[:2])
    assert [f.frame.index for f in playback._visible_frames(result)] == [0,1,2]


def test_empty_record_has_one_visible_initial_frame(initial_state):
    result = SimulationResult(initial_state,initial_state,())
    frames = playback._visible_frames(result)
    assert len(frames) == 1 and frames[0].frame.index == 0


def test_plain_render_has_complete_river_and_english_codes(state_factory):
    river = tuple(Tile(i) for i in range(20))
    state = state_factory(discards=(river,(),(),()))
    result = SimulationResult(state,state,())
    frame = ReplayFrame(0,state,None,())
    text = playback.render_frame(frame,result,("DRAWN P0 1m",),speed=2,paused=False,
                                  plain=True,ascii_tiles=False,color=True)
    assert "\x1b" not in text and text.isascii()
    assert "river: " + " ".join(t.code for t in river) in text
    assert text.count("melds: -") == 4
    assert "End of recorded prefix (game unfinished)." in text
    assert result.final_state is state


@pytest.mark.parametrize("speed", [True,False,0,-1,0.249,64.01,float("inf"),float("-inf"),float("nan"),"2",None])
def test_watch_rejects_invalid_speed(initial_state, speed):
    result = SimulationResult(initial_state,initial_state,())
    with pytest.raises(MahjongError) as error:
        playback.watch(result,speed=speed,plain=True)
    assert error.value.code == "INVALID_PLAYBACK"


@pytest.mark.parametrize("speed", [0.25,2,64])
def test_plain_watch_never_waits_or_opens_terminal(prefix_result, speed, monkeypatch, capsys):
    def forbidden(*args,**kwargs):
        pytest.fail("Plain playback must not wait or enter terminal mode")
    monkeypatch.setattr(playback.time,"sleep",forbidden)
    monkeypatch.setattr(playback,"_Terminal",forbidden)
    playback.watch(prefix_result,speed=speed,plain=True)
    text = capsys.readouterr().out
    assert "\x1b" not in text
    assert text.count("Taiwanese mahjong") == 3
    assert "display 0/2" in text and "display 2/2" in text
    assert "operation 5/5" in text and "draws 1 discards 1" in text


def test_non_tty_automatically_uses_plain_output(prefix_result, monkeypatch, capsys):
    monkeypatch.setattr(playback.sys,"stdin",io.StringIO())
    playback.watch(prefix_result)
    assert "\x1b" not in capsys.readouterr().out


def test_plain_detail_prints_every_raw_frame(prefix_result, capsys):
    playback.watch(prefix_result,plain=True,detail=True)
    text = capsys.readouterr().out
    assert text.count("Taiwanese mahjong") == 6
    assert "PASS" in text and "RESPONSE" in text


@pytest.mark.parametrize("plain", [False,True])
def test_step_rejected_for_redirected_input(initial_state, plain, monkeypatch):
    monkeypatch.setattr(playback.sys,"stdin",io.StringIO())
    result = SimulationResult(initial_state,initial_state,())
    with pytest.raises(MahjongError) as error:
        playback.watch(result,step=True,plain=plain)
    assert error.value.code == "INVALID_PLAYBACK"


def test_final_render_includes_score_and_payments(winning_state):
    result = SimulationResult(winning_state,winning_state,())
    text = playback.render_frame(ReplayFrame(0,winning_state,None,()),result,(),speed=2,paused=False)
    assert "Result: SELF_DRAW | winner=0 source=0" in text
    assert "Hand tai: 19" in text
    assert all(f"P{p} -> P0:" in text for p in (1,2,3))
    assert "Score deltas:" in text


def test_v1_output_does_not_guess_scoring(completed_results):
    result = completed_results[1]
    frames = tuple(iter_replay(result.initial_state,result.actions))
    text = playback.render_frame(frames[-1],result,(),speed=2,paused=False)
    assert "Scoring: unavailable (v1 record)." in text
    assert "Hand tai:" not in text


def test_interactive_step_and_quit_use_mock_terminal_only(prefix_result, monkeypatch):
    class TTY(io.StringIO):
        def isatty(self):
            return True
    output = TTY()
    keys = iter(("n","q"))
    lifecycle = []
    class Terminal:
        def __enter__(self):
            lifecycle.append("enter")
            return self
        def __exit__(self,*args):
            lifecycle.append("exit")
        def key(self):
            return next(keys)
    monkeypatch.setattr(playback.sys,"stdin",TTY())
    monkeypatch.setattr(playback.sys,"stdout",output)
    monkeypatch.setattr(playback,"_Terminal",Terminal)
    monkeypatch.setattr(playback.time,"monotonic",lambda:0)
    monkeypatch.setattr(playback.time,"sleep",lambda delay:None)
    playback.watch(prefix_result,step=True,ascii_tiles=True,no_color=True)
    assert lifecycle == ["enter","exit"]
    text = output.getvalue()
    assert "Display 0/2" in text and "Display 1/2" in text
    assert "Display 2/2" not in text


def test_interactive_exception_exits_terminal_context(prefix_result, monkeypatch):
    class TTY(io.StringIO):
        def isatty(self):
            return True
    exited = []
    class Terminal:
        def __enter__(self):
            return self
        def __exit__(self,*args):
            exited.append(args[0])
        def key(self):
            raise KeyboardInterrupt
    monkeypatch.setattr(playback.sys,"stdin",TTY())
    monkeypatch.setattr(playback.sys,"stdout",TTY())
    monkeypatch.setattr(playback,"_Terminal",Terminal)
    with pytest.raises(KeyboardInterrupt):
        playback.watch(prefix_result,step=True)
    assert exited == [KeyboardInterrupt]
