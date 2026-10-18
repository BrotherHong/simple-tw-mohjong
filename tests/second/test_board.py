"""Display cell widths, tile palettes, wrapping and complete player panels."""

from dataclasses import replace

import pytest

from tw_mahjong.board import display_width, render_board, tile_block
from tw_mahjong.model import Action, ActionKind, Event, EventKind, ReplayFrame, SimulationResult, Tile, full_deck


def render(frame, result, **changes):
    options = dict(primary=None,speed=2,paused=False,visible_index=0,
                   visible_total=len(result.actions),draws=0,discards=0,
                   columns=100,ascii_tiles=True,color=False,result_lines=())
    options.update(changes)
    return render_board(frame,result,(),**options)


@pytest.mark.parametrize("text,width", [("",0),("abc",3),("一萬",4),("Ａ",2),
                                        ("e\u0301",1),("\x1b[31m一萬\x1b[0m",4),
                                        ("* [東  ]",8)])
def test_display_width_ignores_ansi_and_combining_marks(text, width):
    assert display_width(text) == width


@pytest.mark.parametrize("ascii_tiles", [False,True])
@pytest.mark.parametrize("color", [False,True])
def test_every_tile_block_has_fixed_width_and_separate_mark_column(ascii_tiles, color):
    for tile in full_deck():
        normal = tile_block(tile,ascii_tiles=ascii_tiles,color=color)
        marked = tile_block(tile,ascii_tiles=ascii_tiles,color=color,marked=True)
        assert normal.startswith(" ") and marked.startswith("*")
        assert display_width(normal[1:]) == display_width(marked[1:]) == 6
        assert display_width(normal) == display_width(marked) == 7
        assert ("\x1b[" in normal) == color
        if ascii_tiles:
            assert tile.code in normal and normal.isascii()


@pytest.mark.parametrize("tile_id,label,palette", [
    (0,"一萬",31),(32,"九萬",31),(36,"一筒",94),(68,"九筒",94),
    (72,"一索",32),(104,"九索",32),(108,"東",33),(112,"南",33),
    (116,"西",33),(120,"北",33),(124,"中",33),(128,"發",33),(132,"白",33),
    (136,"春花",95),(137,"夏花",95),(138,"秋花",95),(139,"冬花",95),
    (140,"梅花",95),(141,"蘭花",95),(142,"竹花",95),(143,"菊花",95),
])
def test_chinese_tile_names_and_palette(tile_id, label, palette):
    assert label in tile_block(Tile(tile_id),ascii_tiles=False,color=False)
    colored = tile_block(Tile(tile_id),ascii_tiles=False,color=True)
    assert f"\x1b[{palette}m" in colored and colored.endswith("\x1b[0m")


@pytest.mark.parametrize("columns", [20,40,80,119,120,161])
@pytest.mark.parametrize("ascii_tiles,color", [(True,False),(False,False),(False,True)])
def test_board_fits_terminal_width_without_losing_players(initial_state, columns, ascii_tiles, color):
    result = SimulationResult(initial_state,initial_state,())
    frame = ReplayFrame(0,initial_state,None,())
    text = render(frame,result,columns=columns,ascii_tiles=ascii_tiles,color=color)
    assert max(map(display_width,text.splitlines())) <= columns
    for player in range(4):
        assert f"P{player}" in text
    # Player titles are on the same row only in the >=120-column layout.
    shared = any("P0" in line and "P1" in line for line in text.splitlines())
    assert shared == (columns >= 120)
    assert ("\x1b[" in text) == color
    assert "*" in text
    assert initial_state == frame.state


def test_seat_titles_relative_to_dealer_and_no_meld_placeholder(initial_state):
    state = replace(initial_state,dealer=2)
    result = SimulationResult(state,state,())
    frame = ReplayFrame(0,state,None,())
    text = render(frame,result)
    assert "P0 W" in text and "P1 N" in text
    assert "P2 E [dealer]" in text and "P3 S" in text
    assert text.count("Melds: -") == 4


def test_compact_board_limits_river_to_last_twelve(state_factory):
    state = state_factory(discards=(tuple(Tile(i) for i in range(20)),(),(),()))
    result = SimulationResult(state,state,())
    text = render(ReplayFrame(0,state,None,()),result)
    assert "River(20,hidden=8):" in text
    assert "[1m  ]" not in text and "[2m  ]" not in text
    assert "[3m  ]" in text and "[5m  ]" in text


def test_claim_action_shows_actual_claimant_and_external_tile(initial_state):
    claimed = Action(ActionKind.CHI,1,(4,8))
    last_pass = Action(ActionKind.PASS,3)
    event = Event(EventKind.CLAIMED,1,0,claimed)
    frame = ReplayFrame(1,initial_state,last_pass,(event,))
    result = SimulationResult(initial_state,initial_state,(last_pass,))
    text = render(frame,result,primary=claimed)
    action_line = text.split("Action:",1)[1].split("Recent events:",1)[0]
    assert "P1" in action_line and "CHI" in action_line
    assert all(f"[{code}  ]" in action_line for code in ("1m","2m","3m"))
    assert "PASS" not in action_line


def test_nonfinal_response_is_labelled_request(initial_state):
    action = Action(ActionKind.PENG,1,(0,1))
    frame = ReplayFrame(1,initial_state,action,(Event(EventKind.RESPONSE,1,action=action),))
    result = SimulationResult(initial_state,initial_state,(action,))
    assert "request PENG" in render(frame,result,primary=action)
