"""Persistent front/back wall draws, including empty and singleton walls."""

from dataclasses import FrozenInstanceError

import pytest

from tw_mahjong.model import MahjongError, Tile, full_deck
from tw_mahjong.wall import Wall


def test_draws_preserve_supplied_order_and_original_wall():
    tiles = (Tile(7), Tile(136), Tile(1), Tile(90))
    original = Wall(tiles)
    first, after_front = original.draw_front()
    last, after_both = after_front.draw_back()
    assert first == Tile(7) and last == Tile(90)
    assert after_front.tiles == tiles[1:]
    assert after_both.tiles == tiles[1:-1]
    assert original.tiles == tiles
    assert after_front is not original
    with pytest.raises(FrozenInstanceError):
        original.tiles = ()


@pytest.mark.parametrize("method", ["draw_front", "draw_back"])
def test_singleton_draw_returns_empty_wall(method):
    wall = Wall((Tile(143),))
    assert getattr(wall, method)() == (Tile(143), Wall(()))
    assert wall.tiles == (Tile(143),)


@pytest.mark.parametrize("method", ["draw_front", "draw_back"])
def test_empty_draw_is_invalid_wall(method):
    wall = Wall(())
    with pytest.raises(MahjongError) as error:
        getattr(wall, method)()
    assert error.value.code == "INVALID_WALL"
    assert wall.tiles == ()


@pytest.mark.parametrize("tiles", [[], [Tile(0)], (0,), (None,), (Tile(0), Tile(0)), None])
def test_wall_requires_unique_tile_tuple(tiles):
    with pytest.raises(MahjongError) as error:
        Wall(tiles)
    assert error.value.code == "INVALID_WALL"


def test_alternating_draws_conserve_every_physical_tile():
    original = Wall(full_deck())
    wall = original
    drawn = []
    for index in range(144):
        tile, wall = wall.draw_front() if index % 2 == 0 else wall.draw_back()
        drawn.append(tile.id)
    assert sorted(drawn) == list(range(144))
    assert drawn[:6] == [0, 143, 1, 142, 2, 141]
    assert wall.tiles == ()
    assert original.tiles == full_deck()
