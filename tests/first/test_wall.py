import pytest

from tw_mahjong.model import MahjongError, Tile
from tw_mahjong.wall import Wall


def test_draw_both_ends_preserves_order_and_original():
    wall = Wall((Tile(9), Tile(0), Tile(143)))
    front, after_front = wall.draw_front()
    back, after_both = after_front.draw_back()
    assert front == Tile(9)
    assert back == Tile(143)
    assert after_both == Wall((Tile(0),))
    assert wall.tiles == (Tile(9), Tile(0), Tile(143))
    assert after_front.tiles == (Tile(0), Tile(143))


@pytest.mark.parametrize("method", ["draw_front", "draw_back"])
def test_single_tile_then_empty(method):
    tile, empty = getattr(Wall((Tile(42),)), method)()
    assert tile == Tile(42)
    assert empty.tiles == ()
    with pytest.raises(MahjongError) as caught:
        getattr(empty, method)()
    assert caught.value.code == "INVALID_WALL"


@pytest.mark.parametrize("value", [[], [Tile(0)], (0,), (Tile(0), Tile(0)), None])
def test_invalid_wall(value):
    with pytest.raises(MahjongError) as caught:
        Wall(value)
    assert caught.value.code == "INVALID_WALL"
