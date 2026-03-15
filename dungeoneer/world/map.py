"""DungeonMap: 2D grid of tiles with FOV state arrays."""
from __future__ import annotations

import numpy as np

from dungeoneer.world.tile import TileType, TILE_DEFS


class DungeonMap:
    def __init__(self, width: int, height: int) -> None:
        self.width  = width
        self.height = height

        # Tile type grid — start fully walled
        self._tiles: np.ndarray = np.full(
            (height, width), TileType.WALL, dtype=np.int8
        )

        # Derived boolean arrays (rebuilt when tiles change)
        self.walkable:    np.ndarray = np.zeros((height, width), dtype=bool)
        self.transparent: np.ndarray = np.zeros((height, width), dtype=bool)

        # FOV state
        self.visible:  np.ndarray = np.zeros((height, width), dtype=bool)
        self.explored: np.ndarray = np.zeros((height, width), dtype=bool)

    # ------------------------------------------------------------------
    # Tile access
    # ------------------------------------------------------------------

    def get_type(self, x: int, y: int) -> TileType:
        return TileType(self._tiles[y, x])

    def set_type(self, x: int, y: int, tile_type: TileType) -> None:
        self._tiles[y, x] = tile_type
        td = TILE_DEFS[tile_type]
        self.walkable[y, x]    = td.walkable
        self.transparent[y, x] = td.transparent

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def is_walkable(self, x: int, y: int) -> bool:
        return self.in_bounds(x, y) and bool(self.walkable[y, x])

    def is_transparent(self, x: int, y: int) -> bool:
        return self.in_bounds(x, y) and bool(self.transparent[y, x])

    def has_cover(self, x: int, y: int) -> bool:
        if not self.in_bounds(x, y):
            return False
        return TILE_DEFS[TileType(self._tiles[y, x])].has_cover

    # ------------------------------------------------------------------
    # Fill helpers
    # ------------------------------------------------------------------

    def fill_rect(self, x: int, y: int, w: int, h: int, tile_type: TileType) -> None:
        for ry in range(y, y + h):
            for rx in range(x, x + w):
                if self.in_bounds(rx, ry):
                    self.set_type(rx, ry, tile_type)

    def carve_floor(self, x: int, y: int) -> None:
        self.set_type(x, y, TileType.FLOOR)
