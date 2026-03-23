"""Tile type definitions."""
from __future__ import annotations
from dataclasses import dataclass
from enum import IntEnum, auto


class TileType(IntEnum):
    WALL            = auto()
    FLOOR           = auto()
    STAIR_DOWN      = auto()   # kept for save compat, unused in new generation
    DOOR            = auto()
    ELEVATOR_CLOSED = auto()   # wall-like: not walkable, not transparent
    ELEVATOR_OPEN   = auto()   # walkable + transparent (doors open)
    ELEVATOR_ENTRY  = auto()   # entry elevator (came from above) — not walkable, not transparent


@dataclass(frozen=True)
class TileDef:
    """Static properties of a tile type."""
    tile_type:   TileType
    walkable:    bool
    transparent: bool
    has_cover:   bool = False   # grants cover bonus to actors standing on it


# Registry of tile definitions indexed by TileType
TILE_DEFS: dict[TileType, TileDef] = {
    TileType.WALL:            TileDef(TileType.WALL,            False, False),
    TileType.FLOOR:           TileDef(TileType.FLOOR,           True,  True),
    TileType.STAIR_DOWN:      TileDef(TileType.STAIR_DOWN,      True,  True),
    TileType.DOOR:            TileDef(TileType.DOOR,            True,  False),
    TileType.ELEVATOR_CLOSED: TileDef(TileType.ELEVATOR_CLOSED, False, False),
    TileType.ELEVATOR_OPEN:   TileDef(TileType.ELEVATOR_OPEN,   True,  True),
    TileType.ELEVATOR_ENTRY:  TileDef(TileType.ELEVATOR_ENTRY,  False, False),
}
