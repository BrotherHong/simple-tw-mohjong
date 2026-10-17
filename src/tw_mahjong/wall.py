"""Persistent double-ended wall (SPEC WALL)."""

from dataclasses import dataclass

from .model import MahjongError, Tile


@dataclass(frozen=True)
class Wall:
    tiles: tuple[Tile, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.tiles, tuple) or not all(isinstance(t, Tile) for t in self.tiles):
            raise MahjongError("INVALID_WALL", "Wall requires a tuple of tiles")
        if len({t.id for t in self.tiles}) != len(self.tiles):
            raise MahjongError("INVALID_WALL", "Wall contains duplicate physical tiles")

    def draw_front(self) -> tuple[Tile, "Wall"]:
        if not self.tiles:
            raise MahjongError("INVALID_WALL", "Cannot draw from empty wall")
        return self.tiles[0], Wall(self.tiles[1:])

    def draw_back(self) -> tuple[Tile, "Wall"]:
        if not self.tiles:
            raise MahjongError("INVALID_WALL", "Cannot draw from empty wall")
        return self.tiles[-1], Wall(self.tiles[:-1])
