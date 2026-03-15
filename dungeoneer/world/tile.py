"""Tile type definitions."""
from __future__ import annotations
from dataclasses import dataclass
from enum import IntEnum, auto


class TileType(IntEnum):
    WALL       = auto()
    FLOOR      = auto()
    STAIR_DOWN = auto()
    DOOR       = auto()


@dataclass(frozen=True)
class TileDef:
    """Static properties of a tile type."""
    tile_type:   TileType
    walkable:    bool
    transparent: bool
    has_cover:   bool = False   # grants cover bonus to actors standing on it


# Registry of tile definitions indexed by TileType
TILE_DEFS: dict[TileType, TileDef] = {
    TileType.WALL:       TileDef(TileType.WALL,       False, False),
    TileType.FLOOR:      TileDef(TileType.FLOOR,      True,  True),
    TileType.STAIR_DOWN: TileDef(TileType.STAIR_DOWN, True,  True),
    TileType.DOOR:       TileDef(TileType.DOOR,       True,  False),
}
