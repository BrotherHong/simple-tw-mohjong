"""Persistent front/back drawing and wall validation."""

from dataclasses import FrozenInstanceError

import pytest

from tw_mahjong.model import MahjongError, Tile
from tw_mahjong.wall import Wall


def test_draws_preserve_supplied_order_and_original_wall():
    original = Wall((Tile(8), Tile(0), Tile(143)))
    front, after_front = original.draw_front()
    back, after_back = after_front.draw_back()
    assert front == Tile(8)
    assert back == Tile(143)
    assert after_back.tiles == (Tile(0),)
    assert original.tiles == (Tile(8), Tile(0), Tile(143))
    assert after_front.tiles == (Tile(0), Tile(143))


@pytest.mark.parametrize("method", ["draw_front", "draw_back"])
def test_singleton_then_empty_wall(method):
    tile, empty = getattr(Wall((Tile(7),)), method)()
    assert tile == Tile(7)
    assert empty == Wall(())
    with pytest.raises(MahjongError) as exc:
        getattr(empty, method)()
    assert exc.value.code == "INVALID_WALL"


@pytest.mark.parametrize("value", [[], [Tile(0)], (0,), (None,), (Tile(0), Tile(0)), None])
def test_invalid_wall(value):
    with pytest.raises(MahjongError) as exc:
        Wall(value)
    assert exc.value.code == "INVALID_WALL"


def test_wall_is_frozen():
    with pytest.raises(FrozenInstanceError):
        Wall(()).tiles = (Tile(0),)
