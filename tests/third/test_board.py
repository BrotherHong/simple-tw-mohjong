"""Terminal cell widths, tile palette, responsive panels and draw markers."""

from dataclasses import replace

import pytest

from tw_mahjong.board import display_width, render_board, tile_block
from tw_mahjong.model import Action, ActionKind, Event, EventKind, ReplayFrame, Tile
from tw_mahjong.simulation import iter_replay


def render(frame, result, *, columns=100, ascii_tiles=True, color=False, recent=(), primary=None):
    return render_board(frame, result, recent, primary=primary, speed=2, paused=False,
                        visible_index=0, visible_total=5, draws=0, discards=0,
                        columns=columns, ascii_tiles=ascii_tiles, color=color, result_lines=())


@pytest.mark.parametrize("text,width", [("abc", 3), ("一萬", 4), ("東 E", 4),
    ("e\u0301", 1), ("\x1b[1;31m[一萬]\x1b[0m", 6), ("", 0)])
def test_display_width_ignores_ansi_and_combining_marks(text, width):
    assert display_width(text) == width


@pytest.mark.parametrize("kind", range(42))
@pytest.mark.parametrize("ascii_tiles,color", [(False, False), (False, True), (True, False), (True, True)])
def test_all_tile_blocks_have_six_cells_plus_marker(kind, ascii_tiles, color):
    tile = Tile(kind * 4 if kind < 34 else kind + 102)
    plain = tile_block(tile, ascii_tiles=ascii_tiles, color=color)
    marked = tile_block(tile, ascii_tiles=ascii_tiles, color=color, marked=True)
    assert plain.startswith(" ") and marked.startswith("*")
    assert display_width(plain[1:]) == display_width(marked[1:]) == 6
    assert ("\x1b[" in plain) == color
    assert ("\x1b[1;" in marked) == color
    if ascii_tiles:
        assert tile.code in plain


@pytest.mark.parametrize("tile_id,label,palette", [(0, "一萬", 31), (32, "九萬", 31),
    (36, "一筒", 94), (72, "一索", 32), (108, "東", 33), (132, "白", 33),
    (136, "春花", 95), (143, "菊花", 95)])
def test_chinese_labels_and_palette(tile_id, label, palette):
    block = tile_block(Tile(tile_id), ascii_tiles=False, color=True)
    assert label in block and f"\x1b[{palette}m" in block


@pytest.mark.parametrize("columns", [20, 40, 80, 119, 120, 160])
@pytest.mark.parametrize("ascii_tiles,color", [(False, False), (False, True), (True, False)])
def test_responsive_board_fits_terminal_width(prefix, columns, ascii_tiles, color):
    frame = next(iter_replay(prefix.initial_state, prefix.actions))
    board = render(frame, prefix, columns=columns, ascii_tiles=ascii_tiles, color=color)
    assert all(display_width(line) <= columns for line in board.splitlines())
    assert all(f"P{p}" in board for p in range(4))
    borders = [line for line in board.splitlines() if line.startswith("+")]
    assert len(borders) == (4 if columns >= 120 else 8)
    assert ("\x1b[" in board) == color


def test_initial_draw_mark_is_step_local(prefix):
    frames = tuple(iter_replay(prefix.initial_state, prefix.actions))
    first = render(frames[0], prefix)
    # Ignore the legend's asterisk and check actual tile marker prefixes.
    assert "*[" in first
    response = render(frames[2], prefix)
    assert "*[" not in response
    drawn = render(frames[-1], prefix, primary=frames[-1].action)
    assert "*[" in drawn and "DRAW" in drawn


def test_claim_action_line_includes_external_tile(prefix):
    action = Action(ActionKind.PENG, 1, (1, 2))
    event = Event(EventKind.CLAIMED, 1, 0, action)
    frame = ReplayFrame(4, prefix.final_state, Action(ActionKind.PASS, 3), (event,))
    board = render(frame, prefix, primary=action)
    action_line = board.split("Action:", 1)[1].split("Recent events:", 1)[0]
    assert "P1" in action_line and "PENG" in action_line
    assert action_line.count("[1m") == 3


def test_pending_claim_is_labeled_as_request(prefix):
    frames = tuple(iter_replay(prefix.initial_state, prefix.actions))
    action = Action(ActionKind.PENG, 1, (1, 2))
    frame = replace(frames[1], action=action, events=(Event(EventKind.RESPONSE, 1, action=action),))
    board = render(frame, prefix, primary=action)
    assert "request PENG" in board
    assert board.split("Action:", 1)[1].count("[1m") == 3


def test_river_panel_shows_only_latest_twelve_and_total(initial, prefix):
    river = tuple(Tile(i * 4) for i in range(16))
    state = replace(initial, discards=(river, (), (), ()))
    frame = ReplayFrame(0, state, None, ())
    board = render(frame, prefix, columns=100)
    river_part = board.split("River(16,hidden=4):", 1)[1].split("+", 1)[0]
    assert "[1m" not in river_part and "[4m" not in river_part
    assert "[5m" in river_part and "[7p" in river_part
    assert river_part.count("[") == 12


def test_empty_melds_and_relative_wind_labels(prefix):
    state = replace(prefix.initial_state, dealer=2)
    board = render(ReplayFrame(0, state, None, ()), prefix, columns=100)
    assert board.count("Melds: -") == 4
    assert "P0 W" in board and "P2 E [dealer]" in board


def test_declared_melds_are_separate_bullets_in_establishment_order(make_state):
    from tw_mahjong.model import Meld, MeldKind, SimulationResult
    from tw_mahjong.playback import render_frame
    melds = (Meld(MeldKind.CHI, (Tile(0), Tile(4), Tile(8)), 3, 0),
             Meld(MeldKind.PENG, (Tile(36), Tile(37), Tile(38)), 1, 36),
             Meld(MeldKind.KONG_CONCEALED, tuple(Tile(i) for i in range(72, 76)), None, None))
    state = make_state(melds={0: melds})
    result = SimulationResult(state, state, ())
    frame = ReplayFrame(0, state, None, ())
    for text in (render(frame, result), render_frame(frame, result, (), speed=2, paused=False)):
        assert text.index("- CHI") < text.index("- PENG") < text.index("- KONG_CONCEALED")
        assert len([line for line in text.splitlines() if any(f"- {kind}" in line for kind in ("CHI", "PENG", "KONG_CONCEALED"))]) == 3


@pytest.mark.parametrize("ascii_tiles", [True, False])
def test_added_kong_description_distinguishes_declaration_and_completion(added_kong_ready, ascii_tiles):
    from tw_mahjong.model import SimulationResult
    from tw_mahjong.playback import main_action
    from tw_mahjong.simulation import replay
    actions = (Action(ActionKind.KONG_ADDED, 0, (3,)),) + tuple(Action(ActionKind.PASS, p) for p in (1, 2, 3))
    result = SimulationResult(added_kong_ready, replay(added_kong_ready, actions), actions)
    frames = tuple(iter_replay(added_kong_ready, actions))
    declared = render(frames[1], result, primary=main_action(frames[1]), ascii_tiles=ascii_tiles)
    completed = render(frames[-1], result, primary=main_action(frames[-1]), ascii_tiles=ascii_tiles)
    assert ("KONG_ADDED declared" if ascii_tiles else "宣告加槓") in declared
    assert ("KONG_ADDED completed" if ascii_tiles else "加槓成立") in completed


def test_recent_events_are_translated_on_chinese_board(prefix):
    frame = next(iter_replay(prefix.initial_state, prefix.actions))
    text = render(frame, prefix, ascii_tiles=False, recent=("CLAIMED P1", "REQUEST_CHI P2"))
    assert "副露成立 P1" in text and "申請吃 P2" in text
