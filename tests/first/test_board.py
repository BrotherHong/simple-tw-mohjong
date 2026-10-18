import pytest

from tw_mahjong.board import display_width, render_board, tile_block
from tw_mahjong.model import ReplayFrame, SimulationResult, Tile


@pytest.mark.parametrize("text,width", [
    ("", 0), ("abc", 3), ("一萬", 4), ("東 E", 4),
    ("e\u0301", 1), ("\x1b[1;31m一萬\x1b[0m", 4),
])
def test_display_cell_width(text, width):
    assert display_width(text) == width


@pytest.mark.parametrize("tile_id", range(144))
@pytest.mark.parametrize("ascii_tiles", [False, True])
def test_tile_blocks_have_fixed_cell_width(tile_id, ascii_tiles):
    plain = tile_block(Tile(tile_id), ascii_tiles=ascii_tiles, color=False)
    marked = tile_block(Tile(tile_id), ascii_tiles=ascii_tiles, color=True, marked=True)
    assert display_width(plain) == display_width(marked) == 7  # marker column + six-cell block
    assert plain.startswith(" [")
    assert marked.startswith("*")
    assert "\x1b" not in plain
    if ascii_tiles:
        assert Tile(tile_id).code in plain


@pytest.mark.parametrize("tile_id,label,color", [
    (0, "一萬", 31), (36, "一筒", 94), (72, "一索", 32),
    (108, "東", 33), (124, "中", 33), (136, "春花", 95), (143, "菊花", 95),
])
def test_chinese_labels_and_shared_palette(tile_id, label, color):
    block = tile_block(Tile(tile_id), ascii_tiles=False, color=True)
    assert label in block
    assert f"\x1b[{color}m" in block
    assert block.endswith("\x1b[0m")


def board(frame, result, **overrides):
    options = dict(primary=None, speed=2, paused=False, visible_index=0, visible_total=1,
                   draws=0, discards=0, columns=100, ascii_tiles=True,
                   color=False, result_lines=())
    options.update(overrides)
    return render_board(frame, result, (), **options)


@pytest.mark.parametrize("columns", [20, 40, 80, 119, 120, 160])
@pytest.mark.parametrize("ascii_tiles", [False, True])
def test_board_fits_terminal_and_contains_all_players(initial, columns, ascii_tiles):
    frame = ReplayFrame(0, initial, None, ())
    result = SimulationResult(initial, initial, ())
    before = repr(initial)
    rendered = board(frame, result, columns=columns, ascii_tiles=ascii_tiles)
    assert max(map(display_width, rendered.splitlines())) <= columns
    for player in range(4):
        assert f"P{player}" in rendered
    assert "FINISHED" in rendered if ascii_tiles else "播放結束" in rendered
    assert "*" in rendered
    assert "\x1b" not in rendered
    assert repr(initial) == before


def test_wide_layout_places_players_in_two_columns(initial):
    frame = ReplayFrame(0, initial, None, ())
    result = SimulationResult(initial, initial, ())
    wide = board(frame, result, columns=120)
    narrow = board(frame, result, columns=100)
    assert any("P0" in line and "P1" in line for line in wide.splitlines())
    assert not any("P0" in line and "P1" in line for line in narrow.splitlines())


def test_live_board_only_shows_last_twelve_river_tiles(exhausted):
    frame = ReplayFrame(0, exhausted, None, ())
    result = SimulationResult(exhausted, exhausted, ())
    rendered = board(frame, result, columns=100)
    assert "River(136,hidden=124)" in rendered
    assert "[1m" not in rendered
    assert "[R" in rendered and "[G" in rendered and "[B" in rendered
